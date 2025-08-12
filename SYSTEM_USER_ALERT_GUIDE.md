
# System用户告警指南

## 概述
当用户行为监控系统以system用户(UID 0)运行时，由于没有GUI环境，无法显示弹窗告警。
本指南介绍如何在system用户环境下实现有效的告警机制。

## 告警方式

### 1. 控制台告警
- **适用场景**: 系统有控制台输出
- **特点**: 实时显示，醒目格式
- **查看方式**: 直接查看控制台输出

### 2. 文件告警
- **位置**: `logs/alerts/`
- **文件类型**: 
  - `alert_YYYYMMDD_HHMMSS.txt`: 详细告警文件
  - `realtime_alerts.txt`: 实时告警记录
- **查看方式**: 定期检查告警目录

### 3. 日志告警
- **位置**: `logs/monitor_*.log`
- **特点**: 详细的系统运行日志
- **查看方式**: 使用日志查看工具

### 4. 系统日志
- **Linux**: syslog (`/var/log/syslog`)
- **Windows**: 事件查看器
- **查看方式**: 系统日志工具

### 5. 声音告警
- **Linux**: 使用paplay播放系统音效
- **Windows**: 使用系统蜂鸣声
- **特点**: 需要音频设备

## 监控脚本

### 告警监控脚本
```bash
# 运行告警监控
bash alert_monitor.sh

# 实时监控告警文件
tail -f logs/alerts/realtime_alerts.txt

# 查看最新告警
ls -la logs/alerts/ | tail -10
```

### 系统日志监控
```bash
# Linux syslog监控
tail -f /var/log/syslog | grep UserBehaviorMonitor

# 查看最近的告警
journalctl -u UserBehaviorMonitor --since "1 hour ago"
```

## 配置建议

### 1. 启用所有告警方式
```yaml
alert:
  enable_console_alert: true
  enable_file_alert: true
  enable_log_alert: true
  enable_system_notification: true
  enable_sound_alert: true
```

### 2. 设置告警目录权限
```bash
# 确保告警目录可写
chmod 755 logs/alerts/
chown system:system logs/alerts/
```

### 3. 配置日志轮转
```bash
# 防止日志文件过大
logrotate -f /etc/logrotate.d/user_behavior_monitor
```

## 故障排除

### 1. 告警文件不生成
- 检查目录权限
- 检查磁盘空间
- 查看错误日志

### 2. 系统日志不记录
- 检查syslog服务状态
- 检查用户权限
- 查看系统日志配置

### 3. 声音告警不工作
- 检查音频设备
- 检查音频服务
- 检查权限设置

## 最佳实践

1. **定期检查**: 设置定时任务定期检查告警文件
2. **日志轮转**: 配置日志轮转防止文件过大
3. **权限管理**: 确保告警目录有适当权限
4. **监控集成**: 将告警集成到系统监控工具
5. **备份策略**: 定期备份告警和日志文件

## 紧急情况处理

### 发现异常告警时：
1. 立即检查告警文件内容
2. 查看系统日志获取详细信息
3. 检查用户活动日志
4. 必要时锁定系统或强制登出
5. 联系系统管理员

### 告警系统故障时：
1. 检查服务状态
2. 查看错误日志
3. 重启告警服务
4. 检查配置文件
5. 验证权限设置
