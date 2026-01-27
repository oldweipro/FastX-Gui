from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot, QRectF
from PyQt5.QtGui import QPixmap, QPainter, QColor, QBrush, QPainterPath, QLinearGradient, QImage
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QGraphicsDropShadowEffect, QSpacerItem, \
    QSizePolicy
from qfluentwidgets import TextEdit, SwitchButton, IndicatorPosition, PushButton, TitleLabel, BodyLabel, \
    PrimaryPushSettingCard, SubtitleLabel, ScrollArea, isDarkTheme, InfoBar, InfoBarIcon, InfoBarPosition
from qfluentwidgets import FluentIcon as FIF
from PIL import Image
import numpy as np

from app.card.public_card import GuideWidget
from app.common.icon import PNG, Icon
from app.components.link_card import LinkCardView
from app.common.style_sheet import StyleSheet
from app.components.type_writer import TypewriterLabel


class BannerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setFixedHeight(320)
        self.setMaximumHeight(320)

        self.main_layout = QVBoxLayout(self)
        self.galleryLabel = QLabel(f'', self)
        self.galleryLabel.setStyleSheet("color: white;font-size: 30px; font-weight: 600;")
        # self.banner = QPixmap('./app/resource/images/bg37.jpg')
        self.img = Image.open("./app/resource/images/bg37.jpg")
        self.banner = None
        self.path = None

        # 创建阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)  # 阴影模糊半径
        shadow.setColor(Qt.black)  # 阴影颜色
        shadow.setOffset(1.2, 1.2)     # 阴影偏移量

        # 将阴影效果应用于小部件
        self.galleryLabel.setGraphicsEffect(shadow)
        self.galleryLabel.setObjectName('galleryLabel')

        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 20, 0, 0)
        self.main_layout.addWidget(self.galleryLabel)
        self.main_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)

    def paintEvent(self, e):
        super().paintEvent(e)
        painter = QPainter(self)
        painter.setRenderHints(QPainter.SmoothPixmapTransform | QPainter.Antialiasing)

        if not self.banner or not self.path:
            image_height = self.img.width * self.height() // self.width()
            crop_area = (0, 0, self.img.width, image_height)  # (left, upper, right, lower)
            cropped_img = self.img.crop(crop_area)
            img_data = np.array(cropped_img)  # Convert PIL Image to numpy array
            height, width, channels = img_data.shape
            bytes_per_line = channels * width
            self.banner = QImage(img_data.data, width, height, bytes_per_line, QImage.Format_RGB888)

            path = QPainterPath()
            path.addRoundedRect(0, 0, width + 50, height + 50, 10, 10)  # 10 is the radius for corners
            self.path = path.simplified()

        painter.setClipPath(self.path)
        painter.drawImage(self.rect(), self.banner)


class HomeInterface(ScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.view = QWidget(self)
        self.banner = BannerWidget(self.view)
        self.intro = TypewriterLabel()
        self.__initWidget()
        self.__initLayout()
        self.loadSamples()
        self.__connectSignalToSlot()

    def __initWidget(self):
        self.setObjectName(f"homeInterface")
        self.view.setObjectName('view')
        StyleSheet.HOME_INTERFACE.apply(self)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWidget(self.view)
        self.setWidgetResizable(True)

    def __initLayout(self):
        # Create Layouts
        self.Layout = QHBoxLayout(self.view)
        self.Layout.setContentsMargins(0, 48, 0, 0)

        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(25)
        self.main_layout.setAlignment(Qt.AlignTop)

        self.top_layout = QVBoxLayout()
        self.top_layout.setContentsMargins(10, 0, 0, 0)

        self.guide_layout = QVBoxLayout()
        self.guide_layout.setContentsMargins(20, 20, 20, 20)

        self.bottom_layout = QHBoxLayout()
        self.bottom_layout.setContentsMargins(20, 20, 20, 20)
        self.bottom_layout.setSpacing(12)


        # Add Layouts
        self.Layout.addLayout(self.main_layout)
        self.main_layout.addWidget(self.banner)
        self.main_layout.addLayout(self.top_layout)
        self.main_layout.addLayout(self.guide_layout)
        self.top_layout.addWidget(self.intro)
        # self.main_layout.addLayout(self.bottom_layout)
    def loadSamples(self):
        pass

    def __connectSignalToSlot(self):
        pass