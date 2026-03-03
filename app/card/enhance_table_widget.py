import os
import sys

from PySide6.QtCore import QEvent, QModelIndex, Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QHBoxLayout,
    QHeaderView,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    SearchLineEdit,
    SpinBox,
    TableView,
    ToolButton,
)

from app.common.icon import Icon
from app.model import (
    DocumentModel,
    FieldModel,
    FieldFillMode,
    FontModel,
    ProjectModel,
    TemplateModel,
)
from app.resource import resource_rc
from app.table_model import (
    DocumentTableModel,
    FieldTableModel,
    FontTableModel,
    ProjectTableModel,
    TemplateTableModel,
)


class EnhancedTabelWidget(QWidget):
    def __init__(
        self,
        data: list = None,
        model_type: str = "document",
        page_size: int = 10,
    ):
        super().__init__()
        self.data = data if data else []
        self.model_type = model_type
        self.page_size = page_size

        # 定义UI组件
        self.tableView = TableView()
        self.searchLineEdit = SearchLineEdit()
        self.widget_page_controller = QWidget()
        self.bodyLabel = BodyLabel()
        self.spinBox_Page = SpinBox()
        self.toolButton_first_page = ToolButton()
        self.toolButton_last_page = ToolButton()
        self.toolButton_next_page = ToolButton()
        self.toolButton_final_page = ToolButton()

        # 初始化组件
        self._init_widget()
        # 设置布局
        self._init_layout()
        # 连接信号和槽
        self._connect_signals()
        # 初始化数据
        self._init_data()
        # 更新页面信息
        self.update_page_info()

    def _init_widget(self):
        """初始化组件"""
        self.tableView.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableView.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tableView.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )
        self.tableView.setBorderRadius(8)
        self.tableView.setBorderVisible(True)
        self.tableView.verticalHeader().setVisible(False)
        self.tableView.setCurrentIndex(QModelIndex())

        self.searchLineEdit.setPlaceholderText("搜索...")
        self.searchLineEdit.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed
        )

        self.toolButton_first_page.setIcon(Icon.FIRST_PAGE.path())
        self.toolButton_last_page.setIcon(Icon.LAST_PAGE.path())
        self.toolButton_next_page.setIcon(Icon.NEXT_PAGE.path())
        self.toolButton_final_page.setIcon(Icon.FINAL_PAGE.path())

        self.spinBox_Page.setMinimumWidth(50)

    def _init_layout(self):
        """设置布局"""
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.searchLineEdit)
        main_layout.addWidget(self.tableView)

        page_layout = QHBoxLayout(self.widget_page_controller)
        page_layout.setContentsMargins(0, 0, 0, 0)

        # 添加分页按钮和控件
        page_layout.addStretch()
        page_layout.addWidget(self.toolButton_first_page)
        page_layout.addWidget(self.toolButton_last_page)
        page_layout.addWidget(self.spinBox_Page)
        page_layout.addWidget(self.bodyLabel)
        page_layout.addWidget(self.toolButton_next_page)
        page_layout.addWidget(self.toolButton_final_page)
        page_layout.addStretch()

        # 将分页控制器添加到主布局
        main_layout.addWidget(self.widget_page_controller)

        # 初始显示分页控制器
        self.widget_page_controller.show()

    def _connect_signals(self):
        """连接信号和槽"""
        # 连接按钮点击事件
        self.toolButton_first_page.clicked.connect(self._first_page)
        self.toolButton_last_page.clicked.connect(self._last_page)
        self.toolButton_next_page.clicked.connect(self._next_page)
        self.toolButton_final_page.clicked.connect(self._final_page)

        # 连接跳转页面控件信号
        self.spinBox_Page.valueChanged.connect(self._go_to_page)

        # 连接搜索控件信号
        self.searchLineEdit.searchButton.clicked.connect(self._search)
        self.searchLineEdit.returnPressed.connect(self._search)

        # 安装事件过滤器以处理点击空白区域清除选中
        self.tableView.viewport().installEventFilter(self)

    def _init_data(self):
        """初始化数据模型"""
        # 根据model_type选择合适的模型
        if self.model_type == "document":
            self.table_model = DocumentTableModel(
                self.data, page_size=self.page_size
            )
        elif self.model_type == "project":
            self.table_model = ProjectTableModel(
                self.data, page_size=self.page_size
            )
        elif self.model_type == "template":
            self.table_model = TemplateTableModel(
                self.data, page_size=self.page_size
            )
        elif self.model_type == "field":
            self.table_model = FieldTableModel(
                self.data, page_size=self.page_size
            )
        elif self.model_type == "font":
            self.table_model = FontTableModel(
                self.data, page_size=self.page_size
            )
        else:
            raise ValueError(
                f"[EnhancedTabelWidget] Unsupported model type: {self.model_type}"
            )

        # 设置模型到表格
        self.tableView.setModel(self.table_model)

        # 保存原始数据
        self.original_data = self.data.copy() if self.data else []

    def _first_page(self):
        """处理首页按钮点击事件"""
        self.table_model.set_current_page(1)
        self.update_page_info()

    def _last_page(self):
        """处理上一页按钮点击事件"""
        current_page = self.table_model.current_page()
        if current_page > 1:
            self.table_model.set_current_page(current_page - 1)
            self.update_page_info()

    def _next_page(self):
        """处理下一页按钮点击事件"""
        current_page = self.table_model.current_page()
        page_count = self.table_model.page_count()
        if current_page < page_count:
            self.table_model.set_current_page(current_page + 1)
            self.update_page_info()

    def _final_page(self):
        """处理末页按钮点击事件"""
        page_count = self.table_model.page_count()
        self.table_model.set_current_page(page_count)
        self.update_page_info()

    def update_page_info(self):
        """更新页面信息显示"""
        # 如果小于等于一页，则隐藏页码控件
        if self.table_model.page_count() <= 1:
            self.widget_page_controller.hide()
        else:
            self.widget_page_controller.show()
        page_info = self.table_model.get_page_info()
        self.bodyLabel.setText(page_info)

        # 更新跳转页面控件的范围和当前值
        self.spinBox_Page.setMinimum(1)
        self.spinBox_Page.setMaximum(self.table_model.page_count())
        self.spinBox_Page.setValue(self.table_model.current_page())

    def _go_to_page(self, page: int):
        """跳转到指定页码"""
        self.table_model.set_current_page(page)
        self.update_page_info()

    def _search(self):
        """处理搜索功能"""
        self.widget_page_controller.show()
        search_text = self.searchLineEdit.text().strip()
        if not search_text:
            # 如果搜索文本为空，恢复原始数据
            self.data = self.original_data.copy() if self.original_data else []
            self.table_model.set_data(self.data)
            self.update_page_info()
            return

        # 根据搜索文本过滤数据
        filtered_data = []
        for item in self.original_data:
            # 检查对象的所有属性是否包含搜索文本
            if self._item_matches_search(item, search_text):
                filtered_data.append(item)

        # 更新数据
        self.data = filtered_data
        self.table_model.set_data(self.data)

        # 重置到第一页
        self.table_model.set_current_page(1)
        self.update_page_info()

    def _item_matches_search(self, item, search_text: str) -> bool:
        """检查项目是否匹配搜索文本"""
        # 获取对象的所有属性值
        for attr_name in dir(item):
            # 跳过私有属性和方法
            if not attr_name.startswith("_") and not callable(
                getattr(item, attr_name)
            ):
                attr_value = getattr(item, attr_name)
                # 如果属性值包含搜索文本，返回True
                if (
                    isinstance(attr_value, str)
                    and search_text.lower() in attr_value.lower()
                ):
                    return True
                # 如果属性是字典，检查字典的键和值
                elif isinstance(attr_value, dict):
                    for key, value in attr_value.items():
                        if (
                            isinstance(key, str)
                            and search_text.lower() in key.lower()
                        ):
                            return True
                        if (
                            isinstance(value, str)
                            and search_text.lower() in value.lower()
                        ):
                            return True
                # 处理列表类型
                elif isinstance(attr_value, list):
                    for value in attr_value:
                        if (
                            isinstance(value, str)
                            and search_text.lower() in value.lower()
                        ):
                            return True
        return False

    def set_column(
        self,
        column_title: str,
        width: int = None,
        replace_str: str = None,
        hide_flag: bool = False,
    ):
        column_count = self.table_model.columnCount()
        column_title_list = [
            self.table_model.headerData(i, Qt.Horizontal, 0)
            for i in range(column_count)
        ]
        if column_title in column_title_list:
            if hide_flag:
                self.tableView.setColumnHidden(
                    column_title_list.index(column_title), True
                )
                return
            if width:
                self.tableView.horizontalHeader().setSectionResizeMode(
                    column_title_list.index(column_title), QHeaderView.Fixed
                )
                self.tableView.setColumnWidth(
                    column_title_list.index(column_title), width
                )
            if replace_str:
                self.table_model.setHeaderData(
                    column_title_list.index(column_title),
                    Qt.Horizontal,
                    replace_str,
                )

    def eventFilter(self, watched, event):
        """事件过滤器，用于处理点击表格空白区域清除选中"""
        if watched == self.tableView.viewport():
            if event.type() == QEvent.MouseButtonPress:
                # 获取点击位置对应的索引
                pos = (
                    event.position().toPoint()
                    if hasattr(event, "position")
                    else event.pos()
                )
                index = self.tableView.indexAt(pos)
                # 如果点击的是空白区域（即索引无效）
                if not index.isValid():
                    # 清除选中
                    self.tableView.clearSelection()
                    self.tableView.setCurrentIndex(QModelIndex())
        # 调用父类的事件过滤器
        return super().eventFilter(watched, event)

    def set_data(self, data: list = None):
        """设置数据列表"""
        self.data = data if data else []
        self.original_data = self.data.copy()
        self.table_model.set_data(self.data)
        # 重置到第一页
        self.table_model.set_current_page(1)
        self.update_page_info()

    def get_data(self) -> list:
        """获取当前显示的数据列表"""
        return self.data


if __name__ == "__main__":

    # 生成测试数据
    documents = []
    for i in range(1, 101):
        doc = DocumentModel(
            project_id=f"PROJ{(i-1)//5+1:03d}",
            template_id=f"TEMP{(i-1)%5+1:03d}",
            document_number=f"2023-{i:03d}",
            document_name=f"测试文档{i}",
            document_description=f"这是第{i}个测试文档",
            document_tags=f"标签{i}",
            created_at=f"2023-01-{i:02d}",
            updated_at=f"2023-02-{i:02d}",
        )
        documents.append(doc)

    # 生成项目测试数据
    projects = []
    for i in range(1, 51):
        proj = ProjectModel(
            project_number=f"PROJ{i:03d}",
            project_name=f"测试项目{i}",
            project_description=f"这是第{i}个测试项目",
            project_tags=f"标签{i}",
            prepared_by=f"编制人{i}",
            project_path=f"/projects/proj{i}",
            created_at=f"2023-01-{i:02d}",
            updated_at=f"2023-02-{i:02d}",
        )
        projects.append(proj)

    # 生成模板测试数据
    templates = []
    for i in range(1, 31):
        temp = TemplateModel(
            template_number=f"TEMP{i:03d}",
            template_category=f"分类{(i-1)%3+1}",
            template_name=f"测试模板{i}",
            created_at=f"2023-01-{i:02d}",
        )
        templates.append(temp)

    # 生成字段测试数据
    fields = []
    for i in range(1, 12):
        field = FieldModel(
            field_name=f"字段{i}",
            field_value=f"值{i+1},值{i+2},值{i+3}",
            fill_mode=FieldFillMode.MATCH_FILL_RIGHT,
            table_num=1,
            table_row=i,
            table_col=i,
            font_id=1,
        )
        fields.append(field)

    app = QApplication(sys.argv)

    flag = "field"

    if flag == "document":
        print("Testing Document Model...")
        document_manager = EnhancedTabelWidget(
            documents, "document", page_size=10
        )
        document_manager.show()
    elif flag == "project":
        print("Testing Project Model...")
        project_manager = EnhancedTabelWidget(
            projects, "project", page_size=10
        )
        project_manager.show()
    elif flag == "template":
        print("Testing Template Model...")
        template_manager = EnhancedTabelWidget(
            templates, "template", page_size=10
        )
        template_manager.show()
    elif flag == "field":
        print("Testing Field Model...")
        field_manager = EnhancedTabelWidget(fields, "field", page_size=10)
        field_manager.show()

    sys.exit(app.exec())
