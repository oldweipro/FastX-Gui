# FastX-Gui 插件系统设计文档

## 概述

FastX-Gui 采用插件化架构设计，旨在构建一个可扩展的工具Hub平台。通过标准化的插件接口和MVC架构模式，开发者可以轻松地添加新的工具功能，而无需修改核心代码。

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
│  │  ├── ccp_tool/        ← CCP工具插件示例              │  │
│  │  ├── dem_tool/        ← DEM工具插件                  │  │
│  │  ├── e2e_tool/        ← E2E工具插件                  │  │
│  │  └── ...              ← 更多插件                     │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                 工具界面 (ToolsInterface)             │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │  │
│  │  │ Diagnostic  │  │ Communica-  │  │ Utilities   │   │  │
│  │  │   Group     │  │   tion      │  │    Group    │   │  │
│  │  │             │  │    Group    │  │             │   │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘   │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 插件系统核心组件

### 1. PluginBase (插件基类)

所有插件必须继承此类并实现其抽象方法。

```python
class PluginBase(ABC):
    def initialize(self) -> bool:           # 初始化插件
    def get_main_widget(self) -> QWidget:   # 获取主界面组件
    def cleanup(self):                      # 清理资源
    def get_config(self) -> Dict:           # 获取配置
    def set_config(self, config: Dict):     # 设置配置
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

## 插件目录结构规范

每个插件应遵循以下标准目录结构：

```
app/plugins/plugin_name/
├── __init__.py              # 插件包初始化
├── manifest.json            # 插件元数据描述文件
├── plugin.py                # 插件主入口文件
├── ui/                      # 用户界面层 (MVC - View)
│   ├── __init__.py
│   ├── main_widget.py       # 主界面组件
│   └── components/          # 子组件
│       ├── xxx_component.py
│       └── ...
├── core/                    # 核心业务逻辑层 (MVC - Model)
│   ├── __init__.py
│   ├── processor.py         # 核心处理器
│   └── models/              # 数据模型
│       ├── xxx_model.py
│       └── ...
├── service/                 # 服务层 (MVC - Controller)
│   ├── __init__.py
│   └── xxx_service.py
├── resources/               # 插件资源文件
│   ├── icons/               # 图标文件
│   ├── translations/        # 翻译文件
│   └── templates/           # 模板文件
└── tests/                   # 测试文件
    ├── __init__.py
    ├── test_xxx.py
    └── ...
```

## 插件开发指南

### 1. 创建插件步骤

#### 步骤1：创建插件目录结构
```bash
mkdir -p app/plugins/my_tool/{ui,core,service,resources,tests}
touch app/plugins/my_tool/__init__.py
touch app/plugins/my_tool/plugin.py
touch app/plugins/my_tool/manifest.json
```

#### 步骤2：编写插件元数据 (manifest.json)
```json
{
    "name": "my_tool",
    "version": "1.0.0",
    "description": "我的工具插件描述",
    "author": "开发者姓名",
    "category": "diagnostic",
    "icon": "icons/tool_icon.png",
    "dependencies": ["numpy", "pandas"],
    "enabled": true
}
```

#### 步骤3：实现插件主类 (plugin.py)
```python
from app.plugins.plugin_base import PluginBase, PluginInfo, PluginCategory
from .ui.main_widget import MyToolMainWidget

class MyToolPlugin(PluginBase):
    def __init__(self):
        plugin_info = PluginInfo(
            name="My Tool",
            version="1.0.0",
            description="我的工具插件",
            author="开发者",
            category=PluginCategory.DIAGNOSTIC
        )
        super().__init__(plugin_info)
        self._main_widget = None
        self._config = {}

    @classmethod
    def get_plugin_info(cls) -> PluginInfo:
        return PluginInfo(
            name="My Tool",
            version="1.0.0",
            description="我的工具插件",
            author="开发者",
            category=PluginCategory.DIAGNOSTIC
        )

    def initialize(self) -> bool:
        # 初始化插件逻辑
        self._config = {"some_setting": "value"}
        self._is_initialized = True
        return True

    def get_main_widget(self, parent=None):
        if self._main_widget is None:
            self._main_widget = MyToolMainWidget(parent)
        return self._main_widget

    def cleanup(self):
        if self._main_widget:
            self._main_widget.cleanup()
        self._config.clear()

    def get_config(self):
        if self._main_widget:
            self._config.update(self._main_widget.get_config())
        return self._config.copy()

    def set_config(self, config):
        self._config.update(config)
        if self._main_widget:
            self._main_widget.set_config(config)
```

#### 步骤4：实现UI组件 (ui/main_widget.py)
```python
from PySide6.QtWidgets import QWidget
from qfluentwidgets import ExpandSettingCard

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
        
    def get_config(self):
        return {"setting1": "value1"}
        
    def set_config(self, config):
        # 应用配置到界面
        pass
        
    def cleanup(self):
        # 清理资源
        pass
```

### 2. 插件分类

插件按功能分为以下几类：

| 分类 | 枚举值 | 用途 |
|------|--------|------|
| Diagnostic | `PluginCategory.DIAGNOSTIC` | 诊断工具 |
| Communication | `PluginCategory.COMMUNICATION` | 通信工具 |
| Serial | `PluginCategory.SERIAL` | 串口工具 |
| Utilities | `PluginCategory.UTILITIES` | 实用工具 |
| Custom | `PluginCategory.CUSTOM` | 自定义工具 |

### 3. 配置管理

插件配置通过以下方式管理：

```python
# 获取配置
config = plugin.get_config()

# 设置配置
plugin.set_config({
    "input_path": "/path/to/input",
    "output_path": "/path/to/output",
    "enabled": True
})

# 配置持久化由PluginManager自动处理
```

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
4. 导入每个插件模块
   ↓
5. 注册符合条件的插件类
   ↓
6. 初始化每个插件实例
   ↓
7. 插件准备就绪
```

## 最佳实践

### 1. 命名规范

- 插件目录名：使用小写字母和下划线，如 `ccp_tool`
- 插件类名：使用驼峰命名法，如 `CCPToolPlugin`
- 模块文件名：使用小写字母和下划线，如 `main_widget.py`

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
    self._config.clear()
    # 关闭数据库连接等
```

### 4. 日志记录

使用 loguru 记录插件相关日志：

```python
from loguru import logger

logger.info("插件加载成功")
logger.warning("配置项缺失")
logger.error("处理过程出错")
```

## 扩展性考虑

### 1. 热插拔支持
未来可扩展支持运行时动态加载/卸载插件

### 2. 插件市场
可扩展为在线插件市场，支持插件下载和更新

### 3. 权限管理
可为不同插件设置不同的访问权限

### 4. 依赖管理
完善的依赖解析和版本冲突处理

## 当前实现状态

✅ 已完成：
- 插件系统基础架构
- 标准插件目录结构
- CCP工具插件示例
- ToolsInterface 插件化改造

🔄 待完善：
- 更多工具插件迁移
- 插件配置持久化
- 插件间通信机制
- 插件市场前端界面

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

## 贡献指南

欢迎贡献新的插件！请遵循：
1. 使用标准插件结构
2. 编写单元测试
3. 提供完整的文档
4. 遵循代码风格规范