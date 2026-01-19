# coding:utf-8
from pathlib import Path
from typing import List
from PyQt5.QtCore import Qt, QFileInfo
from PyQt5.QtGui import QDropEvent
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout

from qfluentwidgets import ScrollArea, InfoBar, InfoBarPosition, PushButton

from app.components.info_card import AppInfoCard
from ..components.config_card import BasicConfigCard

class FuncInterface(ScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.view = QWidget(self)

        self.funcInfoCard = AppInfoCard()
        self.basicSettingCard = BasicConfigCard()
        # self.muxSettingCard = MuxConfigCard()
        # self.advanceSettingCard = AdvanceConfigCard()
        # self.proxySettingCard = ProxyConfigCard()
        # self.liveSettingCard = LiveConfigCard()
        # self.decryptionCard = DecryptionConfigCard()

        self.vBoxLayout = QVBoxLayout(self.view)

        self._initWidget()

    def _initWidget(self):
        self.setWidget(self.view)
        self.setAcceptDrops(True)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.vBoxLayout.setSpacing(10)
        self.vBoxLayout.setContentsMargins(0, 0, 10, 10)
        self.vBoxLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.vBoxLayout.addWidget(self.funcInfoCard, 0, Qt.AlignmentFlag.AlignTop)
        self.vBoxLayout.addWidget(self.basicSettingCard, 0, Qt.AlignmentFlag.AlignTop)

        self.resize(780, 800)
        self.setObjectName("packageInterface")
        self.enableTransparentBackground()
        # self._connectSignalToSlot()

    def _onDownloadButtonClicked(self):
        pass

    def _connectSignalToSlot(self):
        self.basicSettingCard.exeButton.clicked.connect(self._onDownloadButtonClicked)