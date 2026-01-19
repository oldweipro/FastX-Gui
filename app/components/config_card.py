# coding:utf-8
import os
import re
from typing import List
from PyQt5.QtCore import Qt, QTime

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QFileDialog

from qfluentwidgets import (IconWidget, BodyLabel, FluentIcon, InfoBarIcon, ComboBox,
                            PrimaryPushButton, LineEdit, GroupHeaderCardWidget, PushButton,
                            CompactSpinBox, SwitchButton, IndicatorPosition, PlainTextEdit,
                            ToolTipFilter, ConfigItem)

from app.common.icon import Logo, PNG
from app.common.config import cfg


class BasicConfigCard(GroupHeaderCardWidget):
    """ Basic config card """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle(self.tr("Basic Settings"))
        self.mediaParser = None

        self.toolsEngineComboBox = ComboBox()
        self.chooseMappingTableButton = PushButton(self.tr("Choose"))
        self.chooseDataTypeButton = PushButton(self.tr("Choose"))
        self.chooseInterfaceButton = PushButton(self.tr("Choose"))
        self.outputFolderButton = PushButton(self.tr("Choose"))

        self.hintIcon = IconWidget(InfoBarIcon.INFORMATION, self)
        self.hintLabel = BodyLabel(self.tr("Click the execute button to start running") + ' 👉')
        self.exeButton = PrimaryPushButton(self.tr("Execute"), self, FluentIcon.PLAY_SOLID)

        self.toolBarLayout = QHBoxLayout()

        self._initWidgets()

    def _initWidgets(self):
        self.setBorderRadius(8)

        self.toolsEngineComboBox.setMinimumWidth(120)
        self.toolsEngineComboBox.addItem(self.tr("L2 Func"), userData="FUNC")
        self.toolsEngineComboBox.addItem(self.tr("Ipc Com"), userData="IPC")
        self.toolsEngineComboBox.addItem(self.tr("Srp Com"), userData="SRP")

        self.toolsEngineComboBox.setMinimumWidth(120)
        self.chooseMappingTableButton.setFixedWidth(120)
        self.chooseDataTypeButton.setFixedWidth(120)
        self.chooseInterfaceButton.setFixedWidth(120)
        self.outputFolderButton.setFixedWidth(120)
        self.exeButton.setFixedWidth(120)

        self.exeButton.setEnabled(True)
        self.chooseDataTypeButton.setEnabled(False)
        self.chooseInterfaceButton.setEnabled(False)
        self.hintIcon.setFixedSize(16, 16)

        self._initLayout()
        self._connectSignalToSlot()

        self.toolsEngineComboBox.setCurrentText(cfg.get(cfg.fastRteToolsEngine))

    def _initLayout(self):
        # add widget to group
        self.toolsEngineGroup = self.addGroup(
            icon=Logo.FFMPEG.icon(),
            title=self.tr("Change Tools"),
            content=self.tr("Select the Tools Engine to Generator"),
            widget=self.toolsEngineComboBox
        )
        self.chooseMappingTableGroup = self.addGroup(
            icon=Logo.GEAR.icon(),
            title=self.tr("Mapping Table Path"),
            content=cfg.get(cfg.fastRteMappingTableFolder),
            widget=self.chooseMappingTableButton
        )
        self.chooseDataTypGroup = self.addGroup(
            icon=Logo.GEAR.icon(),
            title=self.tr("DataType Arxml Path"),
            content=cfg.get(cfg.fastRteDataTypeFolder),
            widget=self.chooseDataTypeButton
        )
        self.chooseInterfaceGroup = self.addGroup(
            icon=Logo.GEAR.icon(),
            title=self.tr("Interface Arxml Path"),
            content=cfg.get(cfg.fastRteInterfaceFolder),
            widget=self.chooseInterfaceButton
        )
        self.outputFolderGroup = self.addGroup(
            icon=Logo.FOLDER.icon(),
            title=self.tr("Output Folder"),
            content=cfg.get(cfg.fastRteOutputFolder),
            widget=self.outputFolderButton
        )

        # add widgets to bottom toolbar
        self.toolBarLayout.setContentsMargins(24, 15, 24, 20)
        self.toolBarLayout.setSpacing(10)
        self.toolBarLayout.addWidget(self.hintIcon, 0, Qt.AlignmentFlag.AlignLeft)
        self.toolBarLayout.addWidget(self.hintLabel, 0, Qt.AlignmentFlag.AlignLeft)
        self.toolBarLayout.addStretch(1)
        self.toolBarLayout.addWidget(self.exeButton, 0, Qt.AlignmentFlag.AlignRight)
        self.toolBarLayout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.vBoxLayout.addLayout(self.toolBarLayout)

    def _onChooseMappingTableButtonClicked(self):
        path, _ = QFileDialog.getOpenFileName(self, self.tr("Choose"))
        if not path or cfg.get(cfg.fastRteMappingTableFolder) == path:
            return
        cfg.set(cfg.fastRteMappingTableFolder, path)
        self.chooseMappingTableGroup.setContent(path)

    def _onChooseDataTypeButtonClicked(self):
        path, _ = QFileDialog.getOpenFileName(self, self.tr("Choose"))
        if not path or cfg.get(cfg.fastRteDataTypeFolder) == path:
            return
        cfg.set(cfg.fastRteDataTypeFolder, path)
        self.chooseDataTypGroup.setContent(path)

    def _onChooseInterfaceButtonClicked(self):
        path, _ = QFileDialog.getOpenFileName(self, self.tr("Choose"))
        if not path or cfg.get(cfg.fastRteInterfaceFolder) == path:
            return
        cfg.set(cfg.fastRteInterfaceFolder, path)
        self.chooseInterfaceGroup.setContent(path)

    def _chooseOutputFolder(self):
        folder = QFileDialog.getExistingDirectory(self, self.tr("Choose folder"), self.outputFolderGroup.content())

        if folder:
            folder = folder.replace("\\", "/")
            cfg.set(cfg.fastRteOutputFolder, folder)
            self.outputFolderGroup.setContent(folder)

    def _onToolsEngineChanged(self):
        icons = [Logo.FFMPEG, Logo.BENTO, PNG.SHAKA_PACKAGER]
        self.toolsEngineGroup.setIcon(icons[self.toolsEngineComboBox.currentIndex()].icon())
        cfg.set(cfg.fastRteToolsEngine, self.toolsEngineComboBox.currentText())

    def _connectSignalToSlot(self):
        self.toolsEngineComboBox.currentIndexChanged.connect(self._onToolsEngineChanged)
        self.outputFolderButton.clicked.connect(self._chooseOutputFolder)
        self.chooseMappingTableButton.clicked.connect(self._onChooseMappingTableButtonClicked)
        self.chooseDataTypeButton.clicked.connect(self._onChooseDataTypeButtonClicked)
        self.chooseInterfaceButton.clicked.connect(self._onChooseInterfaceButtonClicked)