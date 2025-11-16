"""
指定股票代码配置管理
支持从配置文件加载目标股票列表
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class TargetStock:
    """目标股票信息"""
    code: str
    name: str
    exchange: str
    symbol: str  # 完整股票代码，如 000001.SZ

    def __post_init__(self):
        """后处理，确保数据格式正确"""
        self.code = self.code.strip()
        self.name = self.name.strip()
        self.exchange = self.exchange.strip().upper()
        self.symbol = f"{self.code}.{self.exchange}"


class TargetStocksConfig:
    """目标股票配置管理器"""

    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置管理器

        Args:
            config_file: 配置文件路径，默认为项目根目录下的 target_stocks.conf
        """
        if config_file is None:
            # 默认配置文件位置
            project_root = Path(__file__).parent.parent.parent.parent
            config_file = project_root / "target_stocks.conf"

        self.config_file = Path(config_file)
        self._target_stocks: List[TargetStock] = []

    def load_config(self) -> List[TargetStock]:
        """
        从配置文件加载目标股票列表

        Returns:
            目标股票列表
        """
        if not self.config_file.exists():
            logger.warning(f"配置文件不存在: {self.config_file}")
            return []

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            stocks = []
            for line_num, line in enumerate(lines, 1):
                line = line.strip()

                # 跳过空行和注释行
                if not line or line.startswith('#'):
                    continue

                # 解析股票信息
                try:
                    stock = self._parse_line(line)
                    if stock:
                        stocks.append(stock)
                        logger.debug(f"加载目标股票: {stock.symbol} - {stock.name}")
                except Exception as e:
                    logger.warning(f"解析配置文件第{line_num}行失败: {line}, 错误: {e}")
                    continue

            self._target_stocks = stocks
            logger.info(f"成功加载 {len(stocks)} 只目标股票")
            return stocks

        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return []

    def _parse_line(self, line: str) -> Optional[TargetStock]:
        """
        解析配置行

        格式: 股票代码:股票名称:交易所
        例如: 000001:平安银行:SZ

        Args:
            line: 配置行

        Returns:
            解析后的目标股票对象
        """
        # 移除行尾注释
        if '#' in line:
            line = line[:line.index('#')]

        # 分割字段
        parts = [part.strip() for part in line.split(':')]

        if len(parts) < 2:
            raise ValueError(f"配置格式错误，至少需要股票代码和名称")

        code = parts[0]
        name = parts[1]

        # 如果没有指定交易所，根据股票代码推断
        if len(parts) >= 3:
            exchange = parts[2].upper()
        else:
            exchange = self._infer_exchange(code)

        # 验证股票代码格式
        if not self._validate_stock_code(code):
            raise ValueError(f"股票代码格式错误: {code}")

        # 验证交易所代码
        if exchange not in ['SH', 'SZ']:
            raise ValueError(f"交易所代码错误: {exchange}")

        return TargetStock(code=code, name=name, exchange=exchange, symbol=f"{code}.{exchange}")

    def _infer_exchange(self, code: str) -> str:
        """
        根据股票代码推断交易所

        Args:
            code: 股票代码

        Returns:
            交易所代码 (SH/SZ)
        """
        # 上海证券交易所：6开头
        if code.startswith('6'):
            return 'SH'
        # 深圳证券交易所：0、2、3开头
        elif code.startswith(('0', '2', '3')):
            return 'SZ'
        else:
            # 默认为深圳
            logger.warning(f"无法推断交易所 {code}，默认使用深圳")
            return 'SZ'

    def _validate_stock_code(self, code: str) -> bool:
        """
        验证股票代码格式

        Args:
            code: 股票代码

        Returns:
            是否有效
        """
        # A股股票代码为6位数字
        return bool(re.match(r'^\d{6}$', code))

    def get_target_stocks(self) -> List[TargetStock]:
        """
        获取目标股票列表

        Returns:
            目标股票列表
        """
        if not self._target_stocks:
            self.load_config()
        return self._target_stocks

    def get_symbols(self) -> List[str]:
        """
        获取目标股票代码列表

        Returns:
            股票代码列表，如 ['000001.SZ', '600036.SH']
        """
        return [stock.symbol for stock in self.get_target_stocks()]

    def get_codes(self) -> List[str]:
        """
        获取股票代码列表

        Returns:
            股票代码列表，如 ['000001', '600036']
        """
        return [stock.code for stock in self.get_target_stocks()]

    def get_stock_by_code(self, code: str) -> Optional[TargetStock]:
        """
        根据股票代码查找股票信息

        Args:
            code: 股票代码

        Returns:
            目标股票对象，未找到返回None
        """
        for stock in self.get_target_stocks():
            if stock.code == code:
                return stock
        return None

    def get_stock_by_symbol(self, symbol: str) -> Optional[TargetStock]:
        """
        根据完整股票代码查找股票信息

        Args:
            symbol: 完整股票代码，如 000001.SZ

        Returns:
            目标股票对象，未找到返回None
        """
        for stock in self.get_target_stocks():
            if stock.symbol == symbol:
                return stock
        return None

    def filter_stocks_by_codes(self, stock_df, code_column: str = 'code'):
        """
        从股票数据中筛选出目标股票
        优化版本：优先使用名称匹配，避免代码格式问题

        Args:
            stock_df: 股票数据DataFrame
            code_column: 股票代码列名

        Returns:
            筛选后的股票数据
        """
        if stock_df.empty:
            return pd.DataFrame()

        target_stocks = self.get_target_stocks()
        logger.info(f"🎯 筛选 {len(target_stocks)} 只目标股票")

        # 创建代码到名称的映射
        code_to_name = {stock.code: stock.name for stock in target_stocks}

        # 检查DataFrame中的列，优先使用名称匹配
        name_column = None
        for col in ['名称', 'name', 'Name', '股票名称']:
            if col in stock_df.columns:
                name_column = col
                break

        # 优先使用名称匹配，更可靠
        if name_column:
            logger.info(f"✅ 使用名称列 '{name_column}' 进行匹配")
            target_names = set(code_to_name.values())
            filtered_df = stock_df[stock_df[name_column].isin(target_names)]

            if len(filtered_df) > 0:
                logger.info(f"🎉 名称匹配成功，找到 {len(filtered_df)} 只目标股票")
                return filtered_df
            else:
                logger.warning("⚠️  名称匹配未找到结果，尝试代码匹配")

        # 备用：尝试代码匹配
        if code_column not in stock_df.columns:
            # 尝试找到代码列
            for col in ['代码', 'symbol', 'code', 'Code']:
                if col in stock_df.columns:
                    code_column = col
                    break

        if code_column in stock_df.columns:
            logger.info(f"🔄 使用代码列 '{code_column}' 进行匹配")
            target_codes = list(code_to_name.keys())
            filtered_stocks = []

            for _, row in stock_df.iterrows():
                market_code = str(row[code_column])

                # 智能代码匹配
                for target_code in target_codes:
                    if (market_code == target_code or  # 完全匹配
                        market_code == target_code.split('.')[0] or  # 忽略后缀
                        market_code.replace('sh', '').replace('sz', '') == target_code.replace('.SH', '').replace('.SZ', '') or  # 移除交易所标识
                        target_code.split('.')[0] in market_code):  # 包含6位代码
                        filtered_stocks.append(row)
                        break

            if filtered_stocks:
                filtered_df = pd.DataFrame(filtered_stocks)
                logger.info(f"✅ 代码匹配成功，找到 {len(filtered_df)} 只目标股票")
                return filtered_df

        # 如果都失败，记录详细日志并返回空DataFrame
        logger.warning("❌ 无法匹配目标股票")
        logger.warning(f"   目标股票: {[f'{code}:{name}' for code, name in code_to_name.items()]}")
        logger.warning(f"   数据列: {list(stock_df.columns)}")
        if '代码' in stock_df.columns:
            sample_codes = stock_df['代码'].head(5).tolist()
            logger.warning(f"   数据代码示例: {sample_codes}")
        if '名称' in stock_df.columns:
            sample_names = stock_df['名称'].head(5).tolist()
            logger.warning(f"   数据名称示例: {sample_names}")

        return pd.DataFrame()

    def create_sample_config(self, file_path: Optional[str] = None):
        """
        创建示例配置文件

        Args:
            file_path: 配置文件路径
        """
        if file_path is None:
            file_path = self.config_file

        sample_content = """# 指定股票代码筛选配置
# 格式：股票代码:股票名称:交易所 (SH=上海, SZ=深圳)
# 每行一只股票，支持注释

# 银行股
000001:平安银行:SZ
600036:招商银行:SH
601166:兴业银行:SH

# 保险股
601318:中国平安:SH
601601:中国太保:SH

# 高股息股票
600900:长江电力:SH
000069:华侨城A:SZ
"""

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(sample_content)
            logger.info(f"示例配置文件已创建: {file_path}")
        except Exception as e:
            logger.error(f"创建示例配置文件失败: {e}")


# 全局配置实例
_target_config: Optional[TargetStocksConfig] = None


def get_target_stocks_config(config_file: Optional[str] = None) -> TargetStocksConfig:
    """
    获取目标股票配置实例（单例模式）

    Args:
        config_file: 配置文件路径

    Returns:
        配置实例
    """
    global _target_config
    if _target_config is None or config_file is not None:
        _target_config = TargetStocksConfig(config_file)
    return _target_config