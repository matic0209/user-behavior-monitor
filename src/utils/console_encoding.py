"""
控制台编码工具：确保在 Windows 控制台下安全输出 Unicode（含中文/表情）。

使用方式：

from src.utils.console_encoding import ensure_utf8_console
ensure_utf8_console()
"""

import os
import sys


def ensure_utf8_console():
    """确保 stdout/stderr 使用 UTF-8，并在 Windows 下切换代码页。

    - 设置 PYTHONUTF8=1 和 PYTHONIOENCODING=utf-8
    - 尝试将 sys.stdout/sys.stderr 重新配置为 utf-8 + errors='replace'
    - Windows 平台执行 chcp 65001，避免 GBK 控制台编码报错
    """
    try:
        os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
        os.environ.setdefault('PYTHONUTF8', '1')

        try:
            if hasattr(sys.stdout, 'reconfigure'):
                sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            if hasattr(sys.stderr, 'reconfigure'):
                sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass

        if sys.platform == 'win32':
            try:
                os.system('chcp 65001 > nul 2>&1')
            except Exception:
                pass
    except Exception:
        # 编码设置失败时忽略，避免阻断主流程
        pass


