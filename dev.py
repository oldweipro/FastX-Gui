#!/usr/bin/env python3
"""
FastX-Gui 开发工具
用于管理翻译和资源文件
"""

import glob
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path


class FastXDevTool:
    """FastX-Gui 开发工具类"""

    def __init__(self):
        # 项目根目录
        self.project_root = Path(__file__).parent
        self.app_dir = self.project_root / "app"
        self.resource_dir = self.app_dir / "resource"
        self.i18n_dir = self.resource_dir / "i18n"
        self.common_dir = self.app_dir / "common"

        # 工具目录
        self.tools_dir = self.project_root / "tools" / "linguist_5.15.18"

        # 确保目录存在
        self.i18n_dir.mkdir(parents=True, exist_ok=True)

        # 需要排除的目录和文件
        self.exclude_patterns = [
            ".venv",
            "__pycache__",
            "*__init__.py",
            ".git",
            ".vscode",
            ".idea",
            "node_modules",
            "dist",
            "build",
            "*.pyc",
            "*.pyo",
            "*.ui",
            "ui_*.py",
            ".DS_Store",
            "*.json",  # 排除 lupdate 生成的临时 .json 文件
        ]

        # 颜色输出
        self.COLORS = {
            "RED": "\033[91m",
            "GREEN": "\033[92m",
            "YELLOW": "\033[93m",
            "BLUE": "\033[94m",
            "MAGENTA": "\033[95m",
            "CYAN": "\033[96m",
            "END": "\033[0m",
            "BOLD": "\033[1m",
        }

    def print_color(self, text, color="GREEN"):
        """彩色打印"""
        color_code = self.COLORS.get(color, self.COLORS["END"])
        print(f"{color_code}{text}{self.COLORS['END']}")

    def print_header(self, text):
        """打印标题"""
        print("\n" + "=" * 60)
        self.print_color(f" {text} ", "CYAN")
        print("=" * 60)

    def print_success(self, text):
        """打印成功信息"""
        self.print_color(f"✅ {text}", "GREEN")

    def print_error(self, text):
        """打印错误信息"""
        self.print_color(f"❌ {text}", "RED")

    def print_warning(self, text):
        """打印警告信息"""
        self.print_color(f"⚠️ {text}", "YELLOW")

    def print_info(self, text):
        """打印信息"""
        self.print_color(f"ℹ️ {text}", "BLUE")

    def cleanup_temp_files(self):
        """清理 lupdate 生成的临时文件"""
        temp_patterns = [
            "*.json",  # lupdate 生成的临时 JSON 文件
            "lupdate_*.tmp",
        ]

        cleaned = 0
        for pattern in temp_patterns:
            for temp_file in glob.glob(str(self.project_root / pattern)):
                try:
                    os.remove(temp_file)
                    self.print_info(f"清理临时文件: {os.path.basename(temp_file)}")
                    cleaned += 1
                except:
                    pass

        if cleaned > 0:
            self.print_success(f"清理了 {cleaned} 个临时文件")

    def should_exclude(self, file_path):
        """判断文件是否应该排除"""
        path_str = str(file_path)

        # 检查排除模式
        for pattern in self.exclude_patterns:
            # 如果是目录模式
            if pattern.startswith(".") or pattern.endswith("__"):
                if pattern in path_str.split(os.sep):
                    return True
            # 如果是文件模式
            elif "*" in pattern:
                import fnmatch

                if fnmatch.fnmatch(file_path.name, pattern):
                    return True
            # 精确匹配
            elif pattern in path_str:
                return True

        return False

    def find_source_files(self):
        """查找所有需要翻译的源文件（过滤不需要的）"""
        source_files = []

        # 只搜索特定的目录，而不是整个项目
        search_dirs = [
            self.app_dir,
            self.project_root,  # 根目录下的主要文件
        ]

        for search_dir in search_dirs:
            if not search_dir.exists():
                continue

            # Python 文件
            for py_file in search_dir.rglob("*.py"):
                if not self.should_exclude(py_file):
                    rel_path = py_file.relative_to(self.project_root)
                    source_files.append(str(rel_path))

            # UI 文件
            for ui_file in search_dir.rglob("*.ui"):
                if not self.should_exclude(ui_file):
                    rel_path = ui_file.relative_to(self.project_root)
                    source_files.append(str(rel_path))

        # 移除重复项
        source_files = list(set(source_files))
        source_files.sort()  # 按字母顺序排序

        return source_files

    def create_main_pro(self):
        """创建或更新 main.pro 文件"""
        source_files = self.find_source_files()

        if not source_files:
            self.print_warning("没有找到有效的源文件")
            return None

        # 查找现有的翻译文件
        ts_files = []
        for ts_file in self.i18n_dir.glob("*.ts"):
            ts_files.append(str(ts_file.relative_to(self.project_root)))

        # 如果没有 ts 文件，创建默认的
        if not ts_files:
            ts_files = [
                str(self.i18n_dir / "app.zh_CN.ts"),
                str(self.i18n_dir / "app.zh_HK.ts"),
            ]
            # 确保目录存在
            for ts_file in ts_files:
                ts_path = self.project_root / ts_file
                ts_path.parent.mkdir(parents=True, exist_ok=True)

        # 生成 .pro 文件内容
        source_str = " \\\n            ".join(source_files)
        ts_str = " \\\n                ".join(ts_files)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        pro_content = f"""# Generated by dev.py on {timestamp}
# DO NOT EDIT MANUALLY

# 源文件
SOURCES += {source_str}

# 翻译文件
TRANSLATIONS += {ts_str}

# 编码设置
CODECFORTR = UTF-8

# 禁止生成临时文件
QMAKE_EXTRA_TARGETS += no_temp_files
"""

        pro_file = self.project_root / "main.pro"
        pro_file.write_text(pro_content, encoding="utf-8")

        self.print_success("已更新 main.pro 文件")
        self.print_info(f"包含 {len(source_files)} 个源文件")

        # 显示包含的文件
        if len(source_files) <= 20:  # 如果文件不多，显示列表
            self.print_info("包含的文件:")
            for i, file in enumerate(source_files, 1):
                print(f"  {i:2d}. {file}")
        else:
            self.print_info(f"包含 {len(source_files)} 个文件（使用 --verbose 查看详情）")

        self.print_info(f"包含 {len(ts_files)} 个翻译文件")
        for ts_file in ts_files:
            print(f"  - {ts_file}")

        return str(pro_file)

    def find_lupdate(self):
        """查找 lupdate.exe 工具"""
        # 1. 首先检查 tools 目录
        lupdate_exe = self.tools_dir / "lupdate.exe"
        if lupdate_exe.exists():
            self.print_success(f"找到 lupdate.exe: {lupdate_exe}")
            return str(lupdate_exe)

        # 2. 检查其他可能的名称
        possible_names = [
            "lupdate.exe",
            "lupdate-pro.exe",
            "lupdate",
            "lupdate-pro",
        ]

        # 3. 检查 tools 目录中的其他文件
        if self.tools_dir.exists():
            for exe_name in possible_names:
                exe_path = self.tools_dir / exe_name
                if exe_path.exists():
                    self.print_success(f"找到 {exe_name}: {exe_path}")
                    return str(exe_path)

        # 4. 检查系统 PATH
        for exe_name in possible_names:
            try:
                subprocess.run([exe_name, "--version"], capture_output=True, check=True)
                self.print_success(f"找到系统 {exe_name}")
                return exe_name
            except:
                continue

        self.print_error("未找到 lupdate 工具")
        self.print_info(f"请确保 {self.tools_dir} 目录包含 lupdate.exe")
        self.print_info("或者将 lupdate 添加到系统 PATH")
        return None

    def run_lupdate(self, pro_file, verbose=False):
        """运行 lupdate.exe"""
        lupdate_path = self.find_lupdate()
        if not lupdate_path:
            return False

        # 构建命令 - 添加 -no-obsolete 避免警告
        cmd = [lupdate_path, "-no-obsolete", pro_file]
        if verbose:
            cmd.append("-verbose")

        self.print_info(f"执行命令: {' '.join(cmd)}")

        try:
            # 清理之前的临时文件
            self.cleanup_temp_files()

            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=30,
            )

            # 运行后清理临时文件
            self.cleanup_temp_files()

            if result.returncode == 0:
                self.print_success("翻译字符串提取成功")
                if result.stdout and verbose:
                    self.print_info(f"输出: {result.stdout.strip()}")
                elif result.stdout:
                    # 显示关键信息
                    for line in result.stdout.split("\n"):
                        if line.strip():
                            self.print_info(line.strip())
                return True
            else:
                # 即使有警告，只要 .ts 文件生成了就算成功
                if "WARNING: Could not find qmake spec" in result.stderr:
                    self.print_warning("lupdate 警告（可以忽略）: Could not find qmake spec 'default'")
                    # 检查 .ts 文件是否生成
                    ts_files = list(self.i18n_dir.glob("*.ts"))
                    if ts_files:
                        self.print_success(f"已生成 {len(ts_files)} 个 .ts 文件")
                        return True

                self.print_error(f"提取失败: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            self.print_error("命令执行超时")
            self.cleanup_temp_files()
            return False
        except Exception as e:
            self.print_error(f"执行错误: {e}")
            self.cleanup_temp_files()
            return False

    def extract_translations(self, verbose=False):
        """提取翻译字符串到 .ts 文件"""
        self.print_header("提取翻译字符串")

        # 1. 创建或更新 main.pro
        pro_file = self.create_main_pro()
        if not pro_file:
            return False

        # 2. 运行 lupdate
        success = self.run_lupdate(pro_file, verbose)

        if success:
            # 显示提取的字符串统计
            self.show_translation_stats()

        return success

    def show_translation_stats(self):
        """显示翻译统计信息"""
        ts_files = list(self.i18n_dir.glob("*.ts"))

        if not ts_files:
            self.print_warning("没有找到 .ts 文件")
            return

        self.print_info("翻译文件统计:")

        for ts_file in ts_files:
            try:
                tree = ET.parse(ts_file)
                root = tree.getroot()

                total = 0
                translated = 0
                unfinished = 0

                for message in root.iter("message"):
                    total += 1
                    translation = message.find("translation")
                    if translation is not None:
                        if translation.get("type") != "unfinished" and translation.text:
                            translated += 1
                        else:
                            unfinished += 1
                    else:
                        unfinished += 1

                percentage = (translated / total * 100) if total > 0 else 0

                print(f"  {ts_file.name}:")
                print(f"    总计: {total} | 已翻译: {translated} | 未完成: {unfinished}")
                print(f"    进度: {percentage:.1f}%")

                # 显示一些未翻译的示例
                if unfinished > 0 and total <= 50:  # 如果文件不大，显示示例
                    print("    未翻译示例:")
                    count = 0
                    for message in root.iter("message"):
                        if count >= 3:  # 最多显示3个
                            break
                        translation = message.find("translation")
                        if translation is None or translation.get("type") == "unfinished" or not translation.text:
                            source = message.find("source")
                            if source is not None and source.text:
                                print(f"      - {source.text[:50]}...")
                                count += 1

            except Exception as e:
                print(f"  读取 {ts_file} 失败: {e}")

    def find_linguist(self):
        """查找 linguist.exe 工具"""
        # 1. 首先检查 tools 目录
        linguist_exe = self.tools_dir / "linguist.exe"
        if linguist_exe.exists():
            self.print_success(f"找到 linguist.exe: {linguist_exe}")
            return str(linguist_exe)

        # 2. 检查其他可能的名称
        possible_names = ["linguist.exe", "linguist"]

        # 3. 检查 tools 目录中的其他文件
        if self.tools_dir.exists():
            for exe_name in possible_names:
                exe_path = self.tools_dir / exe_name
                if exe_path.exists():
                    self.print_success(f"找到 {exe_name}: {exe_path}")
                    return str(exe_path)

        # 4. 检查系统 PATH
        for exe_name in possible_names:
            try:
                subprocess.run([exe_name, "--version"], capture_output=True, check=True)
                self.print_success(f"找到系统 {exe_name}")
                return exe_name
            except:
                continue

        self.print_error("未找到 linguist 工具")
        self.print_info(f"请确保 {self.tools_dir} 目录包含 linguist.exe")
        return None

    def open_linguist(self, ts_file=None):
        """打开 Qt Linguist"""
        self.print_header("打开 Qt Linguist")

        linguist_path = self.find_linguist()
        if not linguist_path:
            return False

        cmd = [linguist_path]

        if ts_file:
            if isinstance(ts_file, str):
                ts_path = Path(ts_file)
                if not ts_path.is_absolute():
                    ts_path = self.i18n_dir / ts_path
            else:
                ts_path = ts_file

            if ts_path.exists():
                cmd.append(str(ts_path))
            else:
                self.print_warning(f"文件不存在: {ts_path}")
                # 打开所有 ts 文件
                ts_files = list(self.i18n_dir.glob("*.ts"))
                for tf in ts_files:
                    cmd.append(str(tf))
        else:
            # 打开所有 ts 文件
            ts_files = list(self.i18n_dir.glob("*.ts"))
            if ts_files:
                for tf in ts_files:
                    cmd.append(str(tf))
            else:
                self.print_warning("没有找到 .ts 文件，请先运行提取字符串")
                return False

        self.print_info(f"执行命令: {' '.join(cmd)}")

        try:
            # 使用 start 命令在 Windows 上打开，避免阻塞
            if sys.platform == "win32":
                subprocess.Popen(cmd, shell=True)
            else:
                subprocess.Popen(cmd)

            self.print_success("Qt Linguist 已启动")
            self.print_info("请在 Qt Linguist 中编辑翻译，完成后保存文件")
            return True

        except Exception as e:
            self.print_error(f"启动失败: {e}")
            return False

    def find_lrelease(self):
        """查找 lrelease.exe 工具"""
        # 1. 首先检查 tools 目录
        lrelease_exe = self.tools_dir / "lrelease.exe"
        if lrelease_exe.exists():
            self.print_success(f"找到 lrelease.exe: {lrelease_exe}")
            return str(lrelease_exe)

        # 2. 检查其他可能的名称
        possible_names = [
            "lrelease.exe",
            "lrelease-pro.exe",
            "lrelease",
            "lrelease-pro",
        ]

        # 3. 检查 tools 目录中的其他文件
        if self.tools_dir.exists():
            for exe_name in possible_names:
                exe_path = self.tools_dir / exe_name
                if exe_path.exists():
                    self.print_success(f"找到 {exe_name}: {exe_path}")
                    return str(exe_path)

        # 4. 检查系统 PATH
        for exe_name in possible_names:
            try:
                subprocess.run([exe_name, "--version"], capture_output=True, check=True)
                self.print_success(f"找到系统 {exe_name}")
                return exe_name
            except:
                continue

        self.print_error("未找到 lrelease 工具")
        self.print_info(f"请确保 {self.tools_dir} 目录包含 lrelease.exe")
        return None

    def compile_translations(self):
        """编译 .ts 文件为 .qm 文件"""
        self.print_header("编译翻译文件")

        lrelease_path = self.find_lrelease()
        if not lrelease_path:
            return False

        ts_files = list(self.i18n_dir.glob("*.ts"))

        if not ts_files:
            self.print_warning("没有找到 .ts 文件")
            return False

        success_count = 0
        error_count = 0

        for ts_file in ts_files:
            qm_file = ts_file.with_suffix(".qm")

            cmd = [lrelease_path, str(ts_file), "-qm", str(qm_file)]

            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    timeout=10,
                )

                if result.returncode == 0:
                    self.print_success(f"编译完成: {ts_file.name} -> {qm_file.name}")
                    success_count += 1
                else:
                    self.print_error(f"编译失败 {ts_file.name}: {result.stderr}")
                    error_count += 1

            except subprocess.TimeoutExpired:
                self.print_error(f"编译超时: {ts_file.name}")
                error_count += 1
            except Exception as e:
                self.print_error(f"执行错误 {ts_file.name}: {e}")
                error_count += 1

        if success_count > 0:
            self.print_success(f"成功编译 {success_count} 个文件")

        if error_count > 0:
            self.print_error(f"失败 {error_count} 个文件")

        return error_count == 0

    def update_resource_qrc(self):
        """更新 resource.qrc 文件，使用统一的 /app 前缀"""
        self.print_header("更新资源文件")

        qrc_file = self.resource_dir / "resource.qrc"

        # 创建根元素
        rcc = ET.Element("RCC")

        # 创建统一的 /app 前缀
        qresource_app = ET.SubElement(rcc, "qresource", prefix="/app")

        added_files = []

        # 1. 添加 QSS 资源
        qss_dir = self.resource_dir / "qss"
        if qss_dir.exists():
            qss_count = 0
            for theme_dir in qss_dir.iterdir():
                if theme_dir.is_dir():
                    for qss_file in theme_dir.rglob("*.qss"):
                        relative_path = qss_file.relative_to(self.resource_dir)
                        file_elem = ET.SubElement(qresource_app, "file")
                        file_elem.text = str(relative_path).replace("\\", "/")
                        added_files.append(str(relative_path))
                        qss_count += 1

            if qss_count > 0:
                self.print_info(f"添加了 {qss_count} 个 QSS 资源")

        # 2. 添加图片资源 (ICO 优先，然后其他图片)
        images_dir = self.resource_dir / "images"
        if images_dir.exists():
            # 先添加 ICO 文件
            ico_count = 0
            for img_file in images_dir.rglob("*.ico"):
                if img_file.is_file():
                    relative_path = img_file.relative_to(self.resource_dir)
                    file_elem = ET.SubElement(qresource_app, "file")
                    file_elem.text = str(relative_path).replace("\\", "/")
                    added_files.append(str(relative_path))
                    ico_count += 1

            if ico_count > 0:
                self.print_info(f"添加了 {ico_count} 个 ICO 图标")

            # 添加其他图片文件
            img_count = 0
            for img_file in images_dir.rglob("*"):
                if img_file.is_file() and img_file.suffix.lower() in [
                    ".png",
                    ".jpg",
                    ".jpeg",
                    ".svg",
                ]:
                    relative_path = img_file.relative_to(self.resource_dir)
                    file_elem = ET.SubElement(qresource_app, "file")
                    file_elem.text = str(relative_path).replace("\\", "/")
                    added_files.append(str(relative_path))
                    img_count += 1

            if img_count > 0:
                self.print_info(f"添加了 {img_count} 个图片资源")

        # 3. 添加翻译资源
        if self.i18n_dir.exists():
            i18n_count = 0
            for qm_file in self.i18n_dir.glob("*.qm"):
                relative_path = qm_file.relative_to(self.resource_dir)
                file_elem = ET.SubElement(qresource_app, "file")
                file_elem.text = str(relative_path).replace("\\", "/")
                added_files.append(str(relative_path))
                i18n_count += 1

            if i18n_count > 0:
                self.print_info(f"添加了 {i18n_count} 个翻译资源")

        # 4. 添加 JSON 资源
        json_count = 0
        for json_file in self.resource_dir.rglob("*.json"):
            if json_file.is_file():
                relative_path = json_file.relative_to(self.resource_dir)
                file_elem = ET.SubElement(qresource_app, "file")
                file_elem.text = str(relative_path).replace("\\", "/")
                added_files.append(str(relative_path))
                json_count += 1

        if json_count > 0:
            self.print_info(f"添加了 {json_count} 个 JSON 资源")

        # 5. 添加 TTF 字体资源
        ttf_count = 0
        for ttf_file in self.resource_dir.rglob("*.ttf"):
            if ttf_file.is_file():
                relative_path = ttf_file.relative_to(self.resource_dir)
                file_elem = ET.SubElement(qresource_app, "file")
                file_elem.text = str(relative_path).replace("\\", "/")
                added_files.append(str(relative_path))
                ttf_count += 1

        if ttf_count > 0:
            self.print_info(f"添加了 {ttf_count} 个 TTF 字体资源")

        # 按字母顺序排序
        qresource_app[:] = sorted(qresource_app, key=lambda x: x.text)

        # 美化 XML
        def indent(elem, level=0):
            indent_str = "    "  # 4个空格缩进
            i = "\n" + level * indent_str
            if len(elem):
                if not elem.text or not elem.text.strip():
                    elem.text = i + indent_str
                if not elem.tail or not elem.tail.strip():
                    elem.tail = i
                for child in elem:
                    indent(child, level + 1)
                if not child.tail or not child.tail.strip():
                    child.tail = i
            else:
                if level and (not elem.tail or not elem.tail.strip()):
                    elem.tail = i

        indent(rcc)

        # 转换为字符串
        xml_str = ET.tostring(rcc, encoding="unicode", method="xml")

        # 保存文件
        qrc_file.write_text(xml_str, encoding="utf-8")

        # 显示添加的文件
        if len(added_files) > 0:
            self.print_success(f"已更新 resource.qrc，包含 {len(added_files)} 个资源文件")
            if len(added_files) <= 20:  # 如果文件不多，显示列表
                self.print_info("添加的资源:")
                for i, file in enumerate(sorted(added_files), 1):
                    print(f"  {i:3d}. {file}")
        else:
            self.print_warning("resource.qrc 中没有找到任何资源")

        return str(qrc_file)

    def find_resource_compiler(self):
        """查找资源编译器 - 优先使用 PySide6 的 pyside6-rcc，然后尝试 PyQt5 的 pyrcc5"""
        # 1. 首先检查系统 PATH 中的 pyside6-rcc
        try:
            result = subprocess.run(
                ["pyside6-rcc", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                self.print_success("找到系统 pyside6-rcc")
                return "pyside6-rcc"
        except:
            pass

        # 2. 检查 Python 脚本目录中的 pyside6-rcc
        script_dir = Path(sys.executable).parent
        pyside6_rcc_exe = script_dir / "pyside6-rcc.exe"
        if pyside6_rcc_exe.exists():
            self.print_success(f"找到 pyside6-rcc.exe: {pyside6_rcc_exe}")
            return str(pyside6_rcc_exe)

        # 3. 检查当前虚拟环境中的 pyside6-rcc
        if hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix:
            # 在虚拟环境中
            venv_script_dir = Path(sys.prefix) / "Scripts"
            if sys.platform != "win32":
                venv_script_dir = Path(sys.prefix) / "bin"

            venv_pyside6_rcc = venv_script_dir / "pyside6-rcc"
            if sys.platform == "win32":
                venv_pyside6_rcc = venv_script_dir / "pyside6-rcc.exe"

            if venv_pyside6_rcc.exists():
                self.print_success(f"找到虚拟环境 pyside6-rcc: {venv_pyside6_rcc}")
                return str(venv_pyside6_rcc)

        # 4. 尝试 PyQt5 的 pyrcc5 作为备选
        try:
            result = subprocess.run(
                ["pyrcc5", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                self.print_success("找到系统 pyrcc5")
                return "pyrcc5"
        except:
            pass

        # 5. 检查 Python 脚本目录中的 pyrcc5
        pyrcc5_exe = script_dir / "pyrcc5.exe"
        if pyrcc5_exe.exists():
            self.print_success(f"找到 pyrcc5.exe: {pyrcc5_exe}")
            return str(pyrcc5_exe)

        # 6. 检查当前虚拟环境中的 pyrcc5
        if hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix:
            venv_pyrcc5 = venv_script_dir / "pyrcc5"
            if sys.platform == "win32":
                venv_pyrcc5 = venv_script_dir / "pyrcc5.exe"

            if venv_pyrcc5.exists():
                self.print_success(f"找到虚拟环境 pyrcc5: {venv_pyrcc5}")
                return str(venv_pyrcc5)

        self.print_error("未找到资源编译器")
        self.print_info("\n解决方案:")
        self.print_info("1. 确保 PySide6 已安装: pip install PySide6")
        self.print_info("2. 或确保 PyQt5 已安装: pip install PyQt5")
        self.print_info("3. 确保资源编译器已添加到系统 PATH")

        return None

    def compile_qrc_to_py(self):
        """简化的编译方法 - 不添加文件头，直接覆盖"""
        self.print_header("编译资源文件")

        qrc_file = self.resource_dir / "resource.qrc"
        output_file = self.common_dir / "resource.py"

        if not qrc_file.exists():
            self.print_error(f"未找到: {qrc_file}")
            return False

        # 先删除可能被占用的文件
        if output_file.exists():
            try:
                output_file.unlink()
                self.print_info("删除旧文件")
                import time

                time.sleep(0.5)  # 等待文件系统释放
            except PermissionError:
                self.print_warning("无法删除旧文件，尝试重命名")
                try:
                    timestamp = int(datetime.now().timestamp())
                    backup_file = output_file.with_name(f"resource_backup_{timestamp}.py")
                    output_file.rename(backup_file)
                    self.print_info(f"已重命名旧文件: {backup_file.name}")
                    import time

                    time.sleep(0.5)
                except:
                    self.print_error("无法处理旧文件")
                    return False

        rcc_path = self.find_resource_compiler()
        if not rcc_path:
            return False

        cmd = [rcc_path, str(qrc_file), "-o", str(output_file)]
        self.print_info(f"命令: {' '.join(cmd)}")

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                if output_file.exists():
                    self.print_success(f"✅ 编译完成: {output_file.name}")
                    self.print_info(f"文件大小: {output_file.stat().st_size} 字节")
                    return True
                else:
                    self.print_error("❌ 未生成输出文件")
                    return False
            else:
                self.print_error(f"❌ 编译失败: {result.stderr}")
                return False

        except Exception as e:
            self.print_error(f"❌ 执行错误: {e}")
            return False

    def verify_resource_file(self, resource_py):
        """验证资源文件是否有效"""
        try:
            # 尝试导入编译的资源文件
            import importlib.util

            spec = importlib.util.spec_from_file_location("temp_resource", resource_py)
            temp_module = importlib.util.module_from_spec(spec)

            # 执行模块
            spec.loader.exec_module(temp_module)

            # 检查是否有 qInitResources 函数
            if hasattr(temp_module, "qInitResources"):
                self.print_info("✅ 资源文件验证通过")
                return True
            else:
                self.print_warning("资源文件可能不完整")
                return False
        except Exception as e:
            self.print_error(f"资源文件验证失败: {e}")
            return False

    def install_pyqt5(self):
        """安装 PyQt5"""
        self.print_header("安装 PyQt5")

        try:
            cmd = [sys.executable, "-m", "pip", "install", "PyQt5"]
            self.print_info(f"执行命令: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=120,
            )

            if result.returncode == 0:
                self.print_success("PyQt5 安装成功")

                # 验证安装
                try:
                    import PyQt5

                    self.print_success("PyQt5 导入成功")
                    return True
                except ImportError:
                    self.print_error("PyQt5 导入失败")
                    return False
            else:
                self.print_error(f"PyQt5 安装失败: {result.stderr}")
                return False

        except Exception as e:
            self.print_error(f"安装过程出错: {e}")
            return False

    def full_workflow(self):
        """完整的翻译资源工作流"""
        self.print_header("FastX-Gui 翻译资源完整工作流")

        steps = [
            (
                "提取翻译字符串",
                lambda: self.extract_translations(verbose=True),
            ),
            ("打开翻译工具", lambda: self.open_linguist()),
            ("编译翻译文件", self.compile_translations),
            ("更新资源文件", self.update_resource_qrc),
            ("编译资源模块", self.compile_qrc_to_py),
        ]

        success = True
        for step_name, step_func in steps:
            print(f"\n步骤: {step_name}")
            print("-" * 40)

            if not step_func():
                self.print_warning(f"步骤 '{step_name}' 未完全成功")
                cont = input("是否继续? (y/n): ").lower()
                if cont != "y":
                    success = False
                    break

        if success:
            self.print_success("\n🎉 所有步骤已完成！")
            self.print_info("\n下一步:")
            self.print_info("1. 在 Qt Linguist 中编辑翻译")
            self.print_info("2. 保存翻译文件")
            self.print_info("3. 重新运行步骤 3-5 编译更新的翻译")
        else:
            self.print_error("\n工作流未完成")

        return success

    def quick_update(self):
        """快速更新（编译现有翻译）"""
        self.print_header("快速更新翻译资源")

        steps = [
            ("编译翻译文件", self.compile_translations),
            ("更新资源文件", self.update_resource_qrc),
            ("编译资源模块", self.compile_qrc_to_py),
        ]

        for step_name, step_func in steps:
            print(f"\n{step_name}...")
            if not step_func():
                self.print_error(f"步骤失败: {step_name}")
                return False

        self.print_success("快速更新完成！")
        return True

    def check_tools(self):
        """检查工具是否存在"""
        self.print_header("检查工具")

        tools = [
            ("lupdate", self.find_lupdate),
            ("lrelease", self.find_lrelease),
            ("linguist", self.find_linguist),
            ("resource compiler", self.find_resource_compiler),
        ]

        all_found = True
        for tool_name, find_func in tools:
            print(f"\n检查 {tool_name}...")
            if find_func():
                self.print_success(f"{tool_name} 可用")
            else:
                self.print_error(f"{tool_name} 不可用")
                all_found = False

        if all_found:
            self.print_success("\n✅ 所有工具都可用")
        else:
            self.print_error("\n❌ 部分工具不可用")

        return all_found

    def show_help(self):
        """显示帮助信息"""
        self.print_header("FastX-Gui 开发工具")

        help_text = """
使用方法:
  python dev.py [命令] [选项]

可用命令:
  check       检查所有工具是否可用
  extract     提取翻译字符串到 .ts 文件
  linguist    打开 Qt Linguist 编辑翻译
  compile     编译 .ts 文件为 .qm 文件
  qrc         更新并编译资源文件
  update      快速更新翻译和资源
  all         完整工作流（提取、编辑、编译）
  help        显示此帮助信息
  list        列出所有源文件
  install     安装 PyQt5
  clean       清理临时文件

选项:
  --verbose   显示详细信息

示例:
  python dev.py check          # 检查工具
  python dev.py clean          # 清理临时文件
  python dev.py extract        # 提取翻译
  python dev.py linguist       # 编辑翻译
  python dev.py compile        # 编译翻译
  python dev.py qrc            # 编译资源
  python dev.py all            # 完整流程

资源访问方式:
  所有资源使用统一前缀: ":/app/"
  例如:
    - 图片: ":/app/images/logo.png"
    - 样式: ":/app/qss/dark/main_window.qss"
    - 翻译: ":/app/i18n/app.zh_CN.qm"
"""
        print(help_text)

    def list_source_files(self):
        """列出所有源文件"""
        self.print_header("列出所有源文件")

        source_files = self.find_source_files()

        if not source_files:
            self.print_warning("没有找到有效的源文件")
            return

        self.print_info(f"找到 {len(source_files)} 个源文件:")

        # 按目录分组显示
        files_by_dir = {}
        for file in source_files:
            dir_name = os.path.dirname(file)
            if dir_name not in files_by_dir:
                files_by_dir[dir_name] = []
            files_by_dir[dir_name].append(os.path.basename(file))

        for dir_name, files in sorted(files_by_dir.items()):
            if dir_name:
                print(f"\n{dir_name}/")
            else:
                print("\n根目录/")

            for file in sorted(files):
                print(f"  - {file}")

    def clean(self):
        """清理临时文件"""
        self.print_header("清理临时文件")

        # 清理 lupdate 生成的临时文件
        self.cleanup_temp_files()

        # 清理可能的其他临时文件
        temp_files = [
            self.project_root / "main.pro",
            self.project_root / "*.ts~",  # 备份文件
        ]

        for temp_file in temp_files:
            if isinstance(temp_file, str):
                # 处理通配符
                import glob

                for file in glob.glob(temp_file):
                    try:
                        os.remove(file)
                        self.print_info(f"清理: {os.path.basename(file)}")
                    except:
                        pass
            elif temp_file.exists():
                try:
                    temp_file.unlink()
                    self.print_info(f"清理: {temp_file.name}")
                except:
                    pass

        self.print_success("清理完成")


def main():
    """主函数"""
    dev_tool = FastXDevTool()

    if len(sys.argv) < 2:
        dev_tool.show_help()
        return

    command = sys.argv[1].lower()
    args = sys.argv[2:]

    verbose = "--verbose" in args

    commands = {
        "check": dev_tool.check_tools,
        "clean": dev_tool.clean,
        "extract": lambda: dev_tool.extract_translations(verbose=verbose),
        "linguist": lambda: dev_tool.open_linguist(),
        "compile": dev_tool.compile_translations,
        "qrc": lambda: dev_tool.update_resource_qrc() and dev_tool.compile_qrc_to_py(),
        "update": dev_tool.quick_update,
        "all": dev_tool.full_workflow,
        "help": dev_tool.show_help,
        "list": dev_tool.list_source_files,
        "install": dev_tool.install_pyqt5,
    }

    if command in commands:
        commands[command]()
    else:
        dev_tool.print_error(f"未知命令: {command}")
        dev_tool.show_help()


if __name__ == "__main__":
    main()
