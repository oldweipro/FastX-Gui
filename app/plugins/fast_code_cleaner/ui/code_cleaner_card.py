from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QVBoxLayout
from qfluentwidgets import (
    ExpandSettingCard,
    PrimaryPushSettingCard,
    PushSettingCard,
    SwitchSettingCard, FluentIconBase, MessageBox, MessageBoxBase, SubtitleLabel, LineEdit,
)
from qfluentwidgets import FluentIcon as FIF

from app.common.config import cfg
from app.common.icon import UIcon
from ..core.code_cleaner_core import CodeCleanerCore


class FastCodeCleanerCard(ExpandSettingCard):
    """Fast Code Cleaner UI Card"""

    def __init__(
        self,
        icon: str | QIcon | FluentIconBase = None,
        title: str = None,
        content=None,
        parent=None,
    ):
        if icon is None:
            icon = UIcon.get("ic_fluent_comment_dismiss_24_regular")
        if not title:
            title = self.tr("Remove Python Code Comment")
        if content is None:
            content = self.tr("To apply software copyrights, need supply whole code without comments")
        super().__init__(icon, title, content, parent)
        self.core = CodeCleanerCore()
        self.__init_cards()
        self.__connect_signals()

    def __init_cards(self):
        self.input_folder_card = PushSettingCard(
            self.tr("Choose folder"),
            FIF.FOLDER_ADD,
            self.tr("Project Input Directory"),
            cfg.get(cfg.rmCommentsInputFolder)
        )
        self.output_folder_card = PushSettingCard(
            self.tr("Choose folder"),
            FIF.FOLDER_ADD,
            self.tr("Project Output Directory"),
            cfg.get(cfg.rmCommentsOutputFolder)
        )
        self.remove_comments_card = SwitchSettingCard(
            FIF.DOCUMENT,
            self.tr("Remove Comments"),
            self.tr("Remove single line comments"),
            cfg.rmCommentsRemoveComments
        )
        self.remove_docstrings_card = SwitchSettingCard(
            FIF.EDIT,
            self.tr("Remove Docstrings"),
            self.tr("Remove module, class and function docstrings"),
            cfg.rmCommentsRemoveDocstrings
        )
        self.remove_empty_lines_card = SwitchSettingCard(
            FIF.LAYOUT,
            self.tr("Remove Empty Lines"),
            self.tr("Remove empty lines from code"),
            cfg.rmCommentsRemoveEmptyLines
        )
        self.keep_triple_quotes_card = SwitchSettingCard(
            FIF.DOCUMENT,
            self.tr("Keep Triple Quotes"),
            self.tr("Keep triple quoted strings"),
            cfg.rmCommentsKeepTripleQuotes
        )
        self.recursive_card = SwitchSettingCard(
            FIF.SYNC,
            self.tr("Recursive"),
            self.tr("Process subdirectories recursively"),
            cfg.rmCommentsRecursive
        )
        self.output_suffix_card = PushSettingCard(
            self.tr("Set suffix"),
            FIF.EDIT,
            self.tr("Output File Suffix"),
            cfg.get(cfg.rmCommentsOutputSuffix)
        )
        self.exclude_files_card = PushSettingCard(
            self.tr("Set exclude files"),
            FIF.FILTER,
            self.tr("Exclude Files (comma separated)"),
            cfg.get(cfg.rmCommentsExcludeFiles)
        )
        self.exclude_patterns_card = PushSettingCard(
            self.tr("Set exclude patterns"),
            FIF.FILTER,
            self.tr("Exclude Patterns (comma separated)"),
            cfg.get(cfg.rmCommentsExcludePatterns)
        )
        self.execute_card = PrimaryPushSettingCard(
            self.tr("Execute"),
            FIF.PLAY,
            self.tr("Execute Code Comment Removal"),
            self.tr("Click to start processing")
        )
        self.__add_cards_to_layout()

    def __add_cards_to_layout(self):
        self.column_layout = QHBoxLayout()
        self.row_left_layout = QVBoxLayout()
        self.row_right_layout = QVBoxLayout()
        self.viewLayout.addLayout(self.column_layout)
        self.column_layout.addLayout(self.row_left_layout)
        self.column_layout.addLayout(self.row_right_layout)
        self.row_left_layout.addWidget(self.input_folder_card)
        self.row_left_layout.addWidget(self.output_folder_card)
        self.row_left_layout.addWidget(self.remove_comments_card)
        self.row_left_layout.addWidget(self.remove_docstrings_card)
        self.row_left_layout.addWidget(self.remove_empty_lines_card)
        self.row_right_layout.addWidget(self.keep_triple_quotes_card)
        self.row_right_layout.addWidget(self.recursive_card)
        self.row_right_layout.addWidget(self.output_suffix_card)
        self.row_right_layout.addWidget(self.exclude_files_card)
        self.row_right_layout.addWidget(self.exclude_patterns_card)
        self.viewLayout.addWidget(self.execute_card)
        self._adjustViewSize()

    def __connect_signals(self):
        self.input_folder_card.clicked.connect(
            lambda: self.__on_choose_folder(cfg.rmCommentsInputFolder, self.input_folder_card)
        )
        self.output_folder_card.clicked.connect(
            lambda: self.__on_choose_folder(cfg.rmCommentsOutputFolder, self.output_folder_card)
        )
        self.remove_comments_card.checkedChanged.connect(
            lambda checked: cfg.set(cfg.rmCommentsRemoveComments, checked)
        )
        self.remove_docstrings_card.checkedChanged.connect(
            lambda checked: cfg.set(cfg.rmCommentsRemoveDocstrings, checked)
        )
        self.remove_empty_lines_card.checkedChanged.connect(
            lambda checked: cfg.set(cfg.rmCommentsRemoveEmptyLines, checked)
        )
        self.keep_triple_quotes_card.checkedChanged.connect(
            lambda checked: cfg.set(cfg.rmCommentsKeepTripleQuotes, checked)
        )
        self.recursive_card.checkedChanged.connect(
            lambda checked: cfg.set(cfg.rmCommentsRecursive, checked)
        )
        self.output_suffix_card.clicked.connect(
            lambda: self.__on_set_value(cfg.rmCommentsOutputSuffix, self.output_suffix_card, self.tr("Set Output Suffix"))
        )
        self.exclude_files_card.clicked.connect(
            lambda: self.__on_set_value(cfg.rmCommentsExcludeFiles, self.exclude_files_card, self.tr("Set Exclude Files"))
        )
        self.exclude_patterns_card.clicked.connect(
            lambda: self.__on_set_value(cfg.rmCommentsExcludePatterns, self.exclude_patterns_card, self.tr("Set Exclude Patterns"))
        )
        self.execute_card.clicked.connect(self.__on_execute)

    def __on_choose_folder(self, config_item, card):
        folder = QFileDialog.getExistingDirectory(self, self.tr("Choose folder"), cfg.get(config_item))
        if not folder or cfg.get(config_item) == folder:
            return
        cfg.set(config_item, folder)
        card.setContent(folder)

    def __on_set_value(self, config_item, card, title):
        current_value = cfg.get(config_item)
        dialog = self.__create_input_dialog(title, current_value)
        if dialog.exec():
            new_value = dialog.lineEdit.text()
            if new_value != current_value:
                cfg.set(config_item, new_value)
                card.setContent(new_value)

    def __create_input_dialog(self, title, default_value=""):
        class InputDialog(MessageBoxBase):
            def __init__(self, parent=None):
                super().__init__(parent)
                self.titleLabel = SubtitleLabel(title, self)
                self.lineEdit = LineEdit(self)
                self.lineEdit.setText(default_value)
                self.lineEdit.setPlaceholderText(self.tr("Please enter..."))
                self.lineEdit.setClearButtonEnabled(True)
                self.viewLayout.addWidget(self.titleLabel)
                self.viewLayout.addWidget(self.lineEdit)
                self.yesButton.setText(self.tr("OK"))
                self.cancelButton.setText(self.tr("Cancel"))
                self.widget.setMinimumWidth(600)
                self.lineEdit.textChanged.connect(self.validate)
            def validate(self):
                return True
        return InputDialog(self.window())

    def __on_execute(self):
        try:
            input_path = cfg.get(cfg.rmCommentsInputFolder)
            output_path = cfg.get(cfg.rmCommentsOutputFolder)
            stats = self.core.execute(
                input_path=input_path,
                output_path=output_path,
                remove_comments=cfg.get(cfg.rmCommentsRemoveComments),
                remove_docstrings=cfg.get(cfg.rmCommentsRemoveDocstrings),
                remove_empty_lines=cfg.get(cfg.rmCommentsRemoveEmptyLines),
                keep_triple_quotes=cfg.get(cfg.rmCommentsKeepTripleQuotes),
                output_suffix=cfg.get(cfg.rmCommentsOutputSuffix),
                recursive=cfg.get(cfg.rmCommentsRecursive),
                exclude_files=[f.strip() for f in cfg.get(cfg.rmCommentsExcludeFiles).split(',') if f.strip()],
                exclude_patterns=[p.strip() for p in cfg.get(cfg.rmCommentsExcludePatterns).split(',') if p.strip()]
            )
            message = self.tr("Processing completed!\n")
            message += self.tr(f"Total files: {stats['total_files']}\n")
            message += self.tr(f"Processed: {stats['processed']}\n")
            message += self.tr(f"Skipped: {stats['skipped']}\n")
            message += self.tr(f"Errors: {stats['errors']}")
            w = MessageBox(self.tr("Success"), message, self.window())
            w.setClosableOnMaskClicked(True)
            w.setDraggable(True)
            w.exec_()
        except Exception as e:
            MessageBox(self.tr("Error"), self.tr(f"Processing failed: {str(e)}"), self.window()).exec_()
