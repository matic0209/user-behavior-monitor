# 心跳功能说明

## 概述

用户行为监控系统现已集成心跳上报功能，系统会定期向指定服务器发送心跳信号，用于监控系统运行状态。

## 功能特性

### 心跳配置
- **心跳地址**: `http://127.0.0.1:26002/heartbeat`
- **心跳间隔**: 30秒
- **数据格式**: JSON格式，包含 `{"type": 4}`

### 心跳数据格式
```json
{
    "type": 4
}
```

### 网络请求详情
- **请求方法**: POST
- **Content-Type**: application/json
- **超时时间**: 10秒
- **重试机制**: 自动重试，失败不影响主程序运行

## 使用方法

### 1. 启动系统
系统启动时会自动开始心跳上报：
```bash
python user_behavior_monitor.py
```

### 2. 测试心跳功能
使用提供的测试脚本验证心跳功能：
```bash
# 单次测试
python test_heartbeat.py

# 连续测试（每30秒发送一次）
python test_heartbeat.py --continuous
```

### 3. 手动测试心跳
使用curl命令测试：
```bash
curl --location 'http://127.0.0.1:26002/heartbeat' \
--header 'Content-Type: application/json' \
--data '{"type": 4}'
```

## 系统集成

### 心跳线程
- 系统启动时自动创建心跳线程
- 心跳线程为守护线程，不会阻止主程序退出
- 心跳失败不会影响主程序功能

### 统计信息
系统会记录心跳统计信息：
- 发送成功次数
- 发送失败次数
- 成功率统计

### 日志记录
心跳相关的日志级别：
- **DEBUG**: 成功发送的心跳
- **WARNING**: 网络错误或非200状态码
- **ERROR**: 其他异常情况

## 配置选项

### 修改心跳地址
在 `user_behavior_monitor.py` 中修改：
```python
self.heartbeat_url = "http://your-server:port/heartbeat"
```

### 修改心跳间隔
在 `user_behavior_monitor.py` 中修改：
```python
self.heartbeat_interval = 60  # 60秒间隔
```

### 修改心跳数据格式
在 `_send_heartbeat` 方法中修改：
```python
heartbeat_data = {
    "type": 4,
    "timestamp": time.time(),
    "user_id": self.current_user_id
}
```

## 故障排除

### 常见问题

1. **心跳发送失败**
   - 检查目标服务器是否运行
   - 检查网络连接
   - 检查防火墙设置

2. **心跳间隔不准确**
   - 心跳线程每5秒检查一次
   - 实际间隔可能比设定值稍长

3. **心跳统计不准确**
   - 统计信息在程序退出时记录
   - 查看日志文件获取详细信息

### 调试方法

1. **查看日志**
   ```bash
   tail -f logs/monitor_*.log
   ```

2. **使用测试脚本**
   ```bash
   python test_heartbeat.py --continuous
   ```

3. **检查网络连接**
   ```bash
   telnet 127.0.0.1 26002
   ```

## 技术实现

### 核心组件
- `_send_heartbeat()`: 发送心跳请求
- `_heartbeat_worker()`: 心跳工作线程
- `_start_heartbeat()`: 启动心跳线程
- `_stop_heartbeat()`: 停止心跳线程

### 错误处理
- 网络超时处理
- 异常捕获和日志记录
- 失败统计和重试机制

### 线程安全
- 使用守护线程确保程序退出时自动清理
- 线程间通信通过共享变量实现
- 避免阻塞主程序功能

## 版本历史

- **v1.2.0**: 初始版本，集成基础心跳功能
- 支持自定义心跳地址和间隔
- 提供完整的统计和日志功能
- 包含测试工具和故障排除指南 