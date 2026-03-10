# -*- coding: utf-8 -*-
from typing import Any, List

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt


class BaseTableModel(QAbstractTableModel):
    """所有表格模型的基类"""

    def __init__(self, data=None, parent=None, page_size: int = 10):
        """
        初始化基础表格模型
        :param data: 数据列表
        :param parent: 父对象
        :param page_size: 每页显示的记录数
        """
        super().__init__(parent)
        self._data = data if data is not None else []
        self._page_size = page_size
        self._current_page = 1

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """
        返回表格的行数
        :param parent: 父索引
        :return: 行数
        """
        # 返回当前页的记录数
        start_index = (self._current_page - 1) * self._page_size
        end_index = min(start_index + self._page_size, len(self._data))
        return end_index - start_index

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """
        返回表格的列数（抽象方法，需在子类中实现）
        :param parent: 父索引
        :return: 列数
        """
        pass

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        """
        返回指定索引的数据（抽象方法，需在子类中实现）
        :param index: 数据索引
        :param role: 数据角色
        :return: 数据
        """
        pass

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.DisplayRole,
    ) -> Any:
        """
        返回表头数据
        :param section: 部分索引
        :param orientation: 方向
        :param role: 数据角色
        :return: 表头数据
        """
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            # 优先使用自定义表头
            if (
                hasattr(self, "_custom_headers")
                and section < len(self._custom_headers)
                and self._custom_headers[section]
            ):
                return self._custom_headers[section]
            headers = self._get_header_labels()
            if headers and section < len(headers):
                return headers[section]
        elif role == Qt.TextAlignmentRole and orientation == Qt.Horizontal:
            # 居中对齐表头
            return Qt.AlignCenter
        return None

    def _get_header_labels(self) -> List[str]:
        """
        获取表头标签列表（抽象方法，需在子类中实现）
        :return: 表头标签列表
        """
        pass

    def setHeaderData(
        self,
        section: int,
        orientation: Qt.Orientation,
        value: Any,
        role: int = Qt.EditRole,
    ) -> bool:
        """
        设置表头数据
        :param section: 部分索引
        :param orientation: 方向
        :param value: 新的表头值
        :param role: 数据角色
        :return: 是否设置成功
        """
        if role == Qt.EditRole and orientation == Qt.Horizontal:
            if not hasattr(self, "_custom_headers"):
                self._custom_headers = []
            if section >= len(self._custom_headers):
                self._custom_headers.extend(
                    [""] * (section - len(self._custom_headers) + 1)
                )
            self._custom_headers[section] = value
            self.headerDataChanged.emit(orientation, section, section)
            return True
        return False

    def data_list(self) -> List:
        """
        获取所有数据
        :return: 数据列表
        """
        return self._data

    def set_data(self, data: list = None):
        """
        设置数据列表
        :param data: 数据列表
        """
        self.beginResetModel()
        self._data = data if data is not None else []
        self._current_page = 1
        self.endResetModel()

    def current_page(self) -> int:
        """
        获取当前页码
        :return: 当前页码
        """
        return self._current_page

    def set_current_page(self, page: int):
        """
        设置当前页码
        :param page: 页码
        """
        if 1 <= page <= self.page_count():
            self.beginResetModel()
            self._current_page = page
            self.endResetModel()

    def page_size(self) -> int:
        """
        获取每页记录数
        :return: 每页记录数
        """
        return self._page_size

    def page_count(self) -> int:
        """
        获取总页数
        :return: 总页数
        """
        if len(self._data) == 0:
            return 1
        return (len(self._data) + self._page_size - 1) // self._page_size

    def set_page_size(self, size: int):
        """
        设置每页记录数
        :param size: 每页记录数
        """
        if size > 0:
            self.beginResetModel()
            self._page_size = size
            self._current_page = 1
            self.endResetModel()

    def add_item(self, item):
        """
        添加项目
        :param item: 要添加的项目
        """
        self.beginInsertRows(QModelIndex(), len(self._data), len(self._data))
        self._data.append(item)
        self.endInsertRows()

        # 按编号排序
        self._sort_data()

        # 通知视图模型已重置
        self.beginResetModel()
        self.endResetModel()

        # 计算新添加项目的页码和行号
        index = self._data.index(item)
        page = index // self._page_size + 1
        row = index % self._page_size

        # 跳转到新添加的项目
        self.set_current_page(page)

        return row  # 返回行号，便于在视图中选中新增行

    def remove_item(self, row: int):
        """
        移除项目
        :param row: 要移除的项目行索引
        """
        if 0 <= row < len(self._data):
            self.beginRemoveRows(QModelIndex(), row, row)
            self._data.pop(row)
            self.endRemoveRows()

        # 按编号排序
        self._sort_data()

        self.beginResetModel()
        self.endResetModel()

    def update_item(self, row: int, item):
        """
        更新项目
        :param row: 要更新的项目行索引
        :param item: 新的项目数据
        """
        if 0 <= row < len(self._data):
            self._data[row] = item
            self.dataChanged.emit(
                self.index(row, 0), self.index(row, self.columnCount() - 1)
            )

        # 按编号排序
        self._sort_data()

    def get_page_info(self) -> str:
        """
        获取分页信息
        :return: 分页信息字符串 (当前页/总页数)
        """
        return f"{self._current_page}/{self.page_count()}"
