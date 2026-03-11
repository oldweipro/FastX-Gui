"""Item group panel -- dynamic-column table for items of a single template."""

from typing import Any

from PySide6.QtCore import QModelIndex, Qt, Signal
from PySide6.QtWidgets import QHeaderView, QVBoxLayout, QWidget
from qfluentwidgets import StrongBodyLabel, TableView

from app.common.notification import Notification
from app.common.signal_bus import signalBus
from app.view.app_interface.service import item_service, template_service
from app.view.app_interface.table_model.base_table_model import BaseTableModel


class _DynamicItemModel(BaseTableModel):
    """Table model with columns derived from template fields at runtime."""

    def __init__(self, parent=None):
        super().__init__(parent=parent, page_size=50)
        self._headers: list[str] = ["Title"]
        self._field_names: list[str] = []  # field name keys in field_values

    def set_columns(self, field_defs: list[dict]):
        """Configure columns from template field definitions."""
        self._headers = ["Title"] + [
            fd.get("label") or fd["name"] for fd in field_defs
        ] + ["Created At"]
        self._field_names = [fd["name"] for fd in field_defs]

    def columnCount(self, parent=None) -> int:
        return len(self._headers)

    def _get_header_labels(self) -> list[str]:
        return self._headers

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid():
            return None
        row = (self._current_page - 1) * self._page_size + index.row()
        if row >= len(self._data):
            return None
        item = self._data[row]
        col = index.column()

        if role == Qt.DisplayRole:
            if col == 0:
                return item.get("title", "")
            field_idx = col - 1
            if field_idx < len(self._field_names):
                fv = item.get("field_values") or {}
                val = fv.get(self._field_names[field_idx], "")
                if isinstance(val, bool):
                    return "Yes" if val else "No"
                return str(val) if val else ""
            # Last column: Created At
            if col == len(self._headers) - 1:
                dt = item.get("created_at")
                return dt.strftime("%Y-%m-%d %H:%M") if dt else ""
            return ""
        if role == Qt.UserRole:
            return item.get("id", "")
        return None

    def _sort_data(self):
        self._data.sort(key=lambda x: x.get("created_at", ""), reverse=True)


class ItemGroupPanel(QWidget):
    """Panel showing all items of one template in a dynamic-column table."""

    editItemRequested = Signal(str, str)  # item_id, project_id

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._project_id = ""
        self._template_id = ""
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(8)

        self.title_label = StrongBodyLabel("Items", self)
        layout.addWidget(self.title_label)

        self.model = _DynamicItemModel(self)
        self.table = TableView(self)
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(TableView.SelectRows)
        self.table.setSelectionMode(TableView.SingleSelection)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.doubleClicked.connect(self._on_double_click)
        layout.addWidget(self.table, 1)

    def load_group(self, template_id: str, project_id: str):
        self._template_id = template_id
        self._project_id = project_id

        tmpl = template_service.get_template(template_id)
        if tmpl is None:
            self.title_label.setText("Items (unknown template)")
            self.model.set_columns([])
            self.model.set_data([])
            return

        self.title_label.setText(f"Items \u2014 {tmpl['name']}")
        field_defs = tmpl.get("fields", [])
        self.model.set_columns(field_defs)

        items = item_service.list_items(project_id, template_id=template_id)
        self.model.set_data(items)

    def _on_double_click(self, index: QModelIndex):
        item_id = self.model.data(index, Qt.UserRole)
        if item_id:
            self.editItemRequested.emit(item_id, self._project_id)

    def _get_selected_id(self) -> str | None:
        indexes = self.table.selectionModel().selectedRows()
        if not indexes:
            return None
        return self.model.data(indexes[0], Qt.UserRole)

    # -- Actions (called from command bar) --

    def on_new_item(self):
        from app.view.app_interface.dialogs.item_create_dialog import ItemCreateDialog

        templates = template_service.list_templates(self._project_id)
        if not templates:
            Notification.warning("Warning", "Create a template first", parent=self)
            return
        dlg = ItemCreateDialog(templates, self.window(), default_template_id=self._template_id)
        if dlg.exec():
            data = dlg.get_data()
            if data:
                try:
                    result = item_service.create_item(
                        project_id=self._project_id,
                        template_id=data["template_id"],
                        title=data["title"],
                    )
                    signalBus.dataChanged.emit()
                    self.load_group(self._template_id, self._project_id)
                    self.editItemRequested.emit(result["id"], self._project_id)
                except Exception as e:
                    Notification.error("Error", str(e), parent=self)

    def on_delete_item(self):
        from qfluentwidgets import MessageBox

        item_id = self._get_selected_id()
        if not item_id:
            Notification.warning("Warning", "Select an item first", parent=self)
            return
        box = MessageBox("Delete Item", "Are you sure?", self.window())
        if box.exec():
            item_service.delete_item(item_id)
            signalBus.dataChanged.emit()
            self.load_group(self._template_id, self._project_id)
