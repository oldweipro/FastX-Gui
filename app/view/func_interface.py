# coding:utf-8
from pathlib import Path
from typing import List
from PyQt5.QtCore import Qt, QFileInfo, QUrl
from PyQt5.QtGui import QDropEvent, QColor
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QGraphicsDropShadowEffect, QLabel, QFrame, QActionGroup

from qfluentwidgets import ScrollArea, InfoBar, InfoBarPosition, PushButton, SubtitleLabel, setFont, MessageBox, \
    SettingCardGroup, MessageBoxBase, LineEdit, PlainTextEdit, SimpleCardWidget, SplitPushButton, ExpandSettingCard, \
    FluentIcon as FIF, Action, CheckableMenu, MenuIndicatorType, CommandBar, TransparentDropDownPushButton

from app.components.info_card import AppInfoCard
from app.components.config_card import BasicConfigCard, FloatingWindowBasicSettings
from app.card.autoplot_setting_card import AutoPlotSettingCard
from app.common.style_sheet import StyleSheet

class CustomMessageBox(MessageBoxBase):
    """ Custom message box """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel(self.tr('Operation Console'), self)

        self.automaticPlotCard = AutoPlotSettingCard(
            icon=FIF.IMAGE_EXPORT,
            title=self.tr("Select SWCs"),
            content="Select SWCs of which should be generate by tools"
        )
        self.automaticPlotCard.switchButton.setVisible(False)

        self.card = SimpleCardWidget(self)
        self.logPanel = QWidget(self)
        self.controlPanel = QFrame(self)

        self.logConsole = PlainTextEdit(self)
        self.logConsole.setReadOnly(True)
        self.logConsole.setPlaceholderText("Operation Logs Console ....")

        self.create_menu_actions()

        self.clearLogBtn = PushButton("Clear", self)
        self.excelChkBtn = PushButton("Function Excel Check", self)
        self.genSwcEtasBtn = PushButton("Generate Function SWC For Etas", self)
        self.genSwcMatlabBtn = PushButton("Generate Function SWC For Matlab", self)

        self.card.setObjectName('card')
        self.logPanel.setObjectName('logPanel')
        self.controlPanel.setObjectName('controlPanel')

        StyleSheet.RTE_INTERFACE.apply(self)

        self.hBoxLayout = QHBoxLayout(self.card)
        self.logLayout = QHBoxLayout(self.logPanel)
        self.panelLayout = QVBoxLayout(self.controlPanel)

        self.logLayout.setContentsMargins(1, 1, 1, 1)
        self.panelLayout.setSpacing(8)
        self.panelLayout.setContentsMargins(14, 16, 14, 14)
        self.panelLayout.setAlignment(Qt.AlignTop)

        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.createCommandBar())        # 添加菜单栏
        self.viewLayout.addWidget(self.automaticPlotCard)
        self.viewLayout.addWidget(self.card)

        self.hBoxLayout.addWidget(self.logPanel, 1)
        # self.hBoxLayout.addWidget(self.controlPanel, 0, Qt.AlignRight) # 取消掉日志右侧控制面板
        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)

        self.logLayout.addWidget(self.logConsole)
        self.panelLayout.addWidget(self.clearLogBtn)
        self.panelLayout.addWidget(self.excelChkBtn)
        self.panelLayout.addWidget(self.genSwcEtasBtn)
        self.panelLayout.addWidget(self.genSwcMatlabBtn)
        self.panelLayout.addStretch(1)

        # change the text of button
        self.yesButton.setText(self.tr('Open'))
        self.yesButton.setDisabled(True)
        self.yesButton.setVisible(False)
        self.cancelButton.setText(self.tr('Cancel'))

        self.widget.setMinimumWidth(900)

        self.logConsole.textChanged.connect(self._validateUrl)
        self.clearLogBtn.clicked.connect(self._clearLog)

    def _addLog(self, message):
        """ 添加日志信息 """
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.logConsole.appendPlainText(f"[{timestamp}] {message}")
        # 自动滚动到底部
        self.logConsole.verticalScrollBar().setValue(self.logConsole.verticalScrollBar().maximum())

    def _clearLog(self):
        """ 清空日志 """
        self.logConsole.clear()
        self._addLog(" ")

    def _validateUrl(self, text):
        self.yesButton.setEnabled(True)

    def create_menu_actions(self):
        # create actions
        self.createTimeAction = Action(FIF.CALENDAR, self.tr('Create Date'), checkable=True)
        self.shootTimeAction = Action(FIF.CAMERA, self.tr('Shooting Date'), checkable=True)
        self.modifiedTimeAction = Action(FIF.EDIT, self.tr('Modified time'), checkable=True)
        self.nameAction = Action(FIF.FONT, self.tr('Name'), checkable=True)
        self.actionGroup1 = QActionGroup(self)
        self.actionGroup1.addAction(self.createTimeAction)
        self.actionGroup1.addAction(self.shootTimeAction)
        self.actionGroup1.addAction(self.modifiedTimeAction)
        self.actionGroup1.addAction(self.nameAction)

        self.ascendAction = Action(FIF.UP, self.tr('Ascending'), checkable=True)
        self.descendAction = Action(FIF.DOWN, self.tr('Descending'), checkable=True)
        self.actionGroup2 = QActionGroup(self)
        self.actionGroup2.addAction(self.ascendAction)
        self.actionGroup2.addAction(self.descendAction)

        self.shootTimeAction.setChecked(True)
        self.ascendAction.setChecked(True)

    def createCheckableMenu(self, pos=None):
        menu = CheckableMenu(parent=self, indicatorType=MenuIndicatorType.RADIO)

        menu.addActions([
            self.createTimeAction, self.shootTimeAction,
            self.modifiedTimeAction, self.nameAction
        ])
        menu.addSeparator()
        menu.addActions([self.ascendAction, self.descendAction])

        if pos is not None:
            menu.exec(pos, ani=True)

        return menu

    def createCommandBar(self):
        bar = CommandBar(self)
        bar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        bar.addActions([
            Action(FIF.ADD, self.tr('Add')),
            Action(FIF.ROTATE, self.tr('Rotate')),
            Action(FIF.ZOOM_IN, self.tr('Zoom in')),
            Action(FIF.ZOOM_OUT, self.tr('Zoom out')),
        ])
        bar.addSeparator()
        bar.addActions([
            Action(FIF.EDIT, self.tr('Edit'), checkable=True),
            Action(FIF.INFO, self.tr('Info')),
            Action(FIF.DELETE, self.tr('Delete')),
            Action(FIF.SHARE, self.tr('Share'))
        ])

        # add custom widget
        button = TransparentDropDownPushButton(self.tr('Sort'), self, FIF.SCROLL)
        button.setMenu(self.createCheckableMenu())
        button.setFixedHeight(34)
        setFont(button, 12)
        bar.addWidget(button)

        bar.addHiddenActions([
            Action(FIF.SETTING, self.tr('Settings'), shortcut='Ctrl+I'),
        ])
        return bar


class FuncInterface(ScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.view = QWidget(self)

        self.funcInfoCard = AppInfoCard()
        self.basicSettingCard = BasicConfigCard()


        self._initWidget()
        self.__initLayout()
        self._connectSignalToSlot()

    def _initWidget(self):
        self.setObjectName('funcInterface')
        self.view.setObjectName('scrollWidget')
        self.setWidget(self.view)
        self.setAcceptDrops(True)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.__setQss()
        self.resize(780, 800)


    def __initLayout(self):
        self.Layout = QHBoxLayout(self.view)
        self.Layout.setContentsMargins(0, 48, 0, 0)

        self.main_layout = QVBoxLayout()
        self.main_layout.setObjectName('vBoxLayout')
        self.main_layout.setContentsMargins(10, 0, 10, 10)
        self.main_layout.setSpacing(20)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.Layout.addLayout(self.main_layout)
        self.main_layout.addWidget(self.funcInfoCard)
        self.main_layout.addWidget(self.basicSettingCard)

    def __setQss(self):
        """ set style sheet """
        # initialize style sheet


        self.enableTransparentBackground()
        StyleSheet.RTE_INTERFACE.apply(self)

    def showCustomDialog(self):
        w = CustomMessageBox(self.window())
        if w.exec():
            print(w.urlLineEdit.text())

    def _connectSignalToSlot(self):
        self.basicSettingCard.exeButton.clicked.connect(self.showCustomDialog)