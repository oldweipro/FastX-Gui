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
    remove_comments: bool = True
    remove_docstrings: bool = True
    remove_empty_lines: bool = True
    keep_triple_quotes: bool = False
    output_suffix: str = "_clean.py"


class PyCodeCleaner:
    """Python代码清理器业务类"""

    def __init__(self,
                 input_path: str,
                 output_path: str | None = None,
                 exclude_files: list[str] | None = None,
                 exclude_patterns: list[str] | None = None,
                 config: CleanerConfig | None = None):
        self.input_path = Path(input_path)
        self.output_path = Path(output_path) if output_path else None
        self.exclude_files = set(exclude_files or [])
        self.exclude_patterns = exclude_patterns or []
        self.config = config or CleanerConfig()
        self.stats = {'total_files': 0, 'processed': 0, 'skipped': 0, 'errors': 0}
        self.progress_callback: Callable | None = None
        self.log_callback: Callable | None = None
        self.error_callback: Callable | None = None

    def set_callbacks(self,
                      progress_callback: Callable | None = None,
                      log_callback: Callable | None = None,
                      error_callback: Callable | None = None):
        self.progress_callback = progress_callback
        self.log_callback = log_callback
        self.error_callback = error_callback

    def _log(self, message: str, level: str = "info"):
        if self.log_callback:
            self.log_callback(message, level)

    def _update_progress(self, current: int, total: int):
        if self.progress_callback:
            self.progress_callback(current, total)

    def _is_docstring(self, prev_tok, tok, next_tok=None) -> bool:
        if self.config.keep_triple_quotes and tok.string.startswith('"""'):
            return False
        if prev_tok and prev_tok.type == tokenize.ENCODING:
            return True
        if prev_tok and prev_tok.type == tokenize.INDENT:
            return True
        return False

    def _should_exclude_file(self, filepath: Path) -> bool:
        filename = filepath.name
        if filename in self.exclude_files:
            return True
        for pattern in self.exclude_patterns:
            if re.match(pattern.replace("*", ".*").replace("?", "."), filename):
                return True
        return False

    def _clean_code(self, code: str) -> str:
        result = []
        code_bytes = io.BytesIO(code.encode("utf-8"))
        try:
            prev_tok = None
            tokens = list(tokenize.tokenize(code_bytes.readline))
            for i, tok in enumerate(tokens):
                next_tok = tokens[i + 1] if i + 1 < len(tokens) else None
                if self.config.remove_comments and tok.type == tokenize.COMMENT:
                    prev_tok = tok
                    continue
                if (self.config.remove_docstrings and tok.type == tokenize.STRING and
                        self._is_docstring(prev_tok, tok, next_tok)):
                    prev_tok = tok
                    continue
                result.append((tok.type, tok.string))
                prev_tok = tok
            cleaned = tokenize.untokenize(result).decode("utf-8")
            if self.config.remove_empty_lines:
                lines = [line for line in cleaned.splitlines() if line.strip() != ""]
                cleaned = "\n".join(lines)
            return cleaned
        except Exception as e:
            raise

    def process_single_file(self, input_file: Path, output_file: Path | None = None) -> bool:
        try:
            with open(input_file, encoding="utf-8") as f:
                code = f.read()
            cleaned_code = self._clean_code(code)
            if output_file is None:
                output_file = input_file.parent / f"{input_file.stem}{self.config.output_suffix}"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(cleaned_code)
            self.stats['processed'] += 1
            return True
        except Exception as e:
            self.stats['errors'] += 1
            return False

    def process_directory(self, input_dir: Path, output_dir: Path | None = None, recursive: bool = False) -> dict:
        self.stats = {'total_files': 0, 'processed': 0, 'skipped': 0, 'errors': 0}
        py_files = []
        if recursive:
            for root, dirs, files in os.walk(input_dir):
                for file in files:
                    if file.endswith('.py'):
                        py_files.append(Path(root) / file)
        else:
            for item in input_dir.iterdir():
                if item.is_file() and item.suffix == '.py':
                    py_files.append(item)
        self.stats['total_files'] = len(py_files)
        for i, py_file in enumerate(py_files):
            self._update_progress(i + 1, len(py_files))
            if self._should_exclude_file(py_file):
                self.stats['skipped'] += 1
                continue
            if output_dir:
                if recursive:
                    relative_path = py_file.relative_to(input_dir)
                    out_file = output_dir / relative_path.parent / f"{py_file.stem}{self.config.output_suffix}"
                else:
                    out_file = output_dir / f"{py_file.stem}{self.config.output_suffix}"
            else:
                out_file = None
            self.process_single_file(py_file, out_file)
        return self.stats

    def process(self) -> dict:
        if self.input_path.is_file():
            if self.output_path and self.output_path.is_dir():
                out_file = self.output_path / f"{self.input_path.stem}{self.config.output_suffix}"
                success = self.process_single_file(self.input_path, out_file)
            else:
                success = self.process_single_file(self.input_path, self.output_path)
            self.stats['total_files'] = 1
            self.stats['processed'] = 1 if success else 0
            self.stats['errors'] = 0 if success else 1
        elif self.input_path.is_dir():
            return self.process_directory(self.input_path, self.output_path, False)
        else:
            raise FileNotFoundError(f"输入路径不存在: {self.input_path}")
        return self.stats


class CodeCleanerCore:
    """Code Cleaner Core class"""

    def execute(self, input_path, output_path, remove_comments=True, remove_docstrings=True,
                remove_empty_lines=True, keep_triple_quotes=False, output_suffix="_clean.py",
                recursive=False, exclude_files=None, exclude_patterns=None):
        config = CleanerConfig(
            remove_comments=remove_comments,
            remove_docstrings=remove_docstrings,
            remove_empty_lines=remove_empty_lines,
            keep_triple_quotes=keep_triple_quotes,
            output_suffix=output_suffix
        )
        cleaner = PyCodeCleaner(
            input_path=input_path,
            output_path=output_path,
            exclude_files=exclude_files or [],
            exclude_patterns=exclude_patterns or [],
            config=config
        )
        return cleaner.process()
