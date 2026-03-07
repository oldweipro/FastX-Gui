from loguru import logger
from PySide6.QtCore import Qt, Signal, QUrl, QSize
from PySide6.QtGui import QActionGroup, QIcon, QFont, QColor
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QVBoxLayout,
    QWidget, QFileDialog,
)
from qfluentwidgets import (
    Action,
    CheckableMenu,
    CommandBar,
    MenuIndicatorType,
    MessageBoxBase,
    PlainTextEdit,
    PushButton,
    ScrollArea,
    SubtitleLabel,
    TransparentDropDownPushButton,
    FluentIcon as FIF,
    ExpandSettingCard, FluentIconBase, SwitchButton, IndicatorPosition, CheckBox,
    BodyLabel,
    FluentIcon,
    HyperlinkLabel,
    ImageLabel,
    PrimaryPushButton,
    SimpleCardWidget,
    TitleLabel,
    TransparentToolButton,
    VerticalSeparator,
    setFont,
    CaptionLabel, PillPushButton, GroupHeaderCardWidget, ComboBox, InfoBarIcon, IconWidget,
)

from app.common.config import cfg
from app.common.icon import UnicodeIcon
from app.common.style_sheet import StyleSheet


class StatisticsWidget(QWidget):
    """Statistics widget"""

    def __init__(self, title: str, value: str, parent=None):
        super().__init__(parent=parent)
        self.titleLabel = CaptionLabel(title, self)
        self.valueLabel = BodyLabel(value, self)
        self.vBoxLayout = QVBoxLayout(self)

        self.vBoxLayout.setContentsMargins(16, 0, 16, 0)
        self.vBoxLayout.addWidget(self.valueLabel, 0, Qt.AlignTop)
        self.vBoxLayout.addWidget(self.titleLabel, 0, Qt.AlignBottom)

        setFont(self.valueLabel, 18, QFont.DemiBold)
        self.titleLabel.setObjectName("titleLabel")
        self.valueLabel.setObjectName("valueLabel")

class CompactTagContainer(QWidget):
    """紧凑标签容器"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(5)  # 设置较小的间距，使标签紧凑

        # 添加弹簧，使标签靠左
        self.layout.addStretch(1)

        self.tags = []

    def add_tag(self, text: str) -> PillPushButton:
        """添加标签并返回标签按钮"""
        tag = PillPushButton(text, self)
        tag.setCheckable(False)
        setFont(tag, 12)
        tag.setFixedSize(80, 32)

        self.layout.addWidget(tag)
        self.tags.append(tag)
        return tag

    def add_tags(self, texts: list[str]):
        """批量添加标签"""
        for text in texts:
            self.add_tag(text)

class FastRteHeaderInfoCard(SimpleCardWidget):
    """M3U8DL information card"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setBorderRadius(8)
        self.iconLabel = ImageLabel(QIcon(":/app/images/ico/M3U8DL.ico").pixmap(120, 120), self)

        self.nameLabel = TitleLabel(self.tr("FastRte"), self)
        self.updateButton = PrimaryPushButton(self.tr("Update"), self)
        self.companyLabel = HyperlinkLabel(QUrl("https://github.com/fastxteam/FastX-Gui"), "FastXTeam", self)
        self.versionWidget = StatisticsWidget(self.tr("Version"), "v0.1.0", self)
        self.fileSizeWidget = StatisticsWidget(self.tr("File Size"), "19MB", self)
        self.updateTimeWidget = StatisticsWidget(self.tr("Update Time"), "2026-01-19", self)

        self.descriptionLabel = BodyLabel(
            self.tr(
                "Rte Connecter is an application tool. The current application field is AUTOSAR CP. The adaptation tool ETAS is used to connect RTE wiring between SWCs. It can generate DataType, Interface and Composition Rte wiring from the table content, which greatly improves the development speed."
            ),
            self,
        )

        # 使用紧凑标签容器
        self.tag_container = CompactTagContainer(self)

        self.shareButton = TransparentToolButton(FluentIcon.SHARE, self)

        self.hBoxLayout = QHBoxLayout(self)
        self.vBoxLayout = QVBoxLayout()
        self.topLayout = QHBoxLayout()
        self.statisticsLayout = QHBoxLayout()
        self.bottomLayout = QHBoxLayout()  # 底部布局，包含标签容器和分享按钮

        self.__initWidgets()

    def __initWidgets(self):
        self.iconLabel.setBorderRadius(8, 8, 8, 8)
        self.iconLabel.scaledToWidth(120)

        self.updateButton.setFixedWidth(160)

        self.descriptionLabel.setWordWrap(True)
        # self.shareButton.clicked.connect(lambda: openUrl(DEPLOY_URL))

        self.shareButton.setFixedSize(32, 32)
        self.shareButton.setIconSize(QSize(14, 14))

        self.nameLabel.setObjectName("nameLabel")
        self.descriptionLabel.setObjectName("descriptionLabel")

        # 初始化标签
        self.tag_container.add_tags(["FUNC", "IPC", "SRP"])

        self.initLayout()

    def initLayout(self):
        self.hBoxLayout.setSpacing(30)
        self.hBoxLayout.setContentsMargins(34, 24, 24, 24)
        self.hBoxLayout.addWidget(self.iconLabel)
        self.hBoxLayout.addLayout(self.vBoxLayout)

        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setSpacing(0)

        # name label and install button
        self.vBoxLayout.addLayout(self.topLayout)
        self.topLayout.setContentsMargins(0, 0, 0, 0)
        self.topLayout.addWidget(self.nameLabel)
        self.topLayout.addWidget(self.updateButton, 0, Qt.AlignRight)

        # company label
        self.vBoxLayout.addSpacing(3)
        self.vBoxLayout.addWidget(self.companyLabel)

        # statistics widgets
        self.vBoxLayout.addSpacing(20)
        self.vBoxLayout.addLayout(self.statisticsLayout)
        self.statisticsLayout.setContentsMargins(0, 0, 0, 0)
        self.statisticsLayout.setSpacing(10)
        self.statisticsLayout.addWidget(self.versionWidget)
        self.statisticsLayout.addWidget(VerticalSeparator())
        self.statisticsLayout.addWidget(self.fileSizeWidget)
        self.statisticsLayout.addWidget(VerticalSeparator())
        self.statisticsLayout.addWidget(self.updateTimeWidget)
        self.statisticsLayout.setAlignment(Qt.AlignLeft)

        # description label
        self.vBoxLayout.addSpacing(20)
        self.vBoxLayout.addWidget(self.descriptionLabel)

        # 底部布局：标签容器 + 分享按钮
        self.vBoxLayout.addSpacing(12)
        self.bottomLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.addLayout(self.bottomLayout)
        # 添加标签容器
        self.bottomLayout.addWidget(self.tag_container)
        # 添加弹簧使分享按钮靠右
        self.bottomLayout.addStretch(1)
        # 分享按钮靠右
        self.bottomLayout.addWidget(self.shareButton, 0, Qt.AlignRight)

    def setVersion(self, version: str):
        text = version or "0.1.0"
        self.versionWidget.valueLabel.setText(text)
        self.versionWidget.valueLabel.setTextColor(QColor(0, 0, 0), QColor(255, 255, 255))

class FastRteContentsSWCsCard(ExpandSettingCard):
    """Setting card for auto plot with switch and expandable options"""

    switchChanged = Signal(bool)
    optionsChanged = Signal(dict)

    def __init__(
        self,
        icon: str | QIcon | FluentIconBase,
        title,
        content=None,
        parent=None,
    ):
        super().__init__(icon, title, content, parent)
        # Switch button
        self.switchButton = SwitchButton("关", self, IndicatorPosition.RIGHT)
        # Add switch button to card layout using addWidget method
        self.card.addWidget(self.switchButton)
        # Configuration options
        self._init_options()
        # Connect signals
        self.switchButton.checkedChanged.connect(self.__onSwitchChanged)

    def _init_options(self):
        """Initialize configuration options in the expandable view"""
        # Create widgets container
        self.viewLayout.setSpacing(19)
        self.viewLayout.setContentsMargins(5, 18, 5, 18)

        # 添加选择Combox
        # 创建主widget
        self.comboxCard = QWidget(self)
        self.comboxCard.setObjectName("widget")

        # 主水平布局
        self.horizontalLayout = QHBoxLayout(self.comboxCard)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        # 用于存储所有CheckBox的列表
        self.checkboxes = []
        # 创建6列，每列8个CheckBox（总共48个）
        for col in range(6):  # 6列
            verticalLayout = QVBoxLayout()
            verticalLayout.setObjectName(f"verticalLayout_col_{col}")
            for row in range(8):  # 每列8个
                checkbox_num = col * 8 + row  # 从0开始编号
                checkbox = CheckBox(self.comboxCard)
                checkbox.setText("")
                checkbox.setChecked(False)
                checkbox.setObjectName(f"CheckBox_{checkbox_num}")
                # 添加到垂直布局
                verticalLayout.addWidget(checkbox)
                # 存储到列表中以便后续访问
                self.checkboxes.append(checkbox)
            # 添加到水平布局
            self.horizontalLayout.addLayout(verticalLayout)
        self.viewLayout.addWidget(self.comboxCard)

        # Adjust view size
        self._adjustViewSize()

    def __onSwitchChanged(self, isChecked: bool):
        """Switch button checked state changed slot"""
        self.setValue(isChecked)
        self.switchChanged.emit(isChecked)

    def setValue(self, isChecked: bool):
        """Set switch button state"""
        self.switchButton.setChecked(isChecked)
        self.switchButton.setText("开" if isChecked else "关")

    def getSwitchState(self) -> bool:
        """Get current switch state"""
        return self.switchButton.isChecked()

class CustomMessageBox(MessageBoxBase):
    """Custom message box"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel(self.tr("Operation Console"), self)

        self.automaticPlotCard = FastRteContentsSWCsCard(
            icon=FIF.CHECKBOX,
            title=self.tr("Select SWCs"),
            content="Select SWCs of which should be generate by tools",
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

        self.card.setObjectName("card")
        self.logPanel.setObjectName("logPanel")
        self.controlPanel.setObjectName("controlPanel")

        self.hBoxLayout = QHBoxLayout(self.card)
        self.logLayout = QHBoxLayout(self.logPanel)
        self.panelLayout = QVBoxLayout(self.controlPanel)

        self.logLayout.setContentsMargins(1, 1, 1, 1)
        self.panelLayout.setSpacing(8)
        self.panelLayout.setContentsMargins(14, 16, 14, 14)
        self.panelLayout.setAlignment(Qt.AlignTop)

        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.createCommandBar())  # 添加菜单栏
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
        self.yesButton.setText(self.tr("Open"))
        self.yesButton.setDisabled(True)
        self.yesButton.setVisible(False)
        self.cancelButton.setText(self.tr("Cancel"))

        self.widget.setMinimumWidth(900)

        self.logConsole.textChanged.connect(self._validateUrl)
        self.clearLogBtn.clicked.connect(self._clearLog)

    def _addLog(self, message):
        """添加日志信息"""
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.logConsole.appendPlainText(f"[{timestamp}] {message}")
        # 自动滚动到底部
        self.logConsole.verticalScrollBar().setValue(self.logConsole.verticalScrollBar().maximum())

    def _clearLog(self):
        """清空日志"""
        self.logConsole.clear()
        self._addLog(" ")

    def _validateUrl(self, text):
        self.yesButton.setEnabled(True)

    def create_menu_actions(self):
        # create actions
        self.createTimeAction = Action(FIF.CALENDAR, self.tr("Create Date"), checkable=True)
        self.shootTimeAction = Action(FIF.CAMERA, self.tr("Shooting Date"), checkable=True)
        self.modifiedTimeAction = Action(FIF.EDIT, self.tr("Modified time"), checkable=True)
        self.nameAction = Action(FIF.FONT, self.tr("Name"), checkable=True)
        self.actionGroup1 = QActionGroup(self)
        self.actionGroup1.addAction(self.createTimeAction)
        self.actionGroup1.addAction(self.shootTimeAction)
        self.actionGroup1.addAction(self.modifiedTimeAction)
        self.actionGroup1.addAction(self.nameAction)

        self.ascendAction = Action(FIF.UP, self.tr("Ascending"), checkable=True)
        self.descendAction = Action(FIF.DOWN, self.tr("Descending"), checkable=True)
        self.actionGroup2 = QActionGroup(self)
        self.actionGroup2.addAction(self.ascendAction)
        self.actionGroup2.addAction(self.descendAction)

        self.shootTimeAction.setChecked(True)
        self.ascendAction.setChecked(True)

    def createCheckableMenu(self, pos=None):
        menu = CheckableMenu(parent=self, indicatorType=MenuIndicatorType.RADIO)

        menu.addActions(
            [
                self.createTimeAction,
                self.shootTimeAction,
                self.modifiedTimeAction,
                self.nameAction,
            ]
        )
        menu.addSeparator()
        menu.addActions([self.ascendAction, self.descendAction])

        if pos is not None:
            menu.exec(pos, ani=True)

        return menu

    def createCommandBar(self):
        bar = CommandBar(self)
        bar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        bar.addActions(
            [
                Action(FIF.ADD, self.tr("Add")),
                Action(FIF.ROTATE, self.tr("Rotate")),
                Action(FIF.ZOOM_IN, self.tr("Zoom in")),
                Action(FIF.ZOOM_OUT, self.tr("Zoom out")),
            ]
        )
        bar.addSeparator()
        bar.addActions(
            [
                Action(FIF.EDIT, self.tr("Edit"), checkable=True),
                Action(FIF.INFO, self.tr("Info")),
                Action(FIF.DELETE, self.tr("Delete")),
                Action(FIF.SHARE, self.tr("Share")),
            ]
        )

        # add custom widget
        button = TransparentDropDownPushButton(self.tr("Sort"), self, FIF.SCROLL)
        button.setMenu(self.createCheckableMenu())
        button.setFixedHeight(34)
        setFont(button, 12)
        bar.addWidget(button)

        bar.addHiddenActions(
            [
                Action(FIF.SETTING, self.tr("Settings"), shortcut="Ctrl+I"),
            ]
        )
        return bar

class BasicConfigCard(GroupHeaderCardWidget):
    """Basic config card"""

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
        self.hintLabel = BodyLabel(self.tr("Click the execute button to start running") + " 👉")
        self.exeButton = PrimaryPushButton(
            self.tr("Execute"),
            self,
            UnicodeIcon.get_icon_by_name("ic_fluent_panel_bottom_20_regular"),
        )

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
            icon=UnicodeIcon.get_icon_by_name("ic_fluent_multiplier_2x_32_regular"),
            title=self.tr("Change Tools"),
            content=self.tr("Select the Tools Engine to Generator"),
            widget=self.toolsEngineComboBox,
        )
        self.chooseMappingTableGroup = self.addGroup(
            icon=UnicodeIcon.get_icon_by_name("ic_fluent_document_table_24_regular"),
            title=self.tr("Mapping Table Path"),
            content=cfg.get(cfg.fastRteMappingTableFile),
            widget=self.chooseMappingTableButton,
        )
        self.chooseDataTypGroup = self.addGroup(
            icon=UnicodeIcon.get_icon_by_name("ic_fluent_document_contract_16_regular"),
            title=self.tr("DataType Arxml Path"),
            content=cfg.get(cfg.fastRteDataTypeFile),
            widget=self.chooseDataTypeButton,
        )
        self.chooseInterfaceGroup = self.addGroup(
            icon=UnicodeIcon.get_icon_by_name("ic_fluent_document_contract_16_regular"),
            title=self.tr("Interface Arxml Path"),
            content=cfg.get(cfg.fastRteInterfaceFile),
            widget=self.chooseInterfaceButton,
        )
        self.outputFolderGroup = self.addGroup(
            icon=UnicodeIcon.get_icon_by_name("ic_fluent_folder_open_24_regular"),
            title=self.tr("Output Folder"),
            content=cfg.get(cfg.fastRteOutputFolder),
            widget=self.outputFolderButton,
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
        if not path or cfg.get(cfg.fastRteMappingTableFile) == path:
            return
        cfg.set(cfg.fastRteMappingTableFile, path)
        self.chooseMappingTableGroup.setContent(path)

    def _onChooseDataTypeButtonClicked(self):
        path, _ = QFileDialog.getOpenFileName(self, self.tr("Choose"))
        if not path or cfg.get(cfg.fastRteDataTypeFile) == path:
            return
        cfg.set(cfg.fastRteDataTypeFile, path)
        self.chooseDataTypGroup.setContent(path)

    def _onChooseInterfaceButtonClicked(self):
        path, _ = QFileDialog.getOpenFileName(self, self.tr("Choose"))
        if not path or cfg.get(cfg.fastRteInterfaceFile) == path:
            return
        cfg.set(cfg.fastRteInterfaceFile, path)
        self.chooseInterfaceGroup.setContent(path)

    def _chooseOutputFolder(self):
        folder = QFileDialog.getExistingDirectory(self, self.tr("Choose folder"), self.outputFolderGroup.content())

        if folder:
            folder = folder.replace("\\", "/")
            cfg.set(cfg.fastRteOutputFolder, folder)
            self.outputFolderGroup.setContent(folder)

    def _onToolsEngineChanged(self):
        icons = [
            UnicodeIcon.get_icon_by_name("ic_fluent_multiplier_2x_32_regular"),
            UnicodeIcon.get_icon_by_name("ic_fluent_dual_screen_span_20_regular"),
            UnicodeIcon.get_icon_by_name("ic_fluent_diamond_link_24_regular"),
        ]
        self.toolsEngineGroup.setIcon(icons[self.toolsEngineComboBox.currentIndex()].icon())
        cfg.set(cfg.fastRteToolsEngine, self.toolsEngineComboBox.currentText())

    def _connectSignalToSlot(self):
        self.toolsEngineComboBox.currentIndexChanged.connect(self._onToolsEngineChanged)
        self.outputFolderButton.clicked.connect(self._chooseOutputFolder)
        self.chooseMappingTableButton.clicked.connect(self._onChooseMappingTableButtonClicked)
        self.chooseDataTypeButton.clicked.connect(self._onChooseDataTypeButtonClicked)
        self.chooseInterfaceButton.clicked.connect(self._onChooseInterfaceButtonClicked)


class FuncInterface(ScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.view = QWidget(self)
        self.funcInfoCard = FastRteHeaderInfoCard()
        self.basicSettingCard = BasicConfigCard()

        self._initWidget()
        self.__initLayout()
        self._connectSignalToSlot()

    def _initWidget(self):
        self.setViewportMargins(0, 48, 0, 20)
        self.setObjectName("funcInterface")
        self.view.setObjectName("scrollWidget")
        self.setWidget(self.view)
        self.setAcceptDrops(True)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.__setQss()
        self.resize(780, 800)

    def __initLayout(self):
        self.Layout = QHBoxLayout(self.view)
        self.Layout.setContentsMargins(0, 0, 0, 0)

        self.main_layout = QVBoxLayout()
        self.main_layout.setObjectName("vBoxLayout")
        self.main_layout.setContentsMargins(10, 0, 10, 10)
        self.main_layout.setSpacing(20)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.Layout.addLayout(self.main_layout)
        self.main_layout.addWidget(self.funcInfoCard)
        self.main_layout.addWidget(self.basicSettingCard)

    def __setQss(self):
        """set style sheet"""
        # initialize style sheet

        self.enableTransparentBackground()
        StyleSheet.RTE_INTERFACE.apply(self)

    def showCustomDialog(self):
        w = CustomMessageBox(self.window())
        if w.exec():
            logger.info(w.urlLineEdit.text())

    def _connectSignalToSlot(self):
        self.basicSettingCard.exeButton.clicked.connect(self.showCustomDialog)
