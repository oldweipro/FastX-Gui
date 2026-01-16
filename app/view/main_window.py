# coding:utf-8
import sys

from PyQt5.QtCore import Qt, QUrl, QSize, QEventLoop, QTimer, QDateTime
from PyQt5.QtGui import QIcon, QDesktopServices, QFont, QColor
from PyQt5.QtWidgets import QApplication, QWidget, QHBoxLayout, QVBoxLayout, QSplashScreen, QLabel, QStatusBar, QFrame
from qfluentwidgets import (NavigationItemPosition, MessageBox, setTheme, Theme, MSFluentWindow, isDarkTheme,
                            NavigationAvatarWidget, SearchLineEdit, qrouter, SubtitleLabel, setFont, SplashScreen,
                            IndeterminateProgressBar, ProgressBar, PushButton, FluentIcon as FIF, InfoBar,
                            InfoBarPosition)
from qframelesswindow import FramelessWindow, TitleBar

from app.common.translator import Translator
from app.common.style_sheet import StyleSheet
from app.view.home_interface import HomeInterface
from app.view.setting_interface import SettingInterface
from app.view.app_interface import AppInterface
from app.view.log_interface import LogInterface
from app.view.rte_interface import RteInterface


class Widget(QWidget):
    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.label = SubtitleLabel(text, self)
        self.hBoxLayout = QHBoxLayout(self)

        setFont(self.label, 24)
        self.label.setAlignment(Qt.AlignCenter)
        self.hBoxLayout.addWidget(self.label, 1, Qt.AlignCenter)
        self.setObjectName(text.replace(' ', '-'))


class CustomTitleBar(TitleBar):
    """ Title bar with icon and title """

    def __init__(self, parent):
        super().__init__(parent)
        self.setFixedHeight(48)
        self.hBoxLayout.removeWidget(self.minBtn)
        self.hBoxLayout.removeWidget(self.maxBtn)
        self.hBoxLayout.removeWidget(self.closeBtn)

        # add window icon
        self.iconLabel = QLabel(self)
        self.iconLabel.setFixedSize(18, 18)
        self.hBoxLayout.insertSpacing(0, 20)
        self.hBoxLayout.insertWidget(1, self.iconLabel, 0, Qt.AlignLeft | Qt.AlignVCenter)
        self.window().windowIconChanged.connect(self.setIcon)

        # add title label
        self.titleLabel = QLabel(self)
        self.hBoxLayout.insertWidget(
            2, self.titleLabel, 0, Qt.AlignLeft | Qt.AlignVCenter)
        self.titleLabel.setObjectName('titleLabel')
        self.window().windowTitleChanged.connect(self.setTitle)

        # add search line edit
        self.searchLineEdit = SearchLineEdit(self)
        self.searchLineEdit.setPlaceholderText('搜索应用、脚本、工具、设置等')
        self.searchLineEdit.setFixedWidth(400)
        self.searchLineEdit.setClearButtonEnabled(True)

        self.vBoxLayout = QVBoxLayout()
        self.buttonLayout = QHBoxLayout()
        self.buttonLayout.setSpacing(0)
        self.buttonLayout.setContentsMargins(0, 0, 0, 0)
        self.buttonLayout.setAlignment(Qt.AlignTop)
        self.buttonLayout.addWidget(self.minBtn)
        self.buttonLayout.addWidget(self.maxBtn)
        self.buttonLayout.addWidget(self.closeBtn)
        self.vBoxLayout.addLayout(self.buttonLayout)
        self.vBoxLayout.addStretch(1)
        self.hBoxLayout.addLayout(self.vBoxLayout, 0)

    def setTitle(self, title):
        self.titleLabel.setText(title)
        self.titleLabel.adjustSize()

    def setIcon(self, icon):
        self.iconLabel.setPixmap(QIcon(icon).pixmap(18, 18))

    def resizeEvent(self, e):
        self.searchLineEdit.move((self.width() - self.searchLineEdit.width()) // 2, 8)


class StatusBarWidget(QFrame):
    """自定义状态栏部件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(40)
        self.setupUI()
        self.setupTimer()

    def setupUI(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 5, 15, 5)
        layout.setSpacing(20)

        # 左侧状态信息
        self.statusLabel = QLabel("就绪")
        self.statusLabel.setFixedWidth(200)
        layout.addWidget(self.statusLabel)

        # 进度条区域
        self.progressWidget = QWidget()
        progressLayout = QHBoxLayout(self.progressWidget)
        progressLayout.setContentsMargins(0, 0, 0, 0)
        progressLayout.setSpacing(10)

        self.progressLabel = QLabel("进度:")
        self.progressBar = ProgressBar()
        self.progressBar.setFixedWidth(150)
        self.progressBar.hide()  # 默认隐藏

        progressLayout.addWidget(self.progressLabel)
        progressLayout.addWidget(self.progressBar)

        layout.addWidget(self.progressWidget)
        layout.addStretch()

        # 右侧信息区域
        # 当前用户
        self.userLabel = QLabel("用户: Guest")
        layout.addWidget(self.userLabel)

        # 分隔线
        separator = QLabel("|")
        separator.setStyleSheet("color: gray;")
        layout.addWidget(separator)

        # 系统时间
        self.timeLabel = QLabel("")
        self.timeLabel.setFixedWidth(120)
        layout.addWidget(self.timeLabel)

        # 分隔线
        separator2 = QLabel("|")
        separator2.setStyleSheet("color: gray;")
        layout.addWidget(separator2)

        # 版本信息
        self.versionLabel = QLabel("版本: v1.0.0")
        layout.addWidget(self.versionLabel)

        # 设置样式
        self.setStyleSheet("""
            StatusBarWidget {
                background-color: rgba(245, 245, 245, 0.95);
                border-top: 1px solid #e0e0e0;
            }
            QLabel {
                color: #666666;
                font-size: 12px;
            }
        """)

    def setupTimer(self):
        """设置定时器更新时间"""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.updateTime)
        self.timer.start(1000)  # 每秒更新一次
        self.updateTime()

    def updateTime(self):
        """更新时间显示"""
        current_time = QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")
        self.timeLabel.setText(current_time)

    def setStatus(self, text):
        """设置状态文本"""
        self.statusLabel.setText(text)

    def showProgress(self, show=True):
        """显示/隐藏进度条"""
        self.progressBar.setVisible(show)
        self.progressLabel.setVisible(show)

    def setProgress(self, value):
        """设置进度条值"""
        self.progressBar.setValue(value)
        self.showProgress(value < 100)

    def setUser(self, username):
        """设置当前用户"""
        self.userLabel.setText(f"用户: {username}")

    def setVersion(self, version):
        """设置版本信息"""
        self.versionLabel.setText(f"版本: {version}")


class MainWindow(MSFluentWindow):
    def __init__(self):
        # 先调用父类初始化
        super().__init__()

        # 设置自定义标题栏
        self.setTitleBar(CustomTitleBar(self))
        self.titleBar.raise_()

        # 调整布局边距以适应标题栏高度
        self.hBoxLayout.setContentsMargins(0, 48, 0, 40)  # 底部增加40px给状态栏

        # 创建启动页面
        self.splashScreen = SplashScreen(self.windowIcon(), self)
        self.splashScreen.setIconSize(QSize(102, 102))

        # 创建状态栏（先创建但不添加到布局）
        self.statusBar = StatusBarWidget(self)

        # 显示窗口
        self.show()

        # 创建子界面
        self.createSubInterface()

    def createSubInterface(self):
        # create sub interface
        loop = QEventLoop(self)
        QTimer.singleShot(1000, loop.quit)

        self.homeInterface    = HomeInterface(self)
        self.appInterface     = AppInterface(self)
        self.projectInterface = RteInterface(self)
        self.libraryInterface = Widget('Library Interface', self)
        self.logInterface     = LogInterface(self)
        self.settingInterface = SettingInterface(self)

        self.initNavigation()
        self.initWindow()

        # 隐藏启动页面
        self.splashScreen.finish()

        # 模拟一些状态变化
        self.simulateStatusChanges()

        loop.exec_()

    def resizeEvent(self, event):
        """重写resize事件以正确定位状态栏"""
        super().resizeEvent(event)
        # 更新状态栏位置和大小
        if hasattr(self, 'statusBar'):
            self.statusBar.setGeometry(
                0,
                self.height() - 40,
                self.width(),
                40
            )

    def initNavigation(self):
        # add navigation items
        t = Translator()
        pos = NavigationItemPosition.TOP
        self.addSubInterface(self.homeInterface, FIF.HOME, t.home, FIF.HOME_FILL, position=pos)
        self.addSubInterface(self.appInterface, FIF.APPLICATION, t.app, position=pos)

        pos = NavigationItemPosition.SCROLL
        self.addSubInterface(self.projectInterface, FIF.CAR, t.project, position=pos)
        self.addSubInterface(self.logInterface, FIF.COMMAND_PROMPT, t.log, position=pos)

        pos = NavigationItemPosition.BOTTOM
        self.navigationInterface.addItem(
            routeKey='Help',
            icon=FIF.HELP,
            text=t.help,
            onClick=self.showMessageBox,
            selectable=False,
            position=pos,
        )
        self.addSubInterface(self.libraryInterface, FIF.BOOK_SHELF, t.library, FIF.LIBRARY_FILL, position=pos)
        self.addSubInterface(self.settingInterface, FIF.SETTING, t.settings, position=pos)

        self.navigationInterface.setCurrentItem(self.homeInterface.objectName())

    def initWindow(self):
        self.resize(1250, 700)
        self.setMinimumWidth(1250)
        self.setWindowTitle('福瑞泰克软件中心MCU工具平台')
        self.setWindowIcon(QIcon(':/qfluentwidgets/images/logo.png'))
        self.titleBar.setAttribute(Qt.WA_StyledBackground)

        # 设置状态栏初始信息
        self.statusBar.setUser("Admin")
        self.statusBar.setVersion("v1.2.0")

        # 确保状态栏在最上层显示
        self.statusBar.raise_()

        desktop = QApplication.desktop().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w // 2 - self.width() // 2, h // 2 - self.height() // 2)
        self.__setQss()
        self.show()

    def simulateStatusChanges(self):
        """模拟状态变化（实际使用时根据业务逻辑调用）"""
        # 模拟进度条
        self.statusBar.setStatus("正在加载资源...")
        self.statusBar.setProgress(30)

        # 3秒后完成进度
        QTimer.singleShot(3000, lambda: self.statusBar.setProgress(100))
        QTimer.singleShot(3500, lambda: self.statusBar.setStatus("就绪"))

        # 5秒后显示一个临时状态
        QTimer.singleShot(5000, lambda: self.statusBar.setStatus("检测到新版本可用"))
        QTimer.singleShot(8000, lambda: self.statusBar.setStatus("就绪"))

    def showMessageBox(self):
        w = MessageBox(
            '刘小豪🥰',
            '快歇一歇吧🚀',
            self
        )
        w.yesButton.setText('好的')
        w.cancelButton.setText('好的')

        if w.exec():
            QDesktopServices.openUrl(QUrl("https://afdian.net/a/zhiyiYo"))

    def showInfoBar(self, title, content, duration=3000):
        """显示信息栏（从底部弹出）"""
        InfoBar.success(
            title=title,
            content=content,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.BOTTOM,
            duration=duration,
            parent=self
        )

    def __setQss(self):
        """ set style sheet """
        # initialize style sheet
        self.setObjectName('mainWindow')
        StyleSheet.MAIN_WINDOW.apply(self)

        # 根据主题调整状态栏样式
        if isDarkTheme():
            self.statusBar.setStyleSheet("""
                StatusBarWidget {
                    background-color: rgba(45, 45, 45, 0.95);
                    border-top: 1px solid #555555;
                }
                QLabel {
                    color: #aaaaaa;
                    font-size: 12px;
                }
            """)
        else:
            self.statusBar.setStyleSheet("""
                StatusBarWidget {
                    background-color: rgba(245, 245, 245, 0.95);
                    border-top: 1px solid #e0e0e0;
                }
                QLabel {
                    color: #666666;
                    font-size: 12px;
                }
            """)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    setTheme(Theme.LIGHT)

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())