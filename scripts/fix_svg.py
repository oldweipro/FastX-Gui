#!/usr/bin/env python3
"""
SVG 图标颜色规范化脚本

【功能说明】
遍历目标目录，确保每个图标都同时拥有 _black.svg 和 _white.svg 两个版本：

【处理规则】
1. 原始文件（无 _black/_white 后缀）：
   - 检测主色调，若偏黑 → 重命名为 _black，再复制一份改色为 _white
   - 检测主色调，若偏白 → 重命名为 _white，再复制一份改色为 _black

2. 只有 _black 版本，缺少 _white：
   - 复制 _black，将颜色替换为白色，保存为 _white

3. 只有 _white 版本，缺少 _black：
   - 复制 _white，将颜色替换为黑色，保存为 _black

4. 已同时存在 _black 和 _white：跳过

【颜色判断】
- 黑色系：fill/stroke 值为 #000000、#212121、#2c2c2c、currentColor（默认黑）等
- 白色系：fill/stroke 值为 #ffffff、#fefefe 等
- 无颜色属性（fill=""，只有描边）：按 path 数量判断，或视为黑色处理

【特殊处理】
- 自动移除 DOCTYPE 声明以避免 Qt 解析错误
- 智能处理 fill="" 空属性，避免重复属性错误
- 支持所有常见 SVG 图形标签：path, circle, rect, ellipse, line, polyline, polygon

【用法】
    uv run fix-svg                          # 处理项目默认图标目录
    python scripts/fix_svg.py               # 同上
    python scripts/fix_svg.py --dir <path>  # 处理指定目录
    python scripts/fix_svg.py --dry-run     # 预览，不写入文件
"""

import argparse
import re
import sys
from pathlib import Path


# ── 颜色常量 ──────────────────────────────────────────────────────────────────

BLACK_COLORS = {
    '#000000', '#000', '#010101',
    '#111111', '#1a1a1a', '#212121',
    '#262626', '#2c2c2c', '#333333', '#3c3c3c',
    'black',
}

WHITE_COLORS = {
    '#ffffff', '#fff', '#fefefe',
    '#f5f5f5', '#f0f0f0',
    'white',
}

# 替换为黑色时使用的标准色
TARGET_BLACK = '#212121'
# 替换为白色时使用的标准色
TARGET_WHITE = '#ffffff'


# ── 颜色检测 ──────────────────────────────────────────────────────────────────

def _extract_fill_colors(content: str) -> list[str]:
    """从 SVG 内容中提取所有 fill 和 stroke 颜色值（小写）"""
    colors = []
    # 匹配 fill="..." 和 stroke="..."
    for m in re.finditer(r'(?:fill|stroke)=["\']([^"\']+)["\']', content, re.IGNORECASE):
        val = m.group(1).strip().lower()
        if val not in ('none', 'inherit', 'transparent', ''):
            colors.append(val)
    # 匹配 CSS style 中的 fill/stroke
    for m in re.finditer(r'(?:fill|stroke)\s*:\s*([^;"\'\s>]+)', content, re.IGNORECASE):
        val = m.group(1).strip().lower()
        if val not in ('none', 'inherit', 'transparent', ''):
            colors.append(val)
    return colors


def _is_dark_color(hex_color: str) -> bool:
    """判断一个十六进制颜色是否为深色（黑色系）"""
    try:
        # 移除 # 符号
        hex_val = hex_color.lstrip('#')
        # 处理简写形式（如 #fff）
        if len(hex_val) == 3:
            hex_val = ''.join([c*2 for c in hex_val])
        
        if len(hex_val) != 6:
            return False
        
        # 转换为 RGB
        r = int(hex_val[0:2], 16)
        g = int(hex_val[2:4], 16)
        b = int(hex_val[4:6], 16)
        
        # 计算亮度（简单的平均值）
        brightness = (r + g + b) / 3
        
        # 亮度低于 80 视为深色
        return brightness < 80
    except Exception:
        return False


def _is_light_color(hex_color: str) -> bool:
    """判断一个十六进制颜色是否为浅色（白色系）"""
    try:
        hex_val = hex_color.lstrip('#')
        if len(hex_val) == 3:
            hex_val = ''.join([c*2 for c in hex_val])
        
        if len(hex_val) != 6:
            return False
        
        r = int(hex_val[0:2], 16)
        g = int(hex_val[2:4], 16)
        b = int(hex_val[4:6], 16)
        
        brightness = (r + g + b) / 3
        
        # 亮度高于 200 视为浅色
        return brightness > 200
    except Exception:
        return False


def detect_color(content: str) -> str:
    """
    检测 SVG 的主色调。

    Returns:
        'black'  - 图形为黑色系
        'white'  - 图形为白色系
        'unknown' - 无法判断（如全部 fill="none"，无彩色）
    """
    colors = _extract_fill_colors(content)

    if not colors:
        # 没有任何颜色属性，默认视为黑色（currentColor 在亮色背景渲染为黑）
        return 'black'

    black_count = 0
    white_count = 0
    none_count  = sum(1 for c in colors if c in ('none', 'transparent'))

    for color in colors:
        if color in BLACK_COLORS or color == 'currentcolor':
            black_count += 1
        elif color in WHITE_COLORS:
            white_count += 1
        elif color.startswith('#') and _is_dark_color(color):
            black_count += 1
        elif color.startswith('#') and _is_light_color(color):
            white_count += 1

    effective = len(colors) - none_count
    if effective == 0:
        return 'black'

    if black_count > white_count:
        return 'black'
    elif white_count > black_count:
        return 'white'
    elif black_count == white_count and black_count > 0:
        return 'black'  # 平局视为黑色
    else:
        # 其他颜色（如品牌色），视为黑色
        return 'black'


# ── 颜色替换 ──────────────────────────────────────────────────────────────────

def _replace_colors(content: str, from_set: set[str], to_color: str) -> str:
    """将 SVG 中属于 from_set 的颜色值全部替换为 to_color"""
    def replacer(m):
        attr = m.group(1)   # fill 或 stroke
        val  = m.group(2)
        if val.lower() in from_set:
            return f'{attr}="{to_color}"'
        return m.group(0)

    content = re.sub(
        r'(fill|stroke)=["\']([^"\']+)["\']',
        replacer,
        content,
        flags=re.IGNORECASE
    )

    def replacer_style(m):
        prop = m.group(1)
        val  = m.group(2)
        if val.strip().lower() in from_set:
            return f'{prop}:{to_color}'
        return m.group(0)

    content = re.sub(
        r'(fill|stroke)\s*:\s*([^;"\'\s>]+)',
        replacer_style,
        content,
        flags=re.IGNORECASE
    )
    return content


def to_white(content: str) -> str:
    """
    将 SVG 中的黑色系（含 currentColor）全部替换为白色。
    
    特殊处理：
    - fill="" 或没有 fill 属性的 path/shape 元素 → 添加 fill="#ffffff"
    - stroke="" → 添加 stroke="#ffffff"
    - 移除 DOCTYPE 声明以避免解析错误
    """
    # 步骤 1: 移除 DOCTYPE 声明（避免 Qt 解析错误）
    result = re.sub(r'<!DOCTYPE[^>]*>', '', content)
    
    # 步骤 2: 替换已有颜色
    result = _replace_colors(result, BLACK_COLORS, TARGET_WHITE)
    
    # 步骤 3: 处理 currentColor
    result = re.sub(
        r'(?:fill|stroke)=["\']currentColor["\']',
        lambda m: f'{m.group(1)}="{TARGET_WHITE}"',
        result,
        flags=re.IGNORECASE
    )
    
    # 步骤 4: 智能处理 path/shape 标签的 fill 属性
    def process_tag(match):
        """处理单个标签，确保有且只有一个 fill 属性"""
        full_tag = match.group(0)
        
        # 检查是否已经有非空 fill 属性
        if re.search(r'\bfill\s*=\s*["\'][^"\']+["\']', full_tag):
            # 已有有效 fill 属性，保持不变
            return full_tag
        
        # 移除空的 fill 属性 (fill="" 或 fill='')
        attrs = re.sub(r'\s*\bfill\s*=\s*["\']["\']', '', full_tag)
        
        # 在标签名后添加 fill="#ffffff"
        tag_name = match.group(1)
        return re.sub(rf'<{tag_name}', f'<{tag_name} fill="{TARGET_WHITE}"', attrs)
    
    # 匹配常见的图形标签的开始标签
    for tag in ['path', 'circle', 'rect', 'ellipse', 'line', 'polyline', 'polygon']:
        result = re.sub(
            rf'<({tag})\s+[^>]*>',
            process_tag,
            result,
            flags=re.IGNORECASE
        )
    
    return result


def to_black(content: str) -> str:
    """
    将 SVG 中的白色系全部替换为黑色。
    
    特殊处理：
    - fill="" 或没有 fill 属性的 path/shape 元素 → 添加 fill="#212121"
    - stroke="" → 添加 stroke="#212121"
    - 移除 DOCTYPE 声明以避免解析错误
    """
    # 步骤 1: 移除 DOCTYPE 声明
    result = re.sub(r'<!DOCTYPE[^>]*>', '', content)
    
    result = _replace_colors(result, WHITE_COLORS, TARGET_BLACK)
    
    # 处理 fill="" 空字符串 → 填充为黑色
    def process_tag(match):
        """处理单个标签，确保有且只有一个 fill 属性"""
        full_tag = match.group(0)
        
        # 检查是否已经有非空 fill 属性
        if re.search(r'\bfill\s*=\s*["\'][^"\']+["\']', full_tag):
            return full_tag
        
        # 移除空的 fill 属性
        attrs = re.sub(r'\s*\bfill\s*=\s*["\']["\']', '', full_tag)
        
        # 添加 fill 属性
        tag_name = match.group(1)
        return re.sub(rf'<{tag_name}', f'<{tag_name} fill="{TARGET_BLACK}"', attrs)
    
    # 匹配常见的图形标签的开始标签
    for tag in ['path', 'circle', 'rect', 'ellipse', 'line', 'polyline', 'polygon']:
        result = re.sub(
            rf'<({tag})\s+[^>]*>',
            process_tag,
            result,
            flags=re.IGNORECASE
        )
    
    return result


# ── 核心处理 ──────────────────────────────────────────────────────────────────

def _stem_base(stem: str) -> str | None:
    """
    从文件名 stem 中去除 _black/_white 后缀，返回基础名。
    如果不带后缀，返回 None（表示是原始文件）。
    """
    if stem.endswith('_black'):
        return stem[:-6]
    if stem.endswith('_white'):
        return stem[:-6]
    return None


def process_directory(icons_path: Path, dry_run: bool = False, recursive: bool = False) -> dict:
    """
    处理目录中的 SVG 图标，确保每个图标都有 _black 和 _white 两个版本。

    Returns:
        统计信息字典
    """
    pattern = '**/*.svg' if recursive else '*.svg'
    all_svgs = list(icons_path.glob(pattern))
    
    # 调试：打印找到的文件
    print(f"[调试] 在 {icons_path} 中找到 {len(all_svgs)} 个 SVG 文件")
    for svg in all_svgs[:5]:  # 只显示前 5 个
        print(f"  - {svg.name}")

    # 按基础名分组
    # groups[base_name] = {'black': Path, 'white': Path, 'raw': Path}
    groups: dict[str, dict] = {}

    for svg in all_svgs:
        stem = svg.stem
        base = _stem_base(stem)

        if base is not None:
            # 有 _black 或 _white 后缀
            key = str(svg.parent / base)
            if key not in groups:
                groups[key] = {'black': None, 'white': None, 'raw': None, 'dir': svg.parent}
            if stem.endswith('_black'):
                groups[key]['black'] = svg
            else:
                groups[key]['white'] = svg
        else:
            # 原始文件（无后缀）
            key = str(svg.parent / stem)
            if key not in groups:
                groups[key] = {'black': None, 'white': None, 'raw': None, 'dir': svg.parent}
            groups[key]['raw'] = svg

    stats = {'renamed': 0, 'created': 0, 'skipped': 0, 'errors': 0}

    for key, g in sorted(groups.items()):
        base_name = Path(key).name
        d: Path = g['dir']

        has_black = g['black'] is not None
        has_white = g['white'] is not None
        has_raw   = g['raw']   is not None

        black_path = d / f'{base_name}_black.svg'
        white_path = d / f'{base_name}_white.svg'

        try:
            # ── 情况1：同时存在 _black 和 _white ─────────────────────────────
            if has_black and has_white:
                if has_raw:
                    print(f'[跳过]   {base_name}  (已有黑白两版，原始文件保留)')
                else:
                    print(f'[跳过]   {base_name}  (已有黑白两版)')
                stats['skipped'] += 1
                continue

            # ── 情况2：原始文件（无后缀），无 _black/_white ────────────────
            if has_raw and not has_black and not has_white:
                raw: Path = g['raw']
                content = raw.read_text(encoding='utf-8')
                color = detect_color(content)
                print(f'[原始]   {raw.name}  → 检测为 {color}')

                if color == 'black':
                    black_content = content
                    white_content = to_white(content)
                else:
                    white_content = content
                    black_content = to_black(content)

                if not dry_run:
                    black_path.write_text(black_content, encoding='utf-8')
                    white_path.write_text(white_content, encoding='utf-8')
                    raw.unlink()  # 删除原始文件

                print(f'  → 生成 {black_path.name}')
                print(f'  → 生成 {white_path.name}')
                print(f'  → 删除 {raw.name}')
                stats['created'] += 2
                stats['renamed'] += 1
                continue

            # ── 情况3：只有 _black，缺少 _white ──────────────────────────────
            if has_black and not has_white:
                content = g['black'].read_text(encoding='utf-8')
                white_content = to_white(content)
                print(f'[配对]   {base_name}_black  → 生成 {white_path.name}')
                if not dry_run:
                    white_path.write_text(white_content, encoding='utf-8')
                stats['created'] += 1

                # 若同时有原始文件，删除
                if has_raw:
                    print(f'  → 删除原始 {g["raw"].name}')
                    if not dry_run:
                        g['raw'].unlink()
                continue

            # ── 情况4：只有 _white，缺少 _black ──────────────────────────────
            if has_white and not has_black:
                content = g['white'].read_text(encoding='utf-8')
                black_content = to_black(content)
                print(f'[配对]   {base_name}_white  → 生成 {black_path.name}')
                if not dry_run:
                    black_path.write_text(black_content, encoding='utf-8')
                stats['created'] += 1

                if has_raw:
                    print(f'  → 删除原始 {g["raw"].name}')
                    if not dry_run:
                        g['raw'].unlink()
                continue

        except Exception as e:
            print(f'[错误]   {base_name}: {e}', file=sys.stderr)
            stats['errors'] += 1

    return stats


# ── 入口 ──────────────────────────────────────────────────────────────────────

def get_project_root() -> Path:
    return Path(__file__).parent.parent


def main():
    parser = argparse.ArgumentParser(
        description='SVG 图标颜色规范化：确保每个图标都有 _black 和 _white 两个版本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
处理规则:
  原始文件（无后缀）  → 检测颜色，重命名为 _black/_white，生成对立色版本
  只有 _black        → 自动生成 _white 版本
  只有 _white        → 自动生成 _black 版本
  已有黑白两版        → 跳过

示例:
  python scripts/fix_svg.py
  python scripts/fix_svg.py --dir app/resource/images/fluentIcon
  python scripts/fix_svg.py --dry-run
        """
    )
    parser.add_argument(
        '--dir',
        help='指定处理目录（默认处理项目内所有图标目录）'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='预览模式，只打印操作，不实际写入文件'
    )
    parser.add_argument(
        '-r', '--recursive',
        action='store_true',
        help='递归处理子目录'
    )
    args = parser.parse_args()

    if args.dry_run:
        print('【预览模式，不写入文件】\n')

    if args.dir:
        dirs = [Path(args.dir)]
    else:
        root = get_project_root()
        dirs = [
            root / 'app' / 'resource' / 'images' / 'icons',
            root / 'app' / 'resource' / 'images' / 'fluentIcon',
        ]
        dirs = [d for d in dirs if d.exists()]

    total = {'renamed': 0, 'created': 0, 'skipped': 0, 'errors': 0}

    for d in dirs:
        print(f'\n{"="*60}')
        print(f'目录: {d}')
        print('='*60)
        stats = process_directory(d, dry_run=args.dry_run, recursive=args.recursive)
        for k in total:
            total[k] += stats[k]

    print(f'\n{"="*60}')
    print(f'处理完成')
    print(f'  原始文件重命名: {total["renamed"]}')
    print(f'  新生成文件:     {total["created"]}')
    print(f'  已跳过:         {total["skipped"]}')
    print(f'  错误:           {total["errors"]}')


if __name__ == '__main__':
    main()
