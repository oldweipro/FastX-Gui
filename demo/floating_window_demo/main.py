# ==================================================
# 悬浮窗 Demo 入口
# 运行方式：python main.py
# 依赖：pip install PySide6 qfluentwidgets
# ==================================================

import sys
import os

# 将 demo 目录加入 sys.path，确保本地模块优先被找到
_DEMO_DIR = os.path.dirname(os.path.abspath(__file__))
if _DEMO_DIR not in sys.path:
    sys.path.insert(0, _DEMO_DIR)

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QScrollArea, QFrame,
)
from PySide6.QtGui import QFont
from qfluentwidgets import (
    FluentWindow, NavigationItemPosition, FluentIcon,
    ScrollArea, PushButton, TitleLabel, BodyLabel,
    setTheme, Theme, qconfig,
)

from config import init_settings, _copy_assets_if_needed
from levitation import LevitationWindow
from settings_panel import FloatingWindowSettingsPanel


# ==================================================
# 设置页面（ScrollArea 容器）
# ==================================================

class SettingsPage(ScrollArea):
    def __init__(self, levitation_win: LevitationWindow, parent=None):
        super().__init__(parent)
        self.setObjectName("settingsPage")
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        inner = QWidget()
        inner.setObjectName("settingsInner")
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(16)

        title = TitleLabel("悬浮窗设置")
        title.setFont(QFont(title.font().family(), 20, QFont.Bold))
        lay.addWidget(title)

        desc = BodyLabel(
            "在此页面调整悬浮窗的外观、行为与交互设置。\n"
            "所有设置实时生效并自动保存到 floating_window_settings.json。"
        )
        desc.setWordWrap(True)
        lay.addWidget(desc)

        self._panel = FloatingWindowSettingsPanel(inner)
        self._panel.set_levitation_window(levitation_win)
        lay.addWidget(self._panel)
        lay.addStretch(1)

        self.setWidget(inner)


# ==================================================
# 主界面页面
# ==================================================

class HomePage(ScrollArea):
    def __init__(self, levitation_win: LevitationWindow, parent=None):
        super().__init__(parent)
        self.setObjectName("homePage")
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._lev = levitation_win

        inner = QWidget()
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(40, 40, 40, 40)
        lay.setSpacing(20)

        title = TitleLabel("悬浮窗 Demo")
        title.setFont(QFont(title.font().family(), 24, QFont.Bold))
        lay.addWidget(title)

        lay.addWidget(BodyLabel(
            "这是一个从 SecRandom 项目完整剥离的悬浮窗独立 Demo。\n\n"
            "• 悬浮窗已自动启动（根据配置决定是否显示）\n"
            "• 可在「悬浮窗设置」页面实时调整所有参数\n"
            "• 配置保存在同目录 floating_window_settings.json\n"
            "• 点击下方按钮可快速显示/隐藏悬浮窗"
        ))

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        btn_show = PushButton("显示悬浮窗")
        btn_show.setFixedWidth(140)
        btn_show.clicked.connect(lambda: levitation_win.set_user_requested_visible(True))

        btn_hide = PushButton("隐藏悬浮窗")
        btn_hide.setFixedWidth(140)
        btn_hide.clicked.connect(lambda: levitation_win.set_user_requested_visible(False))

        btn_toggle = PushButton("切换显示/隐藏")
        btn_toggle.setFixedWidth(160)
        btn_toggle.clicked.connect(levitation_win.toggle_visible)

        for b in (btn_show, btn_hide, btn_toggle):
            btn_row.addWidget(b)
        btn_row.addStretch(1)
        lay.addLayout(btn_row)

        # 信号日志区域
        lay.addWidget(BodyLabel("信号日志（按钮点击时记录）："))
        self._log_label = BodyLabel("（暂无）")
        self._log_label.setWordWrap(True)
        self._log_label.setStyleSheet("color: gray;")
        lay.addWidget(self._log_label)
        lay.addStretch(1)

        self.setWidget(inner)

        # 连接悬浮窗信号
        for sig, name in (
            (levitation_win.rollCallRequested,  "点名"),
            (levitation_win.quickDrawRequested, "闪抽"),
            (levitation_win.lotteryRequested,   "抽奖"),
            (levitation_win.faceDrawRequested,  "人脸"),
            (levitation_win.timerRequested,     "计时"),
        ):
            sig.connect(lambda n=name: self._log(f"触发：{n}"))

    def _log(self, msg: str):
        from datetime import datetime
        ts = datetime.now().strftime("%H:%M:%S")
        prev = self._log_label.text()
        lines = [f"[{ts}] {msg}"] + (prev.splitlines() if prev != "（暂无）" else [])
        self._log_label.setText("\n".join(lines[:10]))


# ==================================================
# 主窗口（FluentWindow）
# ==================================================

class DemoMainWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("悬浮窗 Demo")
        self.resize(900, 640)

        # 初始化配置
        init_settings()

        # 创建悬浮窗
        self._lev = LevitationWindow()
        self._lev._close_guard_enabled = False  # demo 中允许正常关闭

        # 创建页面
        self._home_page     = HomePage(self._lev)
        self._settings_page = SettingsPage(self._lev)

        # 注册导航
        self.addSubInterface(
            self._home_page,
            FluentIcon.HOME,
            "主页",
            position=NavigationItemPosition.TOP,
        )
        self.addSubInterface(
            self._settings_page,
            FluentIcon.SETTING,
            "悬浮窗设置",
            position=NavigationItemPosition.TOP,
        )

    def closeEvent(self, event):
        # 关闭主窗口时同步关闭悬浮窗
        try:
            self._lev._close_guard_enabled = False
            self._lev.close()
        except Exception:
            pass
        super().closeEvent(event)


# ==================================================
# 启动入口
# ==================================================

def main():
    # 最优先：将资源复制到 demo 本地（首次运行时生效，之后幂等跳过）
    _copy_assets_if_needed()

    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    window = DemoMainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
