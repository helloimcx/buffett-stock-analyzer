"""
文件加载工具
处理配置文件和股票代码文件的加载
"""

from typing import List


def load_symbols_from_file(filepath: str) -> List[str]:
    """从文件加载股票代码列表"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            symbols = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
        return symbols
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        return []