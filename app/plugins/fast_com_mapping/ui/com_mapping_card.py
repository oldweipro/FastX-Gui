from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFileDialog, QMessageBox
from qfluentwidgets import (
    ExpandSettingCard, PrimaryPushSettingCard, PushSettingCard, ComboBox, FluentIconBase
)
from qfluentwidgets import FluentIcon as FIF

from app.common.config import cfg
from app.common.icon import UnicodeIcon, Icon


class FastComMappingCard(ExpandSettingCard):
    """Fast COM Mapping UI Card"""

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
            title = self.tr("COM Mapping Tool")
        if content is None:
            content = self.tr("COM Mapping Tool for processing Com files")
        super().__init__(icon, title, content, parent)
        self.combox = ComboBox(self)
        self.combox.addItems(["Option 1", "Option 2", "Option 3"])
        selected_index = cfg.get(cfg.comGroupMappingSelectedOption)
        if 0 <= selected_index < self.combox.count():
            self.combox.setCurrentIndex(selected_index)
        self.card.addWidget(self.combox)
        self.__init_cards()
        self.__on_combo_box_changed(selected_index)
        self.__connect_signals()

    def __init_cards(self):
        self.output_folder_card = PushSettingCard(
            self.tr("Choose folder"), FIF.FOLDER_ADD,
            self.tr("COM Mapping Output Directory"), cfg.get(cfg.comGroupMappingOutputFolder)
        )
        self.input_file_card = PushSettingCard(
            self.tr("Choose file"),
            UnicodeIcon.get_icon_by_name('ic_fluent_document_table_truck_24_regular'),
            self.tr("Input File"), cfg.get(cfg.comGroupMappingInputFile)
        )
        self.execute_card = PrimaryPushSettingCard(
            self.tr("Execute"), FIF.PLAY,
            self.tr("Execute COM Mapping Processing"),
            self.tr("Click to start processing")
        )
        self.__add_cards_to_layout()

    def __add_cards_to_layout(self):
        self.viewLayout.addWidget(self.input_file_card)
        self.viewLayout.addWidget(self.output_folder_card)
        self.viewLayout.addWidget(self.execute_card)
        self._adjustViewSize()

    def __connect_signals(self):
        self.output_folder_card.clicked.connect(
            lambda: self.__on_choose_folder(cfg.comGroupMappingOutputFolder, self.output_folder_card)
        )
        self.input_file_card.clicked.connect(
            lambda: self.__on_choose_file(cfg.comGroupMappingInputFile, self.input_file_card)
        )
        self.execute_card.clicked.connect(self.__on_execute)
        self.combox.currentIndexChanged.connect(self.__on_combo_box_changed)

    def __on_choose_folder(self, config_item, card):
        folder = QFileDialog.getExistingDirectory(self, self.tr("Choose folder"), cfg.get(config_item))
        if not folder or cfg.get(config_item) == folder:
            return
        cfg.set(config_item, folder)
        card.setContent(folder)

    def __on_choose_file(self, config_item, card):
        file, _ = QFileDialog.getOpenFileName(
            self, self.tr("Choose file"), cfg.get(config_item),
            "Excel Files (*.xlsx);;ARXML Files (*.arxml)"
        )
        if not file or cfg.get(config_item) == file:
            return
        cfg.set(config_item, file)
        card.setContent(file)

    def __on_execute(self):
        try:
            message = self.tr("Processing completed!\n")
            QMessageBox.information(self, self.tr("Success"), message)
        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"), self.tr(f"Processing failed: {str(e)}"))

    def __on_combo_box_changed(self, index):
        cfg.set(cfg.comGroupMappingSelectedOption, index)
        if index == 0:
            self.output_folder_card.setVisible(True)
            self.input_file_card.setVisible(True)
            self.execute_card.setVisible(True)
            self.output_folder_card.setEnabled(True)
            self.input_file_card.setEnabled(True)
            self.execute_card.setEnabled(True)
        elif index == 1:
            self.output_folder_card.setVisible(True)
            self.input_file_card.setVisible(True)
            self.execute_card.setVisible(False)
            self.output_folder_card.setEnabled(True)
            self.input_file_card.setEnabled(True)
        elif index == 2:
            self.output_folder_card.setVisible(True)
            self.input_file_card.setVisible(True)
            self.execute_card.setVisible(True)
            self.output_folder_card.setEnabled(False)
            self.input_file_card.setEnabled(False)
            self.execute_card.setEnabled(False)
        self._adjustViewSize()
