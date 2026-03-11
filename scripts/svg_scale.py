#!/usr/bin/env python3
"""
SVG 处理脚本：去除空白边距 / 等比放大

【原理说明】
SVG 由两个独立的尺寸概念控制渲染：
  - width / height : 画布的实际像素尺寸（渲染出来多大）
  - viewBox        : 在坐标空间中"看哪个矩形区域"，格式为 "x y w h"
  渲染引擎会将 viewBox 所指定的内容区域，拉伸/缩放后填满 width×height 画布。

【去除 padding（--trim-only）】
  很多图标设计时图形周围留有空白 padding，例如：
    viewBox="0 0 1024 1024"，但实际图形只在 128~896 范围内
  处理步骤：
    1. 解析所有 <path d="..."> 的坐标数据，计算图形内容的紧边界 (min_x,min_y,max_x,max_y)
    2. 将 viewBox 裁剪为内容边界：viewBox="128 128 768 768"
    3. 保留原始 width/height 不变（如 256×256）
  最终效果：渲染引擎将 768×768 的内容区域填满 256×256 画布，图形放大填满，padding 消失。

【等比放大（默认）】
  将 viewBox 宽高等比缩放，使最大边达到指定尺寸（默认 1024px），同步更新 width/height。
  可与去除 padding 组合使用（先 trim 再 scale）。

【输出文件名】
  输出文件在原文件名后添加 _ab 后缀（auto-bound），如 icon.svg → icon_ab.svg

使用方法:
    python svg_scale.py <input.svg>              # 去除边距 + 放大到 1024px
    python svg_scale.py <input.svg> --trim-only  # 仅去除空白边距，保留原始尺寸
    python svg_scale.py <input.svg> --no-trim    # 不去除边距，只等比放大
    python svg_scale.py <input.svg> -o 512       # 指定放大目标尺寸为 512px
    python svg_scale.py <input.svg> --margin 10  # 放大后额外添加 10px 边距
    python svg_scale.py <input_dir>              # 批量处理目录
    python svg_scale.py <input_dir> -r           # 递归处理子目录
"""

import argparse
import os
import re
import sys
from pathlib import Path
from xml.etree import ElementTree as ET


def parse_path_commands(path_data: str) -> list[tuple[float, float]]:
    """
    解析 SVG path 的 d 属性，提取所有端点的绝对坐标。

    SVG path 支持绝对命令（大写，如 M/L/C）和相对命令（小写，如 m/l/c）：
      - 绝对命令：坐标值直接是画布坐标
      - 相对命令：坐标值是相对当前位置的偏移量

    本函数维护一个"当前位置 (cx, cy)"状态机，对每条命令：
      - 绝对命令直接更新 cx/cy
      - 相对命令将偏移量累加到 cx/cy

    支持的命令：
      M/m  移动到
      L/l  直线到
      H/h  水平线到
      V/v  垂直线到
      C/c  三次贝塞尔曲线（提取控制点+终点）
      S/Q/s/q  平滑/二次贝塞尔曲线
      T/t  平滑二次贝塞尔曲线终点
      A/a  椭圆弧（提取终点坐标，跳过 rx/ry/x-rotation/large-arc/sweep 参数）
      Z/z  闭合路径（无坐标）

    Returns:
        所有端点/控制点的绝对坐标列表 [(x, y), ...]
    """
    points = []
    tokens = re.findall(r'([MmLlHhVvCcSsQqTtAaZz])|([+-]?[\d.]+(?:[eE][+-]?\d+)?)', path_data)
    
    cmd = None
    nums = []
    cx, cy = 0.0, 0.0  # 当前位置
    
    def process(cmd, nums, cx, cy):
        """处理一条命令，返回 (新坐标列表, 新cx, 新cy)"""
        pts = []
        if not nums and cmd not in ('Z', 'z'):
            return pts, cx, cy
        
        if cmd == 'M':
            for i in range(0, len(nums) - 1, 2):
                cx, cy = nums[i], nums[i+1]
                pts.append((cx, cy))
        elif cmd == 'm':
            for i in range(0, len(nums) - 1, 2):
                cx += nums[i]; cy += nums[i+1]
                pts.append((cx, cy))
        elif cmd == 'L':
            for i in range(0, len(nums) - 1, 2):
                cx, cy = nums[i], nums[i+1]
                pts.append((cx, cy))
        elif cmd == 'l':
            for i in range(0, len(nums) - 1, 2):
                cx += nums[i]; cy += nums[i+1]
                pts.append((cx, cy))
        elif cmd == 'H':
            for n in nums:
                cx = n
                pts.append((cx, cy))
        elif cmd == 'h':
            for n in nums:
                cx += n
                pts.append((cx, cy))
        elif cmd == 'V':
            for n in nums:
                cy = n
                pts.append((cx, cy))
        elif cmd == 'v':
            for n in nums:
                cy += n
                pts.append((cx, cy))
        elif cmd == 'C':
            for i in range(0, len(nums) - 5, 6):
                pts.append((nums[i], nums[i+1]))
                pts.append((nums[i+2], nums[i+3]))
                cx, cy = nums[i+4], nums[i+5]
                pts.append((cx, cy))
        elif cmd == 'c':
            for i in range(0, len(nums) - 5, 6):
                pts.append((cx + nums[i], cy + nums[i+1]))
                pts.append((cx + nums[i+2], cy + nums[i+3]))
                cx += nums[i+4]; cy += nums[i+5]
                pts.append((cx, cy))
        elif cmd in ('S', 'Q'):
            for i in range(0, len(nums) - 3, 4):
                pts.append((nums[i], nums[i+1]))
                cx, cy = nums[i+2], nums[i+3]
                pts.append((cx, cy))
        elif cmd in ('s', 'q'):
            for i in range(0, len(nums) - 3, 4):
                pts.append((cx + nums[i], cy + nums[i+1]))
                cx += nums[i+2]; cy += nums[i+3]
                pts.append((cx, cy))
        elif cmd == 'T':
            for i in range(0, len(nums) - 1, 2):
                cx, cy = nums[i], nums[i+1]
                pts.append((cx, cy))
        elif cmd == 't':
            for i in range(0, len(nums) - 1, 2):
                cx += nums[i]; cy += nums[i+1]
                pts.append((cx, cy))
        elif cmd == 'A':
            for i in range(0, len(nums) - 6, 7):
                cx, cy = nums[i+5], nums[i+6]
                pts.append((cx, cy))
        elif cmd == 'a':
            for i in range(0, len(nums) - 6, 7):
                cx += nums[i+5]; cy += nums[i+6]
                pts.append((cx, cy))
        return pts, cx, cy
    
    for letter, number in tokens:
        if letter:
            if cmd is not None:
                new_pts, cx, cy = process(cmd, nums, cx, cy)
                points.extend(new_pts)
            cmd = letter
            nums = []
        elif number:
            try:
                nums.append(float(number))
            except ValueError:
                pass
    
    if cmd is not None:
        new_pts, cx, cy = process(cmd, nums, cx, cy)
        points.extend(new_pts)
    
    return points


def parse_path_bounds(content: str) -> tuple[float, float, float, float] | None:
    """
    扫描 SVG 文本中所有 <path d="..."> 元素，计算图形内容的紧边界框。

    兼容两种 path 写法：
      - 自闭合：<path d="..." />
      - 非自闭合：<path d="...">

    通过 parse_path_commands() 将每条 path 的 d 属性解析为绝对坐标点，
    然后取所有点的 min/max 得到边界。

    Returns:
        (min_x, min_y, max_x, max_y) 内容紧边界，或 None（无 path 时）
    """
    # 提取所有 path 的 d 属性（兼容 自闭合 /> 和 >...</path> 两种格式）
    path_pattern = r'<path\b[^>]*?\bd=["\']([^"\']+)["\'][^>]*?(?:/>|>)'
    paths = re.findall(path_pattern, content, re.IGNORECASE | re.DOTALL)
    
    if not paths:
        return None
    
    all_points = []
    for path_data in paths:
        all_points.extend(parse_path_commands(path_data))
    
    if not all_points:
        return None
    
    xs = [p[0] for p in all_points]
    ys = [p[1] for p in all_points]
    
    return (min(xs), min(ys), max(xs), max(ys))


def trim_svg_padding(content: str, keep_size: bool = False) -> tuple[str, float, float, float, float] | None:
    """
    去除 SVG 图形周围的空白边距。

    【原理】
    SVG 的显示由 viewBox 和 width/height 共同决定：
      - viewBox="x y w h" 指定从坐标空间的哪个矩形区域取内容
      - width/height 是最终画布大小
      - 渲染引擎将 viewBox 区域缩放填满 width×height

    很多图标的 viewBox 比实际图形大（四周有空白 padding）。
    本函数通过解析 path 坐标，计算图形的紧边界，
    再将 viewBox 裁剪为紧边界来去除 padding。

    【keep_size=False（默认，配合 scale_svg 使用）】
      viewBox 裁剪为内容边界，width/height 也同步改为内容尺寸。
      后续 scale_svg 再将其放大到目标尺寸。

    【keep_size=True（--trim-only 模式）】
      viewBox 裁剪为内容边界，但 width/height 保留原始值。
      效果：渲染引擎将裁剪后的内容区域拉伸填满原始画布，
      图形自动变大填满，padding 消失，画布尺寸不变。

      示例：
        原始: viewBox="0 0 1024 1024" width="256" height="256"
              图形实际范围: 128~896（四周各有 128px padding）
        处理: viewBox="128 128 768 768" width="256" height="256"
              渲染器将 768×768 内容填满 256×256 画布 → 图形无 padding 版本

    Args:
        content:    SVG 文本内容
        keep_size:  True=保留原始 width/height（trim-only 模式）

    Returns:
        (新内容, 原始vbW, 原始vbH, 新vbW, 新vbH) 或 None（解析失败时）
    """
    # 获取原始 viewBox
    viewbox_match = re.search(
        r'viewBox=["\']([^"\']+)["\']',
        content,
        re.IGNORECASE
    )
    
    if not viewbox_match:
        print("  警告: 未找到 viewBox，无法裁剪")
        return None
    
    vb_values = viewbox_match.group(1).split()
    if len(vb_values) < 4:
        return None
    
    vb_x = float(vb_values[0])
    vb_y = float(vb_values[1])
    vb_width = float(vb_values[2])
    vb_height = float(vb_values[3])
    
    # 获取原始 width/height
    orig_w_match = re.search(r'(?<!\w)width=["\']([^"\']+)["\']', content, re.IGNORECASE)
    orig_h_match = re.search(r'(?<!\w)height=["\']([^"\']+)["\']', content, re.IGNORECASE)
    orig_width_str = orig_w_match.group(1) if orig_w_match else str(vb_width)
    orig_height_str = orig_h_match.group(1) if orig_h_match else str(vb_height)
    
    # 解析 path 边界
    bounds = parse_path_bounds(content)
    if not bounds:
        print("  警告: 无法解析 path 边界")
        return None
    
    min_x, min_y, max_x, max_y = bounds
    
    # 新 viewBox = 内容紧边界
    new_vb_x = min_x
    new_vb_y = min_y
    new_vb_w = max_x - min_x
    new_vb_h = max_y - min_y
    
    # 更新 viewBox
    new_viewbox = f"{new_vb_x} {new_vb_y} {new_vb_w} {new_vb_h}"
    new_content = re.sub(
        r'viewBox=["\'][^"\']+["\']',
        f'viewBox="{new_viewbox}"',
        content,
        count=1,
        flags=re.IGNORECASE
    )
    
    if keep_size:
        # 保留原始 width/height，让渲染引擎自动缩放填满画布
        target_w = orig_width_str
        target_h = orig_height_str
    else:
        target_w = str(new_vb_w)
        target_h = str(new_vb_h)
    
    new_content = re.sub(
        r'(?<!\w)width=["\'][^"\']+["\']',
        f'width="{target_w}"',
        new_content,
        count=1,
        flags=re.IGNORECASE
    )
    new_content = re.sub(
        r'(?<!\w)height=["\'][^"\']+["\']',
        f'height="{target_h}"',
        new_content,
        count=1,
        flags=re.IGNORECASE
    )
    
    pad_x = min_x - vb_x
    pad_y = min_y - vb_y
    print(f"  原始 viewBox: {vb_x:.1f} {vb_y:.1f} {vb_width:.1f} {vb_height:.1f}")
    print(f"  内容边界:     {min_x:.1f} {min_y:.1f} → {max_x:.1f} {max_y:.1f}")
    print(f"  去除 padding: left={pad_x:.1f}  top={pad_y:.1f}  right={(vb_x+vb_width-max_x):.1f}  bottom={(vb_y+vb_height-max_y):.1f}")
    if keep_size:
        print(f"  画布尺寸保留: {target_w}x{target_h}")
    
    return (new_content, vb_width, vb_height, new_vb_w, new_vb_h)


def parse_svg_size(content: str) -> tuple[float, float, float, float] | None:
    """
    解析 SVG 的尺寸信息
    
    Returns:
        (width, height, viewBox_width, viewBox_height) 或 None
    """
    # 提取 viewBox
    viewbox_match = re.search(
        r'viewBox=["\']([^"\']+)["\']',
        content,
        re.IGNORECASE
    )
    
    if viewbox_match:
        vb_values = viewbox_match.group(1).split()
        if len(vb_values) >= 4:
            vb_width = float(vb_values[2])
            vb_height = float(vb_values[3])
        else:
            return None
    else:
        # 没有 viewBox，尝试从 width/height 创建
        vb_width = None
        vb_height = None
    
    # 提取 width
    width_match = re.search(
        r'width=["\']([^"\']+)["\']',
        content,
        re.IGNORECASE
    )
    
    # 提取 height
    height_match = re.search(
        r'height=["\']([^"\']+)["\']',
        content,
        re.IGNORECASE
    )
    
    if width_match and height_match:
        width_str = width_match.group(1)
        height_str = height_match.group(1)
        
        # 处理 px 单位
        width = float(width_str.replace('px', '').replace('pt', ''))
        height = float(height_str.replace('px', '').replace('pt', ''))
        
        # 如果没有 viewBox，使用 width/height 作为 viewBox
        if vb_width is None:
            vb_width = width
            vb_height = height
            
        return (width, height, vb_width, vb_height)
    
    return None


def scale_svg(content: str, max_size: int = 1024, margin: int = 0) -> str | None:
    """
    等比放大 SVG 到指定最大尺寸
    
    Args:
        content: SVG 文件内容
        max_size: 最大尺寸（宽或高）
        margin: 边距（像素）
    
    Returns:
        处理后的 SVG 内容，或 None（如果处理失败）
    """
    size_info = parse_svg_size(content)
    if not size_info:
        print("  错误: 无法解析 SVG 尺寸")
        return None
    
    orig_width, orig_height, vb_width, vb_height = size_info
    
    # 计算缩放比例（保持等比）
    scale_w = max_size / vb_width
    scale_h = max_size / vb_height
    scale = min(scale_w, scale_h)
    
    # 计算新尺寸
    new_vb_width = vb_width * scale
    new_vb_height = vb_height * scale
    
    # 添加边距
    if margin > 0:
        new_vb_width += margin * 2
        new_vb_height += margin * 2
    
    # 更新 width 和 height
    content = re.sub(
        r'width=["\'][^"\']+["\']',
        f'width="{int(new_vb_width)}"',
        content,
        count=1,
        flags=re.IGNORECASE
    )
    
    content = re.sub(
        r'height=["\'][^"\']+["\']',
        f'height="{int(new_vb_height)}"',
        content,
        count=1,
        flags=re.IGNORECASE
    )
    
    # 更新或添加 viewBox
    if margin > 0:
        # 有边距时，viewBox 需要包含边距
        new_viewbox = f"{-margin} {-margin} {int(new_vb_width)} {int(new_vb_height)}"
    else:
        new_viewbox = f"0 0 {int(vb_width * scale)} {int(vb_height * scale)}"
    
    if re.search(r'viewBox=["\'][^"\']+["\']', content, re.IGNORECASE):
        # 更新现有 viewBox
        content = re.sub(
            r'viewBox=["\'][^"\']+["\']',
            f'viewBox="{new_viewbox}"',
            content,
            count=1,
            flags=re.IGNORECASE
        )
    else:
        # 添加 viewBox 到 svg 标签
        content = re.sub(
            r'(<svg[^>]*)',
            rf'\1 viewBox="{new_viewbox}"',
            content,
            count=1,
            flags=re.IGNORECASE
        )
    
    print(f"  原始尺寸: {orig_width}x{orig_height} (viewBox: {vb_width}x{vb_height})")
    print(f"  新尺寸: {int(new_vb_width)}x{int(new_vb_height)}")
    print(f"  缩放比例: {scale:.2f}x")
    
    return content


def process_file(input_path: Path, max_size: int, margin: int, suffix: str = "", trim: bool = True, trim_only: bool = False) -> bool:
    """
    处理单个 SVG 文件
    
    Args:
        input_path: 输入文件路径
        max_size: 最大尺寸
        margin: 边距
        suffix: 输出文件名后缀
        trim: 是否去除空白边距
        trim_only: 仅去除边距，不进行缩放
    
    Returns:
        是否成功
    """
    print(f"\n处理: {input_path.name}")
    
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"  错误: 无法读取文件 - {e}")
        return False
    
    # 检查是否是 SVG
    if not content.strip().startswith('<?xml') and '<svg' not in content:
        print(f"  跳过: 不是有效的 SVG 文件")
        return False
    
    # 第一步：去除空白边距
    if trim or trim_only:
        # trim_only 模式保留原始画布尺寸（去padding后图形自动填满）
        trim_result = trim_svg_padding(content, keep_size=trim_only)
        if trim_result:
            content = trim_result[0]
        else:
            print("  跳过裁剪，使用原始尺寸")
    
    # 第二步：等比放大（trim_only 模式跳过）
    if trim_only:
        result_content = content
    else:
        result_content = scale_svg(content, max_size, margin)
        if not result_content:
            return False
    
    # 生成输出文件名
    stem = input_path.stem
    # 如果已经有后缀，不再添加
    if not stem.endswith(suffix):
        output_name = f"{stem}{suffix}{input_path.suffix}"
    else:
        output_name = input_path.name
    
    output_path = input_path.parent / output_name
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result_content)
        print(f"  输出: {output_path.name}")
        return True
    except Exception as e:
        print(f"  错误: 无法写入文件 - {e}")
        return False


def process_directory(dir_path: Path, max_size: int, margin: int, recursive: bool = False, trim: bool = True, trim_only: bool = False) -> tuple[int, int]:
    """
    批量处理目录中的 SVG 文件
    
    Returns:
        (成功数, 总数)
    """
    pattern = "**/*.svg" if recursive else "*.svg"
    svg_files = list(dir_path.glob(pattern))
    
    if not svg_files:
        print(f"目录中没有找到 SVG 文件: {dir_path}")
        return (0, 0)
    
    print(f"\n找到 {len(svg_files)} 个 SVG 文件")
    
    success = 0
    for svg_file in svg_files:
        # 跳过已处理的文件（避免重复处理 _ab 文件）
        if svg_file.stem.endswith("_ab"):
            print(f"\n跳过已处理文件: {svg_file.name}")
            continue
            
        if process_file(svg_file, max_size, margin, trim=trim, trim_only=trim_only):
            success += 1
    
    return (success, len(svg_files))


def main():
    parser = argparse.ArgumentParser(
        description="SVG 处理工具（去除边距 / 等比放大）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s icon.svg                    # 去除边距 + 放大到1024px
  %(prog)s icon.svg --trim-only        # 仅去除空白边距，不放大
  %(prog)s icon.svg -o 512             # 指定最大尺寸512px
  %(prog)s icons/                      # 批量处理目录
  %(prog)s icons/ -r                   # 递归处理子目录
  %(prog)s icon.svg --margin 20        # 添加20px边距
  %(prog)s icon.svg --no-trim          # 不去除空白边距，只放大
        """
    )
    
    parser.add_argument(
        'input',
        help='输入文件或目录'
    )
    
    parser.add_argument(
        '-o', '--output-size',
        type=int,
        default=1024,
        help='输出最大尺寸（宽或高），默认 1024'
    )
    
    parser.add_argument(
        '-m', '--margin',
        type=int,
        default=0,
        help='边距（像素），默认 0'
    )
    
    parser.add_argument(
        '-r', '--recursive',
        action='store_true',
        help='递归处理子目录'
    )
    
    parser.add_argument(
        '-s', '--suffix',
        default='',
        help='输出文件名后缀，默认 空'
    )
    
    trim_group = parser.add_mutually_exclusive_group()
    trim_group.add_argument(
        '--trim-only',
        action='store_true',
        default=False,
        help='仅去除空白边距，不进行等比放大'
    )
    trim_group.add_argument(
        '--no-trim',
        dest='trim',
        action='store_false',
        default=True,
        help='不去除空白边距，只进行等比放大'
    )
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    
    if not input_path.exists():
        print(f"错误: 路径不存在 - {args.input}")
        sys.exit(1)
    
    trim = getattr(args, 'trim', True)
    trim_only = args.trim_only
    
    print(f"SVG 处理工具")
    if trim_only:
        print(f"模式: 仅去除空白边距")
    else:
        print(f"最大尺寸: {args.output_size}px")
        print(f"边距: {args.margin}px")
        print(f"去除边距: {'是' if trim else '否'}")
    
    if input_path.is_file():
        success = process_file(input_path, args.output_size, args.margin, args.suffix, trim=trim, trim_only=trim_only)
        sys.exit(0 if success else 1)
    else:
        success, total = process_directory(
            input_path,
            args.output_size,
            args.margin,
            args.recursive,
            trim=trim,
            trim_only=trim_only
        )
        print(f"\n处理完成: {success}/{total} 个文件成功")
        sys.exit(0 if success == total else 1)


if __name__ == '__main__':
    main()
