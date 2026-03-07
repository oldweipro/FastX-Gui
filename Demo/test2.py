import sys
import os
import tempfile
from pathlib import Path
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QAction
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTreeWidget, QTreeWidgetItem, QLabel, QGridLayout, QTableWidget,
    QTableWidgetItem, QHeaderView, QGroupBox, QFrame, QScrollArea,
    QTextEdit, QLineEdit, QComboBox, QPushButton,
    QFileDialog, QFormLayout, QMessageBox
)
from qfluentwidgets import (
    SearchLineEdit, FluentWindow, setTheme, Theme,
    TitleLabel, SubtitleLabel, BodyLabel, StrongBodyLabel,
    PushButton, PrimaryPushButton, InfoBar,
    LineEdit, TextEdit, ComboBox,
    SimpleCardWidget, HorizontalSeparator,
    Action, RoundMenu
)

# 尝试导入Spire.Doc
SPIRE_AVAILABLE = False
SPIRE_VERSION = None
try:
    from spire.doc import Document, FileFormat, ImageType

    # 尝试获取版本信息
    try:
        import spire
        SPIRE_VERSION = getattr(spire, '__version__', 'Unknown')
    except:
        pass

    # 尝试导入，如果不成功则标记为不可用
    SPIRE_AVAILABLE = True
    print(f"Spire.Doc 导入成功 (版本: {SPIRE_VERSION or 'Unknown'})")
except ImportError as e:
    print(f"Spire.Doc未安装或导入失败: {e}")
    print("将使用模拟模式运行")


class DTCTemplateManager:
    """DTC模板管理器 - 负责Word模板的填充和转换"""

    def __init__(self, template_path=None):
        self.template_path = template_path or self._get_default_template()
        self.temp_dir = tempfile.mkdtemp(prefix="dtc_preview_")

    def _get_default_template(self):
        """获取默认模板路径（如果没有则创建示例模板）"""
        template_dir = Path("./templates")
        template_dir.mkdir(exist_ok=True)
        template_file = template_dir / "dtc_template.docx"

        if not template_file.exists():
            self._create_sample_template(str(template_file))

        return str(template_file)

    def _create_sample_template(self, save_path):
        """创建一个示例Word模板"""
        if not SPIRE_AVAILABLE:
            # 模拟模式：创建一个空文件
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write("这是一个模拟的Word模板文件\n")
                f.write("实际使用时请安装Spire.Doc")
            print(f"模拟模板已创建: {save_path}")
            return

        try:
            print(f"开始创建模板: {save_path}")
            doc = Document()
            print("Document对象创建成功")

            # 添加标题
            section = doc.AddSection()
            print("Section添加成功")
            
            title_para = section.AddParagraph()
            title_para.AppendText("诊断故障码(DTC)详细信息")
            # 设置居中对齐
            try:
                from spire.doc import HorizontalAlignment
                title_para.Format.HorizontalAlignment = HorizontalAlignment.Center
            except Exception:
                pass
            print("标题添加成功")

            # 添加基本信息表格（一行两列）
            section.AddParagraph()
            basic_table = section.AddTable(True)
            basic_table.ResetCells(5, 2)  # 5行2列
            
            # 填充基本信息表格
            basic_cells = [
                ("DTC代码", "{dtc_code}"),
                ("故障描述", "{description}"),
                ("故障类别", "{category}"),
                ("严重程度", "{severity}"),
                ("诊断服务", "{service_type}")
            ]
            
            for i, (label, value) in enumerate(basic_cells):
                row = basic_table.Rows[i]
                row.Cells[0].AddParagraph().AppendText(label)
                row.Cells[1].AddParagraph().AppendText(value)
            print("基本信息表格添加成功")

            # 添加前置条件表格（一行一列）
            section.AddParagraph()
            pre_para = section.AddParagraph()
            pre_para.AppendText("前置条件:")
            
            pre_table = section.AddTable(True)
            pre_table.ResetCells(1, 1)  # 1行1列
            pre_table.Rows[0].Cells[0].AddParagraph().AppendText("{preconditions}")
            print("前置条件表格添加成功")

            # 添加故障成熟条件表格（一行一列）
            section.AddParagraph()
            mat_para = section.AddParagraph()
            mat_para.AppendText("故障成熟条件:")
            
            mat_table = section.AddTable(True)
            mat_table.ResetCells(1, 1)  # 1行1列
            mat_table.Rows[0].Cells[0].AddParagraph().AppendText("{maturation_conditions}")
            print("故障成熟条件表格添加成功")

            # 添加快照数据表格（多行多列，带合并）
            section.AddParagraph()
            snap_para = section.AddParagraph()
            snap_para.AppendText("快照数据:")
            
            snap_table = section.AddTable(True)
            snap_table.ResetCells(4, 3)  # 4行3列
            
            # 表头
            snap_table.Rows[0].Cells[0].AddParagraph().AppendText("参数")
            snap_table.Rows[0].Cells[1].AddParagraph().AppendText("数值")
            snap_table.Rows[0].Cells[2].AddParagraph().AppendText("单位")
            
            # 数据行
            snap_table.Rows[1].Cells[0].AddParagraph().AppendText("发动机转速")
            snap_table.Rows[1].Cells[1].AddParagraph().AppendText("{snapshot_engine_speed}")
            snap_table.Rows[1].Cells[2].AddParagraph().AppendText("rpm")
            
            snap_table.Rows[2].Cells[0].AddParagraph().AppendText("车辆速度")
            snap_table.Rows[2].Cells[1].AddParagraph().AppendText("{snapshot_vehicle_speed}")
            snap_table.Rows[2].Cells[2].AddParagraph().AppendText("km/h")
            
            # 合并单元格示例（一行多列合并）
            snap_table.Rows[3].Cells[0].AddParagraph().AppendText("其他数据")
            snap_table.Rows[3].Cells[1].AddParagraph().AppendText("{snapshot_other}")
            snap_table.Rows[3].Cells[2].AddParagraph().AppendText("-")
            print("快照数据表格添加成功")

            # 添加维修建议表格（多行合并）
            section.AddParagraph()
            repair_para = section.AddParagraph()
            repair_para.AppendText("维修建议:")
            
            repair_table = section.AddTable(True)
            repair_table.ResetCells(3, 2)  # 3行2列
            
            # 第一行：维修建议标题
            repair_table.Rows[0].Cells[0].AddParagraph().AppendText("维修步骤")
            repair_table.Rows[0].Cells[1].AddParagraph().AppendText("详细说明")
            
            # 数据行
            repair_table.Rows[1].Cells[0].AddParagraph().AppendText("步骤 1")
            repair_table.Rows[1].Cells[1].AddParagraph().AppendText("{repair_step1}")
            
            repair_table.Rows[2].Cells[0].AddParagraph().AppendText("步骤 2")
            repair_table.Rows[2].Cells[1].AddParagraph().AppendText("{repair_step2}")
            print("维修建议表格添加成功")

            # 保存模板
            try:
                print("尝试保存模板...")
                doc.SaveToFile(save_path)
                doc.Close()
                print(f"模板已创建: {save_path}")
                print(f"模板文件大小: {os.path.getsize(save_path)} 字节")
            except Exception as e:
                print(f"保存模板失败: {e}")
                doc.Close()
                # 创建一个简单的文本文件作为模板
                with open(save_path, 'w', encoding='utf-8') as f:
                    f.write("诊断故障码(DTC)详细信息\n\n")
                    f.write("基本信息:\n")
                    f.write("DTC代码: {dtc_code}\n")
                    f.write("故障描述: {description}\n")
                    f.write("故障类别: {category}\n")
                    f.write("严重程度: {severity}\n")
                    f.write("诊断服务: {service_type}\n\n")
                    f.write("前置条件:\n{preconditions}\n\n")
                    f.write("故障成熟条件:\n{maturation_conditions}\n\n")
                    f.write("快照数据:\n")
                    f.write("参数\t数值\t单位\n")
                    f.write("发动机转速\t{snapshot_engine_speed}\trpm\n")
                    f.write("车辆速度\t{snapshot_vehicle_speed}\tkm/h\n")
                    f.write("其他数据\t{snapshot_other}\t-\n\n")
                    f.write("维修建议:\n")
                    f.write("维修步骤\t详细说明\n")
                    f.write("步骤 1\t{repair_step1}\n")
                    f.write("步骤 2\t{repair_step2}\n")
                print(f"创建了文本模板文件: {save_path}")

        except Exception as e:
            print(f"创建模板失败: {e}")
            import traceback
            traceback.print_exc()
            # 创建一个空文件避免后续错误
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write("")
            print(f"创建了空模板文件: {save_path}")

    def fill_template(self, dtc_data, output_path=None):
        """
        填充模板并返回图片路径列表
        返回: 生成的图片路径列表
        """
        if not SPIRE_AVAILABLE:
            # 模拟模式：返回占位图片
            return self._create_placeholder_image()

        try:
            # 创建临时文件
            temp_doc = output_path or os.path.join(self.temp_dir, f"temp_{dtc_data.get('dtc_code', 'unknown')}.docx")

            # 加载模板
            doc = Document()
            doc.LoadFromFile(self.template_path)

            # 替换占位符
            doc.Replace("{dtc_code}", dtc_data.get("dtc_code", ""), False, True)
            doc.Replace("{description}", dtc_data.get("description", ""), False, True)
            doc.Replace("{category}", dtc_data.get("category", ""), False, True)
            doc.Replace("{severity}", dtc_data.get("severity", ""), False, True)
            doc.Replace("{service_type}", dtc_data.get("service_type", "UDS"), False, True)

            # 处理列表字段
            preconditions = dtc_data.get("preconditions", [])
            if isinstance(preconditions, list):
                preconditions = "\n".join([f"• {item}" for item in preconditions])
            doc.Replace("{preconditions}", preconditions, False, True)

            maturation = dtc_data.get("maturation_conditions", [])
            if isinstance(maturation, list):
                maturation = "\n".join([f"• {item}" for item in maturation])
            doc.Replace("{maturation_conditions}", maturation, False, True)

            # 处理快照数据
            snapshot = dtc_data.get("snapshot_data", {})
            doc.Replace("{snapshot_engine_speed}", str(snapshot.get("engine_speed", "")), False, True)
            doc.Replace("{snapshot_vehicle_speed}", str(snapshot.get("vehicle_speed", "")), False, True)
            # 其他快照数据
            other_data = []
            for key, value in snapshot.items():
                if key not in ["engine_speed", "vehicle_speed"]:
                    other_data.append(f"{key}: {value}")
            doc.Replace("{snapshot_other}", "\n".join(other_data) if other_data else "无", False, True)

            repairs = dtc_data.get("repair_suggestions", [])
            if isinstance(repairs, list):
                repairs = "\n".join([f"• {item}" for item in repairs])
            doc.Replace("{repair_suggestions}", repairs, False, True)
            
            # 处理维修步骤
            doc.Replace("{repair_step1}", repairs.split("\n")[0] if repairs else "无", False, True)
            doc.Replace("{repair_step2}", repairs.split("\n")[1] if len(repairs.split("\n")) > 1 else "无", False, True)

            # 保存填充后的文档
            doc.SaveToFile(temp_doc)
            doc.Close()

            # 转换为图片
            return self._convert_to_images(temp_doc)

        except Exception as e:
            print(f"填充模板失败: {e}")
            return self._create_placeholder_image()

    def _convert_to_images(self, doc_path):
        """将Word文档转换为图片"""
        image_paths = []

        if not SPIRE_AVAILABLE:
            return self._create_placeholder_image()

        try:
            doc = Document()
            doc.LoadFromFile(doc_path)

            # 获取页数
            page_count = doc.GetPageCount()

            # 尝试使用SaveImageToStreams方法
            try:
                from spire.doc import ImageType
                streams = doc.SaveImageToStreams(ImageType.Bitmap)
                if streams:
                    for i, stream in enumerate(streams):
                        img_path = os.path.join(self.temp_dir, f"page_{i + 1}.png")
                        # 保存流到文件
                        with open(img_path, 'wb') as f:
                            f.write(stream.ToArray())
                        image_paths.append(img_path)
                    print(f"成功转换 {len(image_paths)} 页为图片")
                else:
                    # 没有生成图片，使用占位图片
                    print("SaveImageToStreams返回空，使用占位图片")
                    placeholder_paths = self._create_placeholder_image(page_count)
                    image_paths.extend(placeholder_paths)
            except Exception as e:
                print(f"使用SaveImageToStreams失败: {e}")
                # 使用占位图片
                placeholder_paths = self._create_placeholder_image(page_count)
                image_paths.extend(placeholder_paths)

            doc.Close()

        except Exception as e:
            print(f"转换失败: {e}")
            image_paths = self._create_placeholder_image()

        return image_paths

    def _create_placeholder_image(self, count=1):
        """创建占位图片（当Spire不可用时）"""
        try:
            from PIL import Image, ImageDraw

            paths = []
            for i in range(count):
                img_path = os.path.join(self.temp_dir, f"placeholder_{i}.png")

                # 创建一个简单的占位图片
                img = Image.new('RGB', (800, 600), color=(255, 255, 255))
                d = ImageDraw.Draw(img)
                # 只使用基本文本，避免字体问题
                d.text((100, 100), "预览图片\n(Spire.Doc未安装)", fill=(0, 0, 0))
                d.text((100, 200), f"预览第 {i + 1} 页", fill=(0, 0, 0))

                img.save(img_path)
                paths.append(img_path)

            return paths

        except ImportError:
            # 如果没有Pillow，返回空列表
            print("Pillow未安装，无法创建占位图片")
            return []

    def export_to_format(self, dtc_data, format_type="docx", output_path=None):
        """
        导出为指定格式
        format_type: docx, pdf, png
        """
        if not SPIRE_AVAILABLE:
            QMessageBox.warning(None, "警告", "Spire.Doc未安装，无法导出")
            return None

        try:
            # 先填充模板
            temp_doc = os.path.join(self.temp_dir, f"export_{dtc_data.get('dtc_code', 'unknown')}.docx")
            self.fill_template(dtc_data, temp_doc)

            if format_type == "docx":
                # 直接返回docx文件
                if output_path:
                    import shutil
                    shutil.copy(temp_doc, output_path)
                    return output_path
                return temp_doc

            elif format_type == "pdf":
                # 转换为PDF
                doc = Document()
                doc.LoadFromFile(temp_doc)
                pdf_path = output_path or os.path.join(self.temp_dir, f"{dtc_data.get('dtc_code', 'unknown')}.pdf")
                doc.SaveToFile(pdf_path, FileFormat.PDF)
                doc.Close()
                return pdf_path

            elif format_type == "png":
                # 转换为图片
                images = self._convert_to_images(temp_doc)
                if output_path and images:
                    import shutil
                    shutil.copy(images[0], output_path)
                    return output_path
                return images[0] if images else None

        except Exception as e:
            print(f"导出失败: {e}")
            return None


class DTCModel:
    """DTC数据模型"""

    @staticmethod
    def get_sample_data():
        return {
            "U0100": {
                "dtc_code": "U0100",
                "description": "与ECM/PCM通讯丢失",
                "category": "网络通讯",
                "severity": "严重",
                "service_type": "UDS 0x19",
                "preconditions": [
                    "点火开关置于ON位置",
                    "系统电压在9-16V之间",
                    "CAN总线通讯正常"
                ],
                "maturation_conditions": [
                    "连续2个驾驶循环发生",
                    "每个循环故障持续时间>5秒"
                ],
                "snapshot_data": {
                    "engine_speed": "2500 rpm",
                    "vehicle_speed": "60 km/h",
                    "engine_load": "45%",
                    "coolant_temp": "95°C",
                    "battery_voltage": "13.8V"
                },
                "repair_suggestions": [
                    "检查ECM/PCM电源和接地",
                    "检查CAN总线终端电阻",
                    "检查相关线束连接器"
                ]
            },
            "U0101": {
                "dtc_code": "U0101",
                "description": "与TCU通讯丢失",
                "category": "网络通讯",
                "severity": "严重",
                "service_type": "UDS 0x19",
                "preconditions": [
                    "变速器处于非P档",
                    "发动机运转"
                ],
                "maturation_conditions": [
                    "连续3个驾驶循环",
                    "通讯中断超过10秒"
                ],
                "snapshot_data": {
                    "engine_speed": "1800 rpm",
                    "vehicle_speed": "40 km/h",
                    "gear_position": "3",
                    "transmission_temp": "85°C"
                },
                "repair_suggestions": [
                    "检查TCU电源",
                    "检查CAN线束",
                    "检查TCU内部故障"
                ]
            },
            "P0300": {
                "dtc_code": "P0300",
                "description": "检测到随机/多缸缺火",
                "category": "动力系统",
                "severity": "中等",
                "service_type": "OBD",
                "preconditions": [
                    "发动机运转",
                    "水温>70°C"
                ],
                "maturation_conditions": [
                    "曲轴位置传感器检测到缺火",
                    "缺火率超过2%"
                ],
                "snapshot_data": {
                    "engine_speed": "750 rpm",
                    "engine_load": "20%",
                    "coolant_temp": "92°C",
                    "misfire_count_cyl1": "12",
                    "misfire_count_cyl2": "8"
                },
                "repair_suggestions": [
                    "检查火花塞",
                    "检查点火线圈",
                    "检查喷油嘴",
                    "检查气缸压力"
                ]
            },
            "P0420": {
                "dtc_code": "P0420",
                "description": "催化转换器效率低于阈值",
                "category": "排放控制",
                "severity": "中等",
                "service_type": "OBD",
                "preconditions": [
                    "发动机运转",
                    "闭环控制",
                    "水温>75°C"
                ],
                "maturation_conditions": [
                    "前后氧传感器信号比值异常",
                    "持续超过阈值"
                ],
                "snapshot_data": {
                    "engine_speed": "2000 rpm",
                    "engine_load": "40%",
                    "o2_sensor1": "0.7V",
                    "o2_sensor2": "0.4V"
                },
                "repair_suggestions": [
                    "检查催化转换器",
                    "检查氧传感器",
                    "检查排气泄漏"
                ]
            }
        }


class DTCLeftPanel(QFrame):
    """左侧DTC索引面板 - 带右键菜单"""

    dtc_selected = Signal(str)
    dtc_export_requested = Signal(str, str)  # dtc_code, format_type

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("leftPanel")
        self.setMaximumWidth(300)
        self.setMinimumWidth(250)

        self.data_model = DTCModel.get_sample_data()
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # 标题
        title = SubtitleLabel("DTC索引")
        layout.addWidget(title)

        # 搜索框
        self.search_box = SearchLineEdit()
        self.search_box.setPlaceholderText("搜索DTC或描述")
        self.search_box.setClearButtonEnabled(True)
        self.search_box.textChanged.connect(self.filter_items)
        layout.addWidget(self.search_box)

        # DTC列表
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(20)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)
        self.tree.itemClicked.connect(self.on_item_clicked)
        self.tree.setStyleSheet("""
            QTreeWidget::item {
                padding: 8px;
                border-bottom: 1px solid #e0e0e0;
            }
            QTreeWidget::item:selected {
                background-color: #d0e0ff;
                border-left: 4px solid #0078d4;
            }
        """)
        layout.addWidget(self.tree)

    def load_data(self):
        """加载DTC数据到树形控件"""
        # 按类别分组
        categories = {}
        for dtc_code, data in self.data_model.items():
            category = data.get("category", "其他")
            if category not in categories:
                categories[category] = []
            categories[category].append((dtc_code, data))

        # 构建树
        for category, items in categories.items():
            category_item = QTreeWidgetItem([category])
            category_item.setFlags(category_item.flags() & ~Qt.ItemIsSelectable)
            category_item.setExpanded(True)

            for dtc_code, data in items:
                child = QTreeWidgetItem([f"{dtc_code} - {data['description'][:20]}..."])
                child.setData(0, Qt.UserRole, dtc_code)
                category_item.addChild(child)

            self.tree.addTopLevelItem(category_item)

    def filter_items(self, text):
        """过滤树节点"""
        text = text.lower().strip()

        for i in range(self.tree.topLevelItemCount()):
            category_item = self.tree.topLevelItem(i)
            category_visible = False

            for j in range(category_item.childCount()):
                child = category_item.child(j)
                dtc_code = child.data(0, Qt.UserRole).lower()

                # 获取描述
                description = self.data_model.get(dtc_code.upper(), {}).get("description", "").lower()

                if not text or text in dtc_code or text in description:
                    child.setHidden(False)
                    category_visible = True
                else:
                    child.setHidden(True)

            category_item.setHidden(not category_visible)

    def on_item_clicked(self, item, column):
        """处理点击事件"""
        dtc_code = item.data(0, Qt.UserRole)
        if dtc_code:
            self.dtc_selected.emit(dtc_code)

    def show_context_menu(self, pos):
        """显示右键菜单"""
        item = self.tree.itemAt(pos)
        if not item:
            return

        dtc_code = item.data(0, Qt.UserRole)
        if not dtc_code:
            return

        menu = RoundMenu(parent=self)

        # 导出子菜单
        export_menu = RoundMenu("导出为", parent=self)
        export_menu.addAction(
            Action("导出为 Word (.docx)", triggered=lambda: self.dtc_export_requested.emit(dtc_code, "docx")))
        export_menu.addAction(
            Action("导出为 PDF (.pdf)", triggered=lambda: self.dtc_export_requested.emit(dtc_code, "pdf")))
        export_menu.addAction(
            Action("导出为 PNG 图片", triggered=lambda: self.dtc_export_requested.emit(dtc_code, "png")))

        menu.addMenu(export_menu)
        menu.addSeparator()
        menu.addAction(Action("复制DTC代码", triggered=lambda: self.copy_dtc_code(dtc_code)))
        menu.addAction(Action("查看详情", triggered=lambda: self.dtc_selected.emit(dtc_code)))

        menu.exec(self.tree.viewport().mapToGlobal(pos))

    def copy_dtc_code(self, dtc_code):
        """复制DTC代码到剪贴板"""
        clipboard = QApplication.clipboard()
        clipboard.setText(dtc_code)
        InfoBar.success(
            title="已复制",
            content=f"DTC {dtc_code} 已复制到剪贴板",
            parent=self
        )


class DTCEditPanel(QFrame):
    """右侧编辑面板 - 所有字段可编辑"""

    write_fields = Signal(dict)  # 写入字段信号，发送更新后的数据

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("editPanel")
        self.setMaximumWidth(350)
        self.setMinimumWidth(300)

        self.current_dtc = None
        self.current_data = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)

        # 标题
        title = SubtitleLabel("编辑字段")
        layout.addWidget(title)

        # 使用滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        self.form_layout = QVBoxLayout(content)
        self.form_layout.setSpacing(10)

        # 当前编辑的DTC标识
        self.current_label = StrongBodyLabel("当前: 未选择")
        self.form_layout.addWidget(self.current_label)
        self.form_layout.addWidget(HorizontalSeparator())

        # 使用表单布局组织字段
        self.field_widgets = {}

        # 基本信息组
        basic_group = QGroupBox("基本信息")
        basic_form = QFormLayout(basic_group)

        # DTC代码（只读）
        self.field_widgets["dtc_code"] = LineEdit()
        self.field_widgets["dtc_code"].setReadOnly(True)
        basic_form.addRow("DTC代码:", self.field_widgets["dtc_code"])

        # 描述（可编辑）
        self.field_widgets["description"] = TextEdit()
        self.field_widgets["description"].setMaximumHeight(60)
        basic_form.addRow("故障描述:", self.field_widgets["description"])

        # 类别（下拉框）
        self.field_widgets["category"] = ComboBox()
        self.field_widgets["category"].addItems(["网络通讯", "动力系统", "排放控制", "底盘系统", "其他"])
        basic_form.addRow("故障类别:", self.field_widgets["category"])

        # 严重程度（下拉框）
        self.field_widgets["severity"] = ComboBox()
        self.field_widgets["severity"].addItems(["轻微", "中等", "严重", "致命"])
        basic_form.addRow("严重程度:", self.field_widgets["severity"])

        # 服务类型
        self.field_widgets["service_type"] = ComboBox()
        self.field_widgets["service_type"].addItems(["UDS 0x19", "OBD", "增强型诊断"])
        basic_form.addRow("诊断服务:", self.field_widgets["service_type"])

        self.form_layout.addWidget(basic_group)

        # 前置条件组
        pre_group = QGroupBox("前置条件")
        pre_layout = QVBoxLayout(pre_group)
        self.field_widgets["preconditions"] = TextEdit()
        self.field_widgets["preconditions"].setPlaceholderText("每行一个条件")
        pre_layout.addWidget(self.field_widgets["preconditions"])
        self.form_layout.addWidget(pre_group)

        # 故障成熟条件组
        mat_group = QGroupBox("故障成熟条件")
        mat_layout = QVBoxLayout(mat_group)
        self.field_widgets["maturation_conditions"] = TextEdit()
        self.field_widgets["maturation_conditions"].setPlaceholderText("每行一个条件")
        mat_layout.addWidget(self.field_widgets["maturation_conditions"])
        self.form_layout.addWidget(mat_group)

        # 快照数据组
        snap_group = QGroupBox("快照数据")
        snap_layout = QVBoxLayout(snap_group)
        self.field_widgets["snapshot_data"] = TextEdit()
        self.field_widgets["snapshot_data"].setPlaceholderText("格式: 参数: 数值，每行一个")
        snap_layout.addWidget(self.field_widgets["snapshot_data"])
        self.form_layout.addWidget(snap_group)

        # 维修建议组
        repair_group = QGroupBox("维修建议")
        repair_layout = QVBoxLayout(repair_group)
        self.field_widgets["repair_suggestions"] = TextEdit()
        self.field_widgets["repair_suggestions"].setPlaceholderText("每行一条建议")
        repair_layout.addWidget(self.field_widgets["repair_suggestions"])
        self.form_layout.addWidget(repair_group)

        # 按钮组
        btn_layout = QHBoxLayout()

        self.write_btn = PrimaryPushButton("写入字段")
        self.write_btn.clicked.connect(self.on_write_fields)

        self.reset_btn = PushButton("重置")
        self.reset_btn.clicked.connect(self.reset_form)

        btn_layout.addWidget(self.write_btn)
        btn_layout.addWidget(self.reset_btn)

        self.form_layout.addLayout(btn_layout)

        scroll.setWidget(content)
        layout.addWidget(scroll)

    def load_dtc_for_edit(self, dtc_code, data):
        """加载DTC数据到编辑表单"""
        self.current_dtc = dtc_code
        self.current_data = data.copy() if data else {}

        self.current_label.setText(f"当前: {dtc_code}")

        # 填充表单
        self.field_widgets["dtc_code"].setText(data.get("dtc_code", ""))
        self.field_widgets["description"].setText(data.get("description", ""))
        self.field_widgets["category"].setCurrentText(data.get("category", "其他"))
        self.field_widgets["severity"].setCurrentText(data.get("severity", "中等"))
        self.field_widgets["service_type"].setCurrentText(data.get("service_type", "UDS 0x19"))

        # 列表字段（转换为文本）
        preconditions = data.get("preconditions", [])
        if isinstance(preconditions, list):
            self.field_widgets["preconditions"].setText("\n".join(preconditions))

        maturation = data.get("maturation_conditions", [])
        if isinstance(maturation, list):
            self.field_widgets["maturation_conditions"].setText("\n".join(maturation))

        # 快照数据（转换为文本行）
        snapshot = data.get("snapshot_data", {})
        snapshot_text = "\n".join([f"{k}: {v}" for k, v in snapshot.items()])
        self.field_widgets["snapshot_data"].setText(snapshot_text)

        repairs = data.get("repair_suggestions", [])
        if isinstance(repairs, list):
            self.field_widgets["repair_suggestions"].setText("\n".join(repairs))

    def on_write_fields(self):
        """写入字段按钮点击处理"""
        if not self.current_dtc:
            InfoBar.warning(
                title="提示",
                content="请先选择一个DTC",
                parent=self
            )
            return

        # 从表单收集数据
        updated_data = {
            "dtc_code": self.field_widgets["dtc_code"].text(),
            "description": self.field_widgets["description"].toPlainText(),
            "category": self.field_widgets["category"].currentText(),
            "severity": self.field_widgets["severity"].currentText(),
            "service_type": self.field_widgets["service_type"].currentText(),
        }

        # 处理文本字段转换为列表
        pre_text = self.field_widgets["preconditions"].toPlainText().strip()
        updated_data["preconditions"] = [line.strip() for line in pre_text.split("\n") if line.strip()]

        mat_text = self.field_widgets["maturation_conditions"].toPlainText().strip()
        updated_data["maturation_conditions"] = [line.strip() for line in mat_text.split("\n") if line.strip()]

        # 处理快照数据
        snap_text = self.field_widgets["snapshot_data"].toPlainText().strip()
        snapshot = {}
        for line in snap_text.split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                snapshot[key.strip()] = value.strip()
        updated_data["snapshot_data"] = snapshot

        repair_text = self.field_widgets["repair_suggestions"].toPlainText().strip()
        updated_data["repair_suggestions"] = [line.strip() for line in repair_text.split("\n") if line.strip()]

        # 发送信号
        self.write_fields.emit(updated_data)

        InfoBar.success(
            title="成功",
            content=f"DTC {self.current_dtc} 字段已更新",
            parent=self
        )

    def reset_form(self):
        """重置表单到原始数据"""
        if self.current_data:
            self.load_dtc_for_edit(self.current_dtc, self.current_data)


class DTCPreviewPanel(QFrame):
    """中间预览面板 - 显示Word转换后的图片"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.template_manager = DTCTemplateManager()
        self.current_image_paths = []
        self.current_page = 0

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # 标题和工具栏
        tool_layout = QHBoxLayout()

        title = SubtitleLabel("预览区域")
        tool_layout.addWidget(title)

        tool_layout.addStretch()

        self.prev_btn = PushButton("上一页")
        self.prev_btn.clicked.connect(self.prev_page)
        self.prev_btn.setEnabled(False)
        tool_layout.addWidget(self.prev_btn)

        self.page_label = BodyLabel("0/0")
        tool_layout.addWidget(self.page_label)

        self.next_btn = PushButton("下一页")
        self.next_btn.clicked.connect(self.next_page)
        self.next_btn.setEnabled(False)
        tool_layout.addWidget(self.next_btn)

        layout.addLayout(tool_layout)

        # 图片显示区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignCenter)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setScaledContents(False)
        self.scroll_area.setWidget(self.image_label)

        layout.addWidget(self.scroll_area)

    def update_preview(self, dtc_data):
        """更新预览图片"""
        if not dtc_data:
            return

        # 生成新的预览图片
        self.current_image_paths = self.template_manager.fill_template(dtc_data)

        if self.current_image_paths:
            self.current_page = 0
            self.show_current_page()
        else:
            self.image_label.setText("无法生成预览图片")
            self.page_label.setText("0/0")
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)

    def show_current_page(self):
        """显示当前页"""
        if not self.current_image_paths:
            return

        path = self.current_image_paths[self.current_page]
        pixmap = QPixmap(path)

        if pixmap.isNull():
            self.image_label.setText("无法加载图片")
            return

        # 缩放以适应滚动区宽度
        available_width = self.scroll_area.viewport().width() - 20
        if available_width > 10:
            pixmap = pixmap.scaledToWidth(available_width, Qt.SmoothTransformation)

        self.image_label.setPixmap(pixmap)

        # 更新导航
        total = len(self.current_image_paths)
        self.page_label.setText(f"{self.current_page + 1}/{total}")
        self.prev_btn.setEnabled(self.current_page > 0)
        self.next_btn.setEnabled(self.current_page < total - 1)

    def prev_page(self):
        """上一页"""
        if self.current_page > 0:
            self.current_page -= 1
            self.show_current_page()

    def next_page(self):
        """下一页"""
        if self.current_page < len(self.current_image_paths) - 1:
            self.current_page += 1
            self.show_current_page()

    def resizeEvent(self, event):
        """窗口大小变化时重新缩放"""
        super().resizeEvent(event)
        self.show_current_page()


class DTCMainWindow(FluentWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("DTC诊断故障码管理系统 - 模板化文档生成")
        self.resize(1400, 900)

        # 数据模型
        self.data_model = DTCModel.get_sample_data()

        # 创建三个面板
        self.left_panel = DTCLeftPanel()
        self.preview_panel = DTCPreviewPanel()
        self.edit_panel = DTCEditPanel()

        # 创建分割器
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.left_panel)
        self.splitter.addWidget(self.preview_panel)
        self.splitter.addWidget(self.edit_panel)
        self.splitter.setSizes([300, 600, 300])

        # 将分割器添加到中心区域
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.splitter)

        self.stackedWidget.addWidget(central_widget)
        self.stackedWidget.setCurrentWidget(central_widget)

        # 连接信号
        self.left_panel.dtc_selected.connect(self.on_dtc_selected)
        self.left_panel.dtc_export_requested.connect(self.on_export_request)
        self.edit_panel.write_fields.connect(self.on_write_fields)

        # 检查Spire.Doc
        if not SPIRE_AVAILABLE:
            InfoBar.warning(
                title="提示",
                content="Spire.Doc未安装，将使用模拟预览模式",
                parent=self,
                duration=5000
            )

    def on_dtc_selected(self, dtc_code):
        """处理DTC选择"""
        data = self.data_model.get(dtc_code, {})

        # 更新编辑面板
        self.edit_panel.load_dtc_for_edit(dtc_code, data)

        # 更新预览面板
        self.preview_panel.update_preview(data)

    def on_write_fields(self, updated_data):
        """处理字段写入"""
        dtc_code = updated_data.get("dtc_code")

        # 更新数据模型
        self.data_model[dtc_code] = updated_data

        # 刷新预览
        self.preview_panel.update_preview(updated_data)

    def on_export_request(self, dtc_code, format_type):
        """处理导出请求"""
        data = self.data_model.get(dtc_code, {})
        if not data:
            return

        # 选择保存路径
        ext_map = {"docx": "Word 文档 (*.docx)", "pdf": "PDF 文件 (*.pdf)", "png": "PNG 图片 (*.png)"}
        filter_str = ext_map.get(format_type, f"{format_type.upper()} 文件 (*.{format_type})")

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            f"导出DTC {dtc_code}",
            f"{dtc_code}.{format_type}",
            filter_str
        )

        if not file_path:
            return

        try:
            # 导出
            output_path = self.preview_panel.template_manager.export_to_format(
                data, format_type, file_path
            )

            if output_path:
                InfoBar.success(
                    title="导出成功",
                    content=f"已导出到: {output_path}",
                    parent=self
                )
            else:
                InfoBar.error(
                    title="导出失败",
                    content="导出过程中发生错误",
                    parent=self
                )

        except Exception as e:
            InfoBar.error(
                title="导出失败",
                content=str(e),
                parent=self
            )


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 设置主题
    setTheme(Theme.LIGHT)

    try:
        window = DTCMainWindow()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        print(f"程序运行出错: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)