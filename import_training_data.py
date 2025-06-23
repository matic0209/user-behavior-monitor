#!/usr/bin/env python3
"""
导入训练数据到数据库的启动脚本
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.model_trainer.training_data_importer import main

if __name__ == "__main__":
    main() 