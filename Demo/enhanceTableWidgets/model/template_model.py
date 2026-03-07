#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
模板模型

该模块包含了模板数据模型类，用于存储和管理模板相关数据。
"""

from pydantic import BaseModel, Field
from typing import Optional


class TemplateModel(BaseModel):
    """模板模型类"""
    template_number: str = Field(..., description="模板编号")
    template_category: str = Field(..., description="模板分类")
    template_name: str = Field(..., description="模板名称")
    created_at: str = Field(..., description="创建时间")
    template_description: str = Field("", description="模板描述")
    updated_at: Optional[str] = Field(None, description="更新时间")

    class Config:
        from_attributes = True  # 允许从ORM对象创建
