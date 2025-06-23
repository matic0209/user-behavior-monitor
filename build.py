import os
import sys
import shutil
import subprocess
from datetime import datetime
from src.core.data_collector.windows_mouse_collector import WindowsMouseCollector
from src.core.feature_engineer.windows_feature_processor import WindowsFeatureProcessor

def clean_build_dirs():
    """清理构建目录"""
    dirs_to_clean = ['build', 'dist']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
    if os.path.exists('UserBehaviorMonitor.spec'):
        os.remove('UserBehaviorMonitor.spec')

def create_version_file():
    """创建版本信息文件"""
    version_info = f"""
# UTF-8
#
# For more details about fixed file info 'ffi' see:
# http://msdn.microsoft.com/en-us/library/ms646997.aspx
VSVersionInfo(
  ffi=FixedFileInfo(
    # filevers and prodvers should be always a tuple with four items: (1, 2, 3, 4)
    # Set not needed items to zero 0.
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    # Contains a bitmask that specifies the valid bits 'flags'r
    mask=0x3f,
    # Contains a bitmask that specifies the Boolean attributes of the file.
    flags=0x0,
    # The operating system for which this file was designed.
    # 0x4 - NT and there is no need to change it.
    OS=0x40004,
    # The general type of file.
    # 0x1 - the file is an application.
    fileType=0x1,
    # The function of the file.
    # 0x0 - the function is not defined for this fileType
    subtype=0x0,
    # Creation date and time stamp.
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'Your Company'),
        StringStruct(u'FileDescription', u'User Behavior Monitor'),
        StringStruct(u'FileVersion', u'1.0.0'),
        StringStruct(u'InternalName', u'UserBehaviorMonitor'),
        StringStruct(u'LegalCopyright', u'Copyright (c) 2024'),
        StringStruct(u'OriginalFilename', u'UserBehaviorMonitor.exe'),
        StringStruct(u'ProductName', u'User Behavior Monitor'),
        StringStruct(u'ProductVersion', u'1.0.0')])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
"""
    with open('version_info.txt', 'w') as f:
        f.write(version_info)

def build_exe():
    """构建可执行文件"""
    # 创建版本信息文件
    create_version_file()
    
    # PyInstaller命令
    cmd = [
        'pyinstaller',
        '--name=UserBehaviorMonitor',
        '--windowed',  # 不显示控制台窗口
        '--icon=resources/icon.ico',  # 如果有图标的话
        '--version-file=version_info.txt',
        '--add-data=src/utils/config/config.yaml;utils/config',  # 添加配置文件
        '--hidden-import=win32timezone',  # 添加必要的隐藏导入
        '--hidden-import=win32api',
        '--hidden-import=win32security',
        '--hidden-import=win32con',
        '--hidden-import=servicemanager',
        '--hidden-import=win32serviceutil',
        '--hidden-import=win32service',
        '--hidden-import=win32event',
        'src/main.py'  # 主程序入口
    ]
    
    # 执行PyInstaller命令
    subprocess.run(cmd, check=True)

def create_installer():
    """创建安装程序"""
    # 这里可以添加使用Inno Setup创建安装程序的代码
    pass

def main():
    """主函数"""
    try:
        print("开始构建...")
        
        # 清理旧的构建文件
        print("清理旧的构建文件...")
        clean_build_dirs()
        
        # 构建可执行文件
        print("构建可执行文件...")
        build_exe()
        
        # 创建安装程序
        print("创建安装程序...")
        create_installer()
        
        # 采集鼠标数据
        print("采集鼠标数据...")
        collector = WindowsMouseCollector(user_id="your_user")
        collector.start_collection()
        # ... 采集时可用快捷键或命令行停止
        collector.stop_collection()
        
        # 特征处理
        print("特征处理...")
        processor = WindowsFeatureProcessor()
        df = processor.load_data_from_db(user_id="your_user", session_id="session_xxx")
        features = processor.process_features(df)
        processor.save_features_to_db(features, user_id="your_user")
        
        print("构建完成！")
        
    except Exception as e:
        print(f"构建失败: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main() 