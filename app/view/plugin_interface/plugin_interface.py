"""
插件管理界面 - 插件化工具Hub
集成插件管理、卡片展示、详情页、面包屑导航等完整功能
"""

from typing import Dict, List
from PySide6.QtCore import Qt, Signal, QTimer, QSize, QMimeData, QEasingCurve
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QHBoxLayout,
    QScroller,
    QScrollerProperties,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
    QSplitter,
    QListWidget,
    QListWidgetItem,
    QAbstractItemView,
)
from qfluentwidgets import FluentIcon as FIF, LineEditButton
from qfluentwidgets import (
    ScrollArea,
    FlowLayout,
    ComboBox,
    SearchLineEdit,
    CaptionLabel,
    ToolButton,
    TabBar,
    TabCloseButtonDisplayMode,
    StrongBodyLabel,
    SmoothScrollArea,
    ToolTipFilter,
    toggleTheme,
)

from app.common.config import cfg
from app.common.style_sheet import StyleSheet
from app.common.signal_bus import signalBus
from qfluentwidgets import qconfig

# 导入插件系统
from app.plugins import PluginManager, PluginCategory
from .plugin_card import PluginCard
from .plugin_list_card import PluginListCard
from .plugin_detail_dialog import PluginDetailDialog
from app.components.common_widgets import BetterScrollArea


class _DraggableListWidget(QListWidget):
    """支持拖拽排序的插件列表，顺序变化后发射 orderChanged 信号"""

    orderChanged = Signal(list)  # 新的插件名称列表（按显示顺序）

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setSpacing(4)
        self.setFrameShape(QListWidget.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setStyleSheet("""
            QListWidget {
                background: transparent;
                border: none;
                outline: none;
            }
            QListWidget::item {
                background: transparent;
                border: none;
                padding: 0px;
            }
            QListWidget::item:selected {
                background: transparent;
            }
        """)

    def dropEvent(self, event):
        super().dropEvent(event)
        order = [self.item(i).data(Qt.UserRole) for i in range(self.count())]
        self.orderChanged.emit(order)


class PluginInterface(ScrollArea):
    """插件管理界面 - 完整的插件管理平台"""

    pluginOpened = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.view = QWidget(self)

        self.plugin_manager = PluginManager()
        self.plugin_cards: Dict[str, PluginCard] = {}
        self.plugin_list_cards: Dict[str, PluginListCard] = {}
        self._current_category = None
        self._current_search = ""

        self.plugin_tabs = {}
        self.tab_count = 0

        self._left_panel_expanded = False

        self.__initWidget()
        self.__initLayout()
        self._load_plugins()
        self.__connectSignalToSlot()

        # 监听主题变化，刷新所有卡片样式
        qconfig.themeChanged.connect(self._on_theme_changed)

    def __initWidget(self):
        self.setObjectName("pluginInterface")
        self.view.setObjectName("view")
        self.setViewportMargins(0, 48, 0, 0)
        self.setWidget(self.view)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.__setupSmoothScroll()
        StyleSheet.PLUGIN_INTERFACE.apply(self)

    def __setupSmoothScroll(self):
        QScroller.grabGesture(
            self.viewport(),
            QScroller.ScrollerGestureType.LeftMouseButtonGesture,
        )
        scroller = QScroller.scroller(self.viewport())
        props = scroller.scrollerProperties()
        props.setScrollMetric(QScrollerProperties.ScrollMetric.OvershootDragDistanceFactor, 0.05)
        props.setScrollMetric(QScrollerProperties.ScrollMetric.OvershootScrollDistanceFactor, 0.05)
        props.setScrollMetric(QScrollerProperties.ScrollMetric.DecelerationFactor, 0.5)
        scroller.setScrollerProperties(props)

    def __initLayout(self):
        self.Layout = QHBoxLayout(self.view)
        self.Layout.setContentsMargins(0, 0, 0, 0)

        self.main_layout = QVBoxLayout()
        self.main_layout.setObjectName("mainLayout")
        self.main_layout.setContentsMargins(12, 10, 36, 36)
        self.main_layout.setSpacing(16)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.Layout.addLayout(self.main_layout)

        self.tab_bar = TabBar(self)
        self.tab_bar.setCloseButtonDisplayMode(TabCloseButtonDisplayMode.ON_HOVER)
        self.tab_bar.tabCloseRequested.connect(self._on_tab_close_requested)
        self.main_layout.addWidget(self.tab_bar)

        self.tab_stack = QStackedWidget()
        self.main_layout.addWidget(self.tab_stack)

        self.plugin_manager_page = QWidget()
        self.plugin_manager_page.setObjectName("plugin_manager_page")
        self._setup_plugin_manager_page()
        self.tab_stack.addWidget(self.plugin_manager_page)

        self.tab_bar.addTab(
            routeKey="plugin_manager",
            text="插件管理",
            icon=FIF.HOME,
            onClick=lambda: self.tab_stack.setCurrentWidget(self.plugin_manager_page)
        )

    def _setup_plugin_manager_page(self):
        page_layout = QHBoxLayout(self.plugin_manager_page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(0)

        self.splitter = QSplitter(Qt.Orientation.Horizontal, self.plugin_manager_page)
        self.splitter.setHandleWidth(0)
        self.splitter.setChildrenCollapsible(False)

        # ========== 左侧面板 ==========
        self.left_panel = SmoothScrollArea()
        self.left_panel.setObjectName("left_panel")
        self.left_panel.setMinimumWidth(280)
        self.left_panel.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.left_panel.setWidgetResizable(True)

        self.left_container = QWidget()
        self.left_container.setObjectName("left_panel_container")
        self.left_layout = QVBoxLayout(self.left_container)
        self.left_layout.setContentsMargins(12, 12, 12, 12)
        self.left_layout.setSpacing(8)
        self.left_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.left_title = StrongBodyLabel("插件列表", self.left_container)
        self.left_title.setObjectName("left_title")
        self.left_title.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.left_layout.addWidget(self.left_title)

        self.left_stats = CaptionLabel("共 0 个插件", self.left_container)
        self.left_stats.setObjectName("left_stats")
        self.left_layout.addWidget(self.left_stats)

        # 左侧 menubar（刷新、安装、全部隐藏/显示）
        self.category_combo = ComboBox(self.left_container)
        self._refresh_category_combo()  # 动态生成分类选项
        self.category_combo.setFixedWidth(150)

        self.left_menubar = QWidget(self.left_container)
        self.left_menubar_layout = QHBoxLayout(self.left_menubar)
        self.left_menubar_layout.setContentsMargins(5, 4, 0, 4)
        self.left_menubar_layout.setSpacing(8)

        self.left_refresh_btn = ToolButton(FIF.SYNC, self.left_menubar)
        self.left_refresh_btn.setFixedSize(32, 32)
        self.left_refresh_btn.setToolTip(self.tr("刷新插件列表"))
        self.left_refresh_btn.installEventFilter(ToolTipFilter(self.left_refresh_btn))

        self.left_install_btn = ToolButton(FIF.ADD, self.left_menubar)
        self.left_install_btn.setFixedSize(32, 32)
        self.left_install_btn.setToolTip(self.tr("安装插件"))
        self.left_install_btn.installEventFilter(ToolTipFilter(self.left_install_btn))

        # 全部显示/隐藏 toggle 按钮
        self.left_toggle_all_btn = ToolButton(FIF.HIDE, self.left_menubar)
        self.left_toggle_all_btn.setFixedSize(32, 32)
        self.left_toggle_all_btn.setToolTip(self.tr("全部隐藏"))
        self.left_toggle_all_btn.installEventFilter(ToolTipFilter(self.left_toggle_all_btn))
        self._all_plugins_visible = True  # 记录当前状态

        self.left_menubar_layout.addWidget(self.category_combo)
        self.left_menubar_layout.addStretch(1)
        self.left_menubar_layout.addWidget(self.left_refresh_btn)
        self.left_menubar_layout.addWidget(self.left_install_btn)
        self.left_menubar_layout.addWidget(self.left_toggle_all_btn)
        self.left_layout.addWidget(self.left_menubar)

        # 可拖拽排序的列表
        self.list_widget = _DraggableListWidget(self.left_container)
        self.list_widget.setSpacing(4)  # 增大卡片间距
        self.left_layout.addWidget(self.list_widget)

        self.left_panel.setWidget(self.left_container)

        # ========== 右侧面板 ==========
        self.right_panel = SmoothScrollArea()
        self.right_panel.setObjectName("right_panel")
        self.right_panel.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.right_panel.setWidgetResizable(True)

        self.right_container = QWidget()
        self.right_container.setObjectName("right_panel_container")
        self.right_layout = QVBoxLayout(self.right_container)
        self.right_layout.setContentsMargins(12, 12, 12, 12)
        self.right_layout.setSpacing(8)
        self.right_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # 工具栏
        self.toolbar_layout = QHBoxLayout()
        self.toolbar_layout.setSpacing(12)

        self.search_box = SearchLineEdit(self.right_container)
        self.search_box.setPlaceholderText("搜索插件  (Ctrl+F)")
        # self.search_box.setMinimumWidth(280)
        self.search_box.setFixedHeight(34)
        self.menu_btn = LineEditButton(FIF.MENU, self.search_box)
        self.search_box.hBoxLayout.addWidget(self.menu_btn, 0, Qt.AlignRight)
        self.menu_btn.setToolTip("展开插件列表")
        self.menu_btn.clicked.connect(self._toggle_left_panel)
        self.toolbar_layout.addWidget(self.search_box)
        self.toolbar_layout.addStretch(1)
        self.right_layout.addLayout(self.toolbar_layout)

        self.cards_scroll = BetterScrollArea(self.right_container)
        self.cards_scroll.setObjectName("cards_scroll")
        self.cards_scroll.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.cards_scroll.vBoxLayout.setSpacing(0)
        
        self.cards_container = QWidget(self.cards_scroll.view)
        self.cards_flow_layout = FlowLayout(self.cards_container, needAni=True)
        self.cards_flow_layout.setSpacing(16)
        self.cards_flow_layout.setContentsMargins(0, 0, 20, 20)
        
        self.cards_scroll.vBoxLayout.addWidget(self.cards_container)
        self.right_layout.addWidget(self.cards_scroll)

        self.right_panel.setWidget(self.right_container)

        self.splitter.addWidget(self.left_panel)
        self.splitter.addWidget(self.right_panel)
        page_layout.addWidget(self.splitter)

        QTimer.singleShot(0, self._apply_collapsed_state)

    # ------------------------------------------------------------------
    # 面板展开/收缩
    # ------------------------------------------------------------------
    def _apply_collapsed_state(self):
        self.left_panel.setFixedWidth(0)
        self._left_panel_expanded = False
        self.menu_btn.setToolTip("展开插件列表")

    def _toggle_left_panel(self):
        if self._left_panel_expanded:
            self._collapse_left_panel()
        else:
            self._expand_left_panel()

    def _collapse_left_panel(self):
        self.left_panel.setFixedWidth(0)
        self._left_panel_expanded = False
        self.menu_btn.setToolTip("展开插件列表")

    def _expand_left_panel(self):
        self.left_panel.setFixedWidth(400)
        self._left_panel_expanded = True
        self.menu_btn.setToolTip("收缩插件列表")

    # ------------------------------------------------------------------
    # 加载插件
    # ------------------------------------------------------------------
    def _load_plugins(self):
        loaded_count = self.plugin_manager.load_plugins()

        saved_states: dict = cfg.pluginEnabledStates.value or {}
        saved_order: list  = cfg.pluginOrder.value or []

        # 清空旧卡片
        for card in self.plugin_cards.values():
            try:
                card.openPluginRequested.disconnect()
                card.settingsRequested.disconnect()
                card.uninstallRequested.disconnect()
                card.docsRequested.disconnect()
                card.releaseNotesRequested.disconnect()
            except Exception:
                pass
        self.plugin_cards.clear()

        for card in self.plugin_list_cards.values():
            try:
                card.toggled.disconnect()
                card.uninstallRequested.disconnect()
            except Exception:
                pass
        self.plugin_list_cards.clear()

        if hasattr(self, 'cards_flow_layout'):
            for i in reversed(range(self.cards_flow_layout.count())):
                item = self.cards_flow_layout.itemAt(i)
                if item and item.widget():
                    item.widget().deleteLater()

        self.list_widget.clear()

        # 确定插件显示顺序（保持 saved_order，新插件追加末尾）
        all_plugins = self.plugin_manager.get_all_loaded_plugins()
        ordered = [n for n in saved_order if n in all_plugins]
        ordered += [n for n in all_plugins if n not in ordered]

        for plugin_name in ordered:
            plugin_info = self.plugin_manager.get_plugin_info(plugin_name)
            if not plugin_info:
                continue

            # 应用持久化启用状态
            if plugin_name in saved_states:
                plugin_info.enabled = saved_states[plugin_name]

            # 创建 PluginListCard 并嵌入 QListWidget item
            list_card = PluginListCard(plugin_info, self.list_widget)
            self.plugin_list_cards[plugin_name] = list_card

            item = QListWidgetItem(self.list_widget)
            item.setSizeHint(list_card.sizeHint())
            item.setData(Qt.UserRole, plugin_name)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsDragEnabled)
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, list_card)

            list_card.toggled.connect(self._on_plugin_toggled)

            # 只有启用的插件才创建右侧卡片
            if plugin_info.enabled:
                card = PluginCard(plugin_info, self.cards_container)
                self.cards_flow_layout.addWidget(card)
                self.plugin_cards[plugin_name] = card

        self._connect_card_signals()
        self._update_stats()
        self._refresh_category_combo()  # 加载完插件后刷新分类选项

    def _connect_card_signals(self):
        for name, card in self.plugin_cards.items():
            card.openPluginRequested.connect(self._open_plugin_in_tab)
            card.settingsRequested.connect(self._open_plugin_settings)
            card.uninstallRequested.connect(self._uninstall_plugin)
            card.docsRequested.connect(self._open_plugin_docs)
            card.releaseNotesRequested.connect(self._open_plugin_release_notes)

    def __connectSignalToSlot(self):
        self.search_box.textChanged.connect(self._on_search_changed)
        self.search_box.searchSignal.connect(self._on_search_changed)
        self.category_combo.currentIndexChanged.connect(self._on_category_changed)

        # 左侧 menubar 按钮信号
        self.left_refresh_btn.clicked.connect(self._on_refresh)
        self.left_install_btn.clicked.connect(self._on_install_plugin)
        self.left_toggle_all_btn.clicked.connect(self._on_toggle_all_plugins)

        # 拖拽排序持久化
        self.list_widget.orderChanged.connect(self._on_order_changed)

        # Ctrl+F 聚焦搜索框
        shortcut_focus = QShortcut(QKeySequence("Ctrl+F"), self)
        shortcut_focus.activated.connect(self._focus_search)

        # Esc 清除搜索框并失焦
        shortcut_esc = QShortcut(QKeySequence("Escape"), self.search_box)
        shortcut_esc.activated.connect(self._clear_search)

    def _focus_search(self):
        self.search_box.setFocus()
        self.search_box.selectAll()

    def _clear_search(self):
        self.search_box.clear()
        self.search_box.clearFocus()

    # ------------------------------------------------------------------
    # 顺序持久化
    # ------------------------------------------------------------------
    def _on_theme_changed(self):
        """主题切换时刷新所有卡片样式"""
        # 重新应用 QSS 样式
        StyleSheet.PLUGIN_INTERFACE.apply(self)
        
        # 刷新右侧 PluginCard（自绘样式需要手动更新）
        for card in self.plugin_cards.values():
            card.refresh_style()
        # 刷新左侧 PluginListCard
        for card in self.plugin_list_cards.values():
            card.refresh_style()

    def _on_order_changed(self, order: List[str]):
        """顺序变化时持久化"""
        cfg.set(cfg.pluginOrder, order)

    # ------------------------------------------------------------------
    # 过滤
    # ------------------------------------------------------------------
    def _update_stats(self):
        total   = len(self.plugin_list_cards)
        enabled = sum(1 for c in self.plugin_list_cards.values() if c.is_enabled())
        if hasattr(self, 'left_stats'):
            self.left_stats.setText(f"共 {total} 个插件，已显示 {enabled} 个")

    def _apply_filter(self):
        text     = self._current_search.lower()
        category = self._current_category

        # 左侧列表 item 显示/隐藏
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            name = item.data(Qt.UserRole)
            list_card = self.plugin_list_cards.get(name)
            if list_card:
                nm = name.lower()
                pn = list_card.plugin_info.name.lower()
                name_match = (not text) or text in nm or text in pn
                cat_match  = category is None or list_card.plugin_info.category == category
                item.setHidden(not (name_match and cat_match))

        # 右侧卡片
        for name, card in self.plugin_cards.items():
            name_match = (not text) or text in name.lower() or text in card.plugin_info.name.lower() or text in card.plugin_info.description.lower()
            cat_match  = category is None or card.plugin_info.category == category
            card.setVisible(name_match and cat_match)

    def _on_search_changed(self, text: str):
        self._current_search = text
        self._apply_filter()

    def _refresh_category_combo(self):
        """动态刷新分类下拉框 - 根据实际加载的插件分类生成"""
        self.category_combo.clear()
        self.category_combo.addItem("全部分类", "all")
        
        # 收集所有实际使用的分类
        categories = set()
        for plugin_name in self.plugin_manager.get_all_loaded_plugins():
            plugin_info = self.plugin_manager.get_plugin_info(plugin_name)
            if plugin_info:
                categories.add(plugin_info.category)
        
        # 按定义的顺序添加分类（使用字符串值作为data）
        category_order = [
            (PluginCategory.DIAGNOSTIC, "diagnostic", "诊断工具"),
            (PluginCategory.COMMUNICATION, "communication", "通信工具"),
            (PluginCategory.SERIAL, "serial", "串口工具"),
            (PluginCategory.UTILITIES, "utilities", "实用工具"),
            (PluginCategory.CUSTOM, "custom", "自定义"),
        ]
        
        for cat, value, name in category_order:
            if cat in categories:
                self.category_combo.addItem(name, value)

    def _on_category_changed(self, index: int):
        """分类改变时更新筛选"""
        category_map = {
            "all": None,
            "diagnostic": PluginCategory.DIAGNOSTIC,
            "communication": PluginCategory.COMMUNICATION,
            "serial": PluginCategory.SERIAL,
            "utilities": PluginCategory.UTILITIES,
            "custom": PluginCategory.CUSTOM,
        }
        data = self.category_combo.itemData(index)
        self._current_category = category_map.get(data)
        self._apply_filter()

    def _on_refresh(self):
        self._load_plugins()

    def _on_install_plugin(self):
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择插件包", "", "插件包 (*.zip);;所有文件 (*.*)"
        )
        if file_path:
            QMessageBox.information(self, "提示", f"已选择插件包: {file_path}\n安装功能开发中...")

    def _on_toggle_all_plugins(self):
        """切换全部插件的显示/隐藏状态"""
        if self._all_plugins_visible:
            # 全部隐藏
            for name, list_card in self.plugin_list_cards.items():
                if list_card.is_enabled():
                    list_card.set_enabled_state(False)
                    self._on_plugin_toggled(name, False)
            self._all_plugins_visible = False
            self.left_toggle_all_btn.setIcon(FIF.VIEW)
            self.left_toggle_all_btn.setToolTip(self.tr("全部显示"))
        else:
            # 全部显示
            for name, list_card in self.plugin_list_cards.items():
                if not list_card.is_enabled():
                    list_card.set_enabled_state(True)
                    self._on_plugin_toggled(name, True)
            self._all_plugins_visible = True
            self.left_toggle_all_btn.setIcon(FIF.HIDE)
            self.left_toggle_all_btn.setToolTip(self.tr("全部隐藏"))

    # ------------------------------------------------------------------
    # 插件操作
    # ------------------------------------------------------------------
    def _open_plugin_settings(self, plugin_name: str):
        dialog = PluginDetailDialog(plugin_name, self.plugin_manager, self.window())
        dialog.openPluginRequested.connect(self._open_plugin_in_tab)
        dialog.pluginUninstalled.connect(self._on_plugin_uninstalled)
        dialog.exec()

    def _open_plugin_docs(self, plugin_name: str):
        """打开插件文档"""
        import webbrowser
        plugin_instance = self.plugin_manager.get_plugin(plugin_name)
        if not plugin_instance:
            return
        doc_url = plugin_instance.get_doc_url()
        if doc_url:
            webbrowser.open(doc_url)
        else:
            from qfluentwidgets import InfoBar, InfoBarPosition
            InfoBar.info(
                title="暂无文档",
                content=f"插件 {plugin_name} 尚未提供文档链接",
                parent=self,
                position=InfoBarPosition.TOP_RIGHT,
            )

    def _open_plugin_release_notes(self, plugin_name: str):
        """打开 Release Notes"""
        import webbrowser
        plugin_instance = self.plugin_manager.get_plugin(plugin_name)
        if not plugin_instance:
            return
        url = plugin_instance.get_release_notes_url()
        if url:
            webbrowser.open(url)
            return
        notes = plugin_instance.get_release_notes()
        if notes:
            self._show_release_notes_dialog(plugin_name, notes)
        else:
            from qfluentwidgets import InfoBar, InfoBarPosition
            InfoBar.info(
                title="暂无 Release Notes",
                content=f"插件 {plugin_name} 尚未提供更新日志",
                parent=self,
                position=InfoBarPosition.TOP_RIGHT,
            )

    def _show_release_notes_dialog(self, plugin_name: str, notes: str):
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QDialogButtonBox
        dlg = QDialog(self.window())
        dlg.setWindowTitle(f"{plugin_name} - Release Notes")
        dlg.resize(600, 400)
        lay = QVBoxLayout(dlg)
        te = QTextEdit(dlg)
        te.setReadOnly(True)
        te.setPlainText(notes)
        lay.addWidget(te)
        btn = QDialogButtonBox(QDialogButtonBox.Ok, dlg)
        btn.accepted.connect(dlg.accept)
        lay.addWidget(btn)
        dlg.exec()

    def _open_plugin_in_tab(self, plugin_name: str):
        if plugin_name in self.plugin_tabs:
            tab_page = self.plugin_tabs[plugin_name]
            try:
                _ = tab_page.objectName()
                self.tab_bar.setCurrentTab(plugin_name)
                self.tab_stack.setCurrentWidget(tab_page)
                return
            except RuntimeError:
                del self.plugin_tabs[plugin_name]

        plugin_instance = self.plugin_manager.get_plugin(plugin_name)
        if not plugin_instance:
            return

        try:
            plugin_widget = plugin_instance.get_main_widget()
            if not plugin_widget:
                return
            _ = plugin_widget.objectName()
        except RuntimeError:
            return

        tab_page = QWidget()
        tab_layout = QVBoxLayout(tab_page)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.setSpacing(0)
        tab_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        tab_layout.addWidget(plugin_widget)
        tab_layout.addStretch(1)

        self.tab_stack.addWidget(tab_page)
        self.plugin_tabs[plugin_name] = tab_page

        plugin_info = self.plugin_manager.get_plugin_info(plugin_name)
        tab_text = plugin_info.name if plugin_info else plugin_name
        self.tab_bar.addTab(
            routeKey=plugin_name,
            text=tab_text,
            icon=FIF.APPLICATION,
            onClick=lambda: self.tab_stack.setCurrentWidget(tab_page)
        )
        self.tab_bar.setCurrentTab(plugin_name)
        self.tab_stack.setCurrentWidget(tab_page)

    def _on_tab_close_requested(self, index: int):
        item = self.tab_bar.tabItem(index)
        route_key = item.routeKey()
        if route_key == "plugin_manager":
            return
        if route_key in self.plugin_tabs:
            tab_page = self.plugin_tabs.pop(route_key)
            self.tab_stack.removeWidget(tab_page)
        self.tab_bar.removeTab(index)

    def _on_plugin_toggled(self, plugin_name: str, enabled: bool):
        # 持久化启用状态
        saved_states: dict = dict(cfg.pluginEnabledStates.value or {})
        saved_states[plugin_name] = enabled
        cfg.set(cfg.pluginEnabledStates, saved_states)

        if enabled:
            if plugin_name not in self.plugin_cards:
                plugin_info = self.plugin_manager.get_plugin_info(plugin_name)
                if plugin_info:
                    card = PluginCard(plugin_info, self.cards_container)
                    self.cards_flow_layout.addWidget(card)
                    self.plugin_cards[plugin_name] = card
                    card.openPluginRequested.connect(self._open_plugin_in_tab)
                    card.settingsRequested.connect(self._open_plugin_settings)
                    card.uninstallRequested.connect(self._uninstall_plugin)
                    card.docsRequested.connect(self._open_plugin_docs)
                    card.releaseNotesRequested.connect(self._open_plugin_release_notes)
        else:
            if plugin_name in self.plugin_cards:
                self.plugin_cards[plugin_name].deleteLater()
                del self.plugin_cards[plugin_name]

        self._apply_filter()
        self._update_stats()

    def _uninstall_plugin(self, plugin_name: str):
        from PySide6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self,
            "确认卸载",
            f"确定要卸载插件 '{plugin_name}' 吗？\n此操作不可撤销。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.plugin_manager.registry.unregister_plugin(plugin_name)
            if plugin_name in self.plugin_cards:
                self.plugin_cards[plugin_name].deleteLater()
                del self.plugin_cards[plugin_name]
            # 移除左侧列表 item
            for i in range(self.list_widget.count()):
                item = self.list_widget.item(i)
                if item and item.data(Qt.UserRole) == plugin_name:
                    self.list_widget.takeItem(i)
                    break
            if plugin_name in self.plugin_list_cards:
                del self.plugin_list_cards[plugin_name]
            self._update_stats()

    def _on_plugin_uninstalled(self, plugin_name: str):
        if plugin_name in self.plugin_cards:
            self.plugin_cards[plugin_name].deleteLater()
            del self.plugin_cards[plugin_name]
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item and item.data(Qt.UserRole) == plugin_name:
                self.list_widget.takeItem(i)
                break
        if plugin_name in self.plugin_list_cards:
            del self.plugin_list_cards[plugin_name]
        if plugin_name in self.plugin_tabs:
            tab_page = self.plugin_tabs.pop(plugin_name)
            self.tab_stack.removeWidget(tab_page)
        self._update_stats()
