import numpy as np
from PIL import Image
from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QDesktopServices, QImage, QPainter, QPainterPath, QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    ComboBox,
    GroupHeaderCardWidget,
    HyperlinkButton,
    IconWidget,
    ImageLabel,
    InfoBarIcon,
    PrimaryPushButton,
    PushButton,
    SpinBox,
    SwitchButton,
)
from qfluentwidgets import FluentIcon as FIF

from app.common.config import TopmostMode, cfg
from app.common.icon import JPG, PNG, UnicodeIcon
from app.common.setting import (
    ARCH,
    AUTHOR,
    BILIBILI_WEB,
    CODENAME,
    COPYRIGHT_HOLDER,
    CURRENT_YEAR,
    DONATION_URL,
    INITIAL_AUTHORING_YEAR,
    REPO_URL,
    SPECIAL_VERSION,
    SYSTEM,
)
from app.common import resource


class FloatingWindowBasicSettings(GroupHeaderCardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle(self.tr("basic_settings"))
        self.setBorderRadius(8)

        # 创建控件
        self._create_controls()

    def _create_controls(self):
        """创建所有控件"""

        # 启动时显示浮窗 → 改为浮窗开关
        self.startup_switch = SwitchButton()
        self.startup_switch.setChecked(cfg.startupDisplayFloatingWindow.value)
        self.startup_switch.checkedChanged.connect(self._on_floating_window_switch_changed)
        self.addGroup(
            UnicodeIcon.get_icon_by_name("ic_fluent_view_desktop_24_regular"),
            "浮窗开关",
            "控制浮窗的开启与关闭（开启后程序启动时自动显示）",
            self.startup_switch,
        )

        # 监听配置变化，同步开关状态
        cfg.startupDisplayFloatingWindow.valueChanged.connect(self._sync_switch_state)

        # 浮窗透明度
        self.opacity_spinbox = SpinBox()
        self.opacity_spinbox.setRange(0, 100)
        self.opacity_spinbox.setSuffix("%")
        self.opacity_spinbox.setValue(cfg.floatingWindowOpacity.value)
        self.opacity_spinbox.valueChanged.connect(lambda v: setattr(cfg.floatingWindowOpacity, "value", v))
        self.addGroup(
            UnicodeIcon.get_icon_by_name("ic_fluent_brightness_high_20_regular"),
            "浮窗透明度",
            "调整浮窗透明度",
            self.opacity_spinbox,
        )

        # 置顶模式
        self.topmost_combo = ComboBox()
        self.topmost_combo.addItems(["关闭置顶", "置顶", "UIA置顶"])
        self.topmost_combo.setCurrentIndex(cfg.floatingWindowTopmostMode.value.value)
        self.topmost_combo.currentIndexChanged.connect(self._on_topmost_changed)
        self.addGroup(
            UnicodeIcon.get_icon_by_name("ic_fluent_note_pin_20_regular"),
            "置顶模式",
            "选择浮窗置顶方式（UIA置顶需以管理员运行）",
            self.topmost_combo,
        )

        # 浮窗可拖动
        self.draggable_switch = SwitchButton()
        self.draggable_switch.setChecked(cfg.floatingWindowDraggable.value)
        self.draggable_switch.checkedChanged.connect(lambda v: setattr(cfg.floatingWindowDraggable, "value", v))
        self.addGroup(
            UnicodeIcon.get_icon_by_name("ic_fluent_drag_24_regular"),
            "浮窗可拖动",
            "控制浮窗是否可被拖动",
            self.draggable_switch,
        )

        # 长按拖动时间
        self.long_press_spinbox = SpinBox()
        self.long_press_spinbox.setRange(50, 3000)
        self.long_press_spinbox.setSingleStep(100)
        self.long_press_spinbox.setSuffix("ms")
        self.long_press_spinbox.setValue(cfg.floatingWindowLongPressDuration.value)
        self.long_press_spinbox.valueChanged.connect(lambda v: setattr(cfg.floatingWindowLongPressDuration, "value", v))
        self.addGroup(
            UnicodeIcon.get_icon_by_name("ic_fluent_hand_draw_32_regular"),
            "长按时间",
            "设置浮窗长按时间（毫秒）",
            self.long_press_spinbox,
        )

        # 无焦点模式
        self.focus_switch = SwitchButton()
        self.focus_switch.setChecked(cfg.doNotStealFocus.value)
        self.focus_switch.checkedChanged.connect(lambda v: setattr(cfg.doNotStealFocus, "value", v))
        self.addGroup(
            UnicodeIcon.get_icon_by_name("ic_fluent_group_dismiss_24_regular"),
            "无焦点模式",
            "通知窗口显示时不抢占焦点，保持原有顶层软件焦点",
            self.focus_switch,
        )

    def _on_topmost_changed(self, index):
        """置顶模式改变处理"""
        mode_map = {
            0: TopmostMode.DISABLED,
            1: TopmostMode.NORMAL,
            2: TopmostMode.UIA,
        }
        cfg.floatingWindowTopmostMode.value = mode_map[index]

    def _sync_switch_state(self, value):
        """同步开关状态（当配置被其他地方修改时）"""
        # 使用 blockSignals 避免触发循环事件
        self.startup_switch.blockSignals(True)
        self.startup_switch.setChecked(value)
        self.startup_switch.blockSignals(False)

    def _on_floating_window_switch_changed(self, checked):
        """浮窗开关改变处理"""
        # 更新配置（使用 cfg.set 确保立即保存）
        cfg.set(cfg.startupDisplayFloatingWindow, checked)

        # 立即控制浮窗显示/隐藏
        try:
            # 获取主窗口
            from PySide6.QtWidgets import QApplication

            from ..view.main_window import MainWindow

            for widget in QApplication.topLevelWidgets():
                if isinstance(widget, MainWindow):
                    if hasattr(widget, "floatingWindow") and widget.floatingWindow:
                        if checked:
                            widget.floatingWindow.show()
                            # 同步更新托盘菜单
                            if hasattr(widget, "floating_window_action"):
                                widget.floating_window_action.setChecked(True)
                                widget.floating_window_action.setText(widget.tr("Hide floating window"))
                        else:
                            widget.floatingWindow.hide()
                            # 同步更新托盘菜单
                            if hasattr(widget, "floating_window_action"):
                                widget.floating_window_action.setChecked(False)
                                widget.floating_window_action.setText(widget.tr("Show floating window"))
                    break
        except Exception as e:
            print(f"控制浮窗显示失败: {e}")


class BasicConfigCard(GroupHeaderCardWidget):
    """Basic config card"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle(self.tr("Basic Settings"))
        self.mediaParser = None

        self.toolsEngineComboBox = ComboBox()
        self.chooseMappingTableButton = PushButton(self.tr("Choose"))
        self.chooseDataTypeButton = PushButton(self.tr("Choose"))
        self.chooseInterfaceButton = PushButton(self.tr("Choose"))
        self.outputFolderButton = PushButton(self.tr("Choose"))

        self.hintIcon = IconWidget(InfoBarIcon.INFORMATION, self)
        self.hintLabel = BodyLabel(self.tr("Click the execute button to start running") + " 👉")
        self.exeButton = PrimaryPushButton(
            self.tr("Execute"),
            self,
            UnicodeIcon.get_icon_by_name("ic_fluent_panel_bottom_20_regular"),
        )

        self.toolBarLayout = QHBoxLayout()

        self._initWidgets()

    def _initWidgets(self):
        self.setBorderRadius(8)

        self.toolsEngineComboBox.setMinimumWidth(120)
        self.toolsEngineComboBox.addItem(self.tr("L2 Func"), userData="Func")
        self.toolsEngineComboBox.addItem(self.tr("Ipc Com"), userData="Ipc")
        self.toolsEngineComboBox.addItem(self.tr("Srp Com"), userData="Srp")

        self.toolsEngineComboBox.setMinimumWidth(120)
        self.chooseMappingTableButton.setFixedWidth(120)
        self.chooseDataTypeButton.setFixedWidth(120)
        self.chooseInterfaceButton.setFixedWidth(120)
        self.outputFolderButton.setFixedWidth(120)
        self.exeButton.setFixedWidth(120)

        self.exeButton.setEnabled(True)
        self.chooseDataTypeButton.setEnabled(False)
        self.chooseInterfaceButton.setEnabled(False)
        self.hintIcon.setFixedSize(16, 16)

        self._initLayout()
        self._connectSignalToSlot()

        self.toolsEngineComboBox.setCurrentText(cfg.get(cfg.fastRteToolsEngine))

    def _initLayout(self):
        # add widget to group
        self.toolsEngineGroup = self.addGroup(
            icon=UnicodeIcon.get_icon_by_name("ic_fluent_multiplier_2x_32_regular"),
            title=self.tr("Change Tools"),
            content=self.tr("Select the Tools Engine to Generator"),
            widget=self.toolsEngineComboBox,
        )
        self.chooseMappingTableGroup = self.addGroup(
            icon=UnicodeIcon.get_icon_by_name("ic_fluent_document_table_24_regular"),
            title=self.tr("Mapping Table Path"),
            content=cfg.get(cfg.fastRteMappingTableFolder),
            widget=self.chooseMappingTableButton,
        )
        self.chooseDataTypGroup = self.addGroup(
            icon=UnicodeIcon.get_icon_by_name("ic_fluent_document_contract_16_regular"),
            title=self.tr("DataType Arxml Path"),
            content=cfg.get(cfg.fastRteDataTypeFolder),
            widget=self.chooseDataTypeButton,
        )
        self.chooseInterfaceGroup = self.addGroup(
            icon=UnicodeIcon.get_icon_by_name("ic_fluent_document_contract_16_regular"),
            title=self.tr("Interface Arxml Path"),
            content=cfg.get(cfg.fastRteInterfaceFolder),
            widget=self.chooseInterfaceButton,
        )
        self.outputFolderGroup = self.addGroup(
            icon=UnicodeIcon.get_icon_by_name("ic_fluent_folder_open_24_regular"),
            title=self.tr("Output Folder"),
            content=cfg.get(cfg.fastRteOutputFolder),
            widget=self.outputFolderButton,
        )

        # add widgets to bottom toolbar
        self.toolBarLayout.setContentsMargins(24, 15, 24, 20)
        self.toolBarLayout.setSpacing(10)
        self.toolBarLayout.addWidget(self.hintIcon, 0, Qt.AlignmentFlag.AlignLeft)
        self.toolBarLayout.addWidget(self.hintLabel, 0, Qt.AlignmentFlag.AlignLeft)
        self.toolBarLayout.addStretch(1)
        self.toolBarLayout.addWidget(self.exeButton, 0, Qt.AlignmentFlag.AlignRight)
        self.toolBarLayout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.vBoxLayout.addLayout(self.toolBarLayout)

    def _onChooseMappingTableButtonClicked(self):
        path, _ = QFileDialog.getOpenFileName(self, self.tr("Choose"))
        if not path or cfg.get(cfg.fastRteMappingTableFolder) == path:
            return
        cfg.set(cfg.fastRteMappingTableFolder, path)
        self.chooseMappingTableGroup.setContent(path)

    def _onChooseDataTypeButtonClicked(self):
        path, _ = QFileDialog.getOpenFileName(self, self.tr("Choose"))
        if not path or cfg.get(cfg.fastRteDataTypeFolder) == path:
            return
        cfg.set(cfg.fastRteDataTypeFolder, path)
        self.chooseDataTypGroup.setContent(path)

    def _onChooseInterfaceButtonClicked(self):
        path, _ = QFileDialog.getOpenFileName(self, self.tr("Choose"))
        if not path or cfg.get(cfg.fastRteInterfaceFolder) == path:
            return
        cfg.set(cfg.fastRteInterfaceFolder, path)
        self.chooseInterfaceGroup.setContent(path)

    def _chooseOutputFolder(self):
        folder = QFileDialog.getExistingDirectory(self, self.tr("Choose folder"), self.outputFolderGroup.content())

        if folder:
            folder = folder.replace("\\", "/")
            cfg.set(cfg.fastRteOutputFolder, folder)
            self.outputFolderGroup.setContent(folder)

    def _onToolsEngineChanged(self):
        icons = [
            UnicodeIcon.get_icon_by_name("ic_fluent_multiplier_2x_32_regular"),
            UnicodeIcon.get_icon_by_name("ic_fluent_dual_screen_span_20_regular"),
            UnicodeIcon.get_icon_by_name("ic_fluent_diamond_link_24_regular"),
        ]
        self.toolsEngineGroup.setIcon(icons[self.toolsEngineComboBox.currentIndex()].icon())
        cfg.set(cfg.fastRteToolsEngine, self.toolsEngineComboBox.currentText())

    def _connectSignalToSlot(self):
        self.toolsEngineComboBox.currentIndexChanged.connect(self._onToolsEngineChanged)
        self.outputFolderButton.clicked.connect(self._chooseOutputFolder)
        self.chooseMappingTableButton.clicked.connect(self._onChooseMappingTableButtonClicked)
        self.chooseDataTypeButton.clicked.connect(self._onChooseDataTypeButtonClicked)
        self.chooseInterfaceButton.clicked.connect(self._onChooseInterfaceButtonClicked)


class BannerWidgetHomeIF1(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        banner_path = JPG.path(JPG.BACKGROUND_2)
        self.banner_image = ImageLabel(QImage(banner_path))
        self.banner_image.scaledToHeight(400)
        self.banner_image.setBorderRadius(12, 12, 12, 12)
        self.banner_image.setScaledContents(True)

        # 添加横幅图片到布局
        self.vBoxLayout = QHBoxLayout(self)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setSpacing(0)

        # 使图片居中
        self.vBoxLayout.addWidget(self.banner_image, 0, Qt.AlignmentFlag.AlignCenter)


class BannerWidgetHomeIF2(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setFixedHeight(320)
        self.setMaximumHeight(320)

        self.main_layout = QVBoxLayout(self)
        self.galleryLabel = QLabel("", self)
        self.galleryLabel.setStyleSheet("color: white;font-size: 30px; font-weight: 600;")
        # self.banner = QPixmap('./app/resource/images/bg37.jpg')
        self.img = Image.open("./app/resource/images/jpg/background2.jpg")
        self.banner = None
        self.path = None

        # 创建阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)  # 阴影模糊半径
        shadow.setColor(Qt.black)  # 阴影颜色
        shadow.setOffset(1.2, 1.2)  # 阴影偏移量

        # 将阴影效果应用于小部件
        self.galleryLabel.setGraphicsEffect(shadow)
        self.galleryLabel.setObjectName("galleryLabel")

        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 20, 0, 0)
        self.main_layout.addWidget(self.galleryLabel)
        self.main_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)

    def paintEvent(self, e):
        super().paintEvent(e)
        painter = QPainter(self)
        painter.setRenderHints(QPainter.SmoothPixmapTransform | QPainter.Antialiasing)

        if not self.banner or not self.path:
            image_height = self.img.width * self.height() // self.width()
            crop_area = (
                0,
                0,
                self.img.width,
                image_height,
            )  # (left, upper, right, lower)
            cropped_img = self.img.crop(crop_area)
            img_data = np.array(cropped_img)  # Convert PIL Image to numpy array
            height, width, channels = img_data.shape
            bytes_per_line = channels * width
            self.banner = QImage(
                img_data.data,
                width,
                height,
                bytes_per_line,
                QImage.Format_RGB888,
            )

            path = QPainterPath()
            path.addRoundedRect(0, 0, width + 50, height + 50, 10, 10)  # 10 is the radius for corners
            self.path = path.simplified()

        painter.setClipPath(self.path)
        painter.drawImage(self.rect(), self.banner)


class BannerWidgetHomeIF3(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setFixedHeight(320)
        self.setMaximumHeight(320)

        self.main_layout = QVBoxLayout(self)
        self.galleryLabel = QLabel("", self)
        self.galleryLabel.setStyleSheet("color: white;font-size: 30px; font-weight: 600;")

        # 从 Qt 资源加载图片到 PIL Image
        self.img = self.load_image_from_qrc(":/app/images/jpg/background2.jpg")
        self.banner = None
        self.path = None

        # 创建阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(Qt.black)
        shadow.setOffset(1.2, 1.2)

        self.galleryLabel.setGraphicsEffect(shadow)
        self.galleryLabel.setObjectName("galleryLabel")

        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 20, 0, 0)
        self.main_layout.addWidget(self.galleryLabel)
        self.main_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)

    def load_image_from_qrc(self, qrc_path):
        """
        从 Qt 资源路径加载图片到 PIL Image

        Args:
            qrc_path: Qt 资源路径，如 ":/app/images/jpg/background2.jpg"

        Returns:
            PIL.Image 对象，如果加载失败则返回 None
        """
        from PySide6.QtCore import QFile, QIODevice
        import io

        # 创建 QFile 对象读取资源
        file = QFile(qrc_path)
        if not file.open(QIODevice.ReadOnly):
            print(f"无法打开资源: {qrc_path}")
            return None

        # 读取所有数据
        data = file.readAll()
        file.close()

        try:
            # 将二进制数据转换为 PIL Image
            img = Image.open(io.BytesIO(data))
            return img
        except Exception as e:
            print(f"图片加载失败: {e}")
            return None

    def paintEvent(self, e):
        super().paintEvent(e)
        painter = QPainter(self)
        painter.setRenderHints(QPainter.SmoothPixmapTransform | QPainter.Antialiasing)

        if not self.banner or not self.path:
            if self.img is None:
                return  # 图片加载失败，不绘制

            image_height = self.img.width * self.height() // self.width()
            crop_area = (
                0,
                0,
                self.img.width,
                image_height,
            )
            cropped_img = self.img.crop(crop_area)

            # 确保图片是 RGB 模式
            if cropped_img.mode != 'RGB':
                cropped_img = cropped_img.convert('RGB')

            img_data = np.array(cropped_img)
            height, width, channels = img_data.shape
            bytes_per_line = channels * width
            self.banner = QImage(
                img_data.data,
                width,
                height,
                bytes_per_line,
                QImage.Format_RGB888,
            )

            path = QPainterPath()
            path.addRoundedRect(0, 0, width + 50, height + 50, 10, 10)
            self.path = path.simplified()

        if self.banner:
            painter.setClipPath(self.path)
            painter.drawImage(self.rect(), self.banner)

class TypewriterLabelHomeIF(QLabel):
    def __init__(self, parent=None):
        super(TypewriterLabelHomeIF, self).__init__(parent)
        self.texts = [
            "Welcome to use FastXGui. \nThis software is currently in the initial testing stage.\nThe only open function is FastRte. \nMore functions will be developed in the future.💕"
        ]
        self.index = 0
        self.char_index = 0
        self.cursor_visible = True
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_label)
        self.timer.start(90)

    def update_label(self):
        if self.char_index > len(self.texts[self.index]):
            if self.index + 1 >= len(self.texts):
                self.timer.stop()
                return
            # 如果已经打印完一行，就打印下一行
            self.index = (self.index + 1) % len(self.texts)
            self.char_index = 0
        text = self.texts[self.index][: self.char_index]
        if self.cursor_visible:
            text += "|"
        else:
            text += " "
        self.setText(text)
        self.cursor_visible = not self.cursor_visible
        self.char_index += 1


class AboutInfoHomeIf(GroupHeaderCardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle(self.tr("About"))
        self.setBorderRadius(8)

        # 打开bilibili按钮
        self.about_bilibili_Button = HyperlinkButton(
            UnicodeIcon.get_icon_by_name("ic_fluent_globe_arrow_forward_20_regular"),
            BILIBILI_WEB,
            self.tr("Bilibili"),
        )
        bilibili_widget = self._create_button_with_icon(self.about_bilibili_Button, PNG.path(PNG.SHAKA_PACKAGER))

        # 查看当前软件版本号
        version_text = f"{SPECIAL_VERSION} | {CODENAME} ({SYSTEM}-{ARCH})"
        self.about_version_label = BodyLabel(version_text)

        # 打开GitHub按钮
        self.about_github_Button = HyperlinkButton(FIF.GITHUB, REPO_URL, self.tr("GitHub"))
        github_widget = self._create_button_with_icon(self.about_github_Button, PNG.path(PNG.SHAKA_PACKAGER))

        # 查看当前软件版权所属
        # 根据发布年份和当前年份是否相同，决定显示格式
        if INITIAL_AUTHORING_YEAR == CURRENT_YEAR:
            copyright_text = f"Copyright © {INITIAL_AUTHORING_YEAR} {AUTHOR}/{COPYRIGHT_HOLDER}"
        else:
            copyright_text = f"Copyright © {INITIAL_AUTHORING_YEAR}-{CURRENT_YEAR} {AUTHOR}/{COPYRIGHT_HOLDER}"

        self.about_author_label = BodyLabel(copyright_text)
        copyright_widget = self._create_label_with_icon(self.about_author_label, PNG.path(PNG.SHAKA_PACKAGER))

        # 创建贡献人员按钮
        self.contributor_button = PushButton(
            self.tr("Contributor"),
        )
        self.contributor_button.setIcon(UnicodeIcon.get_icon_by_name("ic_fluent_code_block_edit_24_regular"))
        self.contributor_button.clicked.connect(self.show_contributors)

        # 创建捐赠支持按钮
        self.donation_button = PushButton(self.tr("Donation"))
        self.donation_button.setIcon(UnicodeIcon.get_icon_by_name("ic_fluent_drink_margarita_24_regular"))
        self.donation_button.clicked.connect(self.open_donation_url)

        self.addGroup(
            UnicodeIcon.get_icon_by_name("ic_fluent_branch_fork_link_20_regular"),
            self.tr("bilibili"),
            self.tr("open wanqiang.liu's personal bilibili homepage"),
            bilibili_widget,
        )

        self.addGroup(
            FIF.GITHUB,
            self.tr("github"),
            self.tr("open code repository"),
            github_widget,
        )

        self.addGroup(
            UnicodeIcon.get_icon_by_name("ic_fluent_code_block_edit_24_regular"),
            self.tr("Contributor"),
            self.tr("view details of contributor lists"),
            self.contributor_button,
        )

        self.addGroup(
            UnicodeIcon.get_icon_by_name("ic_fluent_drink_margarita_24_regular"),
            self.tr("Donation"),
            self.tr("support project development, thanks for your sponser"),
            self.donation_button,
        )

        self.addGroup(
            UnicodeIcon.get_icon_by_name("ic_fluent_video_background_effect_48_regular"),
            self.tr("Copyright"),
            self.tr("FastXGui GPL-3.0 license"),
            copyright_widget,
        )

        self.addGroup(
            UnicodeIcon.get_icon_by_name("ic_fluent_text_number_format_24_regular"),
            self.tr("version"),
            self.tr("show current software version"),
            self.about_version_label,
        )

    def _create_button_with_icon(self, button, icon):
        """创建带图标的按钮容器"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        layout.addWidget(button)

        icon_label = ImageLabel(icon)
        icon_label.scaledToHeight(30)
        icon_label.setBorderRadius(8, 8, 8, 8)
        layout.addWidget(icon_label)

        layout.addStretch()
        return widget

    def _create_label_with_icon(self, label, icon):
        """创建带图标的标签容器"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        layout.addWidget(label)

        icon_label = ImageLabel(icon)
        icon_label.scaledToHeight(30)
        icon_label.setBorderRadius(8, 8, 8, 8)
        layout.addWidget(icon_label)

        layout.addStretch()
        return widget

    def show_contributors(self):
        """显示贡献人员"""
        QDesktopServices.openUrl(QUrl(REPO_URL))

    def open_donation_url(self):
        """打开捐赠链接"""
        QDesktopServices.openUrl(QUrl(DONATION_URL))
