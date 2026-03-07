"""Main AppInterface — ScrollArea with Tree + Content split layout."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QWidget
from qfluentwidgets import ScrollArea

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
        layout.setContentsMargins(0, 48, 0, 0)
        layout.setSpacing(0)

        # Left: tree panel (fixed width)
        self.tree_panel.setFixedWidth(280)
        layout.addWidget(self.tree_panel)

        # Right: content panel (stretch)
        layout.addWidget(self.content_panel, 1)

    def __connectSignals(self):
        self.tree_panel.nodeSelected.connect(self.content_panel.on_node_selected)
