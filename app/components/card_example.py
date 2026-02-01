# coding:utf-8
""" 可组装卡片系统示例 """
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout
from loguru import logger

from qfluentwidgets import (
    FluentIcon, PushButton, PrimaryPushButton, ComboBox,
    LineEdit, SwitchButton, BodyLabel, TitleLabel,
    CheckBox, RadioButton, HyperlinkLabel
)

from .flexible_card import CardBuilder


class CardExample(QWidget):
    """ 卡片示例类，展示如何使用可组装卡片系统 """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setSpacing(10)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 10)
        self.vBoxLayout.setAlignment(Qt.AlignTop)
        
        # 移除最大宽度限制，允许自动扩展
        from PyQt5.QtWidgets import QWIDGETSIZE_MAX
        self.setMaximumWidth(QWIDGETSIZE_MAX)
        
        # 确保Widget能自动填充父容器宽度
        from PyQt5.QtWidgets import QSizePolicy
        self.setSizePolicy(
            QSizePolicy.Expanding,  # 水平方向自动扩展
            QSizePolicy.Minimum      # 垂直方向最小大小
        )
        
        self._initWidgets()
    
    def _initWidgets(self):
        """ 初始化各种卡片示例 """
        
        # 1. 信息展示卡片示例
        self._createInfoCard()
        
        # 2. 配置卡片示例
        self._createConfigCard()
        
        # 3. 操作卡片示例
        self._createActionCard()
        
        # 4. 日志卡片示例
        self._createLogCard()
        
        # 5. 自定义组合卡片示例
        self._createCustomCard()
    
    def _createInfoCard(self):
        """ 创建信息展示卡片 """
        card = CardBuilder.createInfoCard(
            title="系统信息",
            description="这是一个信息展示卡片示例，用于展示系统状态、版本信息等。",
            parent=self
        )
        
        # 添加版本信息
        versionLayout = QHBoxLayout()
        versionLayout.setSpacing(20)
        versionLayout.addWidget(BodyLabel("版本: v1.0.0"))
        versionLayout.addWidget(BodyLabel("更新时间: 2026-01-20"))
        versionLayout.addWidget(BodyLabel("状态: 运行中"))
        card.addLayout(versionLayout)
        
        # 添加链接
        linkLabel = HyperlinkLabel(QUrl("https://github.com/fastxteam/FastX-Gui"), 
                                  "访问GitHub仓库", self)
        card.addWidget(linkLabel)
        
        # 添加底部按钮
        card.addToolBarWidget(PushButton("查看详情", self, FluentIcon.INFO))
        card.addToolBarWidget(PushButton("更新", self, FluentIcon.UPDATE))
        card.addToolBarStretch()
        card.addToolBarWidget(PushButton("关闭", self, FluentIcon.CLOSE))
        
        self.vBoxLayout.addWidget(card)
    
    def _createConfigCard(self):
        """ 创建配置卡片示例 """
        card = CardBuilder.createConfigCard("基本配置", self)
        
        # 添加配置项
        card.addGroup(
            icon=FluentIcon.SETTING,
            title="选择模式",
            content="请选择系统运行模式",
            widget=self._createModeComboBox()
        )
        
        card.addGroup(
            icon=FluentIcon.FOLDER,
            title="输出路径",
            content="D:/output",
            widget=PushButton("浏览", self)
        )
        
        card.addGroup(
            icon=FluentIcon.CHECKBOX,
            title="启用功能",
            content="是否启用高级功能",
            widget=SwitchButton(self)
        )
        
        # 添加底部工具栏
        card.addToolBarWidget(PrimaryPushButton("保存配置", self, FluentIcon.SAVE))
        card.addToolBarWidget(PushButton("重置", self, FluentIcon.SYNC))
        
        self.vBoxLayout.addWidget(card)
    
    def _createActionCard(self):
        """ 创建操作卡片示例 """
        card = CardBuilder.createActionCard(
            title="快速操作",
            actions=[
                {
                    "text": "开始",
                    "icon": FluentIcon.PLAY,
                    "width": 100,
                    "callback": lambda: logger.debug("开始操作")
                },
                {
                    "text": "暂停",
                    "icon": FluentIcon.PAUSE,
                    "width": 100
                },
                {
                    "text": "停止",
                    "icon": FluentIcon.CLOSE,
                    "width": 100
                }
            ],
            parent=self
        )
        
        self.vBoxLayout.addWidget(card)
    
    def _createLogCard(self):
        """ 创建日志卡片示例 """
        card = CardBuilder.createFlexibleCard("系统日志", self)
        
        # 添加日志内容
        from qfluentwidgets import PlainTextEdit
        logEdit = PlainTextEdit(self)
        logEdit.setPlainText(
            "[2026-01-20 10:00:00] 系统启动\n" +
            "[2026-01-20 10:00:05] 加载配置文件成功\n" +
            "[2026-01-20 10:00:10] 初始化组件完成\n" +
            "[2026-01-20 10:00:15] 系统准备就绪\n"
        )
        logEdit.setMinimumHeight(150)
        card.addWidget(logEdit)
        
        # 添加日志控制按钮
        logLayout = QHBoxLayout()
        logLayout.setSpacing(10)
        logLayout.addWidget(PushButton("清空日志", self, FluentIcon.DELETE))
        logLayout.addWidget(PushButton("导出日志", self, FluentIcon.SHARE))
        logLayout.addWidget(PushButton("刷新", self, FluentIcon.SYNC))
        card.addLayout(logLayout)
        
        self.vBoxLayout.addWidget(card)
    
    def _createCustomCard(self):
        """ 创建自定义组合卡片示例 """
        card = CardBuilder.createFlexibleCard("自定义组合示例", self)
        
        # 添加标题
        subTitle = TitleLabel("组件组合演示", self)
        card.addWidget(subTitle)
        
        # 添加复选框组
        checkboxGroup = QVBoxLayout()
        checkboxGroup.setSpacing(8)
        checkboxGroup.addWidget(CheckBox("选项1", self))
        checkboxGroup.addWidget(CheckBox("选项2", self))
        checkboxGroup.addWidget(CheckBox("选项3", self))
        card.addLayout(checkboxGroup)
        
        # 添加单选按钮组
        radioGroup = QVBoxLayout()
        radioGroup.setSpacing(8)
        radioGroup.addWidget(RadioButton("选项A", self))
        radioGroup.addWidget(RadioButton("选项B", self))
        radioGroup.addWidget(RadioButton("选项C", self))
        card.addLayout(radioGroup)
        
        # 添加输入框
        lineEdit = LineEdit(self)
        lineEdit.setPlaceholderText("请输入文本...")
        card.addWidget(lineEdit)
        
        # 添加底部按钮
        card.addToolBarWidget(PrimaryPushButton("提交", self, FluentIcon.SEND))
        card.addToolBarWidget(PushButton("取消", self, FluentIcon.CANCEL))
        
        self.vBoxLayout.addWidget(card)
    
    def _createModeComboBox(self):
        """ 创建模式选择下拉框 """
        comboBox = ComboBox(self)
        comboBox.addItem("简单模式")
        comboBox.addItem("高级模式")
        comboBox.addItem("自定义模式")
        comboBox.setMinimumWidth(150)
        return comboBox
