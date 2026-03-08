#!/usr/bin/env python3
"""
批量修改 *_white.svg 文件的颜色为白色 (#ffffff)
直接修改文件内容
"""

import os
import sys
from pathlib import Path


def fix_white_svgs(icons_dir: str):
    """将所有 *_white.svg 文件的颜色改为白色"""
    icons_path = Path(icons_dir)
    white_svgs = sorted(icons_path.glob("*_white.svg"))
    
    fixed_count = 0
    skipped_count = 0
    
    for svg_file in white_svgs:
        try:
            content = svg_file.read_text(encoding='utf-8')
            
            # 检查是否需要修改
            if '#2c2c2c' not in content and '#000000' not in content:
                skipped_count += 1
                continue
            
            # 替换颜色为白色
            new_content = content.replace('#2c2c2c', '#ffffff')
            new_content = new_content.replace('#000000', '#ffffff')
            
            svg_file.write_text(new_content, encoding='utf-8')
            print(f"Fixed: {svg_file.name}")
            fixed_count += 1
            
        except Exception as e:
            print(f"Error processing {svg_file.name}: {e}", file=sys.stderr)
    
    print(f"\n{'='*50}")
    print(f"Total fixed: {fixed_count} files")
    print(f"Total skipped (already white): {skipped_count} files")
    print(f"Total processed: {len(white_svgs)} files")


if __name__ == "__main__":
    icons_dir = [
        r".\app\resource\images\icons",
        r".\app\resource\images\fluentIcon"
    ]
    for _ in icons_dir:
        fix_white_svgs(_)
