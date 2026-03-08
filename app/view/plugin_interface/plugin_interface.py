"""
插件管理界面 - 插件化工具Hub
集成插件管理、卡片展示、详情页、面包屑导航等完整功能
"""

from typing import Dict
from PySide6.QtCore import Qt, Signal, QTimer, QSize
from PySide6.QtWidgets import (
    QHBoxLayout,
    QScroller,
    QScrollerProperties,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
    QSplitter,
)
from qfluentwidgets import FluentIcon as FIF, LineEditButton
from qfluentwidgets import (
    ScrollArea,
    FlowLayout,
    ComboBox,
    SearchLineEdit,
    PrimaryPushButton,
    CaptionLabel,
    TransparentToolButton,
    TabBar,
    TabCloseButtonDisplayMode,
    StrongBodyLabel,
)

from app.common.config import cfg
from app.common.style_sheet import StyleSheet

# 导入插件系统
from app.plugins import PluginManager, PluginCategory
from .plugin_card import PluginCard
from .plugin_list_card import PluginListCard
from .plugin_detail_dialog import PluginDetailDialog


class PluginInterface(ScrollArea):
    """插件管理界面 - 完整的插件管理平台"""

    # 信号定义
    pluginOpened = Signal(str)

    def __init__(self, parent=None):
        """
        初始化插件管理界面

        Args:
            parent: 父级窗口，默认为None
        """
        super().__init__(parent)
        self.view = QWidget(self)

        # 插件管理器
        self.plugin_manager = PluginManager()
        self.plugin_cards: Dict[str, PluginCard] = {}
        self.plugin_list_cards: Dict[str, PluginListCard] = {}  # 左侧列表卡片
        self._current_category = None
        self._current_search = ""

        # 插件Tab管理
        self.plugin_tabs = {}  # 存储已打开的插件Tab
        self.tab_count = 0

        # 左侧面板状态（默认收缩）
        self._left_panel_expanded = False

        self.__initWidget()
        self.__initLayout()
        self._load_plugins()
        self.__connectSignalToSlot()

    def __initWidget(self):
        # 设置对象名称用于样式表
        self.setObjectName("pluginInterface")
        # 创建视图容器
        self.view.setObjectName("view")
        # 设置滚动区域属性
        self.setViewportMargins(0, 48, 0, 0)
        self.setWidget(self.view)
        # 允许widget调整大小
        self.setWidgetResizable(True)
        # 设置纵向滚动条政策
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.__setupSmoothScroll()
        # 应用样式表
        StyleSheet.PLUGIN_INTERFACE.apply(self)

    def __setupSmoothScroll(self):
        QScroller.grabGesture(
            self.viewport(),
            QScroller.ScrollerGestureType.LeftMouseButtonGesture,
        )
        scroller = QScroller.scroller(self.viewport())
        scroller_props = scroller.scrollerProperties()
        scroller_props.setScrollMetric(QScrollerProperties.ScrollMetric.OvershootDragDistanceFactor, 0.05)
        scroller_props.setScrollMetric(
            QScrollerProperties.ScrollMetric.OvershootScrollDistanceFactor,
            0.05,
        )
        scroller_props.setScrollMetric(QScrollerProperties.ScrollMetric.DecelerationFactor, 0.5)
        scroller.setScrollerProperties(scroller_props)

    def __initLayout(self):
        """初始化布局"""
        self.Layout = QHBoxLayout(self.view)
        self.Layout.setContentsMargins(0, 0, 0, 0)

        self.main_layout = QVBoxLayout()
        self.main_layout.setObjectName("mainLayout")
        self.main_layout.setContentsMargins(12, 10, 36, 36)
        self.main_layout.setSpacing(16)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.Layout.addLayout(self.main_layout)

        # Tab栏和内容区域
        self.tab_bar = TabBar(self)
        self.tab_bar.setCloseButtonDisplayMode(TabCloseButtonDisplayMode.ON_HOVER)
        self.tab_bar.tabCloseRequested.connect(self._on_tab_close_requested)
        self.main_layout.addWidget(self.tab_bar)

        # Tab内容容器
        self.tab_stack = QStackedWidget()
        self.main_layout.addWidget(self.tab_stack)

        # 插件管理页（默认页）
        self.plugin_manager_page = QWidget()
        self._setup_plugin_manager_page()
        self.tab_stack.addWidget(self.plugin_manager_page)

        # 添加默认Tab
        self.tab_bar.addTab(
            routeKey="plugin_manager",
            text="插件管理",
            icon=FIF.HOME,
            onClick=lambda: self.tab_stack.setCurrentWidget(self.plugin_manager_page)
        )

    def _setup_plugin_manager_page(self):
        """设置插件管理页面 - 左右分栏布局"""
        page_layout = QHBoxLayout(self.plugin_manager_page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(0)

        # 创建分割器，隐藏分割线
        self.splitter = QSplitter(Qt.Orientation.Horizontal, self.plugin_manager_page)
        self.splitter.setHandleWidth(0)
        self.splitter.setChildrenCollapsible(False)

        # ========== 左侧面板 - 插件列表 ==========
        self.left_panel = QWidget()
        self.left_panel.setObjectName("left_panel")
        self.left_panel.setMinimumWidth(280)

        self.left_layout = QVBoxLayout(self.left_panel)
        self.left_layout.setContentsMargins(12, 12, 12, 12)
        self.left_layout.setSpacing(8)

        # 左侧标题
        self.left_title = StrongBodyLabel("插件列表", self.left_panel)
        self.left_title.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.left_layout.addWidget(self.left_title)

        # 左侧统计信息
        self.left_stats = CaptionLabel("共 0 个插件", self.left_panel)
        self.left_stats.setStyleSheet("color: #666;")
        self.left_layout.addWidget(self.left_stats)

        # 左侧滚动区域
        self.left_scroll = ScrollArea(self.left_panel)
        self.left_scroll.setWidgetResizable(True)
        self.left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # self.left_scroll.setStyleSheet("ScrollArea { border: none; background: transparent; }")

        # 左侧卡片容器
        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(8)
        self.list_layout.addStretch(1)
        self.left_scroll.setWidget(self.list_container)
        self.left_layout.addWidget(self.left_scroll)

        # ========== 右侧面板 - 插件卡片 ==========
        self.right_panel = QWidget()
        self.right_panel.setObjectName("right_panel")
        self.right_layout = QVBoxLayout(self.right_panel)
        self.right_layout.setContentsMargins(12, 12, 16, 16)
        self.right_layout.setSpacing(12)

        # 右侧工具栏
        self.toolbar_layout = QHBoxLayout()
        self.toolbar_layout.setSpacing(12)

        # ===== 搜索框：SearchLineEdit 右侧内嵌 MENU 按钮 =====
        self.search_box = SearchLineEdit(self.right_panel)
        self.search_box.setPlaceholderText("搜索插件")
        self.search_box.setMinimumWidth(280)
        self.search_box.setFixedHeight(34)
        # MENU 按钮
        self.menu_btn = LineEditButton(FIF.MENU, self.search_box)
        self.search_box.hBoxLayout.addWidget(self.menu_btn, 0, Qt.AlignRight)
        self.menu_btn.setToolTip("展开插件列表")
        self.menu_btn.clicked.connect(self._toggle_left_panel)
        self.toolbar_layout.addWidget(self.search_box)

        # 分类过滤器
        self.category_combo = ComboBox(self.right_panel)
        self.category_combo.addItem("全部分类", "all")
        self.category_combo.addItem("诊断工具", "diagnostic")
        self.category_combo.addItem("通信工具", "communication")
        self.category_combo.addItem("串口工具", "serial")
        self.category_combo.addItem("实用工具", "utilities")
        self.category_combo.addItem("自定义", "custom")
        self.category_combo.setFixedWidth(150)
        self.toolbar_layout.addWidget(self.category_combo)

        self.toolbar_layout.addStretch(1)

        # 刷新按钮
        self.refresh_btn = TransparentToolButton(FIF.SYNC, self.right_panel)
        self.refresh_btn.setFixedSize(32, 32)
        self.refresh_btn.setToolTip("刷新插件列表")
        self.toolbar_layout.addWidget(self.refresh_btn)

        # 安装插件按钮
        self.install_btn = PrimaryPushButton(FIF.ADD, "安装插件", self.right_panel)
        self.toolbar_layout.addWidget(self.install_btn)

        self.right_layout.addLayout(self.toolbar_layout)

        # 插件卡片容器
        self.cards_container = QWidget()
        self.cards_flow_layout = FlowLayout(self.cards_container, needAni=True)
        self.cards_flow_layout.setSpacing(16)
        self.cards_flow_layout.setContentsMargins(0, 0, 0, 0)
        self.right_layout.addWidget(self.cards_container)

        # 添加到分割器
        self.splitter.addWidget(self.left_panel)
        self.splitter.addWidget(self.right_panel)
        page_layout.addWidget(self.splitter)

        # 默认收缩左侧面板
        QTimer.singleShot(0, self._apply_collapsed_state)

    def _apply_collapsed_state(self):
        """应用初始状态（左侧面板默认收缩）"""
        self.left_panel.setFixedWidth(0)
        self._left_panel_expanded = False
        self.menu_btn.setToolTip("展开插件列表")

    def _toggle_left_panel(self):
        """切换左侧面板展开/收缩"""
        if self._left_panel_expanded:
            self._collapse_left_panel()
        else:
            self._expand_left_panel()

    def _collapse_left_panel(self):
        """收缩左侧面板"""
        self.left_panel.setFixedWidth(0)
        self._left_panel_expanded = False
        self.menu_btn.setToolTip("展开插件列表")

    def _expand_left_panel(self):
        """展开左侧面板"""
        self.left_panel.setFixedWidth(360)
        self._left_panel_expanded = True
        self.menu_btn.setToolTip("收缩插件列表")

    def _load_plugins(self):
        """加载插件并创建卡片"""
        print("[PluginInterface] 开始加载插件...")
        loaded_count = self.plugin_manager.load_plugins()
        print(f"[PluginInterface] 成功加载 {loaded_count} 个插件")

        # 读取持久化的插件启用状态
        saved_states: dict = cfg.pluginEnabledStates.value or {}

        # 清空现有卡片 - 安全删除
        if self.plugin_cards:
            for card in self.plugin_cards.values():
                try:
                    card.openPluginRequested.disconnect()
                    card.settingsRequested.disconnect()
                    card.uninstallRequested.disconnect()
                except:
                    pass
            self.plugin_cards.clear()
        
        if self.plugin_list_cards:
            for card in self.plugin_list_cards.values():
                try:
                    card.toggled.disconnect()
                except:
                    pass
            self.plugin_list_cards.clear()
        
        if hasattr(self, 'cards_flow_layout'):
            for i in reversed(range(self.cards_flow_layout.count())):
                item = self.cards_flow_layout.itemAt(i)
                if item and item.widget():
                    item.widget().deleteLater()

        if hasattr(self, 'list_layout'):
            for i in reversed(range(self.list_layout.count())):
                item = self.list_layout.itemAt(i)
                if item and item.widget():
                    item.widget().deleteLater()

        # 为每个插件创建左侧列表卡片和右侧插件卡片
        for plugin_name in self.plugin_manager.get_all_loaded_plugins():
            plugin_info = self.plugin_manager.get_plugin_info(plugin_name)
            if plugin_info:
                # 应用持久化的启用状态
                if plugin_name in saved_states:
                    plugin_info.enabled = saved_states[plugin_name]

                print(f"[PluginInterface] 创建卡片: {plugin_name} (状态: {'enabled' if plugin_info.enabled else 'disabled'})")
                
                # 创建左侧列表卡片
                list_card = PluginListCard(plugin_info, self.list_container)
                list_card.setVisible(True)
                self.list_layout.insertWidget(self.list_layout.count() - 1, list_card)
                self.plugin_list_cards[plugin_name] = list_card
                list_card.toggled.connect(self._on_plugin_toggled)
                
                # 只有启用的插件才创建右侧卡片
                if plugin_info.enabled:
                    card = PluginCard(plugin_info, self.cards_container)
                    card.setVisible(True)
                    self.cards_flow_layout.addWidget(card)
                    self.plugin_cards[plugin_name] = card

        self._connect_card_signals()
        self._update_stats()
        print(f"[PluginInterface] 插件加载完成，共 {len(self.plugin_list_cards)} 个插件")

    def _connect_card_signals(self):
        """连接右侧卡片信号"""
        for name, card in self.plugin_cards.items():
            card.openPluginRequested.connect(self._open_plugin_in_tab)
            card.settingsRequested.connect(self._open_plugin_settings)
            card.uninstallRequested.connect(self._uninstall_plugin)

    def __connectSignalToSlot(self):
        """连接信号到槽"""
        # SearchLineEdit 同时监听实时输入和回车搜索
        self.search_box.textChanged.connect(self._on_search_changed)
        self.search_box.searchSignal.connect(self._on_search_changed)
        self.category_combo.currentIndexChanged.connect(self._on_category_changed)
        self.refresh_btn.clicked.connect(self._on_refresh)
        self.install_btn.clicked.connect(self._on_install_plugin)

    def _update_stats(self):
        """更新统计信息"""
        total = len(self.plugin_list_cards)
        enabled = sum(1 for card in self.plugin_list_cards.values() if card.is_enabled())
        if hasattr(self, 'left_stats'):
            self.left_stats.setText(f"共 {total} 个插件，已启用 {enabled} 个")

    def _apply_filter(self):
        """应用搜索 + 分类双重过滤，同时更新左侧列表和右侧卡片"""
        text = self._current_search.lower()
        category = self._current_category

        # 过滤左侧列表卡片
        for name, list_card in self.plugin_list_cards.items():
            name_match = text in name.lower() or text in list_card.plugin_info.name.lower()
            cat_match = category is None or list_card.plugin_info.category == category
            list_card.setVisible(name_match and cat_match)

        # 过滤右侧插件卡片
        for name, card in self.plugin_cards.items():
            name_match = text in name.lower() or text in card.plugin_info.description.lower() or text in card.plugin_info.name.lower()
            cat_match = category is None or card.plugin_info.category == category
            card.setVisible(name_match and cat_match)

    def _on_search_changed(self, text: str):
        """搜索过滤"""
        self._current_search = text
        self._apply_filter()

    def _on_category_changed(self, index: int):
        """分类过滤"""
        category_map = {
            "all": None,
            "diagnostic": PluginCategory.DIAGNOSTIC,
            "communication": PluginCategory.COMMUNICATION,
            "serial": PluginCategory.SERIAL,
            "utilities": PluginCategory.UTILITIES,
            "custom": PluginCategory.CUSTOM
        }
        category_str = self.category_combo.itemData(index)
        self._current_category = category_map.get(category_str)
        self._apply_filter()

    def _on_refresh(self):
        """刷新插件列表"""
        self._load_plugins()

    def _on_install_plugin(self):
        """安装新插件"""
        from PySide6.QtWidgets import QFileDialog, QMessageBox

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择插件包",
            "",
            "插件包 (*.zip);;所有文件 (*.*)"
        )

        if file_path:
            # TODO: 实现插件安装逻辑
            QMessageBox.information(self, "提示", f"已选择插件包: {file_path}\n安装功能开发中...")

    def _open_plugin_settings(self, plugin_name: str):
        """打开插件设置 - 通过详情对话框"""
        print(f"[PluginInterface] 打开插件设置对话框: {plugin_name}")
        
        # 创建详情对话框
        dialog = PluginDetailDialog(plugin_name, self.plugin_manager, self.window())
        
        # 连接信号
        dialog.openPluginRequested.connect(self._open_plugin_in_tab)
        dialog.pluginUninstalled.connect(self._on_plugin_uninstalled)
        
        # 显示对话框
        dialog.exec()

    def _open_plugin_in_tab(self, plugin_name: str):
        """在新Tab中打开插件"""
        print(f"[PluginInterface] 在新Tab中打开插件: {plugin_name}")
        
        # 检查是否已经打开
        if plugin_name in self.plugin_tabs:
            tab_page = self.plugin_tabs[plugin_name]
            # 检查Tab页是否仍然有效
            try:
                _ = tab_page.objectName()
                print(f"[PluginInterface] 插件Tab已存在且有效，切换到该Tab: {plugin_name}")
                # 切换到已存在的Tab
                self.tab_bar.setCurrentTab(plugin_name)
                self.tab_stack.setCurrentWidget(tab_page)
                return
            except RuntimeError:
                # Tab页已被删除，从缓存中移除
                print(f"[PluginInterface] 插件Tab已被删除，重新创建: {plugin_name}")
                del self.plugin_tabs[plugin_name]

        # 获取插件实例
        print(f"[PluginInterface] 获取插件实例...")
        plugin_instance = self.plugin_manager.get_plugin(plugin_name)
        if not plugin_instance:
            print(f"[PluginInterface] 错误：无法获取插件实例: {plugin_name}")
            return
        
        print(f"[PluginInterface] 插件实例: {plugin_instance}")

        # 获取插件的主界面
        print(f"[PluginInterface] 获取插件主界面...")
        try:
            plugin_widget = plugin_instance.get_main_widget()
            if not plugin_widget:
                print(f"[PluginInterface] 错误：插件没有主界面: {plugin_name}")
                return
            
            # 检查widget是否有效
            try:
                _ = plugin_widget.objectName()
                print(f"[PluginInterface] 插件主界面有效")
            except RuntimeError:
                print(f"[PluginInterface] 错误：插件主界面已被删除: {plugin_name}")
                return
        except RuntimeError as e:
            print(f"[PluginInterface] 错误：获取插件主界面失败: {e}")
            return

        # 创建Tab页容器
        tab_page = QWidget()
        tab_layout = QVBoxLayout(tab_page)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(plugin_widget)

        # 添加到Tab栈
        self.tab_stack.addWidget(tab_page)
        self.plugin_tabs[plugin_name] = tab_page

        # 添加Tab标签
        plugin_info = self.plugin_manager.get_plugin_info(plugin_name)
        tab_text = plugin_info.name if plugin_info else plugin_name
        print(f"[PluginInterface] 添加Tab标签: {tab_text}")
        
        self.tab_bar.addTab(
            routeKey=plugin_name,
            text=tab_text,
            icon=FIF.APPLICATION,
            onClick=lambda: self.tab_stack.setCurrentWidget(tab_page)
        )

        # 切换到新Tab
        self.tab_bar.setCurrentTab(plugin_name)
        self.tab_stack.setCurrentWidget(tab_page)

        print(f"[PluginInterface] 插件Tab已打开: {plugin_name}")

    def _on_tab_close_requested(self, index: int):
        """Tab关闭请求"""
        item = self.tab_bar.tabItem(index)
        route_key = item.routeKey()
        
        print(f"[PluginInterface] 请求关闭Tab: {route_key} (index: {index})")

        # 不允许关闭插件管理Tab
        if route_key == "plugin_manager":
            print(f"[PluginInterface] 不允许关闭插件管理Tab")
            return

        # 移除Tab（但不删除widget，让插件自己管理）
        if route_key in self.plugin_tabs:
            tab_page = self.plugin_tabs.pop(route_key)
            # 只从stack中移除，不删除widget
            self.tab_stack.removeWidget(tab_page)
            # 注意：不调用deleteLater()，避免删除widget
            print(f"[PluginInterface] Tab页已移除（widget保留）: {route_key}")

        self.tab_bar.removeTab(index)
        print(f"[PluginInterface] Tab已关闭: {route_key}")

    def _on_plugin_toggled(self, plugin_name: str, enabled: bool):
        """插件启用状态切换"""
        print(f"[PluginInterface] 插件 {plugin_name} 状态切换为: {'\u542f\u7528' if enabled else '\u7981\u7528'}")
            
        # 持久化保存到 cfg
        saved_states: dict = dict(cfg.pluginEnabledStates.value or {})
        saved_states[plugin_name] = enabled
        cfg.set(cfg.pluginEnabledStates, saved_states)
    
        if enabled:
            # 启用插件：创建右侧卡片
            if plugin_name not in self.plugin_cards:
                plugin_info = self.plugin_manager.get_plugin_info(plugin_name)
                if plugin_info:
                    card = PluginCard(plugin_info, self.cards_container)
                    card.setVisible(True)
                    self.cards_flow_layout.addWidget(card)
                    self.plugin_cards[plugin_name] = card
                    card.openPluginRequested.connect(self._open_plugin_in_tab)
                    card.settingsRequested.connect(self._open_plugin_settings)
                    card.uninstallRequested.connect(self._uninstall_plugin)
        else:
            # 禁用插件：移除右侧卡片
            if plugin_name in self.plugin_cards:
                self.plugin_cards[plugin_name].deleteLater()
                del self.plugin_cards[plugin_name]
            
        # 重新应用过滤
        self._apply_filter()
        self._update_stats()
    

    def _uninstall_plugin(self, plugin_name: str):
        """卸载插件"""
        from PySide6.QtWidgets import QMessageBox

        print(f"[PluginInterface] 请求卸载插件: {plugin_name}")

        reply = QMessageBox.question(
            self,
            "确认卸载",
            f"确定要卸载插件 '{plugin_name}' 吗？\n此操作不可撤销。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            print(f"[PluginInterface] 确认卸载: {plugin_name}")
            # 从管理器中注销
            self.plugin_manager.registry.unregister_plugin(plugin_name)
            
            # 移除右侧卡片
            if plugin_name in self.plugin_cards:
                self.plugin_cards[plugin_name].deleteLater()
                del self.plugin_cards[plugin_name]
            
            # 移除左侧列表卡片
            if plugin_name in self.plugin_list_cards:
                self.plugin_list_cards[plugin_name].deleteLater()
                del self.plugin_list_cards[plugin_name]
            
            self._update_stats()
            print(f"[PluginInterface] 插件已卸载: {plugin_name}")
        else:
            print(f"[PluginInterface] 取消卸载: {plugin_name}")

    def _on_plugin_uninstalled(self, plugin_name: str):
        """插件卸载完成"""
        print(f"[PluginInterface] 插件卸载完成回调: {plugin_name}")
        
        # 移除右侧卡片
        if plugin_name in self.plugin_cards:
            self.plugin_cards[plugin_name].deleteLater()
            del self.plugin_cards[plugin_name]
        
        # 移除左侧列表卡片
        if plugin_name in self.plugin_list_cards:
            self.plugin_list_cards[plugin_name].deleteLater()
            del self.plugin_list_cards[plugin_name]
                
        # 关闭对应的Tab（如果已打开）
        if plugin_name in self.plugin_tabs:
            tab_page = self.plugin_tabs.pop(plugin_name)
            self.tab_stack.removeWidget(tab_page)
            # 注意：不删除widget，让插件自己管理
            # tab_page.deleteLater()
                
        self._update_stats()

