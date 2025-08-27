# 🎯 用户行为监控系统 - 综合测试执行指南

## 📋 概述

本测试套件提供完整的用户行为监控系统功能验证，包含10个核心测试用例，涵盖从数据采集到异常拦截的全流程测试。

## 🚀 快速开始

### 1. 环境准备

确保Windows环境下已安装：
- Git Bash (推荐)
- Python 3.7+
- UserBehaviorMonitor.exe (已构建)

### 2. 执行测试

```bash
# 进入测试目录
cd tests/scripts_windows

# 执行完整测试套件
bash run_comprehensive_tests.sh
```

### 3. 查看报告

测试完成后，在 `test_results_YYYYMMDD_HHMMSS/` 目录下生成：

- **📄 详细报告**: `UserBehaviorMonitor_TestReport_YYYYMMDD_HHMMSS.md`
- **🌐 交互报告**: `UserBehaviorMonitor_TestReport_YYYYMMDD_HHMMSS.html` ⭐ **推荐**
- **📊 数据报告**: `TestResults_YYYYMMDD_HHMMSS.csv`

## 📊 测试覆盖范围

| 测试用例 | 功能模块 | 关键指标 |
|----------|----------|----------|
| TC01 | 实时数据采集 | 延迟 < 50ms |
| TC02 | 特征提取 | 特征维度完整性 |
| TC03 | 深度学习分类 | 模型训练效果 |
| TC04 | 异常告警 | 告警准确性 |
| TC05 | 行为拦截 | 响应时间 |
| TC06 | 指纹管理 | 匹配准确率 |
| TC07 | 采集指标 | 覆盖率验证 |
| TC08 | 特征数量 | ≥200个特征 |
| TC09 | 算法准确率 | ≥90% 准确率 |
| TC10 | 误报率 | ≤0.1% 误报率 (千分之一) |

## 🎯 预期结果

- ✅ **通过率**: 100%
- ✅ **关键指标**: 全部达标
- ✅ **性能表现**: 优秀级别

## 📞 支持

如有问题，请检查：
1. EXE文件路径是否正确
2. 测试环境依赖是否完整
3. 系统权限是否充足

---

**最后更新**: 2025-08-26  
**测试框架版本**: v2.1
