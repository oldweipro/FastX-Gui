"""Snapshot detail panel -- read-only viewer for a single snapshot."""

import json

from PySide6.QtWidgets import QFileDialog, QFormLayout, QVBoxLayout, QWidget
from qfluentwidgets import (
    BodyLabel,
    InfoBar,
    InfoBarPosition,
    StrongBodyLabel,
    TextEdit,
)

from app.service import snapshot_service


class SnapshotDetailPanel(QWidget):
    """Read-only panel showing snapshot metadata and captured data."""

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._snap_id = ""
        self._snap_data: dict = {}
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(8)

        self.title_label = StrongBodyLabel("Snapshot", self)
        layout.addWidget(self.title_label)

        # Metadata area
        meta_widget = QWidget(self)
        self.meta_layout = QFormLayout(meta_widget)
        self.meta_layout.setSpacing(4)
        self.lbl_name = BodyLabel("", self)
        self.lbl_desc = BodyLabel("", self)
        self.lbl_date = BodyLabel("", self)
        self.lbl_templates = BodyLabel("", self)
        self.lbl_items = BodyLabel("", self)
        self.meta_layout.addRow("Name:", self.lbl_name)
        self.meta_layout.addRow("Description:", self.lbl_desc)
        self.meta_layout.addRow("Created:", self.lbl_date)
        self.meta_layout.addRow("Templates:", self.lbl_templates)
        self.meta_layout.addRow("Items:", self.lbl_items)
        layout.addWidget(meta_widget)

        # Data preview
        layout.addWidget(StrongBodyLabel("Data Preview", self))
        self.data_view = TextEdit(self)
        self.data_view.setReadOnly(True)
        layout.addWidget(self.data_view, 1)

    def load_snapshot(self, snap_id: str):
        self._snap_id = snap_id
        snap = snapshot_service.get_snapshot(snap_id)
        if snap is None:
            self.title_label.setText("Snapshot (not found)")
            return

        self._snap_data = snap.get("snapshot_data", {})

        self.title_label.setText(f"Snapshot: {snap['name']}")
        self.lbl_name.setText(snap.get("name", ""))
        self.lbl_desc.setText(snap.get("description", "") or "\u2014")
        dt = snap.get("created_at")
        self.lbl_date.setText(dt.strftime("%Y-%m-%d %H:%M:%S") if dt else "")

        templates = self._snap_data.get("templates", [])
        items = self._snap_data.get("items", [])
        self.lbl_templates.setText(str(len(templates)))
        self.lbl_items.setText(str(len(items)))

        # Pretty-print the snapshot data
        try:
            preview = json.dumps(self._snap_data, indent=2, ensure_ascii=False, default=str)
        except (TypeError, ValueError):
            preview = str(self._snap_data)
        self.data_view.setPlainText(preview)

    # -- Actions (called from command bar) --

    def on_export_snapshot(self):
        if not self._snap_id:
            return
        snap = snapshot_service.get_snapshot(self._snap_id)
        if snap is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Snapshot", f"{snap['name']}.json", "JSON Files (*.json)"
        )
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(snap["snapshot_data"], f, ensure_ascii=False, indent=2, default=str)
                InfoBar.success("Success", f"Exported to {path}", parent=self, position=InfoBarPosition.TOP)
            except Exception as e:
                InfoBar.error("Error", str(e), parent=self, position=InfoBarPosition.TOP)

    def on_restore_snapshot(self):
        from qfluentwidgets import MessageBox

        if not self._snap_id:
            return
        box = MessageBox(
            "Restore Snapshot",
            "This will replace ALL current templates and items. Continue?",
            self.window(),
        )
        if box.exec():
            try:
                snapshot_service.restore_snapshot(self._snap_id)
                from app.common.signal_bus import signalBus
                signalBus.dataChanged.emit()
                InfoBar.success("Success", "Snapshot restored", parent=self, position=InfoBarPosition.TOP)
            except Exception as e:
                InfoBar.error("Error", str(e), parent=self, position=InfoBarPosition.TOP)
