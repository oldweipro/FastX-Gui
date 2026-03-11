# ==================================================
# 悬浮窗设置面板 - 独立 Demo 版本
# 替代原项目 floating_window_management.py
# 无外部项目依赖，所有文本硬编码中文
# ==================================================

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout
from qfluentwidgets import (
    ComboBox,
    GroupHeaderCardWidget,
    LineEdit,
    PushButton,
    SpinBox,
    SwitchButton,
    MessageBox,
    FluentIcon,
)

from config import readme_settings_async, update_settings

# 固定 SpinBox 宽度
_SPINBOX_W = 180


# --------------------------------------------------
# 多选 ComboBox（简化版，替代原项目 MultiSelectionComboBox）
# --------------------------------------------------

from PySide6.QtCore import Qt, QPoint
from PySide6.QtWidgets import (
    QListWidget, QListWidgetItem, QAbstractItemView,
    QFrame, QVBoxLayout as _QVL,
)
from qfluentwidgets import PushButton as _FBtn


class MultiSelectionComboBox(_FBtn):
    """
    简易多选下拉框：点击弹出浮层列表，支持最少选中数限制
    """
    checkedDataChanged = Signal(list)

    def __init__(self, minimum_checked: int = 1, parent=None):
        super().__init__(parent)
        self._minimum_checked = minimum_checked
        self._items: list[tuple[str, str]] = []   # (label, userData)
        self._checked: set[str] = set()
        self._popup: QFrame | None = None
        self.clicked.connect(self._show_popup)
        self._update_button_text()

    def addItem(self, text: str, userData: str = ""):
        self._items.append((text, userData or text))
        self._update_button_text()

    def setCheckedData(self, keys: list[str]):
        self._checked = set(keys) & {u for _, u in self._items}
        if not self._checked and self._items:
            self._checked = {self._items[0][1]}
        self._update_button_text()

    def checkedData(self) -> list[str]:
        order = [u for _, u in self._items if u in self._checked]
        return order

    def _update_button_text(self):
        labels = [t for t, u in self._items if u in self._checked]
        self.setText(", ".join(labels) if labels else "请选择")

    def _show_popup(self):
        if self._popup and self._popup.isVisible():
            self._popup.close()
            return
        popup = QFrame(None)
        popup.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        popup.setAttribute(Qt.WA_TranslucentBackground)
        popup.setStyleSheet(
            "background: white; border-radius: 8px; border: 1px solid rgba(0,0,0,20);"
        )
        lay = _QVL(popup)
        lay.setContentsMargins(4, 4, 4, 4)
        lay.setSpacing(2)

        list_w = QListWidget()
        list_w.setSelectionMode(QAbstractItemView.NoSelection)
        list_w.setStyleSheet("border: none; background: transparent;")

        for label, userData in self._items:
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, userData)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if userData in self._checked else Qt.Unchecked)
            list_w.addItem(item)

        list_w.itemChanged.connect(lambda i: self._on_item_toggled(i, list_w))
        lay.addWidget(list_w)

        popup.resize(220, min(40 * len(self._items) + 10, 300))
        gp = self.mapToGlobal(QPoint(0, self.height()))
        popup.move(gp)
        popup.show()
        self._popup = popup

    def _on_item_toggled(self, item: QListWidgetItem, list_w: QListWidget):
        userData = item.data(Qt.UserRole)
        if item.checkState() == Qt.Checked:
            self._checked.add(userData)
        else:
            if len(self._checked) <= self._minimum_checked:
                # 不允许取消最后一个选中
                item.setCheckState(Qt.Checked)
                return
            self._checked.discard(userData)
        self._update_button_text()
        self.checkedDataChanged.emit(self.checkedData())


# --------------------------------------------------
# 通用图标占位（使用 FluentIcon 替代原项目 get_theme_icon）
# --------------------------------------------------

def _icon(name: str):
    """按图标名返回 FluentIcon，找不到或属性不存在时均返回 SETTING"""
    _lookup = {
        "ic_fluent_desktop_sync_20_filled":    "SYNC",
        "ic_fluent_brightness_high_20_filled": "BRIGHTNESS",
        "ic_fluent_pin_20_filled":             "PIN",
        "ic_fluent_gesture_20_filled":         "FINGERPRINT",
        "ic_fluent_lock_open_20_filled":       "SETTING",
        "ic_fluent_panel_right_20_filled":     "LAYOUT",
        "ic_fluent_arrow_reset_20_filled":     "ROTATE",
        "ic_fluent_button_20_filled":          "DEVELOPER_TOOLS",
        "ic_fluent_align_left_20_filled":      "ALIGNMENT_LEFT",
        "ic_fluent_design_ideas_20_filled":    "PALETTE",
        "ic_fluent_resize_20_filled":          "ZOOM_IN",
        "ic_fluent_dark_theme_20_filled":      "CONSTRACT",
        "ic_fluent_timer_20_filled":           "STOP_WATCH",
        "ic_fluent_window_ad_20_filled":       "MINIMIZE",
        "ic_fluent_window_20_filled":          "TILES",
    }
    attr = _lookup.get(name, "SETTING")
    return getattr(FluentIcon, attr, FluentIcon.SETTING)


# --------------------------------------------------
# 工厂函数：创建 SwitchButton
# --------------------------------------------------

def _make_switch(section: str, key: str, off_text: str = "关闭", on_text: str = "开启") -> SwitchButton:
    sw = SwitchButton()
    sw.setOffText(off_text)
    sw.setOnText(on_text)
    sw.setChecked(bool(readme_settings_async(section, key)))
    sw.checkedChanged.connect(lambda v: update_settings(section, key, v))
    return sw


# ==================================================
# 基础设置卡片
# ==================================================

class BasicSettingsCard(GroupHeaderCardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("基础设置")
        self.setBorderRadius(8)
        s = "floating_window_management"

        # 启动时显示
        sw_startup = _make_switch(s, "startup_display_floating_window")
        self.addGroup(_icon("ic_fluent_desktop_sync_20_filled"),
                      "启动时显示悬浮窗", "软件启动时是否自动显示悬浮窗", sw_startup)

        # 透明度
        sp_opacity = SpinBox()
        sp_opacity.setFixedWidth(_SPINBOX_W)
        sp_opacity.setRange(0, 100)
        sp_opacity.setSuffix("%")
        sp_opacity.setValue(int(float(readme_settings_async(s, "floating_window_opacity") or 0.8) * 100))
        sp_opacity.valueChanged.connect(lambda v: update_settings(s, "floating_window_opacity", v / 100))
        self.addGroup(_icon("ic_fluent_brightness_high_20_filled"),
                      "悬浮窗透明度", "调整悬浮窗的透明程度（0% 完全透明，100% 完全不透明）", sp_opacity)

        # 置顶模式
        cb_topmost = ComboBox()
        cb_topmost.addItems(["不置顶", "普通置顶", "UIA 置顶（需要管理员）"])
        cb_topmost.setCurrentIndex(int(readme_settings_async(s, "floating_window_topmost_mode") or 1))
        cb_topmost.currentIndexChanged.connect(lambda i: update_settings(s, "floating_window_topmost_mode", i))
        self.addGroup(_icon("ic_fluent_pin_20_filled"),
                      "置顶模式", "控制悬浮窗是否保持在其他窗口上方", cb_topmost)

        # 可拖动
        sw_drag = _make_switch(s, "floating_window_draggable")
        self.addGroup(_icon("ic_fluent_gesture_20_filled"),
                      "允许拖动", "是否允许拖拽移动悬浮窗位置", sw_drag)

        # 长按拖动时间
        sp_lp = SpinBox()
        sp_lp.setFixedWidth(_SPINBOX_W)
        sp_lp.setRange(50, 3000)
        sp_lp.setSingleStep(100)
        sp_lp.setSuffix(" ms")
        sp_lp.setValue(int(readme_settings_async(s, "floating_window_long_press_duration") or 150))
        sp_lp.valueChanged.connect(lambda v: update_settings(s, "floating_window_long_press_duration", v))
        self.addGroup(_icon("ic_fluent_gesture_20_filled"),
                      "长按触发拖动的时间", "鼠标按住多长时间后才允许拖动（毫秒）", sp_lp)

        # 无焦点模式
        sw_focus = _make_switch(s, "do_not_steal_focus")
        self.addGroup(_icon("ic_fluent_lock_open_20_filled"),
                      "无焦点模式", "启用后悬浮窗点击不会抢夺当前窗口焦点", sw_focus)

        # 扩展闪抽组件
        sw_extend = _make_switch(s, "extend_quick_draw_component")
        self.addGroup(_icon("ic_fluent_panel_right_20_filled"),
                      "扩展闪抽组件", "在闪抽按钮旁显示下拉箭头，可快速切换班级/筛选条件", sw_extend)

        # 重置位置
        btn_reset = PushButton("重置位置")
        btn_reset.clicked.connect(lambda: (
            update_settings("float_position", "x", 100),
            update_settings("float_position", "y", 100),
        ))
        self.addGroup(_icon("ic_fluent_arrow_reset_20_filled"),
                      "重置悬浮窗位置", "将悬浮窗移回屏幕左上角（100, 100）", btn_reset)


# ==================================================
# 外观设置卡片
# ==================================================

class AppearanceSettingsCard(GroupHeaderCardWidget):
    appearance_settings_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("外观设置")
        self.setBorderRadius(8)
        s = "floating_window_management"

        # 按钮控制（多选）
        self._btn_combo = MultiSelectionComboBox(minimum_checked=1)
        btn_labels = {
            "roll_call": "点名",
            "quick_draw": "闪抽",
            "lottery": "抽奖",
            "face_draw": "人脸",
            "timer": "计时",
        }
        for key, label in btn_labels.items():
            self._btn_combo.addItem(label, userData=key)
        self._btn_combo.setCheckedData(
            self._normalize_button_control(readme_settings_async(s, "floating_window_button_control"))
        )
        self._btn_combo.checkedDataChanged.connect(self._on_btn_combo_changed)
        self.addGroup(_icon("ic_fluent_button_20_filled"),
                      "显示的按钮", "选择悬浮窗上要显示的功能按钮", self._btn_combo)

        # 排列方式
        cb_placement = ComboBox()
        cb_placement.addItems(["双行网格", "垂直排列", "水平排列"])
        cb_placement.setCurrentIndex(int(readme_settings_async(s, "floating_window_placement") or 0))
        cb_placement.currentIndexChanged.connect(self._make_updater(s, "floating_window_placement"))
        self.addGroup(_icon("ic_fluent_align_left_20_filled"),
                      "按钮排列方式", "控制悬浮窗按钮的排列方向", cb_placement)

        # 显示样式
        cb_style = ComboBox()
        cb_style.addItems(["图标+文字", "仅图标", "仅文字"])
        cb_style.setCurrentIndex(int(readme_settings_async(s, "floating_window_display_style") or 0))
        cb_style.currentIndexChanged.connect(self._make_updater(s, "floating_window_display_style"))
        self.addGroup(_icon("ic_fluent_design_ideas_20_filled"),
                      "按钮显示样式", "控制按钮是显示图标、文字还是两者都显示", cb_style)

        # 大小
        cb_size = ComboBox()
        cb_size.addItems(["超级小", "超小", "小", "中（默认）", "大", "超大", "超级大"])
        cb_size.setCurrentIndex(int(readme_settings_async(s, "floating_window_size") or 3))
        cb_size.currentIndexChanged.connect(self._make_updater(s, "floating_window_size"))
        self.addGroup(_icon("ic_fluent_resize_20_filled"),
                      "悬浮窗大小", "调整按钮与图标的整体尺寸", cb_size)

        # 主题
        cb_theme = ComboBox()
        cb_theme.addItems(["跟随系统", "浅色", "深色"])
        cb_theme.setCurrentIndex(int(readme_settings_async(s, "floating_window_theme") or 0))
        cb_theme.currentIndexChanged.connect(self._make_updater(s, "floating_window_theme"))
        self.addGroup(_icon("ic_fluent_dark_theme_20_filled"),
                      "悬浮窗主题", "单独控制悬浮窗的浅色/深色外观（不影响主界面）", cb_theme)

    def _make_updater(self, section: str, key: str):
        def handler(index: int):
            update_settings(section, key, index)
            self.appearance_settings_changed.emit()
        return handler

    def _on_btn_combo_changed(self, keys: list[str]):
        update_settings("floating_window_management", "floating_window_button_control", keys)
        self.appearance_settings_changed.emit()

    @staticmethod
    def _normalize_button_control(value) -> list[str]:
        allowed = {"roll_call", "quick_draw", "lottery", "face_draw", "timer"}
        if isinstance(value, list):
            keys = [v.strip() for v in value if isinstance(v, str) and v.strip() in allowed]
            return keys or ["roll_call"]
        combos = [
            ["roll_call"], ["quick_draw"], ["lottery"],
            ["roll_call", "quick_draw"], ["roll_call", "lottery"],
            ["quick_draw", "lottery"], ["roll_call", "quick_draw", "lottery"],
            ["timer"], ["roll_call", "timer"], ["quick_draw", "timer"],
            ["lottery", "timer"], ["roll_call", "quick_draw", "timer"],
            ["roll_call", "lottery", "timer"], ["quick_draw", "lottery", "timer"],
            ["roll_call", "quick_draw", "lottery", "timer"],
        ]
        try:
            idx = max(0, min(int(value or 0), len(combos) - 1))
        except Exception:
            idx = 0
        return combos[idx]


# ==================================================
# 贴边设置卡片
# ==================================================

class EdgeSettingsCard(GroupHeaderCardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("贴边设置")
        self.setBorderRadius(8)
        s = "floating_window_management"

        # 贴边开关
        sw = _make_switch(s, "floating_window_stick_to_edge")
        self.addGroup(_icon("ic_fluent_pin_20_filled"),
                      "启用贴边自动隐藏",
                      "悬浮窗拖到屏幕边缘后自动缩进，鼠标经过时展开", sw)

        # 回收秒数
        sp = SpinBox()
        sp.setFixedWidth(_SPINBOX_W)
        sp.setRange(1, 60)
        sp.setSuffix(" s")
        sp.setValue(int(readme_settings_async(s, "floating_window_stick_to_edge_recover_seconds") or 5))
        sp.valueChanged.connect(lambda v: update_settings(s, "floating_window_stick_to_edge_recover_seconds", v))
        self.addGroup(_icon("ic_fluent_timer_20_filled"),
                      "自动隐藏延迟",
                      "鼠标离开后等待多少秒再收回边缘", sp)

        # 指示器样式
        cb = ComboBox()
        cb.addItems(["图标样式", "文字样式", "箭头样式"])
        cb.setCurrentIndex(int(readme_settings_async(s, "floating_window_stick_to_edge_display_style") or 0))
        cb.currentIndexChanged.connect(
            lambda i: update_settings(s, "floating_window_stick_to_edge_display_style", i)
        )
        self.addGroup(_icon("ic_fluent_desktop_sync_20_filled"),
                      "收纳指示器样式",
                      "控制贴边后显示的小按钮外观", cb)


# ==================================================
# 前台隐藏设置卡片
# ==================================================

class ForegroundHidingCard(GroupHeaderCardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("前台应用隐藏")
        self.setBorderRadius(8)
        s = "floating_window_management"

        # 启用开关
        enabled = bool(readme_settings_async(s, "hide_floating_window_on_foreground"))
        sw = SwitchButton()
        sw.setOffText("关闭")
        sw.setOnText("开启")
        sw.setChecked(enabled)
        sw.checkedChanged.connect(lambda v: (
            update_settings(s, "hide_floating_window_on_foreground", v),
            self._set_inputs_enabled(v),
        ))
        self.addGroup(_icon("ic_fluent_window_ad_20_filled"),
                      "前台特定窗口时隐藏",
                      "当指定的窗口处于前台时自动隐藏悬浮窗", sw)

        # 窗口标题
        self._le_titles = LineEdit()
        self._le_titles.setFixedWidth(_SPINBOX_W)
        self._le_titles.setPlaceholderText("分号分隔，如: 钉钉;腾讯会议")
        self._le_titles.setText(
            str(readme_settings_async(s, "hide_floating_window_on_foreground_window_titles") or "")
        )
        self._le_titles.editingFinished.connect(
            lambda: update_settings(s, "hide_floating_window_on_foreground_window_titles",
                                    self._le_titles.text().strip())
        )
        self.addGroup(_icon("ic_fluent_window_20_filled"),
                      "窗口标题关键词",
                      "包含这些关键词的窗口处于前台时隐藏悬浮窗（分号分隔）", self._le_titles)

        # 进程名称
        self._le_procs = LineEdit()
        self._le_procs.setFixedWidth(_SPINBOX_W)
        self._le_procs.setPlaceholderText("分号分隔，如: dingtalk.exe;Teams.exe")
        self._le_procs.setText(
            str(readme_settings_async(s, "hide_floating_window_on_foreground_process_names") or "")
        )
        self._le_procs.editingFinished.connect(
            lambda: update_settings(s, "hide_floating_window_on_foreground_process_names",
                                    self._le_procs.text().strip())
        )
        self.addGroup(_icon("ic_fluent_window_20_filled"),
                      "进程名称关键词",
                      "指定进程处于前台时隐藏悬浮窗（分号分隔）", self._le_procs)

        self._set_inputs_enabled(enabled)

    def _set_inputs_enabled(self, enabled: bool):
        for w in (self._le_titles, self._le_procs):
            try:
                w.setEnabled(bool(enabled))
            except Exception:
                pass


# ==================================================
# 设置面板主容器
# ==================================================

class FloatingWindowSettingsPanel(QWidget):
    """悬浮窗设置面板，包含所有设置卡片"""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.basic_card       = BasicSettingsCard(self)
        self.appearance_card  = AppearanceSettingsCard(self)
        self.edge_card        = EdgeSettingsCard(self)
        self.fg_hiding_card   = ForegroundHidingCard(self)

        layout.addWidget(self.basic_card)
        layout.addWidget(self.appearance_card)
        layout.addWidget(self.edge_card)
        layout.addWidget(self.fg_hiding_card)

        self._levitation_window = None

    def set_levitation_window(self, win):
        self._levitation_window = win
        self.appearance_card.appearance_settings_changed.connect(
            lambda: win.rebuild_ui() if win else None
        )
