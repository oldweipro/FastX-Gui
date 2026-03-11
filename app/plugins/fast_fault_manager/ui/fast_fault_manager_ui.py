from PySide6.QtCore import QModelIndex, QPoint
from PySide6.QtGui import QIcon, Qt
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QVBoxLayout, QWidget, \
    QTableWidget, QTableWidgetItem, QHeaderView, QItemDelegate, QComboBox, QStyledItemDelegate, QMenu, QLineEdit, \
    QAbstractItemView
from qfluentwidgets import (
    ExpandSettingCard,
    PrimaryPushSettingCard,
    PushSettingCard,
    SwitchSettingCard, ScrollArea, FluentIconBase, ComboBox, TableWidget, IconWidget, FluentIcon, SearchLineEdit,
    StrongBodyLabel, Dialog, LineEdit, PrimaryPushButton, PushButton, MessageBoxBase, BodyLabel, SpinBox, SubtitleLabel,
    InfoBar, InfoBarPosition
)
from qfluentwidgets import (
    FluentIcon as FIF,
)

from app.common.config import cfg
from app.common.icon import UnicodeIcon, Icon


class FastFaultManagerToolUI(ExpandSettingCard):
    """FastFaultManager Tool UI class"""

    def __init__(
            self,
            icon: str | QIcon | FluentIconBase = None,
            title: str = None,
            content=None,
            parent=None,
    ):
        if icon is None:
            icon = Icon.FIM
        if not title:
            title = self.tr("FastFaultManager Tool")
        if content is None:
            content = self.tr("FastFaultManager Tool for fault degradation processing")
        super().__init__(icon, title, content, parent)
        self.combox = ComboBox(self)
        self.combox.addItems(["Option 1", "Option 2", "Option 3"])
        selected_index = cfg.get(cfg.fastFaultManagerSelectedOption)
        if 0 <= selected_index < self.combox.count():
            self.combox.setCurrentIndex(selected_index)
        self.card.addWidget(self.combox)
        self.__initCards()
        self.__onComboBoxChanged(selected_index)
        self.connectSignals()

    def __initCards(self):
        self.fastFaultManagerOutputFolderCard = PushSettingCard(
            self.tr("Choose folder"),
            FIF.FOLDER_ADD,
            self.tr("FastFaultManager Output Directory"),
            cfg.get(cfg.fastFaultManagerOutputFolder)
        )
        self.fastFaultManagerInputFileCard = PushSettingCard(
            self.tr("Choose file"),
            UnicodeIcon.get_icon_by_name('ic_fluent_document_table_truck_24_regular'),
            self.tr("Input File"),
            cfg.get(cfg.fastFaultManagerInputFile)
        )
        self.fastFaultManagerExecuteCard = PrimaryPushSettingCard(
            self.tr("Execute"),
            FIF.PLAY,
            self.tr("Execute FastFaultManager Processing"),
            self.tr("Click to start fault degradation processing")
        )
        self.__addCardsToLayout()

    def __addCardsToLayout(self):
        self.viewLayout.addWidget(self.fastFaultManagerInputFileCard)
        self.viewLayout.addWidget(self.fastFaultManagerOutputFolderCard)
        self.viewLayout.addWidget(self.fastFaultManagerExecuteCard)
        self._adjustViewSize()

    def connectSignals(self):
        self.fastFaultManagerOutputFolderCard.clicked.connect(
            lambda: self.__onChooseFolderClicked(cfg.fastFaultManagerOutputFolder, self.fastFaultManagerOutputFolderCard)
        )
        self.fastFaultManagerInputFileCard.clicked.connect(
            lambda: self.__onChooseFileClicked(cfg.fastFaultManagerInputFile, self.fastFaultManagerInputFileCard)
        )
        self.fastFaultManagerExecuteCard.clicked.connect(self.__onExecuteFastFaultManagerClicked)
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

    def __onExecuteFastFaultManagerClicked(self):
        try:
            message = self.tr("Fault degradation processing completed!\n")
            InfoBar.success(
                self.tr("Success"),
                message,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
        except Exception as e:
            InfoBar.error(
                self.tr("Error"),
                self.tr(f"Processing failed: {str(e)}"),
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )

    def __onComboBoxChanged(self, index):
        cfg.set(cfg.fastFaultManagerSelectedOption, index)
        if index == 0:
            self.fastFaultManagerOutputFolderCard.setVisible(True)
            self.fastFaultManagerInputFileCard.setVisible(True)
            self.fastFaultManagerExecuteCard.setVisible(True)
            self.fastFaultManagerOutputFolderCard.setEnabled(True)
            self.fastFaultManagerInputFileCard.setEnabled(True)
            self.fastFaultManagerExecuteCard.setEnabled(True)
        elif index == 1:
            self.fastFaultManagerOutputFolderCard.setVisible(True)
            self.fastFaultManagerInputFileCard.setVisible(True)
            self.fastFaultManagerExecuteCard.setVisible(False)
            self.fastFaultManagerOutputFolderCard.setEnabled(True)
            self.fastFaultManagerInputFileCard.setEnabled(True)
        elif index == 2:
            self.fastFaultManagerOutputFolderCard.setVisible(True)
            self.fastFaultManagerInputFileCard.setVisible(True)
            self.fastFaultManagerExecuteCard.setVisible(True)
            self.fastFaultManagerOutputFolderCard.setEnabled(False)
            self.fastFaultManagerInputFileCard.setEnabled(False)
            self.fastFaultManagerExecuteCard.setEnabled(False)
        self._adjustViewSize()
