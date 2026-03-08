#!/usr/bin/env python3
"""
测试工具界面修复
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

try:
    print("正在测试工具界面导入...")
    
    # 测试导入
    from app.view.tool_interface import ToolsInterface
    print("✓ ToolsInterface 导入成功")
    
    # 测试创建实例
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    
    tool_interface = ToolsInterface()
    print("✓ ToolsInterface 实例创建成功")
    
    print("\n🎉 修复验证通过！工具界面可以正常工作")
    
except Exception as e:
    print(f"❌ 出现错误: {e}")
    import traceback
    traceback.print_exc()
finally:
    # 清理Qt应用
    if 'app' in locals():
        app.quit()