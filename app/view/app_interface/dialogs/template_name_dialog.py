"""Simple dialog for entering a template name and description."""

from qfluentwidgets import LineEdit, MessageBoxBase, SubtitleLabel, TextEdit


class TemplateNameDialog(MessageBoxBase):
    """Dialog for creating a new template (name + description)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel("New Template", self)
        self.nameEdit = LineEdit(self)
        self.nameEdit.setPlaceholderText("Template name")
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
