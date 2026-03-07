"""Item list panel — table of items with template filter, CRUD."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QHeaderView, QVBoxLayout, QWidget
from qfluentwidgets import (
    ComboBox,
    InfoBar,
    InfoBarPosition,
    StrongBodyLabel,
    TableView,
)

from app.common.signal_bus import signalBus
from app.service import import_export_service, item_service, template_service
from app.table_model.fm_item_table_model import FmItemTableModel


class ItemListPanel(QWidget):
    """Content panel showing items for a project, with optional template filter."""

    editItemRequested = Signal(str, str)  # item_id, project_id

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._project_id = ""
        self._template_map: dict[str, str] = {}  # template_id -> name
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(8)

        # Header row with filter
        header = QHBoxLayout()
        self.title_label = StrongBodyLabel("Items", self)
        header.addWidget(self.title_label)
        header.addStretch()
        header.addWidget(StrongBodyLabel("Template:", self))
        self.template_filter = ComboBox(self)
        self.template_filter.setMinimumWidth(180)
        self.template_filter.currentIndexChanged.connect(self._on_filter_changed)
        header.addWidget(self.template_filter)
        layout.addLayout(header)

        # Table
        self.model = FmItemTableModel(page_size=50)
        self.table = TableView(self)
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(TableView.SelectRows)
        self.table.setSelectionMode(TableView.SingleSelection)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.doubleClicked.connect(self._on_double_click)
        layout.addWidget(self.table, 1)

    def load_items(self, project_id: str):
        self._project_id = project_id
        # Populate template filter
        templates = template_service.list_templates(project_id)
        self._template_map = {t["id"]: t["name"] for t in templates}

        self.template_filter.blockSignals(True)
        self.template_filter.clear()
        self.template_filter.addItem("All Templates", userData="")
        for t in templates:
            self.template_filter.addItem(t["name"], userData=t["id"])
        self.template_filter.blockSignals(False)

        self._reload_items()

    def _reload_items(self):
        tmpl_id = self.template_filter.currentData()
        items = item_service.list_items(self._project_id, template_id=tmpl_id if tmpl_id else None)
        # Enrich with template name
        for item in items:
            item["template_name"] = self._template_map.get(item.get("template_id", ""), "")
        self.model.set_data(items)

    def _on_filter_changed(self, index):
        self._reload_items()

    def _on_double_click(self, index):
        item_id = self.model.data(index, Qt.UserRole)
        if item_id:
            self.editItemRequested.emit(item_id, self._project_id)

    def _get_selected_id(self) -> str | None:
        indexes = self.table.selectionModel().selectedRows()
        if not indexes:
            return None
        return self.model.data(indexes[0], Qt.UserRole)

    # ── Actions ──

    def on_new_item(self):
        from app.view.app_interface.dialogs.item_create_dialog import ItemCreateDialog

        templates = template_service.list_templates(self._project_id)
        if not templates:
            InfoBar.warning("Warning", "Create a template first", parent=self, position=InfoBarPosition.TOP)
            return
        dlg = ItemCreateDialog(templates, self.window())
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
                    self._reload_items()
                    self.editItemRequested.emit(result["id"], self._project_id)
                except Exception as e:
                    InfoBar.error("Error", str(e), parent=self, position=InfoBarPosition.TOP)

    def on_delete_item(self):
        from qfluentwidgets import MessageBox

        item_id = self._get_selected_id()
        if not item_id:
            InfoBar.warning("Warning", "Select an item first", parent=self, position=InfoBarPosition.TOP)
            return
        box = MessageBox("Delete Item", "Are you sure?", self.window())
        if box.exec():
            item_service.delete_item(item_id)
            signalBus.dataChanged.emit()
            self._reload_items()

    def on_import_items(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import Items", "", "JSON Files (*.json);;Excel Files (*.xlsx)")
        if path:
            try:
                if path.endswith(".xlsx"):
                    import_export_service.import_project_xlsx(self._project_id, path)
                else:
                    # Determine workspace_id from project
                    from app.service import project_service
                    proj = project_service.get_project(self._project_id)
                    ws_id = proj["workspace_id"] if proj else ""
                    import_export_service.import_project_json(ws_id, path)
                signalBus.dataChanged.emit()
                self._reload_items()
                InfoBar.success("Success", "Import complete", parent=self, position=InfoBarPosition.TOP)
            except Exception as e:
                InfoBar.error("Error", str(e), parent=self, position=InfoBarPosition.TOP)

    def on_export_items(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Items", "", "JSON Files (*.json);;Excel Files (*.xlsx)"
        )
        if path:
            try:
                if path.endswith(".xlsx"):
                    import_export_service.export_project_xlsx(self._project_id, path)
                else:
                    import_export_service.export_project_json(self._project_id, path)
                InfoBar.success("Success", f"Exported to {path}", parent=self, position=InfoBarPosition.TOP)
            except Exception as e:
                InfoBar.error("Error", str(e), parent=self, position=InfoBarPosition.TOP)
