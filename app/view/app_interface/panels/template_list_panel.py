"""Template list panel — table of templates with CRUD."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHeaderView, QVBoxLayout, QWidget
from qfluentwidgets import (
    InfoBar,
    InfoBarPosition,
    StrongBodyLabel,
    TableView,
)

from app.common.signal_bus import signalBus
from app.view.app_interface.service import template_service
from app.view.app_interface.table_model.fm_template_table_model import FmTemplateTableModel


class TemplateListPanel(QWidget):
    """Content panel showing a list of templates for a project."""

    editTemplateRequested = Signal(str, str)  # template_id, project_id

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self._project_id = ""
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(8)

        self.title_label = StrongBodyLabel("Templates", self)
        layout.addWidget(self.title_label)

        self.model = FmTemplateTableModel(page_size=50)
        self.table = TableView(self)
        self.table.setModel(self.model)
        self.table.setSelectionBehavior(TableView.SelectRows)
        self.table.setSelectionMode(TableView.SingleSelection)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.doubleClicked.connect(self._on_double_click)
        layout.addWidget(self.table, 1)

    def load_templates(self, project_id: str):
        self._project_id = project_id
        data = template_service.list_templates(project_id)
        self.model.set_data(data)

    def _on_double_click(self, index):
        tmpl_id = self.model.data(index, Qt.UserRole)
        if tmpl_id:
            self.editTemplateRequested.emit(tmpl_id, self._project_id)

    def _get_selected_id(self) -> str | None:
        indexes = self.table.selectionModel().selectedRows()
        if not indexes:
            return None
        return self.model.data(indexes[0], Qt.UserRole)

    # ── Actions ──

    def on_new_template(self):
        from app.view.app_interface.dialogs.template_name_dialog import TemplateNameDialog

        dlg = TemplateNameDialog(self.window())
        if dlg.exec():
            name, desc = dlg.get_data()
            if name:
                try:
                    result = template_service.create_template(self._project_id, name, desc)
                    signalBus.dataChanged.emit()
                    self.load_templates(self._project_id)
                    # Open the editor for the new template
                    self.editTemplateRequested.emit(result["id"], self._project_id)
                except Exception as e:
                    InfoBar.error("Error", str(e), parent=self, position=InfoBarPosition.TOP)

    def on_delete_template(self):
        from qfluentwidgets import MessageBox

        tmpl_id = self._get_selected_id()
        if not tmpl_id:
            InfoBar.warning("Warning", "Select a template first", parent=self, position=InfoBarPosition.TOP)
            return
        box = MessageBox("Delete Template", "Are you sure?", self.window())
        if box.exec():
            try:
                template_service.delete_template(tmpl_id)
                signalBus.dataChanged.emit()
                self.load_templates(self._project_id)
            except ValueError as e:
                InfoBar.error("Error", str(e), parent=self, position=InfoBarPosition.TOP)
