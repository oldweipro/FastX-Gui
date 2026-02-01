# FastX-Gui

FastX-Gui是一个基于PyQt5和PyQt-Fluent-Widgets开发的图形用户界面应用程序，提供了现代化、美观的用户界面和丰富的功能。

![](./app/resource/images/png/app.png)
## 系统要求

- Python 3.10+
- PyQt5
- PyQt-Fluent-Widgets

## 安装

1. 克隆项目仓库：
   ```bash
   git clone https://github.com/yourusername/FastX-Gui.git
   cd FastX-Gui
   ```

2. 创建虚拟环境并激活：
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   ```

3. 安装依赖：
   ```bash
   # 安装PyQt-Fluent-Widgets (基础版)
   pip install "PyQt-Fluent-Widgets[full]" -i https://pypi.org/simple/
   ```

## 运行

### 更新資源文件
```bash
python dev.py all
```

### 生产模式
```bash
python main.py
```

## 技术依赖

- **PyQt5**: 跨平台GUI框架
- **PyQt-Fluent-Widgets**: 基于Fluent Design System的现代化UI组件库
  - 项目地址: https://github.com/zhiyiYo/PyQt-Fluent-Widgets.git

## License

### 本项目许可证
本项目代码遵循 **GNU General Public License v3.0 (GPLv3)**。

### 第三方组件

#### 1. PyQt-Fluent-Widgets
- **许可证选择**:
  - GNU General Public License v3.0
  - [商业许可证](https://qfluentwidgets.com/price) (可闭源使用)
- **作者声明**: 
  > "PyQt-Fluent-Widgets is licensed under GPLv3 for non-commercial project. For commercial use, please purchase a commercial license."
- **项目地址**: https://github.com/zhiyiYo/PyQt-Fluent-Widgets
- **作者**: zhiyiYo (Zhengzhi Huang)

#### 2. PyQt5
- **许可证选择**:
  - GNU General Public License v3.0
  - [商业许可证](https://www.riverbankcomputing.com/commercial) (可闭源使用)
- **版权**: Copyright © Riverbank Computing Limited

### 许可证组合说明

#### 情况1：使用 GPLv3 版本组件
如果你使用 GPLv3 版本的 PyQt5 和 PyQt-Fluent-Widgets：
- ✅ 可以免费使用、修改本项目
- ✅ 可以用于商业目的
- ❌ 但分发时必须开源所有代码（GPLv3 要求）

#### 情况2：使用商业许可证版本、
如果你购买了两个组件的商业许可证：
- ✅ 可以闭源使用本项目
- ✅ 可以商业分发
- ⚠️ 需遵守商业许可证条款

### 版权声明

Copyright (C) 2026 wanqiang.liu/FastXTeam