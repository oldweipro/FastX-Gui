#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
项目模型

该模块包含了项目数据模型类，用于存储和管理项目相关数据。
"""

from pydantic import BaseModel, Field


class ProjectModel(BaseModel):
    """项目模型类"""
    project_number: str = Field(..., description="项目编号")
    project_name: str = Field(..., description="项目名称")
    project_description: str = Field(..., description="项目描述")
    project_tags: str = Field(..., description="项目标签")
    prepared_by: str = Field(..., description="编制人")
    project_path: str = Field(..., description="项目路径")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")

    class Config:
        from_attributes = True  # 允许从ORM对象创建
