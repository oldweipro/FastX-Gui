""""
插件卡片组件
展示插件的详细信息，支持单击打开、设置、卸载
"""

from typing import Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter, QColor, QPainterPath
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSizePolicy
from qfluentwidgets import (
    BodyLabel, CaptionLabel, StrongBodyLabel,
    FluentIcon as FIF,
    IconWidget, ProgressRing, FluentIconBase,
    TransparentToolButton, themeColor, qconfig, Theme
)
from app.plugins.plugin_base import PluginInfo, PluginCategory
from app.common.icon import Icon, UnicodeIcon


class PluginCard(QWidget):
    """插件卡片组件 - 自绘圆角，布局更清晰"""

    # 信号定义
    openPluginRequested   = Signal(str)
    settingsRequested     = Signal(str)
    uninstallRequested    = Signal(str)
    docsRequested         = Signal(str)
    releaseNotesRequested = Signal(str)

    _RADIUS = 16  # 圆角半径

    def __init__(self, plugin_info: PluginInfo, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.plugin_info = plugin_info
        self._is_enabled = plugin_info.enabled
        self._hovered = False

        self._init_ui()
        self._setup_connections()

    # ------------------------------------------------------------------ #
    #  UI 初始化
    # ------------------------------------------------------------------ #
    def _init_ui(self):
        self.setFixedSize(300, 168)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setMouseTracking(True)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(14, 14, 14, 10)
        outer.setSpacing(0)

        # -------- 主体：左侧大图标 + 右侧信息列 --------
        body = QHBoxLayout()
        body.setSpacing(14)
        body.setContentsMargins(0, 0, 0, 0)
        body.setAlignment(Qt.AlignmentFlag.AlignTop)

        # 左侧图标（48×48，顶对齐）
        self.icon_widget = IconWidget(self._get_icon(), self)
        self.icon_widget.setFixedSize(62, 62)
        body.addWidget(self.icon_widget, 0, Qt.AlignmentFlag.AlignTop)

        # 右侧信息列：名称 → 版本·分类 → 描述
        right_col = QVBoxLayout()
        right_col.setSpacing(4)
        right_col.setContentsMargins(0, 0, 0, 0)
        right_col.setAlignment(Qt.AlignmentFlag.AlignTop)

        # 插件名称
        self.name_label = StrongBodyLabel(self.plugin_info.name, self)
        self.name_label.setObjectName("name_label")
        self.name_label.setStyleSheet("font-size: 13px; font-weight: 600;")
        self.name_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        right_col.addWidget(self.name_label)

        # 版本 · 分类
        meta_row = QHBoxLayout()
        meta_row.setSpacing(4)
        meta_row.setContentsMargins(0, 0, 0, 0)

        self.version_label = CaptionLabel(f"v{self.plugin_info.version}", self)
        self.version_label.setObjectName("version_label")
        self.version_label.setStyleSheet("font-size: 11px;")
        meta_row.addWidget(self.version_label)

        dot = CaptionLabel("·", self)
        dot.setStyleSheet("font-size: 11px;")
        meta_row.addWidget(dot)

        self.category_label = CaptionLabel(self._get_category_text(), self)
        self.category_label.setObjectName("category_label")
        self.category_label.setStyleSheet("font-size: 11px;")
        meta_row.addWidget(self.category_label)
        meta_row.addStretch(1)
        right_col.addLayout(meta_row)

        # 描述（紧跟版本行下方，右侧列内）
        self.desc_label = BodyLabel(self.plugin_info.description, self)
        self.desc_label.setObjectName("desc_label")
        self.desc_label.setWordWrap(True)
        self.desc_label.setMaximumHeight(36)
        self.desc_label.setStyleSheet("font-size: 11px;")
        right_col.addWidget(self.desc_label)

        body.addLayout(right_col, 1)
        outer.addLayout(body)
        outer.addStretch(1)

        # -------- 底部：作者 + 按钮 --------
        footer = QHBoxLayout()
        footer.setSpacing(4)
        footer.setContentsMargins(0, 0, 0, 0)

        self.author_label = CaptionLabel(f"👤 {self.plugin_info.author}", self)
        self.author_label.setObjectName("author_label")
        self.author_label.setStyleSheet("font-size: 11px;")
        footer.addWidget(self.author_label)
        footer.addStretch(1)

        self.status_ring = ProgressRing(self)
        self.status_ring.setFixedSize(18, 18)
        self.status_ring.setVisible(False)
        footer.addWidget(self.status_ring)

        self.open_btn = TransparentToolButton(
            UnicodeIcon.get_icon_by_name("ic_fluent_open_32_regular"), self
        )
        self.open_btn.setFixedSize(30, 30)
        self.open_btn.setToolTip("打开插件")
        footer.addWidget(self.open_btn)

        self.settings_btn = TransparentToolButton(
            UnicodeIcon.get_icon_by_name("ic_fluent_settings_24_regular"), self
        )
        self.settings_btn.setFixedSize(30, 30)
        self.settings_btn.setToolTip("插件设置")
        footer.addWidget(self.settings_btn)

        # 文档按钮
        self.docs_btn = TransparentToolButton(
            UnicodeIcon.get_icon_by_name("ic_fluent_book_open_24_regular"), self
        )
        self.docs_btn.setFixedSize(30, 30)
        self.docs_btn.setToolTip("查看文档")
        footer.addWidget(self.docs_btn)

        # Release Notes 按钮
        self.release_notes_btn = TransparentToolButton(
            UnicodeIcon.get_icon_by_name("ic_fluent_history_24_regular"), self
        )
        self.release_notes_btn.setFixedSize(30, 30)
        self.release_notes_btn.setToolTip("Release Notes")
        footer.addWidget(self.release_notes_btn)

        # 卸载按钮：内置插件置灰不可用
        self.uninstall_btn = TransparentToolButton(
            UnicodeIcon.get_icon_by_name("ic_fluent_delete_24_regular"), self
        )
        self.uninstall_btn.setFixedSize(30, 30)
        is_builtin = getattr(self.plugin_info, 'builtin', False)
        self.uninstall_btn.setEnabled(not is_builtin)
        self.uninstall_btn.setToolTip("内置插件不可卸载" if is_builtin else "卸载插件")
        footer.addWidget(self.uninstall_btn)

        outer.addLayout(footer)

    # ------------------------------------------------------------------ #
    #  自绘圆角卡片背景
    # ------------------------------------------------------------------ #
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        r = self._RADIUS
        rect = self.rect().adjusted(1, 1, -1, -1)

        path = QPainterPath()
        path.addRoundedRect(rect, r, r)

        # 使用 qconfig.theme 获取当前主题，比 isDarkTheme() 更可靠
        dark = qconfig.theme == Theme.DARK

        # 背景色 - 与底色更渐进，保持柔和层次
        if dark:
            # 暗色主题：与背景更融合的深灰色
            bg = QColor(45, 45, 48, 180) if not self._hovered else QColor(52, 52, 56, 200)
        else:
            # 亮色主题：白色背景，hover时稍微蓝一点
            bg = QColor(252, 252, 254, 230) if not self._hovered else QColor(248, 250, 255, 250)
        painter.fillPath(path, bg)

        # 边框 - 使用主题色系，保持柔和层次
        if self._hovered:
            tc = themeColor()
            border_color = QColor(tc.red(), tc.green(), tc.blue(), 160)
            # hover时边框加粗到2px
            from PySide6.QtGui import QPen
            pen = QPen(border_color, 2)
            painter.setPen(pen)
        else:
            # 边框使用主题色的柔和版本
            tc = themeColor()
            if dark:
                # 暗色主题：主题色的暗色柔和版本
                border_color = QColor(tc.red(), tc.green(), tc.blue(), 30)
            else:
                # 亮色主题：主题色的亮色柔和版本
                border_color = QColor(tc.red(), tc.green(), tc.blue(), 40)
            painter.setPen(border_color)

        painter.drawPath(path)

    # ------------------------------------------------------------------ #
    #  悬停事件
    # ------------------------------------------------------------------ #
    def enterEvent(self, event):
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self.update()
        super().leaveEvent(event)

    # ------------------------------------------------------------------ #
    #  点击事件
    # ------------------------------------------------------------------ #
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            child = self.childAt(event.pos())
            btns = [
                self.settings_btn, self.open_btn, self.uninstall_btn,
                self.docs_btn, self.release_notes_btn, self.status_ring
            ]
            if child not in btns and not any(b.isAncestorOf(child) for b in btns if child):
                self.openPluginRequested.emit(self.plugin_info.name)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.openPluginRequested.emit(self.plugin_info.name)
        super().mouseDoubleClickEvent(event)

    # ------------------------------------------------------------------ #
    #  信号连接
    # ------------------------------------------------------------------ #
    def _setup_connections(self):
        self.open_btn.clicked.connect(lambda: self.openPluginRequested.emit(self.plugin_info.name))
        self.settings_btn.clicked.connect(lambda: self.settingsRequested.emit(self.plugin_info.name))
        self.uninstall_btn.clicked.connect(lambda: self.uninstallRequested.emit(self.plugin_info.name))
        self.docs_btn.clicked.connect(lambda: self.docsRequested.emit(self.plugin_info.name))
        self.release_notes_btn.clicked.connect(lambda: self.releaseNotesRequested.emit(self.plugin_info.name))

    # ------------------------------------------------------------------ #
    #  辅助方法
    # ------------------------------------------------------------------ #
    def _get_icon(self):
        if self.plugin_info.icon_path:
            try:
                if isinstance(self.plugin_info.icon_path, str):
                    if hasattr(Icon, self.plugin_info.icon_path):
                        return getattr(Icon, self.plugin_info.icon_path)
                elif isinstance(self.plugin_info.icon_path, (FluentIconBase, FIF)):
                    return self.plugin_info.icon_path
            except Exception:
                pass
        return FIF.APPLICATION

    def _get_category_text(self) -> str:
        texts = {
            PluginCategory.DIAGNOSTIC:    "诊断工具",
            PluginCategory.COMMUNICATION: "通信工具",
            PluginCategory.SERIAL:        "串口工具",
            PluginCategory.UTILITIES:     "实用工具",
            PluginCategory.CUSTOM:        "自定义",
        }
        return texts.get(self.plugin_info.category, "未知")

    def set_enabled(self, enabled: bool):
        self._is_enabled = enabled
        self.plugin_info.enabled = enabled
        self.update()

    def set_loading(self, loading: bool):
        self.status_ring.setVisible(loading)
        self.settings_btn.setEnabled(not loading)
        self.open_btn.setEnabled(not loading)
        self.docs_btn.setEnabled(not loading)
        self.release_notes_btn.setEnabled(not loading)
        # 内置插件卸载按钮始终保持禁用
        if not getattr(self.plugin_info, 'builtin', False):
            self.uninstall_btn.setEnabled(not loading)

    def is_enabled(self) -> bool:
        return self._is_enabled

    def refresh_style(self):
        """强制刷新样式（用于主题切换时）"""
        self.update()
