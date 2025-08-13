import yaml
import os
import sys
from pathlib import Path

class ConfigLoader:
    _instance = None
    _config = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigLoader, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._config is None:
            self.load_config()

    def load_config(self):
        """加载配置文件"""
        # 尝试多个可能的配置文件路径
        possible_paths = [
            Path(__file__).parent / 'config.yaml',
            Path.cwd() / 'src' / 'utils' / 'config' / 'config.yaml',
            Path.cwd() / 'config.yaml'
        ]
        
        config_path = None
        for path in possible_paths:
            if path.exists():
                config_path = path
                break
        
        if not config_path:
            raise FileNotFoundError(f"配置文件不存在，尝试的路径: {[str(p) for p in possible_paths]}")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)
        except Exception as e:
            raise Exception(f"配置文件加载失败: {str(e)}")

    def get(self, key, default=None):
        """获取配置值，支持点分隔的路径"""
        try:
            # 支持点分隔的路径，如 'data_collection.collection_interval'
            keys = key.split('.')
            value = self._config
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            
            return value
        except Exception:
            return default

    def get_feature_config(self):
        """获取特征工程配置"""
        return self._config.get('feature_engineering', {})

    def get_model_config(self):
        """获取模型配置"""
        return self._config.get('model', {})

    def get_prediction_config(self):
        """获取预测配置"""
        return self._config.get('prediction', {})

    def get_paths(self):
        """获取路径配置"""
        # 基准路径优先级：环境变量 > 冻结可执行所在目录 > 项目根目录 > 当前工作目录
        env_base = os.getenv('UBM_BASE_PATH')
        if env_base:
            base_path = Path(env_base)
        elif getattr(sys, 'frozen', False):  # PyInstaller 冻结模式
            base_path = Path(sys.executable).parent
        else:
            # 以源码项目根目录为基准（src/utils/config/ -> 项目根）
            try:
                base_path = Path(__file__).resolve().parents[3]
            except Exception:
                base_path = Path.cwd()
        default_paths = {
            'models': str(base_path / 'models'),
            'data': str(base_path / 'data'),
            'logs': str(base_path / 'logs'),
            'results': str(base_path / 'results'),
            'test_data': str(base_path / 'data' / 'processed' / 'all_test_aggregation.pickle'),
            'train_data': str(base_path / 'data' / 'processed' / 'all_training_aggregation.pickle'),
            'database': str(base_path / 'data' / 'mouse_data.db')
        }
        
        # 合并配置文件中的路径
        config_paths = self._config.get('paths', {})
        default_paths.update(config_paths)
        
        # 如果提供了 UBM_DATABASE 环境变量，则强制覆盖数据库路径
        env_db = os.getenv('UBM_DATABASE')
        if env_db:
            default_paths['database'] = env_db
        
        return default_paths

    def get_alert_config(self):
        """获取告警配置"""
        return self._config.get('alert', {})

    def get_user_config(self):
        """获取用户配置"""
        return self._config.get('user', {})

    def get_data_collection_config(self):
        """获取数据采集配置"""
        return self._config.get('data_collection', {})

    def get_feature_processing_config(self):
        """获取特征处理配置"""
        return self._config.get('feature_processing', {})

    def get_model_training_config(self):
        """获取模型训练配置"""
        return self._config.get('model_training', {})

    def get_logging_config(self):
        """获取日志配置"""
        return self._config.get('logging', {})

    def get_system_config(self):
        """获取系统配置"""
        return self._config.get('system', {})

    def get_platform(self):
        """获取平台信息"""
        return self.get_system_config().get('platform', 'unknown')

    def is_windows(self):
        """检查是否为Windows平台"""
        return self.get_platform().lower() == 'windows'

    @property
    def config(self):
        """获取完整配置"""
        return self._config 