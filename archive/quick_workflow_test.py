#!/usr/bin/env python3
"""
快速工作流程测试
简化版本，用于快速验证各个组件是否正常工作
"""

import os
import sys
import time
import random
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.utils.logger.logger import Logger
from src.utils.config.config_loader import ConfigLoader

class QuickWorkflowTest:
    def __init__(self):
        self.logger = Logger()
        self.config = ConfigLoader()
        self.db_path = Path(self.config.get_paths()['data']) / 'mouse_data.db'
        
        # 快速测试配置
        self.test_user = 'quick_test_user'
        self.events_count = 200  # 减少事件数量以加快测试
        
        self.logger.info("快速工作流程测试初始化完成")

    def generate_quick_test_data(self):
        """生成快速测试数据"""
        self.logger.info("生成快速测试数据...")
        
        # 确保数据库存在
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 创建数据库连接
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建鼠标事件表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mouse_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                timestamp REAL NOT NULL,
                x INTEGER NOT NULL,
                y INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                button TEXT,
                wheel_delta INTEGER DEFAULT 0
            )
        ''')
        
        # 清空现有测试数据
        cursor.execute("DELETE FROM mouse_events WHERE user_id = ?", (self.test_user,))
        
        # 生成简单的鼠标轨迹
        session_id = f"{self.test_user}_session_1"
        start_time = time.time()
        x, y = 100, 100
        
        for i in range(self.events_count):
            timestamp = start_time + i * 0.1
            
            # 简单的线性移动
            x += random.randint(-10, 10)
            y += random.randint(-10, 10)
            x = max(0, min(1920, x))
            y = max(0, min(1080, y))
            
            event_type = 'move' if random.random() < 0.8 else 'click'
            
            cursor.execute('''
                INSERT INTO mouse_events (user_id, session_id, timestamp, x, y, event_type, button, wheel_delta)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (self.test_user, session_id, timestamp, x, y, event_type, 'left', 0))
        
        conn.commit()
        conn.close()
        
        self.logger.info(f"生成了 {self.events_count} 条测试数据")

    def test_feature_processing(self):
        """测试特征处理"""
        self.logger.info("测试特征处理...")
        
        try:
            from src.core.feature_engineer.simple_feature_processor import SimpleFeatureProcessor
            
            processor = SimpleFeatureProcessor()
            success = processor.process_session_features(self.test_user, f"{self.test_user}_session_1")
            
            if success:
                self.logger.info("✅ 特征处理测试成功")
                return True
            else:
                self.logger.error("❌ 特征处理测试失败")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ 特征处理测试异常: {str(e)}")
            return False

    def test_model_training(self):
        """测试模型训练"""
        self.logger.info("测试模型训练...")
        
        try:
            from src.core.model_trainer.simple_model_trainer import SimpleModelTrainer
            
            trainer = SimpleModelTrainer()
            success = trainer.train_user_model(self.test_user)
            
            if success:
                self.logger.info("✅ 模型训练测试成功")
                return True
            else:
                self.logger.error("❌ 模型训练测试失败")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ 模型训练测试异常: {str(e)}")
            return False

    def test_prediction(self):
        """测试预测功能"""
        self.logger.info("测试预测功能...")
        
        try:
            from src.core.predictor.simple_predictor import SimplePredictor
            
            predictor = SimplePredictor()
            
            # 直接测试预测功能，不传递测试数据（让它从数据库加载）
            predictions = predictor.predict_user_behavior(self.test_user)
            
            if predictions is not None and len(predictions) > 0:
                self.logger.info("✅ 预测功能测试成功")
                # 显示第一个预测结果
                first_pred = predictions[0]
                self.logger.info(f"  异常分数: {first_pred.get('anomaly_score', 'N/A')}")
                self.logger.info(f"  预测结果: {first_pred.get('is_normal', 'N/A')}")
                return True
            else:
                self.logger.error("❌ 预测功能测试失败")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ 预测功能测试异常: {str(e)}")
            return False

    def test_database_operations(self):
        """测试数据库操作"""
        self.logger.info("测试数据库操作...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 检查鼠标事件表
            cursor.execute("SELECT COUNT(*) FROM mouse_events WHERE user_id = ?", (self.test_user,))
            mouse_count = cursor.fetchone()[0]
            
            # 检查特征表
            cursor.execute("SELECT COUNT(*) FROM features WHERE user_id = ?", (self.test_user,))
            feature_count = cursor.fetchone()[0]
            
            conn.close()
            
            self.logger.info(f"✅ 数据库操作测试成功")
            self.logger.info(f"  鼠标事件数: {mouse_count}")
            self.logger.info(f"  特征数据数: {feature_count}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 数据库操作测试异常: {str(e)}")
            return False

    def run_quick_test(self):
        """运行快速测试"""
        self.logger.info("=" * 50)
        self.logger.info("开始快速工作流程测试")
        self.logger.info("=" * 50)
        
        test_results = {}
        
        try:
            # 步骤1: 生成测试数据
            self.logger.info("\n📊 步骤1: 生成测试数据")
            self.generate_quick_test_data()
            test_results['data_generation'] = True
            
            # 步骤2: 测试数据库操作
            self.logger.info("\n🗄️ 步骤2: 测试数据库操作")
            test_results['database'] = self.test_database_operations()
            
            # 步骤3: 测试特征处理
            self.logger.info("\n🔧 步骤3: 测试特征处理")
            test_results['feature_processing'] = self.test_feature_processing()
            
            # 步骤4: 测试模型训练
            self.logger.info("\n🤖 步骤4: 测试模型训练")
            test_results['model_training'] = self.test_model_training()
            
            # 步骤5: 测试预测功能
            self.logger.info("\n🎯 步骤5: 测试预测功能")
            test_results['prediction'] = self.test_prediction()
            
            # 生成测试结果报告
            self._generate_quick_test_report(test_results)
            
        except Exception as e:
            self.logger.error(f"快速测试失败: {str(e)}")
            test_results['overall'] = False
            raise

    def _generate_quick_test_report(self, test_results):
        """生成快速测试报告"""
        self.logger.info("\n" + "=" * 50)
        self.logger.info("快速测试结果报告")
        self.logger.info("=" * 50)
        
        # 计算成功率
        success_count = sum(1 for result in test_results.values() if result)
        total_count = len(test_results)
        success_rate = (success_count / total_count) * 100
        
        # 显示详细结果
        for test_name, result in test_results.items():
            status = "✅ 通过" if result else "❌ 失败"
            self.logger.info(f"  {test_name}: {status}")
        
        self.logger.info(f"\n总体成功率: {success_rate:.1f}% ({success_count}/{total_count})")
        
        if success_rate == 100:
            self.logger.info("🎉 所有测试都通过了！工作流程运行正常。")
        elif success_rate >= 80:
            self.logger.info("⚠️ 大部分测试通过，但有一些问题需要检查。")
        else:
            self.logger.error("❌ 多个测试失败，需要检查系统配置。")
        
        # 保存测试结果
        report = {
            'test_time': datetime.now().isoformat(),
            'test_user': self.test_user,
            'events_count': self.events_count,
            'results': test_results,
            'success_rate': success_rate
        }
        
        report_path = Path('logs/quick_test_report.json')
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            import json
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"测试报告已保存到: {report_path}")

def main():
    """主函数"""
    print("🔧 快速工作流程测试工具")
    print("=" * 40)
    
    # 创建测试实例
    test = QuickWorkflowTest()
    
    # 运行快速测试
    test.run_quick_test()

if __name__ == "__main__":
    main()
