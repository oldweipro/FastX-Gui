# coding: utf-8
"""自定义无边框窗口组件。"""

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import BodyLabel, isDarkTheme, qconfig
from qframelesswindow import FramelessWindow


class MyFramelessWindow(FramelessWindow):
    """自定义无边框窗口组件。

    继承自FramelessWindow，支持暗色/亮色主题切换，提供居中显示功能。
    """

    def __init__(self, parent=None, title: str = ""):
        super().__init__(parent=None)

        self.darkQss = """
        MyFramelessWindow{
            background: rgb(32, 32, 32);
        }
        MinimizeButton{
            qproperty-normalColor: white;
            qproperty-normalBackgroundColor: transparent;
            qproperty-hoverColor: white;
            qproperty-hoverBackgroundColor: rgba(255, 255, 255, 26);
            qproperty-pressedColor: white;
            qproperty-pressedBackgroundColor: rgba(255, 255, 255, 51)
        }
        MaximizeButton{
            qproperty-normalColor: white;
            qproperty-normalBackgroundColor: transparent;
            qproperty-hoverColor: white;
            qproperty-hoverBackgroundColor: rgba(255, 255, 255, 26);
            qproperty-pressedColor: white;
            qproperty-pressedBackgroundColor: rgba(255, 255, 255, 51)
        }
        CloseButton {
            qproperty-normalColor: white;
            qproperty-normalBackgroundColor: transparent;
        }
        """
        self.lightQss = """
        MyFramelessWindow{
            background: rgb(240, 244, 249);
        }
        MinimizeButton{
            qproperty-normalColor: black;
            qproperty-normalBackgroundColor: transparent;
            qproperty-hoverColor: black;
            qproperty-hoverBackgroundColor: rgba(0, 0, 0, 26);
            qproperty-pressedColor: black;
            qproperty-pressedBackgroundColor: rgba(0, 0, 0, 51)
        }
        MaximizeButton{
            qproperty-normalColor: black;
            qproperty-normalBackgroundColor: transparent;
            qproperty-hoverColor: black;
            qproperty-hoverBackgroundColor: rgba(0, 0, 0, 26);
            qproperty-pressedColor: black;
            qproperty-pressedBackgroundColor: rgba(0, 0, 0, 51)
        }
        CloseButton{
            qproperty-normalColor: black;
            qproperty-normalBackgroundColor: transparent;
        }
        """

        # 创建标题栏图标
        self.__iconLabel = QLabel()
        self.__iconLabel.setFixedSize(20, 20)
        self.__iconLabel.setScaledContents(True)

        # 加载图标
        icon_path = self._get_icon_path()
        if icon_path:
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                self.__iconLabel.setPixmap(pixmap)
                self.setWindowIcon(pixmap)

        self.__titleLabel = BodyLabel(self.tr(title))
        self.setWindowTitle(title)
        # 设置标题标签的属性，防止与窗口控制按钮重合
        self.__titleLabel.setObjectName("titleLabel")
        self.__titleLabel.setContentsMargins(0, 0, 150, 0)  # 右侧留出150px给按钮区域
        # 启用文本省略，防止标题过长溢出
        self.__titleLabel.setTextInteractionFlags(Qt.NoTextInteraction)
        self.__titleLabel.setWordWrap(False)

        # 创建标题栏布局（图标 + 标题）
        self.__titleBarWidget = QWidget()
        self.__titleBarLayout = QHBoxLayout(self.__titleBarWidget)
        self.__titleBarLayout.setContentsMargins(0, 0, 0, 12)
        self.__titleBarLayout.setSpacing(8)
        self.__titleBarLayout.addWidget(self.__iconLabel)
        self.__titleBarLayout.addWidget(self.__titleLabel)
        self.__titleBarLayout.addStretch()

        self.__centerWidget = QWidget()

        self.__mainLayout = QVBoxLayout(self)
        self.viewLayout = QVBoxLayout(self.__centerWidget)
        self.viewLayout.setContentsMargins(0, 0, 0, 0)
        self.__mainLayout.addWidget(self.__titleBarWidget)
        self.__mainLayout.addWidget(self.__centerWidget)

        self.__centerWidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # 设置最小窗口宽度，防止窗口太小导致标题和按钮重合
        self.setMinimumWidth(400)
        self.setStyleSheet(self.darkQss if isDarkTheme() else self.lightQss)

        # 提升标题栏的层级，确保它在最上层
        self.titleBar.raise_()

        qconfig.themeChanged.connect(self.__on_theme_changed)

        QTimer.singleShot(0, self.__center_window)

    def set_title(self, title: str):
        self.__titleLabel.setText(title)

    def _get_icon_path(self):
        """获取标题栏图标路径。

        使用 Qt 资源路径加载图标。
        优先使用 MyLogo.png，如果不存在则使用 logo.png。
        """
        return ":/app/images/MyLogo.png"

    def __on_theme_changed(self):
        self.setStyleSheet(self.darkQss if isDarkTheme() else self.lightQss)

    def __center_window(self):
        """
        将窗口居中显示
        如果有父窗口则居中在父窗口中央，否则居中在桌面中央
        """
        self.adjustSize()  # 确保窗口大小已经计算好

        if self.parent():
            # 居中在父窗口中央
            parent_geometry = self.parent().geometry()
            x = parent_geometry.left() + (parent_geometry.width() - self.width()) // 2
            y = parent_geometry.top() + (parent_geometry.height() - self.height()) // 2
        else:
            # 居中在桌面中央
            from PySide6.QtWidgets import QApplication

            screen_geometry = QApplication.primaryScreen().geometry()
            x = screen_geometry.left() + (screen_geometry.width() - self.width()) // 2
            y = screen_geometry.top() + (screen_geometry.height() - self.height()) // 2

        self.move(x, y)


__all__ = ["MyFramelessWindow"]
