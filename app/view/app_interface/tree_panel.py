"""Left tree navigation panel with search, hierarchical nodes, and context menus."""

from collections import defaultdict

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QMenu, QTreeWidgetItem, QVBoxLayout, QWidget
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import SearchLineEdit, TransparentToolButton, TreeWidget

from app.common.signal_bus import signalBus
from app.service import item_service, project_service, snapshot_service, template_service, workspace_service


class TreePanel(QWidget):
    """Left panel: hierarchy tree with toolbar and search."""

    # Emitted when a tree node is selected: (node_type, entity_id, extra_data)
    nodeSelected = Signal(str, str, dict)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._init_ui()
        self._connect_signals()
        self.refresh_tree()

    # ── UI setup ─────────────────────────────────────────────────

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 4, 8)
        layout.setSpacing(4)

        # Toolbar
        toolbar_layout = self._build_toolbar()
        layout.addLayout(toolbar_layout)

        # Search
        self.search_edit = SearchLineEdit(self)
        self.search_edit.setPlaceholderText("Search...")
        layout.addWidget(self.search_edit)

        # Tree
        self.tree = TreeWidget(self)
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(20)
        self.tree.setAnimated(True)
        self.tree.setExpandsOnDoubleClick(True)
        layout.addWidget(self.tree, 1)

    def _build_toolbar(self):
        from PySide6.QtWidgets import QHBoxLayout

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
        return toolbar

    def _connect_signals(self):
        self.btn_add_workspace.clicked.connect(self._on_add_workspace)
        self.btn_refresh.clicked.connect(self.refresh_tree)
        self.btn_collapse.clicked.connect(self.tree.collapseAll)
        self.tree.itemClicked.connect(self._on_item_clicked)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._on_context_menu)
        self.search_edit.textChanged.connect(self._on_search_changed)
        signalBus.dataChanged.connect(self.refresh_tree)

    # ── Tree build ───────────────────────────────────────────────

    def refresh_tree(self):
        """Reload the full tree from the database."""
        expanded = self._save_expanded_state()
        self.tree.clear()

        for ws in workspace_service.list_workspaces():
            ws_item = self._make_node(ws["name"], FIF.FOLDER, "workspace", ws["id"])

            for proj in project_service.list_projects(ws["id"]):
                proj_id = proj["id"]
                proj_item = self._make_node(proj["name"], FIF.DOCUMENT, "project", proj_id, ws["id"])

                # ── Templates ──
                tmpl_list_node = self._make_node("Templates", FIF.LABEL, "template_list", proj_id, ws["id"])
                for t in template_service.list_templates(proj_id):
                    tmpl_list_node.addChild(
                        self._make_node(t["name"], FIF.DOCUMENT, "template", t["id"], proj_id)
                    )
                proj_item.addChild(tmpl_list_node)

                # ── Items (grouped by template) ──
                item_list_node = self._make_node("Items", FIF.EDIT, "item_list", proj_id, ws["id"])
                all_items = item_service.list_items(proj_id)
                groups: dict[str, list[dict]] = defaultdict(list)
                for it in all_items:
                    groups[it.get("template_id", "")].append(it)

                tmpl_name_map = {t["id"]: t["name"] for t in template_service.list_templates(proj_id)}
                for tmpl_id, items in groups.items():
                    group_name = tmpl_name_map.get(tmpl_id, tmpl_id[:8])
                    group_node = self._make_node(
                        f"{group_name}s ({len(items)})", FIF.EDIT, "item_group", tmpl_id, proj_id
                    )
                    for it in items:
                        group_node.addChild(
                            self._make_node(it["title"], FIF.EDIT, "item", it["id"], proj_id)
                        )
                    item_list_node.addChild(group_node)
                proj_item.addChild(item_list_node)

                # ── Snapshots ──
                snap_list_node = self._make_node("Snapshots", FIF.HISTORY, "snapshot_list", proj_id, ws["id"])
                for s in snapshot_service.list_snapshots(proj_id):
                    date_str = ""
                    if s.get("created_at"):
                        date_str = s["created_at"].strftime("%Y-%m-%d")
                    snap_list_node.addChild(
                        self._make_node(
                            f"{s['name']} ({date_str})" if date_str else s["name"],
                            FIF.HISTORY, "snapshot", s["id"], proj_id,
                        )
                    )
                proj_item.addChild(snap_list_node)

                ws_item.addChild(proj_item)
            self.tree.addTopLevelItem(ws_item)

        self._restore_expanded_state(expanded)

        # Re-apply search filter if active
        text = self.search_edit.text().strip()
        if text:
            self._apply_search_filter(text)

    @staticmethod
    def _make_node(text: str, icon, node_type: str, node_id: str, extra_id: str = "") -> QTreeWidgetItem:
        """Create a tree item with standard data roles."""
        item = QTreeWidgetItem([text])
        item.setIcon(0, icon.icon())
        item.setData(0, Qt.UserRole, node_type)
        item.setData(0, Qt.UserRole + 1, node_id)
        item.setData(0, Qt.UserRole + 2, extra_id)
        return item

    # ── Expanded state ───────────────────────────────────────────

    def _save_expanded_state(self) -> set[tuple[str, str]]:
        """Recursively collect (node_type, node_id) for all expanded nodes."""
        result: set[tuple[str, str]] = set()
        for i in range(self.tree.topLevelItemCount()):
            self._collect_expanded(self.tree.topLevelItem(i), result)
        return result

    def _collect_expanded(self, item: QTreeWidgetItem, out: set[tuple[str, str]]):
        if item.isExpanded():
            ntype = item.data(0, Qt.UserRole) or ""
            nid = item.data(0, Qt.UserRole + 1) or ""
            out.add((ntype, nid))
        for i in range(item.childCount()):
            self._collect_expanded(item.child(i), out)

    def _restore_expanded_state(self, expanded: set[tuple[str, str]]):
        for i in range(self.tree.topLevelItemCount()):
            self._apply_expanded(self.tree.topLevelItem(i), expanded)

    def _apply_expanded(self, item: QTreeWidgetItem, expanded: set[tuple[str, str]]):
        key = (item.data(0, Qt.UserRole) or "", item.data(0, Qt.UserRole + 1) or "")
        if key in expanded:
            item.setExpanded(True)
        for i in range(item.childCount()):
            self._apply_expanded(item.child(i), expanded)

    # ── Search / filter ──────────────────────────────────────────

    def _on_search_changed(self, text: str):
        text = text.strip()
        if not text:
            # Show all
            for i in range(self.tree.topLevelItemCount()):
                self._set_visible_recursive(self.tree.topLevelItem(i), True)
            return
        self._apply_search_filter(text)

    def _apply_search_filter(self, text: str):
        for i in range(self.tree.topLevelItemCount()):
            self._filter_item(self.tree.topLevelItem(i), text.lower())

    def _filter_item(self, item: QTreeWidgetItem, text: str) -> bool:
        """Returns True if this item or any descendant matches *text*."""
        matches = text in item.text(0).lower()
        child_matches = False
        for i in range(item.childCount()):
            if self._filter_item(item.child(i), text):
                child_matches = True
        visible = matches or child_matches
        item.setHidden(not visible)
        if child_matches:
            item.setExpanded(True)
        return visible

    @staticmethod
    def _set_visible_recursive(item: QTreeWidgetItem, visible: bool):
        item.setHidden(not visible)
        for i in range(item.childCount()):
            TreePanel._set_visible_recursive(item.child(i), visible)

    # ── Click handling ───────────────────────────────────────────

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int):
        node_type = item.data(0, Qt.UserRole) or ""
        node_id = item.data(0, Qt.UserRole + 1) or ""
        extra_id = item.data(0, Qt.UserRole + 2) or ""
        extra: dict = {}
        if extra_id:
            # extra_id is project_id for most child nodes, workspace_id for project/virtual nodes
            if node_type in ("template", "item_group", "item", "snapshot"):
                extra["project_id"] = extra_id
            else:
                extra["workspace_id"] = extra_id
        self.nodeSelected.emit(node_type, node_id, extra)

    # ── Context menus ────────────────────────────────────────────

    def _on_context_menu(self, pos):
        item = self.tree.itemAt(pos)
        if item is None:
            return

        node_type = item.data(0, Qt.UserRole)
        node_id = item.data(0, Qt.UserRole + 1)
        extra_id = item.data(0, Qt.UserRole + 2) or ""
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
        elif node_type == "template":
            menu.addAction("Edit Template", lambda: self.nodeSelected.emit("template", node_id, {"project_id": extra_id}))
            menu.addAction("Delete Template", lambda: self._ctx_delete_template(node_id))
        elif node_type == "item_list":
            menu.addAction("New Item", lambda: self._ctx_new_item(node_id))
        elif node_type == "item_group":
            menu.addAction("New Item", lambda: self._ctx_new_item_for_group(extra_id, node_id))
        elif node_type == "item":
            menu.addAction("Edit Item", lambda: self.nodeSelected.emit("item", node_id, {"project_id": extra_id}))
            menu.addAction("Delete Item", lambda: self._ctx_delete_item(node_id))
        elif node_type == "snapshot_list":
            menu.addAction("Create Snapshot", lambda: self._ctx_create_snapshot(node_id))
        elif node_type == "snapshot":
            menu.addAction("View Snapshot", lambda: self.nodeSelected.emit("snapshot", node_id, {"project_id": extra_id}))
            menu.addAction("Delete Snapshot", lambda: self._ctx_delete_snapshot(node_id))
        else:
            return

        menu.exec(self.tree.viewport().mapToGlobal(pos))

    # ── Context menu action implementations ──────────────────────

    def _on_add_workspace(self):
        from app.view.app_interface.dialogs import WorkspaceDialog

        dlg = WorkspaceDialog(self.window())
        if dlg.exec():
            name, desc = dlg.get_data()
            if name:
                workspace_service.create_workspace(name, desc)
                signalBus.dataChanged.emit()

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

        box = MessageBox("Delete Project", "Are you sure? All data will be deleted.", self.window())
        if box.exec():
            project_service.delete_project(proj_id)
            signalBus.dataChanged.emit()

    def _ctx_create_snapshot(self, project_id: str):
        from app.view.app_interface.dialogs import SnapshotDialog

        dlg = SnapshotDialog(self.window())
        if dlg.exec():
            name, desc = dlg.get_data()
            if name:
                snapshot_service.create_snapshot(project_id, name, desc)
                signalBus.dataChanged.emit()

    def _ctx_new_template(self, project_id: str):
        from app.view.app_interface.dialogs.template_name_dialog import TemplateNameDialog

        dlg = TemplateNameDialog(self.window())
        if dlg.exec():
            name, desc = dlg.get_data()
            if name:
                result = template_service.create_template(project_id, name, desc)
                signalBus.dataChanged.emit()
                self.nodeSelected.emit("template", result["id"], {"project_id": project_id})

    def _ctx_delete_template(self, tmpl_id: str):
        from qfluentwidgets import MessageBox

        box = MessageBox("Delete Template", "Are you sure?", self.window())
        if box.exec():
            try:
                template_service.delete_template(tmpl_id)
                signalBus.dataChanged.emit()
            except ValueError:
                pass  # items still reference it — silently fail (panel shows error)

    def _ctx_new_item(self, project_id: str):
        from app.view.app_interface.dialogs.item_create_dialog import ItemCreateDialog

        templates = template_service.list_templates(project_id)
        if not templates:
            return
        dlg = ItemCreateDialog(templates, self.window())
        if dlg.exec():
            data = dlg.get_data()
            if data:
                result = item_service.create_item(
                    project_id=project_id,
                    template_id=data["template_id"],
                    title=data["title"],
                )
                signalBus.dataChanged.emit()
                self.nodeSelected.emit("item", result["id"], {"project_id": project_id})

    def _ctx_new_item_for_group(self, project_id: str, template_id: str):
        from app.view.app_interface.dialogs.item_create_dialog import ItemCreateDialog

        templates = template_service.list_templates(project_id)
        if not templates:
            return
        dlg = ItemCreateDialog(templates, self.window(), default_template_id=template_id)
        if dlg.exec():
            data = dlg.get_data()
            if data:
                result = item_service.create_item(
                    project_id=project_id,
                    template_id=data["template_id"],
                    title=data["title"],
                )
                signalBus.dataChanged.emit()
                self.nodeSelected.emit("item", result["id"], {"project_id": project_id})

    def _ctx_delete_item(self, item_id: str):
        from qfluentwidgets import MessageBox

        box = MessageBox("Delete Item", "Are you sure?", self.window())
        if box.exec():
            item_service.delete_item(item_id)
            signalBus.dataChanged.emit()

    def _ctx_delete_snapshot(self, snap_id: str):
        from qfluentwidgets import MessageBox

        box = MessageBox("Delete Snapshot", "Are you sure?", self.window())
        if box.exec():
            snapshot_service.delete_snapshot(snap_id)
            signalBus.dataChanged.emit()
