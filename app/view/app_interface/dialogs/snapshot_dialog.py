"""Snapshot creation dialog."""

from qfluentwidgets import LineEdit, MessageBoxBase, SubtitleLabel, TextEdit


class SnapshotDialog(MessageBoxBase):
    """Dialog for creating a project snapshot."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel("Create Snapshot", self)
        self.nameEdit = LineEdit(self)
        self.nameEdit.setPlaceholderText("Snapshot name")
        self.descEdit = TextEdit(self)
        self.descEdit.setPlaceholderText("Description (optional)")
        self.descEdit.setMaximumHeight(80)

        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.nameEdit)
        self.viewLayout.addWidget(self.descEdit)

        self.yesButton.setText("Create")
        self.cancelButton.setText("Cancel")
        self.widget.setMinimumWidth(400)

    def get_data(self) -> tuple[str, str]:
        return self.nameEdit.text().strip(), self.descEdit.toPlainText().strip()
