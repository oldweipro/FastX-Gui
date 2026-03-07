# -*- coding: utf-8 -*-
from typing import Any, List

from PySide6.QtCore import QModelIndex, Qt

from ..model.font_model import FontModel
from .base_table_model import BaseTableModel


class FontTableModel(BaseTableModel):
    """字体表格模型"""

    def __init__(
        self,
        data: List[FontModel] = None,
        parent=None,
        page_size: int = 10,
    ):
        """
        初始化FontModel表格模型
        :param data: FontModel列表
        :param parent: 父对象
        :param page_size: 每页显示的记录数
        """
        super().__init__(data, parent, page_size)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """
        返回表格的列数
        :param parent: 父索引
        :return: 列数
        """
        return 10  # 序号, font_style_name, font_family, font_size, font_color, font_bold, font_italic, font_underline, created_at, updated_at

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
        item: FontModel = self._data[start_index + index.row()]

        if role == Qt.DisplayRole:
            if index.column() == 0:
                # 显示序号 (当前页起始序号 + 行号)
                start_index = (self._current_page - 1) * self._page_size
                return start_index + index.row() + 1
            elif index.column() == 1:
                return item.font_style_name
            elif index.column() == 2:
                return item.font_family
            elif index.column() == 3:
                return item.font_size
            elif index.column() == 4:
                return item.font_color
            elif index.column() == 5:
                return "是" if item.font_bold else "否"
            elif index.column() == 6:
                return "是" if item.font_italic else "否"
            elif index.column() == 7:
                return "是" if item.font_underline else "否"
            elif index.column() == 8:
                return item.created_at
            elif index.column() == 9:
                return item.updated_at
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
            "样式名称",
            "字体名称",
            "字体大小",
            "字体颜色",
            "加粗",
            "斜体",
            "下划线",
            "创建时间",
            "更新时间",
        ]

    def _sort_data(self):
        """
        对字体数据进行排序
        """
        self._data.sort(key=lambda x: x.font_id if x.font_id else 0)
