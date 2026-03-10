from typing import Any

from PySide6.QtCore import QModelIndex, Qt

from app.view.app_interface.table_model.base_table_model import BaseTableModel

_EMPTY = QModelIndex()


class FmSnapshotTableModel(BaseTableModel):
    """Table model for snapshot listing in the fault management system."""

    HEADERS = ["Name", "Description", "Created At", "Size"]

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
                return item.get("name", "")
            if col == 1:
                return item.get("description", "")
            if col == 2:
                dt = item.get("created_at")
                return dt.strftime("%Y-%m-%d %H:%M") if dt else ""
            if col == 3:
                size = item.get("data_size", 0)
                if size < 1024:
                    return f"{size} B"
                return f"{size / 1024:.1f} KB"
        elif role == Qt.TextAlignmentRole:
            if index.column() == 3:
                return Qt.AlignRight | Qt.AlignVCenter
        elif role == Qt.UserRole:
            return item.get("id", "")
        return None

    def _sort_data(self):
        self._data.sort(key=lambda x: x.get("created_at", ""), reverse=True)
