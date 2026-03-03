# -*- coding: utf-8 -*-
from typing import Any, List

from PySide6.QtCore import QModelIndex, Qt

from app.model.template_model import TemplateModel
from app.table_model.base_table_model import BaseTableModel


class TemplateTableModel(BaseTableModel):
    """模板表格模型"""

    def __init__(
        self,
        data: List[TemplateModel] = None,
        parent=None,
        page_size: int = 10,
    ):
        """
        初始化TemplateModel表格模型
        :param data: TemplateModel列表
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
        return 7  # 序号, template_number, template_category, template_name, template_description, created_at, updated_at

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
        item: TemplateModel = self._data[start_index + index.row()]

        if role == Qt.DisplayRole:
            if index.column() == 0:
                # 显示序号 (当前页起始序号 + 行号)
                start_index = (self._current_page - 1) * self._page_size
                return start_index + index.row() + 1
            elif index.column() == 1:
                return item.template_number
            elif index.column() == 2:
                return item.template_category
            elif index.column() == 3:
                return item.template_name
            elif index.column() == 4:
                return item.template_description
            elif index.column() == 5:
                return item.created_at
            elif index.column() == 6:
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
            "模板编号",
            "模板分类",
            "模板名称",
            "模板描述",
            "创建时间",
            "更新时间",
        ]

    def _sort_data(self):
        """
        对模板数据进行排序
        """
        self._data.sort(key=lambda x: x.template_number)
