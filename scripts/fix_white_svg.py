#!/usr/bin/env python3
"""
批量修改 *_white.svg 文件的颜色为白色 (#ffffff)
"""

import os
import re
from pathlib import Path


def fix_white_svgs(icons_dir: str):
    """将所有 *_white.svg 文件的颜色改为白色"""
    icons_path = Path(icons_dir)
    white_svgs = list(icons_path.glob("*_white.svg"))
    
    fixed_count = 0
    for svg_file in white_svgs:
        content = svg_file.read_text(encoding='utf-8')
        
        # 检查是否包含非白色颜色
        if '#2c2c2c' in content or '#000000' in content or 'fill="black"' in content:
            # 替换颜色为白色
            new_content = content.replace('#2c2c2c', '#ffffff')
            new_content = new_content.replace('#000000', '#ffffff')
            new_content = new_content.replace('fill="black"', 'fill="#ffffff"')
            new_content = new_content.replace("fill='black'", 'fill="#ffffff"')
            
            svg_file.write_text(new_content, encoding='utf-8')
            print(f"Fixed: {svg_file.name}")
            fixed_count += 1
    
    print(f"\nTotal fixed: {fixed_count} files")


if __name__ == "__main__":
    icons_dir = r"D:\Github\FastX-Gui\app\resource\images\icons"
    fix_white_svgs(icons_dir)
