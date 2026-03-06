"""
GitHub Releases 更新检查服务
异步检查最新版本，比较当前版本，并通过信号通知结果
"""
from typing import Optional

from PySide6.QtCore import QObject, QThread, Signal

from app.common.setting import VERSION

GITHUB_API_URL = "https://api.github.com/repos/fastxteam/FastX-Gui/releases/latest"
REQUEST_TIMEOUT = 10  # seconds


class UpdateResult:
    """更新检查结果"""

    def __init__(
        self,
        has_update: bool = False,
        latest_version: str = "",
        current_version: str = VERSION,
        release_url: str = "",
        release_notes: str = "",
        error: str = "",
        is_latest: bool = False,
        no_release: bool = False,
    ):
        self.has_update = has_update
        self.latest_version = latest_version
        self.current_version = current_version
        self.release_url = release_url
        self.release_notes = release_notes
        self.error = error
        self.is_latest = is_latest
        self.no_release = no_release  # 仓库尚未发布任何 Release


class UpdateCheckerWorker(QThread):
    """后台工作线程，执行网络请求"""

    finished = Signal(object)  # UpdateResult

    def run(self):
        result = self._check()
        self.finished.emit(result)

    def _check(self) -> UpdateResult:
        try:
            import urllib.request
            import json

            req = urllib.request.Request(
                GITHUB_API_URL,
                headers={
                    "Accept": "application/vnd.github+json",
                    "User-Agent": "FastX-Gui-Updater",
                },
            )
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            latest_version: str = data.get("tag_name", "").strip()
            release_url: str = data.get("html_url", "")
            release_notes: str = data.get("body", "")

            if not latest_version:
                return UpdateResult(error="无法获取最新版本号")

            has_update = _is_newer(latest_version, VERSION)

            return UpdateResult(
                has_update=has_update,
                latest_version=latest_version,
                current_version=VERSION,
                release_url=release_url,
                release_notes=release_notes,
                is_latest=not has_update,
            )

        except Exception as exc:
            err_str = str(exc)
            # 404 → 仓库尚未发布任何 Release
            if "404" in err_str or "HTTP Error 404" in err_str:
                return UpdateResult(no_release=True, error="暂无发布版本")
            if "timed out" in err_str.lower() or "timeout" in err_str.lower():
                return UpdateResult(error="网络连接超时，请稍后重试")
            return UpdateResult(error=f"检查更新失败：{err_str}")


def _parse_version(version: str):
    """将版本字符串解析为可比较的元组，忽略 v 前缀及预发布标记"""
    version = version.lstrip("v").strip()
    # 去掉预发布部分 (如 -beta.1, -rc.1)
    base = version.split("-")[0]
    parts = base.split(".")
    result = []
    for p in parts:
        try:
            result.append(int(p))
        except ValueError:
            result.append(0)
    # 补齐至三位
    while len(result) < 3:
        result.append(0)
    return tuple(result)


def _is_newer(remote: str, local: str) -> bool:
    """判断远端版本是否比本地版本新"""
    return _parse_version(remote) > _parse_version(local)


class UpdateChecker(QObject):
    """更新检查器，供外部使用的门面类

    使用方式：
        checker = UpdateChecker(parent=self)
        checker.checking.connect(on_checking)
        checker.result_ready.connect(on_result)
        checker.check()
    """

    # 开始检查（UI 可据此显示加载状态）
    checking = Signal()
    # 检查完成，携带 UpdateResult
    result_ready = Signal(object)

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._worker: Optional[UpdateCheckerWorker] = None

    def check(self):
        """触发一次异步版本检查（若已有检查在进行则忽略）"""
        if self._worker and self._worker.isRunning():
            return

        self._worker = UpdateCheckerWorker(self)
        self._worker.finished.connect(self._on_finished)
        self.checking.emit()
        self._worker.start()

    def _on_finished(self, result: UpdateResult):
        self.result_ready.emit(result)
        self._worker = None
