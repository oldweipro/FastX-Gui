# coding: utf-8
from enum import Enum

from qfluentwidgets import StyleSheetBase, Theme, isDarkTheme, qconfig


class StyleSheet(StyleSheetBase, Enum):
    """ Style sheet  """

    MAIN_WINDOW = "main_window"
    LINK_CARD = "link_card"
    SAMPLE_CARD = "sample_card"
    HOME_INTERFACE = "home_interface"
    APP_INTERFACE = "app_interface"
    ICON_INTERFACE = "icon_interface"
    VIEW_INTERFACE = "view_interface"
    RTE_INTERFACE = "rte_interface"
    SETTING_INTERFACE = "setting_interface"
    GALLERY_INTERFACE = "gallery_interface"
    LIBRARY_VIEW_INTERFACE = "library_view_interface"

    def path(self, theme=Theme.AUTO):

        theme = qconfig.theme if theme == Theme.AUTO else theme

        # 使用资源路径格式，注意资源文件中没有resource目录
        # return f":/app/qss/{theme.value.lower()}/{self.value}.qss"
        return f"./app/resource/qss/{theme.value.lower()}/{self.value}.qss"
