from typing import Any

from PySide6.QtCore import QModelIndex, Qt

from app.view.app_interface.table_model.base_table_model import BaseTableModel

_EMPTY = QModelIndex()


class FmItemTableModel(BaseTableModel):
    """Table model for item listing in the fault management system."""

    HEADERS = ["Title", "Template", "Created At", "Updated At"]

    def columnCount(self, parent: QModelIndex = _EMPTY) -> int:
        return len(self.HEADERS)

    def _get_header_labels(self) -> list[str]:
        return self.HEADERS

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid():
            return None
        row = (self._current_page - 1) * self._page_size + index.row()
        if row >= len(self._data):
            return None
        item = self._data[row]

        if role == Qt.DisplayRole:
            col = index.column()
            if col == 0:
                return item.get("title", "")
            if col == 1:
                return item.get("template_name", item.get("template_id", ""))
            if col == 2:
                dt = item.get("created_at")
                return dt.strftime("%Y-%m-%d %H:%M") if dt else ""
            if col == 3:
                dt = item.get("updated_at")
                return dt.strftime("%Y-%m-%d %H:%M") if dt else ""
        elif role == Qt.UserRole:
            return item.get("id", "")
        return None

    def _sort_data(self):
        self._data.sort(key=lambda x: x.get("created_at", ""), reverse=True)
