from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import ScrollArea, SubtitleLabel, TabWidget, setFont

from app.common.style_sheet import StyleSheet
from app.model.fault_model import FaultManager
from app.tools.ui.FastFaultManager_template_ui import TemplateManagerUI
from app.tools.ui.FastFaultManager_project_ui import ProjectManagerUI
from app.tools.ui.FastFaultManager_item_ui import ItemManagerUI
from app.tools.ui.FastFaultManager_import_export import ImportExportUI


class TabContent(QWidget):
    """标签页内容部件"""

    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.label = SubtitleLabel(text, self)
        self.label.setAlignment(Qt.AlignCenter)

        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.addWidget(self.label, 1, Qt.AlignCenter)
        setFont(self.label, 24)
        self.setObjectName(text.replace(" ", "-"))


class AppInterface(ScrollArea):
    """应用界面，包含标签页功能"""

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.view = QWidget(self)
        self.tabWidget = TabWidget(self)

        self.__initWidget()
        self.__setQss()
        self.__initLayout()
        self.__initTabs()

    def __initWidget(self):
        """初始化小部件"""
        self.setObjectName("appInterface")
        self.view.setObjectName("view")

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWidget(self.view)
        self.setWidgetResizable(True)

        # 设置标签页属性  注意：tabAddRequested信号默认是可用的，不需要额外设置
        self.tabWidget.setMovable(True)  # 允许标签页拖动
        self.tabWidget.setTabsClosable(True)  # 允许关闭标签页

    def __setQss(self):
        """set style sheet"""
        # initialize style sheet
        StyleSheet.APP_INTERFACE.apply(self)

    def __initLayout(self):
        """初始化布局"""
        self.Layout = QHBoxLayout(self.view)
        self.Layout.setContentsMargins(0, 48, 0, 0)

        self.main_layout = QVBoxLayout()
        self.main_layout.setObjectName("vBoxLayout")
        self.main_layout.setContentsMargins(10, 0, 10, 10)
        self.main_layout.setSpacing(20)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.Layout.addLayout(self.main_layout)
        self.main_layout.addWidget(self.tabWidget)

    def __initTabs(self):
        """初始化标签页"""
        # 添加默认主页标签页
        # self.addHomeTab()
        self.addFaultManagerTab()

        # 连接信号和槽
        self.tabWidget.tabAddRequested.connect(self.addNewTab)
        self.tabWidget.tabCloseRequested.connect(self.tabWidget.removeTab)

    def addHomeTab(self):
        """添加默认主页标签页"""
        print("[AppInterface] 添加默认主页标签页")
        homeContent = TabContent("默认主页", self)
        self.tabWidget.addTab(homeContent, "默认主页", icon=FIF.HOME)
        print("[AppInterface] 默认主页标签页添加成功")

    def addNewTab(self):
        """添加新标签页"""
        print("[AppInterface] 添加新标签页")
        tabCount = self.tabWidget.count()
        if tabCount == 0:
            print("[AppInterface] 标签页为空，添加默认主页")
            self.addHomeTab()
            return
        text = f"新标签页 {tabCount}"
        print(f"[AppInterface] 创建新标签页: {text}")
        content = TabContent(text, self)

        self.tabWidget.addTab(content, text, icon=FIF.BRIGHTNESS)
        print("[AppInterface] 新标签页添加成功")
    
    def addFaultManagerTab(self):
        """添加故障管理系统标签页"""
        print("[AppInterface] 添加故障管理系统标签页")
        # 创建故障管理系统的主界面
        faultManagerContent = QWidget(self)
        faultManagerLayout = QVBoxLayout(faultManagerContent)
        
        # 初始化故障管理器（使用JSON存储）
        fault_manager = FaultManager()
        
        # 标签页
        tabWidget = TabWidget(faultManagerContent)
        
        # 项目管理标签
        print("[AppInterface] 创建项目管理界面")
        projectManager = ProjectManagerUI(fault_manager, tabWidget)
        tabWidget.addTab(projectManager, self.tr("项目管理"), FIF.FOLDER)
        
        # 条目管理标签
        print("[AppInterface] 创建条目管理界面")
        itemManager = ItemManagerUI(fault_manager, tabWidget)
        tabWidget.addTab(itemManager, self.tr("条目管理"), FIF.DOCUMENT)
        
        # 导入导出标签
        print("[AppInterface] 创建导入导出界面")
        importExport = ImportExportUI(fault_manager, tabWidget)
        tabWidget.addTab(importExport, self.tr("导入导出"), FIF.SHARE)
        
        faultManagerLayout.addWidget(tabWidget)
        
        # 连接信号
        tabWidget.currentChanged.connect(lambda index: self._on_fault_manager_tab_changed(index, itemManager, importExport))
        
        self.tabWidget.addTab(faultManagerContent, "故障管理系统", icon=FIF.DOCUMENT)
        print("[AppInterface] 故障管理系统标签页添加成功")
    
    def _on_fault_manager_tab_changed(self, index, itemManager, importExport):
        """故障管理系统标签页切换时的处理"""
        print(f"[AppInterface] 故障管理系统标签页切换到索引: {index}")
        # 当切换到条目管理标签时，重新加载项目列表
        if index == 1:  # 条目管理标签的索引
            print("[AppInterface] 切换到条目管理标签，重新加载项目列表")
            itemManager._load_projects()
        # 当切换到导入导出标签时，重新加载项目列表
        elif index == 2:  # 导入导出标签的索引
            print("[AppInterface] 切换到导入导出标签，重新加载项目列表")
            importExport._load_projects()
