#!/usr/bin/env python3
"""
完整工作流程测试
从数据生成到特征处理、模型训练、在线预测的端到端测试
"""

import os
import sys
import time
import random
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import pickle

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.feature_engineer.simple_feature_processor import SimpleFeatureProcessor
from src.core.model_trainer.simple_model_trainer import SimpleModelTrainer
from src.core.predictor.simple_predictor import SimplePredictor
from src.utils.logger.logger import Logger
from src.utils.config.config_loader import ConfigLoader

class CompleteWorkflowTest:
    def __init__(self):
        self.logger = Logger()
        self.config = ConfigLoader()
        self.db_path = Path(self.config.get_paths()['data']) / 'mouse_data.db'
        
        # 测试用户配置
        self.test_users = ['test_user_1', 'test_user_2', 'test_user_3']
        self.sessions_per_user = 3
        self.events_per_session = 500
        
        self.logger.info("完整工作流程测试初始化完成")

    def generate_test_mouse_data(self):
        """生成测试鼠标数据"""
        self.logger.info("开始生成测试鼠标数据...")
        
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
        cursor.execute("DELETE FROM mouse_events WHERE user_id LIKE 'test_user%'")
        
        # 为每个用户生成数据
        for user_id in self.test_users:
            self.logger.info(f"为用户 {user_id} 生成数据...")
            
            for session_idx in range(self.sessions_per_user):
                session_id = f"{user_id}_session_{session_idx + 1}"
                
                # 生成会话数据
                self._generate_session_data(cursor, user_id, session_id)
        
        conn.commit()
        conn.close()
        
        # 验证数据生成
        self._verify_generated_data()
        
        self.logger.info("测试鼠标数据生成完成")

    def _generate_session_data(self, cursor, user_id, session_id):
        """为单个会话生成鼠标数据"""
        start_time = time.time()
        x, y = 100, 100  # 起始位置
        
        # 为每个用户设置不同的鼠标行为特征
        user_behavior = self._get_user_behavior_pattern(user_id)
        
        for event_idx in range(self.events_per_session):
            timestamp = start_time + event_idx * 0.1  # 100ms间隔
            
            # 根据用户行为模式生成坐标
            x, y = self._generate_next_position(x, y, user_behavior)
            
            # 生成事件类型
            event_type = self._generate_event_type(event_idx, user_behavior)
            
            # 插入数据
            cursor.execute('''
                INSERT INTO mouse_events (user_id, session_id, timestamp, x, y, event_type, button, wheel_delta)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, session_id, timestamp, x, y, event_type, 'left', 0))

    def _get_user_behavior_pattern(self, user_id):
        """获取用户行为模式"""
        patterns = {
            'test_user_1': {
                'speed': 'slow',      # 慢速移动
                'precision': 'high',  # 高精度
                'pattern': 'linear'   # 线性移动
            },
            'test_user_2': {
                'speed': 'fast',      # 快速移动
                'precision': 'medium', # 中等精度
                'pattern': 'random'   # 随机移动
            },
            'test_user_3': {
                'speed': 'medium',    # 中速移动
                'precision': 'low',   # 低精度
                'pattern': 'circular' # 圆形移动
            }
        }
        return patterns.get(user_id, patterns['test_user_1'])

    def _generate_next_position(self, x, y, behavior):
        """生成下一个鼠标位置"""
        if behavior['pattern'] == 'linear':
            # 线性移动
            x += random.randint(-20, 20)
            y += random.randint(-20, 20)
        elif behavior['pattern'] == 'random':
            # 随机移动
            x += random.randint(-50, 50)
            y += random.randint(-50, 50)
        elif behavior['pattern'] == 'circular':
            # 圆形移动
            angle = random.uniform(0, 2 * np.pi)
            radius = random.randint(10, 30)
            x += int(radius * np.cos(angle))
            y += int(radius * np.sin(angle))
        
        # 限制在屏幕范围内
        x = max(0, min(1920, x))
        y = max(0, min(1080, y))
        
        return x, y

    def _generate_event_type(self, event_idx, behavior):
        """生成事件类型"""
        if behavior['speed'] == 'slow':
            # 慢速用户：更多移动事件
            return 'move' if random.random() < 0.8 else 'click'
        elif behavior['speed'] == 'fast':
            # 快速用户：更多点击事件
            return 'click' if random.random() < 0.6 else 'move'
        else:
            # 中速用户：平衡的事件分布
            return 'move' if random.random() < 0.7 else 'click'

    def _verify_generated_data(self):
        """验证生成的数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for user_id in self.test_users:
            cursor.execute("SELECT COUNT(*) FROM mouse_events WHERE user_id = ?", (user_id,))
            count = cursor.fetchone()[0]
            self.logger.info(f"用户 {user_id} 生成了 {count} 条鼠标事件")
        
        conn.close()

    def process_features(self):
        """处理特征"""
        self.logger.info("开始特征处理...")
        
        processor = SimpleFeatureProcessor()
        
        # 为每个用户处理特征
        for user_id in self.test_users:
            self.logger.info(f"处理用户 {user_id} 的特征...")
            
            # 获取用户的所有会话
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT session_id FROM mouse_events WHERE user_id = ?", (user_id,))
            sessions = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            # 处理每个会话的特征
            for session_id in sessions:
                success = processor.process_session_features(user_id, session_id)
                if success:
                    self.logger.info(f"会话 {session_id} 特征处理成功")
                else:
                    self.logger.warning(f"会话 {session_id} 特征处理失败")
        
        self.logger.info("特征处理完成")

    def train_models(self):
        """训练模型"""
        self.logger.info("开始模型训练...")
        
        trainer = SimpleModelTrainer()
        
        # 为每个用户训练模型
        for user_id in self.test_users:
            self.logger.info(f"训练用户 {user_id} 的模型...")
            
            success = trainer.train_user_model(user_id)
            if success:
                self.logger.info(f"用户 {user_id} 模型训练成功")
            else:
                self.logger.error(f"用户 {user_id} 模型训练失败")
        
        self.logger.info("模型训练完成")

    def test_online_prediction(self):
        """测试在线预测"""
        self.logger.info("开始在线预测测试...")
        
        predictor = SimplePredictor()
        
        # 为每个用户测试预测
        for user_id in self.test_users:
            self.logger.info(f"测试用户 {user_id} 的在线预测...")
            
            # 直接测试预测功能，不传递测试数据（让它从数据库加载）
            predictions = predictor.predict_user_behavior(user_id)
            
            if predictions is not None and len(predictions) > 0:
                self.logger.info(f"用户 {user_id} 预测结果:")
                # 显示第一个预测结果
                first_pred = predictions[0]
                self.logger.info(f"  异常分数: {first_pred.get('anomaly_score', 'N/A')}")
                self.logger.info(f"  预测结果: {first_pred.get('is_normal', 'N/A')}")
                self.logger.info(f"  置信度: {first_pred.get('probability', 'N/A')}")
            else:
                self.logger.error(f"用户 {user_id} 预测失败")
        
        self.logger.info("在线预测测试完成")

    def _generate_test_prediction_data(self, user_id):
        """生成测试预测数据"""
        # 生成一些新的鼠标事件数据
        test_events = []
        start_time = time.time()
        x, y = 100, 100
        
        behavior = self._get_user_behavior_pattern(user_id)
        
        for i in range(100):  # 生成100个测试事件
            timestamp = start_time + i * 0.1
            x, y = self._generate_next_position(x, y, behavior)
            event_type = self._generate_event_type(i, behavior)
            
            test_events.append({
                'timestamp': timestamp,
                'x': x,
                'y': y,
                'event_type': event_type,
                'button': 'left',
                'wheel_delta': 0
            })
        
        return test_events

    def run_complete_workflow(self):
        """运行完整工作流程"""
        self.logger.info("=" * 60)
        self.logger.info("开始完整工作流程测试")
        self.logger.info("=" * 60)
        
        try:
            # 步骤1: 生成测试数据
            self.logger.info("\n📊 步骤1: 生成测试数据")
            self.generate_test_mouse_data()
            
            # 步骤2: 处理特征
            self.logger.info("\n🔧 步骤2: 处理特征")
            self.process_features()
            
            # 步骤3: 训练模型
            self.logger.info("\n🤖 步骤3: 训练模型")
            self.train_models()
            
            # 步骤4: 测试在线预测
            self.logger.info("\n🎯 步骤4: 测试在线预测")
            self.test_online_prediction()
            
            self.logger.info("\n" + "=" * 60)
            self.logger.info("✅ 完整工作流程测试成功完成！")
            self.logger.info("=" * 60)
            
            # 生成测试报告
            self._generate_test_report()
            
        except Exception as e:
            self.logger.error(f"工作流程测试失败: {str(e)}")
            raise

    def _generate_test_report(self):
        """生成测试报告"""
        self.logger.info("\n📋 生成测试报告...")
        
        report = {
            'test_time': datetime.now().isoformat(),
            'test_users': self.test_users,
            'sessions_per_user': self.sessions_per_user,
            'events_per_session': self.events_per_session,
            'total_events': len(self.test_users) * self.sessions_per_user * self.events_per_session
        }
        
        # 检查数据库状态
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 鼠标事件统计
        cursor.execute("SELECT COUNT(*) FROM mouse_events WHERE user_id LIKE 'test_user%'")
        mouse_events_count = cursor.fetchone()[0]
        report['mouse_events_count'] = mouse_events_count
        
        # 特征数据统计
        cursor.execute("SELECT COUNT(*) FROM features WHERE user_id LIKE 'test_user%'")
        features_count = cursor.fetchone()[0]
        report['features_count'] = features_count
        
        # 模型文件检查
        models_path = Path(self.config.get_paths()['models'])
        model_files = []
        for user_id in self.test_users:
            model_file = models_path / f"user_{user_id}_model.pkl"
            if model_file.exists():
                model_files.append(f"user_{user_id}_model.pkl")
        
        report['trained_models'] = model_files
        report['model_count'] = len(model_files)
        
        conn.close()
        
        # 保存报告
        report_path = Path('logs/test_report.json')
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            import json
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"测试报告已保存到: {report_path}")
        
        # 显示报告摘要
        self.logger.info("\n📊 测试报告摘要:")
        self.logger.info(f"  测试时间: {report['test_time']}")
        self.logger.info(f"  测试用户数: {len(report['test_users'])}")
        self.logger.info(f"  鼠标事件总数: {report['mouse_events_count']}")
        self.logger.info(f"  特征数据总数: {report['features_count']}")
        self.logger.info(f"  训练模型数: {report['model_count']}")
        self.logger.info(f"  模型文件: {', '.join(report['trained_models'])}")

def main():
    """主函数"""
    print("🔧 完整工作流程测试工具")
    print("=" * 50)
    
    # 创建测试实例
    test = CompleteWorkflowTest()
    
    # 运行完整工作流程
    test.run_complete_workflow()

if __name__ == "__main__":
    main()
