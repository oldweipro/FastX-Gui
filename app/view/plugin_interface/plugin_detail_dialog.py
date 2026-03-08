"""
插件详情对话框
以弹框形式展示插件信息，支持快捷操作
"""

from typing import Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFrame
)
from qfluentwidgets import (
    MessageBoxBase, CardWidget, BodyLabel, StrongBodyLabel, CaptionLabel,
    PushButton, PrimaryPushButton, TransparentPushButton,
    FluentIcon as FIF, IconWidget, ProgressRing,
    SubtitleLabel, TitleLabel, FluentIconBase, SwitchButton,
    isDarkTheme
)

from app.plugins.plugin_base import PluginInfo, PluginBase
from app.plugins.plugin_manager import PluginManager
from app.common.icon import Icon


class PluginDetailDialog(MessageBoxBase):
    """插件详情对话框 - 以弹框形式展示插件完整信息"""

    # 信号定义
    openPluginRequested = Signal(str)  # 打开插件（以Tab形式）
    pluginUninstalled = Signal(str)    # 插件卸载

    def __init__(self, plugin_name: str, plugin_manager: PluginManager, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.plugin_name = plugin_name
        self.plugin_manager = plugin_manager
        self.plugin_info = plugin_manager.get_plugin_info(plugin_name)
        self.plugin_instance = plugin_manager.get_plugin(plugin_name)

        print(f"[PluginDetailDialog] 初始化对话框: {plugin_name}")
        print(f"[PluginDetailDialog] 插件信息: {self.plugin_info}")
        print(f"[PluginDetailDialog] 插件实例: {self.plugin_instance}")

        self._init_content()
        self._setup_connections()

    def _init_content(self):
        """初始化内容"""
        # 标题
        self.titleLabel = TitleLabel(f"{self.plugin_info.name}", self)
        self.viewLayout.addWidget(self.titleLabel)

        # 副标题
        version_text = f"v{self.plugin_info.version} | {self._get_category_text()}"
        self.subtitleLabel = CaptionLabel(version_text, self)
        self.subtitleLabel.setStyleSheet("color: #888;")
        self.viewLayout.addWidget(self.subtitleLabel)

        self.viewLayout.addSpacing(12)

        # 主内容区域（左右分栏）
        self.content_layout = QHBoxLayout()
        self.content_layout.setSpacing(16)

        # 左侧：基本信息和描述
        self.left_widget = QWidget()
        self.left_layout = QVBoxLayout(self.left_widget)
        self.left_layout.setContentsMargins(0, 0, 0, 0)
        self.left_layout.setSpacing(12)

        # 基本信息卡片
        self._create_info_section()
        self.left_layout.addStretch(1)

        self.content_layout.addLayout(self.left_layout, 3)

        # 右侧：设置和操作
        self.right_widget = QWidget()
        self.right_layout = QVBoxLayout(self.right_widget)
        self.right_layout.setContentsMargins(0, 0, 0, 0)
        self.right_layout.setSpacing(12)

        # 快捷操作卡片
        self._create_actions_section()
        self.right_layout.addStretch(1)

        self.content_layout.addLayout(self.right_layout, 2)

        # 添加内容布局
        self.viewLayout.addLayout(self.content_layout)

        # 设置按钮
        self.yesButton.setText("打开插件")
        self.yesButton.setIcon(FIF.PLAY)
        self.cancelButton.setText("关闭")

        # 设置对话框大小
        self.widget.setMinimumWidth(700)
        self.widget.setMinimumHeight(500)

    def _create_info_section(self):
        """创建基本信息区域"""
        # 头部：图标 + 启用开关
        header_layout = QHBoxLayout()
        header_layout.setSpacing(16)

        # 图标
        icon = self._get_icon()
        self.icon_widget = IconWidget(icon, self)
        self.icon_widget.setFixedSize(64, 64)
        header_layout.addWidget(self.icon_widget)

        # 名称和版本
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)

        # 启用开关
        enable_layout = QHBoxLayout()
        enable_layout.setSpacing(8)

        self.enable_label = CaptionLabel("启用状态:", self)
        self.enable_label.setStyleSheet("color: #666;")
        enable_layout.addWidget(self.enable_label)

        self.enable_switch = SwitchButton(self)
        self.enable_switch.setChecked(self.plugin_info.enabled)
        self.enable_switch.setOnText("已启用")
        self.enable_switch.setOffText("已禁用")
        self.enable_switch.setFixedHeight(28)
        enable_layout.addWidget(self.enable_switch)

        enable_layout.addStretch(1)
        info_layout.addLayout(enable_layout)

        # 作者信息
        author_layout = QHBoxLayout()
        author_layout.setSpacing(8)

        author_icon = IconWidget(FIF.PEOPLE, self)
        author_icon.setFixedSize(16, 16)
        author_layout.addWidget(author_icon)

        self.author_label = BodyLabel(f"作者: {self.plugin_info.author}", self)
        self.author_label.setStyleSheet("font-size: 13px;")
        author_layout.addWidget(self.author_label)

        author_layout.addStretch(1)
        info_layout.addLayout(author_layout)

        header_layout.addLayout(info_layout, 1)
        self.left_layout.addLayout(header_layout)

        # 分隔线
        separator = QFrame(self.left_widget)
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #e0e0e0;")
        separator.setFixedHeight(1)
        self.left_layout.addWidget(separator)

        # 描述
        self.desc_title = SubtitleLabel("描述", self)
        self.desc_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.left_layout.addWidget(self.desc_title)

        self.desc_content = BodyLabel(self.plugin_info.description, self)
        self.desc_content.setWordWrap(True)
        self.desc_content.setStyleSheet("font-size: 13px; line-height: 1.6; color: #555;")
        self.left_layout.addWidget(self.desc_content)

        # 详细信息网格
        self.details_grid = QGridLayout()
        self.details_grid.setSpacing(12)
        self.details_grid.setColumnStretch(1, 1)

        details = [
            (FIF.TAG, "分类", self._get_category_text()),
            (FIF.DICTIONARY, "版本", f"v{self.plugin_info.version}"),
            (FIF.SETTING, "依赖", ", ".join(self.plugin_info.dependencies) or "无"),
        ]

        for row, (icon, label, value) in enumerate(details):
            # 图标
            icon_widget = IconWidget(icon, self)
            icon_widget.setFixedSize(16, 16)
            icon_widget.setStyleSheet("color: #666;")
            self.details_grid.addWidget(icon_widget, row, 0)

            # 标签
            key_label = CaptionLabel(f"{label}:", self)
            key_label.setStyleSheet("color: #666; font-size: 12px;")
            self.details_grid.addWidget(key_label, row, 1)

            # 值
            value_label = BodyLabel(value, self)
            value_label.setStyleSheet("font-size: 13px;")
            self.details_grid.addWidget(value_label, row, 2)

        self.left_layout.addLayout(self.details_grid)

    def _create_actions_section(self):
        """创建操作区域"""
        # 快捷操作卡片
        actions_card = CardWidget(self.right_widget)
        actions_layout = QVBoxLayout(actions_card)
        actions_layout.setContentsMargins(16, 12, 16, 12)
        actions_layout.setSpacing(8)

        actions_title = SubtitleLabel("快捷操作", self)
        actions_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        actions_layout.addWidget(actions_title)

        # 打开插件目录
        folder_btn = TransparentPushButton(FIF.FOLDER, "打开插件目录", actions_card)
        folder_btn.setFixedHeight(32)
        folder_btn.clicked.connect(self._on_open_folder)
        actions_layout.addWidget(folder_btn)

        # 重置设置
        reset_btn = TransparentPushButton(FIF.UPDATE, "重置设置", actions_card)
        reset_btn.setFixedHeight(32)
        reset_btn.clicked.connect(self._on_reset_settings)
        actions_layout.addWidget(reset_btn)

        # 检查更新
        update_btn = TransparentPushButton(FIF.CLOUD_DOWNLOAD, "检查更新", actions_card)
        update_btn.setFixedHeight(32)
        actions_layout.addWidget(update_btn)

        self.right_layout.addWidget(actions_card)

        # 设置卡片 - 调用插件自定义设置界面
        settings_card = CardWidget(self.right_widget)
        settings_layout = QVBoxLayout(settings_card)
        settings_layout.setContentsMargins(16, 12, 16, 12)
        settings_layout.setSpacing(8)

        settings_title = SubtitleLabel("插件配置", self)
        settings_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        settings_layout.addWidget(settings_title)

        if self.plugin_instance:
            settings_widget = self.plugin_instance.get_settings_widget(settings_card)
            if settings_widget is not None:
                # 插件提供了自定义设置界面
                settings_layout.addWidget(settings_widget)
            else:
                # 回落到展示 raw config dict
                plugin_config = self.plugin_instance.get_config()
                if plugin_config:
                    for key, value in plugin_config.items():
                        row_layout = QHBoxLayout()
                        row_layout.setSpacing(8)
                        key_label = CaptionLabel(key, settings_card)
                        row_layout.addWidget(key_label)
                        row_layout.addStretch(1)
                        if isinstance(value, bool):
                            switch = SwitchButton(settings_card)
                            switch.setChecked(value)
                            switch.setFixedHeight(24)
                            row_layout.addWidget(switch)
                        else:
                            value_label = CaptionLabel(str(value) if value else "未设置", settings_card)
                            value_label.setStyleSheet("color: #666;")
                            row_layout.addWidget(value_label)
                        settings_layout.addLayout(row_layout)
                else:
                    no_config = CaptionLabel("暂无配置项", settings_card)
                    no_config.setStyleSheet("color: #888; font-style: italic;")
                    settings_layout.addWidget(no_config)
        else:
            no_instance = CaptionLabel("插件实例未加载", settings_card)
            no_instance.setStyleSheet("color: #888; font-style: italic;")
            settings_layout.addWidget(no_instance)

        self.right_layout.addWidget(settings_card)

        # 危险操作（仅非内置插件显示）
        is_builtin = getattr(self.plugin_info, 'builtin', False)
        if not is_builtin:
            danger_card = CardWidget(self.right_widget)
            danger_layout = QVBoxLayout(danger_card)
            danger_layout.setContentsMargins(16, 12, 16, 12)
            danger_layout.setSpacing(8)

            danger_title = SubtitleLabel("危险操作", self)
            danger_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #d13438;")
            danger_layout.addWidget(danger_title)

            uninstall_btn = PushButton(FIF.DELETE, "卸载插件", danger_card)
            uninstall_btn.setFixedHeight(32)
            uninstall_btn.setStyleSheet("color: #d13438;")
            uninstall_btn.clicked.connect(self._on_uninstall)
            danger_layout.addWidget(uninstall_btn)

            self.right_layout.addWidget(danger_card)

    def _setup_connections(self):
        """设置信号连接"""
        print(f"[PluginDetailDialog] 设置信号连接: {self.plugin_name}")
        self.enable_switch.checkedChanged.connect(self._on_enable_changed)

    def _get_icon(self):
        """获取插件图标"""
        if self.plugin_info.icon_path:
            try:
                if isinstance(self.plugin_info.icon_path, str):
                    if hasattr(Icon, self.plugin_info.icon_path):
                        return getattr(Icon, self.plugin_info.icon_path)
                elif isinstance(self.plugin_info.icon_path, (FluentIconBase, FIF)):
                    return self.plugin_info.icon_path
            except Exception:
                pass
        return FIF.PLUGIN

    def _get_category_text(self) -> str:
        """获取分类显示文本"""
        from app.plugins.plugin_base import PluginCategory

        category_texts = {
            PluginCategory.DIAGNOSTIC: "诊断工具",
            PluginCategory.COMMUNICATION: "通信工具",
            PluginCategory.SERIAL: "串口工具",
            PluginCategory.UTILITIES: "实用工具",
            PluginCategory.CUSTOM: "自定义"
        }
        return category_texts.get(self.plugin_info.category, "未知")

    def _on_enable_changed(self, enabled: bool):
        """启用/禁用状态改变"""
        self.plugin_info.enabled = enabled
        print(f"[PluginDetailDialog] 插件 '{self.plugin_name}' 状态改变: {'已启用' if enabled else '已禁用'}")

    def _on_open_folder(self):
        """打开插件目录"""
        import os
        from pathlib import Path

        print(f"[PluginDetailDialog] 尝试打开插件目录: {self.plugin_name}")
        
        plugin_dir = Path(self.plugin_instance.__module__.__file__).parent if self.plugin_instance else None
        if plugin_dir and plugin_dir.exists():
            print(f"[PluginDetailDialog] 打开目录: {plugin_dir}")
            os.startfile(str(plugin_dir))
        else:
            print(f"[PluginDetailDialog] 无法找到插件目录", plugin_dir)

    def _on_reset_settings(self):
        """重置设置"""
        print(f"[PluginDetailDialog] 重置插件设置: {self.plugin_name}")
        if self.plugin_instance:
            self.plugin_instance.set_config({})
            print(f"[PluginDetailDialog] 设置已重置")

    def _on_uninstall(self):
        """卸载插件"""
        from PySide6.QtWidgets import QMessageBox

        print(f"[PluginDetailDialog] 请求卸载插件: {self.plugin_name}")

        reply = QMessageBox.question(
            self,
            "确认卸载",
            f"确定要卸载插件 '{self.plugin_name}' 吗？\n此操作不可撤销。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            print(f"[PluginDetailDialog] 确认卸载: {self.plugin_name}")
            self.plugin_manager.registry.unregister_plugin(self.plugin_name)
            self.pluginUninstalled.emit(self.plugin_name)
            self.reject()  # 关闭对话框
        else:
            print(f"[PluginDetailDialog] 取消卸载: {self.plugin_name}")

    def validate(self):
        """点击确定按钮时触发"""
        print(f"[PluginDetailDialog] 点击打开插件按钮: {self.plugin_name}")
        # 发出打开插件信号
        self.openPluginRequested.emit(self.plugin_name)
        print(f"[PluginDetailDialog] 信号已发送: openPluginRequested")
        return True
