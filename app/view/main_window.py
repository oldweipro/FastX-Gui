import sys

from loguru import logger
from PySide6.QtCore import QDateTime, QEventLoop, QPoint, QSize, Qt, QTimer, QUrl
from PySide6.QtGui import QAction, QColor, QDesktopServices, QFont, QIcon, QPainter
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QSplashScreen,
    QStatusBar,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    ComboBox,
    Flyout,
    FlyoutAnimationType,
    IndeterminateProgressBar,
    InfoBar,
    InfoBarPosition,
    LineEdit,
    MessageBox,
    MessageBoxBase,
    MSFluentWindow,
    NavigationAvatarWidget,
    NavigationBarPushButton,
    NavigationItemPosition,
    ProgressBar,
    PushButton,
    SearchLineEdit,
    SplashScreen,
    SpinBox,
    SplitFluentWindow,
    SubtitleLabel,
    SystemThemeListener,
    SystemTrayMenu,
    Theme,
    TransparentToolButton,
    isDarkTheme,
    qrouter,
    setFont,
    setTheme,
    toggleTheme,
)
from qfluentwidgets import (
    FluentIcon as FIF,
)

from app.components.messagebox_custom import MessageBoxCloseWindow, MessageBoxSupport
from app.common import resource
from app.common.background_manager import get_background_manager
from app.common.config import cfg
from app.common.icon import Icon, UIcon, FIcon
from app.common.setting import APPLY_NAME, VERSION
from app.common.signal_bus import signalBus
from app.common.style_sheet import StyleSheet
from app.common.translator import Translator
from app.common.license_service import get_license_service
from app.components.custom_titlebar import CustomTitleBar, CustomTitleBar1
from app.view.app_interface import AppInterface
from app.view.floating_window import LevitationWindow
from app.view.floating_window.process_center import ProgressCenter
from app.view.func_interface import FuncInterface
from app.view.home_interface import HomeInterface
from app.view.library_interface import LibraryViewInterface
from app.view.log_interface import LoguruInterface, QTextEditLogger
from app.view.setting_interface import SettingInterface
from app.view.tool_interface import ToolsInterface
from app.view.plugin_interface import PluginInterface
from app.view.app_interface.database import init_db


class SimpleUserInfoDialog(MessageBoxBase):
    """用户信息对话框 - 包含隐藏入口"""

    # 隐藏入口触发计数
    _title_click_count = 0
    _last_click_time = 0
    # 管理员邮箱（硬编码，不可通过配置篡改）
    ADMIN_EMAIL = "919740574@qq.com"

    def __init__(self, parent=None):
        super().__init__(parent)

        # 获取授权信息
        self._license_service = get_license_service()
        self._license_info = self._license_service.get_license_info()
        self._machine_code = self._license_service.get_machine_code()

        # 标题（可点击触发隐藏入口）
        self.titleLabel = SubtitleLabel(self.tr("User Info"), self)
        self.titleLabel.setCursor(Qt.PointingHandCursor)
        self.titleLabel.mousePressEvent = self._on_title_clicked

        # 状态信息
        if self._license_info and self._license_info.is_valid:
            status_text = self.tr("Activated")
            status_style = "color: #4caf50; font-weight: bold;"
            if self._license_info.is_permanent:
                license_type = self.tr("Permanent License")
                expire_text = self.tr("Permanent")
            else:
                license_type = f"{self._license_info.duration_days} " + self.tr("days")
                expire_text = f"{self._license_info.end_date} ({self._license_info.days_remaining} " + self.tr("days remaining") + ")"
        else:
            status_text = self.tr("Not Activated")
            status_style = "color: #f44336; font-weight: bold;"
            license_type = "-"
            expire_text = "-"

        # 使用简单的表格布局
        info_widget = QWidget(self)
        info_layout = QVBoxLayout(info_widget)
        info_layout.setSpacing(8)
        info_layout.setContentsMargins(0, 0, 0, 0)

        # 状态行
        status_layout = QHBoxLayout()
        status_label = BodyLabel(self.tr("License Status:"), info_widget)
        status_value = BodyLabel(status_text, info_widget)
        status_value.setStyleSheet(status_style)
        status_layout.addWidget(status_label)
        status_layout.addStretch()
        status_layout.addWidget(status_value)
        info_layout.addLayout(status_layout)

        # 分隔线
        info_layout.addSpacing(5)

        # 邮箱
        email_layout = QHBoxLayout()
        email_layout.addWidget(BodyLabel(self.tr("Licensed Email:"), info_widget))
        email_layout.addStretch()
        email_layout.addWidget(BodyLabel(self._license_info.email if self._license_info else "-", info_widget))
        info_layout.addLayout(email_layout)

        # 授权类型
        type_layout = QHBoxLayout()
        type_layout.addWidget(BodyLabel(self.tr("License Type:"), info_widget))
        type_layout.addStretch()
        type_layout.addWidget(BodyLabel(license_type, info_widget))
        info_layout.addLayout(type_layout)

        # 起始日期
        start_layout = QHBoxLayout()
        start_layout.addWidget(BodyLabel(self.tr("License Start:"), info_widget))
        start_layout.addStretch()
        start_layout.addWidget(BodyLabel(self._license_info.start_date if self._license_info else "-", info_widget))
        info_layout.addLayout(start_layout)

        # 到期时间
        expire_layout = QHBoxLayout()
        expire_layout.addWidget(BodyLabel(self.tr("Expiration Date:"), info_widget))
        expire_layout.addStretch()
        expire_layout.addWidget(BodyLabel(expire_text, info_widget))
        info_layout.addLayout(expire_layout)

        # 分隔线
        info_layout.addSpacing(5)

        # 机器码
        machine_layout = QHBoxLayout()
        machine_layout.addWidget(BodyLabel(self.tr("Machine Code:"), info_widget))
        machine_layout.addStretch()
        machine_label = BodyLabel(self._machine_code, info_widget)
        machine_label.setStyleSheet("font-family: Consolas, Monaco, monospace; font-size: 12px;")
        machine_layout.addWidget(machine_label)
        info_layout.addLayout(machine_layout)

        # 版本
        version_layout = QHBoxLayout()
        version_layout.addWidget(BodyLabel(self.tr("Software Version:"), info_widget))
        version_layout.addStretch()
        version_layout.addWidget(BodyLabel(f"{APPLY_NAME} {VERSION}", info_widget))
        info_layout.addLayout(version_layout)

        # 添加到布局
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addSpacing(15)
        self.viewLayout.addWidget(info_widget)

        # 按钮
        self.yesButton.setText(self.tr("Confirm"))
        self.cancelButton.setText(self.tr("Copy Machine Code"))

        self.widget.setMinimumWidth(400)
        self.widget.setMaximumWidth(450)

    def _on_title_clicked(self, event):
        """隐藏入口：快速连续点击标题5次触发"""
        import time
        current_time = time.time()

        # 如果超过2秒，重置计数
        if current_time - self._last_click_time > 2:
            self._title_click_count = 0

        self._title_click_count += 1
        self._last_click_time = current_time

        # 连续点击5次触发隐藏功能
        if self._title_click_count >= 5:
            self._title_click_count = 0
            self._try_open_hidden_panel()

    def _try_open_hidden_panel(self):
        """尝试打开隐藏面板 - 需要验证管理员邮箱 + 密码"""
        # 第一步：验证管理员邮箱
        current_email = self._license_info.email if self._license_info else ""
        
        if current_email.lower() != self.ADMIN_EMAIL.lower():
            InfoBar.warning(
                self.tr("Access Denied"),
                self.tr("权限不足"),
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self.window()
            )
            self._license_service.add_audit_log(
                "admin_access_denied", current_email, self._machine_code, "非管理员邮箱尝试访问"
            )
            return
        
        # 第二步：检查是否有有效的管理员会话
        if self._license_service.validate_admin_session():
            dialog = LicenseGeneratorDialog(self)
            dialog.exec()
            return
        
        # 第三步：检查是否已设置管理员密码
        if not self._license_service.has_admin_password():
            # 首次使用，显示密码设置对话框
            dialog = AdminPasswordSetupDialog(self)
            if dialog.exec():
                # 密码设置成功，创建会话并打开生成器
                self._license_service.create_admin_session()
                self._license_service.add_audit_log(
                    "admin_password_set", current_email, self._machine_code, "首次设置管理员密码"
                )
                dialog = LicenseGeneratorDialog(self)
                dialog.exec()
        else:
            # 需要验证密码
            dialog = AdminPasswordVerifyDialog(self)
            if dialog.exec():
                # 密码验证成功，创建会话并打开生成器
                self._license_service.create_admin_session()
                self._license_service.add_audit_log(
                    "admin_verify_success", current_email, self._machine_code, "管理员密码验证成功"
                )
                dialog = LicenseGeneratorDialog(self)
                dialog.exec()


class AdminPasswordSetupDialog(MessageBoxBase):
    """管理员密码设置对话框（首次使用）"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle(self.tr("Set Admin Password"))
        
        # 标题
        self.titleLabel = SubtitleLabel(self.tr("First Use - Set Admin Password"), self)
        self.titleLabel.setStyleSheet("color: #e74c3c; font-weight: bold;")
        
        # 密码输入
        from qfluentwidgets import PasswordLineEdit
        self.passwordEdit = PasswordLineEdit(self)
        self.passwordEdit.setPlaceholderText(self.tr("Please enter admin password (at least 6 characters)"))
        
        # 确认密码
        self.confirmEdit = PasswordLineEdit(self)
        self.confirmEdit.setPlaceholderText(self.tr("Please enter the password again to confirm"))
        
        # 提示
        self.hintLabel = BodyLabel(self.tr("This password is used to access the license code generator, please keep it safe"), self)
        self.hintLabel.setStyleSheet("color: gray; font-size: 12px;")
        
        # 布局
        from PySide6.QtWidgets import QFormLayout
        formLayout = QFormLayout()
        formLayout.addRow(self.tr("Password:"), self.passwordEdit)
        formLayout.addRow(self.tr("Confirm:"), self.confirmEdit)
        
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addSpacing(15)
        self.viewLayout.addLayout(formLayout)
        self.viewLayout.addSpacing(10)
        self.viewLayout.addWidget(self.hintLabel)
        
        self.yesButton.setText(self.tr("Confirm Setting"))
        self.cancelButton.setText(self.tr("Cancel"))
        
        self.widget.setMinimumWidth(400)
    
    def validate(self) -> bool:
        """验证输入"""
        password = self.passwordEdit.text()
        confirm = self.confirmEdit.text()
        
        if len(password) < 6:
            InfoBar.warning(
                self.tr("Warning"),
                self.tr("Password must be at least 6 characters"),
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return False
        
        if password != confirm:
            InfoBar.warning(
                self.tr("Warning"),
                self.tr("The two passwords entered do not match"),
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return False
        
        return True
    
    def exec(self):
        """执行对话框"""
        result = super().exec()
        if result:
            if not self.validate():
                return 0
            # 保存密码
            if self._license_service.set_admin_password(self.passwordEdit.text()):
                InfoBar.success(
                    self.tr("Success"),
                    self.tr("Admin password set successfully"),
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
                return 1
            else:
                InfoBar.error(
                    self.tr("Error"),
                    self.tr("Failed to set password"),
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
                return 0
        return 0
    
    @property
    def _license_service(self):
        return get_license_service()


class AdminPasswordVerifyDialog(MessageBoxBase):
    """管理员密码验证对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle(self.tr("Admin Verification"))
        
        # 标题
        self.titleLabel = SubtitleLabel(self.tr("Please enter admin password"), self)
        self.titleLabel.setStyleSheet("color: #e74c3c; font-weight: bold;")
        
        # 密码输入
        from qfluentwidgets import PasswordLineEdit
        self.passwordEdit = PasswordLineEdit(self)
        self.passwordEdit.setPlaceholderText(self.tr("Please enter admin password"))
        
        # 布局
        from PySide6.QtWidgets import QFormLayout
        formLayout = QFormLayout()
        formLayout.addRow(self.tr("Password:"), self.passwordEdit)
        
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addSpacing(15)
        self.viewLayout.addLayout(formLayout)
        
        self.yesButton.setText(self.tr("Verify"))
        self.cancelButton.setText(self.tr("Cancel"))
        
        self.widget.setMinimumWidth(350)
    
    def exec(self):
        """执行对话框"""
        result = super().exec()
        if result:
            password = self.passwordEdit.text()
            if self._license_service.verify_admin_password(password):
                return 1
            else:
                InfoBar.error(
                    self.tr("Error"),
                    self.tr("Incorrect password"),
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
                self._license_service.add_audit_log(
                    "admin_verify_failed", "", self._license_service.get_machine_code(), "管理员密码验证失败"
                )
                return 0
        return 0
    
    @property
    def _license_service(self):
        return get_license_service()


class LicenseGeneratorDialog(MessageBoxBase):
    """隐藏的授权码生成器对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle(self.tr("License Code Generator"))
        
        # 标题
        self.titleLabel = SubtitleLabel(self.tr("License Code Generator (Internal Tool)"), self)
        self.titleLabel.setStyleSheet("color: #e74c3c; font-weight: bold;")
        
        # 邮箱输入
        self.emailEdit = LineEdit(self)
        self.emailEdit.setPlaceholderText(self.tr("Enter user email"))
        
        # 机器码输入
        self.machineCodeEdit = LineEdit(self)
        self.machineCodeEdit.setPlaceholderText(self.tr("Enter machine code (leave blank for general license)"))
        
        # 授权类型
        self.licenseTypeCombo = ComboBox(self)
        self.licenseTypeCombo.addItems([self.tr("Time-limited License"), self.tr("Permanent License")])
        self.licenseTypeCombo.currentIndexChanged.connect(self._on_type_changed)
        
        # 天数输入
        self.daysSpin = SpinBox(self)
        self.daysSpin.setRange(1, 9999)
        self.daysSpin.setValue(365)
        
        # 起始日期
        from PySide6.QtWidgets import QDateEdit
        from PySide6.QtCore import QDate
        self.startDateEdit = QDateEdit(self)
        self.startDateEdit.setCalendarPopup(True)
        self.startDateEdit.setDate(QDate.currentDate())
        self.startDateEdit.setDisplayFormat("yyyy-MM-dd")
        
        # 生成按钮
        self.generateBtn = PushButton(self.tr("Generate License Code"), self)
        self.generateBtn.clicked.connect(self._generate_license)
        
        # 结果显示
        self.resultEdit = LineEdit(self)
        self.resultEdit.setPlaceholderText(self.tr("Generated license code will be displayed here"))
        self.resultEdit.setReadOnly(True)
        
        # 复制按钮
        self.copyBtn = PushButton(self.tr("Copy"), self)
        self.copyBtn.clicked.connect(self._copy_result)
        
        # 布局
        from PySide6.QtWidgets import QFormLayout
        formLayout = QFormLayout()
        formLayout.addRow(self.tr("Email:"), self.emailEdit)
        formLayout.addRow(self.tr("Machine Code:"), self.machineCodeEdit)
        formLayout.addRow(self.tr("License Type:"), self.licenseTypeCombo)
        formLayout.addRow(self.tr("Start Date:"), self.startDateEdit)
        formLayout.addRow(self.tr("License Days:"), self.daysSpin)
        
        resultLayout = QHBoxLayout()
        resultLayout.addWidget(self.resultEdit, 1)
        resultLayout.addWidget(self.copyBtn)
        formLayout.addRow(self.tr("License Code:"), resultLayout)
        
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addSpacing(15)
        self.viewLayout.addLayout(formLayout)
        self.viewLayout.addSpacing(10)
        self.viewLayout.addWidget(self.generateBtn)
        
        self.yesButton.setText(self.tr("Close"))
        self.cancelButton.hide()
        
        self.widget.setMinimumWidth(500)
    
    def _on_type_changed(self, index):
        """授权类型改变"""
        self.daysSpin.setEnabled(index == 0)  # 限时授权才启用天数输入
        if index == 1:  # 永久授权
            self.daysSpin.setValue(0)
    
    def _generate_license(self):
        """生成授权码"""
        import hashlib
        import hmac
        import base64
        import json
        import secrets
        from datetime import datetime
        
        email = self.emailEdit.text().strip()
        if not email:
            InfoBar.warning(
                self.tr("Warning"),
                self.tr("Please enter email"),
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return
        
        machine_code = self.machineCodeEdit.text().strip() or "GENERAL"
        duration_days = 0 if self.licenseTypeCombo.currentIndex() == 1 else self.daysSpin.value()
        start_date = self.startDateEdit.date().toString("yyyy-MM-dd")
        
        # 密钥
        SECRET_KEY = b"FastX-Gui-Secret-Key-2024-v1.0"
        
        # Header
        header = {"alg": "HS256", "typ": "FXG"}
        
        # Payload
        payload = {
            "email": email.lower(),
            "machine_code": machine_code,
            "salt": secrets.token_hex(8),
            "start_date": start_date,
            "duration_days": duration_days,
            "timestamp": datetime.now().isoformat(),
            "version": "1.0"
        }
        
        # 编码
        header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
        payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
        
        # 签名
        message = f"{header_b64}.{payload_b64}"
        signature = hmac.new(SECRET_KEY, message.encode(), hashlib.sha256).digest()
        signature_b64 = base64.urlsafe_b64encode(signature).decode().rstrip("=")
        
        # 组合
        license_code = f"{header_b64}.{payload_b64}.{signature_b64}"
        self.resultEdit.setText(license_code)
        
        # 记录审计日志
        license_service = get_license_service()
        license_type = self.tr("Permanent License") if duration_days == 0 else self.tr("{0} days").format(duration_days)
        license_service.add_audit_log(
            "generate_license",
            email,
            machine_code,
            f"类型: {license_type}, 起始: {start_date}"
        )
    
    def _copy_result(self):
        """复制授权码"""
        text = self.resultEdit.text()
        if text:
            QApplication.clipboard().setText(text)
            InfoBar.success(
                self.tr("Copied"),
                self.tr("License code copied"),
                position=InfoBarPosition.TOP,
                duration=1500,
                parent=self
            )

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
        # 初始化数据库
        init_db()
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
        def log_sink(message, format: bool = False):
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
            level=log_level,
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
        def log_sink(message, format: bool = False):
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
            level=new_log_level,
        )

        # 打印日志等级变更信息
        logger.critical(f"日志等级已变更为: {new_log_level}")

    def _initWindow(self):
        # create splash screen
        self.splashScreen = SplashScreen(self.windowIcon(), self)
        self.splashScreen.setIconSize(QSize(106, 106))
        self.splashScreen.raise_()

        # 任务中心
        self.progressCenterFlyout = None
        self.progressCenter = ProgressCenter(self)
        self.progressCenterButton = TransparentToolButton(UIcon.get('ic_fluent_list_20_regular'), self)
        self.progressCenterButton.setFixedSize(46, 32)
        self.progressCenterButton.clicked.connect(lambda: self.showProgressCenter(FlyoutAnimationType.DROP_DOWN))

        # 主题切换按钮
        self.themeButton = TransparentToolButton(FIF.CONSTRACT, self)
        self.themeButton.setFixedSize(46, 32)
        self.themeButton.setToolTip(self.tr("Toggle theme"))
        self.themeButton.clicked.connect(lambda: toggleTheme(True))

        # 将主题按钮和任务中心按钮插入到标题栏（先插入右侧的，再插入左侧的，避免索引变化问题）
        min_btn_index = self.titleBar.hBoxLayout.indexOf(self.titleBar.minBtn)
        self.titleBar.hBoxLayout.insertWidget(min_btn_index, self.progressCenterButton, 0, Qt.AlignRight)
        # 重新获取索引，因为布局已变化
        min_btn_index = self.titleBar.hBoxLayout.indexOf(self.titleBar.minBtn)
        self.titleBar.hBoxLayout.insertWidget(min_btn_index, self.themeButton, 0, Qt.AlignRight)

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
        self.setWindowIcon(QIcon(":/app/images/png/logo1.png"))
        self.setWindowTitle(f"{APPLY_NAME} {VERSION}")
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
        # 插件管理界面
        # with self.safe_block(default=None, error_msg=self.tr("Create Plugin interface")):
        self.pluginInterface = PluginInterface(self)
        with self.safe_block(default=None, error_msg=self.tr("Create Library interface")):
            self.libraryInterface = LibraryViewInterface(self)
        with self.safe_block(default=None, error_msg=self.tr("Create Settings interface")):
            self.settingInterface = SettingInterface(self)

    def _connectSignalToSlot(self):
        signalBus.micaEnableChanged.connect(self.setMicaEffectEnabled)
        signalBus.switchToSettingGroup.connect(self.switchToSetting)
        signalBus.switchToExpandGroup.connect(self.switchToSetting)
        signalBus.showMainWindow.connect(self._on_show_main_window)  # 连接显示主窗口信号
        self.loguru_interface.settingsButton.clicked.connect(
            lambda: signalBus.switchToSettingGroup.emit(self.settingInterface.appGroup)
        )
        # 启动时检查更新（由设置界面的 checkUpdateAtStartUp 配置项控制）
        self.settingInterface.checkUpdateOnStartup()

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
            routeKey="userCard",
            avatar=":/app/images/png/shoko.png",
            title="FastXTeam/MG",
            subtitle="wanqiang.liu@fastxteam.com",
            onClick=self.__showMessageBox,
            position=pos,
            aboveMenuButton=False,  # place below the expand/collapse button
        )
        with self.safe_block(
            default=None,
            error_msg=self.tr("Load Home interface to left route"),
        ):
            self.addSubInterface(
                self.homeInterface,
                FIF.HOME,
                self.tr("Home"),
                pos,
                isTransparent=False,
            )

        with self.safe_block(default=None, error_msg=self.tr("Load App interface to left route")):
            self.addSubInterface(
                self.appInterface,
                FIF.APPLICATION,
                self.tr("App"),
                pos,
                isTransparent=False,
            )
        self.navigationInterface.addSeparator()

        # 滾動工作區
        pos = NavigationItemPosition.SCROLL
        with self.safe_block(
            default=None,
            error_msg=self.tr("Load Library interface to left route"),
        ):
            self.addSubInterface(
                self.libraryInterface,
                FIF.BOOK_SHELF,
                self.tr("Library"),
                pos,
                isTransparent=False,
            )

        with self.safe_block(
            default=None,
            error_msg=self.tr("Load Func interface to left route"),
        ):
            self.addSubInterface(
                self.funcInterface,
                FIF.BRIGHTNESS,
                self.tr("FastRte"),
                pos,
                isTransparent=True,
            )

        with self.safe_block(
            default=None,
            error_msg=self.tr("Load Tools interface to left route"),
        ):
            self.addSubInterface(
                self.toolInterface,
                FIF.DEVELOPER_TOOLS,
                self.tr("FastPackage"),
                pos,
                isTransparent=False,
            )

        # 插件管理
        # with self.safe_block(
        #     default=None,
        #     error_msg=self.tr("Load Plugin interface to left route"),
        # ):
        self.addSubInterface(
            self.pluginInterface,
            FIcon.APP_STORE,
            self.tr("Plugins"),
            pos,
            isTransparent=False,
        )

        # 底部功能区
        pos = NavigationItemPosition.BOTTOM
        # add custom widget to bottom
        self.navigationInterface.addItem(
            routeKey="sponsor",
            icon=FIF.HEART,
            text=self.tr("sponsor"),
            onClick=lambda: MessageBoxSupport(
                "支持作者🥰",
                "此程序为免费开源项目，如果你付了钱请立刻退款\n如果喜欢本项目，可以微信赞赏送作者一杯咖啡☕\n您的支持就是作者开发和维护项目的动力🚀",
                ":/app/images/jpg/sponsor.jpg",
                self,
            ).exec(),
            selectable=False,
            tooltip=self.tr("sponsor this tools"),
            position=pos,
        )
        with self.safe_block(default=None, error_msg=self.tr("Load Log interface to left route")):
            self.addSubInterface(
                self.loguru_interface,
                Icon.LOGS,
                self.tr("Logs"),
                pos,
                isTransparent=False,
            )

        with self.safe_block(
            default=None,
            error_msg=self.tr("Load Settings interface to left route"),
        ):
            self.addSubInterface(
                self.settingInterface,
                FIF.SETTING,
                self.tr("Settings"),
                pos,
                isTransparent=False,
            )

        with self.safe_block(
            default=None,
            error_msg=self.tr("Activate Home as default selection"),
        ):
            self.navigationInterface.setCurrentItem(self.homeInterface.objectName())

        self.splashScreen.finish()

    def _on_log_clicked(self):
        self.text_logger._clean_trailing_empty_lines()
        self.text_logger.scroll_to_bottom(force=True)

    def __showMessageBox(self):
        """显示用户信息对话框"""
        dialog = SimpleUserInfoDialog(self)
        result = dialog.exec()
        
        # 如果点击了取消按钮（复制机器码）
        if result == 0:  # 0 表示取消按钮
            machine_code = get_license_service().get_machine_code()
            QApplication.clipboard().setText(machine_code)
            
            InfoBar.success(
                self.tr("Copied"),
                self.tr("Machine code copied to clipboard"),
                position=InfoBarPosition.TOP,
                duration=1500,
                parent=self,
            )

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
        self.tray_icon.setIcon(QIcon(":/app/images/png/logo1.png"))
        self.tray_icon.setToolTip(f"{APPLY_NAME} {VERSION}")

        # 创建托盘菜单
        tray_menu = SystemTrayMenu(parent=self)
        tray_menu.aboutToShow.connect(self._on_tray_menu_about_to_show)

        # 显示主界面
        show_action = QAction(self.tr("Show main window"), self)
        show_action.triggered.connect(self.showNormal)
        show_action.triggered.connect(self.activateWindow)
        tray_menu.addAction(show_action)

        # 显示/隐藏悬浮窗
        self.floating_window_action = QAction(self.tr("Show floating window"), self)
        self.floating_window_action.setCheckable(True)

        # 根据浮窗当前状态设置菜单项
        if hasattr(self, "floatingWindow") and self.floatingWindow is not None and self.floatingWindow.isVisible():
            self.floating_window_action.setChecked(True)
            self.floating_window_action.setText(self.tr("Hide floating window"))
        else:
            self.floating_window_action.setChecked(False)
            self.floating_window_action.setText(self.tr("Show floating window"))

        self.floating_window_action.triggered.connect(self._toggle_floating_window)
        tray_menu.addAction(self.floating_window_action)

        tray_menu.addSeparator()
        # 打开设置界面
        setting_action = QAction(self.tr("Settings"), self)
        setting_action.triggered.connect(self._open_settings)
        tray_menu.addAction(setting_action)
        # 退出程序
        quit_action = QAction(self.tr("Exit"), self)
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
            if hasattr(self, "settingInterface"):
                self.switchTo(self.settingInterface)
        except Exception:
            pass

    def _toggle_floating_window(self, checked):
        """切换浮窗显示状态，并同步更新配置"""
        if not hasattr(self, "floatingWindow") or self.floatingWindow is None:
            logger.warning("浮窗未初始化")
            return

        # 更新配置：同步浮窗开关状态
        cfg.set(cfg.startupDisplayFloatingWindow, checked)

        if checked:
            self.floatingWindow.show()
            self.floating_window_action.setText(self.tr("Hide floating window"))
        else:
            self.floatingWindow.hide()
            self.floating_window_action.setText(self.tr("Show floating window"))

    def _on_floating_window_visibility_changed(self, visible):
        """浮窗可见性变更事件处理"""
        # 同步菜单项状态（如果托盘菜单已创建）
        if not hasattr(self, "floating_window_action"):
            # 托盘菜单还未创建，跳过
            return

        self.floating_window_action.setChecked(visible)
        if visible:
            self.floating_window_action.setText(self.tr("Hide floating window"))
        else:
            self.floating_window_action.setText(self.tr("Show floating window"))

    def _setQss(self):
        """set style sheet"""
        # initialize style sheet
        self.setObjectName("mainWindow")
        StyleSheet.MAIN_WINDOW.apply(self)
        self.setMicaEffectEnabled(cfg.get(cfg.micaEnabled))

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if hasattr(self, "splashScreen"):
            self.splashScreen.resize(self.size())

    def switchToSetting(self, settingGroup):
        """switch to sample"""
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
        if hasattr(self, "themeListener"):
            try:
                # 停止主题监听器线程
                self.themeListener.stop()
            except Exception:
                pass

        # 清理浮窗资源
        if hasattr(self, "floatingWindow"):
            try:
                fw = self.floatingWindow
                # 停止所有定时器
                if hasattr(fw, "_edge_detect_timer"):
                    fw._edge_detect_timer.stop()
                if hasattr(fw, "_retract_timer"):
                    fw._retract_timer.stop()
                if hasattr(fw, "_drag_timer"):
                    fw._drag_timer.stop()
                fw.close()
            except Exception:
                pass

        # 清理背景管理器缓存
        if hasattr(self, "backgroundManager"):
            try:
                self.backgroundManager.clear_cache()
            except Exception:
                pass

        # 清理 progressCenterFlyout
        if hasattr(self, "progressCenterFlyout") and self.progressCenterFlyout:
            try:
                self.progressCenterFlyout.close()
                self.progressCenterFlyout.deleteLater()
                self.progressCenterFlyout = None
            except Exception:
                pass

        # 清理日志界面资源
        if hasattr(self, "text_logger"):
            try:
                self.text_logger.close()
            except Exception:
                pass

        if hasattr(self, "loguru_interface"):
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
        close_action = cfg.get(cfg.closeWindowAction)

        if close_action == "ask":
            # 弹出询问对话框
            dialog = MessageBoxCloseWindow(self)
            dialog.exec()

            if dialog.action == "minimize":
                # 最小化到托盘
                e.ignore()
                self.hide()
                self.tray_icon.showMessage(
                    f"{APPLY_NAME}",
                    self.tr("Application minimized to tray"),
                    QSystemTrayIcon.Information,
                    2000,
                )
                # 若用户选择记住，则刷新设置界面以同步显示
                try:
                    if dialog.rememberCheckBox.isChecked():
                        pass
                except Exception:
                    pass
            elif dialog.action == "close":
                # 关闭程序
                self._do_quit(e)
            else:
                # 用户取消操作（例如点击了 X 按钮）
                e.ignore()
        elif close_action == "minimize":
            # 直接最小化到托盘
            e.ignore()
            self.hide()
        elif close_action == "close":
            # 直接关闭程序
            self._do_quit(e)
        else:
            # 默认行为：最小化到托盘
            e.ignore()
            self.hide()
            self.tray_icon.showMessage(
                f"{APPLY_NAME}",
                self.tr("Application minimized to tray"),
                QSystemTrayIcon.Information,
                2000,
            )

    def paintEvent(self, e):
        """Paint event - draw background image if enabled"""
        super().paintEvent(e)

        # Draw background image if enabled
        if hasattr(self, "backgroundManager") and self.backgroundManager.is_background_enabled():
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

    def showProgressCenter(self, aniType=FlyoutAnimationType.DROP_DOWN):
        if self.progressCenterFlyout is None:
            self.progressCenterFlyout = Flyout.make(
                self.progressCenter,
                self.progressCenterButton,
                self,
                aniType=aniType,
                isDeleteOnClose=False,
            )
        else:
            self.progressCenterFlyout.close()
            # 注：使用deleteLater会导致ToolTip被删除，进而报错，并且此处有内存泄露
            del self.progressCenterFlyout
            self.progressCenterFlyout = Flyout.make(
                self.progressCenter,
                self.progressCenterButton,
                self,
                aniType=aniType,
                isDeleteOnClose=False,
            )
