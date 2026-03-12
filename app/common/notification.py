"""
统一通知模块 - 提供系统级和应用内通知的统一接口

使用方式:
    from app.common.notification import Notification
    
    # 成功通知
    Notification.success("操作成功", "文件已保存", parent=self)
    
    # 警告通知
    Notification.warning("警告", "请检查输入", parent=self)
    
    # 错误通知
    Notification.error("错误", "操作失败", parent=self)
    
    # 信息通知
    Notification.info("提示", "正在处理中...", parent=self)
    
    # 可交互通知
    Notification.action(
        title="下载完成",
        content="文件已下载到本地",
        actions=[
            {"text": "打开文件", "callback": lambda: open_file()},
            {"text": "打开目录", "callback": lambda: open_folder()},
        ],
        parent=self
    )
"""
import sys
from typing import Optional, Union, List, Dict, Any, Callable
from enum import Enum

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PySide6.QtGui import QIcon
from loguru import logger
from qfluentwidgets import InfoBar, FluentIcon, InfoBarIcon, InfoBarPosition, HyperlinkButton

from app.common.setting import APPLY_NAME


class NotifyType(Enum):
    """通知类型枚举"""
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    INFO = "info"
    CUSTOM = "custom"


class NotifyPosition(Enum):
    """通知位置枚举 - 映射到InfoBarPosition"""
    TOP = InfoBarPosition.TOP
    BOTTOM = InfoBarPosition.BOTTOM
    TOP_LEFT = InfoBarPosition.TOP_LEFT
    TOP_RIGHT = InfoBarPosition.TOP_RIGHT
    BOTTOM_LEFT = InfoBarPosition.BOTTOM_LEFT
    BOTTOM_RIGHT = InfoBarPosition.BOTTOM_RIGHT
    NONE = InfoBarPosition.NONE


class Notification:
    """
    统一通知接口类
    
    提供静态方法用于显示各种类型的通知：
    - success: 成功通知（绿色）
    - warning: 警告通知（黄色）
    - error: 错误通知（红色）
    - info: 信息通知（蓝色）
    - custom: 自定义通知
    
    所有通知都支持：
    - 自定义持续时间
    - 自定义位置
    - 国际化文本
    - 日志记录
    """
    
    # 默认配置
    DEFAULT_DURATION = {
        NotifyType.SUCCESS: 3000,
        NotifyType.WARNING: 4000,
        NotifyType.ERROR: 5000,
        NotifyType.INFO: 3000,
    }
    
    DEFAULT_POSITION = {
        NotifyType.SUCCESS: NotifyPosition.TOP,
        NotifyType.WARNING: NotifyPosition.TOP,
        NotifyType.ERROR: NotifyPosition.TOP,
        NotifyType.INFO: NotifyPosition.TOP,
    }
    
    @staticmethod
    def success(
        title: str,
        content: str = "",
        parent: Optional[QWidget] = None,
        duration: Optional[int] = None,
        position: Optional[Union[NotifyPosition, InfoBarPosition]] = None,
        is_closable: bool = True,
        orient: Qt.Orientation = Qt.Orientation.Horizontal,
    ) -> InfoBar:
        """
        显示成功通知
        
        Args:
            title: 通知标题
            content: 通知内容
            parent: 父窗口
            duration: 持续时间(毫秒)，None使用默认值
            position: 显示位置，None使用默认值
            is_closable: 是否可关闭
            orient: 布局方向
        
        Returns:
            InfoBar实例
        """
        duration = duration or Notification.DEFAULT_DURATION[NotifyType.SUCCESS]
        position = position or Notification.DEFAULT_POSITION[NotifyType.SUCCESS]
        
        if isinstance(position, NotifyPosition):
            position = position.value
        
        logger.debug(f"[Notification] Success: {title} - {content}")
        return InfoBar.success(
            title=title,
            content=content,
            orient=orient,
            isClosable=is_closable,
            position=position,
            duration=duration,
            parent=parent,
        )
    
    @staticmethod
    def warning(
        title: str,
        content: str = "",
        parent: Optional[QWidget] = None,
        duration: Optional[int] = None,
        position: Optional[Union[NotifyPosition, InfoBarPosition]] = None,
        is_closable: bool = True,
        orient: Qt.Orientation = Qt.Orientation.Horizontal,
    ) -> InfoBar:
        """
        显示警告通知
        
        Args:
            title: 通知标题
            content: 通知内容
            parent: 父窗口
            duration: 持时间(毫秒)，None使用默认值
            position: 显示位置，None使用默认值
            is_closable: 是否可关闭
            orient: 布局方向
        
        Returns:
            InfoBar实例
        """
        duration = duration or Notification.DEFAULT_DURATION[NotifyType.WARNING]
        position = position or Notification.DEFAULT_POSITION[NotifyType.WARNING]
        
        if isinstance(position, NotifyPosition):
            position = position.value
        
        logger.debug(f"[Notification] Warning: {title} - {content}")
        return InfoBar.warning(
            title=title,
            content=content,
            orient=orient,
            isClosable=is_closable,
            position=position,
            duration=duration,
            parent=parent,
        )
    
    @staticmethod
    def error(
        title: str,
        content: str = "",
        parent: Optional[QWidget] = None,
        duration: Optional[int] = None,
        position: Optional[Union[NotifyPosition, InfoBarPosition]] = None,
        is_closable: bool = True,
        orient: Qt.Orientation = Qt.Orientation.Horizontal,
    ) -> InfoBar:
        """
        显示错误通知
        
        Args:
            title: 通知标题
            content: 通知内容
            parent: 父窗口
            duration: 持续时间(毫秒)，None使用默认值
            position: 显示位置，None使用默认值
            is_closable: 是否可关闭
            orient: 布局方向
        
        Returns:
            InfoBar实例
        """
        duration = duration or Notification.DEFAULT_DURATION[NotifyType.ERROR]
        position = position or Notification.DEFAULT_POSITION[NotifyType.ERROR]
        
        if isinstance(position, NotifyPosition):
            position = position.value
        
        logger.error(f"[Notification] Error: {title} - {content}")
        return InfoBar.error(
            title=title,
            content=content,
            orient=orient,
            isClosable=is_closable,
            position=position,
            duration=duration,
            parent=parent,
        )
    
    @staticmethod
    def info(
        title: str,
        content: str = "",
        parent: Optional[QWidget] = None,
        duration: Optional[int] = None,
        position: Optional[Union[NotifyPosition, InfoBarPosition]] = None,
        is_closable: bool = True,
        orient: Qt.Orientation = Qt.Orientation.Horizontal,
    ) -> InfoBar:
        """
        显示信息通知
        
        Args:
            title: 通知标题
            content: 通知内容
            parent: 父窗口
            duration: 持续时间(毫秒)，None使用默认值
            position: 显示位置，None使用默认值
            is_closable: 是否可关闭
            orient: 布局方向
        
        Returns:
            InfoBar实例
        """
        duration = duration or Notification.DEFAULT_DURATION[NotifyType.INFO]
        position = position or Notification.DEFAULT_POSITION[NotifyType.INFO]
        
        if isinstance(position, NotifyPosition):
            position = position.value
        
        logger.debug(f"[Notification] Info: {title} - {content}")
        return InfoBar.info(
            title=title,
            content=content,
            orient=orient,
            isClosable=is_closable,
            position=position,
            duration=duration,
            parent=parent,
        )
    
    @staticmethod
    def custom(
        title: str,
        content: str = "",
        icon: Union[FluentIcon, InfoBarIcon, str] = InfoBarIcon.INFORMATION,
        parent: Optional[QWidget] = None,
        duration: int = 3000,
        position: Optional[Union[NotifyPosition, InfoBarPosition]] = None,
        is_closable: bool = True,
        orient: Qt.Orientation = Qt.Orientation.Horizontal,
        background_color: Optional[str] = None,
        text_color: Optional[str] = None,
    ) -> InfoBar:
        """
        显示自定义通知
        
        Args:
            title: 通知标题
            content: 通知内容
            icon: 自定义图标
            parent: 父窗口
            duration: 持续时间(毫秒)
            position: 显示位置
            is_closable: 是否可关闭
            orient: 布局方向
            background_color: 背景颜色
            text_color: 文字颜色
        
        Returns:
            InfoBar实例
        """
        position = position or NotifyPosition.TOP
        
        if isinstance(position, NotifyPosition):
            position = position.value
        
        logger.debug(f"[Notification] Custom: {title} - {content}")
        info_bar = InfoBar.new(
            icon=icon,
            title=title,
            content=content,
            orient=orient,
            isClosable=is_closable,
            position=position,
            duration=duration,
            parent=parent,
        )
        
        if background_color and text_color:
            info_bar.setCustomBackgroundColor(background_color, text_color)
        
        return info_bar


# ============================================================================
# 可交互通知
# ============================================================================

class ActionButton(HyperlinkButton):
    """通知动作按钮"""
    
    def __init__(self, text: str, callback: Callable, parent=None):
        super().__init__("", text, parent=parent)
        self._callback = callback
        self.clicked.connect(self._on_clicked)
    
    def _on_clicked(self):
        """按钮点击处理"""
        try:
            self._callback()
        except Exception as e:
            logger.exception(f"执行通知回调失败：{e}")


@staticmethod
def action(
    title: str,
    content: str = "",
    actions: List[Dict[str, Any]] = None,
    parent: Optional[QWidget] = None,
    duration: int = 0,  # 0 表示不自动消失
    position: Optional[Union[NotifyPosition, InfoBarPosition]] = None,
    is_closable: bool = True,
    orient: Qt.Orientation = Qt.Orientation.Horizontal,
) -> InfoBar:
    """
    显示可交互通知（带操作按钮）
    
    Args:
        title: 通知标题
        content: 通知内容
        actions: 动作列表，每项为 {"text": str, "callback": callable}
        parent: 父窗口
        duration: 持续时间 (毫秒)，0 表示不自动消失
        position: 显示位置
        is_closable: 是否可关闭
        orient: 布局方向
    
    Returns:
        InfoBar实例
    """
    position = position or NotifyPosition.TOP
    
    if isinstance(position, NotifyPosition):
        position = position.value
    
    logger.debug(f"[Notification] Action: {title} - {content}")
    
    info_bar = InfoBar.new(
        icon=InfoBarIcon.INFORMATION,
        title=title,
        content=content,
        orient=orient,
        isClosable=is_closable,
        position=position,
        duration=duration,
        parent=parent,
    )
    
    # 添加动作按钮
    if actions:
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        
        for action in actions:
            text = action.get("text", "操作")
            callback = action.get("callback", lambda: None)
            
            btn = ActionButton(text, callback, info_bar)
            button_layout.addWidget(btn)
        
        # 将按钮布局添加到 InfoBar
        info_bar.viewLayout.addLayout(button_layout)
    
    return info_bar


@staticmethod
def confirm(
    title: str,
    content: str = "",
    yes_text: str = "确定",
    no_text: str = "取消",
    yes_callback: Callable = None,
    no_callback: Callable = None,
    parent: Optional[QWidget] = None,
    duration: int = 0,
    position: Optional[Union[NotifyPosition, InfoBarPosition]] = None,
) -> InfoBar:
    """
    显示确认通知（是/否选择）
    
    Args:
        title: 通知标题
        content: 通知内容
        yes_text: 确认按钮文本
        no_text: 取消按钮文本
        yes_callback: 确认按钮回调
        no_callback: 取消按钮回调
        parent: 父窗口
        duration: 持续时间
        position: 显示位置
    
    Returns:
        InfoBar实例
    """
    actions = []
    
    if no_callback is not None or no_text != "取消":
        actions.append({"text": no_text, "callback": no_callback or (lambda: None)})
    
    if yes_callback is not None or yes_text != "确定":
        actions.append({"text": yes_text, "callback": yes_callback or (lambda: None)})
    
    return Notification.action(
        title=title,
        content=content,
        actions=actions,
        parent=parent,
        duration=duration,
        position=position,
    )


# ============================================================================
# 系统通知功能
# ============================================================================

def send_system_notification(title: str, content: str, url: str = None) -> bool:
    """
    发送系统级通知（Windows/Linux桌面通知）
    
    Args:
        title: 通知标题
        content: 通知内容
        url: 点击通知后跳转的URL
    
    Returns:
        bool: 通知发送是否成功
    """
    try:
        icon_path = _get_icon_path()
        
        def on_notification_click():
            """点击通知时执行的函数"""
            try:
                if url:
                    import webbrowser
                    webbrowser.open(url)
                    logger.debug(f"已打开通知链接: {url}")
                else:
                    logger.warning("通知未配置URL，无法打开链接")
            except Exception as e:
                logger.exception(f"打开通知链接失败: {e}")
        
        if sys.platform == "win32":
            return _send_windows_notification(
                title, content, icon_path, on_notification_click
            )
        elif sys.platform.startswith("linux"):
            return _send_linux_notification(title, content, icon_path, url)
        else:
            logger.warning(f"当前平台不支持系统通知: {sys.platform}")
            return False
    except Exception as e:
        logger.exception(f"发送系统通知时发生意外错误: {e}")
        return False


def _get_icon_path() -> str:
    """获取应用图标路径"""
    from pathlib import Path
    # 尝试多个可能的图标路径
    possible_paths = [
        Path(__file__).parent.parent / "resource" / "images" / "icon" / "app.ico",
        Path(__file__).parent.parent / "resource" / "images" / "app.ico",
        Path(__file__).parent.parent / "resource" / "icon.ico",
    ]
    for path in possible_paths:
        if path.exists():
            return str(path)
    return ""


def _send_windows_notification(
    title: str, content: str, icon_path: str, callback
) -> bool:
    """发送Windows平台通知"""
    try:
        from win10toast import ToastNotifier
        toaster = ToastNotifier()
        toaster.show_toast(
            title,
            content,
            icon_path=icon_path,
            duration=0,
            threaded=True,
            callback_on_click=callback,
        )
        logger.debug(f"已发送Windows通知: {title}")
        return True
    except ImportError:
        try:
            from plyer import notification
            notification.notify(
                title=title,
                message=content,
                app_name=APPLY_NAME,
                app_icon=icon_path if icon_path else None,
                timeout=0,
            )
            logger.debug(f"已发送Windows通知(使用plyer): {title}")
            return True
        except Exception as e:
            logger.warning(f"发送Windows通知失败: {e}")
            return False


def _send_linux_notification(
    title: str, content: str, icon_path: str, url: str
) -> bool:
    """发送Linux平台通知"""
    try:
        import subprocess
        
        if url:
            subprocess.run(
                [
                    "notify-send",
                    "--icon", icon_path,
                    "--action", f"default={url}",
                    title,
                    content,
                ],
                check=True,
                timeout=0,
            )
            logger.debug(f"已发送Linux通知(包含URL): {title}")
        else:
            subprocess.run(
                ["notify-send", "--icon", icon_path, title, content],
                check=True,
                timeout=0,
            )
            logger.debug(f"已发送Linux通知(不包含URL): {title}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        try:
            from plyer import notification
            notification.notify(
                title=title,
                message=content,
                app_name=APPLY_NAME,
                app_icon=icon_path if icon_path else None,
                timeout=0,
            )
            logger.debug(f"已发送Linux通知(使用plyer): {title}")
            return True
        except Exception as e:
            logger.warning(f"发送Linux通知失败: {e}")
            return False
