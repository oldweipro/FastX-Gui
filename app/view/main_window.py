# coding:utf-8
import sys
from PyQt5.QtCore import Qt, QUrl, QSize, QEventLoop, QTimer, QDateTime, QPoint
from PyQt5.QtGui import QIcon, QDesktopServices, QFont, QColor, QPainter
from PyQt5.QtWidgets import QApplication, QWidget, QHBoxLayout, QVBoxLayout, QSplashScreen, QLabel, QStatusBar, QFrame, \
    QSystemTrayIcon, QAction
from qfluentwidgets import (NavigationItemPosition, MessageBox, setTheme, Theme, MSFluentWindow, isDarkTheme,
                            NavigationAvatarWidget, SearchLineEdit, qrouter, SubtitleLabel, setFont, SplashScreen,
                            IndeterminateProgressBar, ProgressBar, PushButton, FluentIcon as FIF, InfoBar,
                            InfoBarPosition, SystemTrayMenu, NavigationBarPushButton, SystemThemeListener,
                            SplitFluentWindow, FluentTitleBarButton)


from app.view.home_interface import HomeInterface
from app.view.setting_interface import SettingInterface
from app.view.app_interface import AppInterface
from app.view.log_interface import LogInterface
from app.view.func_interface import FuncInterface
from app.view.library_interface import LibraryViewInterface
from app.view.tool_interface import ToolsInterface
from app.view.floating_window import LevitationWindow

from app.common.icon import Icon
from app.common.translator import Translator
from app.common.style_sheet import StyleSheet
from app.common.signal_bus import signalBus
from app.common.config import cfg
from app.common import resource
from app.common.setting import VERSION
from app.common.background_manager import get_background_manager
from app.card.messagebox_custom import MessageBoxCloseWindow, MessageBoxSupport
from app.components.custom_titlebar import CustomTitleBar1, CustomTitleBar


class MainWindow(SplitFluentWindow):
    def __init__(self):
        # 先调用父类初始化
        super().__init__()
        self.initWindow()

        # create system theme listener
        self.themeListener = SystemThemeListener(self)

        # create sub interface
        self.__initInterface()

        # initialize background manager
        self.backgroundManager = get_background_manager(cfg)

        # initialize floating window
        self.__initFloatingWindow()

        # set sidebar expand width
        # self.navigationInterface.setFixedWidth(70)
        self.navigationInterface.setAcrylicEnabled(True)                        # enable acrylic effect
        # self.navigationInterface.setMinimumExpandWidth(120)                     # set sidebar expand width
        self.navigationInterface.setReturnButtonVisible(False)                  #
        self.navigationInterface.setCollapsible(True)                           # force sidebar to always expanded state (disable collapsible)
        self.navigationInterface.setUpdateIndicatorPosOnCollapseFinished(True)  #
        # self.navigationInterface.expand(useAni=False)                           # ensure sidebar is expanded

        # 创建信号连接到槽
        self.__connectSignalToSlot()

        # add items to navigation interface
        self.__initNavigation()

        # add systemTray Menu
        self.__initSystemTray()

        # start theme listener
        self.themeListener.start()

    def initWindow(self):
        self.resize(960, 800)
        self.setResizeEnabled(False)
        self.titleBar.maxBtn.hide()
        self.titleBar.setDoubleClickEnabled(False)
        # 设置自定义标题栏
        # self.setTitleBar(CustomTitleBar1(self))
        # self.titleBar.raise_()
        # # 调整布局边距以适应标题栏高度
        # self.hBoxLayout.setContentsMargins(0, 48, 0, 0)
        # 设置图标,标题
        self.setWindowIcon(QIcon(':/app/images/logo-m.png'))
        self.setWindowTitle(f'FastXGui {VERSION}')
        self.__setQss()

        # create splash screen
        self.splashScreen = SplashScreen(self.windowIcon(), self)
        self.splashScreen.setIconSize(QSize(106, 106))
        self.splashScreen.raise_()
        # desktop show
        desktop = QApplication.primaryScreen().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w // 2 - self.width() // 2, h // 2 - self.height() // 2)
        self.show() # ISSUE-FIX: 修复RegisterLogin无法跳转到Main-Window
        QApplication.processEvents()

    def __initInterface(self):
        # 创建子界面
        self.homeInterface = HomeInterface(self)
        self.appInterface = AppInterface(self)
        self.funcInterface = FuncInterface(self)
        self.toolInterface = ToolsInterface(self)
        self.logInterface = LogInterface(self)
        self.libraryInterface = LibraryViewInterface(self)
        self.settingInterface = SettingInterface(self)

    def __connectSignalToSlot(self):
        signalBus.micaEnableChanged.connect(self.setMicaEffectEnabled)

    def __initNavigation(self):
        # add navigation items
        t = Translator()

        pos = NavigationItemPosition.TOP
        # add user card with custom parameters
        self.userCard = self.navigationInterface.addUserCard(
            routeKey='userCard',
            avatar=':/app/images/shoko.png',
            title='FastXTeam/MG',
            subtitle='wanqiang.liu@fastxteam.com',
            onClick=self.__showMessageBox,
            position=pos,
            aboveMenuButton=False  # place below the expand/collapse button
        )
        self.addSubInterface(self.homeInterface, FIF.HOME, self.tr("Home"), pos, isTransparent=False)
        self.addSubInterface(self.appInterface , FIF.APPLICATION, self.tr("App"), pos, isTransparent=False)
        self.navigationInterface.addSeparator()

        pos = NavigationItemPosition.SCROLL
        self.addSubInterface(self.libraryInterface, FIF.BOOK_SHELF, self.tr("Library"), pos, isTransparent=False)
        self.addSubInterface(self.funcInterface, FIF.BRIGHTNESS, self.tr("FastRte"), pos, isTransparent=True)
        self.addSubInterface(self.toolInterface, FIF.DEVELOPER_TOOLS, self.tr("FastPackage"), pos, isTransparent=False)

        pos = NavigationItemPosition.BOTTOM
        self.addSubInterface(self.logInterface, FIF.COMMAND_PROMPT, self.tr("Log"), pos, isTransparent=False)
        # add custom widget to bottom
        self.navigationInterface.addItem(
            routeKey='sponsor',
            icon=FIF.HEART,
            text=self.tr('sponsor'),
            onClick=lambda: MessageBoxSupport(
                '支持作者🥰',
                '此程序为免费开源项目，如果你付了钱请立刻退款\n如果喜欢本项目，可以微信赞赏送作者一杯咖啡☕\n您的支持就是作者开发和维护项目的动力🚀',
                ':/app/images/sponsor.jpg',
                self
            ).exec(),
            selectable=False,
            tooltip=self.tr('sponsor this tools'),
            position=pos
        )
        self.addSubInterface(self.settingInterface, FIF.SETTING, self.tr('Settings'), pos, isTransparent=False)
        self.navigationInterface.setCurrentItem(self.homeInterface.objectName())
        self.splashScreen.finish()

    def __showMessageBox(self):
        w = MessageBox(
            'User Card',
            'This is a navigation user card that displays avatar, title and subtitle.\n\n'
            'Placement:\n'
            '• aboveMenuButton=True: Place above expand/collapse button\n'
            '• aboveMenuButton=False: Place below menu button (default)',
            self
        )
        w.exec_()

    def __initFloatingWindow(self):
        """初始化悬浮窗"""
        self.floatingWindow = LevitationWindow(self)

    def __initSystemTray(self):
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
        
        # 显示/隐藏悬浮窗
        self.floating_window_action = QAction('显示悬浮窗', self)
        self.floating_window_action.setCheckable(True)
        self.floating_window_action.setChecked(False)
        self.floating_window_action.triggered.connect(self._toggle_floating_window)
        tray_menu.addAction(self.floating_window_action)
        
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

    def _toggle_floating_window(self, checked):
        """切换悬浮窗的显示/隐藏状态"""
        if checked:
            self.floatingWindow.show()
            self.floating_window_action.setText('隐藏悬浮窗')
        else:
            self.floatingWindow.hide()
            self.floating_window_action.setText('显示悬浮窗')

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

    def paintEvent(self, e):
        """ Paint event - draw background image if enabled """
        super().paintEvent(e)

        # Draw background image if enabled
        if hasattr(self, 'backgroundManager') and self.backgroundManager.is_background_enabled():
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)

            # Get background pixmap
            window_size = self.size()
            background_pixmap = self.backgroundManager.get_background_pixmap(window_size)

            if background_pixmap and not background_pixmap.isNull():
                # Apply opacity
                opacity = self.backgroundManager.get_background_opacity() / 100.0  # Convert percentage to float
                painter.setOpacity(opacity)

                # Get display mode
                display_mode = self.backgroundManager.get_background_display_mode()

                # Draw based on display mode
                self.__draw_background_by_mode(painter, background_pixmap, window_size, display_mode)

            painter.end()

    def __draw_background_by_mode(self, painter, background_pixmap, window_size, display_mode):
        """Draw background image according to display mode

        Args:
            painter: QPainter instance
            background_pixmap: Background image pixmap
            window_size: Window size
            display_mode: Display mode string
        """
        pixmap_size = background_pixmap.size()

        if display_mode == "Tile":
            # Tile the image across the window
            for x in range(0, window_size.width(), pixmap_size.width()):
                for y in range(0, window_size.height(), pixmap_size.height()):
                    painter.drawPixmap(x, y, background_pixmap)

        elif display_mode == "Original Size":
            # Center the image at original size
            x = max(0, (window_size.width() - pixmap_size.width()) // 2)
            y = max(0, (window_size.height() - pixmap_size.height()) // 2)
            painter.drawPixmap(x, y, background_pixmap)

        else:
            # For "Stretch", "Keep Aspect Ratio", "Fit Window" modes
            # The scaling is already handled in BackgroundManager, just center and draw
            if display_mode == "Fit Window":
                # Center the image that fits within window
                x = max(0, (window_size.width() - pixmap_size.width()) // 2)
                y = max(0, (window_size.height() - pixmap_size.height()) // 2)
            else:
                # For stretch and keep aspect ratio modes, image should fill the window
                x = max(0, (window_size.width() - pixmap_size.width()) // 2)
                y = max(0, (window_size.height() - pixmap_size.height()) // 2)

            painter.drawPixmap(x, y, background_pixmap)