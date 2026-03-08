#!/usr/bin/env python3
"""
简单插件系统测试
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

try:
    # 测试导入插件系统模块
    from app.plugins import PluginBase, PluginInfo, PluginCategory, PluginManager
    
    print("✓ 插件系统模块导入成功")
    
    # 测试创建插件信息
    info = PluginInfo(
        name="Test Plugin",
        version="1.0.0",
        description="测试插件",
        author="Tester",
        category=PluginCategory.UTILITIES
    )
    print("✓ PluginInfo 创建成功")
    print(f"  插件名称: {info.name}")
    print(f"  分类: {info.category.value}")
    
    # 测试插件管理器
    manager = PluginManager()
    print("✓ PluginManager 创建成功")
    
    # 测试获取已注册插件（应该为空）
    all_plugins = manager.registry.get_all_plugins()
    print(f"✓ 当前注册插件数量: {len(all_plugins)}")
    
    print("\n🎉 插件系统基础功能测试通过!")
    
except ImportError as e:
    print(f"❌ 导入错误: {e}")
except Exception as e:
    print(f"❌ 其他错误: {e}")
    import traceback
    traceback.print_exc()