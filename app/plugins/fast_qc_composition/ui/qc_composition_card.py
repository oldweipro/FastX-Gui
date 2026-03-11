from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QVBoxLayout, QTableWidgetItem, QHeaderView, QAbstractItemView
from qfluentwidgets import (
    ExpandSettingCard, PrimaryPushSettingCard, PushSettingCard, ComboBox, TableWidget,
    FluentIconBase, MessageBox, MessageBoxBase, SubtitleLabel, LineEdit, BodyLabel, SpinBox
)
from qfluentwidgets import FluentIcon as FIF

from app.common.config import cfg
from app.common.icon import UIcon
from app.common.notification import Notification


class TableFrame(TableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.verticalHeader().hide()
        self.setBorderRadius(8)
        self.setBorderVisible(True)
        self.setWordWrap(False)
        self.columnMeta = [
            {"type": "text"},
            {"type": "combo", "options": ["Core0", "Core1", "Core2", "None"]},
            {"type": "int"}, {"type": "int"}, {"type": "int"}, {"type": "int"}
        ]
        self.headInfos = [
            self.tr('Swc Name'), self.tr('Core Assign'), self.tr('P-Ports'),
            self.tr('R-Ports'), self.tr('Runnables'), self.tr('Events')
        ]
        self.swcsInfos = self._load_from_config()
        self.setColumnCount(len(self.headInfos))
        self.setRowCount(len(self.swcsInfos))
        self.setMinimumHeight(300)
        self.setHorizontalHeaderLabels(self.headInfos)
        for i, swcInfo in enumerate(self.swcsInfos):
            for j in range(len(self.headInfos)):
                item = QTableWidgetItem(swcInfo[j])
                item.setTextAlignment(Qt.AlignCenter)
                self.setItem(i, j, item)
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setDefaultAlignment(Qt.AlignCenter)
        self.itemChanged.connect(self._on_item_changed)
        self.doubleClicked.connect(self._on_double_clicked)

    def _load_from_config(self):
        try:
            data = cfg.get(cfg.qcCompositionTableData)
            if data:
                return data
        except:
            pass
        return [['ExampleSwc', 'Core0', '0', '0', '2', '2']]

    def _save_to_config(self):
        data = []
        for i in range(self.rowCount()):
            row = []
            for j in range(self.columnCount()):
                item = self.item(i, j)
                row.append(item.text() if item else '')
            data.append(row)
        cfg.set(cfg.qcCompositionTableData, data)

    def _on_item_changed(self, item):
        self._save_to_config()

    def _create_editor_dialog(self, headers, row_data, column_meta):
        class TableEditDialog(MessageBoxBase):
            def __init__(self, parent=None):
                super().__init__(parent)
                self.titleLabel = SubtitleLabel(self.tr("Edit Item"), self)
                self.viewLayout.addWidget(self.titleLabel)
                self._widgets = []
                for i, title in enumerate(headers):
                    meta = column_meta[i]
                    value = row_data[i]
                    row_layout = QHBoxLayout()
                    row_layout.setSpacing(10)
                    label = BodyLabel(title)
                    label.setFixedWidth(120)
                    label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                    row_layout.addWidget(label)
                    if meta["type"] == "combo":
                        widget = ComboBox()
                        widget.addItems(meta["options"])
                        if value in meta["options"]:
                            widget.setCurrentText(value)
                    elif meta["type"] == "int":
                        widget = SpinBox()
                        widget.setRange(0, 9999)
                        widget.setValue(int(value))
                    else:
                        widget = LineEdit()
                        widget.setText(value)
                    widget.setMinimumWidth(250)
                    row_layout.addWidget(widget)
                    self._widgets.append(widget)
                    self.viewLayout.addLayout(row_layout)
                self.yesButton.setText(self.tr("Save"))
                self.cancelButton.setText(self.tr("Cancel"))
                self.widget.setMinimumWidth(600)

            def get_data(self):
                data = []
                for w in self._widgets:
                    if isinstance(w, ComboBox):
                        data.append(w.currentText())
                    elif isinstance(w, SpinBox):
                        data.append(str(w.value()))
                    else:
                        data.append(w.text())
                return data
        return TableEditDialog(self.window())

    def _on_double_clicked(self, index):
        row = index.row()
        row_data = [self.item(row, col).text() if self.item(row, col) else "" for col in range(self.columnCount())]
        dialog = self._create_editor_dialog(self.headInfos, row_data, self.columnMeta)
        if dialog.exec():
            new_data = dialog.get_data()
            self.blockSignals(True)
            for col, value in enumerate(new_data):
                self.item(row, col).setText(value)
            self.blockSignals(False)
            self._save_to_config()


class FastQcCompositionCard(ExpandSettingCard):
    """Fast QC Composition UI Card"""

    def __init__(
        self,
        icon: str | QIcon | FluentIconBase = None,
        title: str = None,
        content=None,
        parent=None,
    ):
        if icon is None:
            icon = UIcon.get("ic_fluent_channel_share_48_regular")
        if not title:
            title = self.tr("QCraft Composition Arxml Adapter")
        if content is None:
            content = self.tr("To Modify QCraft Composition Arxml File To FT Rules For J6")
        super().__init__(icon, title, content, parent)
        self.combox = ComboBox(self)
        self.combox.addItems(["Option 1", "Option 2", "Option 3"])
        selected_index = cfg.get(cfg.qcCompositionSelectedOption)
        if 0 <= selected_index < self.combox.count():
            self.combox.setCurrentIndex(selected_index)
        self.card.addWidget(self.combox)
        self.__init_cards()
        self.__on_combo_box_changed(selected_index)
        self.__connect_signals()

    def __init_cards(self):
        self.output_folder_card = PushSettingCard(
            self.tr("Choose folder"), FIF.FOLDER_ADD,
            self.tr("Project Output Directory"), cfg.get(cfg.qcCompositionOutputFolder)
        )
        self.input_file_card = PushSettingCard(
            self.tr("Choose file"),
            UIcon.get('ic_fluent_document_table_truck_24_regular'),
            self.tr("Input File"), cfg.get(cfg.qcCompositionInputFile)
        )
        self.table_card = TableFrame(self)
        self.execute_card = PrimaryPushSettingCard(
            self.tr("Execute"), FIF.PLAY,
            self.tr("Execute QCraft Composition Adaptation"),
            self.tr("Click to start processing")
        )
        self.__add_cards_to_layout()

    def __add_cards_to_layout(self):
        self.viewLayout.addWidget(self.input_file_card)
        self.viewLayout.addWidget(self.output_folder_card)
        self.viewLayout.addWidget(self.table_card)
        self.viewLayout.addWidget(self.execute_card)
        self._adjustViewSize()

    def __connect_signals(self):
        self.output_folder_card.clicked.connect(
            lambda: self.__on_choose_folder(cfg.qcCompositionOutputFolder, self.output_folder_card)
        )
        self.input_file_card.clicked.connect(
            lambda: self.__on_choose_file(cfg.qcCompositionInputFile, self.input_file_card)
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
            "Excel Files (*.xlsx);;ARXML Files (*.arxml);;All Files (*)"
        )
        if not file or cfg.get(config_item) == file:
            return
        cfg.set(config_item, file)
        card.setContent(file)

    def __on_execute(self):
        try:
            message = self.tr("Processing completed!\n")
            Notification.success(
                self.tr("Success"),
                message,
                parent=self
            )
        except Exception as e:
            Notification.error(
                self.tr("Error"),
                self.tr(f"Processing failed: {str(e)}"),
                parent=self
            )

    def __on_combo_box_changed(self, index):
        cfg.set(cfg.qcCompositionSelectedOption, index)
        if index == 0:
            self.input_file_card.setVisible(True)
            self.output_folder_card.setVisible(True)
            self.execute_card.setVisible(True)
            self.input_file_card.setEnabled(True)
            self.output_folder_card.setEnabled(True)
            self.execute_card.setEnabled(True)
        elif index == 1:
            self.input_file_card.setVisible(True)
            self.output_folder_card.setVisible(True)
            self.execute_card.setVisible(False)
            self.input_file_card.setEnabled(True)
            self.output_folder_card.setEnabled(True)
        elif index == 2:
            self.input_file_card.setVisible(True)
            self.output_folder_card.setVisible(True)
            self.execute_card.setVisible(True)
            self.input_file_card.setEnabled(False)
            self.output_folder_card.setEnabled(False)
            self.execute_card.setEnabled(False)
        self._adjustViewSize()
