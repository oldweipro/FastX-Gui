from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTabWidget
from qfluentwidgets import (
    FluentIcon as FIF,
    SubtitleLabel,
    TabWidget
)

from app.model.fault_model import FaultManager
from app.tools.ui.FastFaultManager_template_ui import TemplateManagerUI
from app.tools.ui.FastFaultManager_project_ui import ProjectManagerUI
from app.tools.ui.FastFaultManager_item_ui import ItemManagerUI
from app.tools.ui.FastFaultManager_import_export import ImportExportUI


class FastFaultManagerMainUI(QWidget):
    """故障管理文档系统主界面"""
    def __init__(self, parent=None):
        super().__init__(parent)
        # 初始化故障管理器
        self.fault_manager = FaultManager()
        self._init_ui()
    
    def _init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        
        # 标题
        layout.addWidget(SubtitleLabel(self.tr("故障管理文档系统"), self))
        
        # 标签页
        self.tabWidget = TabWidget(self)
        
        # 项目管理标签
        self.projectManager = ProjectManagerUI(self.fault_manager, self)
        self.tabWidget.addTab(self.projectManager, self.tr("项目管理"), FIF.FOLDER)
        
        # 条目管理标签
        self.itemManager = ItemManagerUI(self.fault_manager, self)
        self.tabWidget.addTab(self.itemManager, self.tr("条目管理"), FIF.DOCUMENT)
        
        # 导入导出标签
        self.importExport = ImportExportUI(self.fault_manager, self)
        self.tabWidget.addTab(self.importExport, self.tr("导入导出"), FIF.SHARE)
        
        layout.addWidget(self.tabWidget)
        
        # 连接信号
        # 当项目列表变化时，更新相关界面
        self.tabWidget.currentChanged.connect(self._on_tab_changed)
        
    def _on_tab_changed(self, index):
        """标签页切换时的处理"""
        # 当切换到条目管理标签时，重新加载项目列表
        if index == 1:  # 条目管理标签的索引
            self.itemManager._load_projects()
        # 当切换到导入导出标签时，重新加载项目列表
        elif index == 2:  # 导入导出标签的索引
            self.importExport._load_projects()