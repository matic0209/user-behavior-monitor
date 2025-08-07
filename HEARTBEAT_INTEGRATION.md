# 心跳功能集成说明

## 概述

用户行为监控系统现已成功集成心跳上报功能。系统会定期向指定服务器发送心跳信号，用于监控系统运行状态。

## 功能特性

### 心跳配置
- **心跳地址**: `http://127.0.0.1:26002/heartbeat`
- **心跳间隔**: 30秒
- **数据格式**: JSON格式，包含 `{"type": 4}`

### 网络请求详情
- **请求方法**: POST
- **Content-Type**: application/json
- **超时时间**: 10秒
- **重试机制**: 自动重试，失败不影响主程序运行

## 文件更新

### 1. 主程序文件 (`user_behavior_monitor.py`)
- ✅ 已添加心跳功能
- ✅ 集成到系统启动流程
- ✅ 包含统计和日志功能
- ✅ 线程安全的实现

### 2. 构建脚本 (`build_exe_simple_fixed.py`)
- ✅ 已添加网络模块导入
- ✅ 支持心跳功能的打包
- ✅ 包含所有必要的依赖

### 3. 测试工具
- ✅ `test_heartbeat.py` - 心跳功能测试
- ✅ `mock_heartbeat_server.py` - 模拟心跳服务器
- ✅ `demo_heartbeat.py` - 心跳功能演示

## 使用方法

### 1. 启动系统
```bash
python user_behavior_monitor.py
```
系统启动时会自动开始心跳上报。

### 2. 测试心跳功能
```bash
# 启动模拟服务器
python3 mock_heartbeat_server.py

# 测试心跳功能
python3 test_heartbeat.py

# 连续测试
python3 test_heartbeat.py --continuous

# 演示心跳功能
python3 demo_heartbeat.py
```

### 3. 手动测试心跳
```bash
curl --location 'http://127.0.0.1:26002/heartbeat' \
--header 'Content-Type: application/json' \
--data '{"type": 4}'
```

## 打包说明

### 使用简化版构建脚本
```bash
python build_exe_simple_fixed.py
```

构建脚本已更新，包含以下网络模块：
- `urllib.request`
- `urllib.parse`
- `urllib.error`
- `http.client`
- `socket`

### 构建选项
1. **简化版构建** - 推荐，快速构建
2. **详细版构建** - 包含所有导入
3. **目录模式构建** - 便于调试

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

2. **打包后心跳功能不工作**
   - 确保构建脚本包含网络模块
   - 检查防火墙设置
   - 验证网络连接

3. **心跳间隔不准确**
   - 心跳线程每5秒检查一次
   - 实际间隔可能比设定值稍长

### 调试方法

1. **查看日志**
   ```bash
   tail -f logs/monitor_*.log
   ```

2. **使用测试脚本**
   ```bash
   python3 test_heartbeat.py --continuous
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
- `_get_heartbeat_stats()`: 获取心跳统计
- `_log_heartbeat_stats()`: 记录心跳统计

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
- 更新构建脚本支持心跳功能

## 下一步计划

1. **增强心跳数据**
   - 添加系统状态信息
   - 包含用户行为统计
   - 添加异常检测结果

2. **改进错误处理**
   - 实现指数退避重试
   - 添加网络状态监控
   - 支持多服务器备份

3. **优化性能**
   - 减少心跳频率
   - 优化网络请求
   - 添加心跳缓存

## 总结

心跳功能已成功集成到用户行为监控系统中，提供了完整的监控和统计功能。系统现在可以：

- ✅ 定期发送心跳信号
- ✅ 记录心跳统计信息
- ✅ 处理网络错误和异常
- ✅ 不影响主程序功能
- ✅ 支持自定义配置
- ✅ 提供完整的测试工具

所有相关文件已更新，构建脚本已包含必要的网络模块，确保打包后的程序能够正常使用心跳功能。
