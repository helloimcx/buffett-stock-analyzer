#!/usr/bin/env python3
"""
巴菲特股息筛选系统入口脚本
"""

import sys
from pathlib import Path

# 添加src目录到Python路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# 导入主程序
from src.buffett.main import main

if __name__ == "__main__":
    sys.exit(main())