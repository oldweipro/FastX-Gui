"""
增强的对话框组件 - 提供统一的样式、动画和交互体验
"""

from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QPoint
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from qfluentwidgets import (
    MessageBoxBase,
    IconWidget,
    FluentIcon as FIF,
    BodyLabel,
    StrongBodyLabel,
    SubtitleLabel,
    InfoBarIcon,
)


class EnhancedMessageBox(MessageBoxBase):
    """
    增强的消息框基类
    
    特性:
    - 统一的视觉样式
    - 平滑的打开/关闭动画
    - 可自定义的图标和标题
    - 更好的响应式布局
    """
    
    def __init__(
        self,
        parent=None,
        title: str = "",
        content: str = "",
        icon=None,
        show_icon: bool = True,
    ):
        super().__init__(parent)
        
        self._title_text = title
        self._content_text = content
        self._icon = icon or FIF.MESSAGE
        self._show_icon = show_icon
        
        # 设置最小宽度
        self.widget.setMinimumWidth(450)
        
        # 构建 UI
        self._setup_ui()
        
        # 应用动画
        self._apply_animation()
    
    def _setup_ui(self):
        """设置 UI"""
        # 图标区域（如果显示）
        if self._show_icon:
            icon_widget = IconWidget(self._icon, self)
            icon_widget.setFixedSize(48, 48)
            
            # 标题区域
            title_label = StrongBodyLabel(self._title_text, self)
            title_label.setFont(QFont("Microsoft YaHei UI", 14, QFont.Bold))
            
            content_label = BodyLabel(self._content_text, self)
            content_label.setWordWrap(True)
            content_label.setStyleSheet("color: gray; margin-top: 4px;")
            
            # 布局
            header_layout = QHBoxLayout()
            header_layout.addWidget(icon_widget)
            header_layout.addSpacing(12)
            
            text_layout = QVBoxLayout()
            text_layout.setSpacing(4)
            text_layout.addWidget(title_label)
            text_layout.addWidget(content_label)
            
            header_layout.addLayout(text_layout)
            header_layout.addStretch()
            
            # 插入到主布局顶部
            self.viewLayout.insertLayout(0, header_layout)
        else:
            # 只显示文本
            title_label = SubtitleLabel(self._title_text, self)
            self.viewLayout.insertWidget(0, title_label)
            
            if self._content_text:
                content_label = BodyLabel(self._content_text, self)
                content_label.setWordWrap(True)
                self.viewLayout.insertWidget(1, content_label)
    
    def _apply_animation(self):
        """应用打开动画"""
        # 这里可以添加窗口淡入动画
        # 由于 MessageBoxBase 已经有很好的默认行为，这里是可选的
        pass
    
    def add_custom_widget(self, widget: QWidget, index: int = -1):
        """
        添加自定义组件到对话框
        
        Args:
            widget: 要添加的组件
            index: 插入位置，-1 表示添加到末尾
        """
        if index == -1:
            self.viewLayout.addWidget(widget)
        else:
            self.viewLayout.insertWidget(index, widget)
    
    def set_yes_button_text(self, text: str, icon=None):
        """设置确认按钮文本和图标"""
        self.yesButton.setText(text)
        if icon:
            self.yesButton.setIcon(icon)
    
    def set_cancel_button_text(self, text: str, icon=None):
        """设置取消按钮文本和图标"""
        self.cancelButton.setText(text)
        if icon:
            self.cancelButton.setIcon(icon)


class FormMessageBox(EnhancedMessageBox):
    """
    表单消息框 - 用于输入表单
    
    示例:
        dlg = FormMessageBox(parent, title="新建项目", content="请填写项目信息")
        dlg.add_field("项目名称", LineEdit())
        dlg.add_field("描述", TextEdit())
        if dlg.exec():
            data = dlg.get_data()
    """
    
    def __init__(self, parent=None, title: str = "", content: str = ""):
        super().__init__(parent, title, content, icon=FIF.EDIT)
        
        self._fields = {}
        self._field_layout = QVBoxLayout()
        self._field_layout.setSpacing(12)
        
        # 添加表单容器
        container = QWidget()
        container.setLayout(self._field_layout)
        self.add_custom_widget(container)
    
    def add_field(self, name: str, widget: QWidget, required: bool = False):
        """
        添加表单项
        
        Args:
            name: 字段名称
            widget: 输入组件
            required: 是否必填
        """
        from qfluentwidgets import CaptionLabel
        
        # 标签
        label_text = f"{name}{' *' if required else ''}"
        label = CaptionLabel(label_text, self)
        label.setStyleSheet("font-weight: bold; margin-bottom: 4px;")
        
        self._field_layout.addWidget(label)
        self._field_layout.addWidget(widget)
        
        # 存储引用
        self._fields[name] = widget
    
    def get_data(self) -> dict:
        """获取表单数据"""
        data = {}
        for name, widget in self._fields.items():
            # 尝试获取常见组件的值
            if hasattr(widget, 'text'):
                data[name] = widget.text()
            elif hasattr(widget, 'toPlainText'):
                data[name] = widget.toPlainText()
            elif hasattr(widget, 'currentText'):
                data[name] = widget.currentText()
            else:
                data[name] = None
        return data
