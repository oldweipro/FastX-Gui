"""Simple dialog for creating a new item (title + template selection)."""

from qfluentwidgets import ComboBox, LineEdit, MessageBoxBase, SubtitleLabel


class ItemCreateDialog(MessageBoxBase):
    """Dialog for creating a new item with title and template selection."""

    def __init__(self, templates: list[dict], parent=None):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel("New Item", self)
        self.nameEdit = LineEdit(self)
        self.nameEdit.setPlaceholderText("Item title")
        self.templateCombo = ComboBox(self)
        for t in templates:
            self.templateCombo.addItem(t["name"], userData=t["id"])

        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.nameEdit)
        self.viewLayout.addWidget(self.templateCombo)

        self.yesButton.setText("Create")
        self.cancelButton.setText("Cancel")
        self.widget.setMinimumWidth(400)

    def get_data(self) -> dict | None:
        title = self.nameEdit.text().strip()
        tmpl_id = self.templateCombo.currentData()
        if not title or not tmpl_id:
            return None
        return {"title": title, "template_id": tmpl_id}
