from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFileDialog, QHBoxLayout, QInputDialog, QMessageBox, QVBoxLayout, QWidget
from qfluentwidgets import (
    ExpandSettingCard,
    PrimaryPushSettingCard,
    PushSettingCard,
    SwitchSettingCard, ScrollArea, FluentIconBase,
)
from qfluentwidgets import (
    FluentIcon as FIF,
)

from app.common.config import cfg
from app.common.icon import UnicodeIcon
from app.tools.core.rm_comments_core import RmCommentsCore


class QcCompositionUI(ExpandSettingCard):
    """Remove Comments UI class"""

    def __init__(
        self,
        icon: str | QIcon | FluentIconBase=None,
        title: str = None,
        content=None,
        parent=None,
    ):
        # 如果 icon 为 None，可以设置一个默认图标
        if icon is None:
            icon = UnicodeIcon.get_icon_by_name("ic_fluent_comment_dismiss_24_regular")
        # 如果 title 为空字符串，设置默认标题
        if not title:
            title = self.tr("QCraft Composition Arxml Adapter")
        # 如果 content 为空字符串，设置默认标题
        if content is None:
            content = self.tr("To Modify QCraft Composition Arxml File To FT Rules For J6")
        super().__init__(icon, title, content, parent)
        self.core = RmCommentsCore()
        self.__initCards()
        self.connectSignals()

    def __initCards(self):
        """
        初始化卡片
        """

        # 文件夹选择卡片
        self.rmCodeCommentsInputFolderCard = PushSettingCard(
            self.tr("Choose folder"),
            FIF.FOLDER_ADD,
            self.tr("Project Input Directory"),
            cfg.get(cfg.RmCommentsInputFolder)
        )

        # Execute button
        self.rmCodeCommentsExecuteCard = PrimaryPushSettingCard(
            self.tr("Execute"),
            FIF.PLAY,
            self.tr("Execute Code Comment Removal"),
            self.tr("Click to start processing")
        )

        # 添加卡片到布局
        self.__addCardsToLayout()

    def __addCardsToLayout(self):
        """
        添加卡片到布局
        """
        self.viewLayout.addWidget(self.rmCodeCommentsInputFolderCard)

        # Add execute button
        self.viewLayout.addWidget(self.rmCodeCommentsExecuteCard)

        self._adjustViewSize()

    def connectSignals(self):
        """
        连接信号
        """
        # 按钮 | 去除Python代码备注,空行
        self.rmCodeCommentsInputFolderCard.clicked.connect(
            lambda: self.__onChooseFolderClicked(cfg.RmCommentsInputFolder, self.rmCodeCommentsInputFolderCard)
        )

        # Execute button connection
        self.rmCodeCommentsExecuteCard.clicked.connect(self.__onExecuteRmCommentsClicked)

    def __onChooseFolderClicked(self, config_item, card):
        """
        通用文件夹选择方法

        Args:
            config_item: 配置项
            card: 卡片对象
        """
        folder = QFileDialog.getExistingDirectory(self, self.tr("Choose folder"), cfg.get(config_item))
        if not folder or cfg.get(config_item) == folder:
            return
        cfg.set(config_item, folder)
        card.setContent(folder)

    def __onSetValueClicked(self, config_item, card, title):
        """
        通用值设置方法

        Args:
            config_item: 配置项
            card: 卡片对象
            title: 对话框标题
        """
        current_value = cfg.get(config_item)
        value, ok = QInputDialog.getText(self, title, title, text=current_value)
        if ok and value != current_value:
            cfg.set(config_item, value)
            card.setContent(value)

    def __onExecuteRmCommentsClicked(self):
        """
        执行代码清理
        """
        try:
            # 显示结果
            message = self.tr("Processing completed!\n")
            QMessageBox.information(self, self.tr("Success"), message)
        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"), self.tr(f"Processing failed: {str(e)}"))
