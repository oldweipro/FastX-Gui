import numpy as np
from PIL import Image
from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QDesktopServices, QImage, QPainter, QPainterPath, QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    ComboBox,
    GroupHeaderCardWidget,
    HyperlinkButton,
    IconWidget,
    ImageLabel,
    InfoBarIcon,
    PrimaryPushButton,
    PushButton,
    SpinBox,
    SwitchButton,
    ScrollArea,
    FluentIcon as FIF,
)
from app.common.icon import JPG, PNG, UIcon
from app.common.setting import (
    ARCH,
    AUTHOR,
    BILIBILI_WEB,
    CODENAME,
    COPYRIGHT_HOLDER,
    CURRENT_YEAR,
    DONATION_URL,
    INITIAL_AUTHORING_YEAR,
    REPO_URL,
    SPECIAL_VERSION,
    SYSTEM,
)
from app.common import resource
from app.common.style_sheet import StyleSheet


class BannerWidgetHomeIF1(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        banner_path = JPG.path(JPG.BACKGROUND_2)
        self.banner_image = ImageLabel(QImage(banner_path))
        self.banner_image.scaledToHeight(400)
        self.banner_image.setBorderRadius(12, 12, 12, 12)
        self.banner_image.setScaledContents(True)

        # 添加横幅图片到布局
        self.vBoxLayout = QHBoxLayout(self)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setSpacing(0)

        # 使图片居中
        self.vBoxLayout.addWidget(self.banner_image, 0, Qt.AlignmentFlag.AlignCenter)


class BannerWidgetHomeIF2(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setFixedHeight(320)
        self.setMaximumHeight(320)

        self.main_layout = QVBoxLayout(self)
        self.galleryLabel = QLabel("", self)
        self.galleryLabel.setStyleSheet("color: white;font-size: 30px; font-weight: 600;")
        # self.banner = QPixmap('./app/resource/images/bg37.jpg')
        self.img = Image.open("./app/resource/images/jpg/background2.jpg")
        self.banner = None
        self.path = None

        # 创建阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)  # 阴影模糊半径
        shadow.setColor(Qt.black)  # 阴影颜色
        shadow.setOffset(1.2, 1.2)  # 阴影偏移量

        # 将阴影效果应用于小部件
        self.galleryLabel.setGraphicsEffect(shadow)
        self.galleryLabel.setObjectName("galleryLabel")

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
            crop_area = (
                0,
                0,
                self.img.width,
                image_height,
            )  # (left, upper, right, lower)
            cropped_img = self.img.crop(crop_area)
            img_data = np.array(cropped_img)  # Convert PIL Image to numpy array
            height, width, channels = img_data.shape
            bytes_per_line = channels * width
            self.banner = QImage(
                img_data.data,
                width,
                height,
                bytes_per_line,
                QImage.Format_RGB888,
            )

            path = QPainterPath()
            path.addRoundedRect(0, 0, width + 50, height + 50, 10, 10)  # 10 is the radius for corners
            self.path = path.simplified()

        painter.setClipPath(self.path)
        painter.drawImage(self.rect(), self.banner)


class BannerWidgetHomeIF3(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setFixedHeight(320)
        self.setMaximumHeight(320)

        self.main_layout = QVBoxLayout(self)
        self.galleryLabel = QLabel("", self)
        self.galleryLabel.setStyleSheet("color: white;font-size: 30px; font-weight: 600;")

        # 从 Qt 资源加载图片到 PIL Image
        self.img = self.load_image_from_qrc(":/app/images/jpg/background2.jpg")
        self.banner = None
        self.path = None

        # 创建阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(Qt.black)
        shadow.setOffset(1.2, 1.2)

        self.galleryLabel.setGraphicsEffect(shadow)
        self.galleryLabel.setObjectName("galleryLabel")

        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 20, 0, 0)
        self.main_layout.addWidget(self.galleryLabel)
        self.main_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)

    def load_image_from_qrc(self, qrc_path):
        """
        从 Qt 资源路径加载图片到 PIL Image

        Args:
            qrc_path: Qt 资源路径，如 ":/app/images/jpg/background2.jpg"

        Returns:
            PIL.Image 对象，如果加载失败则返回 None
        """
        from PySide6.QtCore import QFile, QIODevice
        import io

        # 创建 QFile 对象读取资源
        file = QFile(qrc_path)
        if not file.open(QIODevice.ReadOnly):
            print(f"无法打开资源: {qrc_path}")
            return None

        # 读取所有数据
        data = file.readAll()
        file.close()

        try:
            # 将二进制数据转换为 PIL Image
            img = Image.open(io.BytesIO(data))
            return img
        except Exception as e:
            print(f"图片加载失败: {e}")
            return None

    def paintEvent(self, e):
        super().paintEvent(e)
        painter = QPainter(self)
        painter.setRenderHints(QPainter.SmoothPixmapTransform | QPainter.Antialiasing)

        if not self.banner or not self.path:
            if self.img is None:
                return  # 图片加载失败，不绘制

            image_height = self.img.width * self.height() // self.width()
            crop_area = (
                0,
                0,
                self.img.width,
                image_height,
            )
            cropped_img = self.img.crop(crop_area)

            # 确保图片是 RGB 模式
            if cropped_img.mode != 'RGB':
                cropped_img = cropped_img.convert('RGB')

            img_data = np.array(cropped_img)
            height, width, channels = img_data.shape
            bytes_per_line = channels * width
            self.banner = QImage(
                img_data.data,
                width,
                height,
                bytes_per_line,
                QImage.Format_RGB888,
            )

            path = QPainterPath()
            path.addRoundedRect(0, 0, width + 50, height + 50, 10, 10)
            self.path = path.simplified()

        if self.banner:
            painter.setClipPath(self.path)
            painter.drawImage(self.rect(), self.banner)

class TypewriterLabelHomeIF(QLabel):
    def __init__(self, parent=None):
        super(TypewriterLabelHomeIF, self).__init__(parent)
        self.texts = [
            "Welcome to use FastXGui. \nThis software is currently in the initial testing stage.\nThe only open function is FastRte. \nMore functions will be developed in the future.💕"
        ]
        self.index = 0
        self.char_index = 0
        self.cursor_visible = True
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_label)
        self.timer.start(90)

    def update_label(self):
        if self.char_index > len(self.texts[self.index]):
            if self.index + 1 >= len(self.texts):
                self.timer.stop()
                return
            # 如果已经打印完一行，就打印下一行
            self.index = (self.index + 1) % len(self.texts)
            self.char_index = 0
        text = self.texts[self.index][: self.char_index]
        if self.cursor_visible:
            text += "|"
        else:
            text += " "
        self.setText(text)
        self.cursor_visible = not self.cursor_visible
        self.char_index += 1

class AboutInfoHomeIf(GroupHeaderCardWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle(self.tr("About"))
        self.setBorderRadius(8)

        # 打开 bilibili 按钮
        self.about_bilibili_Button = HyperlinkButton(
            UIcon.get("ic_fluent_globe_20_regular"),
            BILIBILI_WEB,
            self.tr("Bilibili"),
        )
        bilibili_widget = self._create_button_with_icon(self.about_bilibili_Button, PNG.path(PNG.SHAKA_PACKAGER))

        # 查看当前软件版本号
        version_text = f"{SPECIAL_VERSION} | {CODENAME} ({SYSTEM}-{ARCH})"
        self.about_version_label = BodyLabel(version_text)

        # 打开 GitHub 按钮
        self.about_github_Button = HyperlinkButton(FIF.GITHUB, REPO_URL, self.tr("GitHub"))
        github_widget = self._create_button_with_icon(self.about_github_Button, PNG.path(PNG.SHAKA_PACKAGER))

        # 查看当前软件版权所属
        # 根据发布年份和当前年份是否相同，决定显示格式
        if INITIAL_AUTHORING_YEAR == CURRENT_YEAR:
            copyright_text = f"Copyright © {INITIAL_AUTHORING_YEAR} {AUTHOR}/{COPYRIGHT_HOLDER}"
        else:
            copyright_text = f"Copyright © {INITIAL_AUTHORING_YEAR}-{CURRENT_YEAR} {AUTHOR}/{COPYRIGHT_HOLDER}"

        self.about_author_label = BodyLabel(copyright_text)
        copyright_widget = self._create_label_with_icon(self.about_author_label, PNG.path(PNG.SHAKA_PACKAGER))

        # 创建贡献人员按钮
        self.contributor_button = PushButton(
            self.tr("Contributor"),
        )
        self.contributor_button.setIcon(UIcon.get("ic_fluent_people_20_regular"))
        self.contributor_button.clicked.connect(self.show_contributors)

        # 创建捐赠支持按钮
        self.donation_button = PushButton(self.tr("Donation"))
        self.donation_button.setIcon(UIcon.get("ic_fluent_gift_20_regular"))
        self.donation_button.clicked.connect(self.open_donation_url)

        self.addGroup(
            UIcon.get("ic_fluent_link_20_regular"),
            self.tr("bilibili"),
            self.tr("open wanqiang.liu's personal bilibili homepage"),
            bilibili_widget,
        )

        self.addGroup(
            FIF.GITHUB,
            self.tr("github"),
            self.tr("open code repository"),
            github_widget,
        )

        self.addGroup(
            UIcon.get("ic_fluent_people_20_regular"),
            self.tr("Contributor"),
            self.tr("view details of contributor lists"),
            self.contributor_button,
        )

        self.addGroup(
            UIcon.get("ic_fluent_gift_20_regular"),
            self.tr("Donation"),
            self.tr("support project development, thanks for your sponser"),
            self.donation_button,
        )

        self.addGroup(
            UIcon.get("ic_fluent_shield_checkmark_20_regular"),
            self.tr("Copyright"),
            self.tr("FastXGui GPL-3.0 license"),
            copyright_widget,
        )

        self.addGroup(
            UIcon.get("ic_fluent_number_123_20_regular"),
            self.tr("version"),
            self.tr("show current software version"),
            self.about_version_label,
        )

    def _create_button_with_icon(self, button, icon):
        """创建带图标的按钮容器"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        layout.addWidget(button)

        icon_label = ImageLabel(icon)
        icon_label.scaledToHeight(30)
        icon_label.setBorderRadius(8, 8, 8, 8)
        layout.addWidget(icon_label)

        layout.addStretch()
        return widget

    def _create_label_with_icon(self, label, icon):
        """创建带图标的标签容器"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        layout.addWidget(label)

        icon_label = ImageLabel(icon)
        icon_label.scaledToHeight(30)
        icon_label.setBorderRadius(8, 8, 8, 8)
        layout.addWidget(icon_label)

        layout.addStretch()
        return widget

    def show_contributors(self):
        """显示贡献人员"""
        QDesktopServices.openUrl(QUrl(REPO_URL))

    def open_donation_url(self):
        """打开捐赠链接"""
        QDesktopServices.openUrl(QUrl(DONATION_URL))


class HomeInterface(ScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.view = QWidget(self)
        self.banner = BannerWidgetHomeIF3(self.view)
        self.about = AboutInfoHomeIf()
        self.__initWidget()
        self.__initLayout()
        self.loadSamples()
        self.__connectSignalToSlot()

    def __initWidget(self):
        self.setViewportMargins(0, 48, 0, 0)
        self.setObjectName("homeInterface")
        self.view.setObjectName("view")
        StyleSheet.HOME_INTERFACE.apply(self)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWidget(self.view)
        self.setWidgetResizable(True)

    def __initLayout(self):
        # Create Layouts
        self.Layout = QHBoxLayout(self.view)
        self.Layout.setContentsMargins(0, 0, 20, 0)

        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(10, 0, 0, 0)
        self.main_layout.setSpacing(25)
        self.main_layout.setAlignment(Qt.AlignTop)

        self.top_layout = QVBoxLayout()
        self.top_layout.setContentsMargins(0, 0, 0, 0)

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
        self.top_layout.addWidget(self.about)
        # self.main_layout.addLayout(self.bottom_layout)

    def loadSamples(self):
        pass

    def __connectSignalToSlot(self):
        pass
