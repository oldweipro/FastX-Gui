import sys
from typing import Optional, Union

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget
from loguru import logger
from qfluentwidgets import InfoBar, FluentIcon, InfoBarIcon, InfoBarPosition

from app.common.setting import APPLY_NAME


# ==================== 通知模块 ====================
class NotificationType:
    """预定义的通知类型"""

    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    INFO = "info"
    CUSTOM = "custom"


class NotificationConfig:
    """通知配置类，用于定义通知的各种参数"""

    def __init__(
        self,
        title: str = "",
        content: str = "",
        icon: Union[FluentIcon, InfoBarIcon, str] = None,
        duration: int = 3000,
        position: Union[InfoBarPosition, str] = InfoBarPosition.TOP,
        is_closable: bool = True,
        orient: Qt.Orientation = Qt.Orientation.Horizontal,
        background_color: Optional[str] = None,
        text_color: Optional[str] = None,
    ):
        self.title = title
        self.content = content
        self.icon = icon
        self.duration = duration
        self.position = position
        self.is_closable = is_closable
        self.orient = orient
        self.background_color = background_color
        self.text_color = text_color


def show_success_notification(
    title: str,
    content: str,
    parent: Optional[QWidget] = None,
    duration: int = 3000,
    position: Union[InfoBarPosition, str] = InfoBarPosition.TOP,
    is_closable: bool = True,
    orient: Qt.Orientation = Qt.Orientation.Horizontal,
) -> InfoBar:
    """显示成功通知"""
    return InfoBar.success(
        title=title,
        content=content,
        orient=orient,
        isClosable=is_closable,
        position=position,
        duration=duration,
        parent=parent,
    )


def show_warning_notification(
    title: str,
    content: str,
    parent: Optional[QWidget] = None,
    duration: int = -1,
    position: Union[InfoBarPosition, str] = InfoBarPosition.BOTTOM,
    is_closable: bool = True,
    orient: Qt.Orientation = Qt.Orientation.Horizontal,
) -> InfoBar:
    """显示警告通知"""
    return InfoBar.warning(
        title=title,
        content=content,
        orient=orient,
        isClosable=is_closable,
        position=position,
        duration=duration,
        parent=parent,
    )


def show_error_notification(
    title: str,
    content: str,
    parent: Optional[QWidget] = None,
    duration: int = 5000,
    position: Union[InfoBarPosition, str] = InfoBarPosition.BOTTOM_RIGHT,
    is_closable: bool = True,
    orient: Qt.Orientation = Qt.Orientation.Vertical,
) -> InfoBar:
    """显示错误通知"""
    return InfoBar.error(
        title=title,
        content=content,
        orient=orient,
        isClosable=is_closable,
        position=position,
        duration=duration,
        parent=parent,
    )

def show_info_notification(
    title: str,
    content: str,
    parent: Optional[QWidget] = None,
    duration: int = -1,
    position: Union[InfoBarPosition, str] = InfoBarPosition.BOTTOM_LEFT,
    is_closable: bool = True,
    orient: Qt.Orientation = Qt.Orientation.Horizontal,
) -> InfoBar:
    """显示信息通知"""
    return InfoBar.info(
        title=title,
        content=content,
        orient=orient,
        isClosable=is_closable,
        position=position,
        duration=duration,
        parent=parent,
    )

def show_custom_notification(
    title: str,
    content: str,
    icon: Union[FluentIcon, InfoBarIcon, str] = InfoBarIcon.INFORMATION,
    parent: Optional[QWidget] = None,
    duration: int = 3000,
    position: Union[InfoBarPosition, str] = InfoBarPosition.TOP,
    is_closable: bool = True,
    orient: Qt.Orientation = Qt.Orientation.Horizontal,
    background_color: Optional[str] = None,
    text_color: Optional[str] = None,
) -> InfoBar:
    """显示自定义通知"""
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

def show_notification(notification_type: str, config: NotificationConfig, parent: Optional[QWidget] = None) -> InfoBar:
    """显示通知

    Args:
        notification_type: 通知类型，值为NotificationType中定义的常量
        config: 通知配置对象
        parent: 父窗口组件

    Returns:
        InfoBar实例
    """
    if parent is not None and not isinstance(parent, QWidget):
        parent = None
    type_handlers = {
        NotificationType.SUCCESS: lambda: InfoBar.success(
            title=config.title,
            content=config.content,
            orient=config.orient,
            isClosable=config.is_closable,
            position=config.position,
            duration=config.duration,
            parent=parent,
        ),
        NotificationType.WARNING: lambda: InfoBar.warning(
            title=config.title,
            content=config.content,
            orient=config.orient,
            isClosable=config.is_closable,
            position=config.position,
            duration=config.duration,
            parent=parent,
        ),
        NotificationType.ERROR: lambda: InfoBar.error(
            title=config.title,
            content=config.content,
            orient=config.orient,
            isClosable=config.is_closable,
            position=config.position,
            duration=config.duration,
            parent=parent,
        ),
        NotificationType.INFO: lambda: InfoBar.info(
            title=config.title,
            content=config.content,
            orient=config.orient,
            isClosable=config.is_closable,
            position=config.position,
            duration=config.duration,
            parent=parent,
        ),
        NotificationType.CUSTOM: lambda: _create_custom_notification(config, parent),
    }

    handler = type_handlers.get(notification_type)
    if handler:
        return handler()

    raise ValueError(f"不支持的通知类型: {notification_type}")

def _create_custom_notification(
    config: NotificationConfig, parent: Optional[QWidget]
) -> InfoBar:
    """创建自定义通知"""
    info_bar = InfoBar.new(
        icon=config.icon or InfoBarIcon.INFORMATION,
        title=config.title,
        content=config.content,
        orient=config.orient,
        isClosable=config.is_closable,
        position=config.position,
        duration=config.duration,
        parent=parent,
    )

    if config.background_color and config.text_color:
        info_bar.setCustomBackgroundColor(config.background_color, config.text_color)

    return info_bar

def send_system_notification(title: str, content: str, url: str = None) -> bool:
    """发送系统通知

    Args:
        title: 通知标题
        content: 通知内容
        url: 点击通知后跳转的URL

    Returns:
        bool: 通知发送是否成功
    """
    try:
        icon_path = str(get_data_path("assets", "icon/secrandom-icon-paper.ico"))

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
                app_icon=icon_path,
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
                    "--icon",
                    icon_path,
                    "--action",
                    f"default={url}",
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
                app_icon=icon_path,
                timeout=0,
            )
            logger.debug(f"已发送Linux通知(使用plyer): {title}")
            return True
        except Exception as e:
            logger.warning(f"发送Linux通知失败: {e}")
            return False

