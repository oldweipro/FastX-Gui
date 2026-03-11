import sys
from pathlib import Path
from typing import Union

from PySide6.QtCore import QStandardPaths, Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QIcon
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QLabel, QWidget
from qfluentwidgets import (
    ColorSettingCard,
    ComboBoxSettingCard,
    CustomColorSettingCard,
    ExpandLayout,
    ExpandSettingCard,
    FolderListSettingCard,
    HyperlinkCard,
    InfoBar,
    InfoBarPosition,
    OptionsSettingCard,
    PrimaryPushSettingCard,
    PushButton,
    PushSettingCard,
    RangeSettingCard,
    ScrollArea,
    SettingCard,
    SettingCardGroup,
    SwitchSettingCard,
    setTheme, LineEdit,
    setThemeColor, isDarkTheme, FluentIconBase, HyperlinkButton, GroupHeaderCardWidget, SwitchButton, ComboBox, SpinBox,
)
from qfluentwidgets import FluentIcon as FIF

from app.common.background_manager import get_background_manager
from app.common.config import cfg, isWin11, TopmostMode
from app.common.icon import UIcon
from app.common.notification import Notification, NotifyPosition
from app.common.setting import (
    AUTHOR,
    COPYRIGHT_HOLDER,
    FEEDBACK_URL,
    HELP_URL,
    RELEASE_URL,
    VERSION,
    YEAR, APPLY_NAME,
)
from app.common.signal_bus import signalBus
from app.common.style_sheet import StyleSheet
from app.common.update_checker import UpdateChecker, UpdateResult


class BackgroundImageCard(SettingCard):
    """Custom setting card with select and clear buttons for background image"""

    def __init__(self, title, content, icon, parent=None):
        super().__init__(icon, title, content, parent)

        # Create buttons
        self.selectButton = PushButton(self.tr("Select image"), self)
        self.clearButton = PushButton(self.tr("Clear"), self)

        # Create button layout
        self.buttonLayout = QHBoxLayout()
        self.buttonLayout.setSpacing(10)
        self.buttonLayout.addWidget(self.selectButton)
        self.buttonLayout.addWidget(self.clearButton)

        # Add button layout to the card
        self.hBoxLayout.addLayout(self.buttonLayout)
        self.hBoxLayout.addSpacing(16)

        # Initialize display
        self._updateDisplay()

    def _updateDisplay(self):
        """Update the card display based on current background image path"""
        bg_path = cfg.get(cfg.backgroundImagePath)
        if bg_path:
            import os

            file_name = os.path.basename(bg_path)
            self.setContent(f"Selected: {file_name}")
            self.clearButton.setEnabled(True)
        else:
            self.setContent(self.tr("Choose a custom background image file"))
            self.clearButton.setEnabled(False)

class HelpSettingCard(HyperlinkCard):
    """
    Help setting card (self-contained, no external dependency)
    """

    def __init__(
        self,
        url,
        text,
        icon: Union[str, QIcon, FluentIconBase],
        title,
        content=None,
        parent=None,
    ):
        super().__init__(url, text, icon, title, content, parent)
        self.installPath = self._getInstallPath()
        self.dataPath = self._getDataPath()

        self.installButton = HyperlinkButton(
            "",
            self.tr("Installation folder"),
            self,
            FIF.FOLDER,
        )
        self.installButton.setToolTip(self.tr("Open installation folder"))
        self.installButton.clicked.connect(lambda: self._openFolder(self.installPath))

        self.dataButton = HyperlinkButton(
            "",
            self.tr("Data folder"),
            self,
            FIF.FOLDER,
        )
        self.dataButton.setToolTip(self.tr("Open data folder"))
        self.dataButton.clicked.connect(lambda: self._openFolder(self.dataPath))

        index = self.hBoxLayout.indexOf(self.linkButton)
        self.hBoxLayout.insertWidget(index, self.installButton, 0, Qt.AlignRight)
        self.hBoxLayout.insertWidget(index+1, self.dataButton, 0, Qt.AlignRight)
        self.hBoxLayout.addSpacing(16)

    @staticmethod
    def _getInstallPath() -> Path:
        """
        Return executable folder (works for dev and frozen)
        """
        if getattr(sys, "frozen", False):
            return Path(sys.executable).resolve().parent
        else:
            return Path(sys.argv[0]).resolve().parent

    @staticmethod
    def _getDataPath() -> Path:
        """
        Return application data folder
        """
        if sys.platform == "win32":
            return Path.home() / "AppData" / "Roaming" / "FastXGui"
        else:
            return Path.home() / ".fastxgui"

    @staticmethod
    def _openFolder(path: Path):
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

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
            UIcon.get("ic_fluent_window_multiple_20_regular"),
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
            UIcon.get("ic_fluent_brightness_high_20_regular"),
            "浮窗透明度",
            "调整浮窗透明度",
            self.opacity_spinbox,
        )

        # 置顶模式
        self.topmost_combo = ComboBox()
        self.topmost_combo.addItems(["关闭置顶", "置顶", "UIA 置顶"])
        self.topmost_combo.setCurrentIndex(cfg.floatingWindowTopmostMode.value.value)
        self.topmost_combo.currentIndexChanged.connect(self._on_topmost_changed)
        self.addGroup(
            UIcon.get("ic_fluent_pin_20_regular"),
            "置顶模式",
            "选择浮窗置顶方式（UIA 置顶需以管理员运行）",
            self.topmost_combo,
        )

        # 浮窗可拖动
        self.draggable_switch = SwitchButton()
        self.draggable_switch.setChecked(cfg.floatingWindowDraggable.value)
        self.draggable_switch.checkedChanged.connect(lambda v: setattr(cfg.floatingWindowDraggable, "value", v))
        self.addGroup(
            UIcon.get("ic_fluent_drag_20_regular"),
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
            UIcon.get("ic_fluent_timer_3_20_regular"),
            "长按时间",
            "设置浮窗长按时间（毫秒）",
            self.long_press_spinbox,
        )

        # 无焦点模式
        self.focus_switch = SwitchButton()
        self.focus_switch.setChecked(cfg.doNotStealFocus.value)
        self.focus_switch.checkedChanged.connect(lambda v: setattr(cfg.doNotStealFocus, "value", v))
        self.addGroup(
            UIcon.get("ic_fluent_target_20_regular"),
            "无焦点模式",
            "通知窗口显示时不抢占焦点，保持原有顶层软件焦点",
            self.focus_switch,
        )

        # 重置位置按钮
        self.reset_pos_btn = PushButton("重置位置")
        self.reset_pos_btn.clicked.connect(self._on_reset_position)
        self.addGroup(
            UIcon.get("ic_fluent_arrow_reset_20_regular"),
            "重置悬浮窗位置",
            "将悬浮窗移回屏幕默认位置",
            self.reset_pos_btn,
        )

    def _on_reset_position(self):
        """重置悬浮窗位置"""
        try:
            # 重置配置
            cfg.set(cfg.floatingWindowPosX, 100)
            cfg.set(cfg.floatingWindowPosY, 100)
            
            # 如果浮窗存在，移动它
            from PySide6.QtWidgets import QApplication
            from ..view.main_window import MainWindow
            
            for widget in QApplication.topLevelWidgets():
                if isinstance(widget, MainWindow):
                    if hasattr(widget, "floatingWindow") and widget.floatingWindow:
                        widget.floatingWindow.move(100, 100)
                        # 如果处于贴边状态，展开它
                        if widget.floatingWindow._retracted:
                            widget.floatingWindow._expand_from_edge()
                    break
        except Exception as e:
            print(f"重置悬浮窗位置失败: {e}")

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


class FloatingWindowAppearanceSettings(GroupHeaderCardWidget):
    """浮窗外观设置卡片"""

    appearance_settings_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle(self.tr("appearance_settings"))
        self.setBorderRadius(8)
        self._create_controls()

    def _create_controls(self):
        """创建外观设置控件"""

        # 按钮控制
        self.btn_combo = self._create_button_control_combo()
        self.addGroup(
            UIcon.get("ic_fluent_checkbox_checked_20_regular"),
            "显示的按钮",
            "选择悬浮窗上要显示的功能按钮",
            self.btn_combo,
        )

        # 排列方式
        self.placement_combo = ComboBox()
        self.placement_combo.addItems(["双行网格", "垂直排列", "水平排列"])
        self.placement_combo.setCurrentIndex(cfg.floatingWindowPlacement.value)
        self.placement_combo.currentIndexChanged.connect(self._on_placement_changed)
        self.addGroup(
            UIcon.get("ic_fluent_line_horizontal_3_20_regular"),
            "按钮排列方式",
            "控制悬浮窗按钮的排列方向",
            self.placement_combo,
        )

        # 显示样式
        self.style_combo = ComboBox()
        self.style_combo.addItems(["图标 + 文字", "仅图标", "仅文字"])
        self.style_combo.setCurrentIndex(cfg.floatingWindowDisplayStyle.value)
        self.style_combo.currentIndexChanged.connect(self._on_style_changed)
        self.addGroup(
            UIcon.get("ic_fluent_color_20_regular"),
            "按钮显示样式",
            "控制按钮是显示图标、文字还是两者都显示",
            self.style_combo,
        )

        # 大小
        self.size_combo = ComboBox()
        self.size_combo.addItems(["超级小", "超小", "小", "中（默认）", "大", "超大", "超级大"])
        self.size_combo.setCurrentIndex(cfg.floatingWindowSize.value)
        self.size_combo.currentIndexChanged.connect(self._on_size_changed)
        self.addGroup(
            UIcon.get("ic_fluent_full_screen_maximize_20_regular"),
            "悬浮窗大小",
            "调整按钮与图标的整体尺寸",
            self.size_combo,
        )

        # 主题
        self.theme_combo = ComboBox()
        self.theme_combo.addItems(["跟随系统", "浅色", "深色"])
        self.theme_combo.setCurrentIndex(cfg.floatingWindowTheme.value)
        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        self.addGroup(
            UIcon.get("ic_fluent_dark_theme_20_regular"),
            "悬浮窗主题",
            "单独控制悬浮窗的浅色/深色外观（不影响主界面）",
            self.theme_combo,
        )

        # 扩展闪抽组件
        self.extend_switch = SwitchButton()
        self.extend_switch.setChecked(cfg.extendQuickDrawComponent.value)
        self.extend_switch.checkedChanged.connect(lambda v: setattr(cfg.extendQuickDrawComponent, "value", v))
        self.addGroup(
            UIcon.get("ic_fluent_panel_separate_right_20_regular"),
            "扩展闪抽组件",
            "在闪抽按钮旁显示下拉箭头，可快速切换班级/筛选条件",
            self.extend_switch,
        )

    def _create_button_control_combo(self) -> ComboBox:
        """创建按钮控制下拉框"""
        combo = ComboBox()
        combo.addItems([
            "仅点名", "仅闪抽", "仅抽奖",
            "点名+闪抽", "点名+抽奖", "闪抽+抽奖", "点名+闪抽+抽奖",
            "仅计时", "点名+计时", "闪抽+计时",
            "抽奖+计时", "点名+闪抽+计时", "点名+抽奖+计时", "闪抽+抽奖+计时",
            "点名+闪抽+抽奖+计时"
        ])
        # 将配置值映射到索引
        value = cfg.floatingWindowButtonControl.value
        if isinstance(value, int) and 0 <= value < combo.count():
            combo.setCurrentIndex(value)
        else:
            combo.setCurrentIndex(6)  # 默认点名+闪抽+抽奖
        combo.currentIndexChanged.connect(self._on_button_control_changed)
        return combo

    def _on_button_control_changed(self, index: int):
        """按钮控制改变"""
        cfg.floatingWindowButtonControl.value = index
        self.appearance_settings_changed.emit()

    def _on_placement_changed(self, index: int):
        """排列方式改变"""
        cfg.floatingWindowPlacement.value = index
        self.appearance_settings_changed.emit()

    def _on_style_changed(self, index: int):
        """显示样式改变"""
        cfg.floatingWindowDisplayStyle.value = index
        self.appearance_settings_changed.emit()

    def _on_size_changed(self, index: int):
        """大小改变"""
        cfg.floatingWindowSize.value = index
        self.appearance_settings_changed.emit()

    def _on_theme_changed(self, index: int):
        """主题改变"""
        cfg.floatingWindowTheme.value = index
        self.appearance_settings_changed.emit()


class FloatingWindowEdgeSettings(GroupHeaderCardWidget):
    """浮窗贴边设置卡片"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle(self.tr("edge_settings"))
        self.setBorderRadius(8)
        self._create_controls()

    def _create_controls(self):
        """创建贴边设置控件"""

        # 贴边开关
        self.stick_switch = SwitchButton()
        self.stick_switch.setChecked(cfg.floatingWindowStickToEdge.value)
        self.stick_switch.checkedChanged.connect(lambda v: setattr(cfg.floatingWindowStickToEdge, "value", v))
        self.addGroup(
            UIcon.get("ic_fluent_pin_20_regular"),
            "启用贴边自动隐藏",
            "悬浮窗拖到屏幕边缘后自动缩进，鼠标经过时展开",
            self.stick_switch,
        )

        # 回收秒数
        self.recover_spinbox = SpinBox()
        self.recover_spinbox.setRange(1, 60)
        self.recover_spinbox.setSuffix(" s")
        self.recover_spinbox.setValue(cfg.floatingWindowStickToEdgeRecoverSeconds.value)
        self.recover_spinbox.valueChanged.connect(lambda v: setattr(cfg.floatingWindowStickToEdgeRecoverSeconds, "value", v))
        self.addGroup(
            UIcon.get("ic_fluent_timer_20_regular"),
            "自动隐藏延迟",
            "鼠标离开后等待多少秒再收回边缘",
            self.recover_spinbox,
        )

        # 指示器样式
        self.indicator_combo = ComboBox()
        self.indicator_combo.addItems(["图标样式", "文字样式", "箭头样式"])
        self.indicator_combo.setCurrentIndex(cfg.floatingWindowStickToEdgeDisplayStyle.value)
        self.indicator_combo.currentIndexChanged.connect(lambda i: setattr(cfg.floatingWindowStickToEdgeDisplayStyle, "value", i))
        self.addGroup(
            UIcon.get("ic_fluent_arrow_sort_20_regular"),
            "收纳指示器样式",
            "控制贴边后显示的小按钮外观",
            self.indicator_combo,
        )


class FloatingWindowForegroundSettings(GroupHeaderCardWidget):
    """浮窗前台隐藏设置卡片"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle(self.tr("foreground_settings"))
        self.setBorderRadius(8)
        self._create_controls()

    def _create_controls(self):
        """创建前台隐藏设置控件"""

        # 启用开关
        self.enabled_switch = SwitchButton()
        self.enabled_switch.setChecked(cfg.hideFloatingWindowOnForeground.value)
        self.enabled_switch.checkedChanged.connect(self._on_enabled_changed)
        self.addGroup(
            UIcon.get("ic_fluent_window_header_horizontal_20_regular"),
            "前台特定窗口时隐藏",
            "当指定的窗口处于前台时自动隐藏悬浮窗",
            self.enabled_switch,
        )

        # 窗口标题
        self.titles_edit = LineEdit()
        self.titles_edit.setPlaceholderText("分号分隔，如: 钉钉;腾讯会议")
        self.titles_edit.setText(cfg.hideFloatingWindowOnForegroundWindowTitles.value)
        self.titles_edit.editingFinished.connect(
            lambda: setattr(cfg.hideFloatingWindowOnForegroundWindowTitles, "value", self.titles_edit.text().strip())
        )
        self.addGroup(
            UIcon.get("ic_fluent_textbox_20_regular"),
            "窗口标题关键词",
            "包含这些关键词的窗口处于前台时隐藏悬浮窗（分号分隔）",
            self.titles_edit,
        )

        # 进程名称
        self.processes_edit = LineEdit()
        self.processes_edit.setPlaceholderText("分号分隔，如: dingtalk.exe;Teams.exe")
        self.processes_edit.setText(cfg.hideFloatingWindowOnForegroundProcessNames.value)
        self.processes_edit.editingFinished.connect(
            lambda: setattr(cfg.hideFloatingWindowOnForegroundProcessNames, "value", self.processes_edit.text().strip())
        )
        self.addGroup(
            UIcon.get("ic_fluent_process_20_regular"),
            "进程名称关键词",
            "指定进程处于前台时隐藏悬浮窗（分号分隔）",
            self.processes_edit,
        )

        self._set_inputs_enabled(self.enabled_switch.isChecked())

    def _on_enabled_changed(self, enabled: bool):
        """启用状态改变"""
        cfg.hideFloatingWindowOnForeground.value = enabled
        self._set_inputs_enabled(enabled)

    def _set_inputs_enabled(self, enabled: bool):
        """设置输入框启用状态"""
        self.titles_edit.setEnabled(enabled)
        self.processes_edit.setEnabled(enabled)


class SettingInterface(ScrollArea):
    """Setting interface"""

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.view = QWidget()
        # initialize background manager
        self.backgroundManager = get_background_manager(cfg)

        # setting label
        self.settingLabel = QLabel(self.tr("Settings"), self)

        # Project folders
        self.projectInThisPCGroup = SettingCardGroup(self.tr("Project on this PC"), self.view)
        self.projectFolderCard = FolderListSettingCard(
            cfg.projectFolders,
            self.tr("Local Project library"),
            directory=QStandardPaths.writableLocation(QStandardPaths.MusicLocation),
            parent=self.projectInThisPCGroup,
        )
        self.downloadFolderCard = PushSettingCard(
            self.tr("Choose folder"),
            FIF.FOLDER_ADD,
            self.tr("Project directory"),
            cfg.get(cfg.downloadFolder),
            self.projectInThisPCGroup,
        )

        # personalization
        self.personalGroup = SettingCardGroup(self.tr("Personalization"), self.view)
        self.micaCard = SwitchSettingCard(
            FIF.TRANSPARENT,
            self.tr("Mica effect"),
            self.tr("Apply semi transparent to windows and surfaces"),
            cfg.micaEnabled,
            self.personalGroup,
        )
        self.themeCard = OptionsSettingCard(
            cfg.themeMode,
            FIF.BRUSH,
            self.tr("Application theme"),
            self.tr("Change the appearance of your application"),
            texts=[
                self.tr("Light"),
                self.tr("Dark"),
                self.tr("Use system setting"),
            ],
            parent=self.personalGroup,
        )
        self.themeColorCard = CustomColorSettingCard(
            cfg.themeColor,
            FIF.PALETTE,
            self.tr("Theme color"),
            self.tr("Change the theme color of you application"),
            self.personalGroup,
        )
        self.zoomCard = OptionsSettingCard(
            cfg.dpiScale,
            FIF.ZOOM,
            self.tr("Interface zoom"),
            self.tr("Change the size of widgets and fonts"),
            texts=[
                "100%",
                "125%",
                "150%",
                "175%",
                "200%",
                self.tr("Use system setting"),
            ],
            parent=self.personalGroup,
        )
        self.languageCard = ComboBoxSettingCard(
            cfg.language,
            FIF.LANGUAGE,
            self.tr("Language"),
            self.tr("Set your preferred language for UI"),
            texts=[
                "简体中文",
                "繁體中文",
                "English",
                self.tr("Use system setting"),
            ],
            parent=self.personalGroup,
        )
        # background settings
        self.backgroundGroupCard = ExpandSettingCard(
            FIF.PHOTO,
            self.tr("Background"),
            self.tr("Customize application background settings"),
            self.view,
        )
        self.backgroundEnabledCard = SwitchSettingCard(
            FIF.PHOTO,
            self.tr("Background image"),
            self.tr("Enable custom background image for the application"),
            cfg.backgroundImageEnabled,
            self.backgroundGroupCard,
        )
        self.backgroundImageCard = BackgroundImageCard(
            self.tr("Background image path"),
            self.tr("Choose a custom background image file"),
            UIcon.get("ic_fluent_image_20_regular"),
            self.backgroundGroupCard,
        )
        self.backgroundOpacityCard = RangeSettingCard(
            cfg.backgroundOpacity,
            FIF.TRANSPARENT,
            self.tr("Background opacity"),
            self.tr("Adjust the opacity of the background image (0-100%)"),
            self.backgroundGroupCard,
        )
        self.backgroundBlurCard = RangeSettingCard(
            cfg.backgroundBlurRadius,
            FIF.BRUSH,
            self.tr("Background blur"),
            self.tr("Adjust the blur radius of the background image (0-50px)"),
            self.backgroundGroupCard,
        )
        self.backgroundDisplayModeCard = ComboBoxSettingCard(
            cfg.backgroundDisplayMode,
            FIF.LAYOUT,
            self.tr("Display mode"),
            self.tr("Choose how the background image is displayed"),
            texts=[
                self.tr("Stretch"),
                self.tr("Keep Aspect Ratio"),
                self.tr("Tile"),
                self.tr("Original Size"),
                self.tr("Fit Window"),
            ],
            parent=self.backgroundGroupCard,
        )

        # 懸浮窗
        self.floatingWindowGroupCard = ExpandSettingCard(
            UIcon.get("ic_fluent_panel_separate_right_20_regular"),
            self.tr("FloatWindow"),
            self.tr("Float Windows Settings"),
            self.view,
        )
        self.floatingWindowBasicCard = FloatingWindowBasicSettings(self.floatingWindowGroupCard)
        self.floatingWindowAppearanceCard = FloatingWindowAppearanceSettings(self.floatingWindowGroupCard)
        self.floatingWindowEdgeCard = FloatingWindowEdgeSettings(self.floatingWindowGroupCard)
        self.floatingWindowForegroundCard = FloatingWindowForegroundSettings(self.floatingWindowGroupCard)

        # material
        self.materialGroup = SettingCardGroup(self.tr("Material"), self.view)
        self.blurRadiusCard = RangeSettingCard(
            cfg.blurRadius,
            FIF.ALBUM,
            self.tr("Acrylic blur radius"),
            self.tr("The greater the radius, the more blurred the image"),
            self.materialGroup,
        )

        # Application
        self.appGroup = SettingCardGroup(self.tr("Application settings"), self.view)
        self.StartupCard = SwitchSettingCard(
            UIcon.get("ic_fluent_power_20_regular"),
            self.tr("Auto StartUp Settings(Beta)"),
            self.tr("Automatically start up the application"),
            configItem=cfg.autoRun,
            parent=self.appGroup,
        )
        self.betaCard = SwitchSettingCard(
            UIcon.get("ic_fluent_flask_20_regular"),
            self.tr("Beta experimental features"),
            self.tr("When turned on, experimental features will be enabled"),
            configItem=cfg.beta,
            parent=self.appGroup,
        )
        self.closeWindowActionCard = ComboBoxSettingCard(
            cfg.closeWindowAction,
            FIF.MINIMIZE,
            self.tr("when close windows"),
            self.tr(
                "Select the default behavior when closing the window, or you can be asked by the dialog box on closing"
            ),
            texts=[self.tr("ask"), self.tr("minimize"), self.tr("close")],
            parent=self.appGroup,
        )

        self.windowSizeModeCard = ComboBoxSettingCard(
            cfg.windowSizeMode,
            UIcon.get("ic_fluent_full_screen_maximize_20_regular"),
            self.tr("window size mode"),
            self.tr("Select the window size mode, fixed size or auto-adaptive to screen resolution"),
            texts=[self.tr("fixed"), self.tr("auto")],
            parent=self.appGroup,
        )

        # Log
        self.logGroupCard = ExpandSettingCard(
            UIcon.get("ic_fluent_document_text_clock_20_regular"),
            self.tr("Logs Settings"),
            self.tr("Custom logs settings"),
            self.view,
        )
        self.logLevelCard = ComboBoxSettingCard(
            cfg.logLevel,
            FIF.COMMAND_PROMPT,
            self.tr("Log level Filter"),
            self.tr("Set the minimum log level to display"),
            texts=[
                self.tr("TRACE"),
                self.tr("DEBUG"),
                self.tr("INFO"),
                self.tr("SUCCESS"),
                self.tr("WARNING"),
                self.tr("ERROR"),
                self.tr("CRITICAL"),
            ],
            parent=self.logGroupCard,
        )
        
        # 创建一套颜色设置卡片，根据当前主题使用对应的配置
        self.logColorTraceCard = ColorSettingCard(
            cfg.logColorTraceDark if isDarkTheme() else cfg.logColorTraceLight,
            FIF.PALETTE,
            self.tr("Trace color"),
            self.tr("Set the color for trace level logs"),
            parent=self.logGroupCard,
        )
        self.logColorDebugCard = ColorSettingCard(
            cfg.logColorDebugDark if isDarkTheme() else cfg.logColorDebugLight,
            FIF.PALETTE,
            self.tr("Debug color"),
            self.tr("Set the color for debug level logs"),
            parent=self.logGroupCard,
        )
        self.logColorInfoCard = ColorSettingCard(
            cfg.logColorInfoDark if isDarkTheme() else cfg.logColorInfoLight,
            FIF.PALETTE,
            self.tr("Info color"),
            self.tr("Set the color for info level logs"),
            parent=self.logGroupCard,
        )
        self.logColorSuccessCard = ColorSettingCard(
            cfg.logColorSuccessDark if isDarkTheme() else cfg.logColorSuccessLight,
            FIF.PALETTE,
            self.tr("Success color"),
            self.tr("Set the color for success level logs"),
            parent=self.logGroupCard,
        )
        self.logColorWarningCard = ColorSettingCard(
            cfg.logColorWarningDark if isDarkTheme() else cfg.logColorWarningLight,
            FIF.PALETTE,
            self.tr("Warning color"),
            self.tr("Set the color for warning level logs"),
            parent=self.logGroupCard,
        )
        self.logColorErrorCard = ColorSettingCard(
            cfg.logColorErrorDark if isDarkTheme() else cfg.logColorErrorLight,
            FIF.PALETTE,
            self.tr("Error color"),
            self.tr("Set the color for error level logs"),
            parent=self.logGroupCard,
        )
        self.logColorCriticalCard = ColorSettingCard(
            cfg.logColorCriticalDark if isDarkTheme() else cfg.logColorCriticalLight,
            FIF.PALETTE,
            self.tr("Critical color"),
            self.tr("Set the color for critical level logs"),
            parent=self.logGroupCard,
        )

        # update software
        self.updateSoftwareGroup = SettingCardGroup(self.tr("Software update"), self.view)
        self.updateOnStartUpCard = SwitchSettingCard(
            FIF.UPDATE,
            self.tr("Check for updates when the application starts"),
            self.tr("The new version will be more stable and have more features"),
            configItem=cfg.checkUpdateAtStartUp,
            parent=self.updateSoftwareGroup,
        )

        # About
        self.aboutGroup = SettingCardGroup(self.tr("About"), self.view)
        self.helpCard = HelpSettingCard(
            HELP_URL,
            self.tr("Open help page"),
            FIF.HELP,
            self.tr("Help"),
            self.tr("Discover new features and learn useful tips about FastXTeam/FastX-Gui"),
            self.aboutGroup,
        )
        self.feedbackCard = PrimaryPushSettingCard(
            self.tr("Provide feedback"),
            FIF.FEEDBACK,
            self.tr("Provide feedback"),
            self.tr("Help us improve FastXTeam/FastX-Gui by providing feedback"),
            self.aboutGroup,
        )
        self.aboutCard = PrimaryPushSettingCard(
            self.tr("Check update"),
            ":/app/images/png/logo.png",
            self.tr("About"),
            "© " + self.tr("Copyright (C)") + f" {YEAR}, {AUTHOR}/{COPYRIGHT_HOLDER}" + self.tr("Version") + VERSION,
            self.aboutGroup,
        )

        self.__initWidget()
        self.__setQss()
        self.__initLayout()
        self.__connectSignalToSlot()

    def __initWidget(self):
        self.resize(1000, 800)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setViewportMargins(0, 120, 0, 20)
        self.setWidget(self.view)
        self.setWidgetResizable(True)

    def __setQss(self):
        """set style sheet"""
        # initialize style sheet
        self.setObjectName("settingInterface")
        self.view.setObjectName("scrollWidget")
        self.settingLabel.setObjectName("settingLabel")
        StyleSheet.SETTING_INTERFACE.apply(self)
        # micaCard
        self.micaCard.setEnabled(isWin11())
        # initialize background cards state
        self.__updateBackgroundCardsState()

    def __initLayout(self):
        self.settingLabel.move(36, 68)

        # add setting card group to layout
        self.expandLayout = ExpandLayout(self.view)
        self.expandLayout.setSpacing(28)
        self.expandLayout.setContentsMargins(36, 10, 36, 0)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # add cards to group
        self.projectInThisPCGroup.addSettingCard(self.projectFolderCard)
        self.projectInThisPCGroup.addSettingCard(self.downloadFolderCard)

        self.personalGroup.addSettingCard(self.micaCard)
        self.personalGroup.addSettingCard(self.themeCard)
        self.personalGroup.addSettingCard(self.themeColorCard)
        self.personalGroup.addSettingCard(self.zoomCard)
        self.personalGroup.addSettingCard(self.languageCard)
        self.personalGroup.addSettingCard(self.backgroundGroupCard)
        self.personalGroup.addSettingCard(self.floatingWindowGroupCard)

        # Add widgets to expand card view instead of as setting cards
        self.backgroundGroupCard.viewLayout.addWidget(self.backgroundEnabledCard)
        self.backgroundGroupCard.viewLayout.addWidget(self.backgroundImageCard)
        self.backgroundGroupCard.viewLayout.addWidget(self.backgroundOpacityCard)
        self.backgroundGroupCard.viewLayout.addWidget(self.backgroundBlurCard)
        self.backgroundGroupCard.viewLayout.addWidget(self.backgroundDisplayModeCard)
        self.backgroundGroupCard._adjustViewSize()

        # float window
        self.floatingWindowGroupCard.viewLayout.addWidget(self.floatingWindowBasicCard)
        self.floatingWindowGroupCard.viewLayout.addWidget(self.floatingWindowAppearanceCard)
        self.floatingWindowGroupCard.viewLayout.addWidget(self.floatingWindowEdgeCard)
        self.floatingWindowGroupCard.viewLayout.addWidget(self.floatingWindowForegroundCard)

        # add log setting cards
        self.logGroupCard.viewLayout.addWidget(self.logLevelCard)
        # 添加日志颜色设置卡片
        self.logGroupCard.viewLayout.addWidget(self.logColorTraceCard)
        self.logGroupCard.viewLayout.addWidget(self.logColorDebugCard)
        self.logGroupCard.viewLayout.addWidget(self.logColorInfoCard)
        self.logGroupCard.viewLayout.addWidget(self.logColorSuccessCard)
        self.logGroupCard.viewLayout.addWidget(self.logColorWarningCard)
        self.logGroupCard.viewLayout.addWidget(self.logColorErrorCard)
        self.logGroupCard.viewLayout.addWidget(self.logColorCriticalCard)

        self.materialGroup.addSettingCard(self.blurRadiusCard)

        self.appGroup.addSettingCard(self.StartupCard)
        self.appGroup.addSettingCard(self.betaCard)
        self.appGroup.addSettingCard(self.closeWindowActionCard)
        self.appGroup.addSettingCard(self.windowSizeModeCard)
        self.appGroup.addSettingCard(self.logGroupCard)

        self.updateSoftwareGroup.addSettingCard(self.updateOnStartUpCard)

        self.aboutGroup.addSettingCard(self.helpCard)
        self.aboutGroup.addSettingCard(self.feedbackCard)
        self.aboutGroup.addSettingCard(self.aboutCard)

        # add setting card groups to layout
        self.expandLayout.addWidget(self.projectInThisPCGroup)
        self.expandLayout.addWidget(self.personalGroup)
        self.expandLayout.addWidget(self.appGroup)
        self.expandLayout.addWidget(self.materialGroup)
        self.expandLayout.addWidget(self.updateSoftwareGroup)
        self.expandLayout.addWidget(self.aboutGroup)
        self._betaEnable() if cfg.beta.value else None  # Beta

    def _createBetaSetting(self):
        self.BetaGroup = SettingCardGroup(self.tr("Beta"), self.view)
        self.debug_Card = SwitchSettingCard(
            UIcon.get("ic_fluent_bug_20_regular"),
            self.tr("Debug Mode"),
            self.tr(
                "The global exception capture will be disabled, and there will be outputs in the commandline.(Code Running Only)"
            ),
            configItem=cfg.debugCard,
            parent=self.BetaGroup,
        )

    def __showRestartTooltip(self):
        """show restart tooltip"""
        InfoBar.success(
            self.tr("Updated successfully"),
            self.tr("Configuration takes effect after restart"),
            duration=1500,
            parent=self,
        )

    def __onDownloadFolderCardClicked(self):
        """download folder card clicked slot"""
        folder = QFileDialog.getExistingDirectory(self, self.tr("Choose folder"), "./")
        if not folder or cfg.get(cfg.downloadFolder) == folder:
            return
        cfg.set(cfg.downloadFolder, folder)
        self.downloadFolderCard.setContent(folder)

    def _betaEnable(self):
        if cfg.beta.value:
            self._createBetaSetting()
            self.expandLayout.addWidget(self.BetaGroup)
            self.BetaGroup.addSettingCard(self.debug_Card)
            self.debug_Card.setVisible(True)
            self.BetaGroup.setVisible(True)
        else:
            self.debug_Card.setValue(False)
            self.debug_Card.setVisible(False)
            self.BetaGroup.setVisible(False)

    def __onBackgroundEnabledChanged(self, isChecked: bool):
        """Handle background image enable/disable"""
        cfg.set(cfg.backgroundImageEnabled, isChecked)
        self.backgroundManager.update_background()
        self.__updateBackgroundCardsState()
        self.__updateBackgroundPreview()

    def __onSelectBackgroundImage(self):
        """Handle background image selection"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            self.tr("Select background image"),
            "",
            self.tr("Image files (*.jpg *.jpeg *.png *.bmp *.gif *.webp)"),
        )

        if file_path:
            cfg.set(cfg.backgroundImagePath, file_path)
            self.backgroundManager.update_background()
            self.backgroundImageCard._updateDisplay()
            self.__updateBackgroundPreview()

    def __onClearBackgroundImage(self):
        """Handle background image clearing"""
        cfg.set(cfg.backgroundImagePath, "")
        self.backgroundManager.update_background()
        self.backgroundImageCard._updateDisplay()
        self.__updateBackgroundPreview()

    def __onBackgroundOpacityChanged(self, value: int):
        """Handle background opacity change"""
        cfg.set(cfg.backgroundOpacity, value)
        self.backgroundManager.update_background()
        self.__updateBackgroundPreview()

    def __onBackgroundBlurChanged(self, value: int):
        """Handle background blur radius change"""
        cfg.set(cfg.backgroundBlurRadius, value)
        self.backgroundManager.update_background()
        self.__updateBackgroundPreview()

    def __onBackgroundDisplayModeChanged(self, index: int):
        """Handle background display mode change"""
        mode = self.backgroundDisplayModeCard.comboBox.itemData(index)
        cfg.set(cfg.backgroundDisplayMode, mode)
        self.backgroundManager.update_background()
        self.__updateBackgroundPreview()

    def __updateBackgroundPreview(self):
        """Update background preview in main window"""
        parent_window = self.window()
        if hasattr(parent_window, "update"):
            parent_window.update()  # Trigger repaint to show background changes

    def scrollToGroup(self, group):
        self.verticalScrollBar().setValue(group.y())

    def __updateBackgroundCardsState(self):
        """Update the enabled state of background setting cards"""
        is_background_enabled = cfg.get(cfg.backgroundImageEnabled)

        # Enable/disable background related cards based on background enabled state
        self.backgroundImageCard.setEnabled(is_background_enabled)
        self.backgroundOpacityCard.setEnabled(is_background_enabled)
        self.backgroundBlurCard.setEnabled(is_background_enabled)
        self.backgroundDisplayModeCard.setEnabled(is_background_enabled)

        # Update display when background is enabled/disabled
        if hasattr(self.backgroundImageCard, "_updateDisplay"):
            self.backgroundImageCard._updateDisplay()

    def __connectSignalToSlot(self):
        """connect signal to slot"""
        cfg.appRestartSig.connect(self.__showRestartTooltip)

        # project in the pc
        self.downloadFolderCard.clicked.connect(self.__onDownloadFolderCardClicked)

        # personalization
        cfg.themeChanged.connect(setTheme)
        cfg.themeChanged.connect(self.__onThemeChanged)
        self.themeColorCard.colorChanged.connect(lambda c: setThemeColor(c))
        self.micaCard.checkedChanged.connect(signalBus.micaEnableChanged)

        # background settings
        self.backgroundEnabledCard.checkedChanged.connect(self.__onBackgroundEnabledChanged)
        self.backgroundImageCard.selectButton.clicked.connect(self.__onSelectBackgroundImage)
        self.backgroundImageCard.clearButton.clicked.connect(self.__onClearBackgroundImage)
        self.backgroundOpacityCard.valueChanged.connect(self.__onBackgroundOpacityChanged)
        self.backgroundBlurCard.valueChanged.connect(self.__onBackgroundBlurChanged)
        self.backgroundDisplayModeCard.comboBox.currentIndexChanged.connect(self.__onBackgroundDisplayModeChanged)

        self.StartupCard.checkedChanged.connect(self.__on_autostart_changed)

        # application
        self.betaCard.checkedChanged.connect(self._betaEnable)

        # check update
        self.aboutCard.clicked.connect(signalBus.checkUpdateSig)
        self.initUpdateChecker()

        # about
        self.feedbackCard.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(FEEDBACK_URL)))

    def __onThemeChanged(self):
        """Handle theme change and update log color cards"""
        #  如果是展開的,則收縮
        if self.logGroupCard.isExpand:
            self.logGroupCard.setExpand(False)

        # 获取所有卡片对象
        cards = [
            self.logColorTraceCard,
            self.logColorDebugCard,
            self.logColorInfoCard,
            self.logColorSuccessCard,
            self.logColorWarningCard,
            self.logColorErrorCard,
            self.logColorCriticalCard
        ]

        # 1. 先从布局中移除
        for card in cards:
            self.logGroupCard.viewLayout.removeWidget(card)
            # 2. 让Qt安全地删除对象
            card.deleteLater()

        # 创建新的颜色设置卡片
        self.logColorTraceCard = ColorSettingCard(
            cfg.logColorTraceDark if isDarkTheme() else cfg.logColorTraceLight,
            FIF.PALETTE,
            self.tr("Trace color"),
            self.tr("Set the color for trace level logs"),
            parent=self.logGroupCard,
        )
        self.logColorDebugCard = ColorSettingCard(
            cfg.logColorDebugDark if isDarkTheme() else cfg.logColorDebugLight,
            FIF.PALETTE,
            self.tr("Debug color"),
            self.tr("Set the color for debug level logs"),
            parent=self.logGroupCard,
        )
        self.logColorInfoCard = ColorSettingCard(
            cfg.logColorInfoDark if isDarkTheme() else cfg.logColorInfoLight,
            FIF.PALETTE,
            self.tr("Info color"),
            self.tr("Set the color for info level logs"),
            parent=self.logGroupCard,
        )
        self.logColorSuccessCard = ColorSettingCard(
            cfg.logColorSuccessDark if isDarkTheme() else cfg.logColorSuccessLight,
            FIF.PALETTE,
            self.tr("Success color"),
            self.tr("Set the color for success level logs"),
            parent=self.logGroupCard,
        )
        self.logColorWarningCard = ColorSettingCard(
            cfg.logColorWarningDark if isDarkTheme() else cfg.logColorWarningLight,
            FIF.PALETTE,
            self.tr("Warning color"),
            self.tr("Set the color for warning level logs"),
            parent=self.logGroupCard,
        )
        self.logColorErrorCard = ColorSettingCard(
            cfg.logColorErrorDark if isDarkTheme() else cfg.logColorErrorLight,
            FIF.PALETTE,
            self.tr("Error color"),
            self.tr("Set the color for error level logs"),
            parent=self.logGroupCard,
        )
        self.logColorCriticalCard = ColorSettingCard(
            cfg.logColorCriticalDark if isDarkTheme() else cfg.logColorCriticalLight,
            FIF.PALETTE,
            self.tr("Critical color"),
            self.tr("Set the color for critical level logs"),
            parent=self.logGroupCard,
        )

        # 添加新的卡片到布局
        self.logGroupCard.viewLayout.addWidget(self.logColorTraceCard)
        self.logGroupCard.viewLayout.addWidget(self.logColorDebugCard)
        self.logGroupCard.viewLayout.addWidget(self.logColorInfoCard)
        self.logGroupCard.viewLayout.addWidget(self.logColorSuccessCard)
        self.logGroupCard.viewLayout.addWidget(self.logColorWarningCard)
        self.logGroupCard.viewLayout.addWidget(self.logColorErrorCard)
        self.logGroupCard.viewLayout.addWidget(self.logColorCriticalCard)

        # 调整布局大小
        self.logGroupCard._adjustViewSize()

    # ------------------------------------------------------------------ #
    #  更新检查
    # ------------------------------------------------------------------ #
    def initUpdateChecker(self):
        """初始化更新检查器（由外部在合适时机调用）"""
        self._updateChecker = UpdateChecker(self)
        self._updateChecker.checking.connect(self._onUpdateChecking)
        self._updateChecker.result_ready.connect(self._onUpdateResult)
        signalBus.checkUpdateSig.connect(self._updateChecker.check)

    def checkUpdateOnStartup(self):
        """启动时静默检查（由 MainWindow 在初始化后调用）"""
        if cfg.get(cfg.checkUpdateAtStartUp):
            if not hasattr(self, "_updateChecker"):
                self.initUpdateChecker()
            self._updateChecker.check()

    def _onUpdateChecking(self):
        """检查开始：按钮进入加载态"""
        self.aboutCard.button.setEnabled(False)
        self.aboutCard.button.setText(self.tr("Checking..."))

    def _onUpdateResult(self, result: UpdateResult):
        """检查完成：恢复按钮并展示结果"""
        self.aboutCard.button.setEnabled(True)
        self.aboutCard.button.setText(self.tr("Check update"))

        parent = self.window()

        if result.error and not result.no_release:
            # 网络错误 / 未知错误
            Notification.error(
                self.tr("Check update"),
                result.error,
                duration=5000,
                position=NotifyPosition.TOP_RIGHT,
                parent=parent,
            )
        elif result.no_release:
            # 仓库尚未发布任何 Release
            Notification.info(
                self.tr("Check update"),
                self.tr("Currently a development version, no release available."),
                duration=4000,
                position=NotifyPosition.TOP_RIGHT,
                parent=parent,
            )
        elif result.is_latest:
            # 已是最新版本
            Notification.success(
                self.tr("Check update"),
                self.tr("Already the latest version: ") + result.current_version,
                duration=3000,
                position=NotifyPosition.TOP_RIGHT,
                parent=parent,
            )
        elif result.has_update:
            # 发现新版本
            InfoBar.info(
                title=self.tr("New version available"),
                content=f"{result.current_version}  →  {result.latest_version}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=-1,
                parent=parent,
            )
            # 额外打开 Release 页面
            if result.release_url:
                QDesktopServices.openUrl(QUrl(result.release_url))

    def set_autostart(self, enabled: bool) -> bool:
        """设置开机自启动

        Args:
            enabled: 是否启用自启动

        Returns:
            bool: 设置是否成功
        """
        try:
            if sys.platform == "win32":
                return self._set_windows_autostart(enabled)
            elif sys.platform.startswith("linux"):
                return self._set_linux_autostart(enabled)
            else:
                return False
        except Exception as e:
            # logger.exception(f"设置开机自启动失败: {e}")
            return False

    def _set_windows_autostart(self, enabled: bool) -> bool:
        """设置Windows开机自启动"""
        try:
            import winreg
        except Exception:
            return False

        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        try:
            # KEY_SET_VALUE 已包含写权限，OpenKey 失败时用 CreateKey 兜底
            try:
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE
                )
            except OSError:
                key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)

            with key:
                if enabled:
                    if getattr(sys, "frozen", False):
                        cmd = f'"{sys.executable}"'
                    else:
                        root = Path(__file__).resolve().parents[2]
                        main_py = root / "main.py"
                        cmd = f'"{sys.executable}" "{str(main_py)}"'
                    winreg.SetValueEx(key, APPLY_NAME, 0, winreg.REG_SZ, cmd)
                else:
                    try:
                        winreg.DeleteValue(key, APPLY_NAME)
                    except OSError:
                        pass  # 键值不存在时忽略
            return True
        except Exception:
            return False

    def _set_linux_autostart(self, enabled: bool) -> bool:
        """设置Linux开机自启动"""
        autostart_dir = Path.home() / ".config" / "autostart"
        autostart_dir.mkdir(parents=True, exist_ok=True)
        desktop = autostart_dir / f"{APPLY_NAME}.desktop"

        if enabled:
            if getattr(sys, "frozen", False):
                exec_cmd = f'"{sys.executable}"'
            else:
                root = Path(__file__).resolve().parents[2]
                main_py = root / "main.py"
                exec_cmd = f'{sys.executable} "{str(main_py)}"'
            content = (
                f"[Desktop Entry]\n"
                f"Type=Application\n"
                f"Name={APPLY_NAME}\n"
                f"Exec={exec_cmd}\n"
                f"Icon=application-x-executable\n"
                f"X-GNOME-Autostart-enabled=true\n"
            )
            desktop.write_text(content, encoding="utf-8")
        else:
            if desktop.exists():
                desktop.unlink()

        return True

    def __on_autostart_changed(self, checked):
        cfg.set(cfg.autoRun, checked)
        ok = self.set_autostart(checked)
        if ok:
            if checked:
                Notification.success(
                    self.tr("auto start up"),
                    self.tr("enable"),
                    parent=self.window(),
                )
            else:
                Notification.info(
                    self.tr("auto start up"),
                    self.tr("disable"),
                    parent=self.window(),
                )
        else:
            Notification.error(
                self.tr("auto start up"),
                self.tr("failure"),
                parent=self.window(),
            )