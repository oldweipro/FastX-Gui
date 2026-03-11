"""
一次性资源打包脚本
运行方式：python _setup_assets.py
将项目 data/ 目录中的图标和字体复制到 demo 本地，使 demo 完全独立。
"""
import shutil
import sys
from pathlib import Path

DEMO_DIR  = Path(__file__).parent
PROJ_ROOT = DEMO_DIR.parent

COPIES = [
    (PROJ_ROOT / "data/assets/FluentSystemIcons-Filled.json",
     DEMO_DIR  / "assets/FluentSystemIcons-Filled.json"),
    (PROJ_ROOT / "data/assets/FluentSystemIcons-Filled.ttf",
     DEMO_DIR  / "assets/FluentSystemIcons-Filled.ttf"),
    (PROJ_ROOT / "data/font/HarmonyOS_Sans_SC/HarmonyOS_Sans_SC_Medium.ttf",
     DEMO_DIR  / "fonts/HarmonyOS_Sans_SC_Medium.ttf"),
]

errors = []
for src, dst in COPIES:
    if not src.exists():
        errors.append(f"  源文件不存在: {src}")
        continue
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(src), str(dst))
    print(f"  已复制: {dst.name}  →  {dst.parent}")

if errors:
    print("\n以下文件未找到：")
    for e in errors:
        print(e)
    sys.exit(1)
else:
    print("\n全部资源已就绪，demo 可完全独立运行。")
