# TC06 用户行为指纹数据管理功能 - 详细测试步骤

## 📋 测试概述

**测试目标**: 验证系统具备用户输入行为指纹数据管理功能，能够创建和存储用户行为的独特模式或"指纹"，用于识别和验证用户身份，同时帮助系统识别正常与异常行为。

**基础数据**: 基于现有的 `mouse_data.db` 数据库，包含以下训练用户指纹数据：
- training_user_12: 240条记录
- training_user_15: 253条记录  
- training_user_16: 201条记录
- training_user_20: 114条记录
- training_user_21: 121条记录
- 等其他训练用户

## 🔧 测试前置条件

### 1. 环境检查
```bash
# 1.1 检查EXE文件是否存在
ls -la dist/UserBehaviorMonitor.exe

# 1.2 检查数据库文件
ls -la data/mouse_data.db

# 1.3 检查数据库内容
sqlite3 data/mouse_data.db "SELECT COUNT(*) FROM features;"
sqlite3 data/mouse_data.db "SELECT COUNT(DISTINCT user_id) FROM features;"
```

### 1.2 数据库结构验证
```sql
-- 验证表结构
.schema features
.schema mouse_events
.schema predictions

-- 验证数据完整性
SELECT user_id, COUNT(*) as record_count 
FROM features 
GROUP BY user_id 
ORDER BY record_count DESC;
```

## 📝 详细测试步骤

### 步骤1: 系统启动和初始化

**操作**: 启动用户行为监控系统
```bash
./dist/UserBehaviorMonitor.exe
```

**验证点**:
- [ ] 进程启动成功，PID可获取
- [ ] 系统显示版本信息和用户信息
- [ ] 日志文件创建成功
- [ ] 数据库连接建立成功

**期望日志关键字**:
```
Windows用户行为异常检测系统启动
版本: v1.2.0 Windows版
系统初始化完成
数据库连接成功
```

### 步骤2: 验证指纹数据存储功能

**操作**: 检查数据库中的指纹特征数据
```sql
-- 2.1 验证特征向量存储
SELECT user_id, COUNT(*) as feature_count, 
       MIN(created_at) as first_record,
       MAX(created_at) as last_record
FROM features 
GROUP BY user_id;

-- 2.2 验证特征向量内容
SELECT user_id, feature_vector 
FROM features 
WHERE user_id = 'training_user_15' 
LIMIT 1;
```

**验证点**:
- [ ] features表包含多个用户的指纹数据
- [ ] 每个用户至少有100条特征记录
- [ ] feature_vector字段包含JSON格式的特征数据
- [ ] 特征数据包含多维度信息（速度、轨迹、时间等）

**期望结果**:
- 用户数量 ≥ 5个
- 每用户记录数 ≥ 100条
- 特征向量包含统计特征（mean, std, min, max）

### 步骤3: 验证指纹特征提取功能

**操作**: 触发特征处理流程
```bash
# 发送重新训练信号
echo "rrrr" | ./dist/UserBehaviorMonitor.exe
```

**验证点**:
- [ ] 系统开始数据采集流程
- [ ] 特征处理器正常工作
- [ ] 日志显示特征提取过程

**期望日志关键字**:
```
开始使用feature_engineering处理鼠标特征
执行数据预处理
提取速度特征
提取轨迹特征  
提取时间特征
提取统计特征
特征处理完成
UBM_MARK: FEATURE_DONE
```

**特征类型验证**:
- [ ] 速度特征: distance_from_previous_mean, velocity_mean
- [ ] 轨迹特征: angle_movement_mean, total_distance
- [ ] 时间特征: elapsed_time_from_previous_mean
- [ ] 统计特征: 各特征的mean, std, min, max

### 步骤4: 验证用户身份识别功能

**操作**: 观察用户ID生成和识别过程

**验证点**:
- [ ] 系统自动获取Windows用户名
- [ ] 生成唯一的用户ID（格式: username_timestamp）
- [ ] 用户ID在会话中保持一致
- [ ] 支持重新训练用户ID（格式: username_retrain_timestamp）

**期望日志关键字**:
```
获取当前用户ID
Windows用户名: [用户名]
生成用户ID: [用户名]_[时间戳]
当前用户: [用户ID]
```

### 步骤5: 验证指纹模式匹配功能

**操作**: 观察系统进行模式匹配的过程

**验证点**:
- [ ] 系统加载已存储的用户指纹模型
- [ ] 新采集数据与指纹模式进行匹配
- [ ] 计算相似度或匹配分数
- [ ] 支持多用户指纹比较

**期望日志关键字**:
```
加载用户模型
成功加载用户 [用户ID] 的模型
特征对齐
模型预测
相似度计算
```

**数据库验证**:
```sql
-- 验证预测结果存储
SELECT user_id, prediction, anomaly_score, probability
FROM predictions 
ORDER BY created_at DESC 
LIMIT 5;
```

### 步骤6: 验证异常行为检测功能

**操作**: 观察基于指纹的异常检测过程

**验证点**:
- [ ] 系统基于用户指纹进行异常检测
- [ ] 输出异常分数（0-1之间）
- [ ] 输出预测结果（正常/异常）
- [ ] 异常阈值判断正确

**期望日志关键字**:
```
开始异常检测
预测用户行为
异常分数: [分数]
预测结果: [正常/异常]
is_normal: [true/false]
anomaly_score: [分数]
```

**阈值验证**:
- [ ] 异常分数 ≥ 0.8 时触发告警
- [ ] 正常行为分数 < 0.8
- [ ] 预测概率合理（0-1之间）

### 步骤7: 验证指纹数据管理功能

**操作**: 验证多用户指纹数据的管理能力

**验证点**:
- [ ] 支持多用户指纹数据存储
- [ ] 支持用户指纹数据查询
- [ ] 支持用户指纹数据更新
- [ ] 数据隔离正确（不同用户数据独立）

**数据库操作验证**:
```sql
-- 7.1 查询用户列表
SELECT DISTINCT user_id FROM features;

-- 7.2 查询特定用户指纹
SELECT COUNT(*) as record_count,
       MIN(timestamp) as first_timestamp,
       MAX(timestamp) as last_timestamp
FROM features 
WHERE user_id = 'training_user_15';

-- 7.3 验证数据完整性
SELECT user_id, 
       COUNT(*) as total_records,
       COUNT(DISTINCT session_id) as sessions
FROM features 
GROUP BY user_id;
```

### 步骤8: 系统优雅退出

**操作**: 发送退出信号
```bash
# 发送4个q字符退出
echo "qqqq"
```

**验证点**:
- [ ] 系统响应退出信号
- [ ] 数据保存完成
- [ ] 日志文件完整
- [ ] 进程正常终止
- [ ] 无内存泄漏或异常

**期望日志关键字**:
```
接收到退出信号
保存数据中...
数据保存完成
系统正常退出
```

## 🎯 测试通过标准

### 核心功能验证
1. **指纹数据存储**: ✅ 数据库包含≥5个用户的指纹数据，每用户≥100条记录
2. **特征提取**: ✅ 成功提取速度、轨迹、时间、统计等多维特征
3. **用户识别**: ✅ 正确识别和生成用户身份标识
4. **模式匹配**: ✅ 能够进行指纹模式匹配和相似度计算
5. **异常检测**: ✅ 基于指纹进行异常行为检测，输出合理分数
6. **数据管理**: ✅ 支持多用户指纹数据的存储、查询、更新
7. **系统稳定性**: ✅ 系统运行稳定，正常启动和退出

### 性能标准
- 特征提取时间 < 30秒
- 异常检测响应时间 < 5秒  
- 内存使用 < 500MB
- CPU使用率 < 50%

### 准确性标准
- 异常检测准确率 ≥ 85%
- 用户识别准确率 ≥ 90%
- 指纹匹配精度 ≥ 80%

## 🚨 异常情况处理

### 常见问题及解决方案

1. **数据库连接失败**
   - 检查 mouse_data.db 文件权限
   - 验证数据库文件完整性
   - 重新导入训练数据

2. **特征提取失败**
   - 检查输入数据格式
   - 验证特征工程模块可用性
   - 查看详细错误日志

3. **用户识别错误**
   - 验证Windows用户名获取
   - 检查用户管理模块
   - 确认权限设置

4. **异常检测不准确**
   - 验证模型文件存在性
   - 检查特征对齐
   - 调整异常阈值

## 📊 测试报告模板

```markdown
## TC06 测试执行报告

**执行时间**: [日期时间]
**测试人员**: [姓名]
**测试环境**: Windows 10/11

### 测试结果汇总
- 总测试步骤: 8
- 通过步骤: [数量]
- 失败步骤: [数量]  
- 总体结论: [通过/失败]

### 详细结果
| 步骤 | 测试内容 | 结果 | 备注 |
|------|----------|------|------|
| 1 | 系统启动 | ✅/❌ | |
| 2 | 指纹数据存储 | ✅/❌ | |
| 3 | 特征提取 | ✅/❌ | |
| 4 | 用户识别 | ✅/❌ | |
| 5 | 模式匹配 | ✅/❌ | |
| 6 | 异常检测 | ✅/❌ | |
| 7 | 数据管理 | ✅/❌ | |
| 8 | 系统退出 | ✅/❌ | |

### 性能指标
- 启动时间: [秒]
- 特征提取时间: [秒]
- 异常检测时间: [秒]
- 内存峰值: [MB]
- CPU峰值: [%]

### 问题记录
[记录测试中发现的问题]

### 改进建议
[提出改进建议]
```

这个详细的测试步骤文档基于现有的 `mouse_data.db` 数据库和系统实现，涵盖了用户行为指纹数据管理的所有核心功能验证。
