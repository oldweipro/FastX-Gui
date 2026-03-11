# ==================================================
# 悬浮窗窗口 - 独立 Demo 版本
# 从 SecRandom 项目完整剥离，无外部项目依赖
# 依赖：PySide6、qfluentwidgets
# ==================================================

import ctypes
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

from PySide6.QtCore import (
    QDateTime, QEasingCurve, QEvent, QObject, QPoint, QRect, QSize, Qt, QTimer,
    Signal,
)
from PySide6.QtGui import (
    QColor, QCursor, QFont, QFontDatabase, QGuiApplication, QIcon, QPainter,
    QPen, QPalette, QPixmap,
)
from PySide6.QtWidgets import (
    QApplication, QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy,
    QVBoxLayout, QWidget,
)
from qfluentwidgets import BodyLabel, PushButton as FluentPushButton, qconfig, Theme

from config import (
    get_assets_dir,
    get_fonts_dir,
    get_settings_signals,
    readme_settings_async,
    update_settings,
)

# --------------------------------------------------
# 常量
# --------------------------------------------------
DEFAULT_ICON_CODEPOINT = 62634  # fallback 图标码点
EXIT_CODE_RESTART = 1000


# --------------------------------------------------
# 主题工具
# --------------------------------------------------

def is_dark_theme() -> bool:
    if qconfig.theme == Theme.AUTO:
        return QApplication.palette().color(QPalette.Window).lightness() <= 127
    return qconfig.theme == Theme.DARK


# --------------------------------------------------
# 图标工具（内联，不依赖外部 personalised 模块）
# --------------------------------------------------

_fluent_icon_map: Optional[Dict[str, int]] = None
_fluent_font_family: Optional[str] = None


def _ensure_fluent_resources() -> None:
    global _fluent_icon_map, _fluent_font_family
    if _fluent_icon_map is None:
        try:
            p = get_assets_dir() / "FluentSystemIcons-Filled.json"
            with open(str(p), "r", encoding="utf-8") as f:
                _fluent_icon_map = json.loads(f.read()) or {}
        except Exception:
            _fluent_icon_map = {}

    if _fluent_font_family is None:
        try:
            p = get_assets_dir() / "FluentSystemIcons-Filled.ttf"
            fid = QFontDatabase.addApplicationFont(str(p))
            if fid >= 0:
                families = QFontDatabase.applicationFontFamilies(fid)
                _fluent_font_family = families[0] if families else ""
            else:
                _fluent_font_family = ""
        except Exception:
            _fluent_font_family = ""


def _resolve_fluent_char(icon_name) -> str:
    _ensure_fluent_resources()
    if isinstance(icon_name, str) and icon_name.startswith("\\u"):
        try:
            return chr(int(icon_name[2:], 16))
        except Exception:
            return chr(DEFAULT_ICON_CODEPOINT)
    if isinstance(icon_name, int):
        try:
            return chr(icon_name)
        except Exception:
            return chr(DEFAULT_ICON_CODEPOINT)
    if isinstance(icon_name, str):
        icon_map = _fluent_icon_map or {}
        try:
            return chr(int(icon_map.get(icon_name, DEFAULT_ICON_CODEPOINT)))
        except Exception:
            return chr(DEFAULT_ICON_CODEPOINT)
    return chr(DEFAULT_ICON_CODEPOINT)


def render_fluent_icon(icon_name, size: QSize, color: QColor) -> QIcon:
    _ensure_fluent_resources()
    font_family = _fluent_font_family or ""
    w = max(size.width(), 1)
    h = max(size.height(), 1)
    px = min(w, h)
    char = _resolve_fluent_char(icon_name)

    pixmap = QPixmap(w, h)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.TextAntialiasing)
    painter.setPen(QPen(color))
    font = QFont(font_family) if font_family else QFont()
    font.setPixelSize(px)
    painter.setFont(font)
    painter.drawText(QRect(0, 0, w, h), Qt.AlignCenter, char)
    painter.end()
    return QIcon(pixmap)


def freeze_icon(icon: QIcon, size: QSize) -> QIcon:
    try:
        qicon = icon.icon() if hasattr(icon, "icon") else icon
    except Exception:
        qicon = icon
    try:
        pixmap = qicon.pixmap(size)
    except Exception:
        pixmap = QIcon().pixmap(size)
    return QIcon(pixmap)


# --------------------------------------------------
# 可垂直拖动的窗口部件（贴边收纳指示器）
# --------------------------------------------------

class DraggableWidget(QWidget):
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


# --------------------------------------------------
# 悬浮窗主类
# --------------------------------------------------

class LevitationWindow(QWidget):
    """
    悬浮窗口
    功能：可拖拽、贴边自动隐藏/展开（动画）、主题跟随、多按钮布局、
          按钮控制、外观样式、前台应用隐藏、置顶模式
    """

    # 信号
    rollCallRequested  = Signal()
    quickDrawRequested = Signal()
    lotteryRequested   = Signal()
    faceDrawRequested  = Signal()
    timerRequested     = Signal()
    visibilityChanged  = Signal(bool)
    positionChanged    = Signal(int, int)

    # 默认常量
    DEFAULT_OPACITY       = 0.8
    DEFAULT_PLACEMENT     = 0
    DEFAULT_DISPLAY_STYLE = 0
    DEFAULT_EDGE_THRESHOLD = 5
    DEFAULT_RETRACT_SECONDS = 5
    DEFAULT_LONG_PRESS_MS   = 150
    DEFAULT_BUTTON_SIZE   = QSize(50, 50)
    DEFAULT_ICON_SIZE     = QSize(24, 24)
    DEFAULT_SPACING       = 6
    DEFAULT_MARGINS       = 6
    DRAG_THRESHOLD        = 12
    MIN_DRAG_TIME         = 100

    # 按钮标签文本（硬编码中文，可按需替换为多语言）
    BUTTON_LABELS = {
        "roll_call":  "点名",
        "quick_draw": "闪抽",
        "lottery":    "抽奖",
        "face_draw":  "人脸",
        "timer":      "计时",
    }
    BUTTON_ICONS = {
        "roll_call":  "ic_fluent_people_20_filled",
        "quick_draw": "ic_fluent_flash_20_filled",
        "lottery":    "ic_fluent_gift_20_filled",
        "face_draw":  "ic_fluent_video_person_sparkle_20_filled",
        "timer":      "ic_fluent_timer_20_filled",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._startup_initial_show = True
        self._close_guard_enabled = True
        self._close_guard_last_log_ms = 0

        self._setup_window_flags()
        self._init_drag_state()
        self._init_edge_state()
        self._init_ui_state()
        self._init_topmost_state()
        self._load_settings()
        self._build_ui()
        self._apply_position()
        self._connect_signals()
        self._apply_theme_style()
        self._apply_window_opacity()
        self._install_drag_filters()
        self._start_topmost()

        if not self._visible_on_start:
            QTimer.singleShot(0, lambda: self._check_edge_proximity(immediate=True))

    # ==================== 初始化 ====================

    def _setup_window_flags(self):
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._base_flags = Qt.FramelessWindowHint | Qt.Tool | Qt.NoDropShadowWindowHint
        self.setWindowFlags(self._base_flags | Qt.WindowStaysOnTopHint)

    def _init_drag_state(self):
        self._dragging = False
        self._press_pos = QPoint()
        self._press_time = 0
        self._drag_timer = QTimer(self)
        self._drag_timer.setSingleShot(True)
        self._drag_timer.timeout.connect(self._begin_drag)

    def _init_edge_state(self):
        self._retracted = False
        self._last_stuck = False
        self._retract_timer = QTimer(self)
        self._retract_timer.setSingleShot(True)
        self._indicator = None
        self.storage_window = None
        self.arrow_widget = None
        self.arrow_button = None

    def _init_ui_state(self):
        self._container = QWidget(self)
        self._layout = None
        self._top = None
        self._bottom = None
        self._buttons_spec: list[str] = []
        self._font_family = self._load_app_font()
        self._quick_draw_extend_panel = None
        self._quick_draw_extend_anchor = None
        self._quick_draw_extend_close_timer = QTimer(self)
        self._quick_draw_extend_close_timer.setSingleShot(True)
        self._quick_draw_extend_close_timer.timeout.connect(
            self._close_quick_draw_extend_panel
        )

    def _init_topmost_state(self):
        self._periodic_topmost_timer = QTimer(self)
        self._periodic_topmost_timer.timeout.connect(lambda: self.raise_() if self.isVisible() and self._topmost_mode != 0 else None)
        self._uiaccess_funcs = None

    def _load_app_font(self) -> str:
        """加载 HarmonyOS Sans SC 字体，回退到系统默认字体"""
        try:
            fonts_dir = get_fonts_dir()
            # 优先 Medium，其次 Regular，最后找任意 ttf
            candidates = ["HarmonyOS_Sans_SC_Medium.ttf", "HarmonyOS_Sans_SC.ttf",
                          "HarmonyOS_Sans_SC_Regular.ttf"]
            ttf_path = None
            for name in candidates:
                p = fonts_dir / name
                if p.exists():
                    ttf_path = p
                    break
            if ttf_path is None:
                # 找 fonts 目录下第一个 .ttf
                ttfs = list(fonts_dir.glob("*.ttf"))
                if ttfs:
                    ttf_path = ttfs[0]
            if ttf_path:
                fid = QFontDatabase.addApplicationFont(str(ttf_path))
                if fid >= 0:
                    families = QFontDatabase.applicationFontFamilies(fid)
                    if families:
                        return families[0]
        except Exception:
            pass
        return QFont().family()

    # ==================== 设置加载 ====================

    def _read_bool(self, section: str, key: str, default: bool) -> bool:
        v = readme_settings_async(section, key)
        return bool(v) if v is not None else default

    def _read_int(self, section: str, key: str, default: int) -> int:
        v = readme_settings_async(section, key)
        return int(v) if v is not None else default

    def _read_float(self, section: str, key: str, default: float) -> float:
        v = readme_settings_async(section, key)
        return float(v) if v is not None else default

    def _load_settings(self):
        s = "floating_window_management"
        self._visible_on_start     = self._read_bool(s, "startup_display_floating_window", False)
        self._opacity              = self._read_float(s, "floating_window_opacity", self.DEFAULT_OPACITY)
        self._floating_window_theme = self._read_int(s, "floating_window_theme", 0)
        self._placement            = self._read_int(s, "floating_window_placement", 0)
        self._display_style        = self._read_int(s, "floating_window_display_style", 0)
        self._extend_quick_draw    = self._read_bool(s, "extend_quick_draw_component", False)
        self._draggable            = self._read_bool(s, "floating_window_draggable", True)
        self._long_press_ms        = self._read_int(s, "floating_window_long_press_duration", self.DEFAULT_LONG_PRESS_MS)
        self._stick_to_edge        = self._read_bool(s, "floating_window_stick_to_edge", True)
        self.floating_window_stick_to_edge = self._stick_to_edge
        self._retract_seconds      = self._read_int(s, "floating_window_stick_to_edge_recover_seconds", self.DEFAULT_RETRACT_SECONDS)
        self.custom_retract_time   = self._retract_seconds
        self._stick_indicator_style = self._read_int(s, "floating_window_stick_to_edge_display_style", 0)
        self.custom_display_mode   = self._stick_indicator_style
        self._do_not_steal_focus   = self._read_bool(s, "do_not_steal_focus", False)
        self._topmost_mode         = self._read_int(s, "floating_window_topmost_mode", 1)
        self._buttons_spec         = self._normalize_button_control(
            readme_settings_async(s, "floating_window_button_control")
        )
        size_idx = self._read_int(s, "floating_window_size", 3)
        self._apply_size_setting(size_idx)

        # 前台隐藏（先初始化，_refresh_window_flags 会用到 _suppress_visibility_tracking）
        self._hide_on_foreground_enabled = self._read_bool(s, "hide_floating_window_on_foreground", False)
        self._hide_on_foreground_titles  = self._split_match_list(
            str(readme_settings_async(s, "hide_floating_window_on_foreground_window_titles") or "")
        )
        self._hide_on_foreground_processes = self._split_match_list(
            str(readme_settings_async(s, "hide_floating_window_on_foreground_process_names") or "")
        )
        self._hidden_by_foreground = False
        self._pre_fg_main_visible  = False
        self._pre_fg_arrow_visible = False
        self._suppress_visibility_tracking = False

        # 现在 _suppress_visibility_tracking 已初始化，可安全调用
        self._refresh_window_flags()

        self._foreground_timer = QTimer(self)
        self._foreground_timer.setInterval(250)
        self._foreground_timer.timeout.connect(self._check_foreground_hide)
        if self._hide_on_foreground_enabled:
            self._foreground_timer.start()

        self._user_requested_visible = bool(self._visible_on_start)

    # ==================== 信号连接 ====================

    def _connect_signals(self):
        get_settings_signals().settingChanged.connect(self._on_setting_changed)
        try:
            qconfig.themeChanged.connect(self._on_theme_changed)
        except Exception:
            pass

    # ==================== 窗口标志管理 ====================

    def _refresh_window_flags(self):
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

    def _start_topmost(self):
        mode = int(getattr(self, "_topmost_mode", 1) or 0)
        if mode != 0 and not self._periodic_topmost_timer.isActive():
            self._periodic_topmost_timer.start(100)

    # ==================== UI 构建 ====================

    def _build_ui(self):
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

    def rebuild_ui(self):
        panel = getattr(self, "_quick_draw_extend_panel", None)
        if panel:
            try:
                panel.close()
            except Exception:
                pass
        self._quick_draw_extend_anchor = None
        self._clear_buttons()
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

    def _clear_buttons(self):
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

    def _create_container_layout(self):
        for attr in ("_top", "_bottom"):
            w = getattr(self, attr, None)
            if w:
                w.deleteLater()
                setattr(self, attr, None)

        if self._placement == 1:
            lay = QVBoxLayout()
            lay.setContentsMargins(self.DEFAULT_MARGINS, self.DEFAULT_MARGINS,
                                   self.DEFAULT_MARGINS, self.DEFAULT_MARGINS)
            lay.setSpacing(self.DEFAULT_SPACING)
            return lay
        if self._placement == 2:
            lay = QHBoxLayout()
            lay.setContentsMargins(self.DEFAULT_MARGINS, self.DEFAULT_MARGINS,
                                   self.DEFAULT_MARGINS, self.DEFAULT_MARGINS)
            lay.setSpacing(self.DEFAULT_SPACING)
            return lay

        # 默认双行网格布局
        lay = QVBoxLayout()
        lay.setContentsMargins(self.DEFAULT_MARGINS, self.DEFAULT_MARGINS,
                               self.DEFAULT_MARGINS, self.DEFAULT_MARGINS)
        lay.setSpacing(self.DEFAULT_SPACING)

        self._top = QWidget()
        self._top.setAttribute(Qt.WA_TranslucentBackground)
        self._bottom = QWidget()
        self._bottom.setAttribute(Qt.WA_TranslucentBackground)

        for sub, container in ((self._top, self._top), (self._bottom, self._bottom)):
            sub_lay = QHBoxLayout(container)
            sub_lay.setContentsMargins(0, 0, 0, 0)
            sub_lay.setSpacing(self.DEFAULT_SPACING)
            sub_lay.setAlignment(Qt.AlignCenter)

        lay.addWidget(self._top)
        lay.addWidget(self._bottom)
        return lay

    def _apply_window_opacity(self):
        self.setWindowOpacity(self._opacity)
        if self._visible_on_start:
            self.show()
        else:
            self.hide()

    # ==================== 按钮创建 ====================

    def _get_icon(self, icon_name: str) -> QIcon:
        dark = self._is_dark()
        color = QColor("#ffffff") if dark else QColor("#000000")
        return render_fluent_icon(icon_name, self._icon_size, color)

    def _is_dark(self) -> bool:
        idx = int(getattr(self, "_floating_window_theme", 0) or 0)
        if idx == 0:
            return is_dark_theme()
        return idx == 2

    def _text_color(self) -> str:
        return "rgba(255,255,255,230)" if self._is_dark() else "rgba(0,0,0,200)"

    def _font(self, size: int) -> QFont:
        s = max(int(size) if size else 8, 1)
        f = QFont(self._font_family) if self._font_family else QFont()
        f.setPointSize(s)
        return f

    def _create_button(self, spec: str) -> QPushButton:
        icon_name = self.BUTTON_ICONS.get(spec, "ic_fluent_people_20_filled")
        text = self.BUTTON_LABELS.get(spec, spec)
        signal_map = {
            "roll_call": self.rollCallRequested,
            "quick_draw": self.quickDrawRequested,
            "lottery": self.lotteryRequested,
            "face_draw": self.faceDrawRequested,
            "timer": self.timerRequested,
        }
        signal = signal_map.get(spec, self.rollCallRequested)
        icon = self._get_icon(icon_name)

        if self._display_style == 1:
            btn = self._make_icon_btn(icon)
        elif self._display_style == 2:
            btn = self._make_text_btn(text)
        else:
            btn = self._make_composite_btn(icon, text)

        btn.clicked.connect(lambda: signal.emit())
        btn.setAttribute(Qt.WA_TranslucentBackground)
        return btn

    def _make_icon_btn(self, icon: QIcon) -> QPushButton:
        btn = QPushButton()
        btn.setIcon(freeze_icon(icon, self._icon_size))
        btn.setIconSize(self._icon_size)
        btn.setFixedSize(self._btn_size)
        btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        btn.setFocusPolicy(Qt.NoFocus)
        btn.setAttribute(Qt.WA_TranslucentBackground)
        btn.setStyleSheet("background: transparent; border: none;")
        return btn

    def _make_text_btn(self, text: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setFixedSize(self._btn_size)
        btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        btn.setFont(self._font(self._font_size))
        btn.setAttribute(Qt.WA_TranslucentBackground)
        btn.setStyleSheet(
            f"background: transparent; border: none; color: {self._text_color()};"
        )
        return btn

    def _make_composite_btn(self, icon: QIcon, text: str) -> QPushButton:
        btn = QPushButton()
        lay = QVBoxLayout(btn)
        lay.setContentsMargins(0, 4, 0, 4)
        lay.setSpacing(2)
        lay.setAlignment(Qt.AlignCenter)
        btn.setStyleSheet("background: transparent; border: none;")

        icon_lbl = QLabel()
        icon_lbl.setPixmap(freeze_icon(icon, self._icon_size).pixmap(self._icon_size))
        icon_lbl.setFixedSize(self._icon_size)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        text_lbl = BodyLabel(text)
        text_lbl.setAlignment(Qt.AlignCenter)
        text_lbl.setFont(self._font(self._font_size))
        text_lbl.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        text_lbl.setFocusPolicy(Qt.NoFocus)
        text_lbl.setStyleSheet(
            f"background: transparent; border: none; color: {self._text_color()};"
        )

        lay.addWidget(icon_lbl)
        lay.addWidget(text_lbl)
        lay.setAlignment(icon_lbl, Qt.AlignCenter)
        lay.setAlignment(text_lbl, Qt.AlignCenter)

        btn.setFixedSize(self._btn_size)
        btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        btn.setAttribute(Qt.WA_TranslucentBackground)
        return btn

    def _add_button(self, btn, index: int, total: int):
        if self._placement in (1, 2):
            self._container.layout().addWidget(btn, 0, Qt.AlignCenter)
            return
        split = (total + 1) // 2
        target = self._top if index < split else self._bottom
        target.layout().addWidget(btn, 0, Qt.AlignCenter)

    # ==================== 扩展闪抽面板 ====================

    def _create_extended_quick_draw_widget(self) -> QWidget:
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
        btn.setIcon(
            freeze_icon(self._get_icon("ic_fluent_chevron_down_20_filled"), icon_sz)
        )
        btn.setIconSize(icon_sz)
        btn.clicked.connect(lambda: self._toggle_qd_panel(btn))
        return btn

    def _toggle_qd_panel(self, anchor: QWidget):
        panel = self._quick_draw_extend_panel
        if panel and panel.isVisible():
            self._close_quick_draw_extend_panel()
            return
        panel = self._ensure_qd_panel()
        self._quick_draw_extend_anchor = anchor
        self._populate_qd_panel()
        self._position_qd_panel(anchor)
        panel.show()
        panel.raise_()
        delay_ms = int(self.custom_retract_time * 1000)
        if delay_ms > 0:
            self._quick_draw_extend_close_timer.start(delay_ms)

    def _close_quick_draw_extend_panel(self):
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

        from qfluentwidgets import ComboBox
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

        class_combo.currentTextChanged.connect(
            lambda t: (
                update_settings("floating_window_management", "quick_draw_class_name", t),
                self._refresh_qd_filters(t, range_combo, gender_combo),
            )
        )
        range_combo.currentTextChanged.connect(
            lambda t: update_settings("floating_window_management", "quick_draw_group_filter", t)
        )
        gender_combo.currentTextChanged.connect(
            lambda t: update_settings("floating_window_management", "quick_draw_gender_filter", t)
        )

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
                "background-color: rgba(32,32,32,220); border-radius: 12px;"
                " border: 1px solid rgba(255,255,255,24);"
            )
        else:
            card.setStyleSheet(
                "background-color: rgba(255,255,255,245); border-radius: 12px;"
                " border: 1px solid rgba(0,0,0,16);"
            )
        return panel

    def _populate_qd_panel(self):
        cc = getattr(self, "_qd_class_combo", None)
        if cc is None:
            return
        saved = str(readme_settings_async("floating_window_management", "quick_draw_class_name") or "")
        # demo 中列表为空，使用占位
        cc.blockSignals(True)
        cc.clear()
        cc.addItems(["示例班级A", "示例班级B"])
        if saved and cc.findText(saved) >= 0:
            cc.setCurrentText(saved)
        cc.blockSignals(False)
        self._refresh_qd_filters(cc.currentText(), self._qd_range_combo, self._qd_gender_combo)

    def _refresh_qd_filters(self, class_name, range_combo, gender_combo):
        from qfluentwidgets import ComboBox
        saved_g = str(readme_settings_async("floating_window_management", "quick_draw_group_filter") or "")
        saved_s = str(readme_settings_async("floating_window_management", "quick_draw_gender_filter") or "")

        range_items = ["全部", "小组1", "小组2"]
        gender_items = ["全部", "男", "女"]

        for combo, items, saved in (
            (range_combo, range_items, saved_g),
            (gender_combo, gender_items, saved_s),
        ):
            combo.blockSignals(True)
            combo.clear()
            combo.addItems(items)
            idx = combo.findText(saved)
            combo.setCurrentIndex(idx if idx >= 0 else 0)
            combo.blockSignals(False)

    def _position_qd_panel(self, anchor: QWidget):
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

    # ==================== 主题样式 ====================

    def _apply_theme_style(self):
        dark = self._is_dark()
        self._container.setAttribute(Qt.WA_StyledBackground, True)
        if dark:
            self._container.setStyleSheet(
                "background-color: rgba(32,32,32,180); border-radius: 12px;"
                " border: 1px solid rgba(255,255,255,20);"
            )
        else:
            self._container.setStyleSheet(
                "background-color: rgba(255,255,255,220); border-radius: 12px;"
                " border: 1px solid rgba(0,0,0,12);"
            )
        direction = "right" if self.x() < 0 else "left"
        self._update_arrow_button_style(direction)

    def _update_arrow_button_style(self, direction: str = "right"):
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
            btn.setIcon(self._get_icon("ic_fluent_people_20_filled"))
            btn.setIconSize(self._storage_icon_size)
        elif style == 1:
            btn.setIcon(QIcon())
            btn.setText("抽")
            btn.setFont(self._font(self._storage_font_size))
        else:
            btn.setIcon(QIcon())
            btn.setText(">" if direction == "right" else "<")
            btn.setFont(self._font(self._storage_font_size))

    # ==================== 大小预设 ====================

    def _apply_size_setting(self, idx: int):
        presets = {
            0: (QSize(20, 20), QSize(6, 6),  4,  QSize(20, 20), QSize(12, 12), 6),
            1: (QSize(30, 30), QSize(12, 12), 6,  QSize(25, 25), QSize(15, 15), 8),
            2: (QSize(40, 40), QSize(18, 18), 8,  QSize(28, 28), QSize(16, 16), 9),
            3: (QSize(50, 50), QSize(22, 22), 10, QSize(30, 30), QSize(18, 18), 10),
            4: (QSize(60, 60), QSize(28, 28), 12, QSize(35, 35), QSize(20, 20), 11),
            5: (QSize(70, 70), QSize(34, 34), 14, QSize(40, 40), QSize(22, 22), 12),
            6: (QSize(80, 80), QSize(40, 40), 16, QSize(45, 45), QSize(24, 24), 13),
        }
        (self._btn_size, self._icon_size, self._font_size,
         self._storage_btn_size, self._storage_icon_size, self._storage_font_size) = \
            presets.get(idx, presets[3])

    # ==================== 按钮控制值规范化 ====================

    def _normalize_button_control(self, value) -> list[str]:
        allowed = {"roll_call", "quick_draw", "lottery", "face_draw", "timer"}
        if isinstance(value, list):
            keys = [v.strip() for v in value if isinstance(v, str) and v.strip() in allowed]
            return keys or self._map_button_combos(0)
        combos = self._map_button_combos
        try:
            idx = int(value or 0)
        except Exception:
            idx = 0
        return combos(idx)

    def _map_button_combos(self, idx: int) -> list[str]:
        table = [
            ["roll_call"], ["quick_draw"], ["lottery"],
            ["roll_call", "quick_draw"], ["roll_call", "lottery"],
            ["quick_draw", "lottery"], ["roll_call", "quick_draw", "lottery"],
            ["timer"], ["roll_call", "timer"], ["quick_draw", "timer"],
            ["lottery", "timer"], ["roll_call", "quick_draw", "timer"],
            ["roll_call", "lottery", "timer"], ["quick_draw", "lottery", "timer"],
            ["roll_call", "quick_draw", "lottery", "timer"],
        ]
        idx = max(0, min(idx, len(table) - 1))
        return table[idx]

    # ==================== 位置管理 ====================

    def _apply_position(self):
        x = int(readme_settings_async("float_position", "x") or 100)
        y = int(readme_settings_async("float_position", "y") or 100)
        nx, ny = self._clamp_to_screen(x, y)
        self.move(nx, ny)
        if self._stick_to_edge:
            self._stick_to_nearest_edge()

    def _clamp_to_screen(self, x: int, y: int) -> tuple[int, int]:
        scr = QGuiApplication.screenAt(self.frameGeometry().center()) or QApplication.primaryScreen()
        geo = scr.availableGeometry()
        cx = max(geo.left(), min(x, geo.right() - self.width() + 1))
        cy = max(geo.top(), min(y, geo.bottom() - self.height() + 1))
        return cx, cy

    def _save_position(self):
        update_settings("float_position", "x", self.x())
        update_settings("float_position", "y", self.y())
        self.positionChanged.emit(self.x(), self.y())

    # ==================== 拖拽 ====================

    def _install_drag_filters(self):
        self._container.installEventFilter(self)
        for w in self._container.findChildren(QWidget):
            w.installEventFilter(self)

    def _begin_drag(self):
        if not self._draggable:
            return
        self._close_quick_draw_extend_panel()
        self._dragging = True
        self.setCursor(Qt.ClosedHandCursor)

    def _end_drag(self):
        self._dragging = False
        self.setCursor(Qt.ArrowCursor)
        self._stick_to_nearest_edge()
        self._save_position()
        if self.floating_window_stick_to_edge:
            QTimer.singleShot(100, self._check_edge_proximity)

    def _should_start_drag(self, delta: QPoint, duration: int) -> bool:
        if duration < self.MIN_DRAG_TIME:
            return False
        threshold = self.DRAG_THRESHOLD * 2 if duration < 150 else self.DRAG_THRESHOLD
        return abs(delta.x()) >= threshold or abs(delta.y()) >= threshold

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton and self._draggable:
            self._close_quick_draw_extend_panel()
            self._press_pos = e.globalPosition().toPoint()
            self._press_time = int(time.monotonic() * 1000)
            self._dragging = False
            self._drag_timer.stop()
            self._drag_timer.start(self._long_press_ms)

    def mouseMoveEvent(self, e):
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
        if e.button() == Qt.LeftButton:
            self._drag_timer.stop()
            self.setCursor(Qt.ArrowCursor)
            if self._dragging and self._draggable:
                self._end_drag()
            self._dragging = False

    def eventFilter(self, obj, event):
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
        if not self._stick_to_edge:
            return
        fg = self.frameGeometry()
        scr = QGuiApplication.screenAt(fg.center()) or QApplication.primaryScreen()
        geo = scr.availableGeometry()
        left = fg.left() - geo.left()
        right = geo.right() - fg.right()
        if left <= self.DEFAULT_EDGE_THRESHOLD:
            self.move(geo.left(), self.y())
        elif right <= self.DEFAULT_EDGE_THRESHOLD:
            self.move(geo.right() - self.width() + 1, self.y())

    def _cancel_retract(self):
        if self._retract_timer.isActive():
            self._retract_timer.stop()

    def _check_edge_proximity(self, immediate: bool = False):
        if not self.floating_window_stick_to_edge:
            return
        if hasattr(self, "animation") and self.animation.state() == 2:  # Running
            self.animation.stop()

        scr = QApplication.primaryScreen().availableGeometry()
        pos = self.pos()
        w = self.width()
        h = self.height()
        threshold = 5

        if pos.x() <= threshold:
            if not hasattr(self, "_original_position"):
                self._original_position = pos
            end_rect = QRect(scr.left() - w + 1, pos.y(), w, h)
            if immediate:
                self.setGeometry(end_rect)
                self._create_arrow_button("right", 0, pos.y() + h // 2 - self._storage_btn_size.height() // 2)
                self._retracted = True
                return
            self._animate_to(end_rect, lambda: (
                self._create_arrow_button("right", 0, pos.y() + h // 2 - self._storage_btn_size.height() // 2),
                setattr(self, "_retracted", True),
            ))
            return

        if pos.x() + w >= scr.width() - threshold:
            if not hasattr(self, "_original_position"):
                self._original_position = pos
            end_rect = QRect(scr.right() - 1, pos.y(), w, h)
            if immediate:
                self.setGeometry(end_rect)
                self._create_arrow_button("left", scr.width() - self._storage_btn_size.width(), pos.y() + h // 2 - self._storage_btn_size.height() // 2)
                self._retracted = True
                return
            self._animate_to(end_rect, lambda: (
                self._create_arrow_button("left", scr.width() - self._storage_btn_size.width(), pos.y() + h // 2 - self._storage_btn_size.height() // 2),
                setattr(self, "_retracted", True),
            ))
            return

        if not self._retracted:
            self._save_position()
        if hasattr(self, "_original_position"):
            del self._original_position
        self._retracted = False

    def _animate_to(self, end_rect: QRect, on_finished=None):
        from PySide6.QtCore import QPropertyAnimation
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(400)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animation.setStartValue(self.geometry())
        self.animation.setEndValue(end_rect)
        if on_finished:
            self.animation.finished.connect(lambda: on_finished())
        self.animation.start()

    def _expand_from_edge(self):
        scr = QApplication.primaryScreen().availableGeometry()
        if self.x() < scr.left():
            self.move(scr.left(), self.y())
        elif self.x() + self.width() > scr.right():
            self.move(scr.right() - self.width() + 1, self.y())
        self._retracted = False

    def _auto_hide_window(self):
        if self.floating_window_stick_to_edge and not self._retracted:
            self._check_edge_proximity()

    def _schedule_auto_hide(self, force: bool = False):
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

    # ==================== 箭头按钮（收纳指示器）====================

    def _create_arrow_button(self, direction: str, x: int, y: int):
        self._delete_arrow_button()

        widget = DraggableWidget()
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

        self.arrow_widget = widget
        self.storage_window = widget

    def _delete_arrow_button(self):
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

    def _show_hidden_window(self, direction: str):
        if hasattr(self, "animation") and self.animation.state() == 2:
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

        from PySide6.QtCore import QPropertyAnimation
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.Type.OutQuad)
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
        if hasattr(self, "_auto_hide_timer") and self._auto_hide_timer.isActive():
            self._auto_hide_timer.stop()

    def leaveEvent(self, e):
        self._schedule_auto_hide(force=True)

    def showEvent(self, event):
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
        super().hideEvent(event)
        if not self._suppress_visibility_tracking:
            self._user_requested_visible = False
            if self.storage_window and self.storage_window.isVisible():
                try:
                    self.storage_window.hide()
                except Exception:
                    pass

    def closeEvent(self, event):
        if self._close_guard_enabled and not QApplication.instance().closingDown():
            event.ignore()
            now = int(QDateTime.currentMSecsSinceEpoch())
            if now - self._close_guard_last_log_ms >= 5000:
                self._close_guard_last_log_ms = now
            try:
                self.show()
                self.raise_()
            except Exception:
                pass
            return
        super().closeEvent(event)

    # ==================== 前台窗口隐藏 ====================

    def _split_match_list(self, raw: str) -> list[str]:
        return [
            s.lower() for part in (raw or "").replace("\n", ";").split(";")
            if (s := part.strip())
        ]

    def _get_foreground_info(self) -> tuple[str, str, int]:
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
        if hidden == self._hidden_by_foreground:
            return
        self._hidden_by_foreground = hidden
        self._suppress_visibility_tracking = True
        try:
            if hidden:
                self._pre_fg_main_visible  = self.isVisible()
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
        self.set_user_requested_visible(not self._user_requested_visible)

    # ==================== 设置变化响应 ====================

    def _on_setting_changed(self, section: str, key: str, value):
        if section == "floating_window_management":
            self._handle_fw_setting(key, value)
        elif section == "float_position":
            if key == "x":
                nx, ny = self._clamp_to_screen(int(value or 0), self.y())
                self.move(nx, ny)
            elif key == "y":
                nx, ny = self._clamp_to_screen(self.x(), int(value or 0))
                self.move(nx, ny)

    def _handle_fw_setting(self, key: str, value):
        if key == "startup_display_floating_window":
            if bool(value):
                self.show()
            else:
                self.hide()
            self.visibilityChanged.emit(bool(value))

        elif key == "extend_quick_draw_component":
            self._extend_quick_draw = bool(value)
            self._close_quick_draw_extend_panel()
            self.rebuild_ui()

        elif key == "floating_window_opacity":
            self._opacity = float(value or 0.8)
            self.setWindowOpacity(self._opacity)
            self._update_arrow_button_style("right" if self.x() < 0 else "left")

        elif key == "floating_window_theme":
            self._floating_window_theme = int(value or 0)
            self.rebuild_ui()
            self._apply_theme_style()

        elif key == "floating_window_topmost_mode":
            self._topmost_mode = int(value or 0)
            self._refresh_window_flags()
            if self._topmost_mode != 0 and not self._periodic_topmost_timer.isActive():
                self._periodic_topmost_timer.start(100)
            elif self._topmost_mode == 0 and self._periodic_topmost_timer.isActive():
                self._periodic_topmost_timer.stop()

        elif key == "floating_window_draggable":
            self._draggable = bool(value)
            if not self._draggable:
                self._dragging = False
                self.setCursor(Qt.ArrowCursor)
                self._drag_timer.stop()
                self._stick_to_nearest_edge()

        elif key == "floating_window_placement":
            self._placement = int(value or 0)
            self.rebuild_ui()

        elif key == "floating_window_display_style":
            self._display_style = int(value or 0)
            self.rebuild_ui()

        elif key == "floating_window_stick_to_edge":
            self._stick_to_edge = bool(value)
            self.floating_window_stick_to_edge = bool(value)
            if bool(value):
                QTimer.singleShot(100, self._check_edge_proximity)
            else:
                self._delete_arrow_button()
                if self._retracted:
                    self._expand_from_edge()

        elif key == "floating_window_stick_to_edge_recover_seconds":
            self._retract_seconds = int(value or 5)
            self.custom_retract_time = self._retract_seconds

        elif key == "floating_window_long_press_duration":
            self._long_press_ms = int(value or 150)

        elif key == "floating_window_stick_to_edge_display_style":
            self._stick_indicator_style = int(value or 0)
            self.custom_display_mode = self._stick_indicator_style
            # 实时刷新已显示的收纳指示器
            if self.arrow_widget and self.arrow_widget.isVisible():
                direction = "right" if self.x() < 0 else "left"
                self._update_arrow_button_style(direction)

        elif key == "floating_window_size":
            self._apply_size_setting(int(value or 3))
            self.rebuild_ui()

        elif key == "floating_window_button_control":
            self._buttons_spec = self._normalize_button_control(value)
            self.rebuild_ui()

        elif key == "do_not_steal_focus":
            self._do_not_steal_focus = bool(value)
            self._refresh_window_flags()

        elif key == "hide_floating_window_on_foreground":
            self._hide_on_foreground_enabled = bool(value)
            if bool(value):
                if not self._foreground_timer.isActive():
                    self._foreground_timer.start()
            else:
                if self._foreground_timer.isActive():
                    self._foreground_timer.stop()
                self._apply_foreground_hidden(False)

        elif key == "hide_floating_window_on_foreground_window_titles":
            self._hide_on_foreground_titles = self._split_match_list(str(value or ""))
            QTimer.singleShot(0, self._check_foreground_hide)

        elif key == "hide_floating_window_on_foreground_process_names":
            self._hide_on_foreground_processes = self._split_match_list(str(value or ""))
            QTimer.singleShot(0, self._check_foreground_hide)

        self._apply_theme_style()

    def _on_theme_changed(self):
        if int(getattr(self, "_floating_window_theme", 0) or 0) == 0:
            self.rebuild_ui()
        self._apply_theme_style()
