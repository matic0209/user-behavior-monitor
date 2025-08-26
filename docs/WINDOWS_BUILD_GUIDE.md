# Windows构建使用指南

## 问题解决

如果您在Windows环境下遇到以下错误：
```
ModuleNotFoundError: No module named 'psutil'
```

请按照以下步骤解决：

## 步骤1: 安装依赖

### 方法1: 使用自动安装脚本（推荐）
```cmd
python install_dependencies_windows.py
```

这个脚本会自动安装所有必要的依赖包。

### 方法2: 手动安装
```cmd
pip install psutil pynput keyboard pyyaml numpy pandas scikit-learn xgboost pywin32 pyinstaller
```

## 步骤2: 验证安装

运行依赖检查脚本：
```cmd
python build_windows.py
```

如果看到以下输出，说明依赖安装成功：
```
[SUCCESS] psutil 可用
[SUCCESS] pynput 可用
[SUCCESS] keyboard 可用
[SUCCESS] yaml 可用
[SUCCESS] numpy 可用
[SUCCESS] pandas 可用
[SUCCESS] sklearn 可用
[SUCCESS] xgboost 可用
[SUCCESS] win32api 可用
[SUCCESS] win32con 可用
[SUCCESS] win32gui 可用
[SUCCESS] win32service 可用
[SUCCESS] win32serviceutil 可用
[SUCCESS] 所有依赖检查通过
```

## 步骤3: 构建可执行文件

### 方法1: 使用完整构建脚本（推荐）
```cmd
python build_windows_full.py
```

### 方法2: 使用通用构建脚本
```cmd
python build_safe.py
```

### 方法3: 使用跨平台构建脚本
```cmd
python build_cross_platform.py
```

### 方法2: 使用通用构建脚本
```cmd
python build_safe.py
```

### 方法3: 使用跨平台构建脚本
```cmd
python build_cross_platform.py
```

## 常见问题解决

### 问题1: 权限错误
**症状**: `PermissionError: [WinError 5]`
**解决**: 
1. 以管理员身份运行命令提示符
2. 运行 `python fix_permission.py`

### 问题2: 编码乱码
**症状**: 中文显示为乱码
**解决**: 
1. 设置环境变量：`set PYTHONIOENCODING=utf-8`
2. 设置控制台编码：`chcp 65001`

### 问题3: 模块缺失
**症状**: `ModuleNotFoundError: No module named 'xxx'`
**解决**: 
1. 运行 `python install_dependencies_windows.py`
2. 手动安装缺失的模块：`pip install 模块名`

### 问题4: 构建失败
**症状**: 构建过程中出错
**解决**: 
1. 清理构建目录：删除 `build`、`dist`、`__pycache__` 目录
2. 结束冲突进程：`taskkill /f /im python.exe`
3. 重新运行构建脚本

## 构建脚本对比

| 脚本 | 特点 | 适用场景 |
|------|------|----------|
| `build_windows_full.py` | Windows专用，完整依赖检查和构建 | Windows环境，推荐使用 |
| `build_windows.py` | Windows专用，仅依赖检查 | 验证环境 |
| `build_safe.py` | 通用脚本，基础功能 | 简单构建 |
| `build_cross_platform.py` | 跨平台，自动适配 | 多平台环境 |

## 成功标志

当看到以下输出时，表示构建成功：

```
[SUCCESS] 构建完成!
[INFO] 可执行文件位置: dist/UserBehaviorMonitor.exe
```

## 验证构建结果

1. **检查文件是否存在**
   ```cmd
   dir dist\UserBehaviorMonitor.exe
   ```

2. **检查文件大小**
   - 正常大小应该在50-200MB之间
   - 如果太小可能缺少依赖

3. **测试运行**
   ```cmd
   dist\UserBehaviorMonitor.exe
   ```

## 故障排除

如果构建仍然失败，请检查：

1. **Python环境**
   ```cmd
   python --version
   pip list
   ```

2. **网络连接**
   - 确保能访问PyPI
   - 检查防火墙设置

3. **磁盘空间**
   - 确保有足够的磁盘空间（至少2GB）

4. **系统权限**
   - 确保有管理员权限
   - 检查防病毒软件是否阻止

## 联系支持

如果问题仍然存在，请提供：

1. 完整的错误信息
2. Windows版本信息
3. Python版本信息
4. 构建脚本的输出日志

---

**注意**: 这些脚本专门针对Windows环境优化，包含了完整的依赖检查和错误处理。
