import sys

from PySide6.QtCore import QRect, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QHBoxLayout, QVBoxLayout, QWidget
from qfluentwidgets import (
    BodyLabel,
    CheckBox,
    HyperlinkButton,
    ImageLabel,
    InfoBar,
    InfoBarPosition,
    LineEdit,
    MSFluentTitleBar,
    PasswordLineEdit,
    PrimaryPushButton,
    isDarkTheme,
    setThemeColor,
)

from app.common import resource
from app.common.config import cfg
from app.common.license_service import get_license_service


def isWin11():
    return sys.platform == "win32" and sys.getwindowsversion().build >= 22000


if isWin11():
    from qframelesswindow import AcrylicWindow as Window
else:
    from qframelesswindow import FramelessWindow as Window


class RegisterWindow(Window):
    """Register window"""

    loginSignal = Signal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        setThemeColor("#28afe9")
        self.setTitleBar(MSFluentTitleBar(self))
        self.license_service = get_license_service()
        
        # 预热机器码缓存（避免点击时卡顿）
        self.license_service.get_machine_code()

        self.imageLabel = ImageLabel(":/app/images/jpg/background.jpg", self)
        self.iconLabel = ImageLabel(":/app/images/png/logo.png", self)

        self.emailLabel = BodyLabel(self.tr("Email"), self)
        self.emailLineEdit = LineEdit(self)

        self.activateCodeLabel = BodyLabel(self.tr("Activation Code"))
        self.activateCodeLineEdit = PasswordLineEdit(self)

        self.rememberCheckBox = CheckBox(self.tr("Remember me"), self)

        self.loginButton = PrimaryPushButton(self.tr("Login"), self)
        
        # 获取激活码链接
        self.getActivationCodeLink = HyperlinkButton("", self.tr("Get Activation Code"), self)

        self.hBoxLayout = QHBoxLayout(self)
        self.vBoxLayout = QVBoxLayout()

        self.__initWidgets()

    def __initWidgets(self):
        self.titleBar.maxBtn.hide()
        self.titleBar.setDoubleClickEnabled(False)
        self.rememberCheckBox.setChecked(cfg.get(cfg.rememberMe))

        self.emailLineEdit.setPlaceholderText("example@example.com")
        self.activateCodeLineEdit.setPlaceholderText("Enter your activation code")

        # 优先从授权服务加载已保存的信息
        saved_license = self.license_service.load_license()
        if saved_license:
            saved_code, saved_email = saved_license
            self.emailLineEdit.setText(saved_email)
            self.activateCodeLineEdit.setText(saved_code)
        elif self.rememberCheckBox.isChecked():
            self.emailLineEdit.setText(cfg.get(cfg.email))
            self.activateCodeLineEdit.setText(cfg.get(cfg.activationCode))

        self.__connectSignalToSlot()
        self.__initLayout()

        if isWin11():
            self.windowEffect.setMicaEffect(self.winId(), isDarkTheme())
        else:
            color = QColor(25, 33, 42) if isDarkTheme() else QColor(240, 244, 249)
            self.setStyleSheet(f"RegisterWindow{{background: {color.name()}}}")

        self.setWindowTitle("PyQt-Fluent-Widgets")
        self.setWindowIcon(QIcon(":/app/images/png/logo.png"))
        self.resize(1000, 650)

        if sys.platform == "darwin":
            self.titleBar.minBtn.hide()
            self.titleBar.closeBtn.hide()
            self.setSystemTitleBarButtonVisible(True)
            self.setWindowFlags(
                (self.windowFlags() & ~Qt.WindowFullscreenButtonHint) & ~Qt.WindowMaximizeButtonHint
                | Qt.CustomizeWindowHint
            )

        self.titleBar.titleLabel.setStyleSheet("""
            QLabel{
                background: transparent;
                font: 13px 'Segoe UI', 'Microsoft YaHei', 'PingFang SC';
                padding: 0 4px;
                color: white
            }
        """)

        desktop = QApplication.screens()[0].availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w // 2 - self.width() // 2, h // 2 - self.height() // 2)

        self.titleBar.raise_()

    def __initLayout(self):
        self.imageLabel.scaledToHeight(650)
        self.iconLabel.scaledToHeight(100)

        self.hBoxLayout.addWidget(self.imageLabel)
        self.hBoxLayout.addLayout(self.vBoxLayout)

        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setContentsMargins(20, 0, 20, 0)
        self.vBoxLayout.setSpacing(0)
        self.hBoxLayout.setSpacing(0)

        self.vBoxLayout.addStretch(1)
        self.vBoxLayout.addWidget(self.iconLabel, 0, Qt.AlignmentFlag.AlignHCenter)
        self.vBoxLayout.addSpacing(38)
        self.vBoxLayout.addWidget(self.emailLabel)
        self.vBoxLayout.addSpacing(11)
        self.vBoxLayout.addWidget(self.emailLineEdit)
        self.vBoxLayout.addSpacing(12)
        self.vBoxLayout.addWidget(self.activateCodeLabel)
        self.vBoxLayout.addSpacing(11)
        self.vBoxLayout.addWidget(self.activateCodeLineEdit)
        self.vBoxLayout.addSpacing(12)
        self.vBoxLayout.addWidget(self.rememberCheckBox)
        self.vBoxLayout.addSpacing(15)
        self.vBoxLayout.addWidget(self.loginButton)
        self.vBoxLayout.addSpacing(10)
        self.vBoxLayout.addWidget(self.getActivationCodeLink, 0, Qt.AlignmentFlag.AlignHCenter)
        self.vBoxLayout.addSpacing(30)
        self.vBoxLayout.addStretch(1)

    def __connectSignalToSlot(self):
        self.loginButton.clicked.connect(self._login)
        self.rememberCheckBox.stateChanged.connect(lambda: cfg.set(cfg.rememberMe, self.rememberCheckBox.isChecked()))
        self.getActivationCodeLink.clicked.connect(self._onGetActivationCode)

    def _login(self):
        code = self.activateCodeLineEdit.text().strip()
        email = self.emailLineEdit.text().strip()

        if not email:
            InfoBar.warning(
                self.tr("Email Required"),
                self.tr("Please enter your email address"),
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self.window(),
            )
            return

        if not code:
            InfoBar.warning(
                self.tr("Activation Code Required"),
                self.tr("Please enter your activation code"),
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self.window(),
            )
            return

        # 验证授权码
        is_valid, message = self.license_service.validate_license_code(code, email)
        
        if not is_valid:
            InfoBar.error(
                self.tr("Activation Failed"),
                message,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self.window(),
            )
            return
        
        # 检测时间篡改
        time_ok, time_msg = self.license_service.check_time_tampering()
        if not time_ok:
            InfoBar.error(
                self.tr("Security Check Failed"),
                time_msg,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self.window(),
            )
            return

        # 保存授权
        try:
            self.license_service.save_license(code, email)
        except Exception as e:
            InfoBar.error(
                self.tr("Save Failed"),
                f"Failed to save license: {str(e)}",
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self.window(),
            )
            return

        InfoBar.success(
            self.tr("Success"),
            self.tr("Activation successful!"),
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self.window(),
        )

        if cfg.get(cfg.rememberMe):
            cfg.set(cfg.email, email)
            cfg.set(cfg.activationCode, code)

        self.loginButton.setDisabled(True)
        QTimer.singleShot(1500, self._showMainWindow)

    def _onGetActivationCode(self):
        """点击获取激活码链接，复制机器码到剪贴板"""
        machine_code = self.license_service.get_machine_code()
        
        # 复制机器码到剪贴板
        clipboard = QApplication.clipboard()
        clipboard.setText(machine_code)
        
        InfoBar.success(
            self.tr("Copied"),
            self.tr("Machine code copied! Please send your email and machine code to developer to get activation code."),
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self.window(),
        )

    def _showMainWindow(self):
        self.close()
        setThemeColor("#009faa")

        self.loginSignal.emit()

    def systemTitleBarRect(self, size):
        """Returns the system title bar rect, only works for macOS"""
        return QRect(size.width() - 75, 0, 75, size.height())
