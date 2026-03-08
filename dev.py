#!/usr/bin/env python3
"""
FastX-Gui 开发工具 - 简化版
用于管理翻译和资源文件
"""

import gc
import glob
import os
import subprocess
import sys
import traceback
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

# 尝试导入 psutil 用于检测文件占用进程
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


class FastXDevTool:
    """FastX-Gui 开发工具类"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.app_dir = self.project_root / "app"
        self.resource_dir = self.app_dir / "resource"
        self.i18n_dir = self.resource_dir / "i18n"
        self.common_dir = self.app_dir / "common"
        self.tools_dir = self.project_root / "tools" / "linguist_5.15.18"

        self.i18n_dir.mkdir(parents=True, exist_ok=True)

        self.exclude_patterns = [
            ".venv", "__pycache__", "*__init__.py", ".git", ".vscode",
            ".idea", "node_modules", "dist", "build", "*.pyc", "*.pyo",
            "*.ui", "ui_*.py", ".DS_Store", "*.json",
        ]

        self.COLORS = {
            "RED": "\033[91m", "GREEN": "\033[92m", "YELLOW": "\033[93m",
            "BLUE": "\033[94m", "CYAN": "\033[96m", "END": "\033[0m", "BOLD": "\033[1m",
        }

    def print_color(self, text, color="GREEN"):
        color_code = self.COLORS.get(color, self.COLORS["END"])
        print(f"{color_code}{text}{self.COLORS['END']}")

    def print_header(self, text):
        print("\n" + "=" * 60)
        self.print_color(f" {text} ", "CYAN")
        print("=" * 60)

    def print_success(self, text): self.print_color(f"✅ {text}", "GREEN")
    def print_error(self, text): self.print_color(f"❌ {text}", "RED")
    def print_warning(self, text): self.print_color(f"⚠️ {text}", "YELLOW")
    def print_info(self, text): self.print_color(f"ℹ️ {text}", "BLUE")

    def print_table(self, headers, rows):
        """打印表格"""
        if not rows:
            return
        
        # 计算列宽
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(cell)))
        
        # 打印表头
        header_line = " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
        separator = "-+-".join("-" * w for w in col_widths)
        print(f"  {header_line}")
        print(f"  {separator}")
        
        # 打印行
        for row in rows:
            row_line = " | ".join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row))
            print(f"  {row_line}")

    def find_file_locking_processes(self, file_path):
        """检测占用指定文件的进程
        
        Args:
            file_path: 文件路径（Path对象或字符串）
            
        Returns:
            list: 占用进程列表，每个元素为 (pid, name, cmdline) 元组
        """
        file_path = str(Path(file_path).resolve())
        locking_processes = []
        
        # 方法1: 使用 psutil 检测
        if HAS_PSUTIL:
            self.print_info("使用 psutil 检测占用进程...")
            try:
                for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'open_files']):
                    try:
                        open_files = proc.info.get('open_files')
                        if open_files:
                            for f in open_files:
                                if f and file_path.lower() in str(f.path).lower():
                                    cmdline = proc.info.get('cmdline') or []
                                    locking_processes.append((
                                        proc.info['pid'],
                                        proc.info['name'],
                                        ' '.join(cmdline) if cmdline else ''
                                    ))
                                    break
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        pass
            except Exception as e:
                self.print_warning(f"psutil 检测失败: {e}")
        
        # 方法2: 使用 handle.exe (Sysinternals) 作为备选
        if not locking_processes:
            handle_exe = self._find_handle_exe()
            if handle_exe:
                self.print_info("使用 handle.exe 检测占用进程...")
                try:
                    # handle.exe 需要管理员权限才能看到所有进程
                    result = subprocess.run(
                        [handle_exe, '-a', '-u', file_path],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    # 解析 handle.exe 输出
                    # 格式示例: python.exe pid: 1234 \BaseNamedObjects\...
                    import re
                    pattern = r'^(.+?)\s+pid:\s*(\d+)\s+'
                    for line in result.stdout.split('\n'):
                        match = re.match(pattern, line.strip())
                        if match:
                            name = match.group(1).strip()
                            pid = int(match.group(2))
                            if (pid, name, '') not in locking_processes:
                                locking_processes.append((pid, name, ''))
                except Exception as e:
                    self.print_warning(f"handle.exe 检测失败: {e}")
        
        return locking_processes

    def _find_handle_exe(self):
        """查找 Sysinternals handle.exe"""
        # 常见安装位置
        possible_paths = [
            Path(os.environ.get('ProgramFiles', 'C:\\Program Files')) / 'Sysinternals' / 'handle.exe',
            Path(os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)')) / 'Sysinternals' / 'handle.exe',
            Path(os.environ.get('USERPROFILE', '')) / 'Downloads' / 'Handle' / 'handle.exe',
            Path(os.environ.get('LOCALAPPDATA', '')) / 'Microsoft' / 'WindowsApps' / 'handle.exe',
        ]
        
        for p in possible_paths:
            if p.exists():
                return str(p)
        
        # 尝试从 PATH 查找
        try:
            result = subprocess.run(['where', 'handle'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return result.stdout.strip().split('\n')[0]
        except:
            pass
        
        return None

    def print_locking_processes(self, file_path):
        """打印占用文件的进程信息"""
        processes = self.find_file_locking_processes(file_path)
        
        if processes:
            self.print_error(f"发现 {len(processes)} 个进程正在占用该文件:")
            self.print_table(
                ["PID", "进程名", "命令行"],
                processes
            )
            self.print_info("解决方案:")
            print("  1. 关闭上述进程")
            print("  2. 或使用任务管理器结束进程:")
            for pid, name, _ in processes:
                print(f"     taskkill /F /PID {pid}  # {name}")
        else:
            self.print_warning("无法确定占用进程，可能原因:")
            print("  1. 没有安装 psutil (pip install psutil)")
            print("  2. 进程权限不足，尝试以管理员身份运行")
            print("  3. 文件被系统服务锁定")
        
        return processes

    def cleanup_temp_files(self):
        """清理临时文件"""
        cleaned = 0
        for pattern in ["*.json", "lupdate_*.tmp"]:
            for temp_file in glob.glob(str(self.project_root / pattern)):
                try:
                    os.remove(temp_file)
                    cleaned += 1
                except:
                    pass
        if cleaned > 0:
            self.print_success(f"清理了 {cleaned} 个临时文件")

    def should_exclude(self, file_path):
        path_str = str(file_path)
        for pattern in self.exclude_patterns:
            if pattern.startswith(".") or pattern.endswith("__"):
                if pattern in path_str.split(os.sep):
                    return True
            elif "*" in pattern:
                import fnmatch
                if fnmatch.fnmatch(file_path.name, pattern):
                    return True
            elif pattern in path_str:
                return True
        return False

    def find_source_files(self):
        source_files = []
        for search_dir in [self.app_dir, self.project_root]:
            if not search_dir.exists():
                continue
            for py_file in search_dir.rglob("*.py"):
                if not self.should_exclude(py_file):
                    source_files.append(str(py_file.relative_to(self.project_root)))
        return sorted(set(source_files))

    def create_main_pro(self):
        source_files = self.find_source_files()
        if not source_files:
            self.print_warning("没有找到有效的源文件")
            return None

        ts_files = [str(f.relative_to(self.project_root)) for f in self.i18n_dir.glob("*.ts")]
        if not ts_files:
            ts_files = [str(self.i18n_dir / "app.zh_CN.ts"), str(self.i18n_dir / "app.zh_HK.ts")]

        source_str = " \\\n            ".join(source_files)
        ts_str = " \\\n                ".join(ts_files)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        pro_content = f"""# Generated by dev.py on {timestamp}
SOURCES += {source_str}
TRANSLATIONS += {ts_str}
CODECFORTR = UTF-8
"""
        (self.project_root / "main.pro").write_text(pro_content, encoding="utf-8")
        self.print_success(f"已更新 main.pro，包含 {len(source_files)} 个源文件")
        return str(self.project_root / "main.pro")

    def run_lupdate(self, pro_file):
        lupdate_exe = self.tools_dir / "lupdate.exe"
        if not lupdate_exe.exists():
            self.print_error(f"未找到 lupdate.exe: {lupdate_exe}")
            return False

        cmd = [str(lupdate_exe), "-no-obsolete", pro_file, "-verbose"]
        self.print_info(f"执行: {os.path.basename(lupdate_exe)} -no-obsolete main.pro -verbose")

        self.cleanup_temp_files()
        result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True, encoding="utf-8", timeout=30)
        self.cleanup_temp_files()

        if result.returncode == 0 or "WARNING: Could not find qmake spec" in result.stderr:
            if "WARNING: Could not find qmake spec" in result.stderr:
                self.print_warning("lupdate 警告（可忽略）: Could not find qmake spec 'default'")
            self.print_success("翻译字符串提取成功")
            return True
        
        self.print_error(f"提取失败: {result.stderr}")
        return False

    def show_translation_stats(self):
        ts_files = list(self.i18n_dir.glob("*.ts"))
        if not ts_files:
            return

        rows = []
        for ts_file in ts_files:
            try:
                tree = ET.parse(ts_file)
                total = sum(1 for _ in tree.getroot().iter("message"))
                translated = sum(1 for m in tree.getroot().iter("message") 
                               if (t := m.find("translation")) is not None and t.get("type") != "unfinished" and t.text)
                progress = f"{translated/total*100:.1f}%" if total > 0 else "0%"
                rows.append([ts_file.name, str(total), str(translated), str(total - translated), progress])
            except Exception as e:
                rows.append([ts_file.name, "错误", "-", "-", str(e)])

        self.print_info("翻译文件统计:")
        self.print_table(["文件", "总计", "已翻译", "未完成", "进度"], rows)

    def extract_translations(self):
        self.print_header("提取翻译字符串")
        pro_file = self.create_main_pro()
        if not pro_file:
            return False
        if self.run_lupdate(pro_file):
            self.show_translation_stats()
            return True
        return False

    def open_linguist(self):
        self.print_header("打开 Qt Linguist")
        linguist_exe = self.tools_dir / "linguist.exe"
        if not linguist_exe.exists():
            self.print_error(f"未找到 linguist.exe: {linguist_exe}")
            return False

        ts_files = list(self.i18n_dir.glob("*.ts"))
        cmd = [str(linguist_exe)] + [str(f) for f in ts_files]
        self.print_info(f"启动: {os.path.basename(linguist_exe)}")
        subprocess.Popen(cmd)
        self.print_success("Qt Linguist 已启动")
        return True

    def compile_translations(self):
        self.print_header("编译翻译文件")
        lrelease_exe = self.tools_dir / "lrelease.exe"
        if not lrelease_exe.exists():
            self.print_error(f"未找到 lrelease.exe: {lrelease_exe}")
            return False

        ts_files = list(self.i18n_dir.glob("*.ts"))
        if not ts_files:
            self.print_warning("没有找到 .ts 文件")
            return False

        rows = []
        for ts_file in ts_files:
            qm_file = ts_file.with_suffix(".qm")
            cmd = [str(lrelease_exe), str(ts_file), "-qm", str(qm_file)]
            result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=10)
            if result.returncode == 0:
                rows.append([ts_file.name, "→", qm_file.name, "✅"])
            else:
                rows.append([ts_file.name, "→", qm_file.name, f"❌ {result.stderr[:50]}"])

        self.print_table(["源文件", "", "目标文件", "状态"], rows)
        return all(r[3].startswith("✅") for r in rows)

    def update_resource_qrc(self):
        self.print_header("更新资源文件")
        qrc_file = self.resource_dir / "resource.qrc"

        rcc = ET.Element("RCC")
        qresource = ET.SubElement(rcc, "qresource", prefix="/app")

        stats = {"QSS": 0, "ICO": 0, "图片": 0, "翻译": 0, "JSON": 0, "TTF": 0}

        # QSS
        qss_dir = self.resource_dir / "qss"
        if qss_dir.exists():
            for f in qss_dir.rglob("*.qss"):
                ET.SubElement(qresource, "file").text = str(f.relative_to(self.resource_dir)).replace("\\", "/")
                stats["QSS"] += 1

        # 图片
        images_dir = self.resource_dir / "images"
        if images_dir.exists():
            for f in images_dir.rglob("*.ico"):
                ET.SubElement(qresource, "file").text = str(f.relative_to(self.resource_dir)).replace("\\", "/")
                stats["ICO"] += 1
            for f in images_dir.rglob("*"):
                if f.suffix.lower() in [".png", ".jpg", ".jpeg", ".svg"]:
                    ET.SubElement(qresource, "file").text = str(f.relative_to(self.resource_dir)).replace("\\", "/")
                    stats["图片"] += 1

        # 翻译
        for f in self.i18n_dir.glob("*.qm"):
            ET.SubElement(qresource, "file").text = str(f.relative_to(self.resource_dir)).replace("\\", "/")
            stats["翻译"] += 1

        # JSON & TTF
        for f in self.resource_dir.rglob("*.json"):
            ET.SubElement(qresource, "file").text = str(f.relative_to(self.resource_dir)).replace("\\", "/")
            stats["JSON"] += 1
        for f in self.resource_dir.rglob("*.ttf"):
            ET.SubElement(qresource, "file").text = str(f.relative_to(self.resource_dir)).replace("\\", "/")
            stats["TTF"] += 1

        # 排序并美化
        qresource[:] = sorted(qresource, key=lambda x: x.text)
        self._indent_xml(rcc)

        qrc_file.write_text(ET.tostring(rcc, encoding="unicode", method="xml"), encoding="utf-8")

        rows = [[k, str(v)] for k, v in stats.items() if v > 0]
        self.print_table(["类型", "数量"], rows)
        self.print_success(f"已更新 resource.qrc，共 {sum(stats.values())} 个资源")
        return True

    def _indent_xml(self, elem, level=0):
        indent_str = "    "
        i = "\n" + level * indent_str
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + indent_str
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for child in elem:
                self._indent_xml(child, level + 1)
            if not child.tail or not child.tail.strip():
                child.tail = i
        elif level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

    def compile_qrc_to_py(self):
        self.print_header("编译资源文件")

        qrc_file = self.resource_dir / "resource.qrc"
        output_file = self.common_dir / "resource.py"

        if not qrc_file.exists():
            self.print_error(f"未找到: {qrc_file}")
            return False

        # 详细诊断文件状态
        self.print_info(f"目标文件: {output_file}")
        self.print_info(f"文件存在: {output_file.exists()}")

        if output_file.exists():
            # 检查文件状态
            stat = output_file.stat()
            self.print_info(f"文件大小: {stat.st_size} 字节")
            self.print_info(f"文件属性: {oct(stat.st_mode)}")

            # 尝试检查文件是否被占用
            try:
                # 尝试以独占模式打开
                with open(output_file, 'r+b') as f:
                    pass
                self.print_info("文件可以以读写模式打开")
            except PermissionError as e:
                self.print_warning(f"文件被占用（PermissionError）: {e}")
            except Exception as e:
                self.print_warning(f"文件访问异常: {type(e).__name__}: {e}")

            # 尝试删除
            self.print_info("尝试删除旧文件...")
            try:
                # 强制垃圾回收，释放可能的引用
                gc.collect()
                output_file.unlink()
                self.print_success("旧文件已删除")
            except PermissionError as e:
                self.print_warning(f"删除失败（PermissionError）: {e}")
                self.print_info("尝试重命名...")
                try:
                    import time
                    timestamp = int(datetime.now().timestamp())
                    backup_file = output_file.with_name(f"resource_backup_{timestamp}.py")
                    output_file.rename(backup_file)
                    self.print_success(f"已重命名为: {backup_file.name}")
                except Exception as e2:
                    self.print_error(f"重命名也失败: {type(e2).__name__}: {e2}")
                    self.print_error("无法处理旧文件，可能有进程正在使用它")
                    # 检测占用进程
                    self.print_locking_processes(output_file)
                    return False
            except Exception as e:
                self.print_error(f"删除失败: {type(e).__name__}: {e}")
                self.print_info(traceback.format_exc())
                return False

        # 查找资源编译器
        rcc_path = self._find_rcc()
        if not rcc_path:
            return False

        cmd = [rcc_path, str(qrc_file), "-o", str(output_file)]
        self.print_info(f"命令: {' '.join(cmd)}")

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                if output_file.exists():
                    self.print_success(f"编译完成: {output_file.name}")
                    self.print_info(f"文件大小: {output_file.stat().st_size} 字节")
                    return True
                else:
                    self.print_error("未生成输出文件")
                    if result.stderr:
                        self.print_error(f"错误输出: {result.stderr}")
                    return False
            else:
                self.print_error(f"编译失败: {result.stderr}")
                return False

        except Exception as e:
            self.print_error(f"执行错误: {type(e).__name__}: {e}")
            self.print_info(traceback.format_exc())
            return False

    def _find_rcc(self):
        """查找资源编译器"""
        # 检查虚拟环境
        script_dir = Path(sys.executable).parent
        venv_rcc = script_dir / "pyside6-rcc.exe" if sys.platform == "win32" else script_dir / "pyside6-rcc"
        
        if venv_rcc.exists():
            self.print_success(f"找到 pyside6-rcc: {venv_rcc}")
            return str(venv_rcc)

        # 检查系统 PATH
        try:
            result = subprocess.run(["pyside6-rcc", "--version"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                self.print_success("找到系统 pyside6-rcc")
                return "pyside6-rcc"
        except:
            pass

        self.print_error("未找到 pyside6-rcc")
        self.print_info("请确保已安装: pip install PySide6")
        return None

    def full_workflow(self):
        """完整工作流"""
        self.print_header("FastX-Gui 翻译资源完整工作流")

        steps = [
            ("提取翻译字符串", self.extract_translations),
            ("打开翻译工具", self.open_linguist),
            ("编译翻译文件", self.compile_translations),
            ("更新资源文件", self.update_resource_qrc),
            ("编译资源模块", self.compile_qrc_to_py),
        ]

        results = []
        for step_name, step_func in steps:
            print(f"\n步骤: {step_name}")
            print("-" * 40)
            try:
                success = step_func()
                results.append([step_name, "✅ 成功" if success else "⚠️ 部分失败"])
                if not success:
                    cont = input("是否继续? (y/n): ").lower()
                    if cont != "y":
                        break
            except Exception as e:
                self.print_error(f"异常: {type(e).__name__}: {e}")
                results.append([step_name, f"❌ 错误: {e}"])
                cont = input("是否继续? (y/n): ").lower()
                if cont != "y":
                    break

        self.print_header("执行结果汇总")
        self.print_table(["步骤", "状态"], results)

        if all("成功" in r[1] or "部分失败" in r[1] for r in results):
            self.print_success("\n🎉 工作流完成！")
        return True


def main():
    dev_tool = FastXDevTool()

    if len(sys.argv) < 2:
        dev_tool.full_workflow()
        return

    command = sys.argv[1].lower()

    if command == "all":
        dev_tool.full_workflow()
    elif command == "help":
        print("用法: python dev.py [all|help]")
    else:
        dev_tool.print_error(f"未知命令: {command}")
        print("用法: python dev.py [all|help]")


if __name__ == "__main__":
    main()
