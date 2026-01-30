# coding:utf-8
# 标准库导入
import ctypes
import os
from typing import Dict, Any

# 第三方库导入
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from qfluentwidgets import *
from qfluentwidgets import FluentIcon as FIF

# 本地模块导入
from ...common.config import cfg


class LevitationWindow(QWidget):
    """
    悬浮窗窗口类
    提供可拖拽、贴边隐藏、主题切换等功能的悬浮窗口
    """

    # ==================== 信号定义 ====================
    visibilityChanged = pyqtSignal(bool)
    positionChanged = pyqtSignal(int, int)

    # ==================== 类常量 ====================
    DEFAULT_OPACITY = 0.8
    DEFAULT_PLACEMENT = 0
    DEFAULT_DISPLAY_STYLE = 0
    DEFAULT_EDGE_THRESHOLD = 5
    DEFAULT_RETRACT_SECONDS = 5
    DEFAULT_LONG_PRESS_MS = 150  # 默认长按时间，稍微增加避免误触发
    DEFAULT_BUTTON_SIZE = QSize(50, 50)  # 按钮大小
    DEFAULT_ICON_SIZE = QSize(24, 24)  # 图标大小
    DEFAULT_SPACING = 6
    DEFAULT_MARGINS = 6  # 贴边隐藏时的最小间距
    DRAG_THRESHOLD = 12  # 拖拽触发阈值，增加阈值避免误识别按钮点击为拖动
    MIN_DRAG_TIME = 100  # 最小拖动识别时间（毫秒），避免极短时间内的移动被识别为拖动

    def __init__(self, parent=None):
        """初始化悬浮窗窗口"""
        super().__init__(parent)

        # ==================== 基础设置 ====================
        self._setup_window_properties()

        # ==================== 拖拽相关属性 ====================
        self._init_drag_properties()

        # ==================== 贴边隐藏属性 ====================
        self._init_edge_properties()

        # ==================== UI相关属性 ====================
        self._init_ui_properties()

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

    # ==================== 初始化方法 ====================

    def _setup_window_properties(self):
        """设置窗口基础属性"""
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._base_window_flags = (
            Qt.FramelessWindowHint | Qt.Tool | Qt.NoDropShadowWindowHint
        )
        self.setWindowFlags(self._base_window_flags | Qt.WindowStaysOnTopHint)

    def _init_drag_properties(self):
        """初始化拖拽相关属性"""
        self._drag_timer = QTimer(self)
        self._drag_timer.setSingleShot(True)
        self._drag_timer.timeout.connect(self._begin_drag)
        self._dragging = False
        self._press_pos = QPoint()
        self._press_time = 0  # 鼠标按下时间戳
        self._click_intent = False  # 标记是否为点击意图

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

    def _init_ui_properties(self):
        """初始化UI相关属性"""
        self._buttons_spec = ["download", "settings"]
        self._font_family = QFont().family()
        self._container = QWidget(self)
        self._layout = None
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

    def _init_settings(self):
        """初始化设置配置"""
        # 基础显示设置
        self._visible_on_start = False
        self._opacity = self.DEFAULT_OPACITY

        # 布局设置
        self._placement = 0
        self._display_style = 0

        # 拖拽设置
        self._draggable = True
        self._long_press_ms = self.DEFAULT_LONG_PRESS_MS

        # 贴边设置
        self._stick_to_edge = True
        self._retract_seconds = self.DEFAULT_RETRACT_SECONDS
        self._stick_indicator_style = 0

        # 浮窗大小设置
        self._apply_size_setting(1)

        # 无焦点模式设置
        self._do_not_steal_focus = False
        self._topmost_mode = 1
        self._refresh_window_flags()

        # 贴边隐藏功能配置
        self._init_edge_hide_settings()

    def _init_edge_hide_settings(self):
        """初始化贴边隐藏功能设置"""
        self.floating_window_stick_to_edge = True
        self.custom_retract_time = self._retract_seconds
        self.custom_display_mode = self._stick_indicator_style
        self._retracted = False

    def _apply_size_setting(self, size_idx: int):
        """应用浮窗大小设置

        Args:
            size_idx: 大小索引，0=超级小，1=超小，2=小，3=中，4=大，5=超大，6=超级大
        """
        if size_idx == 0:
            # 超级小
            self._btn_size = QSize(20, 20)
            self._icon_size = QSize(6, 6)
            self._font_size = 4
        elif size_idx == 1:
            # 超小
            self._btn_size = QSize(30, 30)
            self._icon_size = QSize(12, 12)
            self._font_size = 6
        elif size_idx == 2:
            # 小
            self._btn_size = QSize(40, 40)
            self._icon_size = QSize(18, 18)
            self._font_size = 8
        elif size_idx == 3:
            # 中
            self._btn_size = QSize(50, 50)
            self._icon_size = QSize(22, 22)
            self._font_size = 10
        elif size_idx == 4:
            # 大
            self._btn_size = QSize(60, 60)
            self._icon_size = QSize(28, 28)
            self._font_size = 12
        elif size_idx == 5:
            # 超大
            self._btn_size = QSize(70, 70)
            self._icon_size = QSize(34, 34)
            self._font_size = 14
        elif size_idx == 6:
            # 超级大
            self._btn_size = QSize(80, 80)
            self._icon_size = QSize(40, 40)
            self._font_size = 16

    def _connect_signals(self):
        """连接信号"""
        # 连接主题变更信号
        try:
            cfg.themeChanged.connect(self._on_theme_changed)
        except Exception:
            pass

    def _on_theme_changed(self):
        """主题变更处理"""
        self._apply_theme_style()

    def rebuild_ui(self):
        """
        重新构建浮窗UI
        删除当前布局并创建新的布局
        """
        # 清除现有按钮
        self._clear_buttons()

        # 重新创建容器布局
        container_layout = self._create_container_layout()

        # 设置新的布局
        old_layout = self._container.layout()
        if old_layout:
            QWidget().setLayout(old_layout)  # 从容器中移除旧布局

        self._container.setLayout(container_layout)

        # 重新添加按钮
        for i, spec in enumerate(self._buttons_spec):
            btn = self._create_button(spec)
            self._add_button(btn, i, len(self._buttons_spec))

        self._container.adjustSize()
        self.adjustSize()
        self._install_drag_filters()

    def _clear_buttons(self):
        """清除所有按钮"""
        # 清除顶层和底层的按钮
        if hasattr(self, "_top") and self._top and self._top.layout():
            top_layout = self._top.layout()
            while top_layout.count():
                item = top_layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()

        if hasattr(self, "_bottom") and self._bottom and self._bottom.layout():
            bottom_layout = self._bottom.layout()
            while bottom_layout.count():
                item = bottom_layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()

        # 清除容器直接包含的按钮
        container_layout = self._container.layout()
        if container_layout:
            while container_layout.count():
                item = container_layout.takeAt(0)
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
        return f

    def _apply_theme_style(self):
        """应用主题样式"""
        # 主题样式应用：深色/浅色配色修正
        dark = isDarkTheme()
        self._container.setAttribute(Qt.WA_StyledBackground, True)
        if dark:
            self._container.setStyleSheet(
                "background-color: rgba(32,32,32,180); border-radius: 12px; border: 1px solid rgba(255,255,255,20);"
            )
        else:
            self._container.setStyleSheet(
                "background-color: rgba(255,255,255,220); border-radius: 12px; border: 1px solid rgba(0,0,0,12);"
            )

    def _icon_pixmap(self, icon):
        """获取图标 pixmap"""
        if hasattr(icon, "icon"):
            qicon = icon.icon()
        elif isinstance(icon, QIcon):
            qicon = icon
        else:
            qicon = QIcon()
        return qicon.pixmap(self._icon_size)

    def _refresh_window_flags(self):
        """刷新窗口标志"""
        flags = self._base_window_flags
        if self._topmost_mode != 0:
            flags |= Qt.WindowStaysOnTopHint
        if self._do_not_steal_focus:
            flags |= Qt.WindowDoesNotAcceptFocus
        self.setWindowFlags(flags)
        if self.isVisible():
            self.hide()
            self.show()

    def _build_ui(self):
        """构建UI"""
        lay = self._container.layout()
        if lay:
            while lay.count():
                item = lay.takeAt(0)
                w = item.widget()
                if w:
                    w.deleteLater()
            lay.deleteLater()
        if not self._layout:
            self._layout = QHBoxLayout(self)
            self._layout.setContentsMargins(
                self._margins, self._margins, self._margins, self._margins
            )
            self._layout.addWidget(self._container)
        else:
            self._layout.setContentsMargins(
                self._margins, self._margins, self._margins, self._margins
            )
        self._container_layout = self._create_container_layout()
        self._container.setLayout(self._container_layout)
        self._container_layout.setAlignment(Qt.AlignCenter)
        for i, spec in enumerate(self._buttons_spec):
            btn = self._create_button(spec)
            self._add_button(btn, i, len(self._buttons_spec))
        self._container.adjustSize()
        self.adjustSize()
        self._install_drag_filters()

    def _apply_window(self):
        """应用窗口设置"""
        self.setWindowOpacity(self._opacity)
        if self._visible_on_start:
            self.show()
            # 浮窗显示后立即检测边缘
            QTimer.singleShot(100, self._check_edge_proximity)
        else:
            self.hide()

    def _apply_position(self):
        """应用位置设置"""
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

    def _create_container_layout(self):
        """创建容器布局"""
        if hasattr(self, "_top") and self._top:
            self._top.deleteLater()
            self._top = None
        if hasattr(self, "_bottom") and self._bottom:
            self._bottom.deleteLater()
            self._bottom = None
        if self._placement == 1:  # 垂直布局
            lay = QVBoxLayout()
            lay.setContentsMargins(
                self._margins, self._margins, self._margins, self._margins
            )
            lay.setSpacing(self._spacing)
            return lay
        if self._placement == 2:  # 水平布局
            lay = QHBoxLayout()
            lay.setContentsMargins(
                self._margins, self._margins, self._margins, self._margins
            )
            lay.setSpacing(self._spacing)
            return lay
        lay = QVBoxLayout()
        lay.setContentsMargins(
            self._margins, self._margins, self._margins, self._margins
        )
        lay.setSpacing(self._spacing)
        self._top = QWidget()
        self._top.setAttribute(Qt.WA_TranslucentBackground)
        self._bottom = QWidget()
        self._bottom.setAttribute(Qt.WA_TranslucentBackground)
        t = QHBoxLayout(self._top)
        t.setContentsMargins(0, 0, 0, 0)
        t.setSpacing(self._spacing)
        t.setAlignment(Qt.AlignCenter)
        b = QHBoxLayout(self._bottom)
        b.setContentsMargins(0, 0, 0, 0)
        b.setSpacing(self._spacing)
        b.setAlignment(Qt.AlignCenter)
        lay.addWidget(self._top)
        lay.addWidget(self._bottom)
        return lay

    def _handle_button_click(self, spec):
        """处理按钮点击事件

        Args:
            spec: 按钮类型标识
        """
        # 这里可以根据需要添加按钮点击后的处理逻辑
        if spec == "download":
            # 触发下载功能
            pass
        elif spec == "settings":
            # 打开设置界面
            pass

    def _create_button(self, spec: str) -> QPushButton:
        """创建按钮

        Args:
            spec: 按钮类型标识

        Returns:
            创建好的按钮实例
        """
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

    def _get_button_config(self, spec: str) -> Dict[str, Any]:
        """获取按钮配置信息

        Args:
            spec: 按钮类型标识

        Returns:
            按钮配置字典，包含图标、文本
        """
        button_configs = {
            "download": {
                "icon": FIF.DOWNLOAD,
                "text": "下载",
            },
            "settings": {
                "icon": FIF.SETTING,
                "text": "设置",
            },
        }

        # 默认配置
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
        btn.setStyleSheet("background: transparent; border: none;")
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
        # 复合按钮图标不置灰，避免低对比；忽略鼠标事件
        label.setAttribute(Qt.WA_TransparentForMouseEvents, True)  # 忽略鼠标事件
        label.setFocusPolicy(Qt.NoFocus)  # 无焦点
        # 标签样式：居中对齐、无背景、无边框
        label.setStyleSheet("background: transparent; border: none;")
        return label

    def _create_text_label(self, text: str) -> QLabel:
        """创建文本标签（用于复合按钮）"""
        label = QLabel(text)
        label.setAlignment(Qt.AlignCenter)
        label.setFont(self._font(self._font_size))
        label.setAttribute(Qt.WA_TransparentForMouseEvents, True)  # 忽略鼠标事件
        label.setFocusPolicy(Qt.NoFocus)  # 无焦点
        # 标签样式：居中对齐、无背景、无边框
        label.setStyleSheet("background: transparent; border: none;")
        return label

    def _add_button(self, btn, index, total):
        """添加按钮到布局"""
        if self._placement == 1:
            self._container.layout().addWidget(btn, 0, Qt.AlignCenter)
            return
        if self._placement == 2:
            self._container.layout().addWidget(btn, 0, Qt.AlignCenter)
            return
        # 前半放顶行，后半放底行
        split = (total + 1) // 2
        if index < split:
            self._top.layout().addWidget(btn, 0, Qt.AlignCenter)
        else:
            self._bottom.layout().addWidget(btn, 0, Qt.AlignCenter)

    def mousePressEvent(self, e):
        """鼠标按下事件"""
        if e.button() == Qt.LeftButton:
            if not self._draggable:
                return  # 如果不可拖动，直接返回
            self._press_pos = e.globalPos()
            self._press_time = e.timestamp()  # 记录鼠标按下时间戳
            self._dragging = False
            self._drag_timer.stop()
            self._drag_timer.start(self._long_press_ms)

    def _begin_drag(self):
        """开始拖拽"""
        if not self._draggable:
            return
        self._dragging = True
        self.setCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, e):
        """处理鼠标移动事件"""
        # 如果不可拖动，停止任何正在进行的拖动
        if not self._draggable:
            if self._dragging:
                self._dragging = False
                self.setCursor(Qt.ArrowCursor)
            return

        if e.buttons() & Qt.LeftButton:
            cur = e.globalPos()

            # 检查是否需要开始拖拽，添加时间检测避免误识别点击为拖动
            if not self._dragging:
                delta = cur - self._press_pos
                press_duration = (
                    e.timestamp() - self._press_time if self._press_time > 0 else 0
                )
                if self._should_start_drag(delta, press_duration):
                    self._begin_drag()

            # 执行拖拽
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
            if self._dragging:
                self._dragging = False
                # 只有在可拖动且是用户主动拖动的情况下才保存位置
                if self._draggable:
                    self._end_drag_operation()

    def _should_start_drag(self, delta: QPoint, duration: int = 0) -> bool:
        """判断是否应该开始拖拽

        Args:
            delta: 鼠标移动偏移量
            duration: 鼠标按下持续时间（毫秒）

        Returns:
            是否应该开始拖拽
        """
        # 智能拖动检测：根据持续时间调整识别阈值
        # 1. 首先检查最小时间阈值，避免极短时间内的移动被识别为拖动
        if duration < self.MIN_DRAG_TIME:
            return False  # 时间太短，不识别为拖动

        # 2. 根据持续时间调整距离阈值
        min_distance = self.DRAG_THRESHOLD
        if duration < 150:  # 快速点击（100-150ms）
            min_distance = self.DRAG_THRESHOLD * 2  # 需要较大的移动距离
        # duration >= 150ms 正常使用默认阈值

        return abs(delta.x()) >= min_distance or abs(delta.y()) >= min_distance

    def eventFilter(self, obj, event):
        """事件过滤器，处理拖拽相关事件"""
        if not self._draggable:
            return False

        if event.type() == QEvent.MouseButtonPress:
            return self._handle_mouse_press_event(event)
        elif event.type() == QEvent.MouseMove:
            return self._handle_mouse_move_event(event)
        elif event.type() == QEvent.MouseButtonRelease:
            return self._handle_mouse_release_event(event)

        return False

    def _handle_mouse_press_event(self, event) -> bool:
        """处理鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            if not self._draggable:
                # 如果不可拖动，不启动拖动计时器
                return False
            self._press_pos = event.globalPos()
            self._press_time = event.timestamp()  # 记录时间戳
            self._dragging = False
            self._drag_timer.stop()
            self._drag_timer.start(self._long_press_ms)
        return False

    def _handle_mouse_move_event(self, event) -> bool:
        """处理鼠标移动事件"""
        # 如果不可拖动，停止拖动操作
        if not self._draggable:
            if self._dragging:
                self._dragging = False
                self.setCursor(Qt.ArrowCursor)
            return False

        if event.buttons() & Qt.LeftButton:
            cur = event.globalPos()

            # 检查是否需要开始拖拽，添加时间检测避免误识别点击为拖动
            if not self._dragging:
                delta = cur - self._press_pos
                press_duration = (
                    event.timestamp() - self._press_time if self._press_time > 0 else 0
                )
                if self._should_start_drag(delta, press_duration):
                    self._begin_drag()

            # 执行拖拽
            if self._dragging:
                delta = cur - self._press_pos
                self.move(self.x() + delta.x(), self.y() + delta.y())
                self._press_pos = cur
                return True

        return False

    def _handle_mouse_release_event(self, event) -> bool:
        """处理鼠标释放事件"""
        if event.button() == Qt.LeftButton:
            self._drag_timer.stop()
            # 如果不可拖动，但仍在拖动状态，则结束拖动操作
            if self._draggable and self._dragging:
                self._end_drag_operation()
                return True
            elif not self._draggable and self._dragging:
                # 如果不可拖动但仍在拖动状态，强制结束拖动
                self._dragging = False
                self.setCursor(Qt.ArrowCursor)

        return False

    def _end_drag_operation(self):
        """结束拖拽操作"""
        self._dragging = False
        self.setCursor(Qt.ArrowCursor)
        self._stick_to_nearest_edge()

        self._save_position()

        # 如果启用了边缘贴边隐藏功能，在拖动结束后检查是否需要贴边
        if self.floating_window_stick_to_edge:
            QTimer.singleShot(100, self._check_edge_proximity)

    def _install_drag_filters(self):
        """安装拖拽事件过滤器"""
        self._container.installEventFilter(self)
        for w in self._container.findChildren(QWidget):
            w.installEventFilter(self)

    def enterEvent(self, e):
        """鼠标进入事件"""
        # 当鼠标进入窗口时，删除可能存在的自动隐藏定时器
        if hasattr(self, "_auto_hide_timer"):
            if self._auto_hide_timer.isActive():
                self._auto_hide_timer.stop()
            # 从对象中移除定时器属性，避免内存泄漏
            delattr(self, "_auto_hide_timer")

    def leaveEvent(self, e):
        """鼠标离开事件"""
        # 如果启用了新的贴边隐藏功能，使用新的自动隐藏逻辑
        if self.floating_window_stick_to_edge:
            # 如果已经处于收纳状态，不需要额外处理
            if not self._retracted:
                # 清除旧的定时器
                if (
                    hasattr(self, "_auto_hide_timer")
                    and self._auto_hide_timer.isActive()
                ):
                    self._auto_hide_timer.stop()
                # 创建或重置自动隐藏定时器
                self._auto_hide_timer = QTimer(self)
                self._auto_hide_timer.setSingleShot(True)
                self._auto_hide_timer.timeout.connect(self._auto_hide_window)
                # 设置延迟时间
                self._auto_hide_timer.start(self.custom_retract_time * 1000)

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
            return
        if right <= self._edge_threshold:
            self.move(geo.right() - self.width() + 1, self.y())
            self._last_stuck = True

    def _cancel_retract(self):
        """取消回收"""
        if self._retract_timer.isActive():
            self._retract_timer.stop()

    def _retract_into_edge(self):
        """收回到边缘"""
        # 防多屏错位：基于当前屏幕几何
        fg = self.frameGeometry()
        scr = QGuiApplication.screenAt(fg.center()) or QApplication.primaryScreen()
        geo = scr.availableGeometry()
        if self.x() <= geo.left():
            # 完全移出屏幕左侧
            self.move(geo.left() - self.width(), self.y())
            self._retracted = True
        elif self.x() + self.width() >= geo.right():
            # 完全移出屏幕右侧
            self.move(geo.right(), self.y())
            self._retracted = True

    def _expand_from_edge(self):
        """从边缘展开"""
        fg = self.frameGeometry()
        scr = QGuiApplication.screenAt(fg.center()) or QApplication.primaryScreen()
        geo = scr.availableGeometry()
        if self.x() < geo.left():
            self.move(geo.left(), self.y())
        elif self.x() + self.width() > geo.right():
            self.move(geo.right() - self.width() + 1, self.y())
        self._retracted = False

    def _check_edge_proximity(self):
        """检测窗口是否靠近屏幕边缘，并实现贴边隐藏功能（带动画效果）"""
        # 如果有正在进行的动画，先停止它
        if (
            hasattr(self, "animation")
            and self.animation.state() == QPropertyAnimation.Running
        ):
            self.animation.stop()

        # 如果贴边隐藏功能未启用，直接返回
        if not self.floating_window_stick_to_edge:
            return

        # 获取屏幕尺寸
        screen = QApplication.primaryScreen().availableGeometry()

        # 获取窗口当前位置和尺寸
        window_pos = self.pos()
        window_width = self.width()
        window_height = self.height()

        # 定义边缘阈值（像素）
        edge_threshold = 5

        # 检测左边缘
        if window_pos.x() <= edge_threshold:
            # 保存主浮窗的原始位置（但不更新实际坐标）
            if not hasattr(self, "_original_position"):
                self._original_position = window_pos

            # 创建平滑动画效果
            self.animation = QPropertyAnimation(self, b"geometry")
            # 设置动画持续时间（更流畅的过渡）
            self.animation.setDuration(400)
            # 设置缓动曲线（使用更自然的缓动）
            self.animation.setEasingCurve(QEasingCurve.OutCubic)

            # 设置动画起始值（当前位置）
            self.animation.setStartValue(self.geometry())

            # 设置动画结束值（隐藏位置）- 移出屏幕但保留部分在屏幕内以保持screenAt()正常工作
            end_rect = QRect(
                screen.left() - window_width + 1,
                window_pos.y(),
                window_width,
                window_height,
            )
            self.animation.setEndValue(end_rect)

            # 动画完成后创建收纳浮窗
            def on_animation_finished():
                # 标记为已收纳状态，但保持原始坐标不变
                self._retracted = True

            self.animation.finished.connect(on_animation_finished)

            # 启动动画
            self.animation.start()
            return

        # 检测右边缘
        elif window_pos.x() + window_width >= screen.width() - edge_threshold:
            # 保存主浮窗的原始位置（但不更新实际坐标）
            if not hasattr(self, "_original_position"):
                self._original_position = window_pos

            # 创建平滑动画效果
            self.animation = QPropertyAnimation(self, b"geometry")
            # 设置动画持续时间（更流畅的过渡）
            self.animation.setDuration(400)
            # 设置缓动曲线（使用更自然的缓动）
            self.animation.setEasingCurve(QEasingCurve.OutCubic)

            # 设置动画起始值（当前位置）
            self.animation.setStartValue(self.geometry())

            # 设置动画结束值（隐藏位置）- 移出屏幕但保留部分在屏幕内以保持screenAt()正常工作
            end_rect = QRect(
                screen.right() - 1,
                window_pos.y(),
                window_width,
                window_height,
            )
            self.animation.setEndValue(end_rect)

            # 动画完成后创建收纳浮窗
            def on_animation_finished():
                # 标记为已收纳状态，但保持原始坐标不变
                self._retracted = True

            self.animation.finished.connect(on_animation_finished)

            # 启动动画
            self.animation.start()
            return

        # 保存新位置（仅在窗口未贴边隐藏时）
        if (
            window_pos.x() > edge_threshold
            and window_pos.x() + window_width < screen.width() - edge_threshold
        ):
            # 只有在非收纳状态下才保存位置
            if not self._retracted:
                self._save_position()
            # 清除原始位置
            if hasattr(self, "_original_position"):
                delattr(self, "_original_position")

        self._retracted = False

    def _auto_hide_window(self):
        """自动隐藏窗口"""
        if self.floating_window_stick_to_edge and not self._retracted:
            self._check_edge_proximity()

    def _save_position(self):
        """保存窗口位置"""
        # 这里可以根据需要保存窗口位置到配置文件
        pass

    def show(self):
        """显示窗口"""
        super().show()
        # 浮窗显示后立即检测边缘
        QTimer.singleShot(100, self._check_edge_proximity)
        self.visibilityChanged.emit(True)

    def hide(self):
        """隐藏窗口"""
        super().hide()
        self.visibilityChanged.emit(False)
