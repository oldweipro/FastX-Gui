# coding:utf-8
import os
import re
from typing import List
from PyQt5.QtCore import Qt, QTime

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QFileDialog

from qfluentwidgets import (IconWidget, BodyLabel, FluentIcon, InfoBarIcon, ComboBox,
                            PrimaryPushButton, LineEdit, GroupHeaderCardWidget, PushButton,
                            CompactSpinBox, SwitchButton, IndicatorPosition, PlainTextEdit,
                            ToolTipFilter, ConfigItem, SettingCardGroup, SpinBox)
from qfluentwidgets import FluentIcon as FIF
from app.common.icon import Logo, PNG, UnicodeIcon
from app.common.config import cfg, TopmostMode


class FloatingWindowBasicSettings(GroupHeaderCardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle(self.tr('basic_settings'))
        self.setBorderRadius(8)

        # 创建控件
        self._create_controls()

    def _create_controls(self):
        """创建所有控件"""

        # 启动时显示浮窗
        self.startup_switch = SwitchButton()
        self.startup_switch.setChecked(cfg.startupDisplayFloatingWindow.value)
        self.startup_switch.checkedChanged.connect(
            lambda v: setattr(cfg.startupDisplayFloatingWindow, 'value', v)
        )
        self.addGroup(
            UnicodeIcon.get_icon_by_name('ic_fluent_desktop_sync_20_filled'),
            "启动时显示浮窗",
            "控制软件启动时是否自动显示浮窗",
            self.startup_switch
        )

        # 浮窗透明度
        self.opacity_spinbox = SpinBox()
        self.opacity_spinbox.setRange(0, 100)
        self.opacity_spinbox.setSuffix("%")
        self.opacity_spinbox.setValue(cfg.floatingWindowOpacity.value)
        self.opacity_spinbox.valueChanged.connect(
            lambda v: setattr(cfg.floatingWindowOpacity, 'value', v)
        )
        self.addGroup(
            UnicodeIcon.get_icon_by_name('ic_fluent_brightness_high_20_filled'),
            "浮窗透明度",
            "调整浮窗透明度",
            self.opacity_spinbox
        )

        # 置顶模式
        self.topmost_combo = ComboBox()
        self.topmost_combo.addItems(["关闭置顶", "置顶", "UIA置顶"])
        self.topmost_combo.setCurrentIndex(cfg.floatingWindowTopmostMode.value.value)
        self.topmost_combo.currentIndexChanged.connect(self._on_topmost_changed)
        self.addGroup(
            FIF.PIN,
            "置顶模式",
            "选择浮窗置顶方式（UIA置顶需以管理员运行）",
            self.topmost_combo
        )

        # 浮窗可拖动
        self.draggable_switch = SwitchButton()
        self.draggable_switch.setChecked(cfg.floatingWindowDraggable.value)
        self.draggable_switch.checkedChanged.connect(
            lambda v: setattr(cfg.floatingWindowDraggable, 'value', v)
        )
        self.addGroup(
            FIF.SHARE,
            "浮窗可拖动",
            "控制浮窗是否可被拖动",
            self.draggable_switch
        )

        # 长按拖动时间
        self.long_press_spinbox = SpinBox()
        self.long_press_spinbox.setRange(50, 3000)
        self.long_press_spinbox.setSingleStep(100)
        self.long_press_spinbox.setSuffix("ms")
        self.long_press_spinbox.setValue(cfg.floatingWindowLongPressDuration.value)
        self.long_press_spinbox.valueChanged.connect(
            lambda v: setattr(cfg.floatingWindowLongPressDuration, 'value', v)
        )
        self.addGroup(
            FIF.SHARE,
            "长按时间",
            "设置浮窗长按时间（毫秒）",
            self.long_press_spinbox
        )

        # 无焦点模式
        self.focus_switch = SwitchButton()
        self.focus_switch.setChecked(cfg.doNotStealFocus.value)
        self.focus_switch.checkedChanged.connect(
            lambda v: setattr(cfg.doNotStealFocus, 'value', v)
        )
        self.addGroup(
            FIF.SHARE,
            "无焦点模式",
            "通知窗口显示时不抢占焦点，保持原有顶层软件焦点",
            self.focus_switch
        )

    def _on_topmost_changed(self, index):
        """置顶模式改变处理"""
        mode_map = {
            0: TopmostMode.DISABLED,
            1: TopmostMode.NORMAL,
            2: TopmostMode.UIA
        }
        cfg.floatingWindowTopmostMode.value = mode_map[index]


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
        self.toolsEngineComboBox.addItem(self.tr("L2 Func"), userData="Func")
        self.toolsEngineComboBox.addItem(self.tr("Ipc Com"), userData="Ipc")
        self.toolsEngineComboBox.addItem(self.tr("Srp Com"), userData="Srp")

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