"""Workspace detail panel — shows workspace info and project cards."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFileDialog, QGridLayout, QVBoxLayout, QWidget
from qfluentwidgets import (
    BodyLabel,
    ElevatedCardWidget,
    InfoBar,
    InfoBarPosition,
    StrongBodyLabel,
    TitleLabel,
)

from app.common.signal_bus import signalBus
from app.view.app_interface.service import import_export_service, project_service, workspace_service


class _ProjectCard(ElevatedCardWidget):
    """Card representing a single project within the workspace panel."""

    def __init__(self, project: dict, parent=None):
        super().__init__(parent=parent)
        self.project = project
        self.setFixedSize(240, 130)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)

        name = StrongBodyLabel(project["name"], self)
        desc = BodyLabel(project.get("description", "") or "No description", self)
        desc.setWordWrap(True)

        stats = BodyLabel(
            f"Templates: {project.get('templates', 0)}  |  Items: {project.get('items', 0)}",
            self,
        )

        layout.addWidget(name)
        layout.addWidget(desc, 1)
        layout.addWidget(stats)


class WorkspacePanel(QWidget):
    """Content panel shown when a workspace node is selected."""

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._workspace_id = ""
        self._init_ui()

    def _init_ui(self):
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(16, 8, 16, 8)
        self._layout.setSpacing(12)
        self._layout.setAlignment(Qt.AlignTop)

        self.title_label = TitleLabel("", self)
        self.desc_label = BodyLabel("", self)
        self.desc_label.setWordWrap(True)
        self._layout.addWidget(self.title_label)
        self._layout.addWidget(self.desc_label)

        # Project cards container
        self.cards_container = QWidget(self)
        self.cards_layout = QGridLayout(self.cards_container)
        self.cards_layout.setSpacing(12)
        self.cards_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self._layout.addWidget(self.cards_container, 1)

    def load_workspace(self, workspace_id: str):
        self._workspace_id = workspace_id
        ws = workspace_service.get_workspace(workspace_id)
        if ws is None:
            return

        self.title_label.setText(ws["name"])
        self.desc_label.setText(ws.get("description", ""))

        # Clear old cards
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Load project cards
        projects = project_service.list_projects(workspace_id)
        cols = 3
        for i, proj in enumerate(projects):
            card = _ProjectCard(proj, self.cards_container)
            self.cards_layout.addWidget(card, i // cols, i % cols)

    # ── Actions ──

    def on_new_project(self):
        from app.view.app_interface.dialogs import ProjectDialog

        dlg = ProjectDialog(self.window())
        if dlg.exec():
            name, desc = dlg.get_data()
            if name:
                try:
                    project_service.create_project(self._workspace_id, name, desc)
                    signalBus.dataChanged.emit()
                    self.load_workspace(self._workspace_id)
                except Exception as e:
                    InfoBar.error("Error", str(e), parent=self, position=InfoBarPosition.TOP)

    def on_import_workspace(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import Workspace", "", "JSON Files (*.json)")
        if path:
            try:
                import_export_service.import_project_json(self._workspace_id, path)
                signalBus.dataChanged.emit()
                self.load_workspace(self._workspace_id)
                InfoBar.success("Success", "Workspace imported", parent=self, position=InfoBarPosition.TOP)
            except Exception as e:
                InfoBar.error("Error", str(e), parent=self, position=InfoBarPosition.TOP)
