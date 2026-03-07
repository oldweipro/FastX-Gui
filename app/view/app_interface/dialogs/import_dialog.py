"""Import options dialog."""

from PySide6.QtWidgets import QFileDialog
from qfluentwidgets import LineEdit, MessageBoxBase, PushButton, SubtitleLabel


class ImportDialog(MessageBoxBase):
    """Dialog for configuring import options."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel("Import Data", self)

        self.fileEdit = LineEdit(self)
        self.fileEdit.setPlaceholderText("Select file...")
        self.fileEdit.setReadOnly(True)
        self.browseBtn = PushButton("Browse", self)
        self.browseBtn.clicked.connect(self._browse)

        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.fileEdit)
        self.viewLayout.addWidget(self.browseBtn)

        self.yesButton.setText("Import")
        self.cancelButton.setText("Cancel")
        self.widget.setMinimumWidth(450)

        self._file_path = ""

    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select File", "", "JSON Files (*.json);;Excel Files (*.xlsx)"
        )
        if path:
            self._file_path = path
            self.fileEdit.setText(path)

    def get_data(self) -> dict:
        return {"file_path": self._file_path}
