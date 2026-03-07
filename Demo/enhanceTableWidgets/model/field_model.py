#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
字段模型

该模块包含了字段数据模型类，用于存储和管理字段相关数据。
"""

from enum import Enum
from pydantic import BaseModel, Field


class FieldFillMode(Enum):
    """字段填充模式枚举"""
    MATCH_FILL_RIGHT = "MATCH_FILL_RIGHT"
    # 可以根据需要添加其他填充模式


class FieldModel(BaseModel):
    """字段模型类"""
    field_name: str = Field(..., description="字段名")
    field_value: str = Field(..., description="字段值")
    fill_mode: FieldFillMode = Field(..., description="填充方式")
    table_num: int = Field(..., description="表格序号")
    table_row: int = Field(..., description="表格行号")
    table_col: int = Field(..., description="表格列号")
    font_id: int = Field(..., description="字体ID")
    field_order: int = Field(0, description="字段排序序号")

    class Config:
        from_attributes = True  # 允许从ORM对象创建
