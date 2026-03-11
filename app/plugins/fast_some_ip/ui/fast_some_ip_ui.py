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
    ComboBoxSettingCard, InfoBar, InfoBarPosition
)
from qfluentwidgets import (
    FluentIcon as FIF,
)

from app.common.config import cfg
from app.common.icon import UnicodeIcon, Icon


class FastSomeIpToolUI(ExpandSettingCard):
    """FastSomeIp Tool UI class"""

    def __init__(
            self,
            icon: str | QIcon | FluentIconBase = None,
            title: str = None,
            content=None,
            parent=None,
    ):
        if icon is None:
            icon = Icon.SOMEIP_6
        if not title:
            title = self.tr("FastSomeIp Tool")
        if content is None:
            content = self.tr("FastSomeIp Tool for processing SomeIp files")
        super().__init__(icon, title, content, parent)
        self.combox = ComboBox(self)
        self.combox.addItems(["Option 1", "Option 2", "Option 3"])
        selected_index = cfg.get(cfg.fastSomeIpSelectedOption)
        if 0 <= selected_index < self.combox.count():
            self.combox.setCurrentIndex(selected_index)
        self.card.addWidget(self.combox)
        self.__initCards()
        self.__onComboBoxChanged(selected_index)
        self.connectSignals()

    def __initCards(self):
        self.fastSomeIpOutputFolderCard = PushSettingCard(
            self.tr("Choose folder"),
            FIF.FOLDER_ADD,
            self.tr("FastSomeIp Output Directory"),
            cfg.get(cfg.fastSomeIpOutputFolder)
        )
        self.fastSomeIpInputFileCard = PushSettingCard(
            self.tr("Choose file"),
            UnicodeIcon.get_icon_by_name('ic_fluent_document_table_truck_24_regular'),
            self.tr("Input File"),
            cfg.get(cfg.fastSomeIpInputFile)
        )
        self.fastSomeIpExecuteCard = PrimaryPushSettingCard(
            self.tr("Execute"),
            FIF.PLAY,
            self.tr("Execute FastSomeIp Processing"),
            self.tr("Click to start processing")
        )
        self.__addCardsToLayout()

    def __addCardsToLayout(self):
        self.viewLayout.addWidget(self.fastSomeIpInputFileCard)
        self.viewLayout.addWidget(self.fastSomeIpOutputFolderCard)
        self.viewLayout.addWidget(self.fastSomeIpExecuteCard)
        self._adjustViewSize()

    def connectSignals(self):
        self.fastSomeIpOutputFolderCard.clicked.connect(
            lambda: self.__onChooseFolderClicked(cfg.fastSomeIpOutputFolder, self.fastSomeIpOutputFolderCard)
        )
        self.fastSomeIpInputFileCard.clicked.connect(
            lambda: self.__onChooseFileClicked(cfg.fastSomeIpInputFile, self.fastSomeIpInputFileCard)
        )
        self.fastSomeIpExecuteCard.clicked.connect(self.__onExecuteFastSomeIpClicked)
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

    def __onExecuteFastSomeIpClicked(self):
        try:
            message = self.tr("Processing completed!\n")
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
        cfg.set(cfg.fastSomeIpSelectedOption, index)
        if index == 0:
            self.fastSomeIpOutputFolderCard.setVisible(True)
            self.fastSomeIpInputFileCard.setVisible(True)
            self.fastSomeIpExecuteCard.setVisible(True)
            self.fastSomeIpOutputFolderCard.setEnabled(True)
            self.fastSomeIpInputFileCard.setEnabled(True)
            self.fastSomeIpExecuteCard.setEnabled(True)
        elif index == 1:
            self.fastSomeIpOutputFolderCard.setVisible(True)
            self.fastSomeIpInputFileCard.setVisible(True)
            self.fastSomeIpExecuteCard.setVisible(False)
            self.fastSomeIpOutputFolderCard.setEnabled(True)
            self.fastSomeIpInputFileCard.setEnabled(True)
        elif index == 2:
            self.fastSomeIpOutputFolderCard.setVisible(True)
            self.fastSomeIpInputFileCard.setVisible(True)
            self.fastSomeIpExecuteCard.setVisible(True)
            self.fastSomeIpOutputFolderCard.setEnabled(False)
            self.fastSomeIpInputFileCard.setEnabled(False)
            self.fastSomeIpExecuteCard.setEnabled(False)
        self._adjustViewSize()
