from PySide6.QtCore import QModelIndex, QPoint
from PySide6.QtGui import QIcon, Qt
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QInputDialog, QMessageBox, QVBoxLayout, QWidget, \
    QTableWidget, QTableWidgetItem, QHeaderView, QItemDelegate, QComboBox, QStyledItemDelegate, QMenu, QLineEdit, \
    QAbstractItemView
from qfluentwidgets import (
    ExpandSettingCard,
    PrimaryPushSettingCard,
    PushSettingCard,
    SwitchSettingCard, ScrollArea, FluentIconBase, ComboBox, TableWidget, IconWidget, FluentIcon, SearchLineEdit,
    StrongBodyLabel, Dialog, LineEdit, PrimaryPushButton, PushButton, MessageBoxBase, BodyLabel, SpinBox, SubtitleLabel,
    ComboBoxSettingCard
)
from qfluentwidgets import (
    FluentIcon as FIF,
)

from app.common.config import cfg
from app.common.icon import UnicodeIcon, Icon
from app.tools.core.rm_comments_core import RmCommentsCore


class ComGroupMappingToolUI(ExpandSettingCard):
    """ComGroupMapping Tool UI class"""

    def __init__(
            self,
            icon: str | QIcon | FluentIconBase = None,
            title: str = None,
            content=None,
            parent=None,
    ):
        # 如果 icon 为 None，可以设置一个默认图标
        if icon is None:
            icon = Icon.COM
        # 如果 title 为空字符串，设置默认标题
        if not title:
            title = self.tr("ComGroupMapping Tool")
        # 如果 content 为空字符串，设置默认标题
        if content is None:
            content = self.tr("ComGroupMapping Tool for processing Com files")
        super().__init__(icon, title, content, parent)
        self.core = RmCommentsCore()
        self.combox = ComboBox(self)
        self.combox.addItems(["Option 1", "Option 2", "Option 3"])
        # Load saved option from config
        selected_index = cfg.get(cfg.comGroupMappingSelectedOption)
        if 0 <= selected_index < self.combox.count():
            self.combox.setCurrentIndex(selected_index)
        self.card.addWidget(self.combox)
        self.__initCards()
        # Apply initial card states based on saved option
        self.__onComboBoxChanged(selected_index)
        self.connectSignals()

    def __initCards(self):
        """
        初始化卡片
        """

        # 文件夹选择卡片
        self.comGroupMappingOutputFolderCard = PushSettingCard(
            self.tr("Choose folder"),
            FIF.FOLDER_ADD,
            self.tr("ComGroupMapping Output Directory"),
            cfg.get(cfg.comGroupMappingOutputFolder)
        )

        # 文件选择卡片
        self.comGroupMappingInputFileCard = PushSettingCard(
            self.tr("Choose file"),
            UnicodeIcon.get_icon_by_name('ic_fluent_document_table_truck_24_regular'),
            self.tr("Input File"),
            cfg.get(cfg.comGroupMappingInputFile)
        )

        # Execute button
        self.comGroupMappingExecuteCard = PrimaryPushSettingCard(
            self.tr("Execute"),
            FIF.PLAY,
            self.tr("Execute ComGroupMapping Processing"),
            self.tr("Click to start processing")
        )

        # 添加卡片到布局
        self.__addCardsToLayout()

    def __addCardsToLayout(self):
        """
        添加卡片到布局
        """
        self.viewLayout.addWidget(self.comGroupMappingInputFileCard)
        self.viewLayout.addWidget(self.comGroupMappingOutputFolderCard)
        self.viewLayout.addWidget(self.comGroupMappingExecuteCard)

        self._adjustViewSize()

    def connectSignals(self):
        """
        连接信号
        """
        # 按钮 | 选择文件夹
        self.comGroupMappingOutputFolderCard.clicked.connect(
            lambda: self.__onChooseFolderClicked(cfg.comGroupMappingOutputFolder, self.comGroupMappingOutputFolderCard)
        )

        # 按钮 | 选择文件
        self.comGroupMappingInputFileCard.clicked.connect(
            lambda: self.__onChooseFileClicked(cfg.comGroupMappingInputFile, self.comGroupMappingInputFileCard)
        )

        # Execute button connection
        self.comGroupMappingExecuteCard.clicked.connect(self.__onExecuteComGroupMappingClicked)

        # ComboBox signal for controlling cards
        self.combox.currentIndexChanged.connect(self.__onComboBoxChanged)

    def __onChooseFolderClicked(self, config_item, card):
        """
        通用文件夹选择方法

        Args:
            config_item: 配置项
            card: 卡片对象
        """
        folder = QFileDialog.getExistingDirectory(self, self.tr("Choose folder"), cfg.get(config_item))
        if not folder or cfg.get(config_item) == folder:
            return
        cfg.set(config_item, folder)
        card.setContent(folder)

    def __onChooseFileClicked(self, config_item, card):
        """
        通用文件选择方法

        Args:
            config_item: 配置项
            card: 卡片对象
        """
        file, _ = QFileDialog.getOpenFileName(self, self.tr("Choose file"), cfg.get(config_item), "Excel Files (*.xlsx);;ARXML Files (*.arxml)")
        if not file or cfg.get(config_item) == file:
            return
        cfg.set(config_item, file)
        card.setContent(file)

    def __onSetValueClicked(self, config_item, card, title):
        """
        通用值设置方法

        Args:
            config_item: 配置项
            card: 卡片对象
            title: 对话框标题
        """
        current_value = cfg.get(config_item)
        value, ok = QInputDialog.getText(self, title, title, text=current_value)
        if ok and value != current_value:
            cfg.set(config_item, value)
            card.setContent(value)

    def __onExecuteComGroupMappingClicked(self):
        """
        执行ComGroupMapping处理
        """
        try:
            # 显示结果
            message = self.tr("Processing completed!\n")
            QMessageBox.information(self, self.tr("Success"), message)
        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"), self.tr(f"Processing failed: {str(e)}"))

    def __onComboBoxChanged(self, index):
        """
        处理ComboBox选择变化，控制卡片的可见性和启用状态

        Args:
            index: 选中项的索引
        """
        # Save selected option to config
        cfg.set(cfg.comGroupMappingSelectedOption, index)

        if index == 0:  # Option 1
            # 显示所有卡片并启用
            self.comGroupMappingOutputFolderCard.setVisible(True)
            self.comGroupMappingInputFileCard.setVisible(True)
            self.comGroupMappingExecuteCard.setVisible(True)
            self.comGroupMappingOutputFolderCard.setEnabled(True)
            self.comGroupMappingInputFileCard.setEnabled(True)
            self.comGroupMappingExecuteCard.setEnabled(True)
        elif index == 1:  # Option 2
            # 只显示输入文件夹卡片，禁用执行按钮
            self.comGroupMappingOutputFolderCard.setVisible(True)
            self.comGroupMappingInputFileCard.setVisible(True)
            self.comGroupMappingExecuteCard.setVisible(False)
            self.comGroupMappingOutputFolderCard.setEnabled(True)
            self.comGroupMappingInputFileCard.setEnabled(True)
        elif index == 2:  # Option 3
            # 显示所有卡片但禁用
            self.comGroupMappingOutputFolderCard.setVisible(True)
            self.comGroupMappingInputFileCard.setVisible(True)
            self.comGroupMappingExecuteCard.setVisible(True)
            self.comGroupMappingOutputFolderCard.setEnabled(False)
            self.comGroupMappingInputFileCard.setEnabled(False)
            self.comGroupMappingExecuteCard.setEnabled(False)

        # 调整布局大小
        self._adjustViewSize()