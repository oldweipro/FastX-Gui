"""Project creation/editing dialog."""

from qfluentwidgets import LineEdit, MessageBoxBase, SubtitleLabel, TextEdit


class ProjectDialog(MessageBoxBase):
    """Dialog for creating or editing a project."""

    def __init__(self, parent=None, name: str = "", description: str = ""):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel("Edit Project" if name else "New Project", self)
        self.nameEdit = LineEdit(self)
        self.nameEdit.setPlaceholderText("Project name")
        self.nameEdit.setText(name)
        self.descEdit = TextEdit(self)
        self.descEdit.setPlaceholderText("Description (optional)")
        self.descEdit.setPlainText(description)
        self.descEdit.setMaximumHeight(100)

        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.nameEdit)
        self.viewLayout.addWidget(self.descEdit)

        self.yesButton.setText("OK")
        self.cancelButton.setText("Cancel")
        self.widget.setMinimumWidth(400)

    def get_data(self) -> tuple[str, str]:
        return self.nameEdit.text().strip(), self.descEdit.toPlainText().strip()
