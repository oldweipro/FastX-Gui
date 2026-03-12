# FastX-Gui 插件开发规范

本文档详细说明了如何为 FastX-Gui 开发插件，包括接口规范、最佳实践和示例代码。

## 目录

1. [快速开始](#快速开始)
2. [插件基类说明](#插件基类说明)
3. [必须实现的接口](#必须实现的接口)
4. [推荐实现的接口](#推荐实现的接口)
5. [可选实现的接口](#可选实现的接口)
6. [插件元数据](#插件元数据)
7. [最佳实践](#最佳实践)
8. [完整示例](#完整示例)

---

## 快速开始

### 1. 创建插件目录结构

```
app/plugins/
└── my_plugin/
    ├── __init__.py
    ├── plugin.py          # 插件主类
    ├── manifest.json      # 插件配置文件
    ├── ui/                # UI 组件（可选）
    │   ├── __init__.py
    │   └── main_widget.py
    └── core/              # 核心逻辑（可选）
        └── ...
```

### 2. 编写 manifest.json

```json
{
  "name": "My Plugin",
  "version": "1.0.0",
  "description": "我的插件功能描述",
  "author": "作者名",
  "category": "utilities",
  "icon": "settings_20_filled",
  "main": "plugin:MyPlugin",
  "dependencies": [],
  "builtin": false
}
```

### 3. 实现插件类

```python
from app.plugins.plugin_base import PluginBase, PluginInfo, PluginCategory

class MyPlugin(PluginBase):
    @classmethod
    def get_plugin_info(cls) -> PluginInfo:
        return PluginInfo(
            name="My Plugin",
            version="1.0.0",
            description="我的插件功能描述",
            author="作者名",
            category=PluginCategory.UTILITIES,
            builtin=False,
        )
    
    def initialize(self) -> bool:
        # 初始化逻辑
        return True
    
    def get_main_widget(self, parent=None) -> QWidget:
        # 返回主界面组件
        return QWidget()
    
    def cleanup(self):
        # 清理资源
        pass
```

---

## 插件基类说明

所有插件必须继承 `PluginBase` 类，该类定义了完整的插件生命周期和接口规范。

### 核心特性

- **生命周期管理**: 框架自动管理插件的注册、初始化、激活、停用和卸载
- **配置持久化**: 支持插件配置的自动保存和加载
- **UI 集成**: 无缝集成到主界面的 Tab 系统
- **日志系统**: 支持独立日志或共享全局日志
- **国际化**: 支持多语言

---

## 必须实现的接口

以下接口使用 `@abstractmethod` 装饰，**必须**在子类中实现：

### 1. get_plugin_info() - 类方法

```python
@classmethod
def get_plugin_info(cls) -> PluginInfo:
    """返回插件元数据"""
    return PluginInfo(
        name="My Plugin",
        version="1.0.0",
        description="功能描述",
        author="Author",
        category=PluginCategory.UTILITIES,
        builtin=False,
    )
```

**调用时机**: 插件注册时（程序启动）  
**用途**: 提供插件的基本信息，用于显示在插件卡片上

### 2. initialize()

```python
def initialize(self) -> bool:
    """初始化插件"""
    try:
        # 读取配置
        self._config = self.get_config()
        
        # 预加载资源
        self._load_resources()
        
        # 连接数据库等
        self._setup_database()
        
        self._is_initialized = True
        return True
    except Exception as e:
        logger.error(f"插件初始化失败：{e}")
        return False
```

**调用时机**: 插件注册后、首次使用前（仅一次）  
**返回值**: `True` = 成功，`False` = 失败（插件不会被加载）  
**用途**: 初始化数据库、配置文件、预加载资源等

### 3. get_main_widget(parent)

```python
def get_main_widget(self, parent: Optional[QWidget] = None) -> QWidget:
    """返回插件主界面组件"""
    widget = MyMainWidget(self._config, parent)
    return widget
```

**调用时机**: 用户打开插件时  
**注意**: 每次调用应返回**新**的 QWidget 实例，避免 Qt 对象生命周期问题  
**用途**: 提供插件的主界面

### 4. cleanup()

```python
def cleanup(self):
    """释放插件占用的所有资源"""
    # 关闭数据库连接
    if hasattr(self, '_db'):
        self._db.close()
    
    # 关闭文件句柄
    # 停止线程
    # 其他清理工作
```

**调用时机**: 插件卸载或程序退出时  
**用途**: 清理资源，防止内存泄漏

---

## 推荐实现的接口

以下接口提供默认实现，但**强烈建议**根据需求覆盖：

### 1. get_settings_widget(parent)

```python
def get_settings_widget(self, parent: Optional[QWidget] = None) -> Optional[QWidget]:
    """返回插件设置界面"""
    return MySettingsWidget(self._config, parent)
```

**框架行为**: 用户点击「设置」按钮时调用，将返回的 widget 嵌入标准设置对话框

### 2. get_config()

```python
def get_config(self) -> Dict[str, Any]:
    """读取插件配置"""
    return {
        "timeout": 30,
        "auto_save": True,
        "theme": "light",
    }
```

**用途**: 从配置文件或注册表读取配置

### 3. set_config(config)

```python
def set_config(self, config: Dict[str, Any]):
    """写入插件配置"""
    # 保存到文件或注册表
    with open("config.json", "w") as f:
        json.dump(config, f, indent=2)
```

**用途**: 保存用户配置更改

---

## 可选实现的接口

以下接口根据插件功能选择性实现：

### 输入输出接口

#### on_input(channel, data)

```python
def on_input(self, channel: str, data: Any):
    """接收外部推送的数据"""
    if channel == "can_frame":
        self._process_can_frame(data)
    elif channel == "log":
        self._append_log(data)
```

**用途**: 接收其他插件或框架发送的数据

#### get_output(channel)

```python
def get_output(self, channel: str) -> Any:
    """向外部提供输出数据"""
    if channel == "result":
        return self._last_result
    return None
```

**用途**: 向其他插件提供数据

#### get_input_channels() / get_output_channels()

```python
def get_input_channels(self) -> List[str]:
    """返回支持的输入通道列表"""
    return ["can_frame", "log", "command"]

def get_output_channels(self) -> List[str]:
    """返回支持的输出通道列表"""
    return ["result", "status"]
```

### 文档接口

#### get_doc_url()

```python
def get_doc_url(self) -> Optional[str]:
    """返回文档 URL"""
    return "https://example.com/docs/my-plugin"
```

#### get_release_notes()

```python
def get_release_notes(self) -> Optional[str]:
    """返回 Release Notes 文本（Markdown 格式）"""
    return """
## v1.0.0

### 新功能
- 新增 XXX 功能
- 优化 YYY 性能

### Bug 修复
- 修复 ZZZ 问题
"""
```

#### get_doc_widget(parent)

```python
def get_doc_widget(self, parent: Optional[QWidget] = None) -> Optional[QWidget]:
    """返回内嵌文档面板"""
    return MyDocViewer(parent)
```

### 生命周期回调

#### on_activate()

```python
def on_activate(self):
    """插件激活时的回调（用户打开 Tab）"""
    logger.info("插件已激活")
    self._start_timer()
```

#### on_deactivate()

```python
def on_deactivate(self):
    """插件停用时的回调（用户关闭 Tab）"""
    logger.info("插件已停用")
    self._stop_timer()
```

#### on_tab_opened(tab_widget)

```python
def on_tab_opened(self, tab_widget: QWidget):
    """Tab 打开时的回调"""
    logger.info(f"Tab 已打开：{tab_widget.objectName()}")
```

#### on_tab_closed(tab_id)

```python
def on_tab_closed(self, tab_id: str):
    """Tab 关闭时的回调"""
    logger.info(f"Tab 已关闭：{tab_id}")
```

### 数据导入导出

#### export_data(path)

```python
def export_data(self, path: str) -> bool:
    """导出插件数据"""
    try:
        with open(path, "w") as f:
            json.dump(self._data, f, indent=2)
        return True
    except Exception:
        return False
```

#### import_data(path)

```python
def import_data(self, path: str) -> bool:
    """导入插件数据"""
    try:
        with open(path, "r") as f:
            self._data = json.load(f)
        return True
    except Exception:
        return False
```

### 快捷操作

#### get_quick_actions()

```python
def get_quick_actions(self) -> List[Dict[str, Any]]:
    """返回快捷操作列表"""
    return [
        {
            "name": "刷新数据",
            "icon": FIF.SYNC,
            "callback": self._refresh_data,
            "tooltip": "刷新所有数据",
        },
        {
            "name": "导出数据",
            "icon": FIF.EXPORT,
            "callback": self._export_data,
            "tooltip": "导出当前数据",
        },
    ]
```

### 状态栏

#### get_status_bar_widget(parent)

```python
def get_status_bar_widget(self, parent: Optional[QWidget] = None) -> Optional[QWidget]:
    """返回状态栏组件"""
    label = BodyLabel("就绪", parent)
    self._status_label = label
    return label
```

### 键盘快捷键

#### get_shortcuts()

```python
def get_shortcuts(self) -> List[Dict[str, Any]]:
    """返回快捷键列表"""
    return [
        {
            "key": "Ctrl+S",
            "description": "保存",
            "callback": self._save,
        },
        {
            "key": "Ctrl+R",
            "description": "刷新",
            "callback": self._refresh,
        },
    ]
```

---

## 插件元数据

### PluginInfo 字段说明

```python
@dataclass
class PluginInfo:
    name: str              # 插件唯一名称
    version: str           # 语义化版本号 "major.minor.patch"
    description: str       # 功能简述（显示在卡片上）
    author: str            # 作者 / 团队
    category: PluginCategory  # 分类
    icon_path: str = None  # 图标名称（可选）
    dependencies: List[str] = field(default_factory=list)  # Python 包依赖
    enabled: bool = True   # 运行时启用状态
    builtin: bool = False  # True = 内置插件，不可卸载
```

### PluginCategory 枚举

```python
class PluginCategory(Enum):
    DIAGNOSTIC    = "diagnostic"      # 诊断工具
    COMMUNICATION = "communication"   # 通信工具
    SERIAL        = "serial"          # 串口工具
    UTILITIES     = "utilities"       # 实用工具
    CUSTOM        = "custom"          # 自定义工具
```

---

## 最佳实践

### 1. 资源管理

```python
def initialize(self):
    # 使用上下文管理器
    self._context = ResourceManager()
    self._context.__enter__()
    return True

def cleanup(self):
    # 确保资源被释放
    if hasattr(self, '_context'):
        self._context.__exit__(None, None, None)
```

### 2. 错误处理

```python
def get_main_widget(self, parent=None):
    try:
        return MyWidget(self._config, parent)
    except Exception as e:
        logger.exception(f"创建界面失败：{e}")
        return ErrorWidget(str(e), parent)
```

### 3. 配置验证

```python
def set_config(self, config: Dict[str, Any]):
    # 验证配置
    if "timeout" in config and not isinstance(config["timeout"], int):
        raise ValueError("timeout 必须是整数")
    
    # 保存配置
    save_config(config)
```

### 4. 线程安全

```python
def on_input(self, channel: str, data: Any):
    # 在主线程中处理
    QMetaObject.invokeMethod(
        self,
        "_process_data",
        Qt.QueuedConnection,
        Q_ARG(str, channel),
        Q_ARG(object, data),
    )

@Slot(str, object)
def _process_data(self, channel: str, data: Any):
    # 实际处理逻辑
    pass
```

### 5. 内存管理

```python
def get_main_widget(self, parent=None):
    widget = MyWidget(parent)
    # 使用 weakref 避免循环引用
    import weakref
    widget._plugin_ref = weakref.ref(self)
    return widget
```

---

## 完整示例

### 简单插件示例

```python
"""
Simple Counter Plugin - 演示插件开发的完整流程
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel
from PySide6.QtCore import QTimer
from qfluentwidgets import FluentIcon as FIF
from app.plugins.plugin_base import PluginBase, PluginInfo, PluginCategory

class CounterWidget(QWidget):
    """计数器主界面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        
        self.label = QLabel("计数：0", self)
        self.button = QPushButton("增加", self)
        self.button.setIcon(FIF.ADD)
        
        layout.addWidget(self.label)
        layout.addWidget(self.button)
        
        self.count = 0
        self.button.clicked.connect(self._on_click)
    
    def _on_click(self):
        self.count += 1
        self.label.setText(f"计数：{self.count}")


class SimpleCounterPlugin(PluginBase):
    """简单计数器插件"""
    
    @classmethod
    def get_plugin_info(cls) -> PluginInfo:
        return PluginInfo(
            name="Simple Counter",
            version="1.0.0",
            description="一个简单的计数器插件示例",
            author="FastX Team",
            category=PluginCategory.UTILITIES,
            builtin=False,
        )
    
    def initialize(self) -> bool:
        self._count = 0
        self._is_initialized = True
        return True
    
    def get_main_widget(self, parent=None) -> QWidget:
        widget = CounterWidget(parent)
        return widget
    
    def cleanup(self):
        self._count = 0
    
    def get_config(self) -> dict:
        return {"initial_count": 0}
    
    def set_config(self, config: dict):
        self._initial_count = config.get("initial_count", 0)
    
    def get_settings_widget(self, parent=None):
        from qfluentwidgets import SpinBox
        
        widget = QWidget(parent)
        layout = QVBoxLayout(widget)
        
        label = QLabel("初始值:")
        self.spin_box = SpinBox()
        self.spin_box.setValue(self._initial_count)
        
        layout.addWidget(label)
        layout.addWidget(self.spin_box)
        
        return widget
    
    def get_quick_actions(self):
        return [
            {
                "name": "重置计数",
                "icon": FIF.SYNC,
                "callback": self._reset_count,
                "tooltip": "重置计数器",
            }
        ]
    
    def _reset_count(self):
        self._count = 0
```

---

## 常见问题

### Q: 如何在插件中使用信号槽？

```python
class MyWidget(QWidget):
    data_changed = Signal(dict)
    
    def __init__(self):
        super().__init__()
        self.data_changed.connect(self._on_data_changed)
```

### Q: 如何与其他插件通信？

通过插件管理器：

```python
plugin_manager = self.parent()  # 获取插件管理器
other_plugin = plugin_manager.get_plugin("OtherPluginName")
if other_plugin:
    data = other_plugin.get_output("channel_name")
```

### Q: 如何测试插件？

创建测试文件：

```python
def test_plugin_initialization():
    plugin = MyPlugin()
    assert plugin.initialize() == True
    assert plugin.is_initialized() == True
```

---

## 更新日志

- **v1.0.0** (2025-01-01): 初始版本，包含完整的插件开发规范
