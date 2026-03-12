"""Dialog for editing a single template field with type-aware sections."""

from qfluentwidgets import (
    BodyLabel,
    CheckBox,
    ComboBox,
    LineEdit,
    MessageBoxBase,
    SubtitleLabel,
    TextEdit,
)

from app.view.app_interface.service import template_service

FIELD_TYPES = ["text", "number", "checkbox", "select", "date", "textarea", "template_item"]


class FieldEditDialog(MessageBoxBase):
    """Type-aware dialog for creating or editing a template field.

    Shows/hides sections based on the selected field type:
    - ``select``: options editor + multi-select toggle
    - ``template_item``: reference template picker + multi-select toggle
    - all others: only base fields
    """

    def __init__(
        self,
        field_data: dict | None,
        project_id: str,
        template_id: str,
        parent=None,
    ):
        super().__init__(parent)
        self._project_id = project_id
        self._template_id = template_id

        self.titleLabel = SubtitleLabel(
            "Edit Field" if field_data else "New Field", self
        )
        self.viewLayout.addWidget(self.titleLabel)

        # ── Base fields ──────────────────────────────────────────
        self.nameEdit = LineEdit(self)
        self.nameEdit.setPlaceholderText("Field name (internal key)")
        self.viewLayout.addWidget(BodyLabel("Name:", self))
        self.viewLayout.addWidget(self.nameEdit)

        self.typeCombo = ComboBox(self)
        for ft in FIELD_TYPES:
            self.typeCombo.addItem(ft)
        self.viewLayout.addWidget(BodyLabel("Type:", self))
        self.viewLayout.addWidget(self.typeCombo)

        self.labelEdit = LineEdit(self)
        self.labelEdit.setPlaceholderText("Display label (optional)")
        self.viewLayout.addWidget(BodyLabel("Label:", self))
        self.viewLayout.addWidget(self.labelEdit)

        self.defaultEdit = LineEdit(self)
        self.defaultEdit.setPlaceholderText("Default value (optional)")
        self.viewLayout.addWidget(BodyLabel("Default Value:", self))
        self.viewLayout.addWidget(self.defaultEdit)

        self.requiredCheckBox = CheckBox("Required", self)
        self.viewLayout.addWidget(self.requiredCheckBox)

        # ── select-specific section ──────────────────────────────
        self.optionsLabel = BodyLabel("Options (one per line):", self)
        self.optionsEdit = TextEdit(self)
        self.optionsEdit.setPlaceholderText("Option A\nOption B\nOption C")
        self.optionsEdit.setMaximumHeight(120)
        self.viewLayout.addWidget(self.optionsLabel)
        self.viewLayout.addWidget(self.optionsEdit)

        # ── template_item-specific section ───────────────────────
        self.refTemplateLabel = BodyLabel("Reference Template:", self)
        self.refTemplateCombo = ComboBox(self)
        self._populate_template_combo()
        self.viewLayout.addWidget(self.refTemplateLabel)
        self.viewLayout.addWidget(self.refTemplateCombo)

        # ── shared section (select + template_item) ──────────────
        self.multiSelectCheckBox = CheckBox("Allow multi-select", self)
        self.viewLayout.addWidget(self.multiSelectCheckBox)

        # ── buttons ──────────────────────────────────────────────
        self.yesButton.setText("Save")
        self.cancelButton.setText("Cancel")
        self.widget.setMinimumWidth(420)

        # ── type-change handler ──────────────────────────────────
        self.typeCombo.currentIndexChanged.connect(self._on_type_changed)

        # ── populate from existing data ──────────────────────────
        if field_data:
            self._load_field(field_data)

        # Trigger initial visibility
        self._on_type_changed()

    # ── Private helpers ──────────────────────────────────────────

    def _populate_template_combo(self):
        """Fill the reference-template combo with project templates (excluding self)."""
        templates = template_service.list_templates(self._project_id)
        for t in templates:
            if t["id"] != self._template_id:
                self.refTemplateCombo.addItem(t["name"], userData=t["id"])

    def _load_field(self, fd: dict):
        self.nameEdit.setText(fd.get("name", ""))
        ft = fd.get("field_type", "text")
        idx = FIELD_TYPES.index(ft) if ft in FIELD_TYPES else 0
        self.typeCombo.setCurrentIndex(idx)
        self.labelEdit.setText(fd.get("label", ""))
        self.defaultEdit.setText(fd.get("default_val", "") or "")
        self.requiredCheckBox.setChecked(fd.get("required", False))

        # Options
        opts = fd.get("options", [])
        if isinstance(opts, list):
            self.optionsEdit.setPlainText("\n".join(str(o) for o in opts))

        # Reference template
        ref_id = fd.get("ref_tmpl_id")
        if ref_id:
            idx = self.refTemplateCombo.findData(ref_id)
            if idx >= 0:
                self.refTemplateCombo.setCurrentIndex(idx)

        self.multiSelectCheckBox.setChecked(fd.get("multi_select", False))

    def _on_type_changed(self):
        ft = self.typeCombo.currentText()
        is_select = ft == "select"
        is_tmpl_item = ft == "template_item"

        self.optionsLabel.setVisible(is_select)
        self.optionsEdit.setVisible(is_select)
        self.refTemplateLabel.setVisible(is_tmpl_item)
        self.refTemplateCombo.setVisible(is_tmpl_item)
        self.multiSelectCheckBox.setVisible(is_select or is_tmpl_item)

    # ── Public API ───────────────────────────────────────────────

    def get_data(self) -> dict | None:
        name = self.nameEdit.text().strip()
        if not name:
            return None

        ft = self.typeCombo.currentText()
        label = self.labelEdit.text().strip()
        default_val = self.defaultEdit.text().strip()
        required = self.requiredCheckBox.isChecked()

        options: list[str] = []
        ref_tmpl_id: str | None = None
        multi_select = False

        if ft == "select":
            raw = self.optionsEdit.toPlainText()
            options = [line.strip() for line in raw.splitlines() if line.strip()]
            multi_select = self.multiSelectCheckBox.isChecked()
        elif ft == "template_item":
            ref_tmpl_id = self.refTemplateCombo.currentData()
            multi_select = self.multiSelectCheckBox.isChecked()

        return {
            "name": name,
            "field_type": ft,
            "label": label,
            "required": required,
            "default_val": default_val,
            "options": options,
            "ref_tmpl_id": ref_tmpl_id,
            "multi_select": multi_select,
        }
