"""Main AppInterface — ScrollArea with Tree + Content split layout."""

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QHBoxLayout, QWidget, QSplitter, QVBoxLayout
from qfluentwidgets import ScrollArea, SmoothScrollArea, ToolButton, LineEditButton
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import ToolTipFilter

from app.common.style_sheet import StyleSheet
from app.view.app_interface.content_panel import ContentPanel
from app.view.app_interface.tree_panel import TreePanel


class AppInterface(ScrollArea):
    """Application management interface with tree navigation and content panels."""

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.view = QWidget(self)

        self.tree_panel = TreePanel(self)
        self.content_panel = ContentPanel(self)

        self.__initWidget()
        self.__initLayout()
        self.__connectSignals()

    def __initWidget(self):
        self.setObjectName("appInterface")
        self.view.setObjectName("view")
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWidget(self.view)
        self.setWidgetResizable(True)
        StyleSheet.APP_INTERFACE.apply(self)


    def __initLayout(self):
        layout = QHBoxLayout(self.view)
        layout.setContentsMargins(0, 48, 10, 0)
        layout.setSpacing(0)
    
        self.splitter = QSplitter(Qt.Orientation.Horizontal, self.view)
        self.splitter.setHandleWidth(0)
        self.splitter.setChildrenCollapsible(False)
        # ========== 左侧面板 ==========
        self.left_panel = SmoothScrollArea()
        self.left_panel.setObjectName("left_panel")
        self.left_panel.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.left_panel.setWidgetResizable(True)
        self.left_container = QWidget()
        self.left_container.setObjectName("left_panel_container")
        self.left_layout = QVBoxLayout(self.left_container)
        self.left_layout.setContentsMargins(12, 12, 12, 12)
        self.left_layout.setSpacing(8)
        self.left_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        # Left: tree panel (fixed width)
        self.tree_panel.setFixedWidth(380)
        self.left_layout.addWidget(self.tree_panel)
    
        # ========== 右侧面板 ==========
        self.right_panel = SmoothScrollArea()
        self.right_panel.setObjectName("right_panel")
        self.right_panel.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.right_panel.setWidgetResizable(True)
        self.right_container = QWidget()
        self.right_container.setObjectName("right_panel_container")
        self.right_layout = QVBoxLayout(self.right_container)
        self.right_layout.setContentsMargins(12, 12, 12, 12)
        self.right_layout.setSpacing(8)
        self.right_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Right: content panel (stretch)
        self.right_layout.addWidget(self.content_panel, 1)

        # 合并
        self.left_panel.setWidget(self.left_container)
        self.right_panel.setWidget(self.right_container)
        self.splitter.addWidget(self.left_panel)
        self.splitter.addWidget(self.right_panel)
        layout.addWidget(self.splitter)

        QTimer.singleShot(0, self._apply_collapsed_state)
    
    def _apply_collapsed_state(self):
        self.left_panel.setFixedWidth(0)
        self._left_panel_expanded = False
        if hasattr(self.content_panel, 'toggle_button'):
            self.content_panel.toggle_button.setToolTip(self.tr("Expand navigation"))
            self.content_panel.toggle_button.clicked.connect(self._toggle_left_panel)

    # ------------------------------------------------------------------
    # 面板展开/收缩
    # ------------------------------------------------------------------
    def _toggle_left_panel(self):
        if self._left_panel_expanded:
            self._collapse_left_panel()
        else:
            self._expand_left_panel()

    def _collapse_left_panel(self):
        self.left_panel.setFixedWidth(0)
        self._left_panel_expanded = False
        if hasattr(self.content_panel, 'toggle_button'):
            self.content_panel.toggle_button.setToolTip(self.tr("Expand navigation"))

    def _expand_left_panel(self):
        self.left_panel.setFixedWidth(400)
        self._left_panel_expanded = True
        if hasattr(self.content_panel, 'toggle_button'):
            self.content_panel.toggle_button.setToolTip(self.tr("Collapse navigation"))

    def __connectSignals(self):
        self.tree_panel.nodeSelected.connect(self.content_panel.on_node_selected)