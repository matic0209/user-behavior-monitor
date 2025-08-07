
# 模拟的predict模块
import logging

logger = logging.getLogger(__name__)

def predict_anomaly(user_id, features, model_info=None):
    """模拟的异常预测函数"""
    logger.warning("使用模拟的predict_anomaly函数")
    return {"anomaly_score": 0.0, "prediction": 0}

def predict_user_behavior(user_id, features, threshold=0.5):
    """模拟的用户行为预测函数"""
    logger.warning("使用模拟的predict_user_behavior函数")
    return {"prediction": 0, "confidence": 0.0}
