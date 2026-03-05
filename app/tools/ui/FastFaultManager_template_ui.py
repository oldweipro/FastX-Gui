from PySide6.QtCore import Qt, QModelIndex
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
                               QPushButton, QDialog, QLineEdit, QTextEdit, QFormLayout,
                               QComboBox, QCheckBox, QSpinBox, QTableWidget, QTableWidgetItem,
                               QHeaderView, QMessageBox, QFrame)
from qfluentwidgets import (
    FluentIcon as FIF,
    PrimaryPushButton,
    PushButton,
    Dialog,
    LineEdit,
    TextEdit,
    ComboBox,
    CheckBox,
    SpinBox,
    TableWidget,
    SubtitleLabel,
    BodyLabel,
    CardWidget,
    ElevatedCardWidget,
    ScrollArea,
    MessageBoxBase
)

from app.model.fault_model import FaultManager, Template, Field


class FieldEditorDialog(MessageBoxBase):
    """字段编辑器对话框"""
    def __init__(self, field: Field = None, fault_manager: FaultManager = None, parent=None, project_id: str = None):
        title = self.tr("编辑字段") if field else self.tr("新建字段")
        super().__init__(parent)
        self.setWindowTitle(title)
        self.field = field or Field("", "text", "")
        self.fault_manager = fault_manager
        self.project_id = project_id
        
        # 标题
        self.titleLabel = SubtitleLabel(title, self)
        self.viewLayout.addWidget(self.titleLabel)


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

        # 字段名称
        self.nameEdit = LineEdit(self.scrollWidget)
        self.nameEdit.setText(self.field.name)
        
        # 字段类型
        self.typeComboBox = ComboBox(self.scrollWidget)
        self.typeComboBox.addItems(["text", "number", "checkbox", "select", "date", "textarea", "template_item"])
        if self.field.field_type:
            index = self.typeComboBox.findText(self.field.field_type)
            if index >= 0:
                self.typeComboBox.setCurrentIndex(index)
        
        # 模板选择器（用于template_item类型）
        self.templateComboBox = ComboBox(self.scrollWidget)
        self.templateComboBox.setPlaceholderText(self.tr("选择模板"))
        if self.fault_manager and self.project_id:
            # 清空现有选项
            self.templateComboBox.clear()
            # 只添加当前项目的模板
            for template_id, template in self.fault_manager.templates.items():
                if template.project_id == self.project_id:
                    self.templateComboBox.addItem(template.name, None, template_id)
        if self.field.template_id:
            # 查找并设置选中的模板
            index = -1
            for i in range(self.templateComboBox.count()):
                if self.templateComboBox.itemData(i) == self.field.template_id:
                    index = i
                    break
            if index >= 0:
                self.templateComboBox.setCurrentIndex(index)
            print(f"[FieldEditorDialog] 加载字段时，template_id = {self.field.template_id}, 选择的索引 = {index}")
        
        # 多选选项（用于template_item类型）
        self.multiSelectCheckBox = CheckBox(self.tr("允许多选"), self.scrollWidget)
        self.multiSelectCheckBox.setChecked(self.field.multi_select)
        
        # 字段标签
        self.labelEdit = LineEdit(self.scrollWidget)
        self.labelEdit.setText(self.field.label)
        
        # 必填
        self.requiredCheckBox = CheckBox(self.tr("必填"), self.scrollWidget)
        self.requiredCheckBox.setChecked(self.field.required)
        
        # 默认值
        self.defaultEdit = LineEdit(self.scrollWidget)
        if self.field.default is not None:
            self.defaultEdit.setText(str(self.field.default))
        
        # 选项（仅适用于select类型）
        self.optionsEdit = TextEdit(self.scrollWidget)
        self.optionsEdit.setPlaceholderText(self.tr("每行一个选项"))
        if self.field.options:
            self.optionsEdit.setText("\n".join(self.field.options))
        
        # 布局
        layout = QFormLayout()
        layout.addRow(self.tr("字段名称:"), self.nameEdit)
        layout.addRow(self.tr("字段类型:"), self.typeComboBox)
        layout.addRow(self.tr("字段标签:"), self.labelEdit)
        layout.addRow(self.tr("默认值:"), self.defaultEdit)
        layout.addRow(self.requiredCheckBox)
        layout.addRow(self.tr("选项（仅select类型）:"), self.optionsEdit)
        layout.addRow(self.tr("模板（仅template_item类型）:"), self.templateComboBox)
        layout.addRow(self.tr("多选设置（仅template_item类型）:"), self.multiSelectCheckBox)
        self.scrollLayout.addLayout(layout)

        # 将内容容器设置到滚动区域
        self.scrollArea.setWidget(self.scrollWidget)
        # 将滚动区域添加到主布局（标题下方）
        self.viewLayout.addWidget(self.scrollArea)

        # 设置按钮文本
        self.yesButton.setText("保存")
        self.cancelButton.setText("取消")
        self.widget.setMinimumWidth(600)
        
        # 连接信号
        self.typeComboBox.currentIndexChanged.connect(self._on_type_changed)
        # 初始状态
        self._on_type_changed(self.typeComboBox.currentIndex())
    
    def _on_type_changed(self, index):
        """字段类型变化"""
        field_type = self.typeComboBox.currentText()
        # 显示/隐藏选项编辑框
        if field_type == "select":
            self.optionsEdit.show()
        else:
            self.optionsEdit.hide()
        # 显示/隐藏模板选择框
        if field_type == "template_item":
            self.templateComboBox.show()
            self.multiSelectCheckBox.show()
        else:
            self.templateComboBox.hide()
            self.multiSelectCheckBox.hide()
        
    def get_field(self) -> Field:
        """获取编辑后的字段"""
        self.field.name = self.nameEdit.text()
        self.field.field_type = self.typeComboBox.currentText()
        self.field.label = self.labelEdit.text()
        self.field.required = self.requiredCheckBox.isChecked()
        
        # 设置默认值
        default_text = self.defaultEdit.text()
        if self.field.field_type == "number":
            try:
                self.field.default = int(default_text) if default_text else None
            except ValueError:
                self.field.default = None
        elif self.field.field_type == "checkbox":
            self.field.default = default_text.lower() == "true"
        else:
            self.field.default = default_text if default_text else None
        
        # 设置选项
        if self.field.field_type == "select":
            self.field.options = [option.strip() for option in self.optionsEdit.toPlainText().split("\n") if option.strip()]
        else:
            self.field.options = []
        
        # 设置模板ID和多选设置（仅template_item类型）
        if self.field.field_type == "template_item":
            template_id = self.templateComboBox.currentData()
            self.field.template_id = template_id
            self.field.multi_select = self.multiSelectCheckBox.isChecked()
            print(f"[FieldEditorDialog] 保存字段时，template_id = {template_id}, multi_select = {self.field.multi_select}")
        else:
            self.field.template_id = None
            self.field.multi_select = False
        
        return self.field


class TemplateEditorDialog(MessageBoxBase):
    """模板编辑器对话框"""
    def __init__(self, template: Template = None, fault_manager: FaultManager = None, parent=None, project_id: str = None):
        title = self.tr("编辑模板") if template else self.tr("新建模板")
        super().__init__(parent)
        self.setWindowTitle(title)
        self.project_id = project_id
        if template:
            self.template = template
        else:
            # 新建模板时必须指定项目ID
            if not project_id:
                raise ValueError("新建模板时必须指定项目ID")
            self.template = Template("", project_id, "")
        self.fault_manager = fault_manager
        
        # 标题
        self.titleLabel = SubtitleLabel(title, self)
        self.viewLayout.addWidget(self.titleLabel)

        # 创建滚动区域
        from PySide6.QtWidgets import QFrame
        from PySide6.QtCore import Qt
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

        # 模板名称
        self.nameEdit = LineEdit(self.scrollWidget)
        self.nameEdit.setText(self.template.name)
        
        # 模板描述
        self.descriptionEdit = TextEdit(self.scrollWidget)
        self.descriptionEdit.setText(self.template.description)
        
        # 字段列表
        self.fieldsTable = TableWidget(self.scrollWidget)
        self.fieldsTable.setMinimumHeight(200)
        self.fieldsTable.setColumnCount(4)
        self.fieldsTable.setHorizontalHeaderLabels([self.tr("名称"), self.tr("类型"), self.tr("标签"), self.tr("必填")])
        self.fieldsTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # 子模板列表
        self.subTemplatesComboBox = ComboBox(self.scrollWidget)
        self.subTemplatesComboBox.setPlaceholderText(self.tr("选择子模板"))
        if self.fault_manager:
            for template_id, t in self.fault_manager.templates.items():
                # 只有在编辑现有模板时才排除自身
                if self.template.id and template_id != self.template.id:
                    self.subTemplatesComboBox.addItem(t.name, None, template_id)
        
        # 布局
        layout = QFormLayout()
        layout.addRow(self.tr("模板名称:"), self.nameEdit)
        layout.addRow(self.tr("模板描述:"), self.descriptionEdit)
        
        # 字段管理
        fieldsLayout = QVBoxLayout()
        fieldsLayout.addWidget(SubtitleLabel(self.tr("字段"), self.scrollWidget))
        fieldsLayout.addWidget(self.fieldsTable)
        
        fieldsButtonLayout = QHBoxLayout()
        self.addFieldButton = PushButton(FIF.ADD, self.tr("添加字段"), self.scrollWidget)
        self.editFieldButton = PushButton(FIF.EDIT, self.tr("编辑字段"), self.scrollWidget)
        self.deleteFieldButton = PushButton(FIF.DELETE, self.tr("删除字段"), self.scrollWidget)
        fieldsButtonLayout.addWidget(self.addFieldButton)
        fieldsButtonLayout.addWidget(self.editFieldButton)
        fieldsButtonLayout.addWidget(self.deleteFieldButton)
        fieldsLayout.addLayout(fieldsButtonLayout)
        
        layout.addRow(fieldsLayout)
        
        # 子模板管理
        subTemplatesLayout = QVBoxLayout()
        subTemplatesLayout.addWidget(SubtitleLabel(self.tr("子模板"), self.scrollWidget))
        
        subTemplatesButtonLayout = QHBoxLayout()
        subTemplatesButtonLayout.addWidget(self.subTemplatesComboBox)
        self.addSubTemplateButton = PushButton(FIF.ADD, self.tr("添加"), self.scrollWidget)
        self.removeSubTemplateButton = PushButton(FIF.DELETE, self.tr("移除"), self.scrollWidget)
        subTemplatesButtonLayout.addWidget(self.addSubTemplateButton)
        subTemplatesButtonLayout.addWidget(self.removeSubTemplateButton)
        subTemplatesLayout.addLayout(subTemplatesButtonLayout)
        
        # 已添加的子模板列表
        self.subTemplatesList = QListWidget(self.scrollWidget)
        subTemplatesLayout.addWidget(self.subTemplatesList)
        
        layout.addRow(subTemplatesLayout)
        
        self.scrollLayout.addLayout(layout)

        # 将内容容器设置到滚动区域
        self.scrollArea.setWidget(self.scrollWidget)
        # 将滚动区域添加到主布局（标题下方）
        self.viewLayout.addWidget(self.scrollArea)

        # 设置按钮文本
        self.yesButton.setText("保存")
        self.cancelButton.setText("取消")
        self.widget.setMinimumWidth(960)
        self.widget.setMinimumHeight(700)

        # 连接信号
        self.addFieldButton.clicked.connect(self._on_add_field)
        self.editFieldButton.clicked.connect(self._on_edit_field)
        self.deleteFieldButton.clicked.connect(self._on_delete_field)
        self.addSubTemplateButton.clicked.connect(self._on_add_sub_template)
        self.removeSubTemplateButton.clicked.connect(self._on_remove_sub_template)
        
        # 加载字段和子模板
        self._load_fields()
        self._load_sub_templates()
    
    def _load_fields(self):
        """加载字段列表"""
        # 确保表格有足够的列
        if self.fieldsTable.columnCount() < 5:
            self.fieldsTable.setColumnCount(5)
            self.fieldsTable.setHorizontalHeaderLabels([self.tr("名称"), self.tr("类型"), self.tr("标签"), self.tr("必填"), self.tr("多选")])
        
        self.fieldsTable.setRowCount(0)
        for field in self.template.fields:
            row = self.fieldsTable.rowCount()
            self.fieldsTable.insertRow(row)
            self.fieldsTable.setItem(row, 0, QTableWidgetItem(field.name))
            # 对于template_item类型，显示模板名称和多选设置
            field_type_display = field.field_type
            if field.field_type == "template_item" and field.template_id and self.fault_manager:
                template = self.fault_manager.get_template(field.template_id)
                if template:
                    multi_select_text = "(多选)" if field.multi_select else ""
                    field_type_display = f"template_item ({template.name}){multi_select_text}"
            self.fieldsTable.setItem(row, 1, QTableWidgetItem(field_type_display))
            self.fieldsTable.setItem(row, 2, QTableWidgetItem(field.label))
            self.fieldsTable.setItem(row, 3, QTableWidgetItem("✓" if field.required else ""))
            self.fieldsTable.setItem(row, 4, QTableWidgetItem("✓" if field.multi_select else ""))
    
    def _load_sub_templates(self):
        """加载子模板列表"""
        self.subTemplatesList.clear()
        if self.fault_manager:
            for template_id in self.template.sub_templates:
                if template_id in self.fault_manager.templates:
                    template = self.fault_manager.templates[template_id]
                    item = QListWidgetItem(template.name)
                    item.setData(Qt.UserRole, template_id)
                    self.subTemplatesList.addItem(item)
    
    def _on_add_field(self):
        """添加字段"""
        dialog = FieldEditorDialog(fault_manager=self.fault_manager, parent=self.window(), project_id=self.template.project_id)
        if dialog.exec():
            field = dialog.get_field()
            self.template.add_field(field)
            self._load_fields()
    
    def _on_edit_field(self):
        """编辑字段"""
        selected_rows = self.fieldsTable.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, self.tr("警告"), self.tr("请选择一个字段"))
            return
        
        row = selected_rows[0].row()
        field_name = self.fieldsTable.item(row, 0).text()
        # 找到对应的字段
        field = None
        for f in self.template.fields:
            if f.name == field_name:
                field = f
                break
        
        if field:
            print(f"[TemplateEditorDialog] 编辑字段：{field.name}, type={field.field_type}, template_id={field.template_id}")
            dialog = FieldEditorDialog(field, self.fault_manager, self, project_id=self.template.project_id)
            if dialog.exec():
                updated_field = dialog.get_field()
                print(f"[TemplateEditorDialog] 更新字段：{updated_field.name}, type={updated_field.field_type}, template_id={updated_field.template_id}")
                # 更新字段
                for i, f in enumerate(self.template.fields):
                    if f.id == updated_field.id:
                        self.template.fields[i] = updated_field
                        break
                self._load_fields()
    
    def _on_delete_field(self):
        """删除字段"""
        selected_rows = self.fieldsTable.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, self.tr("警告"), self.tr("请选择一个字段"))
            return
        
        row = selected_rows[0].row()
        field_name = self.fieldsTable.item(row, 0).text()
        
        if QMessageBox.question(self, self.tr("确认"), self.tr(f"确定要删除字段 '{field_name}' 吗？")) == QMessageBox.Yes:
            # 找到对应的字段
            field_id = None
            for f in self.template.fields:
                if f.name == field_name:
                    field_id = f.id
                    break
            
            if field_id:
                self.template.remove_field(field_id)
                self._load_fields()
    
    def _on_add_sub_template(self):
        """添加子模板"""
        index = self.subTemplatesComboBox.currentIndex()
        if index < 0:
            QMessageBox.warning(self, self.tr("警告"), self.tr("请选择一个子模板"))
            return
        
        template_id = self.subTemplatesComboBox.currentData()
        template_name = self.subTemplatesComboBox.currentText()
        
        # 检查是否已添加
        for i in range(self.subTemplatesList.count()):
            if self.subTemplatesList.item(i).data(Qt.UserRole) == template_id:
                QMessageBox.warning(self, self.tr("警告"), self.tr("该子模板已添加"))
                return
        
        self.template.add_sub_template(template_id)
        self._load_sub_templates()
    
    def _on_remove_sub_template(self):
        """移除子模板"""
        selected_items = self.subTemplatesList.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, self.tr("警告"), self.tr("请选择一个子模板"))
            return
        
        item = selected_items[0]
        template_id = item.data(Qt.UserRole)
        template_name = item.text()
        
        if QMessageBox.question(self, self.tr("确认"), self.tr(f"确定要移除子模板 '{template_name}' 吗？")) == QMessageBox.Yes:
            self.template.remove_sub_template(template_id)
            self._load_sub_templates()
    
    def get_template(self) -> Template:
        """获取编辑后的模板"""
        self.template.name = self.nameEdit.text()
        self.template.description = self.descriptionEdit.toPlainText()
        return self.template


class TemplateManagerUI(QWidget):
    """模板管理界面"""
    def __init__(self, fault_manager: FaultManager, parent=None):
        super().__init__(parent)
        self.fault_manager = fault_manager
        self._init_ui()
    
    def _init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        
        # 标题
        layout.addWidget(SubtitleLabel(self.tr("模板管理"), self))
        
        # 操作按钮
        button_layout = QHBoxLayout()
        self.addTemplateButton = PrimaryPushButton(FIF.ADD, self.tr("新建模板"), self)
        self.editTemplateButton = PushButton(FIF.EDIT, self.tr("编辑模板"), self)
        self.deleteTemplateButton = PushButton(FIF.DELETE, self.tr("删除模板"), self)
        button_layout.addWidget(self.addTemplateButton)
        button_layout.addWidget(self.editTemplateButton)
        button_layout.addWidget(self.deleteTemplateButton)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # 模板列表
        self.templateTable = TableWidget(self)
        self.templateTable.setMinimumHeight(200)
        self.templateTable.setColumnCount(4)
        self.templateTable.setHorizontalHeaderLabels([self.tr("名称"), self.tr("描述"), self.tr("字段数量"), self.tr("子模板数量")])
        self.templateTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.templateTable)
        
        # 模板详情
        self.detailCard = ElevatedCardWidget(self)
        detail_layout = QVBoxLayout(self.detailCard)
        
        self.detailTitle = SubtitleLabel(self.tr("模板详情"), self)
        detail_layout.addWidget(self.detailTitle)
        
        self.detailContent = BodyLabel(self.tr("请选择一个模板查看详情"), self)
        self.detailContent.setWordWrap(True)
        detail_layout.addWidget(self.detailContent)
        
        layout.addWidget(self.detailCard)
        
        # 连接信号
        self.addTemplateButton.clicked.connect(self._on_add_template)
        self.editTemplateButton.clicked.connect(self._on_edit_template)
        self.deleteTemplateButton.clicked.connect(self._on_delete_template)
        self.templateTable.itemSelectionChanged.connect(self._on_template_selected)
        
        # 加载模板列表
        self._load_templates()
    
    def _load_templates(self):
        """加载模板列表"""
        self.templateTable.setRowCount(0)
        for template_id, template in self.fault_manager.templates.items():
            row = self.templateTable.rowCount()
            self.templateTable.insertRow(row)
            name_item = QTableWidgetItem(template.name)
            name_item.setData(Qt.UserRole, template_id)
            self.templateTable.setItem(row, 0, name_item)
            self.templateTable.setItem(row, 1, QTableWidgetItem(template.description))
            self.templateTable.setItem(row, 2, QTableWidgetItem(str(len(template.fields))))
            self.templateTable.setItem(row, 3, QTableWidgetItem(str(len(template.sub_templates))))
    
    def _on_template_selected(self):
        """模板选择变化"""
        selected_items = self.templateTable.selectedItems()
        if not selected_items:
            self.detailContent.setText(self.tr("请选择一个模板查看详情"))
            return
        
        item = selected_items[0]
        template_id = item.data(Qt.UserRole)
        template = self.fault_manager.get_template(template_id)
        
        if template:
            detail_text = f"{self.tr('描述')}: {template.description}\n"
            detail_text += f"{self.tr('字段数量')}: {len(template.fields)}\n"
            detail_text += f"{self.tr('子模板数量')}: {len(template.sub_templates)}\n"
            detail_text += f"{self.tr('创建时间')}: {template.created_at}\n"
            detail_text += f"{self.tr('更新时间')}: {template.updated_at}\n"
            self.detailContent.setText(detail_text)
    
    def _on_add_template(self):
        """新建模板"""
        dialog = TemplateEditorDialog(fault_manager=self.fault_manager, parent=self.window())
        if dialog.exec():
            template = dialog.get_template()
            # 创建模板并获取返回的模板对象
            new_template = self.fault_manager.create_template(template.name, template.description)
            # 手动添加字段和子模板
            new_template.fields = template.fields
            new_template.sub_templates = template.sub_templates
            self.fault_manager.update_template(new_template)
            self._load_templates()
    
    def _on_edit_template(self):
        """编辑模板"""
        selected_items = self.templateTable.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, self.tr("警告"), self.tr("请选择一个模板"))
            return
        
        item = selected_items[0]
        template_id = item.data(Qt.UserRole)
        template = self.fault_manager.get_template(template_id)
        
        if template:
            dialog = TemplateEditorDialog(template, self.fault_manager, self)
            if dialog.exec():
                updated_template = dialog.get_template()
                self.fault_manager.update_template(updated_template)
                self._load_templates()
                # 更新选中项
                for i in range(self.templateTable.rowCount()):
                    if self.templateTable.itemData(i, Qt.UserRole) == template_id:
                        self.templateTable.setItem(i, 0, QTableWidgetItem(updated_template.name))
                        self.templateTable.setItem(i, 1, QTableWidgetItem(updated_template.description))
                        self.templateTable.setItem(i, 2, QTableWidgetItem(str(len(updated_template.fields))))
                        self.templateTable.setItem(i, 3, QTableWidgetItem(str(len(updated_template.sub_templates))))
                        break
                self._on_template_selected()
    
    def _on_delete_template(self):
        """删除模板"""
        selected_items = self.templateTable.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, self.tr("警告"), self.tr("请选择一个模板"))
            return
        
        item = selected_items[0]
        template_id = item.data(Qt.UserRole)
        template = self.fault_manager.get_template(template_id)
        
        if template:
            if QMessageBox.question(self, self.tr("确认"), self.tr(f"确定要删除模板 '{template.name}' 吗？")) == QMessageBox.Yes:
                self.fault_manager.delete_template(template_id)
                self._load_templates()
                self.detailContent.setText(self.tr("请选择一个模板查看详情"))