# coding:utf-8
import sys
from loguru import logger
from PyQt5.QtCore import Qt, QUrl, QSize, QEventLoop, QTimer, QDateTime, QPoint
from PyQt5.QtGui import QIcon, QDesktopServices, QFont, QColor, QPainter
from PyQt5.QtWidgets import QApplication, QWidget, QHBoxLayout, QVBoxLayout, QSplashScreen, QLabel, QStatusBar, QFrame, \
    QSystemTrayIcon, QAction, QDesktopWidget, QPlainTextEdit
from PyQt5.uic.properties import QtCore
from qfluentwidgets import (NavigationItemPosition, MessageBox, setTheme, Theme, MSFluentWindow, isDarkTheme,
                            NavigationAvatarWidget, SearchLineEdit, qrouter, SubtitleLabel, setFont, SplashScreen,
                            IndeterminateProgressBar, ProgressBar, PushButton, FluentIcon as FIF, InfoBar,
                            InfoBarPosition, SystemTrayMenu, NavigationBarPushButton, SystemThemeListener,
                            SplitFluentWindow)

from app.view.log_interface import QTextEditLogger, LoguruInterface
from app.view.home_interface import HomeInterface
from app.view.setting_interface import SettingInterface
from app.view.app_interface import AppInterface
from app.view.func_interface import FuncInterface
from app.view.library_interface import LibraryViewInterface
from app.view.tool_interface import ToolsInterface
from app.view.floating_window import LevitationWindow

from app.common.icon import Icon, UnicodeIcon
from app.common.translator import Translator
from app.common.style_sheet import StyleSheet
from app.common.signal_bus import signalBus
from app.common.config import cfg
from app.common import resource
from app.common.setting import VERSION, APPLY_NAME
from app.common.background_manager import get_background_manager
from app.card.messagebox_custom import MessageBoxCloseWindow, MessageBoxSupport
from app.components.custom_titlebar import CustomTitleBar1, CustomTitleBar


class MainWindow(SplitFluentWindow):
    def __init__(self):
        # 先调用父类初始化
        super().__init__()
        self._initWindow()
        self._init_services()
        self._initInterface()
        # initialize floating window
        self._initFloatingWindow()
        # add items to navigation interface
        self._initNavigation()
        # add systemTray Menu
        self._initSystemTray()
        # 创建信号连接到槽
        self._connectSignalToSlot()
        self._setQss()

    @staticmethod
    def safe_block(default=None, error_msg=""):
        """安全执行代码块的上下文管理器"""
        class SafeBlock:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                if exc_type is not None:
                    logger.critical(f"{error_msg}失败: {exc_val}" if error_msg else f"操作失败: {exc_val}")
                    return True  # 抑制异常
                return False
        return SafeBlock()

    def _init_services(self):
        # 創建主題監聽器
        self.themeListener = SystemThemeListener(self)
        # 初始化背景圖片管理器
        self.backgroundManager = get_background_manager(cfg)
        # 初始化日志系统
        self._setup_log_viewer()
        # ComponentUsageTracker()  # 日志使用情况监督
        # ComponentScanner()       # 日志实时监控服务
        # 開始主題監聽
        self.themeListener.start()

    def _setup_log_viewer(self):
        # 先清除所有现有的日志处理器
        logger.remove()
        
        # 创建LoguruInterface和QTextEditLogger
        self.loguru_interface = LoguruInterface(self)
        self.text_logger = QTextEditLogger(self.loguru_interface.log_viewer, max_lines=1000)
        # 连接信号
        self.text_logger.new_log_signal.connect(self.loguru_interface.on_new_log)
        
        # 添加自定义处理器
        def log_sink(message, format : bool=False):
            """将loguru消息转发到Qt界面"""
            try:
                if format:
                    # 获取格式化后的消息
                    self.text_logger.write(message.record["message"])
                else:
                    # 写入Qt日志器
                    self.text_logger.write(message)
            except Exception:
                pass
        
        # 从配置文件中读取日志等级
        log_level = cfg.get(cfg.logLevel)
        
        # 配置loguru使用我们的sink()
        self.log_handler_id = logger.add(
            log_sink,
            format="{time:YYYY/MM/DD HH:mm:ss} | {level:8} | {file}:{line} {message}",
            level=log_level
        )
        
        # 连接日志等级配置变化信号
        cfg.logLevel.valueChanged.connect(self.on_log_level_changed)
        
        # 测试日志
        logger.trace("日志系统初始化完成")
        logger.debug("调试日志测试")
        logger.info("信息日志测试")
    
    def on_log_level_changed(self):
        """处理日志等级配置变化"""
        # 从配置文件中读取新的日志等级
        new_log_level = cfg.get(cfg.logLevel)
        
        # 更新loguru的日志等级
        logger.remove(self.log_handler_id)
        
        # 重新添加处理器
        def log_sink(message, format : bool=False):
            """将loguru消息转发到Qt界面"""
            try:
                if format:
                    # 获取格式化后的消息
                    self.text_logger.write(message.record["message"])
                else:
                    # 写入Qt日志器
                    self.text_logger.write(message)
            except Exception:
                pass
        
        self.log_handler_id = logger.add(
            log_sink,
            format="{time:YYYY/MM/DD hh:mm:ss} | {level:8} | {file}:{line} {message}",
            level=new_log_level
        )
        
        # 打印日志等级变更信息
        logger.critical(f"日志等级已变更为: {new_log_level}")

    def _initWindow(self):
        # create splash screen
        self.splashScreen = SplashScreen(self.windowIcon(), self)
        self.splashScreen.setIconSize(QSize(106, 106))
        self.splashScreen.raise_()

        # 桌面可用区域
        desktop = QApplication.primaryScreen().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.window_width = int(0.8 * w)
        self.window_height = int(0.85 * h)

        # 获取窗口大小模式配置
        if cfg.get(cfg.windowSizeMode) == "auto":
            # self.setAttribute(Qt.WA_TranslucentBackground)
            # 自适应分辨率模式
            self.resize(self.window_width, self.window_height)
            self.setResizeEnabled(True)
            self.titleBar.maxBtn.show()
            self.titleBar.setDoubleClickEnabled(True)
            self.navigationInterface.setExpandWidth(275)
        else:
            # 固定大小模式
            self.resize(1400, 960)
            # 可以避免導航欄展開往右推動界面,當前設置是懸浮在内容區上
            self.navigationInterface.setMinimumExpandWidth(2000)
            # 設置是否可以改變大小
            self.setResizeEnabled(False)
            # 是否隱藏最大化菜單
            self.titleBar.maxBtn.hide()
            # 是否禁用雙擊最大化
            self.titleBar.setDoubleClickEnabled(False)
            # 设置自定义标题栏 | 目前有點BUG(暫時保留)
            # self.setTitleBar(CustomTitleBar(self))
            # self.titleBar.raise_()
            # 调整布局边距以适应标题栏高度 | SplitWindows軟件圖標和標題會占據一部分
            # self.hBoxLayout.setContentsMargins(0, 48, 0, 0)
        # 设置图标,标题
        self.setWindowIcon(QIcon(':/app/images/png/logo1.png'))
        self.setWindowTitle(f'{APPLY_NAME} {VERSION}')
        # 初始化位置
        self.move(w // 2 - self.width() // 2, h // 2 - self.height() // 2)
        # 显示窗口
        self.show()
        QApplication.processEvents()

    def _initInterface(self):
        # 创建子界面
        with self.safe_block(default=None, error_msg=self.tr("Create Home interface")):
            self.homeInterface = HomeInterface(self)
        with self.safe_block(default=None, error_msg=self.tr("Create App interface")):
            self.appInterface = AppInterface(self)
        with self.safe_block(default=None, error_msg=self.tr("Create Func interface")):
            self.funcInterface = FuncInterface(self)
        with self.safe_block(default=None, error_msg=self.tr("Create Tools interface")):
            self.toolInterface = ToolsInterface(self)
        with self.safe_block(default=None, error_msg=self.tr("Create Library interface")):
            self.libraryInterface = LibraryViewInterface(self)
        with self.safe_block(default=None, error_msg=self.tr("Create Settings interface")):
            self.settingInterface = SettingInterface(self)


    def _connectSignalToSlot(self):
        signalBus.micaEnableChanged.connect(self.setMicaEffectEnabled)
        signalBus.switchToSettingGroup.connect(self.switchToSetting)
        signalBus.switchToExpandGroup.connect(self.switchToSetting)
        signalBus.showMainWindow.connect(self._on_show_main_window)  # 连接显示主窗口信号
        self.loguru_interface.settingsButton.clicked.connect(lambda: signalBus.switchToSettingGroup.emit(self.settingInterface.appGroup))

    def _initNavigation(self):
        # set sidebar expand width
        # self.navigationInterface.setFixedWidth(70)
        # enable acrylic effect
        self.navigationInterface.setAcrylicEnabled(True)
        # set sidebar expand width
        # self.navigationInterface.setMinimumExpandWidth(120)
        self.navigationInterface.setReturnButtonVisible(False)
        # force sidebar to always expanded state (disable collapsible)
        self.navigationInterface.setCollapsible(True)
        # 導航路由切換滑動特效
        self.navigationInterface.setUpdateIndicatorPosOnCollapseFinished(True)
        # ensure sidebar is expanded
        # self.navigationInterface.expand(useAni=False)

        # 主功能区
        pos = NavigationItemPosition.TOP
        # add user card with custom parameters
        self.userCard = self.navigationInterface.addUserCard(
            routeKey='userCard',
            avatar=':/app/images/png/shoko.png',
            title='FastXTeam/MG',
            subtitle='wanqiang.liu@fastxteam.com',
            onClick=self.__showMessageBox,
            position=pos,
            aboveMenuButton=False  # place below the expand/collapse button
        )
        with self.safe_block(default=None, error_msg=self.tr("Load Home interface to left route")):
            self.addSubInterface(self.homeInterface, FIF.HOME, self.tr("Home"), pos, isTransparent=False)

        with self.safe_block(default=None, error_msg=self.tr("Load App interface to left route")):
            self.addSubInterface(self.appInterface , FIF.APPLICATION, self.tr("App"), pos, isTransparent=False)
        self.navigationInterface.addSeparator()

        # 滾動工作區
        pos = NavigationItemPosition.SCROLL
        with self.safe_block(default=None, error_msg=self.tr("Load Library interface to left route")):
            self.addSubInterface(self.libraryInterface, FIF.BOOK_SHELF, self.tr("Library"), pos, isTransparent=False)

        with self.safe_block(default=None, error_msg=self.tr("Load Func interface to left route")):
            self.addSubInterface(self.funcInterface, FIF.BRIGHTNESS, self.tr("FastRte"), pos, isTransparent=True)

        with self.safe_block(default=None, error_msg=self.tr("Load Tools interface to left route")):
            self.addSubInterface(self.toolInterface, FIF.DEVELOPER_TOOLS, self.tr("FastPackage"), pos, isTransparent=False)

        # 底部功能区
        pos = NavigationItemPosition.BOTTOM
        # add custom widget to bottom
        self.navigationInterface.addItem(
            routeKey='sponsor',
            icon=FIF.HEART,
            text=self.tr('sponsor'),
            onClick=lambda: MessageBoxSupport(
                '支持作者🥰',
                '此程序为免费开源项目，如果你付了钱请立刻退款\n如果喜欢本项目，可以微信赞赏送作者一杯咖啡☕\n您的支持就是作者开发和维护项目的动力🚀',
                ':/app/images/jpg/sponsor.jpg',
                self
            ).exec(),
            selectable=False,
            tooltip=self.tr('sponsor this tools'),
            position=pos
        )
        with self.safe_block(default=None, error_msg=self.tr("Load Log interface to left route")):
            self.addSubInterface(self.loguru_interface, UnicodeIcon.get_icon_by_name("ic_fluent_document_bullet_list_clock_24_regular"), self.tr("Logs"), pos, isTransparent=False)

        with self.safe_block(default=None, error_msg=self.tr("Load Settings interface to left route")):
            self.addSubInterface(self.settingInterface, FIF.SETTING, self.tr('Settings'), pos, isTransparent=False)

        with self.safe_block(default=None, error_msg=self.tr("Activate Home as default selection")):
            self.navigationInterface.setCurrentItem(self.homeInterface.objectName())

        self.splashScreen.finish()

    def _on_log_clicked(self):
        self.text_logger._clean_trailing_empty_lines()
        self.text_logger.scroll_to_bottom(force=True)

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

    def _initFloatingWindow(self):
        """初始化悬浮窗"""
        try:
            self.floatingWindow = LevitationWindow(self)
            
            # 连接浮窗可见性变更信号
            self.floatingWindow.visibilityChanged.connect(self._on_floating_window_visibility_changed)
            
            # 根据配置决定是否显示浮窗（但不设置托盘菜单状态，因为此时还没创建）
            if cfg.get(cfg.startupDisplayFloatingWindow):
                self.floatingWindow.show()
            else:
                self.floatingWindow.hide()
        except Exception as e:
            logger.error(f"浮窗初始化失败: {e}")
            import traceback
            traceback.print_exc()
            # 即使浮窗初始化失败，也不影响主窗口启动
            self.floatingWindow = None

    def _initSystemTray(self):
        """初始化系统托盘"""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(':/app/images/png/logo1.png'))
        self.tray_icon.setToolTip(f'{APPLY_NAME} {VERSION}')

        # 创建托盘菜单
        tray_menu = SystemTrayMenu(parent=self)
        tray_menu.aboutToShow.connect(self._on_tray_menu_about_to_show)

        # 显示主界面
        show_action = QAction(self.tr('Show main window'), self)
        show_action.triggered.connect(self.showNormal)
        show_action.triggered.connect(self.activateWindow)
        tray_menu.addAction(show_action)
        
        # 显示/隐藏悬浮窗
        self.floating_window_action = QAction(self.tr('Show floating window'), self)
        self.floating_window_action.setCheckable(True)
        
        # 根据浮窗当前状态设置菜单项
        if hasattr(self, 'floatingWindow') and self.floatingWindow is not None and self.floatingWindow.isVisible():
            self.floating_window_action.setChecked(True)
            self.floating_window_action.setText(self.tr('Hide floating window'))
        else:
            self.floating_window_action.setChecked(False)
            self.floating_window_action.setText(self.tr('Show floating window'))
            
        self.floating_window_action.triggered.connect(self._toggle_floating_window)
        tray_menu.addAction(self.floating_window_action)
        
        tray_menu.addSeparator()
        # 打开设置界面
        setting_action = QAction(self.tr('Settings'), self)
        setting_action.triggered.connect(self._open_settings)
        tray_menu.addAction(setting_action)
        # 退出程序
        quit_action = QAction(self.tr('Exit'), self)
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
        """切换浮窗显示状态，并同步更新配置"""
        if not hasattr(self, 'floatingWindow') or self.floatingWindow is None:
            logger.warning("浮窗未初始化")
            return
        
        # 更新配置：同步浮窗开关状态
        cfg.set(cfg.startupDisplayFloatingWindow, checked)
        
        if checked:
            self.floatingWindow.show()
            self.floating_window_action.setText(self.tr('Hide floating window'))
        else:
            self.floatingWindow.hide()
            self.floating_window_action.setText(self.tr('Show floating window'))
    
    def _on_floating_window_visibility_changed(self, visible):
        """浮窗可见性变更事件处理"""
        # 同步菜单项状态（如果托盘菜单已创建）
        if not hasattr(self, 'floating_window_action'):
            # 托盘菜单还未创建，跳过
            return
            
        self.floating_window_action.setChecked(visible)
        if visible:
            self.floating_window_action.setText(self.tr('Hide floating window'))
        else:
            self.floating_window_action.setText(self.tr('Show floating window'))

    def _setQss(self):
        """ set style sheet """
        # initialize style sheet
        self.setObjectName('mainWindow')
        StyleSheet.MAIN_WINDOW.apply(self)
        self.setMicaEffectEnabled(cfg.get(cfg.micaEnabled))

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if hasattr(self, 'splashScreen'):
            self.splashScreen.resize(self.size())

    def switchToSetting(self, settingGroup):
        """ switch to sample """
        self.stackedWidget.setCurrentWidget(self.settingInterface, False)
        # 如果settingGroup不为None，则滚动到指定的组
        if settingGroup is not None:
            self.settingInterface.scrollToGroup(settingGroup)
    
    def _on_show_main_window(self):
        """显示主窗口"""
        self.showNormal()
        self.activateWindow()

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
        if hasattr(self, 'themeListener'):
            try:
                # 停止主题监听器线程
                self.themeListener.stop()
            except Exception:
                pass

        # 清理日志界面资源
        if hasattr(self, 'text_logger'):
            try:
                self.text_logger.close()
            except Exception:
                pass

        if hasattr(self, 'loguru_interface'):
            try:
                self.loguru_interface.cleanup()
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
                    f'{APPLY_NAME}',
                    self.tr('Application minimized to tray'),
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
                f'{APPLY_NAME}',
                self.tr('Application minimized to tray'),
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