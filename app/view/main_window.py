# coding:utf-8
import sys

from PyQt5.QtCore import Qt, QUrl, QSize, QEventLoop, QTimer
from PyQt5.QtGui import QIcon, QDesktopServices, QFont
from PyQt5.QtWidgets import QApplication, QWidget, QHBoxLayout, QVBoxLayout, QSplashScreen, QLabel
from qfluentwidgets import (NavigationItemPosition, MessageBox, setTheme, Theme, MSFluentWindow, isDarkTheme,
                            NavigationAvatarWidget, SearchLineEdit, qrouter, SubtitleLabel, setFont, SplashScreen)
from qfluentwidgets import FluentIcon as FIF
from qframelesswindow import FramelessWindow, TitleBar

from app.common.translator import Translator
from ..common.style_sheet import StyleSheet
from .home_interface import HomeInterface
from .setting_interface import SettingInterface


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
        self.searchLineEdit.move((self.width() - self.searchLineEdit.width()) //2, 8)


class MainWindow(MSFluentWindow):
    def __init__(self):
        # 先调用父类初始化，但要注意MSFluentWindow会默认设置自己的标题栏
        super().__init__()
        
        # 立即替换为自定义标题栏
        self.setTitleBar(CustomTitleBar(self))
        # 确保标题栏在最上层
        self.titleBar.raise_()
        # 调整布局边距以适应标题栏高度
        self.hBoxLayout.setContentsMargins(0, 48, 0, 0)
        
        # 创建启动页面
        self.splashScreen = SplashScreen(self.windowIcon(), self)
        self.splashScreen.setIconSize(QSize(102, 102))
        
        # 先显示启动页面
        self.show()
        
        # 创建子界面
        self.createSubInterface()

    def createSubInterface(self):
        # create sub interface
        loop = QEventLoop(self)
        QTimer.singleShot(1000, loop.quit)

        self.homeInterface    = HomeInterface(self)
        self.appInterface     = Widget('Application Interface', self)
        self.projectInterface = Widget('Project Interface', self)
        self.libraryInterface = Widget('Library Interface', self)
        self.logInterface     = Widget('Log Interface', self)
        self.settingInterface = SettingInterface(self)

        self.initNavigation()
        self.initWindow()
        # 隐藏启动页面
        self.splashScreen.finish()

        loop.exec_()

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
        self.resize(1200, 700)
        self.setMinimumWidth(1200)
        self.setWindowTitle('福瑞泰克软件中心MCU工具平台')
        self.setWindowIcon(QIcon(':/qfluentwidgets/images/logo.png'))
        self.titleBar.setAttribute(Qt.WA_StyledBackground)

        desktop = QApplication.desktop().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w//2 - self.width()//2, h//2 - self.height()//2)
        self.__setQss()
        self.show()

    def __setQss(self):
        """ set style sheet """
        # initialize style sheet
        self.setObjectName('mainWindow')
        StyleSheet.MAIN_WINDOW.apply(self)

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
