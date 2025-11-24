#!/usr/bin/env python3
"""一键封装 Win7 打包流程的自动化脚本."""

from __future__ import annotations

import argparse
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List, Optional


ROOT_DIR = Path(__file__).resolve().parent
ARCHIVE_DIR = ROOT_DIR / "archive"
REQUIREMENTS_FILE = ROOT_DIR / "requirements.txt"

# 支持的构建脚本映射，方便未来扩展
BUILD_TARGETS = {
    "release": ROOT_DIR / "build_release.py",
    "safe": ROOT_DIR / "build_safe.py",
    "quick": ROOT_DIR / "quick_build.py",
    "simple": ROOT_DIR / "simple_build.py",
    "optimized": ROOT_DIR / "build_optimized_exe.py",
    "full": ROOT_DIR / "build_windows_full.py",
    "cross": ROOT_DIR / "build_cross_platform.py",
}

EXTRA_PACKAGES = [
    "pyinstaller>=5.13",
    "pywin32>=305",
    "keyboard>=0.13.5",
]


class StepError(RuntimeError):
    """在执行某个步骤时失败抛出的统一异常."""


def log_step(title: str) -> None:
    print("\n" + "=" * 70)
    print(f"[STEP] {title}")
    print("=" * 70)


def run_command(cmd: List[str], description: str, env: Optional[dict] = None) -> None:
    """运行外部命令并在失败时抛出 StepError."""

    log_step(description)
    full_env = os.environ.copy()
    if env:
        full_env.update(env)

    print(f"[CMD] {' '.join(str(part) for part in cmd)}")
    try:
        subprocess.run(cmd, check=True, env=full_env)
    except subprocess.CalledProcessError as exc:
        raise StepError(
            f"命令执行失败 (exit={exc.returncode}): {' '.join(cmd)}"
        ) from exc


def ensure_utf8_console() -> None:
    """确保后续子进程使用 UTF-8 输出."""

    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    os.environ.setdefault("PYTHONUTF8", "1")

    if platform.system() == "Windows":
        # 强制切换为 UTF-8 代码页，忽略执行失败
        subprocess.run("chcp 65001 > nul", shell=True, check=False)
        print("[INFO] 已尝试将控制台代码页切换到 UTF-8")


def pip_install(args: Iterable[str], description: str) -> None:
    cmd = [sys.executable, "-m", "pip", "install"] + list(args)
    run_command(cmd, description)


def install_requirements() -> None:
    if not REQUIREMENTS_FILE.exists():
        raise StepError(f"未找到依赖清单: {REQUIREMENTS_FILE}")
    pip_install(["--upgrade", "pip", "wheel", "setuptools"], "升级 pip/wheel/setuptools")
    pip_install(["-r", str(REQUIREMENTS_FILE)], "安装项目 requirements")
    extra_packages: List[str]
    if platform.system() == "Windows":
        extra_packages = EXTRA_PACKAGES
    else:
        extra_packages = [EXTRA_PACKAGES[0]]  # 仅安装 PyInstaller 以便调试
    pip_install(extra_packages, "安装额外的构建依赖 (PyInstaller 等)")


def run_python_script(script_path: Path, description: str) -> None:
    if not script_path.exists():
        raise StepError(f"找不到脚本: {script_path}")
    run_command([sys.executable, str(script_path)], description)


def ensure_release_script() -> None:
    """必要时运行修复脚本来生成 build_release.py."""

    release_script = BUILD_TARGETS["release"]
    if release_script.exists():
        return

    fix_release = ARCHIVE_DIR / "fix_release_issues.py"
    if not fix_release.exists():
        raise StepError("缺少 archive/fix_release_issues.py，无法自动创建 build_release.py")

    run_python_script(fix_release, "运行 fix_release_issues.py 以生成 build_release.py")
    if not release_script.exists():
        raise StepError("fix_release_issues.py 执行后仍未生成 build_release.py")


def clean_permissions() -> None:
    if platform.system() != "Windows":
        print("[INFO] 非 Windows 平台，跳过权限修复脚本")
        return

    fixer = ARCHIVE_DIR / "fix_permission.py"
    if fixer.exists():
        run_python_script(fixer, "执行权限&清理修复脚本")
    else:
        print("[WARN] 未找到 archive/fix_permission.py，跳过清理步骤")


def select_build_script(builder: str, custom: Optional[str]) -> Path:
    if custom:
        path = Path(custom).expanduser()
        if not path.exists():
            raise StepError(f"自定义构建脚本不存在: {path}")
        return path

    if builder not in BUILD_TARGETS:
        raise StepError(f"未知构建类型: {builder}")

    script_path = BUILD_TARGETS[builder]
    if builder == "release":
        ensure_release_script()

    if not script_path.exists():
        raise StepError(f"构建脚本 {builder} ({script_path}) 不存在，请先准备此脚本或使用 release 模式")

    return script_path


def run_build(script_path: Path) -> None:
    run_command([sys.executable, str(script_path)], f"运行构建脚本: {script_path.name}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Win7 环境下一键安装依赖、修复并执行打包的辅助脚本",
    )
    parser.add_argument(
        "--builder",
        choices=sorted(BUILD_TARGETS.keys()),
        default="release",
        help="要运行的构建脚本类型 (默认: release)",
    )
    parser.add_argument(
        "--custom-script",
        help="传入完整路径以运行自定义构建脚本（覆盖 --builder）",
    )
    parser.add_argument(
        "--skip-install",
        action="store_true",
        help="跳过 pip 依赖安装步骤",
    )
    parser.add_argument(
        "--skip-fixes",
        action="store_true",
        help="跳过权限清理与 fix_release_issues 等修复步骤",
    )
    parser.add_argument(
        "--only-install",
        action="store_true",
        help="只安装依赖与执行修复，不触发构建",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if platform.system() != "Windows":
        print("[WARN] 当前不是 Windows 系统，脚本仍会执行，但 Win7 专属操作可能无效")
    else:
        print(f"[INFO] 检测到 Windows {platform.release()} ({platform.version()})")

    ensure_utf8_console()

    if not args.skip_install:
        install_requirements()
    else:
        print("[INFO] 已跳过依赖安装")

    if not args.skip_fixes:
        clean_permissions()
        if args.builder == "release" and not args.custom_script:
            ensure_release_script()
    else:
        print("[INFO] 已跳过修复/清理步骤")

    if args.only_install:
        print("[INFO] 仅执行安装/修复，未触发构建。")
        return

    build_script = select_build_script(args.builder, args.custom_script)
    run_build(build_script)


if __name__ == "__main__":
    try:
        main()
    except StepError as exc:
        print(f"\n[ERROR] {exc}")
        sys.exit(1)
