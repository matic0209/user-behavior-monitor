#!/usr/bin/env python3
"""
TC06 用户行为指纹数据管理功能验证脚本
基于现有的 mouse_data.db 数据库进行功能验证
"""

import sqlite3
import json
import sys
import os
from pathlib import Path
from datetime import datetime

class TC06FingerprintVerifier:
    def __init__(self, db_path="data/mouse_data.db"):
        self.db_path = Path(db_path)
        self.test_results = []
        
    def log_result(self, step, description, result, details=""):
        """记录测试结果"""
        status = "✅ 通过" if result else "❌ 失败"
        self.test_results.append({
            'step': step,
            'description': description,
            'result': result,
            'status': status,
            'details': details
        })
        print(f"步骤{step}: {description} - {status}")
        if details:
            print(f"    详情: {details}")
    
    def verify_database_structure(self):
        """步骤2: 验证指纹数据存储功能"""
        try:
            if not self.db_path.exists():
                self.log_result(2, "验证指纹数据存储", False, "数据库文件不存在")
                return False
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 检查表结构
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            required_tables = ['features', 'mouse_events', 'predictions']
            
            missing_tables = [table for table in required_tables if table not in tables]
            if missing_tables:
                self.log_result(2, "验证指纹数据存储", False, f"缺少表: {missing_tables}")
                return False
            
            # 检查用户数据
            cursor.execute("SELECT COUNT(DISTINCT user_id) FROM features")
            user_count = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT user_id, COUNT(*) as record_count 
                FROM features 
                GROUP BY user_id 
                ORDER BY record_count DESC
            """)
            user_data = cursor.fetchall()
            
            # 验证数据量
            min_users = 5
            min_records_per_user = 100
            
            if user_count < min_users:
                self.log_result(2, "验证指纹数据存储", False, 
                              f"用户数量不足: {user_count} < {min_users}")
                return False
            
            insufficient_users = [user for user, count in user_data if count < min_records_per_user]
            if insufficient_users:
                self.log_result(2, "验证指纹数据存储", False, 
                              f"部分用户记录不足: {insufficient_users}")
                return False
            
            self.log_result(2, "验证指纹数据存储", True, 
                          f"用户数: {user_count}, 记录数: {[count for _, count in user_data[:5]]}")
            
            conn.close()
            return True
            
        except Exception as e:
            self.log_result(2, "验证指纹数据存储", False, f"异常: {str(e)}")
            return False
    
    def verify_feature_vectors(self):
        """步骤3: 验证指纹特征提取功能"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 获取特征向量样本
            cursor.execute("""
                SELECT user_id, feature_vector 
                FROM features 
                WHERE user_id = 'training_user_15' 
                LIMIT 1
            """)
            result = cursor.fetchone()
            
            if not result:
                self.log_result(3, "验证指纹特征提取", False, "无法找到特征向量样本")
                return False
            
            user_id, feature_vector_str = result
            
            # 解析特征向量
            try:
                feature_vector = json.loads(feature_vector_str)
            except json.JSONDecodeError:
                self.log_result(3, "验证指纹特征提取", False, "特征向量格式错误")
                return False
            
            # 验证特征类型
            required_feature_types = [
                'mean',  # 统计特征
                'std',   # 标准差特征
                'min',   # 最小值特征
                'max',   # 最大值特征
            ]
            
            feature_keys = list(feature_vector.keys())
            found_types = []
            
            for feature_type in required_feature_types:
                if any(feature_type in key for key in feature_keys):
                    found_types.append(feature_type)
            
            if len(found_types) < 3:
                self.log_result(3, "验证指纹特征提取", False, 
                              f"特征类型不足: {found_types}")
                return False
            
            # 验证特征数量
            if len(feature_keys) < 10:
                self.log_result(3, "验证指纹特征提取", False, 
                              f"特征数量不足: {len(feature_keys)}")
                return False
            
            self.log_result(3, "验证指纹特征提取", True, 
                          f"特征数量: {len(feature_keys)}, 类型: {found_types}")
            
            conn.close()
            return True
            
        except Exception as e:
            self.log_result(3, "验证指纹特征提取", False, f"异常: {str(e)}")
            return False
    
    def verify_user_management(self):
        """步骤7: 验证指纹数据管理功能"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 验证多用户数据隔离
            cursor.execute("""
                SELECT user_id, 
                       COUNT(*) as total_records,
                       COUNT(DISTINCT session_id) as sessions,
                       MIN(created_at) as first_record,
                       MAX(created_at) as last_record
                FROM features 
                GROUP BY user_id
            """)
            
            user_stats = cursor.fetchall()
            
            if len(user_stats) < 5:
                self.log_result(7, "验证指纹数据管理", False, 
                              f"用户数量不足: {len(user_stats)}")
                return False
            
            # 验证数据完整性
            for user_id, records, sessions, first, last in user_stats:
                if records < 50:  # 每用户至少50条记录
                    self.log_result(7, "验证指纹数据管理", False, 
                                  f"用户 {user_id} 记录不足: {records}")
                    return False
                
                if sessions < 1:  # 每用户至少1个会话
                    self.log_result(7, "验证指纹数据管理", False, 
                                  f"用户 {user_id} 会话不足: {sessions}")
                    return False
            
            # 验证时间戳合理性
            cursor.execute("SELECT MIN(created_at), MAX(created_at) FROM features")
            min_time, max_time = cursor.fetchone()
            
            self.log_result(7, "验证指纹数据管理", True, 
                          f"管理 {len(user_stats)} 个用户, 时间范围: {min_time} 到 {max_time}")
            
            conn.close()
            return True
            
        except Exception as e:
            self.log_result(7, "验证指纹数据管理", False, f"异常: {str(e)}")
            return False
    
    def verify_anomaly_detection_data(self):
        """步骤6: 验证异常行为检测数据"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 检查predictions表
            cursor.execute("SELECT COUNT(*) FROM predictions")
            prediction_count = cursor.fetchone()[0]
            
            if prediction_count == 0:
                self.log_result(6, "验证异常行为检测", False, "无预测记录")
                return False
            
            # 检查预测数据格式
            cursor.execute("""
                SELECT user_id, prediction, anomaly_score, probability, is_normal
                FROM predictions 
                ORDER BY created_at DESC 
                LIMIT 5
            """)
            
            predictions = cursor.fetchall()
            
            for user_id, prediction, anomaly_score, probability, is_normal in predictions:
                # 验证数据范围
                if not (0 <= anomaly_score <= 1):
                    self.log_result(6, "验证异常行为检测", False, 
                                  f"异常分数超范围: {anomaly_score}")
                    return False
                
                if not (0 <= probability <= 1):
                    self.log_result(6, "验证异常行为检测", False, 
                                  f"概率超范围: {probability}")
                    return False
            
            self.log_result(6, "验证异常行为检测", True, 
                          f"预测记录: {prediction_count}, 最新5条数据格式正确")
            
            conn.close()
            return True
            
        except Exception as e:
            self.log_result(6, "验证异常行为检测", False, f"异常: {str(e)}")
            return False
    
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "="*60)
        print("TC06 用户行为指纹数据管理功能验证报告")
        print("="*60)
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"数据库路径: {self.db_path}")
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['result'])
        
        print(f"\n测试汇总:")
        print(f"  总测试项: {total_tests}")
        print(f"  通过项数: {passed_tests}")
        print(f"  失败项数: {total_tests - passed_tests}")
        print(f"  通过率: {passed_tests/total_tests*100:.1f}%")
        
        print(f"\n详细结果:")
        for result in self.test_results:
            print(f"  {result['status']} 步骤{result['step']}: {result['description']}")
            if result['details']:
                print(f"      {result['details']}")
        
        overall_result = "✅ 整体通过" if passed_tests == total_tests else "❌ 整体失败"
        print(f"\n{overall_result}")
        
        return passed_tests == total_tests
    
    def run_verification(self):
        """运行完整验证"""
        print("开始 TC06 用户行为指纹数据管理功能验证...")
        print("="*60)
        
        # 执行各项验证
        self.verify_database_structure()      # 步骤2
        self.verify_feature_vectors()         # 步骤3  
        self.verify_anomaly_detection_data()  # 步骤6
        self.verify_user_management()         # 步骤7
        
        # 生成报告
        return self.generate_report()

def main():
    """主函数"""
    # 检查数据库文件路径
    db_path = "data/mouse_data.db"
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    
    # 运行验证
    verifier = TC06FingerprintVerifier(db_path)
    success = verifier.run_verification()
    
    # 返回适当的退出码
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
