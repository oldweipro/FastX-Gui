from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, 
                               QLineEdit, QTextEdit, QComboBox, QCheckBox, QSpinBox, 
                               QScrollArea, QGroupBox, QGridLayout)
from qfluentwidgets import (
    FluentIcon as FIF,
    SubtitleLabel,
    BodyLabel,
    ElevatedCardWidget,
    PushButton,
    PrimaryPushButton,
    ToolTip
)

from app.model.fault_model import Template, Item


class FormRenderer(QWidget):
    """表单渲染器，根据模板生成表单"""
    def __init__(self, template: Template = None, item: Item = None, parent=None):
        super().__init__(parent)
        self.template = template
        self.item = item
        self.field_widgets = {}
        self._init_ui()
    
    def _init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        
        # 标题
        if self.template:
            layout.addWidget(SubtitleLabel(self.template.name, self))
            if self.template.description:
                layout.addWidget(BodyLabel(self.template.description, self))
        
        # 表单区域
        self.formScrollArea = QScrollArea(self)
        self.formScrollArea.setWidgetResizable(True)
        self.formWidget = QWidget()
        self.formLayout = QVBoxLayout(self.formWidget)
        self.formScrollArea.setWidget(self.formWidget)
        layout.addWidget(self.formScrollArea)
        
        # 渲染表单
        if self.template:
            self._render_form()
    
    def _render_form(self):
        """渲染表单"""
        # 渲染模板字段
        self._render_template_fields(self.template)
    
    def _render_template_fields(self, template: Template, parent_layout=None):
        """渲染模板及其子模板的字段"""
        if parent_layout is None:
            parent_layout = self.formLayout
        
        # 为子模板创建分组
        if template != self.template:
            group_box = QGroupBox(template.name)
            group_layout = QFormLayout(group_box)
            parent_layout.addWidget(group_box)
            current_layout = group_layout
        else:
            current_layout = parent_layout
        
        # 渲染字段
        for field in template.fields:
            self._render_field(field, current_layout)
        
        # 渲染子模板
        for sub_template_id in template.sub_templates:
            # 这里假设子模板已经加载
            # 在实际使用中，需要从FaultManager中获取子模板
            # 这里简化处理，假设传入的是完整的模板对象
            pass
    
    def _render_field(self, field, layout):
        """渲染单个字段"""
        label = QLabel(f"{field.label}{' *' if field.required else ''}")
        
        if field.field_type == "text":
            widget = QLineEdit()
            widget.setPlaceholderText(field.label)
        elif field.field_type == "number":
            widget = QSpinBox()
            widget.setRange(-999999, 999999)
        elif field.field_type == "checkbox":
            widget = QCheckBox()
        elif field.field_type == "select":
            widget = QComboBox()
            widget.addItems(field.options)
            widget.setPlaceholderText("请选择")
        elif field.field_type == "textarea":
            widget = QTextEdit()
            widget.setPlaceholderText(field.label)
            widget.setMinimumHeight(100)
        else:
            widget = QLineEdit()
            widget.setPlaceholderText(field.label)
        
        # 设置默认值
        if self.item and field.id in self.item.field_values:
            value = self.item.field_values[field.id]
            if field.field_type == "text" or field.field_type == "textarea":
                widget.setText(str(value))
            elif field.field_type == "number":
                widget.setValue(int(value))
            elif field.field_type == "checkbox":
                widget.setChecked(bool(value))
            elif field.field_type == "select":
                index = widget.findText(str(value))
                if index >= 0:
                    widget.setCurrentIndex(index)
        elif field.default is not None:
            if field.field_type == "text" or field.field_type == "textarea":
                widget.setText(str(field.default))
            elif field.field_type == "number":
                widget.setValue(int(field.default))
            elif field.field_type == "checkbox":
                widget.setChecked(bool(field.default))
            elif field.field_type == "select":
                index = widget.findText(str(field.default))
                if index >= 0:
                    widget.setCurrentIndex(index)
        
        # 存储字段控件
        self.field_widgets[field.id] = (widget, field.field_type)
        
        # 添加到布局
        if field.field_type == "checkbox":
            # 复选框特殊处理，标签在右侧
            h_layout = QHBoxLayout()
            h_layout.addWidget(widget)
            h_layout.addWidget(label)
            h_layout.addStretch()
            layout.addRow(h_layout)
        else:
            layout.addRow(label, widget)
    
    def get_form_data(self) -> dict:
        """获取表单数据"""
        data = {}
        for field_id, (widget, field_type) in self.field_widgets.items():
            if field_type == "text" or field_type == "textarea":
                data[field_id] = widget.toPlainText() if hasattr(widget, "toPlainText") else widget.text()
            elif field_type == "number":
                data[field_id] = widget.value()
            elif field_type == "checkbox":
                data[field_id] = widget.isChecked()
            elif field_type == "select":
                data[field_id] = widget.currentText()
        return data
    
    def set_form_data(self, data: dict):
        """设置表单数据"""
        for field_id, value in data.items():
            if field_id in self.field_widgets:
                widget, field_type = self.field_widgets[field_id]
                if field_type == "text" or field_type == "textarea":
                    widget.setText(str(value))
                elif field_type == "number":
                    widget.setValue(int(value))
                elif field_type == "checkbox":
                    widget.setChecked(bool(value))
                elif field_type == "select":
                    index = widget.findText(str(value))
                    if index >= 0:
                        widget.setCurrentIndex(index)
    
    def update_template(self, template: Template):
        """更新模板"""
        self.template = template
        self.field_widgets.clear()
        
        # 清空布局
        for i in reversed(range(self.formLayout.count())):
            widget = self.formLayout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        
        # 重新渲染表单
        self._render_form()
    
    def update_item(self, item: Item):
        """更新条目"""
        self.item = item
        self.set_form_data(item.field_values if item else {})


class FormPreviewDialog(QWidget):
    """表单预览对话框"""
    def __init__(self, template: Template, item: Item = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("表单预览")
        self.resize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # 表单渲染器
        self.form_renderer = FormRenderer(template, item, self)
        layout.addWidget(self.form_renderer)
        
        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.close_button = PushButton(FIF.CLOSE, "关闭", self)
        button_layout.addWidget(self.close_button)
        layout.addLayout(button_layout)
        
        # 连接信号
        self.close_button.clicked.connect(self.close)
    
    def get_form_data(self) -> dict:
        """获取表单数据"""
        return self.form_renderer.get_form_data()
    
    def set_form_data(self, data: dict):
        """设置表单数据"""
        self.form_renderer.set_form_data(data)