# DEM 故障分析器插件

基于 AUTOSAR CP DEM 的 DTC 故障状态分析工具

## 功能特性

- ✅ DTC 状态码解析（支持 0x6C 或 6C 格式）
- ✅ 8 个状态位的可视化展示
- ✅ 置位/复位状态详细分析
- ✅ 符合 AUTOSAR CP DEM 规范
- ✅ 现代化的 QFluentWidgets UI 界面

## 安装说明

本插件已集成到 FastX-Gui 项目中，位于：
```
app/plugins/fast_dem_fault_analyzer/
```

## 使用方法

1. **启动 FastX-Gui**

2. **打开插件管理界面**
   - 在主界面导航到"插件"页面
   
3. **启用插件**
   - 在插件列表中找到"DEM 故障分析器"
   - 点击开关启用插件

4. **使用分析功能**
   - 点击插件卡片打开分析界面
   - 输入 DTC 状态码（如：`0x6C` 或 `6C`）
   - 点击"分析"按钮
   - 查看详细的状态位解析结果

## 状态位说明

### Bit 0 - testFailed (TF)
请求时刻测试结果为失败

### Bit 1 - testFailedThisOperationCycle (TFTOC)
在当前点火循环至少失败 1 次

### Bit 2 - pendingDTC (PDTC)
在当前或者上一个点火循环测试结果不为失败

### Bit 3 - confirmedDTC (CDTC)
请求时刻 DTC 被确认，一般确认是在一个点火周期内发生错误 1 次

### Bit 4 - testNotCompleteSinceLastClear (TNCSLC)
自上次清除 DTC 之后测试结果已完成，即测试结果为 PASS 或者 FAIL

### Bit 5 - testFailedSinceLastClear (TFSLC)
自上次清除 DTC 后测试结果都不是 FAIL

### Bit 6 - testNotCompletedThisOperationCycle (TNCTOC)
在当前点火周期内测试结果已完成，即为 PASS 或 FAIL 状态

### Bit 7 - warningIndicatorRequested (WIR)
ECU 没有得到点亮警示灯请求

## 技术架构

```
fast_dem_fault_analyzer/
├── plugin.py              # 插件主入口（继承 PluginBase）
├── __init__.py           # 包初始化
├── manifest.json         # 插件配置文件
├── core/
│   ├── __init__.py
│   └── dem_fault_analyzer.py  # 核心业务逻辑
└── ui/
    ├── __init__.py
    └── dem_fault_card.py      # UI 组件（QFluentWidgets）
```

## 开发说明

### 依赖项

- Python >= 3.8
- PySide6
- qfluentwidgets

### 扩展功能

如需添加更多功能，可以：

1. **添加新的分析方法**
   - 在 `core/dem_fault_analyzer.py` 中添加新方法
   
2. **自定义 UI 组件**
   - 在 `ui/` 目录下创建新的 Widget
   - 使用 QFluentWidgets 提供的组件

3. **配置持久化**
   - 实现 `get_config()` 和 `set_config()` 方法

## 版本历史

### v0.1.11
- ✅ 初始版本发布
- ✅ 基础 DTC 状态分析功能
- ✅ QFluentWidgets UI 适配
- ✅ 完整的状态位解析

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

---

**作者**: FastX Team  
**最后更新**: 2025-12-27
