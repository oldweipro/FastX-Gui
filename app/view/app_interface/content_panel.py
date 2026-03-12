"""Right content panel with stacked widgets and context-sensitive command bar."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QStackedWidget, QVBoxLayout, QWidget
from qfluentwidgets import (
    Action,
    CommandBar,
    SubtitleLabel,
    ToolButton, TransparentToolButton,
)
from qfluentwidgets import (
    FluentIcon as FIF,
)
from qfluentwidgets import ToolTipFilter

from app.components.main_layout_card import SeparatorWidget
from app.view.app_interface.panels.item_editor_panel import ItemEditorPanel
from app.view.app_interface.panels.item_group_panel import ItemGroupPanel
from app.view.app_interface.panels.item_list_panel import ItemListPanel
from app.view.app_interface.panels.project_panel import ProjectPanel
from app.view.app_interface.panels.snapshot_detail_panel import SnapshotDetailPanel
from app.view.app_interface.panels.snapshot_panel import SnapshotPanel
from app.view.app_interface.panels.template_editor_panel import TemplateEditorPanel
from app.view.app_interface.panels.template_list_panel import TemplateListPanel
from app.view.app_interface.panels.workspace_panel import WorkspacePanel


class ContentPanel(QWidget):
    """Right content area that shows different panels based on tree selection."""

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._current_node_type = ""
        self._current_node_id = ""
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Command bar
        self.command_bar = CommandBar(self)
        self.command_bar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        
        # 添加收缩/展开按钮到 CommandBar 左侧
        self.toggle_button = TransparentToolButton(FIF.MENU, self)
        self.toggle_button.setFixedSize(32, 32)
        self.toggle_button.setToolTip("Collapse/Expand navigation")
        self.toggle_button.installEventFilter(ToolTipFilter(self.toggle_button))
        
        # 将按钮添加到 command bar
        self.command_bar.addWidget(self.toggle_button)
        self.separator = SeparatorWidget(self)
        self.command_bar.addWidget(self.separator)
        layout.addWidget(self.command_bar)

        # Stacked widget for panels
        self.stack = QStackedWidget(self)
        layout.addWidget(self.stack, 1)

        # Welcome / empty panel
        self.welcome_panel = QWidget(self)
        welcome_layout = QVBoxLayout(self.welcome_panel)
        welcome_layout.setAlignment(Qt.AlignCenter)
        lbl = SubtitleLabel("Select a workspace or project from the tree", self.welcome_panel)
        lbl.setAlignment(Qt.AlignCenter)
        welcome_layout.addWidget(lbl)

        # Create all panels
        self.workspace_panel = WorkspacePanel(self)
        self.project_panel = ProjectPanel(self)
        self.template_list_panel = TemplateListPanel(self)
        self.template_editor_panel = TemplateEditorPanel(self)
        self.item_list_panel = ItemListPanel(self)
        self.item_editor_panel = ItemEditorPanel(self)
        self.item_group_panel = ItemGroupPanel(self)
        self.snapshot_panel = SnapshotPanel(self)
        self.snapshot_detail_panel = SnapshotDetailPanel(self)

        # Add to stack
        self.stack.addWidget(self.welcome_panel)            # 0
        self.stack.addWidget(self.workspace_panel)           # 1
        self.stack.addWidget(self.project_panel)             # 2
        self.stack.addWidget(self.template_list_panel)       # 3
        self.stack.addWidget(self.template_editor_panel)     # 4
        self.stack.addWidget(self.item_list_panel)           # 5
        self.stack.addWidget(self.item_editor_panel)         # 6
        self.stack.addWidget(self.item_group_panel)          # 7
        self.stack.addWidget(self.snapshot_panel)             # 8
        self.stack.addWidget(self.snapshot_detail_panel)      # 9

        # Connect sub-panel navigation signals
        self.template_list_panel.editTemplateRequested.connect(self._open_template_editor)
        self.item_list_panel.editItemRequested.connect(self._open_item_editor)
        self.item_group_panel.editItemRequested.connect(self._open_item_editor)

        self.stack.setCurrentWidget(self.welcome_panel)

    def on_node_selected(self, node_type: str, node_id: str, extra: dict):
        """Handle tree node selection and show the appropriate panel."""
        self._current_node_type = node_type
        self._current_node_id = node_id

        if node_type == "workspace":
            self.workspace_panel.load_workspace(node_id)
            self.stack.setCurrentWidget(self.workspace_panel)
            self._setup_command_bar_workspace(node_id)
        elif node_type == "project":
            self.project_panel.load_project(node_id)
            self.stack.setCurrentWidget(self.project_panel)
            self._setup_command_bar_project(node_id)
        elif node_type == "template_list":
            self.template_list_panel.load_templates(node_id)
            self.stack.setCurrentWidget(self.template_list_panel)
            self._setup_command_bar_templates(node_id)
        elif node_type == "template":
            project_id = extra.get("project_id", "")
            self._open_template_editor(node_id, project_id)
        elif node_type == "item_list":
            self.item_list_panel.load_items(node_id)
            self.stack.setCurrentWidget(self.item_list_panel)
            self._setup_command_bar_items(node_id)
        elif node_type == "item_group":
            project_id = extra.get("project_id", "")
            self.item_group_panel.load_group(node_id, project_id)
            self.stack.setCurrentWidget(self.item_group_panel)
            self._setup_command_bar_item_group(node_id, project_id)
        elif node_type == "item":
            project_id = extra.get("project_id", "")
            self._open_item_editor(node_id, project_id)
        elif node_type == "snapshot_list":
            self.snapshot_panel.load_snapshots(node_id)
            self.stack.setCurrentWidget(self.snapshot_panel)
            self._setup_command_bar_snapshots(node_id)
        elif node_type == "snapshot":
            project_id = extra.get("project_id", "")
            self.snapshot_detail_panel.load_snapshot(node_id)
            self.stack.setCurrentWidget(self.snapshot_detail_panel)
            self._setup_command_bar_snapshot_detail(project_id)
        else:
            self.stack.setCurrentWidget(self.welcome_panel)
            self._clear_and_add([])

    # ── Sub-panel navigation ──

    def _open_template_editor(self, template_id: str, project_id: str):
        self.template_editor_panel.load_template(template_id, project_id)
        self.stack.setCurrentWidget(self.template_editor_panel)
        self._setup_command_bar_template_editor(project_id)

    def _open_item_editor(self, item_id: str, project_id: str):
        self.item_editor_panel.load_item(item_id, project_id)
        self.stack.setCurrentWidget(self.item_editor_panel)
        self._setup_command_bar_item_editor(project_id)

    # ── Command bar setup per context ──

    def _clear_and_add(self, actions: list[Action]):
        # CommandBar has no clear() — remove all existing actions first
        for old in self.command_bar.actions():
            self.command_bar.removeAction(old)
        for a in actions:
            self.command_bar.addAction(a)

    def _setup_command_bar_workspace(self, ws_id: str):
        actions = [
            Action(FIF.ADD, "New Project", triggered=lambda: self.workspace_panel.on_new_project()),
            Action(FIF.DOWNLOAD, "Import Workspace", triggered=lambda: self.workspace_panel.on_import_workspace()),
        ]
        self._clear_and_add(actions)

    def _setup_command_bar_project(self, proj_id: str):
        actions = [
            Action(FIF.EDIT, "Edit", triggered=lambda: self.project_panel.on_edit_project()),
            Action(FIF.DELETE, "Delete", triggered=lambda: self.project_panel.on_delete_project()),
            Action(FIF.HISTORY, "Create Snapshot", triggered=lambda: self.project_panel.on_create_snapshot()),
            Action(FIF.SHARE, "Export", triggered=lambda: self.project_panel.on_export_project()),
        ]
        self._clear_and_add(actions)

    def _setup_command_bar_templates(self, proj_id: str):
        actions = [
            Action(FIF.ADD, "New Template", triggered=lambda: self.template_list_panel.on_new_template()),
            Action(FIF.DELETE, "Delete", triggered=lambda: self.template_list_panel.on_delete_template()),
        ]
        self._clear_and_add(actions)

    def _setup_command_bar_items(self, proj_id: str):
        actions = [
            Action(FIF.ADD, "New Item", triggered=lambda: self.item_list_panel.on_new_item()),
            Action(FIF.DELETE, "Delete", triggered=lambda: self.item_list_panel.on_delete_item()),
            Action(FIF.DOWNLOAD, "Import", triggered=lambda: self.item_list_panel.on_import_items()),
            Action(FIF.SHARE, "Export", triggered=lambda: self.item_list_panel.on_export_items()),
        ]
        self._clear_and_add(actions)

    def _setup_command_bar_snapshots(self, proj_id: str):
        actions = [
            Action(FIF.ADD, "Create Snapshot", triggered=lambda: self.snapshot_panel.on_create_snapshot()),
            Action(FIF.SYNC, "Restore", triggered=lambda: self.snapshot_panel.on_restore_snapshot()),
            Action(FIF.SHARE, "Export", triggered=lambda: self.snapshot_panel.on_export_snapshot()),
        ]
        self._clear_and_add(actions)

    def _setup_command_bar_item_group(self, template_id: str, project_id: str):
        actions = [
            Action(FIF.ADD, "New Item", triggered=lambda: self.item_group_panel.on_new_item()),
            Action(FIF.DELETE, "Delete", triggered=lambda: self.item_group_panel.on_delete_item()),
            Action(FIF.RETURN, "Back to Items", triggered=lambda: self._back_to_item_list(project_id)),
        ]
        self._clear_and_add(actions)

    def _setup_command_bar_snapshot_detail(self, project_id: str):
        actions = [
            Action(FIF.SYNC, "Restore", triggered=lambda: self.snapshot_detail_panel.on_restore_snapshot()),
            Action(FIF.SHARE, "Export", triggered=lambda: self.snapshot_detail_panel.on_export_snapshot()),
            Action(FIF.RETURN, "Back to Snapshots", triggered=lambda: self._back_to_snapshot_list(project_id)),
        ]
        self._clear_and_add(actions)

    def _setup_command_bar_template_editor(self, proj_id: str):
        actions = [
            Action(FIF.ADD, "Add Field", triggered=lambda: self.template_editor_panel.on_add_field()),
            Action(FIF.EDIT, "Edit Field", triggered=lambda: self.template_editor_panel.on_edit_field()),
            Action(FIF.DELETE, "Remove Field", triggered=lambda: self.template_editor_panel.on_remove_field()),
            Action(FIF.UP, "Move Up", triggered=lambda: self.template_editor_panel.on_move_up()),
            Action(FIF.DOWN, "Move Down", triggered=lambda: self.template_editor_panel.on_move_down()),
            Action(FIF.SAVE, "Save", triggered=lambda: self.template_editor_panel.on_save()),
            Action(FIF.RETURN, "Back to List", triggered=lambda: self._back_to_template_list(proj_id)),
        ]
        self._clear_and_add(actions)

    def _setup_command_bar_item_editor(self, proj_id: str):
        actions = [
            Action(FIF.SAVE, "Save", triggered=lambda: self.item_editor_panel.on_save()),
            Action(FIF.RETURN, "Back to List", triggered=lambda: self._back_to_item_list(proj_id)),
        ]
        self._clear_and_add(actions)

    def _back_to_template_list(self, project_id: str):
        self.template_list_panel.load_templates(project_id)
        self.stack.setCurrentWidget(self.template_list_panel)
        self._setup_command_bar_templates(project_id)

    def _back_to_item_list(self, project_id: str):
        self.item_list_panel.load_items(project_id)
        self.stack.setCurrentWidget(self.item_list_panel)
        self._setup_command_bar_items(project_id)

    def _back_to_snapshot_list(self, project_id: str):
        self.snapshot_panel.load_snapshots(project_id)
        self.stack.setCurrentWidget(self.snapshot_panel)
        self._setup_command_bar_snapshots(project_id)
