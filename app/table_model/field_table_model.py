# -*- coding: utf-8 -*-
from typing import Any, List

from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtGui import QColor, QFont

from app.model import FieldModel, FontModel
from app.table_model import BaseTableModel


class FieldTableModel(BaseTableModel):
    """字段表格模型"""

    def __init__(
        self, data: List[FieldModel] = None, parent=None, page_size: int = 10
    ):
        """
        初始化FieldModel表格模型
        :param data: FieldModel列表
        :param parent: 父对象
        :param page_size: 每页显示的记录数
        """
        super().__init__(data, parent, page_size)
        # 先按字段名排序，再按field_order排序
        if self._data:
            self._data.sort(key=lambda x: x.field_name)
            self._data.sort(key=lambda x: x.field_order)

        # 模拟字体映射
        self._font_map: dict[int, FontModel] = {}
        # 创建一个默认字体
        default_font = FontModel(
            font_id=1,
            font_style_name="默认字体",
            font_family="SimHei",
            font_size=12,
            font_color="#000000",
            font_bold=False,
            font_italic=False,
            font_underline=False
        )
        self._font_map[1] = default_font

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """
        返回表格的列数
        :param parent: 父索引
        :return: 列数
        """
        return 7  # field_order, field_name, field_value, fill_mode, font_id, font_size, table_position

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        """
        返回指定索引的数据
        :param index: 数据索引
        :param role: 数据角色
        :return: 数据
        """
        if not index.isValid() or index.row() >= len(self._data):
            return None

        # 获取当前页的数据
        start_index = (self._current_page - 1) * self._page_size
        item: FieldModel = self._data[start_index + index.row()]
        font = self._font_map.get(item.font_id)

        if role == Qt.DisplayRole:
            if index.column() == 0:
                # 显示排序序号
                return item.field_order
            elif index.column() == 1:
                return item.field_name
            elif index.column() == 2:
                # 返回字段值的预览（前几个值）
                if item.field_value and isinstance(item.field_value, str):
                    values = item.field_value.split(",")
                    preview = ",".join(values[:3])
                    if len(values) > 3:
                        preview += "..."
                    return preview
                else:
                    return str(item.field_value)
            elif index.column() == 3:
                return item.fill_mode.value
            elif index.column() == 4:
                # 显示示例字体
                return "中文Aa"
            elif index.column() == 5:
                # 显示字号

                if font:
                    return font.font_size
                else:
                    return "未知字号"
            elif index.column() == 6:
                # 显示表格信息 (表格序号:行序号,列序号)
                return f"表 {item.table_num} - 行 {item.table_row} - 列 {item.table_col}"

        elif role == Qt.FontRole:
            if index.column() == 4:
                # 应用默认字体
                if font:
                    return font.to_QFont()
                else:
                    return QFont()
        elif role == Qt.ForegroundRole:
            if index.column() == 4:
                # 设置字体列的文本颜色
                if font:
                    return font.to_QColor()
                else:
                    return QColor(Qt.black)

        elif role == Qt.TextAlignmentRole:
            # 居中对齐所有内容
            return Qt.AlignCenter

        return None

    def _get_header_labels(self) -> List[str]:
        """
        获取表头标签列表
        :return: 表头标签列表
        """
        return [
            "序号",
            "字段名",
            "字段值",
            "填充方式",
            "字体预览",
            "字体大小",
            "表格位置",
        ]

    def _sort_data(self):
        """
        对字段数据进行排序
        """
        # 先按字段名排序，再按field_order排序
        self._data.sort(key=lambda x: x.field_name)
        self._data.sort(key=lambda x: x.field_order)
