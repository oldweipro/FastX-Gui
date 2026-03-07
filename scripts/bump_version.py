#!/usr/bin/env python
"""
版本升级脚本
用于自动升级 pyproject.toml 和 setting.py 中的版本号

用法:
    python scripts/bump_version.py [major|minor|patch] [--version x.y.z]
    
示例:
    python scripts/bump_version.py patch   # 0.1.0 -> 0.1.1
    python scripts/bump_version.py minor   # 0.1.0 -> 0.2.0
    python scripts/bump_version.py major   # 0.1.0 -> 1.0.0
    python scripts/bump_version.py --version 1.2.3  # 直接指定版本
"""

import argparse
import re
import sys
from pathlib import Path


def get_project_root() -> Path:
    """获取项目根目录"""
    return Path(__file__).parent.parent


def parse_version(version_str: str) -> tuple[int, int, int]:
    """解析版本字符串，返回 (major, minor, patch)"""
    # 移除 'v' 前缀
    version_str = version_str.lstrip("v")
    parts = version_str.split(".")
    if len(parts) != 3:
        raise ValueError(f"Invalid version format: {version_str}")
    return int(parts[0]), int(parts[1]), int(parts[2])


def version_to_str(major: int, minor: int, patch: int) -> str:
    """将版本号转换为字符串"""
    return f"{major}.{minor}.{patch}"


def bump_version(current: tuple[int, int, int], bump_type: str) -> tuple[int, int, int]:
    """根据类型升级版本"""
    major, minor, patch = current
    if bump_type == "major":
        return major + 1, 0, 0
    elif bump_type == "minor":
        return major, minor + 1, 0
    elif bump_type == "patch":
        return major, minor, patch + 1
    else:
        raise ValueError(f"Unknown bump type: {bump_type}")


def update_pyproject_toml(file_path: Path, new_version: str) -> bool:
    """更新 pyproject.toml 中的版本"""
    if not file_path.exists():
        print(f"Error: {file_path} not found")
        return False

    content = file_path.read_text(encoding="utf-8")
    # 匹配 version = "x.y.z" 格式
    pattern = r'^version\s*=\s*"[^"]*"'
    new_content = re.sub(pattern, f'version = "{new_version}"', content, count=1, flags=re.MULTILINE)

    if new_content == content:
        print("Warning: No version found in pyproject.toml")
        return False

    file_path.write_text(new_content, encoding="utf-8")
    print(f"Updated pyproject.toml: version = \"{new_version}\"")
    return True


def update_setting_py(file_path: Path, new_version: str) -> bool:
    """更新 setting.py 中的 VERSION"""
    if not file_path.exists():
        print(f"Error: {file_path} not found")
        return False

    content = file_path.read_text(encoding="utf-8")
    # 匹配 VERSION = "vx.y.z" 或 VERSION = "x.y.z" 格式
    pattern = r'^VERSION\s*=\s*"[^"]*"'
    # 保持带 v 前缀
    version_with_v = f"v{new_version}" if not new_version.startswith("v") else new_version
    new_content = re.sub(pattern, f'VERSION = "{version_with_v}"', content, count=1, flags=re.MULTILINE)

    if new_content == content:
        print("Warning: No VERSION found in setting.py")
        return False

    file_path.write_text(new_content, encoding="utf-8")
    print(f"Updated setting.py: VERSION = \"{version_with_v}\"")
    return True


def get_current_version(pyproject_path: Path) -> str:
    """从 pyproject.toml 获取当前版本"""
    content = pyproject_path.read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]*)"', content, re.MULTILINE)
    if match:
        return match.group(1)
    raise ValueError("Cannot find version in pyproject.toml")


def main():
    parser = argparse.ArgumentParser(description="Bump version for FastX-Gui")
    parser.add_argument(
        "bump_type",
        nargs="?",
        choices=["major", "minor", "patch"],
        help="Version bump type: major (x.0.0), minor (0.x.0), or patch (0.0.x)",
    )
    parser.add_argument("--version", "-v", type=str, help="Specify exact version (e.g., 1.2.3)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be changed without making changes")
    args = parser.parse_args()

    if not args.bump_type and not args.version:
        parser.print_help()
        sys.exit(1)

    project_root = get_project_root()
    pyproject_path = project_root / "pyproject.toml"
    setting_path = project_root / "app" / "common" / "setting.py"

    # 获取当前版本
    current_version = get_current_version(pyproject_path)
    print(f"Current version: {current_version}")

    # 计算新版本
    if args.version:
        new_version = args.version.lstrip("v")
    else:
        current_tuple = parse_version(current_version)
        new_tuple = bump_version(current_tuple, args.bump_type)
        new_version = version_to_str(*new_tuple)

    print(f"New version: {new_version}")

    if args.dry_run:
        print("\n[DRY RUN] Would update:")
        print(f"  - {pyproject_path}: version = \"{new_version}\"")
        print(f"  - {setting_path}: VERSION = \"v{new_version}\"")
        return

    # 执行更新
    success = True
    success &= update_pyproject_toml(pyproject_path, new_version)
    success &= update_setting_py(setting_path, new_version)

    if success:
        print(f"\n✓ Version successfully bumped to {new_version}")
        # 输出版本号供 GitHub Actions 使用
        print(f"::set-output name=version::{new_version}")
        print(f"::set-output name=version_with_v::v{new_version}")
    else:
        print("\n✗ Failed to bump version")
        sys.exit(1)


if __name__ == "__main__":
    main()
