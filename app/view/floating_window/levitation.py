# 标准库导入
import ctypes
import os
import time
from typing import Any

from PySide6.QtCore import *
from PySide6.QtGui import *

# 第三方库导入
from PySide6.QtWidgets import *
from qfluentwidgets import *
from qfluentwidgets import FluentIcon as FIF

# 本地模块导入
from ...common.config import cfg, TopmostMode


class LevitationWindow(QWidget):
    """
    悬浮窗窗口类
    提供可拖拽、贴边隐藏、主题切换、多按钮布局等功能的悬浮窗口
    """

    # ==================== 信号定义 ====================
    rollCallRequested = Signal()
    quickDrawRequested = Signal()
    lotteryRequested = Signal()
    faceDrawRequested = Signal()
    timerRequested = Signal()
    visibilityChanged = Signal(bool)
    positionChanged = Signal(int, int)

    # ==================== 类常量 ====================
    DEFAULT_OPACITY = 0.8
    DEFAULT_PLACEMENT = 0
    DEFAULT_DISPLAY_STYLE = 0
    DEFAULT_EDGE_THRESHOLD = 5
    DEFAULT_RETRACT_SECONDS = 5
    DEFAULT_LONG_PRESS_MS = 150
    DEFAULT_BUTTON_SIZE = QSize(50, 50)
    DEFAULT_ICON_SIZE = QSize(24, 24)
    DEFAULT_SPACING = 6
    DEFAULT_MARGINS = 6
    DRAG_THRESHOLD = 12
    MIN_DRAG_TIME = 100

    # 按钮标签文本
    BUTTON_LABELS = {
        "roll_call": "点名",
        "quick_draw": "闪抽",
        "lottery": "抽奖",
        "face_draw": "人脸",
        "timer": "计时",
        "settings": "设置",
        "close": "关闭",
    }

    BUTTON_ICONS = {
        "roll_call": "ic_fluent_people_20_filled",
        "quick_draw": "ic_fluent_flash_20_filled",
        "lottery": "ic_fluent_gift_20_filled",
        "face_draw": "ic_fluent_video_person_sparkle_20_filled",
        "timer": "ic_fluent_timer_20_filled",
        "settings": "ic_fluent_settings_20_filled",
        "close": "ic_fluent_dismiss_20_filled",
    }

    def __init__(self, parent=None):
        """初始化悬浮窗窗口"""
        super().__init__(parent)
        self._startup_initial_show = True
        self._close_guard_enabled = True
        self._close_guard_last_log_ms = 0

        # ==================== 基础设置 ====================
        self._setup_window_properties()

        # ==================== 拖拽相关属性 ====================
        self._init_drag_properties()

        # ==================== 贴边隐藏属性 ====================
        self._init_edge_properties()

        # ==================== UI相关属性 ====================
        self._init_ui_properties()

        # ==================== 置顶状态 ====================
        self._init_topmost_state()

        # ==================== 初始化配置 ====================
        self._init_settings()

        # ==================== 构建UI ====================
        self._build_ui()
        self._apply_window()
        self._apply_position()
        self._install_drag_filters()

        # ==================== 信号连接 ====================
        self._connect_signals()

        # ==================== 主题应用 ====================
        self._apply_theme_style()

        # ==================== 边缘感应定时器 ====================
        self._edge_detect_timer = QTimer(self)
        self._edge_detect_timer.timeout.connect(self._detect_mouse_near_edge)
        self._edge_detect_timer.start(100)

        if not self._visible_on_start:
            QTimer.singleShot(0, lambda: self._check_edge_proximity(immediate=True))

    # ==================== 初始化方法 ====================

    def _setup_window_properties(self):
        """设置窗口基础属性"""
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._base_flags = Qt.FramelessWindowHint | Qt.Tool | Qt.NoDropShadowWindowHint
        self.setWindowFlags(self._base_flags | Qt.WindowStaysOnTopHint)

    def _init_drag_properties(self):
        """初始化拖拽相关属性"""
        self._drag_timer = QTimer(self)
        self._drag_timer.setSingleShot(True)
        self._drag_timer.timeout.connect(self._begin_drag)
        self._dragging = False
        self._press_pos = QPoint()
        self._press_time = 0

    def _init_edge_properties(self):
        """初始化贴边隐藏相关属性"""
        self._indicator = None
        self._retract_timer = QTimer(self)
        self._retract_timer.setSingleShot(True)
        self._retracted = False
        self._last_stuck = False
        self._edge_threshold = self.DEFAULT_EDGE_THRESHOLD
        self._stick_to_edge = True
        self._retract_seconds = self.DEFAULT_RETRACT_SECONDS
        self._long_press_ms = self.DEFAULT_LONG_PRESS_MS
        self.storage_window = None
        self.arrow_widget = None
        self.arrow_button = None

    def _init_ui_properties(self):
        """初始化UI相关属性"""
        self._container = QWidget(self)
        self._layout = None
        self._top = None
        self._bottom = None
        self._font_family = QFont().family()
        self._quick_draw_extend_panel = None
        self._quick_draw_extend_anchor = None
        self._quick_draw_extend_close_timer = QTimer(self)
        self._quick_draw_extend_close_timer.setSingleShot(True)
        self._quick_draw_extend_close_timer.timeout.connect(
            self._close_quick_draw_extend_panel
        )
        self._btn_size = self.DEFAULT_BUTTON_SIZE
        self._icon_size = self.DEFAULT_ICON_SIZE
        self._font_size = 10
        self._storage_btn_size = QSize(30, 30)
        self._storage_icon_size = QSize(18, 18)
        self._storage_font_size = 10
        self._spacing = self.DEFAULT_SPACING
        self._margins = self.DEFAULT_MARGINS
        self._placement = self.DEFAULT_PLACEMENT
        self._display_style = self.DEFAULT_DISPLAY_STYLE

    def _init_topmost_state(self):
        """初始化置顶状态"""
        self._periodic_topmost_timer = QTimer(self)
        self._periodic_topmost_timer.timeout.connect(lambda: self.raise_() if self.isVisible() and self._topmost_mode != 0 else None)
        self._uiaccess_funcs = None

    def _init_settings(self):
        """初始化设置配置"""
        try:
            # 从配置文件读取设置
            self._visible_on_start = cfg.get(cfg.startupDisplayFloatingWindow)
            self._opacity = cfg.get(cfg.floatingWindowOpacity) / 100.0

            # 布局设置
            self._placement = cfg.get(cfg.floatingWindowPlacement)
            self._display_style = cfg.get(cfg.floatingWindowDisplayStyle)

            # 拖拽设置
            self._draggable = cfg.get(cfg.floatingWindowDraggable)
            self._long_press_ms = cfg.get(cfg.floatingWindowLongPressDuration)

            # 贴边设置
            self._stick_to_edge = cfg.get(cfg.floatingWindowStickToEdge)
            self._retract_seconds = cfg.get(cfg.floatingWindowStickToEdgeRecoverSeconds)
            self._stick_indicator_style = cfg.get(cfg.floatingWindowStickToEdgeDisplayStyle)

            # 浮窗大小设置
            self._apply_size_setting(cfg.get(cfg.floatingWindowSize))

            # 无焦点模式设置
            self._do_not_steal_focus = cfg.get(cfg.doNotStealFocus)
            self._topmost_mode = cfg.get(cfg.floatingWindowTopmostMode).value

            # 主题设置
            self._floating_window_theme = cfg.get(cfg.floatingWindowTheme)

            # 扩展闪抽组件
            self._extend_quick_draw = cfg.get(cfg.extendQuickDrawComponent)

            # 按钮控制
            self._buttons_spec = self._normalize_button_control(cfg.get(cfg.floatingWindowButtonControl))

            # 前台隐藏设置
            self._hide_on_foreground_enabled = cfg.get(cfg.hideFloatingWindowOnForeground)
            self._hide_on_foreground_titles = self._split_match_list(
                cfg.get(cfg.hideFloatingWindowOnForegroundWindowTitles)
            )
            self._hide_on_foreground_processes = self._split_match_list(
                cfg.get(cfg.hideFloatingWindowOnForegroundProcessNames)
            )
            self._hidden_by_foreground = False
            self._pre_fg_main_visible = False
            self._pre_fg_arrow_visible = False
            self._suppress_visibility_tracking = False

            self._refresh_window_flags()

            # 前台隐藏定时器
            self._foreground_timer = QTimer(self)
            self._foreground_timer.setInterval(250)
            self._foreground_timer.timeout.connect(self._check_foreground_hide)
            if self._hide_on_foreground_enabled:
                self._foreground_timer.start()

            self._user_requested_visible = bool(self._visible_on_start)

        except Exception as e:
            # 如果配置读取失败，使用默认值
            print(f"浮窗配置读取失败，使用默认值: {e}")
            self._visible_on_start = False
            self._opacity = self.DEFAULT_OPACITY
            self._placement = self.DEFAULT_PLACEMENT
            self._display_style = self.DEFAULT_DISPLAY_STYLE
            self._draggable = True
            self._long_press_ms = self.DEFAULT_LONG_PRESS_MS
            self._stick_to_edge = True
            self._retract_seconds = self.DEFAULT_RETRACT_SECONDS
            self._stick_indicator_style = 0
            self._apply_size_setting(1)
            self._do_not_steal_focus = False
            self._topmost_mode = 1
            self._floating_window_theme = 0
            self._extend_quick_draw = False
            self._buttons_spec = ["roll_call", "quick_draw", "lottery"]
            self._hide_on_foreground_enabled = False
            self._hide_on_foreground_titles = []
            self._hide_on_foreground_processes = []
            self._hidden_by_foreground = False
            self._pre_fg_main_visible = False
            self._pre_fg_arrow_visible = False
            self._suppress_visibility_tracking = False
            self._user_requested_visible = False
            self._refresh_window_flags()

        # 贴边隐藏功能配置
        self._init_edge_hide_settings()

        # 连接配置变更信号
        self._connect_config_signals()

    def _init_edge_hide_settings(self):
        """初始化贴边隐藏功能设置"""
        self.floating_window_stick_to_edge = self._stick_to_edge
        self.custom_retract_time = self._retract_seconds
        self.custom_display_mode = self._stick_indicator_style
        self._retracted = False

    def _apply_size_setting(self, size_idx: int):
        """应用浮窗大小设置"""
        presets = {
            0: (QSize(20, 20), QSize(6, 6), 4, QSize(20, 20), QSize(12, 12), 6),
            1: (QSize(30, 30), QSize(12, 12), 6, QSize(25, 25), QSize(15, 15), 8),
            2: (QSize(40, 40), QSize(18, 18), 8, QSize(28, 28), QSize(16, 16), 9),
            3: (QSize(50, 50), QSize(22, 22), 10, QSize(30, 30), QSize(18, 18), 10),
            4: (QSize(60, 60), QSize(28, 28), 12, QSize(35, 35), QSize(20, 20), 11),
            5: (QSize(70, 70), QSize(34, 34), 14, QSize(40, 40), QSize(22, 22), 12),
            6: (QSize(80, 80), QSize(40, 40), 16, QSize(45, 45), QSize(24, 24), 13),
        }
        (self._btn_size, self._icon_size, self._font_size,
         self._storage_btn_size, self._storage_icon_size, self._storage_font_size) = \
            presets.get(size_idx, presets[3])

    def _normalize_button_control(self, value) -> list[str]:
        """规范化按钮控制值"""
        allowed = {"roll_call", "quick_draw", "lottery", "face_draw", "timer", "settings", "close"}
        if isinstance(value, list):
            keys = [v.strip() for v in value if isinstance(v, str) and v.strip() in allowed]
            return keys or ["roll_call", "quick_draw", "lottery"]
        # 如果是整数索引，映射到组合
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
            idx = max(0, min(int(value or 3), len(combos) - 1))
        except Exception:
            idx = 3
        return combos[idx]

    def _split_match_list(self, raw: str) -> list[str]:
        """分割匹配列表"""
        return [
            s.lower() for part in (raw or "").replace("\n", ";").split(";")
            if (s := part.strip())
        ]

    def _connect_signals(self):
        """连接信号"""
        # 连接主题变更信号
        try:
            cfg.themeChanged.connect(self._on_theme_changed)
        except Exception:
            pass

    def _connect_config_signals(self):
        """连接配置变更信号"""
        try:
            cfg.floatingWindowOpacity.valueChanged.connect(self._on_opacity_changed)
            cfg.floatingWindowDraggable.valueChanged.connect(self._on_draggable_changed)
            cfg.floatingWindowLongPressDuration.valueChanged.connect(self._on_long_press_changed)
            cfg.floatingWindowStickToEdge.valueChanged.connect(self._on_stick_to_edge_changed)
            cfg.floatingWindowStickToEdgeRecoverSeconds.valueChanged.connect(self._on_retract_seconds_changed)
            cfg.floatingWindowSize.valueChanged.connect(self._on_size_changed)
            cfg.floatingWindowPlacement.valueChanged.connect(self._on_placement_changed)
            cfg.floatingWindowDisplayStyle.valueChanged.connect(self._on_display_style_changed)
            cfg.floatingWindowTopmostMode.valueChanged.connect(self._on_topmost_mode_changed)
            cfg.doNotStealFocus.valueChanged.connect(self._on_focus_mode_changed)
            cfg.floatingWindowTheme.valueChanged.connect(self._on_theme_setting_changed)
            cfg.extendQuickDrawComponent.valueChanged.connect(self._on_extend_quick_draw_changed)
            cfg.floatingWindowButtonControl.valueChanged.connect(self._on_button_control_changed)
            cfg.hideFloatingWindowOnForeground.valueChanged.connect(self._on_hide_on_foreground_changed)
            cfg.hideFloatingWindowOnForegroundWindowTitles.valueChanged.connect(self._on_hide_titles_changed)
            cfg.hideFloatingWindowOnForegroundProcessNames.valueChanged.connect(self._on_hide_processes_changed)
            cfg.floatingWindowStickToEdgeDisplayStyle.valueChanged.connect(self._on_indicator_style_changed)
        except Exception:
            pass

    def _on_opacity_changed(self, value):
        """透明度变更"""
        self._opacity = value / 100.0
        self.setWindowOpacity(self._opacity)

    def _on_draggable_changed(self, value):
        """可拖动状态变更"""
        self._draggable = value

    def _on_long_press_changed(self, value):
        """长按时间变更"""
        self._long_press_ms = value

    def _on_stick_to_edge_changed(self, value):
        """贴边隐藏开关变更"""
        self._stick_to_edge = value
        self.floating_window_stick_to_edge = value
        if not value and self._retracted:
            self._expand_from_edge()

    def _on_retract_seconds_changed(self, value):
        """收纳延迟时间变更"""
        self._retract_seconds = value
        self.custom_retract_time = value

    def _on_size_changed(self, value):
        """浮窗大小变更"""
        self._apply_size_setting(value)
        self.rebuild_ui()

    def _on_placement_changed(self, value):
        """布局方式变更"""
        self._placement = value
        self.rebuild_ui()

    def _on_display_style_changed(self, value):
        """显示样式变更"""
        self._display_style = value
        self.rebuild_ui()

    def _on_topmost_mode_changed(self, value):
        """置顶模式变更"""
        self._topmost_mode = value.value
        self._refresh_window_flags()
        if self._topmost_mode != 0 and not self._periodic_topmost_timer.isActive():
            self._periodic_topmost_timer.start(100)
        elif self._topmost_mode == 0 and self._periodic_topmost_timer.isActive():
            self._periodic_topmost_timer.stop()

    def _on_focus_mode_changed(self, value):
        """焦点模式变更"""
        self._do_not_steal_focus = value
        self._refresh_window_flags()

    def _on_theme_setting_changed(self, value):
        """主题设置变更"""
        self._floating_window_theme = value
        self.rebuild_ui()
        self._apply_theme_style()

    def _on_extend_quick_draw_changed(self, value):
        """扩展闪抽组件变更"""
        self._extend_quick_draw = value
        self._close_quick_draw_extend_panel()
        self.rebuild_ui()

    def _on_button_control_changed(self, value):
        """按钮控制变更"""
        self._buttons_spec = self._normalize_button_control(value)
        self.rebuild_ui()

    def _on_hide_on_foreground_changed(self, value):
        """前台隐藏开关变更"""
        self._hide_on_foreground_enabled = value
        if value:
            if not self._foreground_timer.isActive():
                self._foreground_timer.start()
        else:
            if self._foreground_timer.isActive():
                self._foreground_timer.stop()
            self._apply_foreground_hidden(False)

    def _on_hide_titles_changed(self, value):
        """隐藏窗口标题变更"""
        self._hide_on_foreground_titles = self._split_match_list(value)
        QTimer.singleShot(0, self._check_foreground_hide)

    def _on_hide_processes_changed(self, value):
        """隐藏进程名称变更"""
        self._hide_on_foreground_processes = self._split_match_list(value)
        QTimer.singleShot(0, self._check_foreground_hide)

    def _on_indicator_style_changed(self, value):
        """指示器样式变更"""
        self._stick_indicator_style = value
        # 如果箭头按钮存在且可见，更新其样式
        if self.arrow_widget and self.arrow_widget.isVisible():
            direction = "right" if self.x() < 0 else "left"
            self._update_arrow_button_style(direction)

    def _on_theme_changed(self):
        """主题变更处理"""
        if self._floating_window_theme == 0:  # 跟随系统
            self.rebuild_ui()
        self._apply_theme_style()

    def rebuild_ui(self):
        """重新构建浮窗UI"""
        # 关闭扩展面板
        self._close_quick_draw_extend_panel()

        # 清除现有按钮
        self._clear_buttons()

        # 重新创建容器布局
        container_layout = self._create_container_layout()

        # 设置新的布局
        old_layout = self._container.layout()
        if old_layout:
            QWidget().setLayout(old_layout)

        self._container.setLayout(container_layout)
        try:
            container_layout.setAlignment(Qt.AlignCenter)
        except Exception:
            pass

        # 重新添加按钮
        for i, spec in enumerate(self._buttons_spec):
            if spec == "quick_draw" and self._extend_quick_draw:
                btn = self._create_extended_quick_draw_widget()
            else:
                btn = self._create_button(spec)
            self._add_button(btn, i, len(self._buttons_spec))

        self._container.adjustSize()
        self.adjustSize()
        self._install_drag_filters()

    def _clear_buttons(self):
        """清除所有按钮"""
        for attr in ("_top", "_bottom"):
            w = getattr(self, attr, None)
            if w and w.layout():
                lay = w.layout()
                while lay.count():
                    item = lay.takeAt(0)
                    widget = item.widget()
                    if widget:
                        widget.deleteLater()
        lay = self._container.layout()
        if lay:
            while lay.count():
                item = lay.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()

    def _font(self, size):
        s = int(size) if size and int(size) > 0 else 8
        if s <= 0:
            s = 8
        f = QFont(self._font_family) if self._font_family else QFont()
        if s > 0:
            f.setPointSize(s)
        f.setWeight(QFont.Medium)
        return f

    def _apply_theme_style(self):
        """应用主题样式"""
        dark = self._is_dark()
        self._container.setAttribute(Qt.WA_StyledBackground, True)
        if dark:
            self._container.setStyleSheet(
                "background-color: rgba(32,32,32,180); border-radius: 12px; border: 1px solid rgba(255,255,255,20);"
            )
        else:
            self._container.setStyleSheet(
                "background-color: rgba(255,255,255,220); border-radius: 12px; border: 1px solid rgba(0,0,0,12);"
            )
        direction = "right" if self.x() < 0 else "left"
        self._update_arrow_button_style(direction)

    def _is_dark(self) -> bool:
        """判断是否深色主题"""
        idx = int(getattr(self, "_floating_window_theme", 0) or 0)
        if idx == 0:
            return isDarkTheme()
        return idx == 2

    def _text_color(self) -> str:
        """获取文本颜色"""
        return "rgba(255,255,255,230)" if self._is_dark() else "rgba(0,0,0,200)"

    def _refresh_window_flags(self):
        """刷新窗口标志"""
        no_focus = bool(getattr(self, "_do_not_steal_focus", False))
        try:
            self.setAttribute(Qt.WA_ShowWithoutActivating, no_focus)
        except Exception:
            pass
        flags = self._base_flags
        if getattr(self, "_topmost_mode", 1) != 0:
            flags |= Qt.WindowStaysOnTopHint
        if no_focus:
            flags |= Qt.WindowDoesNotAcceptFocus
        self.setWindowFlags(flags)
        if self.isVisible():
            prev = self._suppress_visibility_tracking
            self._suppress_visibility_tracking = True
            try:
                self.hide()
                self.show()
            finally:
                self._suppress_visibility_tracking = prev

        # 同步更新收纳指示器窗口的无焦点标志
        arrow = getattr(self, "arrow_widget", None)
        if arrow:
            try:
                af = Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.NoDropShadowWindowHint
                if no_focus:
                    af |= Qt.WindowDoesNotAcceptFocus
                arrow.setAttribute(Qt.WA_ShowWithoutActivating, no_focus)
                arrow_visible = arrow.isVisible()
                arrow.setWindowFlags(af)
                if arrow_visible:
                    arrow.show()
            except Exception:
                pass

    def _build_ui(self):
        """构建UI"""
        if not self._layout:
            self._layout = QHBoxLayout(self)
            self._layout.setContentsMargins(
                self.DEFAULT_MARGINS, self.DEFAULT_MARGINS,
                self.DEFAULT_MARGINS, self.DEFAULT_MARGINS
            )
            self._layout.addWidget(self._container)

        container_layout = self._create_container_layout()
        old = self._container.layout()
        if old:
            QWidget().setLayout(old)
        self._container.setLayout(container_layout)
        try:
            container_layout.setAlignment(Qt.AlignCenter)
        except Exception:
            pass

        for i, spec in enumerate(self._buttons_spec):
            if spec == "quick_draw" and self._extend_quick_draw:
                btn = self._create_extended_quick_draw_widget()
            else:
                btn = self._create_button(spec)
            self._add_button(btn, i, len(self._buttons_spec))

        self._container.adjustSize()
        self.adjustSize()
        self._install_drag_filters()

    def _create_container_layout(self):
        """创建容器布局"""
        for attr in ("_top", "_bottom"):
            w = getattr(self, attr, None)
            if w:
                w.deleteLater()
                setattr(self, attr, None)

        if self._placement == 1:
            lay = QVBoxLayout()
            lay.setContentsMargins(self._margins, self._margins, self._margins, self._margins)
            lay.setSpacing(self._spacing)
            return lay
        if self._placement == 2:
            lay = QHBoxLayout()
            lay.setContentsMargins(self._margins, self._margins, self._margins, self._margins)
            lay.setSpacing(self._spacing)
            return lay

        lay = QVBoxLayout()
        lay.setContentsMargins(self._margins, self._margins, self._margins, self._margins)
        lay.setSpacing(self._spacing)

        self._top = QWidget()
        self._top.setAttribute(Qt.WA_TranslucentBackground)
        self._bottom = QWidget()
        self._bottom.setAttribute(Qt.WA_TranslucentBackground)

        for sub, container in ((self._top, self._top), (self._bottom, self._bottom)):
            sub_lay = QHBoxLayout(container)
            sub_lay.setContentsMargins(0, 0, 0, 0)
            sub_lay.setSpacing(self._spacing)
            sub_lay.setAlignment(Qt.AlignCenter)

        lay.addWidget(self._top)
        lay.addWidget(self._bottom)
        return lay

    def _apply_window(self):
        """应用窗口设置"""
        self.setWindowOpacity(self._opacity)
        if self._visible_on_start:
            self.show()
        else:
            self.hide()

    def _apply_position(self):
        """应用位置设置"""
        try:
            x = cfg.get(cfg.floatingWindowPosX) if hasattr(cfg, "floatingWindowPosX") else 100
            y = cfg.get(cfg.floatingWindowPosY) if hasattr(cfg, "floatingWindowPosY") else 100
        except Exception:
            x = 100
            y = 100
        nx, ny = self._clamp_to_screen(x, y)
        self.move(nx, ny)

    def _clamp_to_screen(self, x, y):
        """限制窗口位置在屏幕内"""
        fg = self.frameGeometry()
        scr = QGuiApplication.screenAt(fg.center()) or QApplication.primaryScreen()
        geo = scr.availableGeometry()
        cx = max(geo.left(), min(x, geo.right() - self.width() + 1))
        cy = max(geo.top(), min(y, geo.bottom() - self.height() + 1))
        return cx, cy

    def _create_button(self, spec: str) -> QPushButton:
        """创建按钮"""
        # 获取按钮配置信息
        button_config = self._get_button_config(spec)
        icon = button_config["icon"]
        text = button_config["text"]

        # 根据显示样式创建不同类型的按钮
        if self._display_style == 1:
            btn = self._create_icon_only_button(icon)
        elif self._display_style == 2:
            btn = self._create_text_only_button(text)
        else:
            btn = self._create_composite_button(icon, text)

        # 连接信号
        btn.clicked.connect(lambda: self._handle_button_click(spec))
        btn.setAttribute(Qt.WA_TranslucentBackground)
        return btn

    def _get_button_config(self, spec: str) -> dict[str, Any]:
        """获取按钮配置信息"""
        from ...common.icon import UIcon

        button_configs = {
            "roll_call": {
                "icon": UIcon.get(self.BUTTON_ICONS["roll_call"]),
                "text": self.BUTTON_LABELS["roll_call"],
            },
            "quick_draw": {
                "icon": UIcon.get(self.BUTTON_ICONS["quick_draw"]),
                "text": self.BUTTON_LABELS["quick_draw"],
            },
            "lottery": {
                "icon": UIcon.get(self.BUTTON_ICONS["lottery"]),
                "text": self.BUTTON_LABELS["lottery"],
            },
            "face_draw": {
                "icon": UIcon.get(self.BUTTON_ICONS["face_draw"]),
                "text": self.BUTTON_LABELS["face_draw"],
            },
            "timer": {
                "icon": UIcon.get(self.BUTTON_ICONS["timer"]),
                "text": self.BUTTON_LABELS["timer"],
            },
            "settings": {
                "icon": FIF.SETTING,
                "text": self.BUTTON_LABELS["settings"],
            },
            "close": {
                "icon": FIF.CLOSE,
                "text": self.BUTTON_LABELS["close"],
            },
        }

        default_config = {
            "icon": FIF.HOME,
            "text": "主页",
        }

        return button_configs.get(spec, default_config)

    def _create_icon_only_button(self, icon) -> TransparentToolButton:
        """创建仅图标按钮"""
        btn = TransparentToolButton()
        btn.setIcon(icon)
        btn.setIconSize(self._icon_size)
        btn.setFixedSize(self._btn_size)
        btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        btn.setAttribute(Qt.WA_TranslucentBackground)
        btn.setStyleSheet("background: transparent; border: none;")
        return btn

    def _create_text_only_button(self, text: str) -> PushButton:
        """创建仅文本按钮"""
        btn = PushButton(text)
        btn.setFixedSize(self._btn_size)
        btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        btn.setFont(self._font(self._font_size))
        btn.setAttribute(Qt.WA_TranslucentBackground)
        btn.setStyleSheet(f"background: transparent; border: none; color: {self._text_color()};")
        return btn

    def _create_composite_button(self, icon, text: str) -> QPushButton:
        """创建图文复合按钮"""
        btn = QPushButton()
        layout = QVBoxLayout(btn)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(2)
        layout.setAlignment(Qt.AlignCenter)
        btn.setStyleSheet("background: transparent; border: none;")

        # 图标标签
        icon_label = self._create_icon_label(icon)
        layout.addWidget(icon_label)

        # 文本标签
        text_label = self._create_text_label(text)
        layout.addWidget(text_label)

        # 布局设置
        layout.setAlignment(Qt.AlignCenter)
        layout.setAlignment(icon_label, Qt.AlignCenter)
        layout.setAlignment(text_label, Qt.AlignCenter)

        btn.setFixedSize(self._btn_size)
        btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        btn.setAttribute(Qt.WA_TranslucentBackground)
        return btn

    def _create_icon_label(self, icon) -> TransparentToolButton:
        """创建图标标签（用于复合按钮）"""
        label = TransparentToolButton()
        label.setIcon(icon)
        label.setIconSize(self._icon_size)
        label.setFixedSize(self._icon_size)
        label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        label.setFocusPolicy(Qt.NoFocus)
        label.setStyleSheet("background: transparent; border: none;")
        return label

    def _create_text_label(self, text: str) -> QLabel:
        """创建文本标签（用于复合按钮）"""
        label = QLabel(text)
        label.setAlignment(Qt.AlignCenter)
        label.setFont(self._font(self._font_size))
        label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        label.setFocusPolicy(Qt.NoFocus)
        label.setStyleSheet(f"background: transparent; border: none; color: {self._text_color()};")
        return label

    def _add_button(self, btn, index, total):
        """添加按钮到布局"""
        if self._placement in (1, 2):
            self._container.layout().addWidget(btn, 0, Qt.AlignCenter)
            return
        split = (total + 1) // 2
        target = self._top if index < split else self._bottom
        target.layout().addWidget(btn, 0, Qt.AlignCenter)

    def _handle_button_click(self, spec):
        """处理按钮点击事件"""
        from ...common.signal_bus import signalBus

        signal_map = {
            "roll_call": self.rollCallRequested,
            "quick_draw": self.quickDrawRequested,
            "lottery": self.lotteryRequested,
            "face_draw": self.faceDrawRequested,
            "timer": self.timerRequested,
        }

        if spec in signal_map:
            signal_map[spec].emit()
        elif spec == "settings":
            # 打开设置界面
            try:
                signalBus.showMainWindow.emit()
                QTimer.singleShot(100, lambda: self._switch_to_settings())
            except Exception as e:
                print(f"打开设置失败: {e}")
        elif spec == "close":
            # 关闭浮窗
            try:
                cfg.set(cfg.startupDisplayFloatingWindow, False)
                self.hide()
                if self.parent() and hasattr(self.parent(), "floating_window_action"):
                    self.parent().floating_window_action.setChecked(False)
                    self.parent().floating_window_action.setText(self.parent().tr("Show floating window"))
            except Exception as e:
                print(f"关闭浮窗失败: {e}")

    def _switch_to_settings(self):
        """切换到设置界面"""
        try:
            if self.parent() and hasattr(self.parent(), "settingInterface"):
                parent = self.parent()
                if hasattr(parent, "stackedWidget"):
                    parent.stackedWidget.setCurrentWidget(parent.settingInterface, False)
        except Exception as e:
            print(f"切换到设置界面失败: {e}")

    # ==================== 扩展闪抽面板 ====================

    def _create_extended_quick_draw_widget(self) -> QWidget:
        """创建扩展闪抽组件"""
        qd_btn = self._create_button("quick_draw")
        arrow_btn = self._create_qd_arrow_btn()
        wrapper = QWidget()
        wrapper.setAttribute(Qt.WA_TranslucentBackground)
        lay = QHBoxLayout(wrapper)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(max(2, self.DEFAULT_SPACING // 2))
        lay.setAlignment(Qt.AlignCenter)
        lay.addWidget(qd_btn)
        lay.addWidget(arrow_btn)
        return wrapper

    def _create_qd_arrow_btn(self) -> QPushButton:
        """创建闪抽下拉箭头按钮"""
        from ...common.icon import UIcon

        btn = QPushButton()
        btn.setAttribute(Qt.WA_TranslucentBackground)
        btn.setFocusPolicy(Qt.NoFocus)
        btn.setStyleSheet("background: transparent; border: none;")
        w = max(20, int(self._btn_size.width() * 0.45))
        h = int(self._btn_size.height())
        btn.setFixedSize(QSize(w, h))
        icon_sz = QSize(
            max(14, int(self._icon_size.width() * 0.75)),
            max(14, int(self._icon_size.height() * 0.75)),
        )
        btn.setIcon(UIcon.get("ic_fluent_chevron_down_20_filled"))
        btn.setIconSize(icon_sz)
        btn.clicked.connect(lambda: self._toggle_qd_panel(btn))
        return btn

    def _toggle_qd_panel(self, anchor: QWidget):
        """切换闪抽扩展面板"""
        panel = self._quick_draw_extend_panel
        if panel and panel.isVisible():
            self._close_quick_draw_extend_panel()
            return
        panel = self._ensure_qd_panel()
        self._quick_draw_extend_anchor = anchor
        self._position_qd_panel(anchor)
        panel.show()
        panel.raise_()
        delay_ms = int(self.custom_retract_time * 1000)
        if delay_ms > 0:
            self._quick_draw_extend_close_timer.start(delay_ms)

    def _close_quick_draw_extend_panel(self):
        """关闭闪抽扩展面板"""
        if self._quick_draw_extend_close_timer.isActive():
            self._quick_draw_extend_close_timer.stop()
        panel = self._quick_draw_extend_panel
        if panel:
            try:
                if panel.isVisible():
                    panel.close()
            except Exception:
                pass
        self._quick_draw_extend_anchor = None

    def _ensure_qd_panel(self) -> QFrame:
        """确保闪抽扩展面板存在"""
        panel = self._quick_draw_extend_panel
        if panel:
            try:
                panel.setParent(None)
                panel.close()
            except Exception:
                pass

        panel = QFrame(None)
        panel.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        panel.setAttribute(Qt.WA_TranslucentBackground)
        try:
            panel.setAttribute(Qt.WA_ShowWithoutActivating, bool(self._do_not_steal_focus))
        except Exception:
            pass
        panel.installEventFilter(self)

        outer = QVBoxLayout(panel)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        card = QWidget(panel)
        card.setObjectName("qd_extend_card")
        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(12, 12, 12, 12)
        card_lay.setSpacing(8)

        lbl_font = self._font(max(8, self._font_size))

        class_combo = ComboBox()
        class_combo.setFont(lbl_font)
        class_combo.setFixedHeight(34)
        class_combo.setMinimumWidth(220)
        class_combo.setPlaceholderText("请选择班级")

        range_combo = ComboBox()
        range_combo.setFont(lbl_font)
        range_combo.setFixedHeight(34)
        range_combo.setMinimumWidth(220)

        gender_combo = ComboBox()
        gender_combo.setFont(lbl_font)
        gender_combo.setFixedHeight(34)
        gender_combo.setMinimumWidth(220)

        card_lay.addWidget(class_combo)
        card_lay.addWidget(range_combo)
        card_lay.addWidget(gender_combo)
        outer.addWidget(card)

        self._qd_card = card
        self._qd_class_combo = class_combo
        self._qd_range_combo = range_combo
        self._qd_gender_combo = gender_combo
        self._quick_draw_extend_panel = panel

        dark = self._is_dark()
        if dark:
            card.setStyleSheet(
                "background-color: rgba(32,32,32,220); border-radius: 12px; border: 1px solid rgba(255,255,255,24);"
            )
        else:
            card.setStyleSheet(
                "background-color: rgba(255,255,255,245); border-radius: 12px; border: 1px solid rgba(0,0,0,16);"
            )
        return panel

    def _position_qd_panel(self, anchor: QWidget):
        """定位闪抽扩展面板"""
        panel = self._quick_draw_extend_panel
        if panel is None:
            return
        try:
            anchor_tl = anchor.mapToGlobal(QPoint(0, 0))
            anchor_rect = QRect(anchor_tl, anchor.size())
        except Exception:
            p = QCursor.pos()
            anchor_rect = QRect(p, QSize(1, 1))

        scr = QGuiApplication.screenAt(anchor_rect.center()) or QApplication.primaryScreen()
        geo = scr.availableGeometry()
        panel.adjustSize()
        main_geo = self.frameGeometry()
        w, h = panel.width(), panel.height()

        candidates = []
        x, y = main_geo.right() + 6, anchor_rect.center().y() - h // 2
        if x + w <= geo.right() + 1:
            candidates.append((x, y))
        x, y = anchor_rect.center().x() - w // 2, main_geo.bottom() + 6
        if y + h <= geo.bottom() + 1:
            candidates.append((x, y))
        x, y = main_geo.left() - w - 6, anchor_rect.center().y() - h // 2
        if x >= geo.left():
            candidates.append((x, y))
        if not candidates:
            candidates.append((main_geo.right() + 6, anchor_rect.center().y() - h // 2))

        x, y = candidates[0]
        x = max(geo.left(), min(x, geo.right() - w + 1))
        y = max(geo.top(), min(y, geo.bottom() - h + 1))
        panel.move(x, y)

    # ==================== 鼠标事件处理 ====================

    def mousePressEvent(self, e):
        """鼠标按下事件"""
        if e.button() == Qt.LeftButton and self._draggable:
            self._close_quick_draw_extend_panel()
            self._press_pos = e.globalPosition().toPoint()
            self._press_time = int(time.monotonic() * 1000)
            self._dragging = False
            self._drag_timer.stop()
            self._drag_timer.start(self._long_press_ms)

    def mouseMoveEvent(self, e):
        """鼠标移动事件"""
        if not self._draggable:
            if self._dragging:
                self._dragging = False
                self.setCursor(Qt.ArrowCursor)
            return
        if e.buttons() & Qt.LeftButton:
            cur = e.globalPosition().toPoint()
            if not self._dragging:
                delta = cur - self._press_pos
                dur = int(time.monotonic() * 1000) - self._press_time if self._press_time else 0
                if self._should_start_drag(delta, dur):
                    self._begin_drag()
            if self._dragging:
                delta = cur - self._press_pos
                self.move(self.x() + delta.x(), self.y() + delta.y())
                self._press_pos = cur
                self._cancel_retract()

    def mouseReleaseEvent(self, e):
        """鼠标释放事件"""
        if e.button() == Qt.LeftButton:
            self._drag_timer.stop()
            self.setCursor(Qt.ArrowCursor)
            if self._dragging and self._draggable:
                self._end_drag()
            self._dragging = False

    def _should_start_drag(self, delta: QPoint, duration: int) -> bool:
        """判断是否应该开始拖拽"""
        if duration < self.MIN_DRAG_TIME:
            return False
        threshold = self.DRAG_THRESHOLD * 2 if duration < 150 else self.DRAG_THRESHOLD
        return abs(delta.x()) >= threshold or abs(delta.y()) >= threshold

    def _begin_drag(self):
        """开始拖拽"""
        if not self._draggable:
            return
        self._close_quick_draw_extend_panel()
        self._dragging = True
        self.setCursor(Qt.ClosedHandCursor)

    def _end_drag(self):
        """结束拖拽"""
        self._dragging = False
        self.setCursor(Qt.ArrowCursor)
        self._stick_to_nearest_edge()
        self._save_position()
        if self.floating_window_stick_to_edge:
            QTimer.singleShot(100, self._check_edge_proximity)

    def _install_drag_filters(self):
        """安装拖拽事件过滤器"""
        self._container.installEventFilter(self)
        for w in self._container.findChildren(QWidget):
            w.installEventFilter(self)

    def eventFilter(self, obj, event):
        """事件过滤器"""
        panel = self._quick_draw_extend_panel
        if panel and obj is panel:
            if event.type() in (QEvent.WindowDeactivate, QEvent.Hide, QEvent.Close):
                QTimer.singleShot(0, self._close_quick_draw_extend_panel)
            return False

        if not self._draggable:
            return False

        if event.type() == QEvent.MouseButtonPress:
            if event.button() == Qt.LeftButton:
                self._close_quick_draw_extend_panel()
                self._press_pos = event.globalPosition().toPoint()
                self._press_time = int(time.monotonic() * 1000)
                self._dragging = False
                self._drag_timer.stop()
                self._drag_timer.start(self._long_press_ms)
            return False

        if event.type() == QEvent.MouseMove:
            if event.buttons() & Qt.LeftButton:
                cur = event.globalPosition().toPoint()
                if not self._dragging:
                    delta = cur - self._press_pos
                    dur = int(time.monotonic() * 1000) - self._press_time if self._press_time else 0
                    if self._should_start_drag(delta, dur):
                        self._begin_drag()
                if self._dragging:
                    delta = cur - self._press_pos
                    self.move(self.x() + delta.x(), self.y() + delta.y())
                    self._press_pos = cur
                    return True
            return False

        if event.type() == QEvent.MouseButtonRelease:
            if event.button() == Qt.LeftButton:
                self._drag_timer.stop()
                if self._draggable and self._dragging:
                    self._end_drag()
                    return True
                self._dragging = False
            return False

        return False

    # ==================== 贴边隐藏 ====================

    def _stick_to_nearest_edge(self):
        """吸附到最近的边缘"""
        if not self._stick_to_edge:
            return
        fg = self.frameGeometry()
        scr = QGuiApplication.screenAt(fg.center()) or QApplication.primaryScreen()
        geo = scr.availableGeometry()
        left = fg.left() - geo.left()
        right = geo.right() - fg.right()
        self._last_stuck = False
        if left <= self._edge_threshold:
            self.move(geo.left(), self.y())
            self._last_stuck = True
        elif right <= self._edge_threshold:
            self.move(geo.right() - self.width() + 1, self.y())
            self._last_stuck = True

    def _cancel_retract(self):
        """取消回收"""
        if self._retract_timer.isActive():
            self._retract_timer.stop()

    def _check_edge_proximity(self, immediate: bool = False):
        """检测窗口是否靠近屏幕边缘，并实现贴边隐藏功能"""
        if not self.floating_window_stick_to_edge:
            return

        if hasattr(self, "animation") and self.animation.state() == QPropertyAnimation.Running:
            self.animation.stop()

        screen = QApplication.primaryScreen().availableGeometry()
        window_pos = self.pos()
        window_width = self.width()
        window_height = self.height()
        edge_threshold = 5

        # 检测左边缘
        if window_pos.x() <= edge_threshold:
            if not hasattr(self, "_original_position"):
                self._original_position = window_pos

            self.animation = QPropertyAnimation(self, b"geometry")
            self.animation.setDuration(400)
            self.animation.setEasingCurve(QEasingCurve.OutCubic)
            self.animation.setStartValue(self.geometry())
            end_rect = QRect(
                screen.left() - window_width + 1,
                window_pos.y(),
                window_width,
                window_height,
            )
            self.animation.setEndValue(end_rect)

            def on_animation_finished():
                self._retracted = True
                self._create_arrow_button("right", 0, window_pos.y() + window_height // 2 - self._storage_btn_size.height() // 2)

            self.animation.finished.connect(on_animation_finished)
            self.animation.start()
            return

        # 检测右边缘
        elif window_pos.x() + window_width >= screen.width() - edge_threshold:
            if not hasattr(self, "_original_position"):
                self._original_position = window_pos

            self.animation = QPropertyAnimation(self, b"geometry")
            self.animation.setDuration(400)
            self.animation.setEasingCurve(QEasingCurve.OutCubic)
            self.animation.setStartValue(self.geometry())
            end_rect = QRect(
                screen.right() - 1,
                window_pos.y(),
                window_width,
                window_height,
            )
            self.animation.setEndValue(end_rect)

            def on_animation_finished():
                self._retracted = True
                self._create_arrow_button("left", screen.width() - self._storage_btn_size.width(), window_pos.y() + window_height // 2 - self._storage_btn_size.height() // 2)

            self.animation.finished.connect(on_animation_finished)
            self.animation.start()
            return

        # 保存新位置
        if window_pos.x() > edge_threshold and window_pos.x() + window_width < screen.width() - edge_threshold:
            if not self._retracted:
                self._save_position()
            if hasattr(self, "_original_position"):
                delattr(self, "_original_position")

        self._retracted = False

    def _expand_from_edge(self):
        """从边缘展开"""
        scr = QApplication.primaryScreen().availableGeometry()
        if self.x() < scr.left():
            self.move(scr.left(), self.y())
        elif self.x() + self.width() > scr.right():
            self.move(scr.right() - self.width() + 1, self.y())
        self._retracted = False

    def _auto_hide_window(self):
        """自动隐藏窗口"""
        if self.floating_window_stick_to_edge and not self._retracted:
            self._check_edge_proximity()

    def _save_position(self):
        """保存窗口位置到配置文件"""
        try:
            pos = self.pos()
            if hasattr(cfg, "floatingWindowPosX"):
                cfg.set(cfg.floatingWindowPosX, pos.x())
            if hasattr(cfg, "floatingWindowPosY"):
                cfg.set(cfg.floatingWindowPosY, pos.y())
            self.positionChanged.emit(pos.x(), pos.y())
        except Exception:
            pass

    def _detect_mouse_near_edge(self):
        """检测鼠标是否靠近已收纳的浮窗边缘"""
        if not self._retracted or not self.floating_window_stick_to_edge:
            return

        try:
            mouse_pos = QCursor.pos()
            screen = QApplication.primaryScreen().availableGeometry()
            sense_distance = 20
            window_geometry = self.geometry()
            window_y_center = window_geometry.center().y()
            window_height = window_geometry.height()

            mouse_in_window_height = (
                window_y_center - window_height // 2 - sense_distance
                <= mouse_pos.y()
                <= window_y_center + window_height // 2 + sense_distance
            )

            if not mouse_in_window_height:
                return

            if window_geometry.x() < screen.left() and mouse_pos.x() <= screen.left() + sense_distance:
                self._show_hidden_window("right")
            elif window_geometry.x() + window_geometry.width() > screen.right() and mouse_pos.x() >= screen.right() - sense_distance:
                self._show_hidden_window("left")
        except Exception:
            pass

    # ==================== 箭头按钮（收纳指示器）====================

    def _create_arrow_button(self, direction: str, x: int, y: int):
        """创建箭头按钮"""
        self._delete_arrow_button()

        widget = DraggableIndicatorWidget()
        widget.setFixedSize(self._storage_btn_size)
        widget.move(x, y)
        widget.setFixedX(x)
        flags = Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.NoDropShadowWindowHint
        if self._do_not_steal_focus:
            flags |= Qt.WindowDoesNotAcceptFocus
        widget.setWindowFlags(flags)
        try:
            widget.setAttribute(Qt.WA_ShowWithoutActivating, self._do_not_steal_focus)
        except Exception:
            pass
        widget.setAttribute(Qt.WA_TranslucentBackground)

        lay = QVBoxLayout()
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        btn = QPushButton()
        btn.setFixedSize(self._storage_btn_size)
        btn.setAttribute(Qt.WA_TranslucentBackground)
        btn.setFocusPolicy(Qt.NoFocus)
        self.arrow_button = btn
        
        # 先应用样式再显示
        self._update_arrow_button_style(direction)

        btn.clicked.connect(lambda: self._show_hidden_window(direction))

        orig_release = widget.mouseReleaseEvent

        def new_release(ev):
            orig_release(ev)
            if ev.button() == Qt.LeftButton and not getattr(widget, "_was_dragging", False):
                self._show_hidden_window(direction)

        widget.mouseReleaseEvent = new_release

        lay.addWidget(btn, alignment=Qt.AlignCenter)
        widget.setLayout(lay)
        widget.raise_()
        widget.show()
        
        # 强制刷新确保显示
        widget.update()
        btn.update()

        self.arrow_widget = widget
        self.storage_window = widget

    def _delete_arrow_button(self):
        """删除箭头按钮"""
        for attr in ("arrow_widget", "storage_window"):
            w = getattr(self, attr, None)
            if w:
                try:
                    w.deleteLater()
                except Exception:
                    pass
                setattr(self, attr, None)
        btn = getattr(self, "arrow_button", None)
        if btn:
            try:
                btn.deleteLater()
            except Exception:
                pass
            self.arrow_button = None

    def _update_arrow_button_style(self, direction: str = "right"):
        """更新箭头按钮样式"""
        btn = getattr(self, "arrow_button", None)
        if btn is None:
            return
        dark = self._is_dark()
        opacity = int(self._opacity * 255)
        if dark:
            btn.setStyleSheet(
                f"background-color: rgba(32,32,32,{opacity}); color: rgba(255,255,255,200);"
                " border-radius: 6px; border: 1px solid rgba(255,255,255,20);"
            )
        else:
            btn.setStyleSheet(
                f"background-color: rgba(255,255,255,{opacity}); color: rgba(0,0,0,180);"
                " border-radius: 6px; border: 1px solid rgba(0,0,0,12);"
            )
        # 同步指示器样式（图标/文字）
        style = int(getattr(self, "_stick_indicator_style", 0) or 0)
        if style == 0:
            btn.setText("")
            btn.setIcon(FIF.PEOPLE.icon())
            btn.setIconSize(self._storage_icon_size)
        elif style == 1:
            btn.setIcon(QIcon())
            btn.setText("抽")
            btn.setFont(self._font(self._storage_font_size))
        else:
            btn.setIcon(QIcon())
            btn.setText(">" if direction == "right" else "<")
            btn.setFont(self._font(self._storage_font_size))

    def _show_hidden_window(self, direction: str):
        """显示隐藏的窗口"""
        if hasattr(self, "animation") and self.animation.state() == QPropertyAnimation.Running:
            self.animation.stop()

        scr = QApplication.primaryScreen().availableGeometry()
        w = self.width()
        h = self.height()

        arrow = getattr(self, "arrow_widget", None)
        arrow_pos = arrow.pos() if arrow else self.pos()
        arrow_h = arrow.height() if arrow else 30
        window_y = arrow_pos.y() + arrow_h // 2 - h // 2
        window_y = max(scr.top(), min(window_y, scr.bottom() - h))

        if direction == "right":
            end_rect = QRect(scr.left(), window_y, w, h)
        else:
            end_rect = QRect(scr.right() - w + 1, window_y, w, h)

        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.OutQuad)
        self.animation.setStartValue(self.geometry())
        self.animation.setEndValue(end_rect)

        def on_done():
            self._retracted = False
            self.raise_()
            delay_ms = int(self.custom_retract_time * 1000)
            if delay_ms > 0:
                if hasattr(self, "_auto_hide_timer") and self._auto_hide_timer.isActive():
                    self._auto_hide_timer.stop()
                self._auto_hide_timer = QTimer(self)
                self._auto_hide_timer.setSingleShot(True)
                self._auto_hide_timer.timeout.connect(self._auto_hide_window)
                self._auto_hide_timer.start(delay_ms)

        self.animation.finished.connect(on_done)
        self.animation.start()
        self._delete_arrow_button()
        self.raise_()

    # ==================== Qt 事件重写 ====================

    def enterEvent(self, e):
        """鼠标进入事件"""
        if hasattr(self, "_auto_hide_timer") and self._auto_hide_timer.isActive():
            self._auto_hide_timer.stop()

    def leaveEvent(self, e):
        """鼠标离开事件"""
        self._schedule_auto_hide(force=True)

    def _schedule_auto_hide(self, force: bool = False):
        """计划自动隐藏"""
        if not self.floating_window_stick_to_edge or self._retracted or not self.isVisible():
            return
        if not force:
            try:
                if self.frameGeometry().contains(QCursor.pos()):
                    return
            except Exception:
                pass
        delay_ms = int(self.custom_retract_time * 1000)
        if delay_ms <= 0:
            return
        if hasattr(self, "_auto_hide_timer") and self._auto_hide_timer.isActive():
            self._auto_hide_timer.stop()
        self._auto_hide_timer = QTimer(self)
        self._auto_hide_timer.setSingleShot(True)
        self._auto_hide_timer.timeout.connect(self._auto_hide_window)
        self._auto_hide_timer.start(delay_ms)

    def showEvent(self, event):
        """显示事件"""
        super().showEvent(event)
        if not self._suppress_visibility_tracking:
            self._user_requested_visible = True
            if self._retracted and self.storage_window and not self.storage_window.isVisible():
                try:
                    self.storage_window.show()
                except Exception:
                    pass
            if self._startup_initial_show:
                self._check_edge_proximity(immediate=True)
                self._startup_initial_show = False
                self._schedule_auto_hide(force=False)
            else:
                QTimer.singleShot(100, self._check_edge_proximity)

    def hideEvent(self, event):
        """隐藏事件"""
        super().hideEvent(event)
        if not self._suppress_visibility_tracking:
            self._user_requested_visible = False
            if self.storage_window and self.storage_window.isVisible():
                try:
                    self.storage_window.hide()
                except Exception:
                    pass

    def closeEvent(self, event):
        """关闭事件"""
        # 如果应用程序正在关闭，允许关闭
        if QApplication.instance().closingDown():
            self._close_guard_enabled = False
            event.accept()
            return
        
        # 如果父窗口已经关闭或不可见，允许关闭
        parent = self.parent()
        if parent is None or not parent.isVisible():
            self._close_guard_enabled = False
            event.accept()
            return
            
        # 关闭保护：防止误关闭，只隐藏不关闭
        if self._close_guard_enabled:
            event.ignore()
            now = int(QDateTime.currentMSecsSinceEpoch())
            if now - self._close_guard_last_log_ms >= 5000:
                self._close_guard_last_log_ms = now
            try:
                self.hide()
                # 同步更新配置和托盘菜单
                cfg.set(cfg.startupDisplayFloatingWindow, False)
                if parent and hasattr(parent, "floating_window_action"):
                    parent.floating_window_action.setChecked(False)
                    parent.floating_window_action.setText(parent.tr("Show floating window"))
            except Exception:
                pass
            return
        super().closeEvent(event)

    def show(self):
        """显示窗口"""
        super().show()
        QTimer.singleShot(100, self._check_edge_proximity)
        self.visibilityChanged.emit(True)

    def hide(self):
        """隐藏窗口"""
        super().hide()
        self.visibilityChanged.emit(False)

    # ==================== 前台窗口隐藏 ====================

    def _get_foreground_info(self) -> tuple[str, str, int]:
        """获取前台窗口信息"""
        try:
            user32 = ctypes.WinDLL("user32", use_last_error=True)
            hwnd = user32.GetForegroundWindow()
            if not hwnd:
                return "", "", 0
            length = int(user32.GetWindowTextLengthW(hwnd) or 0)
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            title = str(buf.value or "")
            pid = ctypes.c_ulong(0)
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            pid_int = int(pid.value or 0)
            process_name = ""
            try:
                if pid_int and pid_int != os.getpid():
                    import psutil
                    process_name = str(psutil.Process(pid_int).name() or "")
            except Exception:
                pass
            return title, process_name, pid_int
        except Exception:
            return "", "", 0

    def _check_foreground_hide(self):
        """检查前台窗口隐藏"""
        if not self._hide_on_foreground_enabled:
            return
        title, proc, pid = self._get_foreground_info()
        if pid == os.getpid():
            self._apply_foreground_hidden(False)
            return
        title_l = title.lower()
        proc_l = proc.lower()
        matched = any(t and t in title_l for t in self._hide_on_foreground_titles) or \
                  any(p and p in proc_l for p in self._hide_on_foreground_processes)
        self._apply_foreground_hidden(matched)

    def _apply_foreground_hidden(self, hidden: bool):
        """应用前台隐藏状态"""
        if hidden == self._hidden_by_foreground:
            return
        self._hidden_by_foreground = hidden
        self._suppress_visibility_tracking = True
        try:
            if hidden:
                self._pre_fg_main_visible = self.isVisible()
                self._pre_fg_arrow_visible = bool(self.arrow_widget and self.arrow_widget.isVisible())
                if self.isVisible():
                    self.hide()
                if self.arrow_widget and self.arrow_widget.isVisible():
                    self.arrow_widget.hide()
            else:
                if self._user_requested_visible and self._pre_fg_main_visible and not self.isVisible():
                    self.show()
                if (self._user_requested_visible and self._pre_fg_arrow_visible
                        and self.arrow_widget and not self.arrow_widget.isVisible()):
                    self.arrow_widget.show()
        finally:
            self._suppress_visibility_tracking = False

    # ==================== 可见性控制 ====================

    def set_user_requested_visible(self, visible: bool):
        """设置用户请求的可见性"""
        self._user_requested_visible = bool(visible)
        if visible:
            super().show()
            if self._retracted and self.storage_window:
                try:
                    self.storage_window.show()
                except Exception:
                    pass
        else:
            if self.storage_window and self.storage_window.isVisible():
                try:
                    self.storage_window.hide()
                except Exception:
                    pass
            super().hide()

    def toggle_visible(self):
        """切换可见性"""
        self.set_user_requested_visible(not self._user_requested_visible)


class DraggableIndicatorWidget(QWidget):
    """可垂直拖动的收纳指示器窗口"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self._dragging = False
        self._drag_start_y = 0
        self._original_y = 0
        self._fixed_x = 0
        self._press_start_time = 0
        self._long_press_duration = 100
        self._long_press_timer = QTimer(self)
        self._long_press_timer.setSingleShot(True)
        self._long_press_timer.timeout.connect(self._on_long_press)
        self._long_press_triggered = False
        self._keep_on_top_enabled = True
        self._was_dragging = False

        self._keep_top_timer = QTimer(self)
        self._keep_top_timer.timeout.connect(self._keep_window_on_top)
        self._keep_top_timer.start(100)

    def set_keep_on_top_enabled(self, enabled: bool) -> None:
        self._keep_on_top_enabled = bool(enabled)
        if self._keep_on_top_enabled:
            if not self._keep_top_timer.isActive():
                self._keep_top_timer.start(100)
        else:
            if self._keep_top_timer.isActive():
                self._keep_top_timer.stop()

    def setFixedX(self, x: int) -> None:
        self._fixed_x = x

    def _keep_window_on_top(self) -> None:
        if self._keep_on_top_enabled:
            try:
                self.raise_()
            except Exception:
                pass

    def _on_long_press(self) -> None:
        self._long_press_triggered = True
        self.setCursor(Qt.ClosedHandCursor)

    def closeEvent(self, event):
        for timer in (self._keep_top_timer, self._long_press_timer):
            try:
                if timer and timer.isActive():
                    timer.stop()
            except Exception:
                pass
        super().closeEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._press_start_time = QDateTime.currentMSecsSinceEpoch()
            self._drag_start_y = event.globalY()
            self._original_y = self.y()
            self._long_press_triggered = False
            self._was_dragging = False
            self._long_press_timer.start(self._long_press_duration)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            now = QDateTime.currentMSecsSinceEpoch()
            if self._long_press_triggered or (
                now - self._press_start_time > 100
                and abs(event.globalY() - self._drag_start_y) > 5
            ):
                if not self._dragging:
                    self._dragging = True
                    self._was_dragging = True
                    self.setCursor(Qt.ClosedHandCursor)
                    if not self._long_press_triggered:
                        self._long_press_timer.stop()

                new_y = self._original_y + (event.globalY() - self._drag_start_y)
                scr = QApplication.primaryScreen().availableGeometry()
                new_y = max(scr.top(), min(new_y, scr.bottom() - self.height()))
                self.move(self._fixed_x, new_y)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging = False
            self._long_press_timer.stop()
            self.setCursor(Qt.ArrowCursor)
