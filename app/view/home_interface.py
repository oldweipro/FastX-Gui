from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget
from qfluentwidgets import (
    ScrollArea,
)

from app.common.style_sheet import StyleSheet
from app.components.config_card import AboutInfoHomeIf, BannerWidgetHomeIF2


class HomeInterface(ScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.view = QWidget(self)
        self.banner = BannerWidgetHomeIF2(self.view)
        self.about = AboutInfoHomeIf()
        self.__initWidget()
        self.__initLayout()
        self.loadSamples()
        self.__connectSignalToSlot()

    def __initWidget(self):
        self.setViewportMargins(0, 48, 0, 0)
        self.setObjectName("homeInterface")
        self.view.setObjectName("view")
        StyleSheet.HOME_INTERFACE.apply(self)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWidget(self.view)
        self.setWidgetResizable(True)

    def __initLayout(self):
        # Create Layouts
        self.Layout = QHBoxLayout(self.view)
        self.Layout.setContentsMargins(0, 0, 20, 0)

        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(10, 0, 0, 0)
        self.main_layout.setSpacing(25)
        self.main_layout.setAlignment(Qt.AlignTop)

        self.top_layout = QVBoxLayout()
        self.top_layout.setContentsMargins(0, 0, 0, 0)

        self.guide_layout = QVBoxLayout()
        self.guide_layout.setContentsMargins(20, 20, 20, 20)

        self.bottom_layout = QHBoxLayout()
        self.bottom_layout.setContentsMargins(20, 20, 20, 20)
        self.bottom_layout.setSpacing(12)

        # Add Layouts
        self.Layout.addLayout(self.main_layout)
        self.main_layout.addWidget(self.banner)
        self.main_layout.addLayout(self.top_layout)
        self.main_layout.addLayout(self.guide_layout)
        self.top_layout.addWidget(self.about)
        # self.main_layout.addLayout(self.bottom_layout)

    def loadSamples(self):
        pass

    def __connectSignalToSlot(self):
        pass
