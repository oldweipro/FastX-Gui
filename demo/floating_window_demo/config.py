# ==================================================
# 自包含配置管理模块
# 替代原项目中 settings_access / path_utils / settings_default 的依赖
# ==================================================

import json
import os
import sys
from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, Signal

# --------------------------------------------------
# 路径工具
# --------------------------------------------------

def _get_app_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent


def get_demo_config_path() -> Path:
    return _get_app_root() / "floating_window_settings.json"


def get_assets_dir() -> Path:
    """返回 demo 本地 assets/ 目录"""
    return _get_app_root() / "assets"


def get_fonts_dir() -> Path:
    """返回 demo 本地 fonts/ 目录"""
    return _get_app_root() / "fonts"


def _copy_assets_if_needed() -> None:
    """
    将上级项目的图标/字体资源复制到 demo 本地 assets/ fonts/ 目录。
    仅在文件不存在时复制，幂等安全。
    在 项目根目录下首次运行后，demo 即可迁移到任意独立目录运行。
    """
    import shutil
    demo_dir  = _get_app_root()
    proj_root = demo_dir.parent

    copies = [
        (proj_root / "data/assets/FluentSystemIcons-Filled.json",
         demo_dir   / "assets/FluentSystemIcons-Filled.json"),
        (proj_root / "data/assets/FluentSystemIcons-Filled.ttf",
         demo_dir   / "assets/FluentSystemIcons-Filled.ttf"),
        (proj_root / "data/font/HarmonyOS_Sans_SC/HarmonyOS_Sans_SC_Medium.ttf",
         demo_dir   / "fonts/HarmonyOS_Sans_SC_Medium.ttf"),
    ]
    for src, dst in copies:
        if src.exists() and not dst.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(src), str(dst))


# --------------------------------------------------
# 默认设置
# --------------------------------------------------

DEFAULT_SETTINGS: dict[str, Any] = {
    "floating_window_management": {
        "startup_display_floating_window": True,
        "floating_window_opacity": 0.8,
        "floating_window_topmost_mode": 1,
        "floating_window_draggable": True,
        "floating_window_long_press_duration": 150,
        "do_not_steal_focus": False,
        "extend_quick_draw_component": False,
        "floating_window_button_control": ["roll_call", "quick_draw", "lottery"],
        "floating_window_placement": 0,
        "floating_window_display_style": 0,
        "floating_window_size": 3,
        "floating_window_theme": 0,
        "floating_window_stick_to_edge": True,
        "floating_window_stick_to_edge_recover_seconds": 5,
        "floating_window_stick_to_edge_display_style": 0,
        "hide_floating_window_on_foreground": False,
        "hide_floating_window_on_foreground_window_titles": "",
        "hide_floating_window_on_foreground_process_names": "",
        "quick_draw_class_name": "",
        "quick_draw_group_filter": "",
        "quick_draw_gender_filter": "",
    },
    "float_position": {
        "x": 100,
        "y": 100,
    },
}

# --------------------------------------------------
# 设置变化信号
# --------------------------------------------------

class SettingsSignals(QObject):
    settingChanged = Signal(str, str, object)


_settings_signals = SettingsSignals()


def get_settings_signals() -> SettingsSignals:
    return _settings_signals


# --------------------------------------------------
# 读/写接口
# --------------------------------------------------

def _load_file() -> dict:
    path = get_demo_config_path()
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_file(data: dict) -> None:
    path = get_demo_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def _get_default(section: str, key: str) -> Any:
    return DEFAULT_SETTINGS.get(section, {}).get(key)


def readme_settings_async(section: str, key: str, _timeout=None) -> Any:
    """读取配置值（同步实现，兼容原 API）"""
    data = _load_file()
    if section in data and key in data[section]:
        return data[section][key]
    return _get_default(section, key)


def update_settings(section: str, key: str, value: Any) -> None:
    """写入配置值并触发信号"""
    data = _load_file()
    data.setdefault(section, {})[key] = value
    _save_file(data)
    get_settings_signals().settingChanged.emit(section, key, value)


def init_settings() -> None:
    """初始化配置文件（首次运行时填充默认值）"""
    data = _load_file()
    changed = False
    for section, keys in DEFAULT_SETTINGS.items():
        data.setdefault(section, {})
        for key, default in keys.items():
            if key not in data[section]:
                data[section][key] = default
                changed = True
    if changed:
        _save_file(data)


if __name__ == "__main__":
    _copy_assets_if_needed()
    print("资源文件已复制完成。")
    print(f"  图标资源: {get_assets_dir()}")
    print(f"  字体资源: {get_fonts_dir()}")
