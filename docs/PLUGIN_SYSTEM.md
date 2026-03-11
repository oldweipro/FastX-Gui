# FastX-Gui 插件系统设计文档

## 概述

FastX-Gui 采用插件化架构设计，旨在构建一个可扩展的工具Hub平台。通过标准化的插件接口和MVC架构模式，开发者可以轻松地添加新的工具功能，而无需修改核心代码。

## 目录

1. [系统架构](#系统架构)
2. [插件命名规范](#插件命名规范)
3. [核心组件](#核心组件)
4. [插件目录结构规范](#插件目录结构规范)
5. [插件开发指南](#插件开发指南)
6. [插件加载机制](#插件加载机制)
7. [当前插件列表](#当前插件列表)
8. [最佳实践](#最佳实践)
9. [故障排除](#故障排除)

---

## 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    主应用程序 (main.py)                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              插件管理系统 (Plugin System)             │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │  │
│  │  │ PluginBase  │  │ PluginMgr   │  │ PluginReg   │   │  │
│  │  │ (基类)      │  │ (管理器)    │  │ (注册中心)  │   │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘   │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                    插件目录结构                        │  │
│  │  app/plugins/                                        │  │
│  │  ├── fast_ccp/           ← CCP工具插件               │  │
│  │  ├── fast_dem/           ← DEM工具插件               │  │
│  │  ├── fast_e2e/           ← E2E工具插件               │  │
│  │  ├── fast_fault_manager/ ← 故障管理插件              │  │
│  │  ├── fast_some_ip/       ← SomeIP工具插件            │  │
│  │  ├── rm_comments/        ← 注释清理插件              │  │
│  │  ├── qc_composition/      ← QC组合工具插件           │  │
│  │  ├── com_group_mapping/   ← COM组映射插件            │  │
│  │  └── ...                  ← 更多插件                 │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                 工具界面 (PluginInterface)            │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │  │
│  │  │ Diagnostic  │  │ Communica-  │  │ Utilities   │   │  │
│  │  │   Group     │  │   tion      │  │    Group    │   │  │
│  │  │             │  │    Group    │  │             │   │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘   │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 插件命名规范

### 目录命名

| 规则 | 示例 | 说明 |
|------|------|------|
| 格式 | `fast_` + `功能名` | 小写 snake_case |
| 前缀 | `fast_` | 统一前缀标识 |

**示例：**
- `fast_ccp` - CCP 工具
- `fast_dem` - DEM 工具
- `fast_e2e` - E2E 工具
- `fast_fault_manager` - 故障管理
- `fast_some_ip` - SomeIP 工具
- `rm_comments` - 注释清理（工具类）
- `qc_composition` - QC 组合（工具类）
- `com_group_mapping` - COM 组映射（工具类）

### 类命名

| 规则 | 示例 | 说明 |
|------|------|------|
| 格式 | `Fast` + `Name` + `Plugin` | PascalCase |
| 前缀 | `Fast` | 统一前缀 |

**示例：**
- `FastCCPPlugin`
- `FastDemPlugin`
- `FastE2EPlugin`
- `FastFaultManagerPlugin`
- `FastSomeIpPlugin`
- `RmCommentsPlugin`
- `QcCompositionPlugin`
- `ComGroupMappingPlugin`

---

## 核心组件

### 1. PluginBase (插件基类)

所有插件必须继承此类并实现其抽象方法。

```python
from app.plugins.plugin_base import PluginBase, PluginInfo, PluginCategory

class MyToolPlugin(PluginBase):
    @classmethod
    def get_plugin_info(cls) -> PluginInfo:
        return PluginInfo(
            name="My Tool",
            version="1.0.0",
            description="我的工具插件",
            author="开发者",
            category=PluginCategory.UTILITIES
        )
    
    def initialize(self) -> bool:
        # 初始化逻辑
        return True
    
    def get_main_widget(self, parent=None):
        # 返回主界面组件
        return self._main_widget
    
    def cleanup(self):
        # 清理资源
        pass
```

### 2. PluginManager (插件管理器)

负责插件的生命周期管理：
- 加载/卸载插件
- 配置管理
- 状态跟踪
- 依赖检查

### 3. PluginRegistry (插件注册中心)

负责插件的注册和发现：
- 自动扫描插件目录
- 维护插件注册表
- 提供插件查找功能
- 支持按分类检索

---

## 插件目录结构规范

每个插件应遵循以下标准目录结构：

```
app/plugins/fast_xxx/
├── __init__.py              # 插件包初始化，导出插件类
├── manifest.json            # 插件元数据描述文件
├── plugin.py                # 插件主入口文件
├── ui/                      # 用户界面层 (MVC - View)
│   ├── __init__.py
│   ├── main_widget.py       # 主界面组件
│   └── components/          # 子组件
│       └── xxx_component.py
├── core/                    # 核心业务逻辑层 (MVC - Model)
│   ├── __init__.py
│   └── processor.py         # 核心处理器
├── service/                 # 服务层 (MVC - Controller)
│   ├── __init__.py
│   └── xxx_service.py
├── models/                  # 数据模型
│   ├── __init__.py
│   └── xxx_model.py
├── resources/               # 插件资源文件
│   ├── icons/               # 图标文件
│   └── templates/           # 模板文件
└── tests/                   # 测试文件（可选）
    └── test_xxx.py
```

### manifest.json 格式

```json
{
    "name": "fast_xxx",
    "display_name": "XXX Tool",
    "version": "1.0.0",
    "description": "插件描述",
    "author": "开发者",
    "category": "utilities",
    "icon": "resources/icons/icon.png",
    "dependencies": [],
    "enabled": true
}
```

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| name | string | 是 | 插件目录名 |
| display_name | string | 是 | 显示名称 |
| version | string | 是 | 版本号 (semver) |
| description | string | 是 | 插件描述 |
| author | string | 否 | 作者 |
| category | string | 是 | 分类 |
| icon | string | 否 | 图标路径 |
| dependencies | array | 否 | 依赖列表 |
| enabled | boolean | 否 | 是否启用 |

---

## 插件开发指南

### 1. 创建插件步骤

#### 步骤1：创建插件目录结构

```bash
mkdir -p app/plugins/fast_my_tool/{ui,core,service,resources}
touch app/plugins/fast_my_tool/__init__.py
touch app/plugins/fast_my_tool/plugin.py
touch app/plugins/fast_my_tool/manifest.json
```

#### 步骤2：编写 manifest.json

```json
{
    "name": "fast_my_tool",
    "display_name": "My Tool",
    "version": "1.0.0",
    "description": "我的工具插件",
    "author": "开发者",
    "category": "utilities",
    "enabled": true
}
```

#### 步骤3：实现插件主类 (plugin.py)

```python
from app.plugins.plugin_base import PluginBase, PluginInfo, PluginCategory
from .ui.main_widget import MyToolMainWidget

class FastMyToolPlugin(PluginBase):
    def __init__(self):
        plugin_info = PluginInfo(
            name="fast_my_tool",
            display_name="My Tool",
            version="1.0.0",
            description="我的工具插件",
            author="开发者",
            category=PluginCategory.UTILITIES
        )
        super().__init__(plugin_info)
        self._main_widget = None

    @classmethod
    def get_plugin_info(cls) -> PluginInfo:
        return PluginInfo(
            name="fast_my_tool",
            display_name="My Tool",
            version="1.0.0",
            description="我的工具插件",
            author="开发者",
            category=PluginCategory.UTILITIES
        )

    def initialize(self) -> bool:
        self._is_initialized = True
        return True

    def get_main_widget(self, parent=None):
        if self._main_widget is None:
            self._main_widget = MyToolMainWidget(parent)
        return self._main_widget

    def cleanup(self):
        if self._main_widget:
            self._main_widget.cleanup()
            self._main_widget = None
```

#### 步骤4：实现UI组件 (ui/main_widget.py)

```python
from PySide6.QtWidgets import QWidget, QVBoxLayout
from qfluentwidgets import ExpandSettingCard, FluentIcon as FIF

class MyToolMainWidget(ExpandSettingCard):
    def __init__(self, parent=None):
        super().__init__(
            icon=FIF.BOOK_SVG,
            title="My Tool",
            content="我的工具描述",
            parent=parent
        )
        self._init_ui()
        
    def _init_ui(self):
        # 初始化界面组件
        pass
        
    def cleanup(self):
        # 清理资源
        pass
```

### 2. 插件分类

| 分类 | 枚举值 | 用途 |
|------|--------|------|
| Diagnostic | `PluginCategory.DIAGNOSTIC` | 诊断工具 |
| Communication | `PluginCategory.COMMUNICATION` | 通信工具 |
| Serial | `PluginCategory.SERIAL` | 串口工具 |
| Utilities | `PluginCategory.UTILITIES` | 实用工具 |
| Custom | `PluginCategory.CUSTOM` | 自定义工具 |

---

## 插件加载机制

### 自动发现机制

插件管理器会自动扫描 `app/plugins/` 目录下的所有子目录，识别符合规范的插件并自动注册。

### 加载流程

```
1. PluginManager.load_plugins()
   ↓
2. PluginRegistry.discover_plugins()
   ↓
3. 扫描 plugins 目录
   ↓
4. 读取 manifest.json
   ↓
5. 导入插件模块
   ↓
6. 注册插件类
   ↓
7. 初始化插件实例
   ↓
8. 插件准备就绪
```

---

## 当前插件列表

| 插件名 | 目录 | 分类 | 说明 |
|--------|------|------|------|
| FastCCP | `fast_ccp` | Utilities | CCP 标定工具 |
| FastDem | `fast_dem` | Utilities | DEM 文件处理 |
| FastE2E | `fast_e2e` | Utilities | E2E 配置生成 |
| FastFaultManager | `fast_fault_manager` | Utilities | 故障管理工具 |
| FastSomeIp | `fast_some_ip` | Communication | SomeIP 配置工具 |
| RmComments | `rm_comments` | Utilities | 代码注释清理 |
| QcComposition | `qc_composition` | Utilities | QC 组合工具 |
| ComGroupMapping | `com_group_mapping` | Utilities | COM 组映射工具 |

---

## 最佳实践

### 1. 命名规范

- **目录名**：`fast_` + 功能名（小写 snake_case）
- **类名**：`Fast` + Name + `Plugin`（PascalCase）
- **模块文件名**：小写 snake_case

### 2. 错误处理

```python
def initialize(self) -> bool:
    try:
        # 初始化逻辑
        self._is_initialized = True
        return True
    except Exception as e:
        logger.error(f"插件初始化失败: {e}")
        return False
```

### 3. 资源管理

```python
def cleanup(self):
    # 清理UI组件
    if self._main_widget:
        self._main_widget.cleanup()
        self._main_widget = None
    
    # 清理其他资源
    # 关闭数据库连接等
```

### 4. 日志记录

```python
from loguru import logger

logger.info("插件加载成功")
logger.warning("配置项缺失")
logger.error("处理过程出错")
```

---

## 故障排除

### 常见问题

1. **插件未被发现**
   - 检查插件目录结构是否正确
   - 确认 `__init__.py` 文件存在
   - 验证插件类是否正确继承 `PluginBase`

2. **插件初始化失败**
   - 查看日志输出
   - 检查依赖项是否满足
   - 验证配置是否正确

3. **界面显示异常**
   - 确认 `get_main_widget()` 返回有效的 QWidget
   - 检查父级窗口设置
   - 验证UI组件初始化逻辑

---

## 贡献指南

欢迎贡献新的插件！请遵循：
1. 使用标准插件结构
2. 遵循命名规范
3. 编写单元测试
4. 提供完整的文档
5. 遵循代码风格规范