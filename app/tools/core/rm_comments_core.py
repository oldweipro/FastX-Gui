import io
import os
import re
import tokenize
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from loguru import logger


@dataclass
class CleanerConfig:
    """清理配置类"""
    remove_comments: bool = True  # 是否删除单行注释
    remove_docstrings: bool = True  # 是否删除文档字符串
    remove_empty_lines: bool = True  # 是否删除空行
    keep_triple_quotes: bool = False  # 是否保留三引号字符串（仅当删除文档字符串时有效）
    output_suffix: str = "_clean.py"  # 输出文件后缀


class PyCodeCleaner:
    """Python代码清理器业务类"""

    def __init__(self,
                 input_path: str,
                 output_path: str | None = None,
                 exclude_files: list[str] | None = None,
                 exclude_patterns: list[str] | None = None,
                 config: CleanerConfig | None = None):
        """
        初始化清理器

        Args:
            input_path: 输入路径（文件或目录）
            output_path: 输出路径，如果为None则自动生成
            exclude_files: 要排除的文件名列表
            exclude_patterns: 要排除的文件名模式（支持通配符）
            config: 清理配置
        """
        self.input_path = Path(input_path)
        self.output_path = Path(output_path) if output_path else None

        self.exclude_files = set(exclude_files or [])
        self.exclude_patterns = exclude_patterns or []

        self.config = config or CleanerConfig()

        # 处理统计
        self.stats = {
            'total_files': 0,
            'processed': 0,
            'skipped': 0,
            'errors': 0
        }

        # 回调函数
        self.progress_callback: Callable | None = None
        self.log_callback: Callable | None = None
        self.error_callback: Callable | None = None

    def set_callbacks(self,
                      progress_callback: Callable | None = None,
                      log_callback: Callable | None = None,
                      error_callback: Callable | None = None):
        """设置回调函数"""
        self.progress_callback = progress_callback
        self.log_callback = log_callback
        self.error_callback = error_callback

    def _log(self, message: str, level: str = "info"):
        """记录日志"""
        if self.log_callback:
            self.log_callback(message, level)

    def _update_progress(self, current: int, total: int):
        """更新进度"""
        if self.progress_callback:
            self.progress_callback(current, total)

    def _handle_error(self, error: Exception, context: str = ""):
        """处理错误"""
        if self.error_callback:
            self.error_callback(error, context)

    def _is_docstring(self, prev_tok, tok, next_tok=None) -> bool:
        """
        判断给定的 STRING token 是否为文档字符串

        Args:
            prev_tok: 前一个token
            tok: 当前token
            next_tok: 下一个token（可选）

        Returns:
            是否为文档字符串
        """
        # 如果配置保留三引号字符串，并且是三引号，则不作为docstring处理
        if self.config.keep_triple_quotes and tok.string.startswith('"""'):
            return False

        # 模块级 docstring：文件开头紧跟 ENCODING 的第一个 STRING
        if prev_tok and prev_tok.type == tokenize.ENCODING:
            return True

        # 函数/类的 docstring：STRING 紧跟在 INDENT 之后
        if prev_tok and prev_tok.type == tokenize.INDENT:
            return True

        # 或者 STRING 紧跟在 NL/NEWLINE + INDENT 之后（处理多行定义）
        if prev_tok and prev_tok.type in (tokenize.NL, tokenize.NEWLINE):
            # 需要检查前前一个token
            return False

        return False

    def _should_exclude_file(self, filepath: Path) -> bool:
        """判断文件是否应该被排除"""
        filename = filepath.name

        # 检查排除的文件名
        if filename in self.exclude_files:
            self._log(f"跳过排除文件: {filename}", "info")
            return True

        # 检查排除模式
        for pattern in self.exclude_patterns:
            if re.match(pattern.replace("*", ".*").replace("?", "."), filename):
                self._log(f"跳过模式匹配文件: {filename} (模式: {pattern})", "info")
                return True

        return False

    def _clean_code(self, code: str) -> str:
        """
        清理代码的核心逻辑

        Args:
            code: 原始代码

        Returns:
            清理后的代码
        """
        result = []
        code_bytes = io.BytesIO(code.encode("utf-8"))

        try:
            prev_tok = None
            tokens = list(tokenize.tokenize(code_bytes.readline))

            for i, tok in enumerate(tokens):
                next_tok = tokens[i + 1] if i + 1 < len(tokens) else None

                # 删除单行注释
                if self.config.remove_comments and tok.type == tokenize.COMMENT:
                    prev_tok = tok
                    continue

                # 删除文档字符串
                if (self.config.remove_docstrings and tok.type == tokenize.STRING and
                        self._is_docstring(prev_tok, tok, next_tok)):
                    prev_tok = tok
                    continue

                # 保留其他 token
                result.append((tok.type, tok.string))
                prev_tok = tok

            # 反tokenize得到代码
            cleaned = tokenize.untokenize(result).decode("utf-8")

            # 删除空行
            if self.config.remove_empty_lines:
                lines = []
                for line in cleaned.splitlines():
                    if line.strip() == "":
                        continue
                    lines.append(line)
                cleaned = "\n".join(lines)

            return cleaned

        except Exception as e:
            self._handle_error(e, "清理代码时出错")
            raise

    def process_single_file(self, input_file: Path, output_file: Path | None = None) -> bool:
        """
        处理单个文件

        Args:
            input_file: 输入文件路径
            output_file: 输出文件路径，如果为None则自动生成

        Returns:
            处理是否成功
        """
        try:
            self._log(f"开始处理文件: {input_file}", "info")

            # 读取文件
            with open(input_file, encoding="utf-8") as f:
                code = f.read()

            # 清理代码
            cleaned_code = self._clean_code(code)

            # 确定输出路径
            if output_file is None:
                output_file = input_file.parent / f"{input_file.stem}{self.config.output_suffix}"

            # 确保输出目录存在
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # 写入文件
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(cleaned_code)

            self._log(f"文件处理完成: {input_file} -> {output_file}", "success")
            self.stats['processed'] += 1
            return True

        except Exception as e:
            self._log(f"处理文件失败: {input_file} - {str(e)}", "error")
            self.stats['errors'] += 1
            return False

    def process_directory(self,
                          input_dir: Path,
                          output_dir: Path | None = None,
                          recursive: bool = False) -> dict:
        """
        处理目录

        Args:
            input_dir: 输入目录
            output_dir: 输出目录，如果为None则使用输入目录
            recursive: 是否递归处理子目录

        Returns:
            处理统计信息
        """
        # 重置统计
        self.stats = {'total_files': 0, 'processed': 0, 'skipped': 0, 'errors': 0}

        # 收集所有Python文件
        py_files = []

        if recursive:
            for root, dirs, files in os.walk(input_dir):
                root_path = Path(root)
                for file in files:
                    if file.endswith('.py'):
                        py_files.append(root_path / file)
        else:
            for item in input_dir.iterdir():
                if item.is_file() and item.suffix == '.py':
                    py_files.append(item)

        self.stats['total_files'] = len(py_files)
        self._log(f"找到 {len(py_files)} 个Python文件", "info")

        # 处理文件
        for i, py_file in enumerate(py_files):
            # 更新进度
            self._update_progress(i + 1, len(py_files))

            # 检查是否排除
            if self._should_exclude_file(py_file):
                self.stats['skipped'] += 1
                continue

            # 确定输出路径
            if output_dir:
                if recursive:
                    # 保持目录结构
                    relative_path = py_file.relative_to(input_dir)
                    out_file = output_dir / relative_path.parent / f"{py_file.stem}{self.config.output_suffix}"
                else:
                    out_file = output_dir / f"{py_file.stem}{self.config.output_suffix}"
            else:
                out_file = None

            # 处理文件
            self.process_single_file(py_file, out_file)

        return self.stats

    def process(self) -> dict:
        """
        主要处理入口

        Returns:
            处理统计信息
        """
        self._log("开始代码清理任务", "info")

        if self.input_path.is_file():
            # 处理单个文件
            if self.output_path and self.output_path.is_dir():
                # 输出是目录，在目录中创建新文件
                out_file = self.output_path / f"{self.input_path.stem}{self.config.output_suffix}"
                success = self.process_single_file(self.input_path, out_file)
            else:
                # 输出是文件或None
                success = self.process_single_file(self.input_path, self.output_path)

            self.stats['total_files'] = 1
            self.stats['processed'] = 1 if success else 0
            self.stats['errors'] = 0 if success else 1

        elif self.input_path.is_dir():
            # 处理目录
            recursive = False  # 可以根据需要修改
            return self.process_directory(self.input_path, self.output_path, recursive)

        else:
            error_msg = f"输入路径不存在: {self.input_path}"
            self._log(error_msg, "error")
            raise FileNotFoundError(error_msg)

        return self.stats


class RmCommentsCore:
    """Remove Comments Core class"""

    def execute(
        self,
        input_path,
        output_path,
        remove_comments=True,
        remove_docstrings=True,
        remove_empty_lines=True,
        keep_triple_quotes=False,
        output_suffix="_clean.py",
        recursive=False,
        exclude_files=None,
        exclude_patterns=None
    ):
        """
        执行代码清理

        Args:
            input_path: 输入路径
            output_path: 输出路径
            remove_comments: 是否移除注释
            remove_docstrings: 是否移除文档字符串
            remove_empty_lines: 是否移除空行
            keep_triple_quotes: 是否保留三引号字符串
            output_suffix: 输出文件后缀
            recursive: 是否递归处理子目录
            exclude_files: 排除的文件名列表
            exclude_patterns: 排除的文件模式列表

        Returns:
            处理统计信息
        """
        # 创建配置
        config = CleanerConfig(
            remove_comments=remove_comments,
            remove_docstrings=remove_docstrings,
            remove_empty_lines=remove_empty_lines,
            keep_triple_quotes=keep_triple_quotes,
            output_suffix=output_suffix
        )

        # 创建清理器
        cleaner = PyCodeCleaner(
            input_path=input_path,
            output_path=output_path,
            exclude_files=exclude_files or [],
            exclude_patterns=exclude_patterns or [],
            config=config
        )

        # 设置回调
        def log_callback(message, level):
            logger.trace(f"[{level}] {message}")

        def progress_callback(current, total):
            logger.debug(f"Progress: {current}/{total}")

        def error_callback(error, context):
            logger.error(f"Error ({context}): {str(error)}")

        cleaner.set_callbacks(
            log_callback=log_callback,
            progress_callback=progress_callback,
            error_callback=error_callback
        )

        # 执行清理
        stats = cleaner.process()

        return stats
