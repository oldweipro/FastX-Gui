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


class ComGroupMappingToolUI(ExpandSettingCard):
    """ComGroupMapping Tool UI class"""

    def __init__(
            self,
            icon: str | QIcon | FluentIconBase = None,
            title: str = None,
            content=None,
            parent=None,
    ):
        if icon is None:
            icon = Icon.COM
        if not title:
            title = self.tr("ComGroupMapping Tool")
        if content is None:
            content = self.tr("ComGroupMapping Tool for processing Com files")
        super().__init__(icon, title, content, parent)
        self.combox = ComboBox(self)
        self.combox.addItems(["Option 1", "Option 2", "Option 3"])
        selected_index = cfg.get(cfg.comGroupMappingSelectedOption)
        if 0 <= selected_index < self.combox.count():
            self.combox.setCurrentIndex(selected_index)
        self.card.addWidget(self.combox)
        self.__initCards()
        self.__onComboBoxChanged(selected_index)
        self.connectSignals()

    def __initCards(self):
        self.comGroupMappingOutputFolderCard = PushSettingCard(
            self.tr("Choose folder"),
            FIF.FOLDER_ADD,
            self.tr("ComGroupMapping Output Directory"),
            cfg.get(cfg.comGroupMappingOutputFolder)
        )
        self.comGroupMappingInputFileCard = PushSettingCard(
            self.tr("Choose file"),
            UnicodeIcon.get_icon_by_name('ic_fluent_document_table_truck_24_regular'),
            self.tr("Input File"),
            cfg.get(cfg.comGroupMappingInputFile)
        )
        self.comGroupMappingExecuteCard = PrimaryPushSettingCard(
            self.tr("Execute"),
            FIF.PLAY,
            self.tr("Execute ComGroupMapping Processing"),
            self.tr("Click to start processing")
        )
        self.__addCardsToLayout()

    def __addCardsToLayout(self):
        self.viewLayout.addWidget(self.comGroupMappingInputFileCard)
        self.viewLayout.addWidget(self.comGroupMappingOutputFolderCard)
        self.viewLayout.addWidget(self.comGroupMappingExecuteCard)
        self._adjustViewSize()

    def connectSignals(self):
        self.comGroupMappingOutputFolderCard.clicked.connect(
            lambda: self.__onChooseFolderClicked(cfg.comGroupMappingOutputFolder, self.comGroupMappingOutputFolderCard)
        )
        self.comGroupMappingInputFileCard.clicked.connect(
            lambda: self.__onChooseFileClicked(cfg.comGroupMappingInputFile, self.comGroupMappingInputFileCard)
        )
        self.comGroupMappingExecuteCard.clicked.connect(self.__onExecuteComGroupMappingClicked)
        self.combox.currentIndexChanged.connect(self.__onComboBoxChanged)

    def __onChooseFolderClicked(self, config_item, card):
        folder = QFileDialog.getExistingDirectory(self, self.tr("Choose folder"), cfg.get(config_item))
        if not folder or cfg.get(config_item) == folder:
            return
        cfg.set(config_item, folder)
        card.setContent(folder)

    def __onChooseFileClicked(self, config_item, card):
        file, _ = QFileDialog.getOpenFileName(self, self.tr("Choose file"), cfg.get(config_item), "Excel Files (*.xlsx);;ARXML Files (*.arxml)")
        if not file or cfg.get(config_item) == file:
            return
        cfg.set(config_item, file)
        card.setContent(file)

    def __onExecuteComGroupMappingClicked(self):
        try:
            message = self.tr("Processing completed!\n")
            QMessageBox.information(self, self.tr("Success"), message)
        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"), self.tr(f"Processing failed: {str(e)}"))

    def __onComboBoxChanged(self, index):
        cfg.set(cfg.comGroupMappingSelectedOption, index)
        if index == 0:
            self.comGroupMappingOutputFolderCard.setVisible(True)
            self.comGroupMappingInputFileCard.setVisible(True)
            self.comGroupMappingExecuteCard.setVisible(True)
            self.comGroupMappingOutputFolderCard.setEnabled(True)
            self.comGroupMappingInputFileCard.setEnabled(True)
            self.comGroupMappingExecuteCard.setEnabled(True)
        elif index == 1:
            self.comGroupMappingOutputFolderCard.setVisible(True)
            self.comGroupMappingInputFileCard.setVisible(True)
            self.comGroupMappingExecuteCard.setVisible(False)
            self.comGroupMappingOutputFolderCard.setEnabled(True)
            self.comGroupMappingInputFileCard.setEnabled(True)
        elif index == 2:
            self.comGroupMappingOutputFolderCard.setVisible(True)
            self.comGroupMappingInputFileCard.setVisible(True)
            self.comGroupMappingExecuteCard.setVisible(True)
            self.comGroupMappingOutputFolderCard.setEnabled(False)
            self.comGroupMappingInputFileCard.setEnabled(False)
            self.comGroupMappingExecuteCard.setEnabled(False)
        self._adjustViewSize()
