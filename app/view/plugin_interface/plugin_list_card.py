"""
插件列表卡片组件
用于左侧插件列表，控制插件的显示/隐藏状态，支持拖拽排序
"""

from typing import Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout
from qfluentwidgets import (
    CardWidget, CaptionLabel, StrongBodyLabel,
    SwitchButton, FluentIcon as FIF, IconWidget, FluentIconBase,
    TransparentToolButton, isDarkTheme
)

from app.plugins.plugin_base import PluginInfo, PluginCategory


class PluginListCard(CardWidget):
    """
    插件列表卡片 - 紧凑卡片，控制插件显示/隐藏。
    内置插件：开关正常可用；卸载按钮置灰不可点击。
    非内置插件：开关正常可用；卸载按钮可点击。
    """

    toggled = Signal(str, bool)       # 插件名, 新显示状态
    uninstallRequested = Signal(str)  # 卸载请求

    def __init__(self, plugin_info: PluginInfo, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.plugin_info = plugin_info
        self._is_enabled = plugin_info.enabled

        self._init_ui()
        self._setup_connections()

    def _init_ui(self):
        self.setFixedHeight(56)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._update_style()

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(12, 8, 8, 8)
        self.layout.setSpacing(10)

        # 拖拽手柄图标（提示用户可拖拽）
        self.drag_handle = IconWidget(FIF.MENU, self)
        self.drag_handle.setFixedSize(14, 14)
        self.drag_handle.setToolTip("拖动以调整顺序")
        self.layout.addWidget(self.drag_handle)

        # 插件图标
        self.icon_widget = IconWidget(self._get_icon(), self)
        self.icon_widget.setFixedSize(28, 28)
        self.layout.addWidget(self.icon_widget)

        # 插件信息列
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        info_layout.setContentsMargins(0, 0, 0, 0)

        self.name_label = StrongBodyLabel(self.plugin_info.name, self)
        self.name_label.setStyleSheet("font-size: 12px;")
        info_layout.addWidget(self.name_label)

        meta_layout = QHBoxLayout()
        meta_layout.setSpacing(4)
        meta_layout.setContentsMargins(0, 0, 0, 0)

        self.version_label = CaptionLabel(f"v{self.plugin_info.version}", self)
        self.version_label.setStyleSheet("color: #0078d4; font-size: 10px;")
        meta_layout.addWidget(self.version_label)

        sep = CaptionLabel("·", self)
        sep.setStyleSheet("font-size: 10px;")
        meta_layout.addWidget(sep)

        self.category_label = CaptionLabel(self._get_category_text(), self)
        self.category_label.setStyleSheet("font-size: 10px;")
        meta_layout.addWidget(self.category_label)
        meta_layout.addStretch(1)
        info_layout.addLayout(meta_layout)

        self.layout.addLayout(info_layout, 1)

        # 卸载按钮（内置插件置灰）
        self.uninstall_btn = TransparentToolButton(FIF.DELETE, self)
        self.uninstall_btn.setFixedSize(24, 24)
        self.uninstall_btn.setToolTip("卸载插件" if not self.plugin_info.builtin else "内置插件不可卸载")
        self.uninstall_btn.setEnabled(not self.plugin_info.builtin)
        self.layout.addWidget(self.uninstall_btn)

        # 显示/隐藏开关（所有插件均可操作）
        self.enable_switch = SwitchButton(self)
        self.enable_switch.setChecked(self._is_enabled)
        self.enable_switch.setOnText("显示")
        self.enable_switch.setOffText("隐藏")
        self._update_tooltip()
        self.layout.addWidget(self.enable_switch)

    def _setup_connections(self):
        self.enable_switch.checkedChanged.connect(self._on_switch_changed)
        self.uninstall_btn.clicked.connect(
            lambda: self.uninstallRequested.emit(self.plugin_info.name)
        )

    def _on_switch_changed(self, checked: bool):
        self._is_enabled = checked
        self.plugin_info.enabled = checked
        self._update_tooltip()
        self._update_style()
        self.toggled.emit(self.plugin_info.name, checked)

    def _update_tooltip(self):
        self.enable_switch.setToolTip("点击隐藏插件" if self._is_enabled else "点击显示插件")

    def _update_style(self):
        dark = isDarkTheme()
        if dark:
            if self._is_enabled:
                style = """
                    PluginListCard {
                        background-color: rgba(45, 45, 50, 0.7);
                        border: 1px solid rgba(0, 120, 212, 0.25);
                        border-radius: 8px;
                    }
                """
            else:
                style = """
                    PluginListCard {
                        background-color: rgba(28, 28, 30, 0.5);
                        border: 1px solid rgba(70, 70, 75, 0.4);
                        border-radius: 8px;
                    }
                """
        else:
            if self._is_enabled:
                style = """
                    PluginListCard {
                        background-color: rgba(240, 248, 255, 0.85);
                        border: 1px solid rgba(0, 120, 212, 0.25);
                        border-radius: 8px;
                    }
                """
            else:
                style = """
                    PluginListCard {
                        background-color: rgba(245, 245, 248, 0.6);
                        border: 1px solid rgba(200, 200, 205, 0.5);
                        border-radius: 8px;
                    }
                """
        self.setStyleSheet(style)

    def _get_icon(self):
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
        return {
            PluginCategory.DIAGNOSTIC:    "诊断",
            PluginCategory.COMMUNICATION: "通信",
            PluginCategory.SERIAL:        "串口",
            PluginCategory.UTILITIES:     "工具",
            PluginCategory.CUSTOM:        "自定义",
        }.get(self.plugin_info.category, "未知")

    def set_enabled_state(self, enabled: bool):
        self._is_enabled = enabled
        self.plugin_info.enabled = enabled
        self.enable_switch.setChecked(enabled)
        self._update_tooltip()
        self._update_style()

    def is_enabled(self) -> bool:
        return self._is_enabled
