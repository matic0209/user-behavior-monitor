#!/usr/bin/env python3
"""
优化的PyInstaller打包脚本
专门针对长期运行的用户行为监控系统进行优化
"""

import os
import sys
import subprocess
import shutil
import json
from pathlib import Path
import platform

class OptimizedExeBuilder:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.build_dir = self.project_root / "build"
        self.dist_dir = self.project_root / "dist"
        self.installer_dir = self.project_root / "installer"
        
    def _copy_database_to_dist(self):
        """将项目 data/mouse_data.db 复制到 dist/data/ 下，便于运行时使用真实数据库"""
        try:
            src_db = self.project_root / 'data' / 'mouse_data.db'
            if not src_db.exists():
                print("[WARN] 源数据库不存在: data/mouse_data.db，跳过复制")
                return False
            target_dir = self.dist_dir / 'data'
            target_dir.mkdir(parents=True, exist_ok=True)
            target_db = target_dir / 'mouse_data.db'
            shutil.copy2(src_db, target_db)
            print(f"[OK] 已复制数据库到: {target_db}")
            return True
        except Exception as e:
            print(f"[WARN] 复制数据库到 dist 失败: {e}")
            return False

    def clean_build(self):
        """清理构建目录"""
        print("🧹 清理构建目录...")
        
        dirs_to_clean = ['build', 'dist', '__pycache__']
        for dir_name in dirs_to_clean:
            dir_path = self.project_root / dir_name
            if dir_path.exists():
                shutil.rmtree(dir_path)
                print(f"✓ 已删除 {dir_name}")
        
        # 清理spec文件
        spec_files = list(self.project_root.glob('*.spec'))
        for spec_file in spec_files:
            spec_file.unlink()
            print(f"✓ 已删除 {spec_file.name}")
    
    def install_dependencies(self):
        """安装打包依赖"""
        print("📦 安装打包依赖...")
        
        dependencies = [
            'pyinstaller>=5.0',
            'pywin32>=228',
            'pynput>=1.7.6',
            'xgboost>=1.5.0',
            'scikit-learn>=0.24.0',
            'pandas>=1.2.0',
            'numpy>=1.19.2',
            'pyyaml>=6.0',
            'psutil>=5.8.0'
        ]
        
        for dep in dependencies:
            try:
                subprocess.run([
                    sys.executable, '-m', 'pip', 'install', dep, '--quiet'
                ], check=True, capture_output=True)
                print(f"✓ 已安装 {dep}")
            except subprocess.CalledProcessError as e:
                print(f"✗ 安装 {dep} 失败: {e}")
                return False
        
        return True
    
    def _find_pyinstaller(self):
        """查找pyinstaller可执行文件"""
        try:
            # 方法1: 直接查找pyinstaller命令
            result = subprocess.run(['pyinstaller', '--version'], 
                                 capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"✓ 找到PyInstaller: {result.stdout.strip()}")
                return ['pyinstaller']
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        try:
            # 方法2: 使用python -m pyinstaller
            result = subprocess.run([sys.executable, '-m', 'PyInstaller', '--version'], 
                                 capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"✓ 找到PyInstaller: {result.stdout.strip()}")
                return [sys.executable, '-m', 'PyInstaller']
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        try:
            # 方法3: 使用python -m pyinstaller (小写)
            result = subprocess.run([sys.executable, '-m', 'pyinstaller', '--version'], 
                                 capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"✓ 找到PyInstaller: {result.stdout.strip()}")
                return [sys.executable, '-m', 'pyinstaller']
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        print("✗ 找不到PyInstaller，尝试重新安装...")
        return None
    
    def create_spec_file(self):
        """创建优化的spec文件"""
        print("📝 创建优化的spec文件...")
        
        # 获取项目根目录的绝对路径
        project_root = str(self.project_root.absolute())
        
        spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from pathlib import Path

# 添加项目根目录
project_root = r"{project_root}"
sys.path.insert(0, project_root)

# 数据文件
datas = [
    (os.path.join(project_root, 'src/utils/config'), 'src/utils/config'),
    (os.path.join(project_root, 'data'), 'data'),
    (os.path.join(project_root, 'models'), 'models'),
    (os.path.join(project_root, 'logs'), 'logs'),
    # 强制收集关键模块（对应--collect-all）
    (os.path.join(project_root, 'src/core'), 'src/core'),
    (os.path.join(project_root, 'src/utils'), 'src/utils'),
    (os.path.join(project_root, 'src/predict.py'), 'src/'),
]

# 隐藏导入
hiddenimports = [
    'win32api',
    'win32con', 
    'win32gui',
    'win32service',
    'win32serviceutil',
    'win32event',
    'servicemanager',
    'pynput',
    'pynput.keyboard',
    'pynput.mouse',
    'keyboard',  # 添加keyboard模块
    'xgboost',
    'sklearn',
    'sklearn.ensemble',
    'sklearn.model_selection',
    'pandas',
    'numpy',
    'yaml',
    'psutil',
    'tkinter',
    'tkinter.messagebox',
    'sqlite3',
    'threading',
    'time',
    'json',
    'datetime',
    'pathlib',
    'subprocess',
    'platform',
    'signal',
    'traceback',
    # 添加网络通信模块（心跳功能）
    'urllib.request',
    'urllib.parse',
    'urllib.error'
]

# 排除模块
excludes = [
    'matplotlib',
    'seaborn',
    'PIL',
    'cv2',
    'tensorflow',
    'torch',
    'jupyter',
    'notebook',
    'IPython',
    'pytest',
    'unittest',
    'doctest'
]

a = Analysis(
    [os.path.join(project_root, 'user_behavior_monitor.py')],
    pathex=[project_root],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
    # 数据文件已在上面定义，这里不需要重复添加
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='UserBehaviorMonitor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # 保留控制台用于调试
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None
)
'''
        
        spec_file = self.project_root / "user_behavior_monitor.spec"
        with open(spec_file, 'w', encoding='utf-8') as f:
            f.write(spec_content)
        
        print("✓ spec文件创建完成")
        return spec_file
    
    def build_executable(self):
        """构建可执行文件（兼容build_windows_full.py的函数名）"""
        return self.build_exe()
    
    def build_exe(self):
        """构建可执行文件"""
        print("🔨 开始构建可执行文件...")
        
        # 查找pyinstaller
        pyinstaller_cmd = self._find_pyinstaller()
        if not pyinstaller_cmd:
            print("❌ 找不到PyInstaller，请确保已正确安装")
            return False
        
        # 使用spec文件构建
        cmd = pyinstaller_cmd + [
            '--clean',
            'user_behavior_monitor.spec'
        ]
        
        try:
            print(f"执行命令: {' '.join(cmd)}")
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print("✓ 构建成功!")
            # 构建成功后，复制数据库到 dist
            self._copy_database_to_dist()
            return True
        except subprocess.CalledProcessError as e:
            print(f"✗ 构建失败: {e}")
            print(f"错误输出: {e.stderr}")
            return False
    
    def create_service_exe(self):
        """创建服务可执行文件"""
        print("🔧 创建Windows服务可执行文件...")
        
        # 获取项目根目录的绝对路径
        project_root = str(self.project_root.absolute())
        
        service_spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from pathlib import Path

# 添加项目根目录
project_root = r"{project_root}"
sys.path.insert(0, project_root)

a = Analysis(
    [os.path.join(project_root, 'windows_service.py')],
    pathex=[project_root],
    binaries=[],
    datas=[],
    hiddenimports=[
        'win32api',
        'win32con',
        'win32gui',
        'win32service',
        'win32serviceutil',
        'win32event',
        'servicemanager',
        'pynput',
        'pynput.keyboard',
        'pynput.mouse',
        'xgboost',
        'sklearn',
        'pandas',
        'numpy',
        'yaml',
        'psutil',
        'tkinter',
        'tkinter.messagebox',
        'sqlite3',
        'threading',
        'time',
        'json',
        'datetime',
        'pathlib',
        'subprocess',
        'platform',
        'signal',
        'traceback'
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'seaborn',
        'PIL',
        'cv2',
        'tensorflow',
        'torch',
        'jupyter',
        'notebook',
        'IPython',
        'pytest',
        'unittest',
        'doctest'
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='UserBehaviorMonitorService',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 服务模式无控制台
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None
)
'''
        
        service_spec_file = self.project_root / "windows_service.spec"
        with open(service_spec_file, 'w', encoding='utf-8') as f:
            f.write(service_spec_content)
        
        # 查找pyinstaller
        pyinstaller_cmd = self._find_pyinstaller()
        if not pyinstaller_cmd:
            print("❌ 找不到PyInstaller，请确保已正确安装")
            return False
        
        # 构建服务
        cmd = pyinstaller_cmd + [
            '--clean',
            'windows_service.spec'
        ]
        
        try:
            print(f"执行命令: {' '.join(cmd)}")
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print("✓ 服务构建成功!")
            # 确保数据库也存在于 dist，用于主程序运行
            self._copy_database_to_dist()
            return True
        except subprocess.CalledProcessError as e:
            print(f"✗ 服务构建失败: {e}")
            print(f"错误输出: {e.stderr}")
            return False
    
    def create_installer(self):
        """创建安装包"""
        print("📦 创建安装包...")
        
        # 创建安装目录
        self.installer_dir.mkdir(exist_ok=True)
        
        # 复制可执行文件
        exe_files = [
            "dist/UserBehaviorMonitor.exe",
            "dist/UserBehaviorMonitorService.exe"
        ]
        
        for exe_file in exe_files:
            exe_path = self.project_root / exe_file
            if exe_path.exists():
                shutil.copy2(exe_path, self.installer_dir)
                print(f"✓ 已复制 {exe_file}")
            else:
                print(f"⚠️ 文件不存在: {exe_file}")
        
        # 复制数据库到安装包
        try:
            src_db = self.project_root / 'data' / 'mouse_data.db'
            if src_db.exists():
                installer_data_dir = self.installer_dir / 'data'
                installer_data_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_db, installer_data_dir / 'mouse_data.db')
                print("[OK] 已将数据库复制到安装包: installer/data/mouse_data.db")
            else:
                print("[WARN] 未找到 data/mouse_data.db，安装包不包含数据库")
        except Exception as e:
            print(f"[WARN] 复制数据库到安装包失败: {e}")
        
        # 创建优化的安装脚本
        self._create_install_script()
        
        # 创建卸载脚本
        self._create_uninstall_script()
        
        # 创建配置文件
        self._create_config_files()
        
        # 创建README
        self._create_readme()
        
        print("✓ 安装包创建完成!")
    
    def _create_install_script(self):
        """创建安装脚本"""
        install_script = self.installer_dir / "install.bat"
        with open(install_script, 'w', encoding='utf-8') as f:
            f.write("""@echo off
chcp 65001 >nul
echo ========================================
echo 用户行为监控系统安装程序
echo ========================================

echo.
echo 正在检查管理员权限...
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo 错误: 需要管理员权限运行此程序
    echo 请右键点击此文件，选择"以管理员身份运行"
    pause
    exit /b 1
)

echo ✓ 管理员权限检查通过

echo.
echo 正在安装Windows服务...
UserBehaviorMonitorService.exe install
if %errorLevel% neq 0 (
    echo 警告: 服务安装失败，但程序仍可正常运行
)

echo.
echo 正在启动监控服务...
UserBehaviorMonitorService.exe start
if %errorLevel% neq 0 (
    echo 警告: 服务启动失败，将使用普通模式运行
)

echo.
echo 正在创建必要目录...
if not exist "logs" mkdir logs
if not exist "data" mkdir data
if not exist "models" mkdir models

echo.
echo ========================================
echo 安装完成!
echo ========================================
echo.
echo 系统功能:
echo - 自动采集用户行为数据
echo - 基于机器学习进行异常检测
echo - 检测到异常时自动锁屏保护
echo - 支持手动触发告警测试
echo.
echo 快捷键说明:
echo - 连续按 r 键4次: 重新采集和训练模型
echo - 连续按 a 键4次: 手动触发告警测试
echo - 连续按 q 键4次: 退出系统
echo.
echo 日志文件位置: logs/
echo 配置文件位置: data/
echo.
echo 按任意键退出...
pause >nul
""")
    
    def _create_uninstall_script(self):
        """创建卸载脚本"""
        uninstall_script = self.installer_dir / "uninstall.bat"
        with open(uninstall_script, 'w', encoding='utf-8') as f:
            f.write("""@echo off
chcp 65001 >nul
echo ========================================
echo 用户行为监控系统卸载程序
echo ========================================

echo.
echo 正在检查管理员权限...
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo 错误: 需要管理员权限运行此程序
    echo 请右键点击此文件，选择"以管理员身份运行"
    pause
    exit /b 1
)

echo ✓ 管理员权限检查通过

echo.
echo 正在停止监控服务...
UserBehaviorMonitorService.exe stop

echo.
echo 正在卸载Windows服务...
UserBehaviorMonitorService.exe remove

echo.
echo 正在清理数据文件...
if exist "logs" rmdir /s /q logs
if exist "data" rmdir /s /q data
if exist "models" rmdir /s /q models

echo.
echo ========================================
echo 卸载完成!
echo ========================================
echo.
echo 所有相关文件已清理
echo 按任意键退出...
pause >nul
""")
    
    def _create_config_files(self):
        """创建配置文件"""
        # 创建默认配置
        config_file = self.installer_dir / "config.json"
        default_config = {
            "system": {
                "auto_start": True,
                "run_as_service": True,
                "log_level": "INFO",
                "max_log_size": "10MB",
                "log_rotation": True
            },
            "monitoring": {
                "collection_interval": 0.1,
                "prediction_interval": 30,
                "training_interval": 86400,
                "alert_threshold": 0.8,
                "lock_screen_threshold": 0.8
            },
            "features": {
                "enable_mouse_tracking": True,
                "enable_keyboard_tracking": False,
                "enable_window_tracking": False
            }
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
        
        print("✓ 配置文件创建完成")
    
    def _create_readme(self):
        """创建README文件"""
        readme_file = self.installer_dir / "README.txt"
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write("""用户行为监控系统 v1.2.0
================================

系统说明:
本系统是一个基于机器学习的用户行为异常检测系统，能够实时监控用户行为，
检测异常活动并自动采取安全措施。

主要功能:
✓ 自动采集鼠标行为数据
✓ 基于XGBoost的异常检测
✓ 实时异常行为识别
✓ 自动锁屏保护
✓ 手动告警测试
✓ 后台服务运行

安装说明:
1. 以管理员身份运行 install.bat
2. 系统将自动安装并启动服务
3. 服务将在后台运行，无需用户干预

卸载说明:
1. 以管理员身份运行 uninstall.bat
2. 系统将停止并卸载服务

快捷键:
- 连续按 r 键4次: 重新采集和训练模型
- 连续按 a 键4次: 手动触发告警测试
- 连续按 q 键4次: 退出系统

文件说明:
- UserBehaviorMonitor.exe: 主程序（带控制台）
- UserBehaviorMonitorService.exe: Windows服务程序
- install.bat: 安装脚本
- uninstall.bat: 卸载脚本
- config.json: 配置文件
- logs/: 日志文件目录
- data/: 数据文件目录
- models/: 模型文件目录

日志文件:
- logs/user_behavior_monitor.log: 主程序日志
- logs/windows_service.log: 服务日志
- logs/error_*.log: 错误日志
- logs/debug_*.log: 调试日志

注意事项:
- 首次运行需要采集足够的数据才能开始检测
- 系统会自动在后台运行，无需手动启动
- 如遇问题请查看日志文件
- 建议定期备份data目录中的数据

技术支持:
如有问题请联系技术支持团队

版本信息:
- 版本: v1.2.0
- 构建时间: """ + platform.system() + " " + platform.release() + """
- Python版本: """ + platform.python_version() + """
""")
    
    def optimize_for_long_term(self):
        """针对长期运行进行优化"""
        print("⚡ 针对长期运行进行优化...")
        
        # 创建优化配置文件
        optimization_config = {
            "memory_management": {
                "enable_garbage_collection": True,
                "gc_interval": 300,  # 5分钟
                "max_memory_usage": "512MB"
            },
            "performance": {
                "enable_caching": True,
                "cache_size": 1000,
                "prediction_batch_size": 100
            },
            "reliability": {
                "auto_restart_on_crash": True,
                "max_restart_attempts": 3,
                "restart_delay": 30
            },
            "logging": {
                "log_rotation": True,
                "max_log_files": 10,
                "max_log_size": "10MB",
                "compress_old_logs": True
            }
        }
        
        config_file = self.project_root / "optimization_config.json"
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(optimization_config, f, indent=2, ensure_ascii=False)
        
        print("✓ 优化配置创建完成")
    
    def check_windows(self):
        """检查是否在Windows环境下（兼容build_windows_full.py的功能）"""
        if sys.platform != 'win32':
            print("❌ 错误: 此脚本只能在Windows系统上运行")
            return False
        return True
    
    def check_dependencies(self):
        """检查依赖是否安装（兼容build_windows_full.py的功能）"""
        print("🔍 检查依赖...")
        
        required_modules = [
            'psutil',
            'pynput',
            'keyboard',
            'yaml',
            'numpy',
            'pandas',
            'sklearn',
            'xgboost',
            'win32api',
            'win32con',
            'win32gui',
            'win32service',
            'win32serviceutil'
        ]
        
        missing_modules = []
        
        for module in required_modules:
            try:
                __import__(module)
                print(f"✓ {module} 可用")
            except ImportError:
                print(f"✗ {module} 缺失")
                missing_modules.append(module)
        
        if missing_modules:
            print(f"\n❌ 以下模块缺失: {missing_modules}")
            print("💡 请先运行: python install_dependencies_windows.py")
            return False
        
        print("✓ 所有依赖检查通过")
        return True
    
    def setup_environment(self):
        """设置环境（兼容build_windows_full.py的功能）"""
        # 注意：此处避免使用表情符号，防止在 GBK 控制台下触发编码错误
        print("[SETUP] 设置环境...")
        
        # 设置编码
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        os.environ['PYTHONUTF8'] = '1'
        
        # 运行时重配置标准输出/错误编码，避免 Windows GBK 控制台下的 UnicodeEncodeError
        try:
            # Python 3.7+ 支持 reconfigure
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            # 老版本或非 TTY 环境下忽略
            pass
        
        # 设置控制台编码（Windows）
        if sys.platform == 'win32':
            os.system('chcp 65001 > nul 2>&1')
        
        # 依然避免使用不在 GBK 的符号，保证在极端环境下也不会报错
        print("[OK] 环境设置完成")
    
    def kill_conflicting_processes(self):
        """结束冲突的进程（兼容build_windows_full.py的功能）"""
        print("🔪 检查并结束冲突进程...")
        
        # 获取当前进程ID
        current_pid = os.getpid()
        print(f"当前进程ID: {current_pid}")
        
        processes = ['UserBehaviorMonitor.exe', 'pyinstaller.exe']
        
        for process_name in processes:
            try:
                # 使用tasklist查找进程
                result = subprocess.run(['tasklist', '/FI', f'IMAGENAME eq {process_name}'], 
                                     capture_output=True, text=True, timeout=10)
                
                if process_name in result.stdout:
                    print(f"发现冲突进程: {process_name}")
                    
                    # 尝试结束进程
                    try:
                        subprocess.run(['taskkill', '/F', '/IM', process_name], 
                                     capture_output=True, timeout=10)
                        print(f"✓ 已结束进程: {process_name}")
                    except subprocess.TimeoutExpired:
                        print(f"⚠ 结束进程超时: {process_name}")
                    except Exception as e:
                        print(f"⚠ 结束进程失败: {process_name}, 错误: {e}")
                        
            except subprocess.TimeoutExpired:
                print(f"⚠ 检查进程超时: {process_name}")
            except Exception as e:
                print(f"⚠ 检查进程失败: {process_name}, 错误: {e}")
        
        print("✓ 进程检查完成")
    
    def build(self):
        """执行完整构建流程"""
        # 先设置环境，确保后续包含表情/中文的输出在 Windows 控制台不会因 GBK 编码报错
        self.setup_environment()
        print("🚀 开始优化构建流程...")
        print("=" * 50)
        
        # 检查操作系统
        if sys.platform != 'win32':
            print("❌ 错误: 此脚本只能在Windows系统上运行")
            return False
        
        try:
            # 检查Windows环境
            if not self.check_windows():
                return False
            
            # 检查依赖
            if not self.check_dependencies():
                return False
            
            # 结束冲突进程
            self.kill_conflicting_processes()
            
            # 清理构建目录
            self.clean_build()
            
            # 等待文件系统稳定
            print("⏳ 等待文件系统稳定...")
            import time
            time.sleep(2)
            print("✓ 等待完成")
            
            # 安装依赖
            if not self.install_dependencies():
                return False
            
            # 针对长期运行进行优化
            self.optimize_for_long_term()
            
            # 创建spec文件
            self.create_spec_file()
            
            # 构建主程序
            if not self.build_exe():
                return False
            
            # 构建服务程序
            if not self.create_service_exe():
                return False
            
            # 创建安装包
            self.create_installer()
            
            print("\n" + "=" * 50)
            print("✅ 构建完成!")
            print("=" * 50)
            print("📁 可执行文件位置: dist/")
            print("📦 安装包位置: installer/")
            print("🔧 优化配置: optimization_config.json")
            print("\n📋 下一步:")
            print("1. 测试 dist/UserBehaviorMonitor.exe")
            print("2. 以管理员身份运行 installer/install.bat")
            print("3. 检查 logs/ 目录中的日志文件")
            
            return True
            
        except Exception as e:
            print(f"❌ 构建过程中出现错误: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """主函数"""
    print("用户行为监控系统 - 优化构建工具")
    print("专门针对长期运行进行优化")
    print("=" * 50)
    
    builder = OptimizedExeBuilder()
    success = builder.build()
    
    if success:
        print("\n🎉 构建成功完成!")
    else:
        print("\n❌ 构建失败!")

if __name__ == '__main__':
    main() 