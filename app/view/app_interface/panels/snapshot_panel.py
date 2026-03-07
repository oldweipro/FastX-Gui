"""Snapshot panel — list of snapshots with create, restore, and export."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFileDialog, QHeaderView, QVBoxLayout, QWidget
from qfluentwidgets import (
    InfoBar,
    InfoBarPosition,
    StrongBodyLabel,
    TableView,
)

from app.common.signal_bus import signalBus
from app.service import snapshot_service
from app.table_model.fm_snapshot_table_model import FmSnapshotTableModel


class SnapshotPanel(QWidget):
    """Content panel for managing project snapshots."""

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._project_id = ""
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(8)

        self.title_label = StrongBodyLabel("Snapshots", self)
        layout.addWidget(self.title_label)

        self.model = FmSnapshotTableModel(page_size=50)
        self.table = TableView(self)
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(TableView.SelectRows)
        self.table.setSelectionMode(TableView.SingleSelection)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table, 1)

    def load_snapshots(self, project_id: str):
        self._project_id = project_id
        data = snapshot_service.list_snapshots(project_id)
        self.model.set_data(data)

    def _get_selected_id(self) -> str | None:
        indexes = self.table.selectionModel().selectedRows()
        if not indexes:
            return None
        return self.model.data(indexes[0], Qt.UserRole)

    # ── Actions ──

    def on_create_snapshot(self):
        from app.view.app_interface.dialogs import SnapshotDialog

        dlg = SnapshotDialog(self.window())
        if dlg.exec():
            name, desc = dlg.get_data()
            if name:
                try:
                    snapshot_service.create_snapshot(self._project_id, name, desc)
                    signalBus.dataChanged.emit()
                    self.load_snapshots(self._project_id)
                    InfoBar.success("Success", "Snapshot created", parent=self, position=InfoBarPosition.TOP)
                except Exception as e:
                    InfoBar.error("Error", str(e), parent=self, position=InfoBarPosition.TOP)

    def on_restore_snapshot(self):
        from qfluentwidgets import MessageBox

        snap_id = self._get_selected_id()
        if not snap_id:
            InfoBar.warning("Warning", "Select a snapshot first", parent=self, position=InfoBarPosition.TOP)
            return

        box = MessageBox(
            "Restore Snapshot",
            "This will replace ALL current templates and items. Continue?",
            self.window(),
        )
        if box.exec():
            try:
                snapshot_service.restore_snapshot(snap_id)
                signalBus.dataChanged.emit()
                InfoBar.success("Success", "Snapshot restored", parent=self, position=InfoBarPosition.TOP)
            except Exception as e:
                InfoBar.error("Error", str(e), parent=self, position=InfoBarPosition.TOP)

    def on_export_snapshot(self):
        snap_id = self._get_selected_id()
        if not snap_id:
            InfoBar.warning("Warning", "Select a snapshot first", parent=self, position=InfoBarPosition.TOP)
            return

        snap = snapshot_service.get_snapshot(snap_id)
        if snap is None:
            return

        path, _ = QFileDialog.getSaveFileName(self, "Export Snapshot", f"{snap['name']}.json", "JSON Files (*.json)")
        if path:
            import json
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(snap["snapshot_data"], f, ensure_ascii=False, indent=2, default=str)
                InfoBar.success("Success", f"Snapshot exported to {path}", parent=self, position=InfoBarPosition.TOP)
            except Exception as e:
                InfoBar.error("Error", str(e), parent=self, position=InfoBarPosition.TOP)
