"""
面包屑导航组件
用于显示当前位置和支持快速导航
"""

from typing import List, Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QHBoxLayout
from qfluentwidgets import (
    BreadcrumbBar, FluentIcon as FIF, 
    TransparentToolButton, BodyLabel
)


class BreadcrumbNavigation(QWidget):
    """面包屑导航组件"""
    
    # 信号定义
    navigateRequested = Signal(str)  # 导航到指定路径
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._path_items: List[str] = []
        self._init_ui()
    
    def _init_ui(self):
        """初始化UI"""
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(4)
        
        # 主页按钮
        self.home_btn = TransparentToolButton(FIF.HOME, self)
        self.home_btn.setFixedSize(32, 32)
        self.home_btn.setToolTip(self.tr("Back to Home"))
        self.home_btn.clicked.connect(lambda: self.navigateRequested.emit("home"))
        self.layout.addWidget(self.home_btn)
        
        # 面包屑条
        self.breadcrumb_bar = BreadcrumbBar(self)
        self.breadcrumb_bar.currentItemChanged.connect(self._on_breadcrumb_changed)
        self.layout.addWidget(self.breadcrumb_bar, 1)
        
        # 刷新按钮
        self.refresh_btn = TransparentToolButton(FIF.SYNC, self)
        self.refresh_btn.setFixedSize(32, 32)
        self.refresh_btn.setToolTip(self.tr("Refresh"))
        self.layout.addWidget(self.refresh_btn)
    
    def set_path(self, path_items: List[str]):
        """
        设置面包屑路径
        
        Args:
            path_items: 路径项列表，如 ["插件管理", "CCP Tool"]
        """
        self._path_items = path_items
        self._update_breadcrumb()
    
    def _update_breadcrumb(self):
        """更新面包屑显示"""
        self.breadcrumb_bar.clear()
        
        for i, item in enumerate(self._path_items):
            self.breadcrumb_bar.addItem(
                routeKey=f"item_{i}",
                text=item
            )
        
        # 选中最后一项
        if self._path_items:
            self.breadcrumb_bar.setCurrentItem(f"item_{len(self._path_items) - 1}")
    
    def _on_breadcrumb_changed(self, route_key: str):
        """面包屑项改变时触发"""
        if route_key.startswith("item_"):
            index = int(route_key.split("_")[1])
            if 0 <= index < len(self._path_items):
                # 构建导航路径
                path = "/".join(self._path_items[:index + 1])
                self.navigateRequested.emit(path)
    
    def get_current_path(self) -> str:
        """获取当前路径"""
        return "/".join(self._path_items)
    
    def add_path_item(self, item: str):
        """添加路径项"""
        self._path_items.append(item)
        self._update_breadcrumb()
    
    def pop_path_item(self) -> Optional[str]:
        """移除最后一个路径项"""
        if self._path_items:
            item = self._path_items.pop()
            self._update_breadcrumb()
            return item
        return None
    
    def clear_path(self):
        """清空路径"""
        self._path_items.clear()
        self._update_breadcrumb()
