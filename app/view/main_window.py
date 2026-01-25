# coding:utf-8
import sys

from PyQt5.QtCore import Qt, QUrl, QSize, QEventLoop, QTimer, QDateTime
from PyQt5.QtGui import QIcon, QDesktopServices, QFont, QColor
from PyQt5.QtWidgets import QApplication, QWidget, QHBoxLayout, QVBoxLayout, QSplashScreen, QLabel, QStatusBar, QFrame, \
    QSystemTrayIcon, QAction
from qfluentwidgets import (NavigationItemPosition, MessageBox, setTheme, Theme, MSFluentWindow, isDarkTheme,
                            NavigationAvatarWidget, SearchLineEdit, qrouter, SubtitleLabel, setFont, SplashScreen,
                            IndeterminateProgressBar, ProgressBar, PushButton, FluentIcon as FIF, InfoBar,
                            InfoBarPosition, SystemTrayMenu)
from qframelesswindow import FramelessWindow, TitleBar

from app.view.home_interface import HomeInterface
from app.view.setting_interface import SettingInterface
from app.view.app_interface import AppInterface
from app.view.log_interface import LogInterface
from app.view.rte_interface import RteInterface
from app.view.func_interface import FuncInterface
from app.view.library_interface import LibraryViewInterface

from app.common.icon import Icon
from app.common.translator import Translator
from app.common.style_sheet import StyleSheet
from app.common.signal_bus import signalBus
from app.common.config import cfg
from app.common import resource
from app.common.setting import VERSION
from app.card.messagebox_custom import MessageBoxCloseWindow


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
        self.hBoxLayout.insertWidget(2, self.titleLabel, 0, Qt.AlignLeft | Qt.AlignVCenter)
        self.titleLabel.setObjectName('titleLabel')
        self.window().windowTitleChanged.connect(self.setTitle)

        # add search line edit
        self.searchLineEdit = SearchLineEdit(self)
        self.searchLineEdit.setObjectName('searchLineEdit')
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
        StyleSheet.MAIN_WINDOW.apply(self)
        self.titleLabel.setText(title)
        self.titleLabel.adjustSize()

    def setIcon(self, icon):
        self.iconLabel.setPixmap(QIcon(icon).pixmap(18, 18))

    def resizeEvent(self, e):
        self.searchLineEdit.move((self.width() - self.searchLineEdit.width()) // 2, 8)

class MainWindow(MSFluentWindow):
    def __init__(self):
        # 先调用父类初始化
        super().__init__()
        self.initWindow()
        self.initInterface()
        # 创建信号连接到槽
        self.connectSignalToSlot()
        # add items to navigation interface
        self.initNavigation()
        self.initSystemTray()

    def initWindow(self):
        self.resize(1200, 860)
        self.setMinimumWidth(1200)
        self.setMaximumWidth(1200)
        # 设置自定义标题栏
        self.setTitleBar(CustomTitleBar(self))
        self.titleBar.raise_()
        # 调整布局边距以适应标题栏高度
        self.hBoxLayout.setContentsMargins(0, 48, 0, 0)
        # 设置图标,标题
        self.setWindowIcon(QIcon(':/app/images/logo-m.png'))
        self.setWindowTitle(f'FastXGui {VERSION}')
        self.__setQss()

        # create splash screen
        self.splashScreen = SplashScreen(self.windowIcon(), self)
        self.splashScreen.setIconSize(QSize(106, 106))
        self.splashScreen.raise_()
        # desktop show
        desktop = QApplication.desktop().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w // 2 - self.width() // 2, h // 2 - self.height() // 2)
        self.show()
        QApplication.processEvents()

    def initInterface(self):
        # 创建子界面
        self.homeInterface = HomeInterface(self)
        self.appInterface = AppInterface(self)
        self.projectInterface = RteInterface(self)
        self.funcInterface = FuncInterface(self)
        self.libraryInterface = LibraryViewInterface(self)
        self.logInterface = LogInterface(self)
        self.settingInterface = SettingInterface(self)

    def connectSignalToSlot(self):
        signalBus.micaEnableChanged.connect(self.setMicaEffectEnabled)

    def initNavigation(self):
        # add navigation items
        t = Translator()
        pos = NavigationItemPosition.TOP
        self.addSubInterface(self.homeInterface, FIF.HOME, self.tr("Home"), FIF.HOME_FILL, position=pos, isTransparent=True)
        self.addSubInterface(self.appInterface , FIF.APPLICATION, self.tr("App"), position=pos, isTransparent=False)

        pos = NavigationItemPosition.SCROLL
        self.addSubInterface(self.projectInterface, FIF.CAR, self.tr("Project"), position=pos, isTransparent=False)
        self.addSubInterface(self.logInterface, FIF.COMMAND_PROMPT, self.tr("Log"), position=pos, isTransparent=False)
        self.addSubInterface(self.funcInterface, FIF.CALORIES, self.tr("Rte"), position=pos, isTransparent=True)
        self.addSubInterface(self.libraryInterface, FIF.BOOK_SHELF, self.tr("Library"), FIF.LIBRARY_FILL, position=pos, isTransparent=False)

        pos = NavigationItemPosition.BOTTOM
        self.navigationInterface.addItem(
            routeKey='Help',
            icon=FIF.HELP,
            text= self.tr("Help"),
            onClick=self.showMessageBox,
            selectable=False,
            position=pos,
        )
        self.addSubInterface(self.settingInterface, Icon.SETTINGS, self.tr('Settings'), Icon.SETTINGS_FILLED, position=pos, isTransparent=False)
        self.navigationInterface.setCurrentItem(self.homeInterface.objectName())
        self.splashScreen.finish()

    def initSystemTray(self):
        """初始化系统托盘"""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(':/app/images/logo-m.png'))
        self.tray_icon.setToolTip(f'FastXGui {VERSION}')

        # 创建托盘菜单
        tray_menu = SystemTrayMenu(parent=self)
        tray_menu.aboutToShow.connect(self._on_tray_menu_about_to_show)

        # 显示主界面
        show_action = QAction('显示主界面', self)
        show_action.triggered.connect(self.showNormal)
        show_action.triggered.connect(self.activateWindow)
        tray_menu.addAction(show_action)

        tray_menu.addSeparator()

        # 打开设置界面
        setting_action = QAction('设置', self)
        setting_action.triggered.connect(self._open_settings)
        tray_menu.addAction(setting_action)

        # 退出程序
        quit_action = QAction('退出', self)
        quit_action.triggered.connect(self._quitApp)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._onTrayIconActivated)
        self.tray_icon.show()

    def _on_tray_menu_about_to_show(self):
        """托盘菜单即将显示时激活窗口，解决 Windows 上点击外部区域无法关闭菜单的问题"""
        self.activateWindow()

    def _onTrayIconActivated(self, reason):
        """托盘图标被激活时的处理"""
        if reason == QSystemTrayIcon.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self.showNormal()
                self.activateWindow()

    def _quitApp(self):
        """退出应用程序"""
        self._do_quit()

    def _open_settings(self):
        try:
            self.showNormal()
            self.activateWindow()
            if hasattr(self, 'settingInterface'):
                self.switchTo(self.settingInterface)
        except Exception:
            pass

    def __setQss(self):
        """ set style sheet """
        # initialize style sheet
        self.setObjectName('mainWindow')
        StyleSheet.MAIN_WINDOW.apply(self)
        self.setMicaEffectEnabled(cfg.get(cfg.micaEnabled))

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if hasattr(self, 'splashScreen'):
            self.splashScreen.resize(self.size())

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

    def _do_quit(self, e=None):
        """执行退出前的清理并退出程序
        e: 可选的 QCloseEvent，用于调用 e.accept()
        """
        try:
            self.hide()
            self.tray_icon.hide()
            QApplication.processEvents()
        except Exception:
            pass

        # 停止运行任务和主题监听

        # 可选地清理日志界面资源
        if hasattr(self, 'logInterface'):
            try:
                self.logInterface.cleanup()
            except Exception:
                pass

        # 如果传入了事件，接受它
        if e is not None:
            try:
                e.accept()
            except Exception:
                pass

        QApplication.quit()

    def closeEvent(self, e):
        """关闭窗口时根据配置执行对应操作"""
        close_action = cfg.get(cfg.close_window_action)

        if close_action == 'ask':
            # 弹出询问对话框
            dialog = MessageBoxCloseWindow(self)
            dialog.exec()

            if dialog.action == 'minimize':
                # 最小化到托盘
                e.ignore()
                self.hide()
                self.tray_icon.showMessage(
                    'FastXGui',
                    '程序已最小化到托盘',
                    QSystemTrayIcon.Information,
                    2000
                )
                # 若用户选择记住，则刷新设置界面以同步显示
                try:
                    if dialog.rememberCheckBox.isChecked():
                        pass
                except Exception:
                    pass
            elif dialog.action == 'close':
                # 关闭程序
                self._do_quit(e)
            else:
                # 用户取消操作（例如点击了 X 按钮）
                e.ignore()
        elif close_action == 'minimize':
            # 直接最小化到托盘
            e.ignore()
            self.hide()
        elif close_action == 'close':
            # 直接关闭程序
            self._do_quit(e)
        else:
            # 默认行为：最小化到托盘
            e.ignore()
            self.hide()
            self.tray_icon.showMessage(
                'FastXGui',
                '程序已最小化到托盘',
                QSystemTrayIcon.Information,
                2000
            )