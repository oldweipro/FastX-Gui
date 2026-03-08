"""
插件列表卡片组件
用于左侧插件列表，控制插件的启用/禁用状态
"""

from typing import Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel
from qfluentwidgets import (
    CardWidget, BodyLabel, CaptionLabel, StrongBodyLabel,
    SwitchButton, FluentIcon as FIF, IconWidget, FluentIconBase, isDarkTheme
)

from app.plugins.plugin_base import PluginInfo, PluginCategory


class PluginListCard(CardWidget):
    """插件列表卡片 - 紧凑的卡片形式，用于左侧列表控制插件启用/禁用"""
    
    # 信号定义
    toggled = Signal(str, bool)  # 插件名, 新状态
    
    def __init__(self, plugin_info: PluginInfo, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.plugin_info = plugin_info
        self._is_enabled = plugin_info.enabled
        
        self._init_ui()
        self._setup_connections()
    
    def _init_ui(self):
        """初始化UI - 紧凑的卡片布局"""
        self.setFixedHeight(56)
        # self.setBorderRadius(8)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # 设置卡片样式
        self._update_style()
        
        # 主布局
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(12, 8, 12, 8)
        self.layout.setSpacing(10)
        
        # 插件图标
        icon = self._get_icon()
        self.icon_widget = IconWidget(icon, self)
        self.icon_widget.setFixedSize(28, 28)
        self.layout.addWidget(self.icon_widget)
        
        # 插件信息（名称和版本）
        self.info_layout = QVBoxLayout()
        self.info_layout.setSpacing(2)
        
        # 插件名称
        self.name_label = StrongBodyLabel(self.plugin_info.name, self)
        self.name_label.setStyleSheet("font-size: 13px;")
        self.info_layout.addWidget(self.name_label)
        
        # 版本和分类
        self.meta_layout = QHBoxLayout()
        self.meta_layout.setSpacing(6)
        
        self.version_label = CaptionLabel(f"Version: {self.plugin_info.version}", self)
        self.version_label.setStyleSheet("color: #0078d4; font-size: 11px;")
        self.meta_layout.addWidget(self.version_label)
        
        separator = CaptionLabel(" | ", self)
        separator.setStyleSheet("color: #999; font-size: 11px;")
        self.meta_layout.addWidget(separator)
        
        self.category_label = CaptionLabel(f"Category: {self._get_category_text()}", self)
        self.category_label.setStyleSheet("color: #666; font-size: 11px;")
        self.meta_layout.addWidget(self.category_label)
        
        self.meta_layout.addStretch(1)
        self.info_layout.addLayout(self.meta_layout)
        
        self.layout.addLayout(self.info_layout, 1)
        
        # 启用/禁用开关
        self.enable_switch = SwitchButton(self)
        self.enable_switch.setChecked(self._is_enabled)
        self.enable_switch.setOnText("显示")
        self.enable_switch.setOffText("隐藏")
        self._update_tooltip()
        self.layout.addWidget(self.enable_switch)

        # 内置插件：开关禁用、显示“内置”徽章
        if getattr(self.plugin_info, 'builtin', False):
            self.enable_switch.setEnabled(False)
            self.enable_switch.setToolTip("内置插件不可禁用")
            badge = CaptionLabel("内置", self)
            badge.setStyleSheet(
                "color: #fff; background-color: #0078d4;"
                "border-radius: 4px; padding: 1px 5px; font-size: 10px;"
            )
            self.layout.addWidget(badge)
    
    def _setup_connections(self):
        """设置信号连接"""
        self.enable_switch.checkedChanged.connect(self._on_switch_changed)
    
    def _on_switch_changed(self, checked: bool):
        """开关状态改变"""
        self._is_enabled = checked
        self.plugin_info.enabled = checked
        self._update_tooltip()
        self._update_style()
        self.toggled.emit(self.plugin_info.name, checked)
    
    def _update_tooltip(self):
        """更新工具提示"""
        if self._is_enabled:
            self.enable_switch.setToolTip("点击禁用插件")
        else:
            self.enable_switch.setToolTip("点击启用插件")
    
    def _update_style(self):
        """更新卡片样式"""
        if isDarkTheme():
            if self._is_enabled:
                style = """
                    PluginListCard {
                        background-color: rgba(45, 45, 45, 0.6);
                        border: 1px solid rgba(0, 120, 212, 0.3);
                        border-radius: 8px;
                    }
                """
            else:
                style = """
                    PluginListCard {
                        background-color: rgba(30, 30, 30, 0.4);
                        border: 1px solid rgba(80, 80, 80, 0.3);
                        border-radius: 8px;
                    }
                """
        else:
            if self._is_enabled:
                style = """
                    PluginListCard {
                        background-color: rgba(240, 248, 255, 0.9);
                        border: 1px solid rgba(0, 120, 212, 0.3);
                        border-radius: 8px;
                    }
                """
            else:
                style = """
                    PluginListCard {
                        background-color: rgba(245, 245, 245, 0.6);
                        border: 1px solid rgba(200, 200, 200, 0.5);
                        border-radius: 8px;
                    }
                """
        self.setStyleSheet(style)
    
    def _get_icon(self):
        """获取插件图标"""
        if self.plugin_info.icon_path:
            try:
                if isinstance(self.plugin_info.icon_path, str):
                    from app.common.icon import Icon
                    if hasattr(Icon, self.plugin_info.icon_path):
                        return getattr(Icon, self.plugin_info.icon_path)
                elif isinstance(self.plugin_info.icon_path, (FluentIconBase, FIF)):
                    return self.plugin_info.icon_path
            except Exception:
                pass
        return FIF.APPLICATION
    
    def _get_category_text(self) -> str:
        """获取分类显示文本"""
        category_texts = {
            PluginCategory.DIAGNOSTIC: "诊断",
            PluginCategory.COMMUNICATION: "通信",
            PluginCategory.SERIAL: "串口",
            PluginCategory.UTILITIES: "工具",
            PluginCategory.CUSTOM: "自定义"
        }
        return category_texts.get(self.plugin_info.category, "未知")
    
    def set_enabled_state(self, enabled: bool):
        """设置启用状态（外部调用）"""
        self._is_enabled = enabled
        self.plugin_info.enabled = enabled
        self.enable_switch.setChecked(enabled)
        self._update_tooltip()
        self._update_style()
    
    def is_enabled(self) -> bool:
        """获取启用状态"""
        return self._is_enabled
