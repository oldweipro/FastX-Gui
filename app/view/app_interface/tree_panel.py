"""Left tree navigation panel."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QTreeWidgetItem, QVBoxLayout, QWidget
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import TransparentToolButton, TreeWidget

from app.common.signal_bus import signalBus
from app.service import project_service, workspace_service


class TreePanel(QWidget):
    """Left panel: hierarchy tree with toolbar."""

    # Emitted when a tree node is selected: (node_type, entity_id, extra_data)
    nodeSelected = Signal(str, str, dict)

    NODE_TYPE = "node_type"
    NODE_ID = "node_id"

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._init_ui()
        self._connect_signals()
        self.refresh_tree()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 4, 8)
        layout.setSpacing(4)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(2)
        self.btn_add_workspace = TransparentToolButton(FIF.ADD, self)
        self.btn_add_workspace.setToolTip("New Workspace")
        self.btn_refresh = TransparentToolButton(FIF.SYNC, self)
        self.btn_refresh.setToolTip("Refresh")
        self.btn_collapse = TransparentToolButton(FIF.MINIMIZE, self)
        self.btn_collapse.setToolTip("Collapse All")
        toolbar.addWidget(self.btn_add_workspace)
        toolbar.addWidget(self.btn_refresh)
        toolbar.addWidget(self.btn_collapse)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Tree
        self.tree = TreeWidget(self)
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(20)
        self.tree.setAnimated(True)
        self.tree.setExpandsOnDoubleClick(True)
        layout.addWidget(self.tree, 1)

    def _connect_signals(self):
        self.btn_add_workspace.clicked.connect(self._on_add_workspace)
        self.btn_refresh.clicked.connect(self.refresh_tree)
        self.btn_collapse.clicked.connect(self.tree.collapseAll)
        self.tree.itemClicked.connect(self._on_item_clicked)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._on_context_menu)
        signalBus.dataChanged.connect(self.refresh_tree)

    def refresh_tree(self):
        """Reload the full tree from the database."""
        # Save expanded state
        expanded_ids = set()
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            if item.isExpanded():
                expanded_ids.add(item.data(0, Qt.UserRole + 1))
            for j in range(item.childCount()):
                child = item.child(j)
                if child.isExpanded():
                    expanded_ids.add(child.data(0, Qt.UserRole + 1))

        self.tree.clear()
        workspaces = workspace_service.list_workspaces()

        for ws in workspaces:
            ws_item = QTreeWidgetItem([ws["name"]])
            ws_item.setIcon(0, FIF.FOLDER.icon())
            ws_item.setData(0, Qt.UserRole, "workspace")
            ws_item.setData(0, Qt.UserRole + 1, ws["id"])

            projects = project_service.list_projects(ws["id"])
            for proj in projects:
                proj_item = QTreeWidgetItem([proj["name"]])
                proj_item.setIcon(0, FIF.DOCUMENT.icon())
                proj_item.setData(0, Qt.UserRole, "project")
                proj_item.setData(0, Qt.UserRole + 1, proj["id"])
                proj_item.setData(0, Qt.UserRole + 2, ws["id"])  # parent workspace id

                # Virtual child nodes
                for label, icon, ntype in [
                    ("Templates", FIF.LABEL, "template_list"),
                    ("Items", FIF.EDIT, "item_list"),
                    ("Snapshots", FIF.HISTORY, "snapshot_list"),
                ]:
                    child = QTreeWidgetItem([label])
                    child.setIcon(0, icon.icon())
                    child.setData(0, Qt.UserRole, ntype)
                    child.setData(0, Qt.UserRole + 1, proj["id"])  # project_id
                    child.setData(0, Qt.UserRole + 2, ws["id"])  # workspace_id
                    proj_item.addChild(child)

                ws_item.addChild(proj_item)

            self.tree.addTopLevelItem(ws_item)

            # Restore expanded state
            if ws["id"] in expanded_ids:
                ws_item.setExpanded(True)
                for j in range(ws_item.childCount()):
                    child = ws_item.child(j)
                    if child.data(0, Qt.UserRole + 1) in expanded_ids:
                        child.setExpanded(True)

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int):
        node_type = item.data(0, Qt.UserRole)
        node_id = item.data(0, Qt.UserRole + 1) or ""
        extra = {}
        workspace_id = item.data(0, Qt.UserRole + 2)
        if workspace_id:
            extra["workspace_id"] = workspace_id
        self.nodeSelected.emit(node_type, node_id, extra)

    def _on_add_workspace(self):
        from app.view.app_interface.dialogs import WorkspaceDialog

        dlg = WorkspaceDialog(self.window())
        if dlg.exec():
            name, desc = dlg.get_data()
            if name:
                workspace_service.create_workspace(name, desc)
                signalBus.dataChanged.emit()

    def _on_context_menu(self, pos):
        from PySide6.QtWidgets import QMenu


        item = self.tree.itemAt(pos)
        if item is None:
            return

        node_type = item.data(0, Qt.UserRole)
        node_id = item.data(0, Qt.UserRole + 1)
        menu = QMenu(self)

        if node_type == "workspace":
            menu.addAction("New Project", lambda: self._ctx_new_project(node_id))
            menu.addAction("Edit Workspace", lambda: self._ctx_edit_workspace(node_id))
            menu.addAction("Delete Workspace", lambda: self._ctx_delete_workspace(node_id))
        elif node_type == "project":
            menu.addAction("Edit Project", lambda: self._ctx_edit_project(node_id))
            menu.addAction("Delete Project", lambda: self._ctx_delete_project(node_id))
            menu.addAction("Create Snapshot", lambda: self._ctx_create_snapshot(node_id))
        elif node_type == "template_list":
            menu.addAction("New Template", lambda: self._ctx_new_template(node_id))
        elif node_type == "item_list":
            menu.addAction("New Item", lambda: self._ctx_new_item(node_id))
        elif node_type == "snapshot_list":
            menu.addAction("Create Snapshot", lambda: self._ctx_create_snapshot(node_id))
        else:
            return

        menu.exec(self.tree.viewport().mapToGlobal(pos))

    # ── Context menu actions ──

    def _ctx_new_project(self, workspace_id: str):
        from app.view.app_interface.dialogs import ProjectDialog

        dlg = ProjectDialog(self.window())
        if dlg.exec():
            name, desc = dlg.get_data()
            if name:
                project_service.create_project(workspace_id, name, desc)
                signalBus.dataChanged.emit()

    def _ctx_edit_workspace(self, ws_id: str):
        from app.view.app_interface.dialogs import WorkspaceDialog

        ws = workspace_service.get_workspace(ws_id)
        if ws is None:
            return
        dlg = WorkspaceDialog(self.window(), ws["name"], ws["description"])
        if dlg.exec():
            name, desc = dlg.get_data()
            workspace_service.update_workspace(ws_id, name=name, description=desc)
            signalBus.dataChanged.emit()

    def _ctx_delete_workspace(self, ws_id: str):
        from qfluentwidgets import MessageBox

        box = MessageBox("Delete Workspace", "Are you sure? All projects within will be deleted.", self.window())
        if box.exec():
            workspace_service.delete_workspace(ws_id)
            signalBus.dataChanged.emit()

    def _ctx_edit_project(self, proj_id: str):
        from app.view.app_interface.dialogs import ProjectDialog

        proj = project_service.get_project(proj_id)
        if proj is None:
            return
        dlg = ProjectDialog(self.window(), proj["name"], proj["description"])
        if dlg.exec():
            name, desc = dlg.get_data()
            project_service.update_project(proj_id, name=name, description=desc)
            signalBus.dataChanged.emit()

    def _ctx_delete_project(self, proj_id: str):
        from qfluentwidgets import MessageBox

        box = MessageBox("Delete Project", "Are you sure? All templates, items, and snapshots will be deleted.", self.window())
        if box.exec():
            project_service.delete_project(proj_id)
            signalBus.dataChanged.emit()

    def _ctx_create_snapshot(self, project_id: str):
        from app.service import snapshot_service
        from app.view.app_interface.dialogs import SnapshotDialog

        dlg = SnapshotDialog(self.window())
        if dlg.exec():
            name, desc = dlg.get_data()
            if name:
                snapshot_service.create_snapshot(project_id, name, desc)
                signalBus.dataChanged.emit()

    def _ctx_new_template(self, project_id: str):
        """Emit selection to navigate to template list panel which has creation UI."""
        self.nodeSelected.emit("template_list", project_id, {})

    def _ctx_new_item(self, project_id: str):
        """Emit selection to navigate to item list panel which has creation UI."""
        self.nodeSelected.emit("item_list", project_id, {})
