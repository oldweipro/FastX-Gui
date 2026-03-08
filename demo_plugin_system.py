#!/usr/bin/env python3
"""
插件系统演示脚本
展示如何使用插件系统加载和管理插件
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.plugins import PluginManager, PluginCategory
from loguru import logger


def demo_plugin_system():
    """演示插件系统基本功能"""
    
    print("=" * 50)
    print("FastX-Gui 插件系统演示")
    print("=" * 50)
    
    # 1. 创建插件管理器
    print("\n1. 初始化插件管理器...")
    plugin_manager = PluginManager()
    
    # 2. 加载插件
    print("\n2. 加载插件...")
    loaded_count = plugin_manager.load_plugins()
    print(f"   成功加载 {loaded_count} 个插件")
    
    # 3. 显示所有已加载的插件
    print("\n3. 已加载的插件:")
    loaded_plugins = plugin_manager.get_all_loaded_plugins()
    if loaded_plugins:
        for plugin_name in loaded_plugins:
            plugin_info = plugin_manager.get_plugin_info(plugin_name)
            if plugin_info:
                print(f"   - {plugin_info.name} (v{plugin_info.version})")
                print(f"     分类: {plugin_info.category.value}")
                print(f"     描述: {plugin_info.description}")
    else:
        print("   暂无已加载的插件")
    
    # 4. 按分类显示插件
    print("\n4. 按分类显示插件:")
    categories = plugin_manager.registry.get_all_categories()
    for category in categories:
        plugins_in_category = plugin_manager.get_plugins_by_category(category)
        if plugins_in_category:
            print(f"   {category.value.upper()} ({len(plugins_in_category)}个):")
            for plugin_name in plugins_in_category:
                plugin_info = plugin_manager.get_plugin_info(plugin_name)
                if plugin_info:
                    print(f"     - {plugin_info.name}")
    
    # 5. 演示插件配置管理
    print("\n5. 插件配置管理演示:")
    if loaded_plugins:
        sample_plugin = loaded_plugins[0]
        plugin = plugin_manager.get_plugin(sample_plugin)
        if plugin:
            print(f"   插件: {plugin.name}")
            
            # 获取配置
            config = plugin.get_config()
            print(f"   当前配置: {config}")
            
            # 修改配置
            new_config = {"demo_setting": "demo_value"}
            plugin.set_config(new_config)
            print(f"   更新后配置: {plugin.get_config()}")
    
    # 6. 清理资源
    print("\n6. 清理插件资源...")
    plugin_manager.shutdown()
    
    print("\n" + "=" * 50)
    print("演示完成!")
    print("=" * 50)


def demo_plugin_categories():
    """演示插件分类功能"""
    
    print("\n" + "=" * 50)
    print("插件分类演示")
    print("=" * 50)
    
    # 显示所有支持的分类
    print("\n支持的插件分类:")
    for category in PluginCategory:
        descriptions = {
            PluginCategory.DIAGNOSTIC: "诊断工具 - 用于系统诊断和故障排查",
            PluginCategory.COMMUNICATION: "通信工具 - 网络和通信相关工具",
            PluginCategory.SERIAL: "串口工具 - 串行通信调试工具",
            PluginCategory.UTILITIES: "实用工具 - 通用辅助工具",
            PluginCategory.CUSTOM: "自定义工具 - 用户自定义工具"
        }
        desc = descriptions.get(category, "未定义分类")
        print(f"  {category.value:15} - {desc}")


if __name__ == "__main__":
    try:
        # 配置日志
        logger.remove()
        logger.add(sys.stderr, level="INFO")
        
        # 运行演示
        demo_plugin_system()
        demo_plugin_categories()
        
    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
    except Exception as e:
        print(f"\n运行出错: {e}")
        import traceback
        traceback.print_exc()