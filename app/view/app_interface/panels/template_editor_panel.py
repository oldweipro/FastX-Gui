"""Template editor panel — edit template name, description, and manage fields."""

import json

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    CheckBox,
    InfoBar,
    InfoBarPosition,
    LineEdit,
    PrimaryPushButton,
    PushButton,
    StrongBodyLabel,
    TableWidget,
)

from app.common.signal_bus import signalBus
from app.service import template_service

FIELD_TYPES = ["text", "number", "checkbox", "select", "date", "textarea", "template_item"]


class TemplateEditorPanel(QWidget):
    """Inline editor for a template and its fields."""

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._template_id = ""
        self._project_id = ""
        self._fields: list[dict] = []
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(8)

        # Template info
        self.title_label = StrongBodyLabel("Edit Template", self)
        layout.addWidget(self.title_label)

        form = QHBoxLayout()
        form.setSpacing(8)
        self.name_edit = LineEdit(self)
        self.name_edit.setPlaceholderText("Template name")
        self.desc_edit = LineEdit(self)
        self.desc_edit.setPlaceholderText("Description")
        form.addWidget(BodyLabel("Name:", self))
        form.addWidget(self.name_edit, 1)
        form.addWidget(BodyLabel("Desc:", self))
        form.addWidget(self.desc_edit, 1)
        layout.addLayout(form)

        # Fields section
        layout.addWidget(StrongBodyLabel("Fields", self))

        self.field_table = TableWidget(self)
        self.field_table.setColumnCount(5)
        self.field_table.setHorizontalHeaderLabels(["Name", "Type", "Label", "Required", "Options"])
        self.field_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.field_table.verticalHeader().setVisible(False)
        self.field_table.setSelectionBehavior(TableWidget.SelectRows)
        layout.addWidget(self.field_table, 1)

        # Field buttons
        btn_row = QHBoxLayout()
        self.btn_add_field = PrimaryPushButton("Add Field", self)
        self.btn_remove_field = PushButton("Remove Field", self)
        self.btn_move_up = PushButton("Move Up", self)
        self.btn_move_down = PushButton("Move Down", self)
        btn_row.addWidget(self.btn_add_field)
        btn_row.addWidget(self.btn_remove_field)
        btn_row.addWidget(self.btn_move_up)
        btn_row.addWidget(self.btn_move_down)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.btn_add_field.clicked.connect(self._add_field_row)
        self.btn_remove_field.clicked.connect(self._remove_field_row)
        self.btn_move_up.clicked.connect(self._move_up)
        self.btn_move_down.clicked.connect(self._move_down)

    def load_template(self, template_id: str, project_id: str):
        self._template_id = template_id
        self._project_id = project_id

        tmpl = template_service.get_template(template_id)
        if tmpl is None:
            return

        self.name_edit.setText(tmpl["name"])
        self.desc_edit.setText(tmpl.get("description", ""))
        self._fields = tmpl.get("fields", [])
        self._rebuild_field_table()

    def _rebuild_field_table(self):
        self.field_table.setRowCount(0)
        self.field_table.setRowCount(len(self._fields))
        for i, f in enumerate(self._fields):
            self.field_table.setItem(i, 0, _item(f.get("name", "")))
            # Type combo
            combo = QComboBox(self)
            combo.addItems(FIELD_TYPES)
            idx = FIELD_TYPES.index(f.get("field_type", "text")) if f.get("field_type", "text") in FIELD_TYPES else 0
            combo.setCurrentIndex(idx)
            self.field_table.setCellWidget(i, 1, combo)
            self.field_table.setItem(i, 2, _item(f.get("label", "")))
            # Required checkbox
            cb = CheckBox(self)
            cb.setChecked(f.get("required", False))
            self.field_table.setCellWidget(i, 3, cb)
            # Options as text
            opts = f.get("options", [])
            self.field_table.setItem(i, 4, _item(json.dumps(opts, ensure_ascii=False) if opts else ""))

    def _add_field_row(self):
        self._fields.append({"name": "", "field_type": "text", "label": "", "required": False, "options": []})
        self._rebuild_field_table()

    def _remove_field_row(self):
        row = self.field_table.currentRow()
        if 0 <= row < len(self._fields):
            self._collect_fields_from_table()
            self._fields.pop(row)
            self._rebuild_field_table()

    def _move_up(self):
        row = self.field_table.currentRow()
        if row > 0:
            self._collect_fields_from_table()
            self._fields[row - 1], self._fields[row] = self._fields[row], self._fields[row - 1]
            self._rebuild_field_table()
            self.field_table.selectRow(row - 1)

    def _move_down(self):
        row = self.field_table.currentRow()
        if 0 <= row < len(self._fields) - 1:
            self._collect_fields_from_table()
            self._fields[row], self._fields[row + 1] = self._fields[row + 1], self._fields[row]
            self._rebuild_field_table()
            self.field_table.selectRow(row + 1)

    def _collect_fields_from_table(self):
        """Read current field data from the table widgets."""
        fields = []
        for i in range(self.field_table.rowCount()):
            name_item = self.field_table.item(i, 0)
            combo = self.field_table.cellWidget(i, 1)
            label_item = self.field_table.item(i, 2)
            cb = self.field_table.cellWidget(i, 3)
            opts_item = self.field_table.item(i, 4)

            opts_text = opts_item.text() if opts_item else ""
            try:
                opts = json.loads(opts_text) if opts_text else []
            except (json.JSONDecodeError, TypeError):
                opts = [s.strip() for s in opts_text.split(",") if s.strip()] if opts_text else []

            fields.append({
                "name": name_item.text() if name_item else "",
                "field_type": combo.currentText() if combo else "text",
                "label": label_item.text() if label_item else "",
                "required": cb.isChecked() if cb else False,
                "options": opts,
            })
        self._fields = fields

    def on_save(self):
        self._collect_fields_from_table()
        name = self.name_edit.text().strip()
        desc = self.desc_edit.text().strip()
        if not name:
            InfoBar.warning("Warning", "Template name cannot be empty", parent=self, position=InfoBarPosition.TOP)
            return
        try:
            template_service.update_template(self._template_id, name=name, description=desc, fields=self._fields)
            signalBus.dataChanged.emit()
            InfoBar.success("Saved", "Template updated", parent=self, position=InfoBarPosition.TOP)
        except Exception as e:
            InfoBar.error("Error", str(e), parent=self, position=InfoBarPosition.TOP)


def _item(text: str):
    from PySide6.QtWidgets import QTableWidgetItem
    item = QTableWidgetItem(text)
    item.setFlags(item.flags() | Qt.ItemIsEditable)
    return item
