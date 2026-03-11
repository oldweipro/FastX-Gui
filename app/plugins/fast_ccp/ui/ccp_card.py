"""Fast CCP UI Card"""
from typing import Dict, Any, Optional
from PySide6.QtWidgets import QWidget, QFileDialog
from qfluentwidgets import (
    ExpandSettingCard, PrimaryPushSettingCard, PushSettingCard,
    ComboBox, FluentIcon as FIF, MessageBox
)

from app.common.config import cfg
from app.common.icon import Icon
from app.common.notification import Notification
from ..core.ccp_core import CcpCore


class FastCcpCard(ExpandSettingCard):
    """Fast CCP UI Card"""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(
            icon=Icon.CCP,
            title=self.tr("CCP Tool"),
            content=self.tr("CCP protocol diagnostic and analysis tool"),
            parent=parent
        )
        self.processor = CcpCore()
        self.__init_ui()
        self.__connect_signals()

    def __init_ui(self):
        self.option_combo = ComboBox(self)
        self.option_combo.addItems([
            self.tr("Full Processing"),
            self.tr("Analysis Only"),
            self.tr("Configuration Mode")
        ])
        self.output_folder_card = PushSettingCard(
            self.tr("Choose folder"), FIF.FOLDER_ADD,
            self.tr("Output Directory"), cfg.get(cfg.fastCCPOutputFolder) or ""
        )
        self.input_file_card = PushSettingCard(
            self.tr("Choose file"), FIF.DOCUMENT,
            self.tr("Input File"), cfg.get(cfg.fastCCPInputFile) or ""
        )
        self.execute_card = PrimaryPushSettingCard(
            self.tr("Execute"), FIF.PLAY,
            self.tr("Execute CCP Processing"),
            self.tr("Click to start processing")
        )
        self.__add_cards_to_layout()
        self.__apply_option_state(0)

    def __add_cards_to_layout(self):
        self.card.addWidget(self.option_combo)
        self.viewLayout.addWidget(self.input_file_card)
        self.viewLayout.addWidget(self.output_folder_card)
        self.viewLayout.addWidget(self.execute_card)
        self._adjustViewSize()

    def __connect_signals(self):
        self.option_combo.currentIndexChanged.connect(self.__on_option_changed)
        self.output_folder_card.clicked.connect(self.__on_choose_output_folder)
        self.input_file_card.clicked.connect(self.__on_choose_input_file)
        self.execute_card.clicked.connect(self.__on_execute_clicked)

    def __on_option_changed(self, index: int):
        self.__apply_option_state(index)
        cfg.set(cfg.fastCCPSelectedOption, index)

    def __on_choose_output_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, self.tr("Choose output folder"), cfg.get(cfg.fastCCPOutputFolder) or ""
        )
        if folder:
            cfg.set(cfg.fastCCPOutputFolder, folder)
            self.output_folder_card.setContent(folder)

    def __on_choose_input_file(self):
        file, _ = QFileDialog.getOpenFileName(
            self, self.tr("Choose input file"), cfg.get(cfg.fastCCPInputFile) or "",
            "All Files (*.*);;Excel Files (*.xlsx);;ARXML Files (*.arxml)"
        )
        if file:
            cfg.set(cfg.fastCCPInputFile, file)
            self.input_file_card.setContent(file)

    def __on_execute_clicked(self):
        try:
            config = self.get_config()
            if not config["input_file"]:
                Notification.warning(
                    self.tr("Warning"),
                    self.tr("Please select input file"),
                    parent=self
                )
                return
            result = self.processor.process(config)
            if result.success:
                Notification.success(
                    self.tr("Success"),
                    self.tr(f"Processing completed!\n{result.message}"),
                    parent=self
                )
            else:
                Notification.error(
                    self.tr("Error"),
                    self.tr(f"Processing failed: {result.message}"),
                    parent=self
                )
        except Exception as e:
            Notification.error(
                self.tr("Error"),
                self.tr(f"Processing error: {str(e)}"),
                parent=self
            )

    def __apply_option_state(self, index: int):
        if index == 0:
            self.output_folder_card.setVisible(True)
            self.input_file_card.setVisible(True)
            self.execute_card.setVisible(True)
            self.output_folder_card.setEnabled(True)
            self.input_file_card.setEnabled(True)
            self.execute_card.setEnabled(True)
        elif index == 1:
            self.output_folder_card.setVisible(False)
            self.input_file_card.setVisible(True)
            self.execute_card.setVisible(True)
            self.input_file_card.setEnabled(True)
            self.execute_card.setEnabled(True)
        elif index == 2:
            self.output_folder_card.setVisible(True)
            self.input_file_card.setVisible(False)
            self.execute_card.setVisible(False)
            self.output_folder_card.setEnabled(True)

    def get_config(self) -> Dict[str, Any]:
        return {
            "input_file": cfg.get(cfg.fastCCPInputFile) or "",
            "output_folder": cfg.get(cfg.fastCCPOutputFolder) or "",
            "selected_option": self.option_combo.currentIndex()
        }

    def set_config(self, config: Dict[str, Any]):
        if "input_file" in config:
            cfg.set(cfg.fastCCPInputFile, config["input_file"])
            self.input_file_card.setContent(config["input_file"])
        if "output_folder" in config:
            cfg.set(cfg.fastCCPOutputFolder, config["output_folder"])
            self.output_folder_card.setContent(config["output_folder"])
        if "selected_option" in config:
            index = config["selected_option"]
            if 0 <= index < self.option_combo.count():
                self.option_combo.setCurrentIndex(index)
                self.__apply_option_state(index)

    def cleanup(self):
        self.processor.cleanup()
