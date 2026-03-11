import sys
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTreeWidget, QTreeWidgetItem, QLabel, QGridLayout, QTableWidget,
    QTableWidgetItem, QHeaderView, QGroupBox, QFrame, QScrollArea
)
from qfluentwidgets import (
    SearchLineEdit, FluentWindow, FluentIcon as FIF,
    setTheme, Theme, TitleLabel, SubtitleLabel, BodyLabel,
    StrongBodyLabel, TableView, CheckBox, PushButton
)


class DeviceInspectionDemo(FluentWindow):
    """主窗口，继承自 FluentWindow 以获得 Fluent 风格"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("设备开箱检验记录 - Fluent Demo")
        self.resize(1200, 800)

        # 创建左侧导航和右侧界面
        self.createLeftPanel()
        self.createRightPanel()

        # 将两个面板添加到堆栈窗口中（FluentWindow 提供了堆栈导航，我们直接添加到中心区域）
        # 这里简单地将它们放在一个水平布局中，覆盖默认的堆栈导航
        centralWidget = QWidget()
        layout = QHBoxLayout(centralWidget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        layout.addWidget(self.leftPanel, 1)
        layout.addWidget(self.rightPanel, 2)
        self.centralWidget = centralWidget
        # 替换原有的中心部件
        self.stackedWidget.addWidget(centralWidget)   # FluentWindow 中心是 QStackedWidget
        # 设置初始索引
        self.stackedWidget.setCurrentWidget(centralWidget)

    def createLeftPanel(self):
        """左侧设备记录列表（带搜索和复选框）"""
        self.leftPanel = QFrame()
        self.leftPanel.setObjectName("leftPanel")
        self.leftPanel.setMaximumWidth(350)
        layout = QVBoxLayout(self.leftPanel)
        layout.setSpacing(10)

        # 搜索框
        self.searchBox = SearchLineEdit()
        self.searchBox.setPlaceholderText("输入关键字搜索")
        self.searchBox.setClearButtonEnabled(True)
        self.searchBox.setMaximumHeight(36)
        layout.addWidget(self.searchBox)

        # 树形记录列表（带复选框）
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(20)
        self.tree.setStyleSheet("""
            QTreeWidget::item {
                padding: 4px;
                border-bottom: 1px solid #f0f0f0;
            }
            QTreeWidget::item:selected {
                background-color: #e0f0ff;
            }
        """)

        # 添加根节点：001. 设备开箱记录
        root_item = QTreeWidgetItem(["001. 设备开箱记录"])
        root_item.setFlags(root_item.flags() | Qt.ItemIsUserCheckable)
        root_item.setCheckState(0, Qt.Unchecked)
        root_item.setExpanded(True)   # 默认展开

        # 添加子节点：G4-010001 ~ G4-010010
        for i in range(1, 11):
            child = QTreeWidgetItem([f"G4-01000{i} - 设备开箱记录"])
            child.setFlags(child.flags() | Qt.ItemIsUserCheckable)
            child.setCheckState(0, Qt.Unchecked)
            root_item.addChild(child)

        self.tree.addTopLevelItem(root_item)

        # 添加更多测试根节点（示例）
        root_item2 = QTreeWidgetItem(["002. 检验批质量验收记录"])
        root_item2.setFlags(root_item2.flags() | Qt.ItemIsUserCheckable)
        root_item2.setCheckState(0, Qt.Unchecked)
        self.tree.addTopLevelItem(root_item2)

        layout.addWidget(self.tree)

        # 底部统计按钮（可选）
        btnLayout = QHBoxLayout()
        btnLayout.addStretch()
        selectAllBtn = PushButton("全选")
        deselectAllBtn = PushButton("取消全选")
        btnLayout.addWidget(selectAllBtn)
        btnLayout.addWidget(deselectAllBtn)
        layout.addLayout(btnLayout)

        # 信号连接（示例功能）
        selectAllBtn.clicked.connect(self.selectAll)
        deselectAllBtn.clicked.connect(self.deselectAll)

    def createRightPanel(self):
        """右侧详细检验记录表单"""
        self.rightPanel = QFrame()
        self.rightPanel.setObjectName("rightPanel")
        layout = QVBoxLayout(self.rightPanel)
        layout.setSpacing(15)

        # 标题
        titleLabel = TitleLabel("设备开箱检验记录")
        layout.addWidget(titleLabel)

        # 基础信息表格（使用网格布局）
        infoGroup = QGroupBox("基本信息")
        grid = QGridLayout(infoGroup)
        grid.setVerticalSpacing(10)
        grid.setHorizontalSpacing(20)

        # 第一行
        grid.addWidget(StrongBodyLabel("工程名称:"), 0, 0)
        grid.addWidget(BodyLabel("打孔工程"), 0, 1)
        grid.addWidget(StrongBodyLabel("资料编号:"), 0, 2)
        grid.addWidget(BodyLabel("IV-G4-11000006"), 0, 3)

        # 第二行
        grid.addWidget(StrongBodyLabel("设备名称:"), 1, 0)
        grid.addWidget(BodyLabel("设备_06"), 1, 1)
        grid.addWidget(StrongBodyLabel("检查日期:"), 1, 2)
        grid.addWidget(BodyLabel("2025年12月06日"), 1, 3)

        # 第三行
        grid.addWidget(StrongBodyLabel("规格型号:"), 2, 0)
        grid.addWidget(BodyLabel("型号_06"), 2, 1)
        grid.addWidget(StrongBodyLabel("生产厂家:"), 2, 2)
        grid.addWidget(BodyLabel("6.有限公司"), 2, 3)

        # 第四行
        grid.addWidget(StrongBodyLabel("产品合格证编号:"), 3, 0)
        grid.addWidget(BodyLabel("M-006"), 3, 1)
        grid.addWidget(StrongBodyLabel("数量:"), 3, 2)
        grid.addWidget(BodyLabel("1台"), 3, 3)

        layout.addWidget(infoGroup)

        # 随机文件表格
        fileGroup = QGroupBox("随机文件的份数是否齐全")
        fileLayout = QVBoxLayout(fileGroup)
        self.fileTable = QTableWidget()
        self.fileTable.setColumnCount(6)
        self.fileTable.setHorizontalHeaderLabels(["序号", "备件名称", "规格型号", "单位", "数量", "备注"])
        self.fileTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.fileTable.setRowCount(2)

        # 填充数据
        data = [
            ["1", "设备铭牌", "1份", "齐全", "", ""],
            ["2", "质量合格证明", "1份", "齐全", "", ""]
        ]
        for row, items in enumerate(data):
            for col, text in enumerate(items):
                self.fileTable.setItem(row, col, QTableWidgetItem(text))
        fileLayout.addWidget(self.fileTable)
        layout.addWidget(fileGroup)

        # 缺、损备件表格
        lossGroup = QGroupBox("缺、损备件与附件明细")
        lossLayout = QVBoxLayout(lossGroup)
        self.lossTable = QTableWidget()
        self.lossTable.setColumnCount(6)
        self.lossTable.setHorizontalHeaderLabels(["序号", "备件名称", "规格型号", "单位", "数量", "备注"])
        self.lossTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.lossTable.setRowCount(0)   # 无数据
        lossLayout.addWidget(self.lossTable)
        layout.addWidget(lossGroup)

        # 底部占位
        layout.addStretch()

        # 为了适应内容，放入滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.rightPanel)
        self.rightPanel = scroll

    def selectAll(self):
        """全选根节点及其子节点（示例）"""
        root = self.tree.topLevelItem(0)
        if root:
            root.setCheckState(0, Qt.Checked)
            for i in range(root.childCount()):
                root.child(i).setCheckState(0, Qt.Checked)

    def deselectAll(self):
        """取消全选"""
        root = self.tree.topLevelItem(0)
        if root:
            root.setCheckState(0, Qt.Unchecked)
            for i in range(root.childCount()):
                root.child(i).setCheckState(0, Qt.Unchecked)


if __name__ == "__main__":
    # 启用高 DPI 支持
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)

    # 设置主题（可选：浅色/深色）
    setTheme(Theme.LIGHT)

    w = DeviceInspectionDemo()
    w.show()

    sys.exit(app.exec_())