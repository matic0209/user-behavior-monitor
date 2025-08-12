# 负样本处理逻辑修复

## 🔍 问题描述

在训练算法中，负样本的处理逻辑存在问题。正确的做法应该是：
- **正样本**：当前用户的行为数据（正常行为）
- **负样本**：其他用户的行为数据（异常行为）

但之前的代码错误地优先使用了训练数据作为负样本，而不是其他用户数据。

## ❌ 之前的问题

### 错误的处理流程
```python
# 1. 优先加载训练数据作为负样本
negative_samples = self.load_training_data_as_negative_samples(user_id, negative_sample_limit)

# 2. 如果训练数据不够，补充其他用户数据
if len(negative_samples) < negative_sample_limit // 2:
    additional_samples = self.load_other_users_features_from_db(user_id, negative_sample_limit - len(negative_samples))
```

**问题**：训练数据（`training_user%` 和 `test_user%`）不应该作为主要的负样本来源，因为：
1. 训练数据可能包含当前用户的数据
2. 训练数据的特征分布可能与真实的其他用户行为不同
3. 这会导致模型学习错误的异常模式

## ✅ 修复后的正确流程

### 正确的处理流程
```python
# 1. 优先加载其他用户数据作为负样本（正确的做法）
negative_samples = self.load_other_users_features_from_db(user_id, negative_sample_limit)

# 2. 如果其他用户数据不够，补充训练数据作为备用负样本
if len(negative_samples) < negative_sample_limit // 2:
    additional_samples = self.load_training_data_as_negative_samples(user_id, negative_sample_limit - len(negative_samples))
```

**优势**：
1. **更真实的异常检测**：使用真实的其他用户数据作为负样本
2. **更好的泛化能力**：模型学习到真实的用户间差异
3. **更准确的异常分数**：基于真实用户行为差异计算异常分数

## 📊 数据来源对比

### 负样本数据来源优先级

| 优先级 | 数据来源 | 说明 | 使用场景 |
|--------|----------|------|----------|
| 1 | 其他用户数据 | 真实的其他用户行为 | 主要负样本来源 |
| 2 | 训练数据 | 预处理的训练数据 | 备用负样本来源 |
| 3 | 合成数据 | 人工生成的数据 | 最后的选择 |

### 数据查询逻辑

#### 其他用户数据查询
```sql
SELECT feature_vector FROM features 
WHERE user_id != ? AND user_id NOT LIKE 'training_user%' AND user_id NOT LIKE 'test_user%'
ORDER BY timestamp DESC
```

#### 训练数据查询
```sql
SELECT feature_vector FROM features 
WHERE user_id LIKE 'training_user%' OR user_id LIKE 'test_user%'
ORDER BY timestamp DESC
```

## 🔧 修复的文件

1. **`src/core/model_trainer/simple_model_trainer.py`**
   - 修改 `prepare_training_data()` 方法
   - 调整负样本加载优先级

2. **`user_behavior_monitor_uos20_offline/src/core/model_trainer/simple_model_trainer.py`**
   - 同步修复离线版本

## 📈 预期效果

### 模型性能提升
- **更准确的异常检测**：基于真实用户差异
- **更低的误报率**：减少对正常行为的误判
- **更高的召回率**：更好地识别真正的异常行为

### 训练数据质量
- **更平衡的数据集**：正负样本比例更合理
- **更真实的特征分布**：反映真实的使用场景
- **更好的泛化能力**：适应不同的用户环境

## 🧪 验证方法

### 1. 检查训练日志
```bash
# 查看训练数据统计
grep "训练数据统计" logs/monitor_*.log
```

### 2. 验证负样本来源
```bash
# 检查数据库中的用户分布
sqlite3 data/mouse_data.db "SELECT user_id, COUNT(*) FROM features GROUP BY user_id;"
```

### 3. 模型性能测试
```bash
# 运行预测测试
python src/predict.py
```

## 📝 注意事项

1. **数据隐私**：确保其他用户数据的使用符合隐私政策
2. **数据质量**：定期清理和更新负样本数据
3. **模型更新**：修复后需要重新训练现有模型
4. **监控效果**：观察修复后的异常检测效果

## 🔄 后续优化

1. **动态负样本选择**：根据用户相似度选择负样本
2. **负样本权重调整**：为不同类型的负样本设置不同权重
3. **在线学习**：实时更新负样本库
4. **异常样本检测**：识别和移除异常的负样本
