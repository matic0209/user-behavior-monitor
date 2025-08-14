# 日志管理使用指南

## 概述

为了控制日志文件大小，我们实现了以下功能：

### 1. 自动日志轮转
- **主日志文件**: 最大10MB，保留5个备份
- **错误日志文件**: 最大5MB，保留3个备份  
- **调试日志文件**: 最大5MB，保留3个备份

### 2. 自动清理功能
- 删除7天前的日志文件
- 最多保留50个日志文件
- 按修改时间自动清理最旧的文件

### 3. 日志管理工具
提供 `log_manager.py` 工具来管理日志文件

## 使用方法

### 查看日志信息
```bash
python log_manager.py info
```

**输出示例:**
```
=== 日志文件信息 ===
日志目录: /path/to/logs
总文件数: 15
总大小: 0.1 MB

文件详情:
  monitor_20250807_095850.log: 0.0 MB (2025-08-07 09:59:09)
  debug_20250807_095850.log: 0.0 MB (2025-08-07 09:59:09)
  ...
```

### 清理旧日志文件
```bash
# 清理7天前的日志，最多保留50个文件
python log_manager.py cleanup

# 自定义清理参数
python log_manager.py cleanup 14 30  # 清理14天前的日志，最多保留30个文件
```

### 压缩日志文件
```bash
python log_manager.py compress
```

**功能说明:**
- 自动压缩大于1MB的日志文件
- 使用gzip压缩，节省磁盘空间
- 压缩后删除原文件

### 监控日志大小
```bash
# 监控日志大小，默认最大100MB
python log_manager.py monitor

# 自定义最大大小
python log_manager.py monitor 50  # 最大50MB
```

### 设置日志级别
```bash
python log_manager.py set-level INFO
```

**可用的日志级别:**
- `DEBUG`: 最详细的日志信息
- `INFO`: 一般信息
- `WARNING`: 警告信息
- `ERROR`: 错误信息

## 日志文件说明

### 文件类型
1. **monitor_*.log**: 主日志文件，记录所有级别的日志
2. **error_*.log**: 错误日志文件，只记录ERROR级别
3. **debug_*.log**: 调试日志文件，记录DEBUG级别

### 文件命名规则
- 格式: `{类型}_{时间戳}.log`
- 时间戳格式: `YYYYMMDD_HHMMSS`
- 示例: `monitor_20250807_095850.log`

### 轮转文件命名
- 当文件达到最大大小时，会自动创建备份
- 备份文件命名: `{原文件名}.1`, `{原文件名}.2`, ...
- 示例: `monitor_20250807_095850.log.1`

## 配置说明

### 日志大小限制
```python
# 主日志文件
maxBytes=10*1024*1024,  # 10MB
backupCount=5,           # 保留5个备份

# 错误日志文件
maxBytes=5*1024*1024,   # 5MB
backupCount=3,           # 保留3个备份

# 调试日志文件
maxBytes=5*1024*1024,   # 5MB
backupCount=3,           # 保留3个备份
```

### 自动清理配置
```python
# 时间限制
days = 7  # 删除7天前的文件

# 文件数量限制
max_files = 50  # 最多保留50个文件
```

## 最佳实践

### 1. 定期监控
```bash
# 每天检查一次日志大小
python log_manager.py monitor 100
```

### 2. 定期清理
```bash
# 每周清理一次旧日志
python log_manager.py cleanup 7 50
```

### 3. 压缩大文件
```bash
# 当日志文件过多时，压缩大文件
python log_manager.py compress
```

### 4. 设置合适的日志级别
- **开发环境**: 使用 `DEBUG` 级别
- **生产环境**: 使用 `INFO` 级别
- **问题排查**: 临时使用 `DEBUG` 级别

## 故障排除

### 问题1: 日志文件过大
**解决**: 运行清理命令
```bash
python log_manager.py cleanup
python log_manager.py compress
```

### 问题2: 磁盘空间不足
**解决**: 检查并清理日志
```bash
python log_manager.py info
python log_manager.py cleanup 1 10  # 只保留1天内的日志，最多10个文件
```

### 问题3: 日志文件过多
**解决**: 减少保留的文件数量
```bash
python log_manager.py cleanup 7 20  # 只保留20个文件
```

### 问题4: 日志级别不合适
**解决**: 调整日志级别
```bash
python log_manager.py set-level WARNING  # 只记录警告和错误
```

## 监控脚本示例

### 自动监控脚本
```bash
#!/bin/bash
# 每天检查日志大小
python log_manager.py monitor 100

# 如果超过限制，自动清理
if [ $? -ne 0 ]; then
    echo "日志大小超过限制，开始清理..."
    python log_manager.py cleanup
    python log_manager.py compress
fi
```

### 定时任务设置
```bash
# 添加到crontab
# 每天凌晨2点检查日志
0 2 * * * cd /path/to/project && python log_manager.py cleanup

# 每周日凌晨3点压缩日志
0 3 * * 0 cd /path/to/project && python log_manager.py compress
```

---

**注意**: 日志管理功能会自动运行，无需手动干预。建议定期检查日志大小，确保磁盘空间充足。
