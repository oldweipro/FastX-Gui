import datetime
import json
import sys
import typing
from enum import Enum
from typing import List, Optional, Any, Type

from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, Signal
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QFileDialog, QHeaderView, QSizePolicy, QDialog, QFrame
)
from PySide6.QtGui import QIcon

# 导入 qfluentwidgets 组件
from qfluentwidgets import (
    setTheme, Theme, PushButton, SearchLineEdit, SpinBox, BodyLabel,
    TableView, InfoBar, InfoBarPosition, FluentIcon, ToolButton,
    MessageBoxBase, SubtitleLabel, LineEdit, ComboBox, Dialog, DoubleSpinBox, TextEdit, DateTimeEdit, DateEdit,
    ScrollArea, RoundMenu, TransparentDropDownPushButton, Action, PrimaryDropDownToolButton, PrimaryDropDownPushButton,
    TransparentDropDownToolButton
)

# 尝试使用相对导入
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.common.icon import Icon
from pydantic import BaseModel, Field

class EnumCore(Enum):
    Core0 = 'Core0'
    Core1 = 'Core1'
    Core2 = 'Core2'
    Core3 = 'Core3'

# -------------------- 数据模型 (使用 Pydantic) --------------------
class Document(BaseModel):
    """文档数据类"""
    id: int = Field(..., title="ID")
    enable: bool = Field(..., title='使能')
    core: EnumCore = Field(...,title='内核分配')
    doc_number: str = Field(..., title="文档编号")
    name: str = Field(..., title="名称")
    description: str = Field("", title="描述")
    tags: str = Field("", title="标签")
    created_at: str = Field(..., title="创建时间")


# -------------------- 非 Pydantic 数据模型 --------------------
class Product:
    """产品数据类（非 Pydantic）"""
    def __init__(self, id, name, price, stock, category):
        self.id = id
        self.name = name
        self.price = price
        self.stock = stock
        self.category = category



# -------------------- 基础分页模型 --------------------
class BaseTableModel(QAbstractTableModel):
    """
    分页表格模型的基类
    管理原始数据 _all_data 和过滤后数据 _filtered_data
    提供分页、过滤、获取行对象的基础实现
    子类必须实现 columnCount()、data()、_get_header_labels()
    以及可选的 to_dataframe() / from_dataframe() 用于导入导出
    """
    def __init__(self, data: Optional[List] = None, page_size: int = 10, parent=None):
        super().__init__(parent)
        self._all_data = data if data is not None else []
        self._filtered_data = self._all_data[:]   # 初始与全部数据相同
        self._page_size = page_size
        self._current_page = 1
        self._sort_column = -1  # 默认不排序
        self._sort_order = Qt.AscendingOrder  # 默认升序

    # ---------- 必须由子类实现的方法 ----------
    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        raise NotImplementedError

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        raise NotImplementedError

    def _get_header_labels(self) -> List[str]:
        """返回表头标签列表"""
        raise NotImplementedError

    # ---------- 分页/过滤接口 ----------
    def filter(self, text: str):
        """默认过滤逻辑（动态解析属性）"""
        if not text:
            self._filtered_data = self._all_data[:]
        else:
            low_text = text.lower()
            self._filtered_data = [
                item for item in self._all_data
                if self._is_item_match(item, low_text)
            ]
        self._current_page = 1
        self.beginResetModel()
        self.endResetModel()

    def _is_item_match(self, item, text):
        """检查项目是否匹配搜索文本"""
        # 对于 PydanticTableModel，直接通过字段名获取值
        if hasattr(self, 'fields') and hasattr(item, '__dict__'):
            for field_name in self.fields:
                value = getattr(item, field_name, "")
                # 处理枚举类型
                if hasattr(value, 'value'):
                    value = value.value
                if text in str(value).lower():
                    return True
        
        # 对于其他模型，尝试获取对象的所有属性
        if hasattr(item, '__dict__'):
            # 尝试获取对象的所有属性
            for attr_name, attr_value in item.__dict__.items():
                # 跳过私有属性
                if attr_name.startswith('_'):
                    continue
                # 处理枚举类型
                if hasattr(attr_value, 'value'):
                    attr_value = attr_value.value
                if text in str(attr_value).lower():
                    return True
        
        # 默认返回 False
        return False

    def page_count(self) -> int:
        return max(1, (len(self._filtered_data) + self._page_size - 1) // self._page_size)

    def current_page(self) -> int:
        return self._current_page

    def set_current_page(self, page: int):
        if 1 <= page <= self.page_count():
            self._current_page = page
            self.beginResetModel()
            self.endResetModel()

    def get_item(self, row: int) -> Any:
        """返回当前页中第 row 行的原始数据对象"""
        start = (self._current_page - 1) * self._page_size
        return self._filtered_data[start + row]

    # ---------- 导入导出（需子类实现）----------
    def to_dataframe(self):
        """将 _all_data 转换为 pandas.DataFrame（子类需实现）"""
        raise NotImplementedError("子类必须实现 to_dataframe 方法")

    def from_dataframe(self, df):
        """从 pandas.DataFrame 加载数据到 _all_data（子类需实现）"""
        raise NotImplementedError("子类必须实现 from_dataframe 方法")

    def import_from_excel(self, filepath: str):
        """从 Excel 导入数据"""
        try:
            import pandas as pd
            df = pd.read_excel(filepath)
            self.from_dataframe(df)
            self.set_all_data(self._all_data)  # 触发视图刷新
            InfoBar.success(
                title="导入成功",
                content=f"已从 {filepath} 导入数据",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=None
            )
        except Exception as e:
            InfoBar.error(
                title="导入失败",
                content=str(e),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=None
            )
            raise

    def export_to_excel(self, filepath: str):
        """导出数据到 Excel"""
        try:
            import pandas as pd
            df = self.to_dataframe()
            df.to_excel(filepath, index=False)
            InfoBar.success(
                title="导出成功",
                content=f"已导出到 {filepath}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=None
            )
        except Exception as e:
            InfoBar.error(
                title="导出失败",
                content=str(e),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=None
            )
            raise

    # ---------- 辅助方法 ----------
    def set_all_data(self, data: List):
        """设置全部数据，重置过滤和页码"""
        self.beginResetModel()
        self._all_data = data[:]
        self._filtered_data = data[:]
        self._current_page = 1
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        start = (self._current_page - 1) * self._page_size
        end = min(start + self._page_size, len(self._filtered_data))
        return end - start

    def headerData(self, section: int, orientation: Qt.Orientation,
                   role: int = Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            headers = self._get_header_labels()
            if headers and section < len(headers):
                return headers[section]
        return None

    def sort(self, column: int, order: Qt.SortOrder = Qt.AscendingOrder):
        """
        排序数据
        :param column: 排序列索引
        :param order: 排序方向
        """
        self.beginResetModel()
        self._sort_column = column
        self._sort_order = order
        self._sort_data()
        self.endResetModel()

    def clearSort(self):
        """
        清除排序，恢复到初始状态
        """
        self.beginResetModel()
        self._sort_column = -1
        self._sort_order = Qt.AscendingOrder
        # 恢复原始数据顺序
        self._filtered_data = self._all_data[:]
        self.endResetModel()

    def _sort_data(self):
        """
        排序数据（通用实现）
        """
        if self._sort_column >= 0 and self._filtered_data:
            # 定义一个获取列值的函数
            def get_column_value(item, column):
                # 对于 PydanticTableModel，直接通过字段名获取值
                if hasattr(self, 'fields') and hasattr(item, '__dict__'):
                    if column < len(self.fields):
                        field_name = self.fields[column]
                        value = getattr(item, field_name, "")
                        # 处理枚举类型
                        if hasattr(value, 'value'):
                            return value.value
                        return value
                
                # 对于其他模型，尝试通过 data 方法获取列值
                # 注意：这里需要确保 data 方法能够正确处理索引
                try:
                    # 创建一个临时索引来获取数据
                    # 使用 0 作为行索引，因为我们只关心列的值类型
                    temp_index = self.createIndex(0, column)
                    value = self.data(temp_index, Qt.DisplayRole)
                    if value is not None:
                        # 处理枚举类型
                        if hasattr(value, 'value'):
                            return value.value
                        return value
                except Exception:
                    pass
                
                # 对于其他模型，尝试获取对象的属性
                if hasattr(item, '__dict__'):
                    # 尝试获取对象的所有属性
                    attrs = list(item.__dict__.keys())
                    # 去除私有属性
                    attrs = [attr for attr in attrs if not attr.startswith('_')]
                    # 如果列索引在属性列表范围内，返回对应属性值
                    if column < len(attrs):
                        attr_name = attrs[column]
                        value = getattr(item, attr_name, "")
                        # 处理枚举类型
                        if hasattr(value, 'value'):
                            return value.value
                        return value
                
                # 默认返回空字符串
                return ""
            
            # 排序数据
            self._filtered_data.sort(
                key=lambda item: get_column_value(item, self._sort_column),
                reverse=(self._sort_order == Qt.DescendingOrder)
            )


# -------------------- 具体文档模型 --------------------
class DocumentTableModel(BaseTableModel):
    """文档表格模型，负责显示 Document 对象"""
    def columnCount(self, parent=QModelIndex()) -> int:
        return 5   # 编号、名称、描述、标签、创建时间

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        try:
            item: Document = self.get_item(index.row())
            if role == Qt.DisplayRole:
                col = index.column()
                if col == 0:
                    return item.doc_number
                elif col == 1:
                    return item.name
                elif col == 2:
                    return item.description
                elif col == 3:
                    return item.tags
                elif col == 4:
                    return item.created_at
        except Exception:
            # 如果索引越界，返回 None
            pass
        return None

    def _get_header_labels(self):
        return ["文档编号", "名称", "描述", "标签", "创建时间"]

    def filter(self, text: str):
        """针对特定字段搜索"""
        if not text:
            self._filtered_data = self._all_data[:]
        else:
            low = text.lower()
            self._filtered_data = [
                d for d in self._all_data
                if low in d.name.lower() or low in d.doc_number.lower()
            ]
        self._current_page = 1
        self.beginResetModel()
        self.endResetModel()

    def to_dataframe(self):
        """将文档列表转换为 DataFrame"""
        import pandas as pd
        return pd.DataFrame([d.model_dump() for d in self._all_data])

    def from_dataframe(self, df):
        """从 DataFrame 加载文档列表"""
        self._all_data = [Document(**row) for _, row in df.iterrows()]


class ProductTableModel(BaseTableModel):
    """产品表格模型（非 Pydantic）"""
    def columnCount(self, parent=QModelIndex()) -> int:
        return 5   # ID、名称、价格、库存、类别

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        try:
            item: Product = self.get_item(index.row())
            if role == Qt.DisplayRole:
                col = index.column()
                if col == 0:
                    return item.id
                elif col == 1:
                    return item.name
                elif col == 2:
                    return item.price
                elif col == 3:
                    return item.stock
                elif col == 4:
                    return item.category
        except Exception:
            # 如果索引越界，返回 None
            pass
        return None

    def _get_header_labels(self):
        return ["ID", "名称", "价格", "库存", "类别"]

    def to_dataframe(self):
        """将产品列表转换为 DataFrame"""
        import pandas as pd
        data = []
        for item in self._all_data:
            data.append({
                'id': item.id,
                'name': item.name,
                'price': item.price,
                'stock': item.stock,
                'category': item.category
            })
        return pd.DataFrame(data)

    def from_dataframe(self, df):
        """从 DataFrame 加载产品列表"""
        self._all_data = []
        for _, row in df.iterrows():
            product = Product(
                id=int(row.get('id', 0)),
                name=str(row.get('name', '')),
                price=float(row.get('price', 0.0)),
                stock=int(row.get('stock', 0)),
                category=str(row.get('category', ''))
            )
            self._all_data.append(product)


class PydanticTableModel(BaseTableModel):
    """
    通用的 Pydantic 表格模型，自动根据模型类的字段生成列。
    可通过 include_fields / exclude_fields 控制显示哪些字段。
    """
    def __init__(self, model_class: Type[BaseModel],
                 data: Optional[List] = None,
                 page_size: int = 10,
                 parent=None,
                 include_fields: Optional[List[str]] = None,
                 exclude_fields: Optional[List[str]] = None,
                 field_titles: Optional[dict] = None):
        super().__init__(data, page_size, parent)
        self.model_class = model_class

        # 确定要显示的字段
        all_fields = list(model_class.model_fields.keys())
        if include_fields is not None:
            self.fields = [f for f in all_fields if f in include_fields]
        elif exclude_fields is not None:
            self.fields = [f for f in all_fields if f not in exclude_fields]
        else:
            self.fields = all_fields

        # 构建列标题（优先使用 field_titles 映射，否则使用字段的 title 或字段名）
        self.headers = []
        for f in self.fields:
            if field_titles and f in field_titles:
                self.headers.append(field_titles[f])
            else:
                field_info = model_class.model_fields[f]
                self.headers.append(field_info.title or f)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self.fields)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        try:
            item = self.get_item(index.row())
            field_name = self.fields[index.column()]
            if role == Qt.DisplayRole:
                value = getattr(item, field_name, "")
                # 特殊处理枚举、布尔等类型，使其显示为友好字符串
                if isinstance(value, Enum):
                    return value.value
                elif isinstance(value, bool):
                    return "是" if value else "否"
                return str(value)
        except Exception:
            # 如果索引越界，返回 None
            pass
        return None

    def _get_header_labels(self) -> List[str]:
        return self.headers

    def to_dataframe(self):
        """将文档列表转换为 DataFrame"""
        import pandas as pd
        return pd.DataFrame([d.model_dump(mode='json') for d in self._all_data])

    def from_dataframe(self, df):
        """从 DataFrame 加载文档列表"""
        self._all_data = [Document(**row) for _, row in df.iterrows()]

# -------------------- 动态编辑对话框 --------------------
class DynamicEditDialog(MessageBoxBase):
    def __init__(self, item, parent=None):
        super().__init__(parent)
        self.item = item
        self.model_class = None
        self.fields = []
        self.field_infos = {}
        
        # 检查是否是 Pydantic 模型或具有 model_fields 属性的对象
        if hasattr(item, '_original_model_class'):
            # 临时对象，使用原始模型类
            self.model_class = item._original_model_class
            self.fields = list(self.model_class.model_fields.keys())
            self.field_infos = {f: self.model_class.model_fields[f] for f in self.fields}
        elif hasattr(item, '__class__') and hasattr(item.__class__, 'model_fields'):
            # 标准 Pydantic 模型
            self.model_class = type(item)
            self.fields = list(self.model_class.model_fields.keys())
            self.field_infos = {f: self.model_class.model_fields[f] for f in self.fields}
        else:
            # 非 Pydantic 模型，使用对象的属性
            self.fields = [attr for attr in dir(item) if not attr.startswith('_') and not callable(getattr(item, attr))]
            # 为非 Pydantic 模型创建假的 field_info
            for field in self.fields:
                self.field_infos[field] = type('FieldInfo', (), {'title': field, 'annotation': str})()

        # 标题（始终可见，不在滚动区域内）
        if self.model_class:
            title = f"编辑 {self.model_class.__name__}"
        else:
            title = "编辑数据"
        self.titleLabel = SubtitleLabel(title, self)
        self.viewLayout.addWidget(self.titleLabel)

        # 创建滚动区域
        self.scrollArea = ScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setFrameShape(QFrame.Shape.NoFrame)          # 去除边框
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # 设置滚动区域背景透明
        self.scrollArea.setStyleSheet("ScrollArea { background: transparent; border: none; }")
        self.scrollArea.viewport().setStyleSheet("background: transparent;")

        # 滚动区域的内容容器及其布局
        self.scrollWidget = QWidget()
        self.scrollLayout = QVBoxLayout(self.scrollWidget)
        self.scrollLayout.setSpacing(12)                       # 与 viewLayout 默认间距一致
        self.scrollLayout.setContentsMargins(0, 0, 20, 0)       # 边距由外层 viewLayout 控制

        self.editors = {}

        for field in self.fields:
            field_info = self.field_infos[field]
            field_title = field_info.title or field
            current_value = getattr(item, field)

            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)

            label = BodyLabel(field_title)
            label.setFixedWidth(120)
            label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            row_layout.addWidget(label)

            editor = self._create_editor(field, field_info, current_value)
            editor.setMinimumWidth(250)
            row_layout.addWidget(editor)

            self.editors[field] = editor
            self.scrollLayout.addWidget(row_widget)

        # 将内容容器设置到滚动区域
        self.scrollArea.setWidget(self.scrollWidget)
        # 将滚动区域添加到主布局（标题下方）
        self.viewLayout.addWidget(self.scrollArea)

        # 设置按钮文本
        self.yesButton.setText("保存")
        self.cancelButton.setText("取消")
        self.widget.setMinimumWidth(600)

        # 限制对话框最大高度（屏幕高度的80%）
        screen = QApplication.primaryScreen().availableGeometry()
        max_height = int(screen.height() * 0.8)
        self.setMaximumHeight(max_height)

    @staticmethod
    def _create_editor(field, field_info, current_value):
        annotation = field_info.annotation
        origin = typing.get_origin(annotation)
        args = typing.get_args(annotation)

        # 处理 Optional
        if origin is typing.Union and type(None) in args:
            real_type = next(t for t in args if t is not type(None))
            annotation = real_type
            origin = typing.get_origin(annotation)
            args = typing.get_args(annotation)

        # 基本类型
        # 检查是否为PydanticUndefinedType
        is_undefined = False
        try:
            from pydantic import PydanticUndefined
            is_undefined = current_value is PydanticUndefined
        except ImportError:
            pass
        
        # 额外检查：如果current_value的类型名称包含"Undefined"，也视为undefined
        if not is_undefined and hasattr(current_value, '__class__'):
            class_name = current_value.__class__.__name__
            if 'Undefined' in class_name:
                is_undefined = True
        
        if annotation is int or (origin is None and annotation is int):
            editor = SpinBox()
            editor.setRange(-10**9, 10**9)
            editor.setValue(current_value if current_value is not None and not is_undefined else 0)
        elif annotation is float:
            editor = DoubleSpinBox()
            editor.setRange(-10**9, 10**9)
            editor.setValue(current_value if current_value is not None and not is_undefined else 0.0)
        elif annotation is bool:
            editor = ComboBox()
            editor.addItems(["True", "False"])
            if current_value is not None and not is_undefined:
                editor.setCurrentText(str(current_value))
            else:
                editor.setCurrentText("False")
        elif annotation is str:
            editor = LineEdit()
            editor.setText(str(current_value) if current_value is not None and not is_undefined else "")
        elif isinstance(annotation, type) and issubclass(annotation, Enum):
            editor = ComboBox()
            editor.addItems([e.value for e in annotation])
            if current_value is not None and not is_undefined:
                editor.setCurrentText(current_value.value if isinstance(current_value, Enum) else str(current_value))
            else:
                # 选择第一个枚举值
                if editor.count() > 0:
                    editor.setCurrentIndex(0)
        elif annotation is list or (origin is list):
            editor = TextEdit()
            editor.setPlainText(json.dumps(current_value, ensure_ascii=False, indent=2) if current_value is not None and not is_undefined else "[]")
            editor.setMinimumHeight(80)
        elif annotation is dict or (origin is dict):
            editor = TextEdit()
            editor.setPlainText(json.dumps(current_value, ensure_ascii=False, indent=2) if current_value is not None and not is_undefined else "{}")
            editor.setMinimumHeight(80)
        elif annotation is datetime:
            editor = DateTimeEdit()
            if current_value and not is_undefined:
                editor.setDateTime(current_value)
        elif annotation is datetime.date:
            editor = DateEdit()
            if current_value and not is_undefined:
                editor.setDate(current_value)
        else:
            editor = LineEdit()
            editor.setText(str(current_value) if current_value is not None and not is_undefined else "")
        return editor

    def get_updated_item(self):
        updated_data = {}
        for field, editor in self.editors.items():
            # 检查是否有 field_info（Pydantic 模型）
            if hasattr(self, 'field_infos') and field in self.field_infos:
                field_info = self.field_infos[field]
                annotation = field_info.annotation
                origin = typing.get_origin(annotation)
                args = typing.get_args(annotation)

                # 处理 Optional
                if origin is typing.Union and type(None) in args:
                    real_type = next(t for t in args if t is not type(None))
                    annotation = real_type
                    origin = typing.get_origin(annotation)
                    args = typing.get_args(annotation)
            else:
                # 非 Pydantic 模型，使用默认类型
                annotation = str

            if isinstance(editor, SpinBox):
                value = editor.value()
            elif isinstance(editor, DoubleSpinBox):
                value = editor.value()
            elif isinstance(editor, ComboBox):
                if hasattr(self, 'field_infos') and field in self.field_infos:
                    field_info = self.field_infos[field]
                    if isinstance(field_info.annotation, type) and issubclass(field_info.annotation, Enum):
                        value = field_info.annotation(editor.currentText())
                    else:
                        value = editor.currentText()
                else:
                    value = editor.currentText()
            elif isinstance(editor, TextEdit):
                text = editor.toPlainText()
                try:
                    value = json.loads(text)
                except:
                    value = text
            elif isinstance(editor, DateTimeEdit):
                value = editor.dateTime().toPython()
            elif isinstance(editor, DateEdit):
                value = editor.date().toPython()
            else:
                value = editor.text()
            updated_data[field] = value
        
        # 检查是否是 Pydantic 模型
        if hasattr(self, 'model_class') and self.model_class:
            return self.model_class(**updated_data)
        else:
            # 非 Pydantic 模型，返回一个普通对象
            class UpdatedItem:
                def __init__(self, data):
                    self.__dict__ = data
            return UpdatedItem(updated_data)

# -------------------- 通用表格组件 --------------------
class EnhancedTableWidget(QWidget):
    """
    通用分页表格组件（使用 qfluentwidgets）
    - 接受外部模型（必须实现约定的分页/过滤接口）
    - 提供搜索、分页导航、导入/导出按钮
    - 双击行时发射 doubleClicked 信号，携带该行数据对象
    """
    def __init__(self, model: Optional[QAbstractTableModel] = None, page_size: int = 10, parent=None):
        super().__init__(parent)
        self._model = None
        self._page_size = page_size

        # 创建UI组件（使用 qfluentwidgets）
        self.tableView = TableView(self)
        self.searchEdit = SearchLineEdit(self)
        self.searchEdit.setPlaceholderText("搜索...")
        self.searchEdit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # 创建右键菜单
        self.context_menu = RoundMenu(parent=self)
        # 添加复制功能
        self.context_menu.addAction(Action(FluentIcon.COPY, self.tr('复制 (JSON格式)'), triggered=lambda: self._on_copy_current_row('json')))
        self.context_menu.addAction(Action(FluentIcon.COPY, self.tr('复制所有行 (JSON格式)'), triggered=lambda: self._on_copy_all_rows('json')))
        self.context_menu.addSeparator()
        self.context_menu.addAction(Action(FluentIcon.COPY, self.tr('复制 (单行分隔符格式)'), triggered=lambda: self._on_copy_current_row('csv')))
        self.context_menu.addAction(Action(FluentIcon.COPY, self.tr('复制所有行 (单行分隔符格式)'), triggered=lambda: self._on_copy_all_rows('csv')))
        self.context_menu.addSeparator()
        self.context_menu.addAction(Action(FluentIcon.PASTE, self.tr('粘贴到当前行(单行)'), triggered=self._on_paste_to_current_row))
        self.context_menu.addAction(Action(FluentIcon.PASTE, self.tr('插入粘贴(单/多行)'), triggered=self._on_paste_multiple_rows))
        self.context_menu.addSeparator()
        # 添加行操作
        self.context_menu.addAction(Action(FluentIcon.ADD, self.tr('新增行'), triggered=self._on_add_row))
        self.context_menu.addAction(Action(FluentIcon.ADD, self.tr('插入行'), triggered=self._on_insert_row))
        self.context_menu.addAction(Action(FluentIcon.DELETE, self.tr('删除当前行'), triggered=self._on_delete_current_row))
        self.context_menu.addSeparator()
        # 添加导入导出功能
        self.context_menu.addAction(Action(FluentIcon.SEND, self.tr('导入到表格'), triggered=self._on_import))
        self.context_menu.addAction(Action(FluentIcon.SAVE, self.tr('导出到表格'), triggered=self._on_export))
        self.context_menu.addSeparator()
        # 添加排序功能
        self.context_menu.addAction(Action(FluentIcon.SCROLL, self.tr('清除筛选'), triggered=self._on_clear_sort))
        
        # 连接右键菜单信号
        self.tableView.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tableView.customContextMenuRequested.connect(self._show_context_menu)

        # 分页控制器
        self.pageWidget = QWidget(self)
        self.labelPageInfo = BodyLabel(self)
        self.spinPage = SpinBox(self)
        self.btnFirst = ToolButton(self)
        self.btnPrev = ToolButton(self)
        self.btnNext = ToolButton(self)
        self.btnLast = ToolButton(self)
        
        # 添加每页显示行数设置
        self.pageSizeLabel = BodyLabel("页")
        self.pageSizeComboBox = ComboBox()
        self.pageSizeComboBox.addItems(["10", "20", "30", "50", "100"])
        self.pageSizeComboBox.setCurrentText(str(self._page_size))
        self.pageSizeComboBox.currentTextChanged.connect(self._on_page_size_changed)

        # 设置按钮图标（使用 FluentIcon）
        self.btnFirst.setIcon(Icon.GO_START)
        self.btnPrev.setIcon(Icon.LEFT)
        self.btnNext.setIcon(Icon.RIGHT)
        self.btnLast.setIcon(Icon.GO_END)

        self._init_ui()
        self._connect_signals()

        if model is not None:
            self.setModel(model)

    def _init_ui(self):
        """初始化界面布局"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 搜索栏
        top_layout = QHBoxLayout()
        top_layout.addWidget(self.searchEdit)
        main_layout.addLayout(top_layout)

        # 表格
        self.tableView.setSelectionBehavior(TableView.SelectRows)
        self.tableView.setSelectionMode(TableView.ExtendedSelection)  # 支持多行选择
        self.tableView.horizontalHeader().setStretchLastSection(True)
        self.tableView.verticalHeader().setVisible(False)
        self.tableView.setBorderRadius(8)
        self.tableView.setBorderVisible(True)
        # 启用排序
        self.tableView.setSortingEnabled(True)
        main_layout.addWidget(self.tableView)

        # 分页控制器
        page_layout = QHBoxLayout(self.pageWidget)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.addStretch()
        page_layout.addWidget(self.btnFirst)
        page_layout.addWidget(self.btnPrev)
        page_layout.addWidget(self.spinPage)
        page_layout.addWidget(self.labelPageInfo)
        page_layout.addWidget(self.btnNext)
        page_layout.addWidget(self.btnLast)
        page_layout.addSpacing(20)
        page_layout.addWidget(self.pageSizeLabel)
        page_layout.addWidget(self.pageSizeComboBox)
        page_layout.addStretch()
        main_layout.addWidget(self.pageWidget)

        self.pageWidget.hide()

    def _connect_signals(self):
        """
        连接信号槽
        """
        self.searchEdit.searchButton.clicked.connect(self._on_search)
        self.searchEdit.returnPressed.connect(self._on_search)

        self.searchEdit.searchSignal.connect(self._on_search)
        self.searchEdit.clearSignal.connect(self._on_search)

        self.btnFirst.clicked.connect(lambda: self._go_to_page(1))
        self.btnPrev.clicked.connect(self._prev_page)
        self.btnNext.clicked.connect(self._next_page)
        self.btnLast.clicked.connect(self._last_page)
        self.spinPage.valueChanged.connect(self._go_to_page)

        self.tableView.doubleClicked.connect(self._on_double_click)
        
        # 添加Ctrl+C快捷键支持
        self.tableView.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tableView.customContextMenuRequested.connect(self._show_context_menu)
        
        # 注册Ctrl+C快捷键
        from PySide6.QtGui import QKeySequence
        copy_action = Action(FluentIcon.COPY, "复制", self)
        copy_action.setShortcut(QKeySequence.Copy)
        copy_action.triggered.connect(lambda: self._on_copy_current_row('json'))
        self.addAction(copy_action)

    # ------------------- 公共方法 -------------------
    def setModel(self, model: QAbstractTableModel):
        """设置数据模型（支持动态更换）"""
        self._model = model
        self.tableView.setModel(model)
        self._update_page_controls()
        # 启用右键菜单
        self.context_menu.setEnabled(True)

    def set_column(self, column_title: str, width: int = None,
                   replace_str: str = None, hide: bool = False):
        """
        设置列属性：宽度、隐藏、重命名
        """
        if self._model is None:
            return
        model = self._model
        col_count = model.columnCount()
        headers = [model.headerData(i, Qt.Horizontal) for i in range(col_count)]
        if column_title not in headers:
            return
        col_idx = headers.index(column_title)

        if hide:
            self.tableView.setColumnHidden(col_idx, True)
            return
        if width is not None:
            self.tableView.horizontalHeader().setSectionResizeMode(col_idx, QHeaderView.Fixed)
            self.tableView.setColumnWidth(col_idx, width)
        if replace_str is not None:
            model.setHeaderData(col_idx, Qt.Horizontal, replace_str)

    def set_page_size(self, page_size: int):
        """
        设置每页显示行数
        """
        if self._model and hasattr(self._model, '_page_size'):
            self._model._page_size = page_size
            self._model._current_page = 1  # 重置到第一页
            self._model.beginResetModel()
            self._model.endResetModel()
            self._update_page_controls()

    # ------------------- 私有槽函数 -------------------
    def _on_search(self):
        if self._model is None:
            return
        text = self.searchEdit.text().strip()
        if hasattr(self._model, 'filter'):
            self._model.filter(text)
            self._update_page_controls()

    def _on_import(self):
        if not hasattr(self._model, 'import_from_excel'):
            return
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择Excel文件", "", "Excel文件 (*.xlsx)"
        )
        if file_path:
            try:
                self._model.import_from_excel(file_path)
                self._update_page_controls()
            except Exception as e:
                InfoBar.error(
                    title="导入失败",
                    content=str(e),
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )

    def _on_export(self):
        if not hasattr(self._model, 'export_to_excel'):
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存Excel文件", "", "Excel文件 (*.xlsx)"
        )
        if file_path:
            try:
                self._model.export_to_excel(file_path)
            except Exception as e:
                InfoBar.error(
                    title="导出失败",
                    content=str(e),
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )

    def _on_double_click(self, index: QModelIndex):
        if self._model is None:
            return
        if hasattr(self._model, 'get_item'):
            row = index.row()
            item = self._model.get_item(row)
            if not isinstance(item, BaseModel):
                return
            dialog = DynamicEditDialog(item, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:  # 注意：MessageBoxBase 的 exec 返回值是 QDialog.Accepted
                updated = dialog.get_updated_item()
                # 更新数据：找到原对象并替换
                data_list = self._model._all_data
                for i, doc in enumerate(data_list):
                    if doc.doc_number == item.doc_number:  # 使用唯一标识符
                        data_list[i] = updated
                        break
                self._model.set_all_data(data_list)
                self._update_page_controls()

    def _update_page_controls(self):
        if self._model is None:
            self.pageWidget.hide()
            return
        if not all(hasattr(self._model, attr) for attr in
                   ('page_count', 'current_page', 'set_current_page')):
            self.pageWidget.hide()
            return

        total_pages = self._model.page_count()
        current = self._model.current_page()
        
        # 确保当前页有效
        if current > total_pages and total_pages > 0:
            self._model.set_current_page(total_pages)
            current = total_pages
        
        if total_pages <= 1:
            self.pageWidget.hide()
        else:
            self.pageWidget.show()
            self.labelPageInfo.setText(f"{current}/{total_pages}")
            self.spinPage.blockSignals(True)
            self.spinPage.setRange(1, total_pages)
            self.spinPage.setValue(current)
            self.spinPage.blockSignals(False)
            self.btnFirst.setEnabled(current > 1)
            self.btnPrev.setEnabled(current > 1)
            self.btnNext.setEnabled(current < total_pages)
            self.btnLast.setEnabled(current < total_pages)

    def _go_to_page(self, page: int):
        if self._model and hasattr(self._model, 'set_current_page'):
            self._model.set_current_page(page)
            self._update_page_controls()

    def _prev_page(self):
        if self._model and hasattr(self._model, 'current_page'):
            cur = self._model.current_page()
            if cur > 1:
                self._go_to_page(cur - 1)

    def _next_page(self):
        if self._model and hasattr(self._model, 'current_page'):
            cur = self._model.current_page()
            if cur < self._model.page_count():
                self._go_to_page(cur + 1)

    def _last_page(self):
        if self._model and hasattr(self._model, 'page_count'):
            self._go_to_page(self._model.page_count())

    def _on_clear_sort(self):
        """
        清除排序
        """
        if self._model and hasattr(self._model, 'clearSort'):
            self._model.clearSort()
            self._update_page_controls()

    def _on_page_size_changed(self, value):
        """
        处理每页显示行数变化
        """
        try:
            page_size = int(value)
            self.set_page_size(page_size)
        except ValueError:
            pass

    def _show_context_menu(self, pos):
        """
        显示右键菜单
        """
        # 首先获取鼠标所在的行
        index = self.tableView.indexAt(pos)
        if index.isValid():
            # 如果没有选中任何行，或者Ctrl键没有按下，选中鼠标所在的行
            if not self.tableView.selectionModel().hasSelection():
                # 选中该行
                self.tableView.setCurrentIndex(index)
        # 显示右键菜单
        self.context_menu.exec(self.tableView.mapToGlobal(pos))

    def _on_copy_current_row(self, format_type='json'):
        """
        复制当前行或选中的多行
        :param format_type: 复制格式，'json' 或 'csv'
        """
        selected_indexes = self.tableView.selectionModel().selectedRows()
        if not selected_indexes:
            return
        
        items = []
        for index in selected_indexes:
            row = index.row()
            if self._model and hasattr(self._model, 'get_item'):
                item = self._model.get_item(row)
                items.append(item)
        
        if not items:
            return
        
        # 实现复制逻辑，将数据保存到剪贴板
        import json
        data_list = []
        for item in items:
            if hasattr(item, 'model_dump'):
                # Pydantic 模型，使用 mode='json' 确保枚举类型正确序列化
                data = item.model_dump(mode='json')
            else:
                # 普通模型
                data = {}
                for attr in dir(item):
                    if not attr.startswith('_') and not callable(getattr(item, attr)):
                        value = getattr(item, attr)
                        # 处理枚举类型
                        if hasattr(value, 'value'):
                            value = value.value
                        data[attr] = value
            data_list.append(data)
        
        if format_type == 'json':
            # 将数据转换为 JSON 字符串并复制到剪贴板
            json_data = json.dumps(data_list, ensure_ascii=False, indent=2)
            QApplication.clipboard().setText(json_data)
        else:
            # 将数据转换为单行分隔符格式并复制到剪贴板
            if data_list:
                # 获取所有字段名
                fields = list(data_list[0].keys())
                # 生成 CSV 格式
                csv_lines = []
                # 添加表头
                csv_lines.append('\t'.join(fields))
                # 添加数据行
                for data in data_list:
                    values = [str(data.get(field, '')) for field in fields]
                    csv_lines.append('\t'.join(values))
                csv_data = '\n'.join(csv_lines)
                QApplication.clipboard().setText(csv_data)
        
        print(f"复制 {len(items)} 行，格式: {format_type}")

    def _on_copy_all_rows(self, format_type='json'):
        """
        复制所有行
        :param format_type: 复制格式，'json' 或 'csv'
        """
        if self._model and hasattr(self._model, '_all_data'):
            data = self._model._all_data
            # 实现复制逻辑，将所有数据保存到剪贴板
            import json
            all_data = []
            for item in data:
                if hasattr(item, 'model_dump'):
                    # Pydantic 模型，使用 mode='json' 确保枚举类型正确序列化
                    item_data = item.model_dump(mode='json')
                else:
                    # 普通模型
                    item_data = {}
                    for attr in dir(item):
                        if not attr.startswith('_') and not callable(getattr(item, attr)):
                            value = getattr(item, attr)
                            # 处理枚举类型
                            if hasattr(value, 'value'):
                                value = value.value
                            item_data[attr] = value
                all_data.append(item_data)
            
            if format_type == 'json':
                # 将数据转换为 JSON 字符串并复制到剪贴板
                json_data = json.dumps(all_data, ensure_ascii=False, indent=2)
                QApplication.clipboard().setText(json_data)
            else:
                # 将数据转换为单行分隔符格式并复制到剪贴板
                if all_data:
                    # 获取所有字段名
                    fields = list(all_data[0].keys())
                    # 生成 CSV 格式
                    csv_lines = []
                    # 添加表头
                    csv_lines.append('\t'.join(fields))
                    # 添加数据行
                    for item_data in all_data:
                        values = [str(item_data.get(field, '')) for field in fields]
                        csv_lines.append('\t'.join(values))
                    csv_data = '\n'.join(csv_lines)
                    QApplication.clipboard().setText(csv_data)
            
            print(f"复制所有行: {len(data)} 行，格式: {format_type}")

    def _on_paste_to_current_row(self):
        """
        粘贴到当前行
        """
        current_index = self.tableView.currentIndex()
        if not current_index.isValid():
            return
        row = current_index.row()
        # 实现粘贴逻辑，从剪贴板中获取数据并粘贴到当前行
        import json
        clipboard_data = QApplication.clipboard().text()
        try:
            data = json.loads(clipboard_data)
            if self._model and hasattr(self._model, '_all_data'):
                # 获取当前行的原始数据
                if hasattr(self._model, 'get_item'):
                    item = self._model.get_item(row)
                    # 检查data是否为列表（多行复制）
                    if isinstance(data, list) and len(data) > 0:
                        # 使用列表中的第一个元素
                        data = data[0]
                    # 更新数据
                    if hasattr(item, 'model_dump'):
                        # Pydantic 模型
                        if isinstance(data, dict):
                            for key, value in data.items():
                                if hasattr(item, key):
                                    # 处理枚举类型
                                    field_info = type(item).model_fields.get(key)
                                    if field_info and hasattr(field_info.annotation, '__members__'):
                                        # 枚举类型，将字符串转换为枚举值
                                        enum_class = field_info.annotation
                                        if value in enum_class.__members__:
                                            value = enum_class(value)
                                    setattr(item, key, value)
                    else:
                        # 普通模型
                        if isinstance(data, dict):
                            for key, value in data.items():
                                if hasattr(item, key):
                                    setattr(item, key, value)
                    # 刷新模型
                    self._model.beginResetModel()
                    self._model.endResetModel()
                    print(f"粘贴到当前行: {row}")
        except Exception as e:
            print(f"粘贴失败: {e}")

    def _on_paste_multiple_rows(self):
        """
        批量粘贴多行数据
        """
        current_index = self.tableView.currentIndex()
        if not current_index.isValid():
            return
        row = current_index.row()
        # 实现粘贴逻辑，从剪贴板中获取数据并批量粘贴
        import json
        clipboard_data = QApplication.clipboard().text()
        try:
            data = json.loads(clipboard_data)
            if self._model and hasattr(self._model, '_all_data'):
                # 检查data是否为列表（多行复制）
                if isinstance(data, list):
                    # 计算插入位置
                    if hasattr(self._model, 'current_page') and hasattr(self._model, '_page_size'):
                        page = self._model.current_page()
                        page_size = self._model._page_size
                        insert_pos = (page - 1) * page_size + row
                    else:
                        insert_pos = row
                    
                    # 确保插入位置在有效范围内
                    insert_pos = min(insert_pos, len(self._model._all_data))
                    
                    # 获取模型类
                    model_class = None
                    if hasattr(self._model, 'model_class'):
                        model_class = self._model.model_class
                    elif len(self._model._all_data) > 0:
                        model_class = type(self._model._all_data[0])
                    
                    if model_class:
                        # 批量插入数据
                        for i, item_data in enumerate(data):
                            if isinstance(item_data, dict):
                                # 创建新实例
                                if hasattr(model_class, 'model_fields'):
                                    # Pydantic 模型
                                    # 处理枚举类型
                                    for key, value in item_data.items():
                                        field_info = model_class.model_fields.get(key)
                                        if field_info and hasattr(field_info.annotation, '__members__'):
                                            # 枚举类型，将字符串转换为枚举值
                                            enum_class = field_info.annotation
                                            if value in enum_class.__members__:
                                                item_data[key] = enum_class(value)
                                    # 创建新实例
                                    new_item = model_class(**item_data)
                                else:
                                    # 普通模型
                                    new_item = model_class()
                                    for key, value in item_data.items():
                                        if hasattr(new_item, key):
                                            setattr(new_item, key, value)
                                
                                # 插入到模型中
                                self._model._all_data.insert(insert_pos + i, new_item)
                        
                        # 复制数据到filtered_data
                        self._model._filtered_data = self._model._all_data[:]
                        # 如果有排序，重新排序数据
                        if hasattr(self._model, '_sort_column') and self._model._sort_column >= 0:
                            self._model._sort_data()
                        # 刷新模型
                        self._model.beginResetModel()
                        self._model.endResetModel()
                        # 更新分页控件
                        self._update_page_controls()
                        print(f"批量粘贴 {len(data)} 行")
        except Exception as e:
            print(f"批量粘贴失败: {e}")

    def _on_add_row(self):
        """
        新增行
        """
        if self._model and hasattr(self._model, '_all_data'):
            # 根据模型类型创建新实例
            if hasattr(self._model, 'model_class'):
                # PydanticTableModel
                model_class = self._model.model_class
                # 创建一个空实例用于编辑
                # 为必填字段提供默认值
                default_data = {}
                for field_name, field_info in model_class.model_fields.items():
                    if field_info.default is not None:
                        default_data[field_name] = field_info.default
                    elif field_info.default_factory is not None:
                        default_data[field_name] = field_info.default_factory()
                    else:
                        # 为必填字段提供默认值
                        if field_info.annotation is int:
                            default_data[field_name] = 0
                        elif field_info.annotation is bool:
                            default_data[field_name] = False
                        elif field_info.annotation is str:
                            default_data[field_name] = ""
                        elif hasattr(field_info.annotation, '__members__'):  # 枚举类型
                            # 使用枚举的第一个值
                            enum_values = list(field_info.annotation.__members__.values())
                            if enum_values:
                                default_data[field_name] = enum_values[0]
                            else:
                                default_data[field_name] = None
                        else:
                            default_data[field_name] = None
                try:
                    # 直接创建一个字典，然后在对话框中编辑
                    # 这样可以避免 Pydantic 验证错误
                    # 显示编辑对话框
                    # 注意：这里我们需要创建一个临时对象，用于对话框显示
                    # 创建一个临时类，模拟Pydantic模型的结构
                    class TempItem:
                        def __init__(self, data, model_class):
                            self.__dict__ = data
                            # 存储原始模型类
                            self._original_model_class = model_class
                    
                    # 创建临时对象
                    temp_item = TempItem(default_data, model_class)
                    # 直接设置model_fields属性，而不是设置到类上
                    temp_item.model_fields = model_class.model_fields
                    # 显示编辑对话框
                    dialog = DynamicEditDialog(temp_item, self)
                    if dialog.exec() == QDialog.DialogCode.Accepted:
                        # 获取更新后的数据
                        updated_item = dialog.get_updated_item()
                        # 构建数据字典
                        data_dict = {}
                        for field_name in model_class.model_fields.keys():
                            if hasattr(updated_item, field_name):
                                value = getattr(updated_item, field_name)
                                # 避免PydanticUndefined值
                                if value == 'PydanticUndefined':
                                    data_dict[field_name] = default_data[field_name]
                                else:
                                    data_dict[field_name] = value
                            # 确保所有字段都有值
                            elif field_name in default_data:
                                data_dict[field_name] = default_data[field_name]
                        # 不自动重置 ID，使用用户输入的 ID
                        # if 'id' in data_dict:
                        #     data_dict['id'] = len(self._model._all_data) + 1
                        # 创建新实例
                        new_item = model_class(**data_dict)
                        # 添加新实例到模型
                        self._model._all_data.append(new_item)
                        # 复制数据到filtered_data
                        self._model._filtered_data = self._model._all_data[:]
                        # 如果有排序，重新排序数据
                        if hasattr(self._model, '_sort_column') and self._model._sort_column >= 0:
                            self._model._sort_data()
                        # 刷新模型
                        self._model.beginResetModel()
                        self._model.endResetModel()
                        # 更新分页控件
                        self._update_page_controls()
                        print("新增行")
                except Exception as e:
                    print(f"创建新实例失败: {e}")
                    return
            elif hasattr(self._model, '_all_data') and len(self._model._all_data) > 0:
                # 普通模型，复制最后一行的数据
                last_item = self._model._all_data[-1]
                if hasattr(last_item, 'model_dump'):
                    # Pydantic 模型
                    # 显示编辑对话框
                    dialog = DynamicEditDialog(last_item, self)
                    if dialog.exec() == QDialog.DialogCode.Accepted:
                        # 获取更新后的数据
                        new_item = dialog.get_updated_item()
                        # 重置 ID
                        if hasattr(new_item, 'id'):
                            new_item.id = len(self._model._all_data) + 1
                        # 添加新实例到模型
                        self._model._all_data.append(new_item)
                        # 复制数据到filtered_data
                        self._model._filtered_data = self._model._all_data[:]
                        # 如果有排序，重新排序数据
                        if hasattr(self._model, '_sort_column') and self._model._sort_column >= 0:
                            self._model._sort_data()
                        # 刷新模型
                        self._model.beginResetModel()
                        self._model.endResetModel()
                        # 更新分页控件
                        self._update_page_controls()
                        print("新增行")
                else:
                    # 普通模型
                    # 显示编辑对话框
                    dialog = DynamicEditDialog(last_item, self)
                    if dialog.exec() == QDialog.DialogCode.Accepted:
                        # 获取更新后的数据
                        new_item = dialog.get_updated_item()
                        # 重置 ID
                        if hasattr(new_item, 'id'):
                            new_item.id = len(self._model._all_data) + 1
                        # 添加新实例到模型
                        self._model._all_data.append(new_item)
                        # 复制数据到filtered_data
                        self._model._filtered_data = self._model._all_data[:]
                        # 如果有排序，重新排序数据
                        if hasattr(self._model, '_sort_column') and self._model._sort_column >= 0:
                            self._model._sort_data()
                        # 刷新模型
                        self._model.beginResetModel()
                        self._model.endResetModel()
                        # 更新分页控件
                        self._update_page_controls()
                        print("新增行")
            else:
                # 无法创建新实例
                print("无法创建新行")
                return

    def _on_insert_row(self):
        """
        插入行
        """
        current_index = self.tableView.currentIndex()
        row = current_index.row() if current_index.isValid() else 0
        if self._model and hasattr(self._model, '_all_data'):
            # 根据模型类型创建新实例
            if hasattr(self._model, 'model_class'):
                # PydanticTableModel
                model_class = self._model.model_class
                # 创建一个空实例用于编辑
                # 为必填字段提供默认值
                default_data = {}
                for field_name, field_info in model_class.model_fields.items():
                    if field_info.default is not None:
                        default_data[field_name] = field_info.default
                    elif field_info.default_factory is not None:
                        default_data[field_name] = field_info.default_factory()
                    else:
                        # 为必填字段提供默认值
                        if field_info.annotation is int:
                            default_data[field_name] = 0
                        elif field_info.annotation is bool:
                            default_data[field_name] = False
                        elif field_info.annotation is str:
                            default_data[field_name] = ""
                        elif hasattr(field_info.annotation, '__members__'):  # 枚举类型
                            # 使用枚举的第一个值
                            enum_values = list(field_info.annotation.__members__.values())
                            if enum_values:
                                default_data[field_name] = enum_values[0]
                            else:
                                default_data[field_name] = None
                        else:
                            default_data[field_name] = None
                try:
                    # 直接创建一个字典，然后在对话框中编辑
                    # 这样可以避免 Pydantic 验证错误
                    # 显示编辑对话框
                    # 注意：这里我们需要创建一个临时对象，用于对话框显示
                    # 创建一个临时类，模拟Pydantic模型的结构
                    class TempItem:
                        def __init__(self, data, model_class):
                            self.__dict__ = data
                            # 存储原始模型类
                            self._original_model_class = model_class
                    
                    # 创建临时对象
                    temp_item = TempItem(default_data, model_class)
                    # 直接设置model_fields属性，而不是设置到类上
                    temp_item.model_fields = model_class.model_fields
                    # 显示编辑对话框
                    dialog = DynamicEditDialog(temp_item, self)
                    if dialog.exec() == QDialog.DialogCode.Accepted:
                        # 获取更新后的数据
                        updated_item = dialog.get_updated_item()
                        # 构建数据字典
                        data_dict = {}
                        for field_name in model_class.model_fields.keys():
                            if hasattr(updated_item, field_name):
                                value = getattr(updated_item, field_name)
                                # 避免PydanticUndefined值
                                if value == 'PydanticUndefined':
                                    data_dict[field_name] = default_data[field_name]
                                else:
                                    data_dict[field_name] = value
                            # 确保所有字段都有值
                            elif field_name in default_data:
                                data_dict[field_name] = default_data[field_name]
                        # 不自动重置 ID，使用用户输入的 ID
                        # if 'id' in data_dict:
                        #     data_dict['id'] = len(self._model._all_data) + 1
                        # 创建新实例
                        new_item = model_class(**data_dict)
                        # 计算插入位置
                        # 注意：这里需要考虑当前页的偏移
                        if hasattr(self._model, 'current_page') and hasattr(self._model, 'page_size'):
                            page = self._model.current_page()
                            page_size = self._model._page_size
                            insert_pos = (page - 1) * page_size + row
                        else:
                            insert_pos = row
                        
                        # 确保插入位置在有效范围内
                        insert_pos = min(insert_pos, len(self._model._all_data))
                        
                        # 插入新实例到模型
                        self._model._all_data.insert(insert_pos, new_item)
                        # 复制数据到filtered_data
                        self._model._filtered_data = self._model._all_data[:]
                        # 如果有排序，重新排序数据
                        if hasattr(self._model, '_sort_column') and self._model._sort_column >= 0:
                            self._model._sort_data()
                        # 刷新模型
                        self._model.beginResetModel()
                        self._model.endResetModel()
                        # 更新分页控件
                        self._update_page_controls()
                        print(f"在第 {row} 行前插入行")
                except Exception as e:
                    print(f"创建新实例失败: {e}")
                    return
            elif hasattr(self._model, '_all_data') and len(self._model._all_data) > 0:
                # 普通模型，复制当前行或最后一行的数据
                if current_index.isValid() and hasattr(self._model, 'get_item'):
                    # 复制当前行
                    item = self._model.get_item(row)
                else:
                    # 复制最后一行
                    item = self._model._all_data[-1]
                
                if hasattr(item, 'model_dump'):
                    # Pydantic 模型
                    # 显示编辑对话框
                    dialog = DynamicEditDialog(item, self)
                    if dialog.exec() == QDialog.DialogCode.Accepted:
                        # 获取更新后的数据
                        new_item = dialog.get_updated_item()
                        # 重置 ID
                        if hasattr(new_item, 'id'):
                            new_item.id = len(self._model._all_data) + 1
                        # 计算插入位置
                        # 注意：这里需要考虑当前页的偏移
                        if hasattr(self._model, 'current_page') and hasattr(self._model, 'page_size'):
                            page = self._model.current_page()
                            page_size = self._model._page_size
                            insert_pos = (page - 1) * page_size + row
                        else:
                            insert_pos = row
                        
                        # 确保插入位置在有效范围内
                        insert_pos = min(insert_pos, len(self._model._all_data))
                        
                        # 插入新实例到模型
                        self._model._all_data.insert(insert_pos, new_item)
                        # 复制数据到filtered_data
                        self._model._filtered_data = self._model._all_data[:]
                        # 如果有排序，重新排序数据
                        if hasattr(self._model, '_sort_column') and self._model._sort_column >= 0:
                            self._model._sort_data()
                        # 刷新模型
                        self._model.beginResetModel()
                        self._model.endResetModel()
                        # 更新分页控件
                        self._update_page_controls()
                        print(f"在第 {row} 行前插入行")
                else:
                    # 普通模型
                    # 显示编辑对话框
                    dialog = DynamicEditDialog(item, self)
                    if dialog.exec() == QDialog.DialogCode.Accepted:
                        # 获取更新后的数据
                        new_item = dialog.get_updated_item()
                        # 重置 ID
                        if hasattr(new_item, 'id'):
                            new_item.id = len(self._model._all_data) + 1
                        # 计算插入位置
                        # 注意：这里需要考虑当前页的偏移
                        if hasattr(self._model, 'current_page') and hasattr(self._model, '_page_size'):
                            page = self._model.current_page()
                            page_size = self._model._page_size
                            insert_pos = (page - 1) * page_size + row
                        else:
                            insert_pos = row
                        
                        # 确保插入位置在有效范围内
                        insert_pos = min(insert_pos, len(self._model._all_data))
                        
                        # 插入新实例到模型
                        self._model._all_data.insert(insert_pos, new_item)
                        # 复制数据到filtered_data
                        self._model._filtered_data = self._model._all_data[:]
                        # 如果有排序，重新排序数据
                        if hasattr(self._model, '_sort_column') and self._model._sort_column >= 0:
                            self._model._sort_data()
                        # 刷新模型
                        self._model.beginResetModel()
                        self._model.endResetModel()
                        # 更新分页控件
                        self._update_page_controls()
                        print(f"在第 {row} 行前插入行")
            else:
                # 无法创建新实例
                print("无法创建新行")
                return

    def _on_delete_current_row(self):
        """
        删除当前行或选中的多行
        """
        selected_indexes = self.tableView.selectionModel().selectedRows()
        if not selected_indexes:
            return
        
        # 收集所有要删除的行索引（考虑分页偏移）
        delete_positions = []
        for index in selected_indexes:
            row = index.row()
            if self._model and hasattr(self._model, '_all_data'):
                try:
                    # 计算删除位置，考虑当前页的偏移
                    if hasattr(self._model, 'current_page') and hasattr(self._model, '_page_size'):
                        page = self._model.current_page()
                        page_size = self._model._page_size
                        delete_pos = (page - 1) * page_size + row
                    else:
                        # 没有分页，直接使用行索引
                        delete_pos = row
                    
                    # 确保删除位置在有效范围内
                    if 0 <= delete_pos < len(self._model._all_data):
                        delete_positions.append(delete_pos)
                except Exception as e:
                    print(f"计算删除位置失败: {e}")
        
        # 按降序排序，避免删除时索引变化
        delete_positions.sort(reverse=True)
        
        # 执行删除操作
        for pos in delete_positions:
            if 0 <= pos < len(self._model._all_data):
                self._model._all_data.pop(pos)
        
        if delete_positions:
            # 复制数据到filtered_data
            self._model._filtered_data = self._model._all_data[:]
            # 如果有排序，重新排序数据
            if hasattr(self._model, '_sort_column') and self._model._sort_column >= 0:
                self._model._sort_data()
            # 刷新模型
            self._model.beginResetModel()
            self._model.endResetModel()
            # 更新分页控件
            self._update_page_controls()
            print(f"删除 {len(delete_positions)} 行")







if __name__ == "__main__":
    import app.common.resource
    import numpy as np
    from numpy.random import choice
    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            setTheme(Theme.AUTO)

            self.setWindowTitle("EnhancedTableWidget with Pydantic & qfluentwidgets")
            self.resize(800, 600)

            # 准备测试数据
            # 生成项目测试数据
            documents = []
            for i in range(1, 51):
                doc = Document(
                    id=i,
                    enable=choice([True, False]),  # 随机使能状态
                    core=choice([EnumCore.Core0, EnumCore.Core1, EnumCore.Core2, EnumCore.Core3]),  # 随机内核分配
                    doc_number=f"DOC{np.random.randint(0, 51):04d}",  # 格式化为 4 位数字
                    name=choice(["项目计划", "需求文档", "设计说明书", "测试报告", "用户手册"]),
                    description=f"这是第{i}个文档的描述信息，可能包含一些详细内容。",
                    tags=choice(["重要", "普通", "归档", "进行中"]),
                    created_at="2023-01-01"
                )
                documents.append(doc)

            # 测试1：
            # self.model = DocumentTableModel(documents, page_size=5)
            # self.tableWidget = EnhancedTableWidget(model=self.model)
            # self.setCentralWidget(self.tableWidget)

            # 测试2： 自动显示 Document 的所有字段
            self.model = PydanticTableModel(Document, documents, page_size=15)
            self.tableWidget = EnhancedTableWidget(model=self.model)
            self.setCentralWidget(self.tableWidget)

            # 测试3： 只显示部分字段，并自定义标题
            # self.model = PydanticTableModel(
            #     Document, documents, page_size=10,
            #     include_fields=['doc_number', 'name', 'enable', 'core'],
            #     field_titles={'enable': '启用', 'core': '内核'}
            # )
            # self.tableWidget = EnhancedTableWidget(model=self.model)
            # self.setCentralWidget(self.tableWidget)

            # 测试4： 非 Pydantic 模型
            # 生成产品测试数据
            # products = []
            # categories = ["电子产品", "服装", "食品", "图书", "家居"]
            # for i in range(1, 51):
            #     product = Product(
            #         id=i,
            #         name=f"产品{i}",
            #         price=round(np.random.uniform(10, 1000), 2),
            #         stock=np.random.randint(0, 1000),
            #         category=choice(categories)
            #     )
            #     products.append(product)
            #
            # # 创建产品表格模型
            # self.model = ProductTableModel(products, page_size=10)
            # self.tableWidget = EnhancedTableWidget(model=self.model)
            # self.setCentralWidget(self.tableWidget)
            # print("\n测试非 Pydantic 模型排序功能")

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())