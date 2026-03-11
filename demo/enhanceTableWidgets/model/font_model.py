#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
字体模型

该模块包含了字体数据模型类，用于存储和管理字体相关数据。
"""

from PySide6.QtGui import QFont, QColor
from pydantic import BaseModel, Field
from typing import Optional


class FontModel(BaseModel):
    """字体模型类"""
    font_id: int = Field(..., description="字体ID")
    font_style_name: str = Field(..., description="样式名称")
    font_family: str = Field(..., description="字体名称")
    font_size: int = Field(..., ge=1, description="字体大小")
    font_color: str = Field(..., description="字体颜色")
    font_bold: bool = Field(False, description="是否加粗")
    font_italic: bool = Field(False, description="是否斜体")
    font_underline: bool = Field(False, description="是否下划线")
    created_at: Optional[str] = Field(None, description="创建时间")
    updated_at: Optional[str] = Field(None, description="更新时间")

    def to_QFont(self) -> QFont:
        """
        转换为QFont对象
        :return: QFont对象
        """
        font = QFont(self.font_family, self.font_size)
        font.setBold(self.font_bold)
        font.setItalic(self.font_italic)
        font.setUnderline(self.font_underline)
        return font

    def to_QColor(self) -> QColor:
        """
        转换为QColor对象
        :return: QColor对象
        """
        return QColor(self.font_color)

    class Config:
        from_attributes = True  # 允许从ORM对象创建
