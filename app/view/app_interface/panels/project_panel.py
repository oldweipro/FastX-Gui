"""Project overview panel — shows project stats and details."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QVBoxLayout, QWidget
from qfluentwidgets import (
    BodyLabel,
    SimpleCardWidget,
    SubtitleLabel,
    TitleLabel,
)

from app.common.notification import Notification
from app.common.signal_bus import signalBus
from app.view.app_interface.service import import_export_service, project_service, snapshot_service


class _StatCard(SimpleCardWidget):
    """Small card showing a single statistic."""

    def __init__(self, title: str, value: str, parent=None):
        super().__init__(parent=parent)
        self.setFixedSize(160, 80)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        self.value_label = SubtitleLabel(value, self)
        self.value_label.setAlignment(Qt.AlignCenter)
        self.title_label = BodyLabel(title, self)
        self.title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.value_label)
        layout.addWidget(self.title_label)

    def set_value(self, value: str):
        self.value_label.setText(value)


class ProjectPanel(QWidget):
    """Content panel shown when a project node is selected."""

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._project_id = ""
        self._workspace_id = ""
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignTop)

        self.title_label = TitleLabel("", self)
        self.desc_label = BodyLabel("", self)
        self.desc_label.setWordWrap(True)
        layout.addWidget(self.title_label)
        layout.addWidget(self.desc_label)

        # Stats row
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(12)
        self.card_templates = _StatCard("Templates", "0", self)
        self.card_items = _StatCard("Items", "0", self)
        self.card_snapshots = _StatCard("Snapshots", "0", self)
        stats_layout.addWidget(self.card_templates)
        stats_layout.addWidget(self.card_items)
        stats_layout.addWidget(self.card_snapshots)
        stats_layout.addStretch()
        layout.addLayout(stats_layout)

        # Timestamps
        self.created_label = BodyLabel("", self)
        self.updated_label = BodyLabel("", self)
        layout.addWidget(self.created_label)
        layout.addWidget(self.updated_label)
        layout.addStretch()

    def load_project(self, project_id: str):
        self._project_id = project_id
        overview = project_service.get_overview(project_id)
        if not overview:
            return

        self._workspace_id = project_service.get_project(project_id).get("workspace_id", "") if project_service.get_project(project_id) else ""

        self.title_label.setText(overview.get("name", ""))
        self.desc_label.setText(overview.get("description", "") or "No description")

        self.card_templates.set_value(str(overview.get("templates", 0)))
        self.card_items.set_value(str(overview.get("items", 0)))
        self.card_snapshots.set_value(str(overview.get("snapshots", 0)))

        created = overview.get("created_at")
        updated = overview.get("updated_at")
        self.created_label.setText(f"Created: {created.strftime('%Y-%m-%d %H:%M') if created else 'N/A'}")
        self.updated_label.setText(f"Updated: {updated.strftime('%Y-%m-%d %H:%M') if updated else 'N/A'}")

    # ── Actions ──

    def on_edit_project(self):
        from app.view.app_interface.dialogs import ProjectDialog

        proj = project_service.get_project(self._project_id)
        if proj is None:
            return
        dlg = ProjectDialog(self.window(), proj["name"], proj["description"])
        if dlg.exec():
            name, desc = dlg.get_data()
            project_service.update_project(self._project_id, name=name, description=desc)
            signalBus.dataChanged.emit()
            self.load_project(self._project_id)

    def on_delete_project(self):
        from qfluentwidgets import MessageBox

        box = MessageBox("Delete Project", "Are you sure? All data will be lost.", self.window())
        if box.exec():
            project_service.delete_project(self._project_id)
            signalBus.dataChanged.emit()

    def on_create_snapshot(self):
        from app.view.app_interface.dialogs import SnapshotDialog

        dlg = SnapshotDialog(self.window())
        if dlg.exec():
            name, desc = dlg.get_data()
            if name:
                try:
                    snapshot_service.create_snapshot(self._project_id, name, desc)
                    signalBus.dataChanged.emit()
                    self.load_project(self._project_id)
                    Notification.success("Success", "Snapshot created", parent=self)
                except Exception as e:
                    Notification.error("Error", str(e), parent=self)

    def on_export_project(self):
        path, filt = QFileDialog.getSaveFileName(
            self, "Export Project", "", "JSON Files (*.json);;Excel Files (*.xlsx)"
        )
        if not path:
            return
        try:
            if path.endswith(".xlsx"):
                import_export_service.export_project_xlsx(self._project_id, path)
            else:
                import_export_service.export_project_json(self._project_id, path)
            Notification.success("Success", f"Exported to {path}", parent=self)
        except Exception as e:
            Notification.error("Error", str(e), parent=self)
