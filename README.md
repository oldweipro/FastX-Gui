# FastX-Gui

[![GitHub release](https://img.shields.io/github/v/release/fastxteam/FastX-Gui?include_prereleases)](https://github.com/fastxteam/FastX-Gui/releases)
[![GitHub license](https://img.shields.io/github/license/fastxteam/FastX-Gui)](LICENSE.txt)
[![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)](https://www.python.org/downloads/)

FastX-Gui 是一个基于 PySide6 和 PyQt-Fluent-Widgets 开发的图形用户界面应用程序，提供现代化、美观的用户界面和丰富的功能。

![](./app/resource/images/png/app.png)

## ✨ 功能特性

- 🎨 **现代化 UI** - 基于 Fluent Design System 的美观界面
- 🌐 **国际化支持** - 支持中文简体、中文繁体等多语言
- 🔧 **工具集** - 集成多种实用工具
- 📦 **一键打包** - 使用 Nuitka 编译为独立可执行文件
- 🔄 **自动更新检测** - 支持检测最新版本

## 📋 系统要求

- Windows 10/11 (x64)
- Python 3.13+

## 🚀 快速开始

### 下载安装

从 [Releases](https://github.com/fastxteam/FastX-Gui/releases/latest) 页面下载最新版本的可执行文件，无需安装 Python 环境。

### 从源码运行

1. 克隆项目仓库：
   ```bash
   git clone https://github.com/fastxteam/FastX-Gui.git
   cd FastX-Gui
   ```

2. 安装 [uv](https://docs.astral.sh/uv/)（推荐）或使用 pip：
   ```bash
   # 使用 uv
   uv sync
   
   # 或使用 pip
   pip install -e .
   ```

3. 更新资源文件并运行：
   ```bash
   # 更新资源文件
   python dev.py all
   
   # 运行应用
   uv run python main.py
   ```

## 🔨 构建

使用 Nuitka 构建可执行文件：

```bash
uv run nuitka `
  --standalone `
  --assume-yes-for-downloads `
  --msvc=latest `
  --windows-icon-from-ico=./app/resource/images/ico/logo-m.ico `
  --enable-plugins=pyside6 `
  --onefile `
  --output-dir=./dist `
  ./main.py
```

## 📦 发布流程

项目使用 GitHub Actions 自动化发布：

### 自动发布
在 commit message 中添加关键词触发发布：
- `[release]` 或 `[release-patch]` - 发布补丁版本
- `[release-minor]` - 发布次版本
- `[release-major]` - 发布主版本

### 手动发布
在 GitHub Actions 页面手动触发 workflow，选择版本类型。

## 🛠️ 技术栈

- **PySide6** - Qt 官方 Python 绑定
- **PyQt-Fluent-Widgets** - 基于 Fluent Design System 的现代化 UI 组件库
- **Nuitka** - Python 到 C++ 编译器
- **SQLAlchemy** - 数据库 ORM
- **uv** - 快速 Python 包管理器

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

### 本项目许可证
本项目代码遵循 **GNU General Public License v3.0 (GPLv3)**。

### 第三方组件

#### 1. PyQt-Fluent-Widgets
- **许可证选择**:
  - GNU General Public License v3.0
  - [商业许可证](https://qfluentwidgets.com/price) (可闭源使用)
- **项目地址**: https://github.com/zhiyiYo/PyQt-Fluent-Widgets
- **作者**: zhiyiYo (Zhengzhi Huang)

#### 2. PySide6
- **许可证**: LGPL v3
- **版权**: The Qt Company Ltd

### 许可证组合说明

#### 情况1：使用 GPLv3 版本组件
如果你使用 GPLv3 版本的 PyQt-Fluent-Widgets：
- ✅ 可以免费使用、修改本项目
- ✅ 可以用于商业目的
- ❌ 但分发时必须开源所有代码（GPLv3 要求）

#### 情况2：使用商业许可证版本
如果你购买了 PyQt-Fluent-Widgets 的商业许可证：
- ✅ 可以闭源使用本项目
- ✅ 可以商业分发
- ⚠️ 需遵守商业许可证条款

### 版权声明

Copyright (C) 2026 wanqiang.liu / FastXTeam