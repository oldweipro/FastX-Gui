from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, 
                               QPushButton, QDialog, QLineEdit, QTextEdit, QFormLayout, 
                               QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QFrame)
from qfluentwidgets import (
    FluentIcon as FIF,
    PrimaryPushButton,
    PushButton,
    Dialog,
    LineEdit,
    TextEdit,
    SubtitleLabel,
    BodyLabel,
    ElevatedCardWidget,
    ScrollArea,
    MessageBoxBase,
    TableWidget,
    ComboBox
)

from app.model.fault_model import FaultManager, Project


class ProjectEditorDialog(MessageBoxBase):
    """项目编辑器对话框"""
    def __init__(self, project: Project = None, parent=None):
        title = self.tr("编辑项目") if project else self.tr("新建项目")
        super().__init__(parent)
        self.setWindowTitle(title)
        self.project = project or Project("", "")
        
        # 标题
        self.titleLabel = SubtitleLabel(title, self)
        self.viewLayout.addWidget(self.titleLabel)

        # 创建滚动区域
        self.scrollArea = ScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setFrameShape(QFrame.Shape.NoFrame)          # 去除边框
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # 设置滚动区域背景透明
        self.scrollArea.setStyleSheet("ScrollArea { background: transparent; border: none; }")
        self.scrollArea.viewport().setStyleSheet("background: transparent;")

        # 滚动区域的内容容器及其布局
        self.scrollWidget = QWidget()
        self.scrollLayout = QVBoxLayout(self.scrollWidget)
        self.scrollLayout.setSpacing(12)                       # 与 viewLayout 默认间距一致
        self.scrollLayout.setContentsMargins(0, 0, 20, 0)       # 边距由外层 viewLayout 控制

        # 项目名称
        self.nameEdit = LineEdit(self.scrollWidget)
        self.nameEdit.setText(self.project.name)
        
        # 项目描述
        self.descriptionEdit = TextEdit(self.scrollWidget)
        self.descriptionEdit.setText(self.project.description)
        
        # 布局
        layout = QFormLayout()
        layout.addRow(self.tr("项目名称:"), self.nameEdit)
        layout.addRow(self.tr("项目描述:"), self.descriptionEdit)
        self.scrollLayout.addLayout(layout)

        # 将内容容器设置到滚动区域
        self.scrollArea.setWidget(self.scrollWidget)
        # 将滚动区域添加到主布局（标题下方）
        self.viewLayout.addWidget(self.scrollArea)

        # 设置按钮文本
        self.yesButton.setText("保存")
        self.cancelButton.setText("取消")
        self.widget.setMinimumWidth(600)
    
    def get_project(self) -> Project:
        """获取编辑后的项目"""
        self.project.name = self.nameEdit.text()
        self.project.description = self.descriptionEdit.toPlainText()
        return self.project


class ProjectManagerUI(QWidget):
    """项目管理界面"""
    def __init__(self, fault_manager: FaultManager, parent=None):
        super().__init__(parent)
        self.fault_manager = fault_manager
        self._init_ui()
    
    def _init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        
        # 标题
        layout.addWidget(SubtitleLabel(self.tr("项目管理"), self))
        
        # 操作按钮
        button_layout = QHBoxLayout()
        self.addProjectButton = PrimaryPushButton(FIF.ADD, self.tr("新建项目"), self)
        self.editProjectButton = PushButton(FIF.EDIT, self.tr("编辑项目"), self)
        self.deleteProjectButton = PushButton(FIF.DELETE, self.tr("删除项目"), self)
        button_layout.addWidget(self.addProjectButton)
        button_layout.addWidget(self.editProjectButton)
        button_layout.addWidget(self.deleteProjectButton)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # 项目列表
        self.projectTable = TableWidget(self)
        self.projectTable.setColumnCount(3)
        self.projectTable.setHorizontalHeaderLabels([self.tr("名称"), self.tr("描述"), self.tr("条目数量")])
        self.projectTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.projectTable)
        
        # 项目详情
        self.detailCard = ElevatedCardWidget(self)
        detail_layout = QVBoxLayout(self.detailCard)
        
        self.detailTitle = SubtitleLabel(self.tr("项目详情"), self)
        detail_layout.addWidget(self.detailTitle)
        
        self.detailContent = BodyLabel(self.tr("请选择一个项目查看详情"), self)
        self.detailContent.setWordWrap(True)
        detail_layout.addWidget(self.detailContent)
        
        # 项目条目列表
        self.itemsCard = ElevatedCardWidget(self)
        items_layout = QVBoxLayout(self.itemsCard)
        
        self.itemsTitle = SubtitleLabel(self.tr("项目条目"), self)
        items_layout.addWidget(self.itemsTitle)
        
        self.itemsTable = QTableWidget(self)
        self.itemsTable.setColumnCount(3)
        self.itemsTable.setHorizontalHeaderLabels([self.tr("标题"), self.tr("模板"), self.tr("创建时间")])
        self.itemsTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        items_layout.addWidget(self.itemsTable)
        
        # 项目模板集合
        self.templatesCard = ElevatedCardWidget(self)
        templates_layout = QVBoxLayout(self.templatesCard)
        
        # 模板操作栏
        templates_header_layout = QHBoxLayout()
        self.templatesTitle = SubtitleLabel(self.tr("项目模板集合"), self)
        self.addTemplateButton = PrimaryPushButton(FIF.ADD, self.tr("新建模板"), self)
        self.editTemplateButton = PushButton(FIF.EDIT, self.tr("编辑模板"), self)
        self.deleteTemplateButton = PushButton(FIF.DELETE, self.tr("删除模板"), self)
        templates_header_layout.addWidget(self.templatesTitle)
        templates_header_layout.addStretch()
        templates_header_layout.addWidget(self.addTemplateButton)
        templates_header_layout.addWidget(self.editTemplateButton)
        templates_header_layout.addWidget(self.deleteTemplateButton)
        templates_layout.addLayout(templates_header_layout)
        
        # 已添加的模板列表
        self.templatesTable = TableWidget(self)
        self.templatesTable.setColumnCount(3)
        self.templatesTable.setHorizontalHeaderLabels([self.tr("名称"), self.tr("描述"), self.tr("字段数量")])
        self.templatesTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        templates_layout.addWidget(self.templatesTable)
        
        layout.addWidget(self.detailCard)
        layout.addWidget(self.itemsCard)
        layout.addWidget(self.templatesCard)
        
        # 连接信号
        self.addProjectButton.clicked.connect(self._on_add_project)
        self.editProjectButton.clicked.connect(self._on_edit_project)
        self.deleteProjectButton.clicked.connect(self._on_delete_project)
        self.projectTable.itemSelectionChanged.connect(self._on_project_selected)
        self.addTemplateButton.clicked.connect(self._on_add_template)
        self.editTemplateButton.clicked.connect(self._on_edit_template_clicked)
        self.deleteTemplateButton.clicked.connect(self._on_delete_template)
        self.templatesTable.itemDoubleClicked.connect(self._on_edit_template)
        
        # 加载项目列表
        self._load_projects()
    
    def _load_projects(self):
        """加载项目列表"""
        self.projectTable.setRowCount(0)
        for project_id, project in self.fault_manager.projects.items():
            row = self.projectTable.rowCount()
            self.projectTable.insertRow(row)
            name_item = QTableWidgetItem(project.name)
            name_item.setData(Qt.UserRole, project_id)
            self.projectTable.setItem(row, 0, name_item)
            self.projectTable.setItem(row, 1, QTableWidgetItem(project.description))
            self.projectTable.setItem(row, 2, QTableWidgetItem(str(len(project.item_ids))))
    
    def _load_items(self, project_id: str):
        """加载项目的条目列表"""
        self.itemsTable.setRowCount(0)
        project = self.fault_manager.get_project(project_id)
        if project:
            for item_id in project.item_ids:
                item = self.fault_manager.get_item(item_id)
                if item:
                    # 获取模板名称
                    template_name = ""
                    template = self.fault_manager.get_template(item.template_id)
                    if template:
                        template_name = template.name
                    
                    row = self.itemsTable.rowCount()
                    self.itemsTable.insertRow(row)
                    self.itemsTable.setItem(row, 0, QTableWidgetItem(item.title))
                    self.itemsTable.setItem(row, 1, QTableWidgetItem(template_name))
                    self.itemsTable.setItem(row, 2, QTableWidgetItem(item.created_at))
    
    def _on_project_selected(self):
        """项目选择变化"""
        selected_items = self.projectTable.selectedItems()
        if not selected_items:
            self.detailContent.setText(self.tr("请选择一个项目查看详情"))
            self._load_items("")
            self._load_project_templates("")
            return
        
        item = selected_items[0]
        project_id = item.data(Qt.UserRole)
        project = self.fault_manager.get_project(project_id)
        
        if project:
            # 获取项目的模板数量
            templates = self.fault_manager.get_project_templates(project_id)
            detail_text = f"{self.tr('描述')}: {project.description}\n"
            detail_text += f"{self.tr('条目数量')}: {len(project.item_ids)}\n"
            detail_text += f"{self.tr('模板数量')}: {len(templates)}\n"
            detail_text += f"{self.tr('创建时间')}: {project.created_at}\n"
            detail_text += f"{self.tr('更新时间')}: {project.updated_at}\n"
            self.detailContent.setText(detail_text)
            self._load_items(project_id)
            self._load_project_templates(project_id)
    
    def _on_add_project(self):
        """新建项目"""
        dialog = ProjectEditorDialog(parent=self)
        if dialog.exec():
            project = dialog.get_project()
            self.fault_manager.create_project(project.name, project.description)
            self._load_projects()
    
    def _on_edit_project(self):
        """编辑项目"""
        selected_items = self.projectTable.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, self.tr("警告"), self.tr("请选择一个项目"))
            return
        
        item = selected_items[0]
        project_id = item.data(Qt.UserRole)
        project = self.fault_manager.get_project(project_id)
        
        if project:
            dialog = ProjectEditorDialog(project, self)
            if dialog.exec():
                updated_project = dialog.get_project()
                self.fault_manager.update_project(updated_project)
                self._load_projects()
                # 更新选中项
                for i in range(self.projectTable.rowCount()):
                    if self.projectTable.itemData(i, Qt.UserRole) == project_id:
                        self.projectTable.setItem(i, 0, QTableWidgetItem(updated_project.name))
                        self.projectTable.setItem(i, 1, QTableWidgetItem(updated_project.description))
                        break
                self._on_project_selected()
    
    def _load_project_templates(self, project_id: str):
        """加载项目中的模板到表格"""
        self.templatesTable.setRowCount(0)
        if not project_id:
            return
        
        templates = self.fault_manager.get_project_templates(project_id)
        for template in templates:
            row = self.templatesTable.rowCount()
            self.templatesTable.insertRow(row)
            name_item = QTableWidgetItem(template.name)
            name_item.setData(Qt.UserRole, template.id)
            self.templatesTable.setItem(row, 0, name_item)
            self.templatesTable.setItem(row, 1, QTableWidgetItem(template.description))
            self.templatesTable.setItem(row, 2, QTableWidgetItem(str(len(template.fields))))
    
    def _on_add_template(self):
        """新建模板"""
        selected_items = self.projectTable.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, self.tr("警告"), self.tr("请选择一个项目"))
            return
        
        item = selected_items[0]
        project_id = item.data(Qt.UserRole)
        
        # 导入TemplateEditorDialog
        from .FastFaultManager_template_ui import TemplateEditorDialog
        
        dialog = TemplateEditorDialog(fault_manager=self.fault_manager, parent=self, project_id=project_id)
        if dialog.exec():
            template = dialog.get_template()
            # 创建模板并获取返回的模板对象
            new_template = self.fault_manager.create_template(template.name, project_id, template.description)
            # 手动添加字段和子模板
            new_template.fields = template.fields
            new_template.sub_templates = template.sub_templates
            self.fault_manager.update_template(new_template)
            
            # 重新加载模板列表
            self._load_project_templates(project_id)
            # 更新项目详情
            self._on_project_selected()
    
    def _on_edit_template_clicked(self):
        """点击编辑模板按钮"""
        selected_items = self.templatesTable.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, self.tr("警告"), self.tr("请选择一个模板"))
            return
        
        item = selected_items[0]
        template_id = item.data(Qt.UserRole)
        template = self.fault_manager.get_template(template_id)
        
        if template:
            # 导入TemplateEditorDialog
            from .FastFaultManager_template_ui import TemplateEditorDialog
            
            dialog = TemplateEditorDialog(template, self.fault_manager, self)
            if dialog.exec():
                updated_template = dialog.get_template()
                self.fault_manager.update_template(updated_template)
                
                # 重新加载模板列表
                selected_items = self.projectTable.selectedItems()
                if selected_items:
                    project_id = selected_items[0].data(Qt.UserRole)
                    self._load_project_templates(project_id)
                    # 更新项目详情
                    self._on_project_selected()
    
    def _on_edit_template(self, item, column):
        """双击编辑模板"""
        template_id = item.data(Qt.UserRole)
        template = self.fault_manager.get_template(template_id)
        
        if template:
            # 导入TemplateEditorDialog
            from .FastFaultManager_template_ui import TemplateEditorDialog
            
            dialog = TemplateEditorDialog(template, self.fault_manager, self)
            if dialog.exec():
                updated_template = dialog.get_template()
                self.fault_manager.update_template(updated_template)
                
                # 重新加载模板列表
                selected_items = self.projectTable.selectedItems()
                if selected_items:
                    project_id = selected_items[0].data(Qt.UserRole)
                    self._load_project_templates(project_id)
                    # 更新项目详情
                    self._on_project_selected()
    
    def _on_delete_template(self):
        """删除模板"""
        selected_items = self.templatesTable.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, self.tr("警告"), self.tr("请选择一个模板"))
            return
        
        item = selected_items[0]
        template_id = item.data(Qt.UserRole)
        template = self.fault_manager.get_template(template_id)
        
        if template:
            # 检查是否有条目使用此模板
            has_used = False
            for project in self.fault_manager.projects.values():
                for item_id in project.item_ids:
                    item = self.fault_manager.get_item(item_id)
                    if item and item.template_id == template_id:
                        has_used = True
                        break
                if has_used:
                    break
            
            if has_used:
                QMessageBox.warning(self, self.tr("警告"), self.tr("该模板已被条目使用，无法删除"))
                return
            
            if QMessageBox.question(self, self.tr("确认"), 
                                   self.tr(f"确定要删除模板 '{template.name}' 吗？")) == QMessageBox.Yes:
                self.fault_manager.delete_template(template_id)
                
                # 重新加载模板列表
                selected_items = self.projectTable.selectedItems()
                if selected_items:
                    project_id = selected_items[0].data(Qt.UserRole)
                    self._load_project_templates(project_id)
                    # 更新项目详情
                    self._on_project_selected()
    
    def _on_delete_project(self):
        """删除项目"""
        selected_items = self.projectTable.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, self.tr("警告"), self.tr("请选择一个项目"))
            return
        
        item = selected_items[0]
        project_id = item.data(Qt.UserRole)
        project = self.fault_manager.get_project(project_id)
        
        if project:
            if QMessageBox.question(self, self.tr("确认"), 
                                   self.tr(f"确定要删除项目 '{project.name}' 吗？这将删除项目中的所有条目。")) == QMessageBox.Yes:
                self.fault_manager.delete_project(project_id)
                self._load_projects()
                self.detailContent.setText(self.tr("请选择一个项目查看详情"))
                self._load_items("")
                self._load_templates_for_combo("")
                self._load_project_templates("")