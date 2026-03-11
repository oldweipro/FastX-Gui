#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
文档模型

该模块包含了文档数据模型类，用于存储和管理文档相关数据。
"""

from pydantic import BaseModel, Field


class DocumentModel(BaseModel):
    """文档模型类"""
    project_id: str = Field(..., description="项目ID")
    template_id: str = Field(..., description="模板ID")
    document_number: str = Field(..., description="文档编号")
    document_name: str = Field(..., description="文档名称")
    document_description: str = Field(..., description="文档描述")
    document_tags: str = Field(..., description="文档标签")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")

    class Config:
        from_attributes = True  # 允许从ORM对象创建
