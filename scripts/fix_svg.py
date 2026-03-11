#!/usr/bin/env python3
"""
批量修改 *_white.svg 文件的颜色为白色 (#ffffff)
直接修改文件内容

用法:
    uv run fix-svg
"""

import os
import sys
from pathlib import Path


def get_project_root() -> Path:
    """获取项目根目录"""
    return Path(__file__).parent.parent


def fix_white_svgs(icons_dir: str = None):
    """将所有 *_white.svg 文件的颜色改为白色"""
    if icons_dir is None:
        # 默认处理项目中的图标目录
        project_root = get_project_root()
        icons_dirs = [
            project_root / "app" / "resource" / "images" / "icons",
            project_root / "app" / "resource" / "images" / "fluentIcon"
        ]
        for icons_path in icons_dirs:
            if icons_path.exists():
                _process_directory(icons_path)
        return
    
    _process_directory(Path(icons_dir))


def _process_directory(icons_path: Path):
    """处理单个目录中的 SVG 文件"""
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
    print(f"目录: {icons_path}")
    print(f"Total fixed: {fixed_count} files")
    print(f"Total skipped (already white): {skipped_count} files")
    print(f"Total processed: {len(white_svgs)} files")


def main():
    """主函数"""
    fix_white_svgs()


if __name__ == "__main__":
    main()
