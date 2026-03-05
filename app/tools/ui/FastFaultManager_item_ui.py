from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
                               QPushButton, QDialog, QLineEdit, QTextEdit, QFormLayout,
                               QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
                               QLabel, QScrollArea, QGridLayout, QFrame)
from qfluentwidgets import (
    FluentIcon as FIF,
    PrimaryPushButton,
    PushButton,
    Dialog,
    LineEdit,
    TextEdit,
    ComboBox,
    SubtitleLabel,
    BodyLabel,
    ElevatedCardWidget,
    CheckBox,
    SpinBox,
    MessageBoxBase,
    ScrollArea
)

from app.model.fault_model import FaultManager, Item, Template


class ItemEditorDialog(MessageBoxBase):
    """条目编辑器对话框"""
    def __init__(self, item: Item = None, fault_manager: FaultManager = None, project_id: str = "", parent=None):
        title = self.tr("编辑条目") if item else self.tr("新建条目")
        super().__init__(parent)
        self.setWindowTitle(title)
        self.item = item or Item("", project_id, "")
        self.fault_manager = fault_manager
        self.project_id = project_id
        
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

        # 条目标题
        self.titleEdit = LineEdit(self.scrollWidget)
        self.titleEdit.setText(self.item.title)
        
        # 模板选择
        self.templateComboBox = ComboBox(self.scrollWidget)
        self.templateComboBox.setPlaceholderText(self.tr("选择模板"))
        if self.fault_manager and self.project_id:
            # 只显示当前项目的模板
            for template_id, template in self.fault_manager.templates.items():
                if template.project_id == self.project_id:
                    self.templateComboBox.addItem(template.name, None, template_id)
        
        # 如果是编辑模式，设置当前模板
        if self.item.template_id:
            for i in range(self.templateComboBox.count()):
                if self.templateComboBox.itemData(i) == self.item.template_id:
                    self.templateComboBox.setCurrentIndex(i)
                    break
        
        # 字段表单
        self.fieldsScrollArea = ScrollArea(self.scrollWidget)
        self.fieldsScrollArea.setMinimumHeight(200)
        self.fieldsScrollArea.setWidgetResizable(True)
        self.fieldsWidget = QWidget()
        self.fieldsLayout = QFormLayout(self.fieldsWidget)
        self.fieldsScrollArea.setWidget(self.fieldsWidget)
        
        # 布局
        layout = QFormLayout()
        layout.addRow(self.tr("条目标题:"), self.titleEdit)
        layout.addRow(self.tr("模板:"), self.templateComboBox)
        layout.addRow(self.tr("字段:"), self.fieldsScrollArea)
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
        self.templateComboBox.currentIndexChanged.connect(self._on_template_changed)
        
        # 加载字段
        self._load_fields()
    
    def _load_fields(self):
        """加载字段表单"""
        print("[ItemEditorDialog] 加载字段表单")
        # 清空现有字段
        for i in reversed(range(self.fieldsLayout.count())):
            widget = self.fieldsLayout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        
        # 获取当前模板
        template_id = self.templateComboBox.currentData()
        print(f"[ItemEditorDialog] 当前模板ID: {template_id}")
        if not template_id or not self.fault_manager:
            print("[ItemEditorDialog] 模板ID为空或fault_manager为None")
            return
        
        template = self.fault_manager.get_template(template_id)
        if template:
            print(f"[ItemEditorDialog] 加载模板: {template.name}, 字段数量: {len(template.fields)}")
            # 加载模板字段
            self._load_template_fields(template)
        else:
            print("[ItemEditorDialog] 模板不存在")
    
    def _load_template_fields(self, template: Template):
        """加载模板及其子模板的字段"""
        print(f"[ItemEditorDialog] 加载模板字段: {template.name}")
        # 添加模板字段
        for field in template.fields:
            print(f"[ItemEditorDialog] 加载字段: {field.name}, 类型: {field.field_type}")
            self._add_field_widget(field)
        
        # 加载子模板字段
        for sub_template_id in template.sub_templates:
            sub_template = self.fault_manager.get_template(sub_template_id)
            if sub_template:
                print(f"[ItemEditorDialog] 加载子模板: {sub_template.name}")
                # 添加子模板标题
                label = QLabel(f"{self.tr('子模板')}: {sub_template.name}")
                font = label.font()
                font.setBold(True)
                label.setFont(font)
                self.fieldsLayout.addRow(label)
                # 添加子模板字段
                for field in sub_template.fields:
                    print(f"[ItemEditorDialog] 加载子模板字段: {field.name}, 类型: {field.field_type}")
                    self._add_field_widget(field)
    
    def _add_field_widget(self, field):
        """添加字段控件"""
        print(f"[ItemEditorDialog] 添加字段控件: {field.name}, 类型: {field.field_type}")
        label = QLabel(f"{field.label}{' *' if field.required else ''}")
        
        if field.field_type == "text":
            widget = LineEdit()
            value = self.item.field_values.get(field.id, field.default or "")
            print(f"[ItemEditorDialog] 设置字段值: {value}")
            widget.setText(str(value))
        elif field.field_type == "number":
            widget = SpinBox()
            value = self.item.field_values.get(field.id, field.default or 0)
            print(f"[ItemEditorDialog] 设置字段值: {value}")
            widget.setValue(int(value))
        elif field.field_type == "checkbox":
            widget = CheckBox()
            value = self.item.field_values.get(field.id, field.default or False)
            print(f"[ItemEditorDialog] 设置字段值: {value}")
            widget.setChecked(bool(value))
        elif field.field_type == "select":
            widget = ComboBox()
            widget.addItems(field.options)
            value = self.item.field_values.get(field.id, field.default)
            print(f"[ItemEditorDialog] 设置字段值: {value}")
            if value:
                index = widget.findText(str(value))
                if index >= 0:
                    widget.setCurrentIndex(index)
        elif field.field_type == "textarea":
            widget = TextEdit()
            value = self.item.field_values.get(field.id, field.default or "")
            print(f"[ItemEditorDialog] 设置字段值: {value}")
            widget.setText(str(value))
        elif field.field_type == "template_item":
            from qfluentwidgets import PushButton
            widget = QWidget()
            layout = QVBoxLayout(widget)
            
            # 选择按钮
            selectButton = PushButton(self.tr("选择条目"), widget)
            # 使用闭包确保正确传递 field 对象
            def create_select_handler(f):
                def handler():
                    self._select_template_items(f)
                return handler
            selectButton.clicked.connect(create_select_handler(field))
            
            # 显示选中的条目
            value = self.item.field_values.get(field.id, field.default)
            selected_items = []
            if isinstance(value, list):
                for item_id in value:
                    selected_item = self.fault_manager.get_item(item_id)
                    if selected_item:
                        selected_items.append(selected_item.title)
            elif value:
                selected_item = self.fault_manager.get_item(value)
                if selected_item:
                    selected_items.append(selected_item.title)
            
            # 根据是否允许多选来选择不同的显示组件
            if field.multi_select:
                # 多选使用TextEdit
                selectedDisplay = TextEdit(widget)
                selectedDisplay.setReadOnly(True)
                selectedDisplay.setPlainText("\n".join(selected_items))
                selectedDisplay.setMinimumHeight(100)
                widget.setProperty("selectedDisplay", selectedDisplay)
            else:
                # 单选使用LineEdit
                selectedDisplay = LineEdit(widget)
                selectedDisplay.setReadOnly(True)
                selectedDisplay.setText(selected_items[0] if selected_items else "")
                widget.setProperty("selectedDisplay", selectedDisplay)
            
            layout.addWidget(selectButton)
            layout.addWidget(selectedDisplay)
            
            # 存储字段信息
            widget.setProperty("field_id", field.id)
            widget.setProperty("field_type", field.field_type)
            widget.setProperty("field", field)
            self.fieldsLayout.addRow(label, widget)
        else:
            widget = LineEdit()
            value = self.item.field_values.get(field.id, field.default or "")
            print(f"[ItemEditorDialog] 设置字段值: {value}")
            widget.setText(str(value))
        
        widget.setProperty("field_id", field.id)
        widget.setProperty("field_type", field.field_type)
        self.fieldsLayout.addRow(label, widget)
        print(f"[ItemEditorDialog] 字段控件添加成功: {field.name}")
    
    def _on_template_changed(self):
        """模板选择变化"""
        print("[ItemEditorDialog] 模板选择变化")
        self._load_fields()
    
    def _select_template_items(self, field):
        """选择模板条目"""
        from qfluentwidgets import MessageBoxBase, CheckBox, ScrollArea
        
        # 确保 field 是有效的 Field 对象
        if not hasattr(field, 'label'):
            print("[ItemEditorDialog] 无效的 field 参数")
            return
        
        # 创建选择对话框
        dialog = MessageBoxBase(self)
        dialog.setWindowTitle(self.tr("选择条目"))
        
        # 标题
        titleLabel = SubtitleLabel(f"选择 {field.label}", dialog)
        dialog.viewLayout.addWidget(titleLabel)
        
        # 滚动区域
        scrollArea = ScrollArea()
        scrollArea.setWidgetResizable(True)
        scrollWidget = QWidget()
        scrollLayout = QVBoxLayout(scrollWidget)
        
        # 加载指定模板的条目
        selection_widgets = []
        current_value = self.item.field_values.get(field.id, [])
        if not isinstance(current_value, list):
            current_value = [current_value] if current_value else []
        
        if field.template_id and self.fault_manager:
            for item_id, item in self.fault_manager.items.items():
                # 只显示当前项目中指定模板的条目
                if item.template_id == field.template_id and item.project_id == self.project_id:
                    # 显示条目的具体值而不是标题
                    item_info = self._get_item_display_info(item)
                    
                    if field.multi_select:
                        # 多选使用checkbox
                        widget = CheckBox(item_info)
                        widget.setChecked(item_id in current_value)
                    else:
                        # 单选使用RadioButton
                        from qfluentwidgets import RadioButton
                        widget = RadioButton(item_info)
                        widget.setChecked(item_id in current_value)
                    
                    widget.setProperty("item_id", item_id)
                    selection_widgets.append(widget)
                    scrollLayout.addWidget(widget)
        
        scrollArea.setWidget(scrollWidget)
        dialog.viewLayout.addWidget(scrollArea)
        
        # 设置按钮
        dialog.yesButton.setText("确定")
        dialog.cancelButton.setText("取消")
        
        # 执行对话框
        if dialog.exec():
            # 获取选中的条目
            selected_item_ids = []
            for widget in selection_widgets:
                if widget.isChecked():
                    selected_item_ids.append(widget.property("item_id"))
            
            # 保存选中的值
            if field.multi_select:
                self.item.set_field_value(field.id, selected_item_ids)
            else:
                self.item.set_field_value(field.id, selected_item_ids[0] if selected_item_ids else None)
            
            # 更新显示
            for i in range(self.fieldsLayout.rowCount()):
                field_item = self.fieldsLayout.itemAt(i, QFormLayout.FieldRole)
                if field_item:
                    widget = field_item.widget()
                    if widget and widget.property("field_id") == field.id:
                        selectedDisplay = widget.property("selectedDisplay")
                        if selectedDisplay:
                            # 获取选中条目的标题
                            selected_titles = []
                            for item_id in selected_item_ids:
                                selected_item = self.fault_manager.get_item(item_id)
                                if selected_item:
                                    selected_titles.append(selected_item.title)
                            if field.multi_select:
                                # 多选使用TextEdit
                                selectedDisplay.setPlainText("\n".join(selected_titles))
                            else:
                                # 单选使用LineEdit
                                selectedDisplay.setText(selected_titles[0] if selected_titles else "")
    
    def _get_item_display_info(self, item):
        """获取条目的显示信息"""
        # 显示条目的具体字段值
        info_parts = [item.title]
        if item.field_values:
            for field_id, value in item.field_values.items():
                # 尝试获取字段名称
                field_name = field_id
                template = self.fault_manager.get_template(item.template_id)
                if template:
                    for field in template.fields:
                        if field.id == field_id:
                            field_name = field.label
                            break
                info_parts.append(f"{field_name}: {value}")
        return " | ".join(info_parts)
    
    def get_item(self) -> Item:
        """获取编辑后的条目"""
        print("[ItemEditorDialog] 获取编辑后的条目")
        self.item.title = self.titleEdit.text()
        self.item.template_id = self.templateComboBox.currentData()
        print(f"[ItemEditorDialog] 模板ID: {self.item.template_id}")
        
        # 保存字段值
        print("[ItemEditorDialog] 保存字段值")
        for i in range(self.fieldsLayout.rowCount()):
            label_item = self.fieldsLayout.itemAt(i, QFormLayout.LabelRole)
            field_item = self.fieldsLayout.itemAt(i, QFormLayout.FieldRole)
            
            if label_item and field_item:
                widget = field_item.widget()
                if widget and hasattr(widget, "property"):
                    field_id = widget.property("field_id")
                    field_type = widget.property("field_type")
                    
                    if field_id:
                        if field_type == "text" or field_type == "textarea":
                            value = widget.toPlainText() if hasattr(widget, "toPlainText") else widget.text()
                            print(f"[ItemEditorDialog] 保存字段 {field_id} 值: {value}")
                            self.item.set_field_value(field_id, value)
                        elif field_type == "number":
                            value = widget.value()
                            print(f"[ItemEditorDialog] 保存字段 {field_id} 值: {value}")
                            self.item.set_field_value(field_id, value)
                        elif field_type == "checkbox":
                            value = widget.isChecked()
                            print(f"[ItemEditorDialog] 保存字段 {field_id} 值: {value}")
                            self.item.set_field_value(field_id, value)
                        elif field_type == "select":
                            value = widget.currentText()
                            print(f"[ItemEditorDialog] 保存字段 {field_id} 值: {value}")
                            self.item.set_field_value(field_id, value)
                        # template_item 字段的值已经在 _select_template_items 方法中保存
        
        print(f"[ItemEditorDialog] 字段值保存完成，共 {len(self.item.field_values)} 个字段")
        return self.item


from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem

class ItemManagerUI(QWidget):
    """条目管理界面"""
    def __init__(self, fault_manager: FaultManager, parent=None):
        super().__init__(parent)
        self.fault_manager = fault_manager
        self.current_project_id = None
        self._init_ui()
    
    def _init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        
        # 标题
        layout.addWidget(SubtitleLabel(self.tr("条目管理"), self))
        
        # 操作按钮
        button_layout = QHBoxLayout()
        self.addItemButton = PrimaryPushButton(FIF.ADD, self.tr("新建条目"), self)
        self.editItemButton = PushButton(FIF.EDIT, self.tr("编辑条目"), self)
        self.deleteItemButton = PushButton(FIF.DELETE, self.tr("删除条目"), self)
        button_layout.addWidget(self.addItemButton)
        button_layout.addWidget(self.editItemButton)
        button_layout.addWidget(self.deleteItemButton)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # 项目选择
        project_layout = QHBoxLayout()
        project_layout.addWidget(BodyLabel(self.tr("选择项目:"), self))
        self.projectComboBox = ComboBox(self)
        self.projectComboBox.setPlaceholderText(self.tr("选择项目"))
        project_layout.addWidget(self.projectComboBox)
        project_layout.addStretch()
        layout.addLayout(project_layout)
        
        # 主布局：左侧路由 + 右侧详情
        main_layout = QHBoxLayout()
        
        # 左侧路由（模板和条目树状结构）
        self.treeWidget = QTreeWidget(self)
        self.treeWidget.setHeaderLabel(self.tr("条目结构"))
        self.treeWidget.setMinimumWidth(300)
        main_layout.addWidget(self.treeWidget)
        
        # 右侧详情（表格显示）
        self.detailCard = ElevatedCardWidget(self)
        detail_layout = QVBoxLayout(self.detailCard)
        
        self.detailTitle = SubtitleLabel(self.tr("条目详情"), self)
        detail_layout.addWidget(self.detailTitle)
        
        # 使用TableWidget显示条目详情
        self.detailTable = QTableWidget(self)
        self.detailTable.setColumnCount(2)
        self.detailTable.setHorizontalHeaderLabels([self.tr("字段"), self.tr("值")])
        self.detailTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        detail_layout.addWidget(self.detailTable)
        
        main_layout.addWidget(self.detailCard, 1)
        layout.addLayout(main_layout)
        
        # 连接信号
        self.addItemButton.clicked.connect(self._on_add_item)
        self.editItemButton.clicked.connect(self._on_edit_item)
        self.deleteItemButton.clicked.connect(self._on_delete_item)
        self.projectComboBox.currentIndexChanged.connect(self._on_project_changed)
        self.treeWidget.itemSelectionChanged.connect(self._on_tree_item_selected)
        
        # 加载项目列表
        self._load_projects()
    
    def _load_projects(self):
        """加载项目列表"""
        self.projectComboBox.clear()
        for project_id, project in self.fault_manager.projects.items():
            self.projectComboBox.addItem(project.name, None, project_id)
    
    def _load_tree(self, project_id: str):
        """加载项目的模板和条目树状结构"""
        self.treeWidget.clear()
        if not project_id:
            return
        
        self.current_project_id = project_id
        
        # 获取项目的所有模板
        templates = self.fault_manager.get_project_templates(project_id)
        
        # 为每个模板创建根节点
        for template in templates:
            template_item = QTreeWidgetItem(self.treeWidget)
            template_item.setText(0, template.name)
            template_item.setData(0, Qt.UserRole, f"template:{template.id}")
            
            # 获取该模板的所有条目
            project = self.fault_manager.get_project(project_id)
            if project:
                for item_id in project.item_ids:
                    item = self.fault_manager.get_item(item_id)
                    if item and item.template_id == template.id:
                        item_child = QTreeWidgetItem(template_item)
                        item_child.setText(0, item.title)
                        item_child.setData(0, Qt.UserRole, f"item:{item.id}")
    
    def _on_project_changed(self):
        """项目选择变化"""
        project_id = self.projectComboBox.currentData()
        print(f"项目选择变化: project_id = {project_id}")
        self._load_tree(project_id)
        # 清空详情表格
        self.detailTable.setRowCount(0)
        self.detailTitle.setText(self.tr("条目详情"))
    
    def _on_tree_item_selected(self):
        """树节点选择变化"""
        selected_items = self.treeWidget.selectedItems()
        if not selected_items:
            self.detailTable.setRowCount(0)
            self.detailTitle.setText(self.tr("条目详情"))
            return
        
        item = selected_items[0]
        data = item.data(0, Qt.UserRole)
        
        if data and isinstance(data, str):
            data_parts = data.split(":")
            if len(data_parts) == 2:
                item_type, item_id = data_parts
                
                if item_type == "item":
                    # 显示条目详情
                    current_item = self.fault_manager.get_item(item_id)
                    if current_item:
                        self._show_item_detail(current_item)
                elif item_type == "template":
                    # 显示模板信息
                    template = self.fault_manager.get_template(item_id)
                    if template:
                        self.detailTitle.setText(f"{self.tr('模板详情')}: {template.name}")
                        self.detailTable.setRowCount(0)
                        # 添加模板信息
                        self.detailTable.insertRow(0)
                        self.detailTable.setItem(0, 0, QTableWidgetItem(self.tr("描述")))
                        self.detailTable.setItem(0, 1, QTableWidgetItem(template.description))
                        self.detailTable.insertRow(1)
                        self.detailTable.setItem(1, 0, QTableWidgetItem(self.tr("字段数量")))
                        self.detailTable.setItem(1, 1, QTableWidgetItem(str(len(template.fields))))
    
    def _show_item_detail(self, item):
        """显示条目的详细信息"""
        # 更新标题
        self.detailTitle.setText(f"{self.tr('条目详情')}: {item.title}")
        
        # 清空表格
        self.detailTable.setRowCount(0)
        
        # 获取模板信息
        template = self.fault_manager.get_template(item.template_id)
        if not template:
            return
        
        # 添加基本信息
        self.detailTable.insertRow(0)
        self.detailTable.setItem(0, 0, QTableWidgetItem(self.tr("模板")))
        self.detailTable.setItem(0, 1, QTableWidgetItem(template.name))
        
        self.detailTable.insertRow(1)
        self.detailTable.setItem(1, 0, QTableWidgetItem(self.tr("创建时间")))
        self.detailTable.setItem(1, 1, QTableWidgetItem(item.created_at))
        
        self.detailTable.insertRow(2)
        self.detailTable.setItem(2, 0, QTableWidgetItem(self.tr("更新时间")))
        self.detailTable.setItem(2, 1, QTableWidgetItem(item.updated_at))
        
        # 添加字段值
        row = 3
        if template:
            for field in template.fields:
                value = item.field_values.get(field.id, "")
                # 对于 template_item 类型的字段，显示选中的条目
                if field.field_type == "template_item":
                    if isinstance(value, list):
                        selected_items = []
                        for item_id in value:
                            selected_item = self.fault_manager.get_item(item_id)
                            if selected_item:
                                selected_items.append(selected_item.title)
                        value = "\n".join(selected_items)
                    else:
                        selected_item = self.fault_manager.get_item(value)
                        if selected_item:
                            value = selected_item.title
                
                self.detailTable.insertRow(row)
                self.detailTable.setItem(row, 0, QTableWidgetItem(field.label))
                self.detailTable.setItem(row, 1, QTableWidgetItem(str(value)))
                row += 1
    
    def _on_add_item(self):
        """新建条目"""
        project_id = self.projectComboBox.currentData()
        print(f"新建条目: project_id = {project_id}")
        if not project_id:
            QMessageBox.warning(self, self.tr("警告"), self.tr("请选择一个项目"))
            return
        
        # 检查是否选中了模板节点
        template_id = None
        selected_items = self.treeWidget.selectedItems()
        if selected_items:
            item = selected_items[0]
            data = item.data(0, Qt.UserRole)
            if data and isinstance(data, str):
                data_parts = data.split(":")
                if len(data_parts) == 2 and data_parts[0] == "template":
                    template_id = data_parts[1]
                    print(f"新建条目: 选中的模板ID = {template_id}")
        
        dialog = ItemEditorDialog(fault_manager=self.fault_manager, project_id=project_id, parent=self)
        
        # 如果选中了模板，设置默认模板
        if template_id:
            for i in range(dialog.templateComboBox.count()):
                if dialog.templateComboBox.itemData(i) == template_id:
                    dialog.templateComboBox.setCurrentIndex(i)
                    dialog._on_template_changed()
                    break
        
        if dialog.exec():
            item = dialog.get_item()
            template_id = item.template_id
            print(f"ItemManagerUI._on_add_item: template_id = {template_id}")
            if not template_id:
                QMessageBox.warning(self, self.tr("警告"), self.tr("请选择一个模板"))
                return
            # 创建新条目
            new_item = self.fault_manager.create_item(template_id, project_id, item.title)
            # 设置字段值
            new_item.field_values = item.field_values
            self.fault_manager.update_item(new_item)
            # 重新加载树状结构
            self._load_tree(project_id)
    
    def _on_edit_item(self):
        """编辑条目"""
        selected_items = self.treeWidget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, self.tr("警告"), self.tr("请选择一个条目"))
            return
        
        item = selected_items[0]
        data = item.data(0, Qt.UserRole)
        
        if data and isinstance(data, str):
            data_parts = data.split(":")
            if len(data_parts) == 2 and data_parts[0] == "item":
                item_id = data_parts[1]
                current_item = self.fault_manager.get_item(item_id)
                
                if current_item:
                    dialog = ItemEditorDialog(current_item, self.fault_manager, current_item.project_id, self)
                    if dialog.exec():
                        updated_item = dialog.get_item()
                        self.fault_manager.update_item(updated_item)
                        # 重新加载树状结构
                        self._load_tree(current_item.project_id)
                        # 重新选择编辑的条目
                        self._select_tree_item(f"item:{item_id}")
    
    def _select_tree_item(self, item_data):
        """选择树状结构中的指定条目"""
        def find_item(item):
            if item.data(0, Qt.UserRole) == item_data:
                self.treeWidget.setCurrentItem(item)
                return True
            for i in range(item.childCount()):
                child = item.child(i)
                if find_item(child):
                    return True
            return False
        
        for i in range(self.treeWidget.topLevelItemCount()):
            if find_item(self.treeWidget.topLevelItem(i)):
                break
    
    def _on_delete_item(self):
        """删除条目"""
        selected_items = self.treeWidget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, self.tr("警告"), self.tr("请选择一个条目"))
            return
        
        item = selected_items[0]
        data = item.data(0, Qt.UserRole)
        
        if data and isinstance(data, str):
            data_parts = data.split(":")
            if len(data_parts) == 2 and data_parts[0] == "item":
                item_id = data_parts[1]
                current_item = self.fault_manager.get_item(item_id)
                
                if current_item:
                    if QMessageBox.question(self, self.tr("确认"), 
                                           self.tr(f"确定要删除条目 '{current_item.title}' 吗？")) == QMessageBox.Yes:
                        project_id = current_item.project_id
                        self.fault_manager.delete_item(item_id)
                        # 重新加载树状结构
                        self._load_tree(project_id)
                        # 清空详情表格
                        self.detailTable.setRowCount(0)
                        self.detailTitle.setText(self.tr("条目详情"))