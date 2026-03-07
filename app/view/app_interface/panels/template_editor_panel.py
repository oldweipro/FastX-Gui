"""Template editor panel — edit template name, description, and manage fields."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    InfoBar,
    InfoBarPosition,
    LineEdit,
    StrongBodyLabel,
    TableWidget,
)

from app.common.signal_bus import signalBus
from app.service import template_service

FIELD_TYPES = ["text", "number", "checkbox", "select", "date", "textarea", "template_item"]


class TemplateEditorPanel(QWidget):
    """Editor for a template and its fields.

    The fields table is read-only; all editing is done through the
    :class:`FieldEditDialog` opened via double-click or the CommandBar
    *Edit Field* action.
    """

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
        self.field_table.setColumnCount(7)
        self.field_table.setHorizontalHeaderLabels(
            ["Name", "Type", "Label", "Required", "Default", "Ref Template", "Multi-Select"]
        )
        self.field_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.field_table.verticalHeader().setVisible(False)
        self.field_table.setSelectionBehavior(TableWidget.SelectRows)
        self.field_table.setSelectionMode(TableWidget.SingleSelection)
        self.field_table.setEditTriggers(TableWidget.NoEditTriggers)
        self.field_table.doubleClicked.connect(self._on_double_click)
        layout.addWidget(self.field_table, 1)

    # ── Data loading ─────────────────────────────────────────────

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
        """Repopulate the read-only table from ``self._fields``."""
        # Build a template-name lookup for ref_tmpl_id display
        tmpl_names: dict[str, str] = {}
        if any(f.get("ref_tmpl_id") for f in self._fields):
            for t in template_service.list_templates(self._project_id):
                tmpl_names[t["id"]] = t["name"]

        self.field_table.setRowCount(0)
        self.field_table.setRowCount(len(self._fields))
        for i, f in enumerate(self._fields):
            self.field_table.setItem(i, 0, _ro_item(f.get("name", "")))
            self.field_table.setItem(i, 1, _ro_item(f.get("field_type", "text")))
            self.field_table.setItem(i, 2, _ro_item(f.get("label", "")))
            self.field_table.setItem(i, 3, _ro_item("\u2713" if f.get("required") else ""))
            self.field_table.setItem(i, 4, _ro_item(f.get("default_val", "") or ""))
            ref_id = f.get("ref_tmpl_id")
            self.field_table.setItem(i, 5, _ro_item(tmpl_names.get(ref_id, "") if ref_id else ""))
            self.field_table.setItem(i, 6, _ro_item("\u2713" if f.get("multi_select") else ""))

    # ── Double-click → edit dialog ───────────────────────────────

    def _on_double_click(self, index):
        row = index.row()
        if 0 <= row < len(self._fields):
            self._open_edit_dialog(row)

    def _open_edit_dialog(self, row: int):
        from app.view.app_interface.dialogs.field_edit_dialog import FieldEditDialog

        dlg = FieldEditDialog(
            self._fields[row], self._project_id, self._template_id, self.window()
        )
        if dlg.exec():
            data = dlg.get_data()
            if data:
                self._fields[row] = data
                self._rebuild_field_table()

    # ── Public actions (called from CommandBar) ──────────────────

    def on_add_field(self):
        from app.view.app_interface.dialogs.field_edit_dialog import FieldEditDialog

        dlg = FieldEditDialog(None, self._project_id, self._template_id, self.window())
        if dlg.exec():
            data = dlg.get_data()
            if data:
                self._fields.append(data)
                self._rebuild_field_table()

    def on_edit_field(self):
        row = self.field_table.currentRow()
        if 0 <= row < len(self._fields):
            self._open_edit_dialog(row)
        else:
            InfoBar.warning(
                "Warning", "Select a field first", parent=self, position=InfoBarPosition.TOP
            )

    def on_remove_field(self):
        row = self.field_table.currentRow()
        if 0 <= row < len(self._fields):
            self._fields.pop(row)
            self._rebuild_field_table()
        else:
            InfoBar.warning(
                "Warning", "Select a field first", parent=self, position=InfoBarPosition.TOP
            )

    def on_move_up(self):
        row = self.field_table.currentRow()
        if row > 0:
            self._fields[row - 1], self._fields[row] = self._fields[row], self._fields[row - 1]
            self._rebuild_field_table()
            self.field_table.selectRow(row - 1)

    def on_move_down(self):
        row = self.field_table.currentRow()
        if 0 <= row < len(self._fields) - 1:
            self._fields[row], self._fields[row + 1] = self._fields[row + 1], self._fields[row]
            self._rebuild_field_table()
            self.field_table.selectRow(row + 1)

    # ── Save ─────────────────────────────────────────────────────

    def on_save(self):
        name = self.name_edit.text().strip()
        desc = self.desc_edit.text().strip()
        if not name:
            InfoBar.warning(
                "Warning", "Template name cannot be empty", parent=self, position=InfoBarPosition.TOP
            )
            return
        try:
            template_service.update_template(
                self._template_id, name=name, description=desc, fields=self._fields
            )
            signalBus.dataChanged.emit()
            InfoBar.success("Saved", "Template updated", parent=self, position=InfoBarPosition.TOP)
        except Exception as e:
            InfoBar.error("Error", str(e), parent=self, position=InfoBarPosition.TOP)


def _ro_item(text: str) -> QTableWidgetItem:
    """Create a read-only table item."""
    item = QTableWidgetItem(text)
    item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
    return item
