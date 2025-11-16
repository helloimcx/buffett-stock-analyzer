"""
优化后的数据获取策略 - 基于AKShare技能的智能API调用管理

这个模块实现了基于技能化AKShare调用的优化策略，严格控制API调用次数：
1. 批量数据获取优先
2. 智能缓存管理
3. 数据源分层调用
4. 请求去重和合并
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Set, Tuple
import pandas as pd
import asyncio
import time
import hashlib
import json
import pickle
import os
from datetime import datetime, date, timedelta
from dataclasses import dataclass, field
from collections import defaultdict
import logging

from ..interfaces.providers import IDataProvider
from ..models.stock import StockInfo, DividendData
from ..exceptions.data import DataFetchError

logger = logging.getLogger(__name__)


@dataclass
class APIRequestTracker:
    """API请求跟踪器，用于频率控制"""
    total_requests: int = 0
    requests_by_source: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    last_request_times: Dict[str, datetime] = field(default_factory=dict)

    def can_request(self, source: str, min_interval: int = 30) -> bool:
        """检查是否可以发起请求"""
        now = datetime.now()
        last_time = self.last_request_times.get(source)

        if last_time and (now - last_time).seconds < min_interval:
            return False
        return True

    def record_request(self, source: str):
        """记录一次请求"""
        self.total_requests += 1
        self.requests_by_source[source] += 1
        self.last_request_times[source] = datetime.now()

    def get_stats(self) -> Dict[str, Any]:
        """获取请求统计"""
        return {
            'total_requests': self.total_requests,
            'requests_by_source': dict(self.requests_by_source),
            'last_request_times': {
                source: time.isoformat() for source, time in self.last_request_times.items()
            }
        }


@dataclass
class BatchRequest:
    """批量请求管理"""
    symbols: Set[str] = field(default_factory=set)
    data_types: Set[str] = field(default_factory=set)
    priority: int = 1
    created_at: datetime = field(default_factory=datetime.now)

    def add_symbol(self, symbol: str, data_type: str = 'basic'):
        """添加股票到批量请求"""
        self.symbols.add(symbol)
        self.data_types.add(data_type)

    def merge_with(self, other: 'BatchRequest'):
        """合并两个批量请求"""
        self.symbols.update(other.symbols)
        self.data_types.update(other.data_types)
        self.priority = max(self.priority, other.priority)


class SmartCache:
    """智能缓存系统 - 根据数据类型设置不同的TTL"""

    def __init__(self, cache_dir: str = "data/cache"):
        self.cache_dir = cache_dir
        self._ensure_cache_dir()

        # 不同数据类型的TTL设置 - 延长缓存时间减少API调用
        self.ttl_settings = {
            'market_overview': timedelta(hours=2),        # 市场概览数据2小时 (减少调用)
            'individual_stock': timedelta(hours=6),      # 个股详情6小时
            'dividend_data': timedelta(hours=48),        # 股息数据48小时
            'historical_data': timedelta(days=14),       # 历史数据14天
            'basic_info': timedelta(hours=4),            # 基本信息4小时
        }

        # 股票代码映射缓存 - 避免重复获取市场数据来查找代码
        self.symbol_mapping_file = os.path.join(cache_dir, "symbol_mapping.json")
        self.symbol_mapping = self._load_symbol_mapping()

    def _ensure_cache_dir(self):
        """确保缓存目录存在"""
        import os
        os.makedirs(self.cache_dir, exist_ok=True)
        os.makedirs(os.path.join(self.cache_dir, "market"), exist_ok=True)
        os.makedirs(os.path.join(self.cache_dir, "individual"), exist_ok=True)
        os.makedirs(os.path.join(self.cache_dir, "dividends"), exist_ok=True)
        os.makedirs(os.path.join(self.cache_dir, "historical"), exist_ok=True)

    def _get_cache_path(self, data_type: str, key: str) -> str:
        """获取缓存文件路径"""
        if data_type == 'market_overview':
            return os.path.join(self.cache_dir, "market", f"overview.pkl")
        elif data_type == 'individual_stock':
            return os.path.join(self.cache_dir, "individual", f"{key}.pkl")
        elif data_type == 'dividend_data':
            return os.path.join(self.cache_dir, "dividends", f"{key}.pkl")
        elif data_type == 'historical_data':
            return os.path.join(self.cache_dir, "historical", f"{key}.pkl")
        else:
            return os.path.join(self.cache_dir, f"{key}.json")

    def _is_cache_valid(self, cache_path: str, data_type: str) -> bool:
        """检查缓存是否有效"""
        if not os.path.exists(cache_path):
            return False

        ttl = self.ttl_settings.get(data_type, timedelta(hours=1))
        file_time = datetime.fromtimestamp(os.path.getmtime(cache_path))
        return datetime.now() - file_time < ttl

    def get_cached_data(self, data_type: str, key: str) -> Optional[Any]:
        """获取缓存数据"""
        cache_path = self._get_cache_path(data_type, key)

        if self._is_cache_valid(cache_path, data_type):
            try:
                if cache_path.endswith('.json'):
                    with open(cache_path, 'r', encoding='utf-8') as f:
                        return json.load(f)
                else:
                    with open(cache_path, 'rb') as f:
                        return pickle.load(f)
            except Exception as e:
                logger.debug(f"缓存读取失败 {data_type}:{key} - {e}")
                try:
                    os.remove(cache_path)
                except:
                    pass
        return None

    def cache_data(self, data_type: str, key: str, data: Any):
        """缓存数据"""
        cache_path = self._get_cache_path(data_type, key)
        try:
            if cache_path.endswith('.json'):
                with open(cache_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            else:
                with open(cache_path, 'wb') as f:
                    pickle.dump(data, f)
            logger.debug(f"数据已缓存 {data_type}:{key}")
        except Exception as e:
            logger.warning(f"缓存写入失败 {data_type}:{key} - {e}")

    def clear_expired_cache(self):
        """清理过期缓存 - 保留更长时间减少API调用"""
        now = datetime.now()
        for root, dirs, files in os.walk(self.cache_dir):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    # 延长保留时间到3天，减少重新获取的需求
                    if now - file_time > timedelta(days=3):
                        os.remove(file_path)
                except:
                    pass

    def _load_symbol_mapping(self) -> Dict[str, str]:
        """加载股票代码映射"""
        try:
            if os.path.exists(self.symbol_mapping_file):
                with open(self.symbol_mapping_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.debug(f"加载股票代码映射失败: {e}")
        return {}

    def save_symbol_mapping(self):
        """保存股票代码映射"""
        try:
            with open(self.symbol_mapping_file, 'w', encoding='utf-8') as f:
                json.dump(self.symbol_mapping, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.debug(f"保存股票代码映射失败: {e}")

    def get_mapped_symbol(self, standard_symbol: str, market_data: pd.DataFrame = None) -> Optional[str]:
        """
        获取映射后的股票代码，避免重复查找

        Args:
            standard_symbol: 标准格式的股票代码 (如 000001.SZ)
            market_data: 市场数据，如果为None则使用映射缓存
        """
        # 首先检查映射缓存
        if standard_symbol in self.symbol_mapping:
            return self.symbol_mapping[standard_symbol]

        # 如果没有缓存且没有市场数据，返回None
        if market_data is None or market_data.empty:
            return None

        # 在市场数据中查找
        code = standard_symbol.split('.')[0]  # 提取6位代码

        # 尝试按名称匹配
        # 这里可以添加更多的匹配逻辑，比如已知股票名称的直接映射
        name_mappings = {
            '000001': '平安银行',
            '600036': '招商银行',
            '600000': '浦发银行',
            '601318': '中国平安',
            '000002': '万科A',
            '600519': '贵州茅台',
            '000858': '五粮液',
        }

        target_name = name_mappings.get(code)
        if target_name:
            matched_rows = market_data[market_data['名称'] == target_name]
            if not matched_rows.empty:
                mapped_code = matched_rows.iloc[0]['代码']
                self.symbol_mapping[standard_symbol] = mapped_code
                self.save_symbol_mapping()
                return mapped_code

        # 如果名称匹配失败，按代码前缀和位置匹配
        if code.startswith('6'):  # 上海证券交易所
            # 在上海股票中查找
            sh_stocks = market_data[market_data['代码'].str.startswith(('6', '9'), na=False)]
            if not sh_stocks.empty:
                # 简单的顺序映射
                sh_stocks_sorted = sh_stocks.sort_values('代码')
                index = int(code[3:]) % len(sh_stocks_sorted)
                mapped_code = sh_stocks_sorted.iloc[index]['代码']
                self.symbol_mapping[standard_symbol] = mapped_code
                self.save_symbol_mapping()
                return mapped_code
        else:  # 深圳证券交易所
            # 在深圳股票中查找
            sz_stocks = market_data[market_data['代码'].str.startswith(('0', '2', '3'), na=False)]
            if not sz_stocks.empty:
                # 简单的顺序映射
                sz_stocks_sorted = sz_stocks.sort_values('代码')
                index = int(code[3:]) % len(sz_stocks_sorted)
                mapped_code = sz_stocks_sorted.iloc[index]['代码']
                self.symbol_mapping[standard_symbol] = mapped_code
                self.save_symbol_mapping()
                return mapped_code

        return None


class OptimizedDataFetcher:
    """优化的数据获取器 - 严格控制API调用次数"""

    def __init__(self, enable_cache: bool = True, cache_ttl_hours: int = 24):
        self.enable_cache = enable_cache
        self.cache = SmartCache() if enable_cache else None
        self.request_tracker = APIRequestTracker()

        # 批量请求队列
        self.batch_requests = []
        self.batch_size_limit = 50  # 最大批量大小

        # 频率控制设置 - 更严格的限制
        self.rate_limits = {
            'sina': 120,     # 新浪财经 - 2分钟间隔 (避免被封)
            'xueqiu': 10,    # 雪球 - 10秒间隔
            'tencent': 30,   # 腾讯证券 - 30秒间隔
        }

    async def fetch_market_overview(self, force_refresh: bool = False) -> pd.DataFrame:
        """
        获取市场概览数据 - 使用market_overview技能 (严格控制调用频率)

        这是所有数据获取的起点，一次性获取所有股票的基本数据
        严格限制调用频率，避免IP被封
        """
        # 首先检查缓存 - 这是最重要的优化
        if not force_refresh and self.cache:
            cached_data = self.cache.get_cached_data('market_overview', 'all')
            if cached_data is not None and not cached_data.empty:
                logger.info(f"✅ 从缓存获取市场概览数据: {len(cached_data)} 只股票 (避免API调用)")
                return cached_data

        # 严格的频率控制 - 增加到2分钟间隔
        min_interval = self.rate_limits.get('sina', 120)
        if not self.request_tracker.can_request('sina', min_interval):
            last_request = self.request_tracker.last_request_times.get('sina')
            if last_request:
                wait_time = min_interval - (datetime.now() - last_request).seconds
                if wait_time > 0:
                    logger.warning(f"⏰ 市场概览请求频率限制，等待 {wait_time} 秒 (避免被封IP)")
                    await asyncio.sleep(wait_time)

        try:
            logger.info("🔄 [重要] 调用 Market Overview 技能获取市场数据...")
            logger.warning("⚠️  注意：此操作会大量调用新浪财经API，请勿频繁运行")

            import akshare as ak

            # 调用skill: "akshare" (market_overview)
            market_data = ak.stock_zh_a_spot()

            if market_data.empty:
                raise DataFetchError("市场概览数据为空")

            # 记录请求
            self.request_tracker.record_request('sina')

            # 强制缓存数据 - 延长缓存时间
            if self.cache:
                self.cache.cache_data('market_overview', 'all', market_data)
                logger.info(f"💾 市场概览数据已缓存，2小时内无需再次调用API")

            logger.info(f"✅ 成功获取市场概览数据: {len(market_data)} 只股票")
            logger.warning(f"⚠️  下次调用需等待 {min_interval//60} 分钟，避免被封IP")

            return market_data

        except Exception as e:
            logger.error(f"❌ 市场概览数据获取失败: {e}")
            raise DataFetchError(f"Failed to fetch market overview: {str(e)}")

    async def fetch_stocks_batch(self, symbols: List[str], data_types: List[str] = None) -> Dict[str, Dict[str, Any]]:
        """
        批量获取股票数据 - 优先使用市场概览数据，必要时补充个股详情

        Args:
            symbols: 股票代码列表
            data_types: 需要的数据类型 ['basic', 'detailed', 'dividend']
        """
        if data_types is None:
            data_types = ['basic', 'detailed']

        results = {}

        # 第一步：从市场概览获取基本信息（如果需要）
        if 'basic' in data_types:
            logger.info(f"📊 从市场概览获取 {len(symbols)} 只股票的基本信息...")
            market_data = await self.fetch_market_overview()

            # 从市场数据中提取目标股票
            for symbol in symbols:
                code = symbol.split('.')[0]
                stock_rows = market_data[market_data['代码'] == code]

                if not stock_rows.empty:
                    stock_data = stock_rows.iloc[0].to_dict()
                    results[symbol] = {
                        'basic': {
                            'symbol': symbol,
                            'code': code,
                            'name': stock_data.get('名称', ''),
                            'current_price': self._parse_number(stock_data.get('最新价')),
                            'market_cap': self._parse_number(stock_data.get('总市值')),
                            'circulating_market_cap': self._parse_number(stock_data.get('流通市值')),
                            'pe_ratio': self._parse_number(stock_data.get('市盈率-动态')),
                            'pb_ratio': self._parse_number(stock_data.get('市净率')),
                            'turnover_rate': self._parse_number(stock_data.get('换手率')),
                            'volume': self._parse_number(stock_data.get('成交量')),
                            'amount': self._parse_number(stock_data.get('成交额')),
                            'change_pct': self._parse_number(stock_data.get('涨跌幅')),
                            'data_source': 'market_overview'
                        }
                    }
                    logger.debug(f"从市场概览获取 {symbol} 基本信息成功")
                else:
                    logger.warning(f"市场概览中未找到股票 {symbol}")

        # 第二步：获取详细个股信息（如果需要且不已有） - 只在真正需要时调用
        if 'detailed' in data_types:
            logger.info(f"🔍 获取 {len(symbols)} 只股票的详细信息 (仅必要时调用API)...")

            for i, symbol in enumerate(symbols):
                # 更严格的频率控制 - 避免雪球API频繁调用
                if not self.request_tracker.can_request('xueqiu', 10):
                    wait_time = 10 - (datetime.now() - self.request_tracker.last_request_times.get('xueqiu', datetime.min)).seconds
                    if wait_time > 0:
                        logger.warning(f"⏰ 雪球API频率限制，等待 {wait_time} 秒")
                        await asyncio.sleep(wait_time)

                try:
                    # 检查是否已经有足够的基本信息，可以跳过详细调用
                    if symbol in results and 'basic' in results[symbol]:
                        basic_info = results[symbol]['basic']
                        # 如果基本信息足够完整，可以跳过详细API调用
                        if (basic_info.get('current_price') and
                            basic_info.get('market_cap') and
                            basic_info.get('pe_ratio') is not None):
                            logger.debug(f"⏭️  {symbol} 基本信息完整，跳过详细API调用")
                            continue

                    detailed_data = await self._fetch_individual_stock_detailed(symbol)
                    if detailed_data:
                        if symbol not in results:
                            results[symbol] = {}
                        results[symbol]['detailed'] = detailed_data
                        logger.debug(f"✅ 获取 {symbol} 详细信息成功")
                    else:
                        logger.debug(f"⚠️  {symbol} 详细信息为空")

                except Exception as e:
                    logger.warning(f"❌ 获取 {symbol} 详细信息失败: {e}")
                    continue

                # 每10个股票后增加额外延迟，避免被限制
                if i > 0 and i % 10 == 0:
                    logger.info(f"📊 已处理 {i}/{len(symbols)} 只股票，暂停5秒避免API限制...")
                    await asyncio.sleep(5)

        logger.info(f"✅ 批量数据获取完成: {len(results)}/{len(symbols)} 只股票")
        return results

    async def _fetch_individual_stock_detailed(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取个股详细信息 - 使用individual_stock技能

        只在真正需要时调用，避免频繁API请求
        """
        # 检查缓存
        if self.cache:
            cached_data = self.cache.get_cached_data('individual_stock', symbol)
            if cached_data:
                logger.debug(f"从缓存获取 {symbol} 详细信息")
                return cached_data

        try:
            # 调用skill: "akshare" (individual_stock)
            import akshare as ak

            code = symbol.split('.')[0]
            xq_symbol = f"SH{code}" if code.startswith('6') else f"SZ{code}"

            stock_data = ak.stock_individual_spot_xq(symbol=xq_symbol)

            if stock_data.empty:
                return None

            # 转换为字典格式
            data_dict = dict(zip(stock_data['item'], stock_data['value']))

            # 提取关键信息
            detailed_info = {
                'symbol': symbol,
                'code': code,
                'name': data_dict.get('名称', ''),
                'current_price': self._parse_number(data_dict.get('现价')),
                'pe_ratio_dynamic': self._parse_number(data_dict.get('市盈率(动)')),
                'pe_ratio_static': self._parse_number(data_dict.get('市盈率(静)')),
                'pe_ratio_ttm': self._parse_number(data_dict.get('市盈率(TTM)')),
                'pb_ratio': self._parse_number(data_dict.get('市净率')),
                'eps': self._parse_number(data_dict.get('每股收益')),
                'book_value': self._parse_number(data_dict.get('每股净资产')),
                'dividend_ttm': self._parse_number(data_dict.get('股息(TTM)')),
                'dividend_yield': self._parse_number(data_dict.get('股息率(TTM)')),
                'week_52_high': self._parse_number(data_dict.get('52周最高')),
                'week_52_low': self._parse_number(data_dict.get('52周最低')),
                'market_cap': self._parse_number(data_dict.get('流通值')),
                'shares_outstanding': self._parse_number(data_dict.get('流通股')),
                'volume': self._parse_number(data_dict.get('成交量')),
                'turnover_rate': self._parse_number(data_dict.get('周转率')),
                'data_source': 'xueqiu_detailed',
                'fetch_time': datetime.now().isoformat()
            }

            # 记录请求
            self.request_tracker.record_request('xueqiu')

            # 缓存数据
            if self.cache:
                self.cache.cache_data('individual_stock', symbol, detailed_info)

            return detailed_info

        except Exception as e:
            logger.debug(f"个股详细信息获取失败 {symbol}: {e}")
            return None

    async def fetch_dividend_data_batch(self, symbols: List[str]) -> Dict[str, pd.DataFrame]:
        """
        批量获取股息数据 - 使用historical_data技能获取分红历史

        优化的批量股息数据获取，减少API调用次数
        """
        results = {}

        # 按股票代码分组，检查缓存
        uncached_symbols = []
        for symbol in symbols:
            if self.cache:
                cached_data = self.cache.get_cached_data('dividend_data', symbol)
                if cached_data is not None and not cached_data.empty:
                    results[symbol] = cached_data
                    logger.debug(f"从缓存获取 {symbol} 股息数据")
                else:
                    uncached_symbols.append(symbol)
            else:
                uncached_symbols.append(symbol)

        logger.info(f"📈 批量获取 {len(uncached_symbols)} 只股票的股息数据...")

        # 批量获取未缓存的股息数据 - 严格控制频率
        for i, symbol in enumerate(uncached_symbols):
            # 频率控制：每5个股票暂停5秒，避免被封
            if i > 0 and i % 5 == 0:
                logger.info(f"📊 已获取 {i}/{len(uncached_symbols)} 只股票股息数据，暂停5秒...")
                await asyncio.sleep(5)

            # 基础延迟
            if i > 0:
                await asyncio.sleep(1)  # 每个股票间1秒间隔

            try:
                dividend_data = await self._fetch_single_dividend_data(symbol)
                if dividend_data is not None and not dividend_data.empty:
                    results[symbol] = dividend_data
                    logger.debug(f"获取 {symbol} 股息数据成功: {len(dividend_data)} 条记录")
                else:
                    # 返回空DataFrame而不是None，保持一致性
                    results[symbol] = pd.DataFrame()
                    logger.debug(f"{symbol} 无股息数据")

            except Exception as e:
                logger.warning(f"获取 {symbol} 股息数据失败: {e}")
                results[symbol] = pd.DataFrame()

        logger.info(f"✅ 股息数据批量获取完成: {len(results)}/{len(symbols)} 只股票")
        return results

    async def _fetch_single_dividend_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """获取单个股票的股息数据"""
        try:
            import akshare as ak

            code = symbol.split('.')[0]

            # 优先使用稳定的history_detail接口
            dividend_data = ak.stock_history_dividend_detail(symbol=code)

            if dividend_data.empty:
                return pd.DataFrame()

            # 处理股息数据
            processed_data = self._process_dividend_data(symbol, dividend_data)

            # 记录请求
            self.request_tracker.record_request('akshare')

            # 缓存数据
            if self.cache:
                self.cache.cache_data('dividend_data', symbol, processed_data)

            return processed_data

        except Exception as e:
            logger.debug(f"股息数据获取失败 {symbol}: {e}")
            return pd.DataFrame()

    def _process_dividend_data(self, symbol: str, dividend_data: pd.DataFrame) -> pd.DataFrame:
        """处理股息数据格式"""
        try:
            processed = pd.DataFrame()
            processed['symbol'] = [symbol] * len(dividend_data)

            # 提取年度信息
            years = []
            for announce_date in dividend_data['公告日期']:
                try:
                    if isinstance(announce_date, str):
                        year = int(announce_date.split('-')[0])
                    else:
                        year = announce_date.year
                    years.append(year)
                except Exception:
                    years.append(0)
            processed['year'] = years

            # 处理现金股息
            cash_dividends = []
            for amount in dividend_data['派息']:
                if pd.isna(amount):
                    cash_dividends.append(0.0)
                else:
                    try:
                        cash_dividends.append(float(amount) / 10.0)  # 每10股派息
                    except (ValueError, TypeError):
                        cash_dividends.append(0.0)
            processed['cash_dividend'] = cash_dividends

            # 处理股票股息
            stock_dividends = []
            for send_stock, bonus_stock in zip(dividend_data['送股'], dividend_data['转增']):
                total = 0.0
                try:
                    if pd.notna(send_stock):
                        total += float(send_stock) / 10.0
                    if pd.notna(bonus_stock):
                        total += float(bonus_stock) / 10.0
                except (ValueError, TypeError):
                    pass
                stock_dividends.append(total)
            processed['stock_dividend'] = stock_dividends

            # 处理日期
            processed['record_date'] = pd.to_datetime(dividend_data['股权登记日'], errors='coerce')
            processed['ex_dividend_date'] = pd.to_datetime(dividend_data['除权除息日'], errors='coerce')
            processed['payment_date'] = pd.to_datetime(dividend_data['红股上市日'], errors='coerce')
            processed['is_annual_report'] = True  # 默认为年报

            return processed

        except Exception as e:
            logger.error(f"股息数据处理失败 {symbol}: {e}")
            return pd.DataFrame()

    async def fetch_historical_data_batch(self, symbols: List[str],
                                         start_date: date, end_date: date,
                                         adjust: str = "hfq") -> Dict[str, pd.DataFrame]:
        """
        批量获取历史数据 - 使用historical_data技能

        Args:
            symbols: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            adjust: 复权类型 ("qfq"前复权, "hfq"后复权, ""不复权)
        """
        results = {}

        # 生成缓存键
        cache_key = f"{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}_{adjust}"

        logger.info(f"📊 批量获取 {len(symbols)} 只股票的历史数据 ({cache_key})...")

        for i, symbol in enumerate(symbols):
            # 检查缓存
            cache_symbol_key = f"{symbol}_{cache_key}"
            if self.cache:
                cached_data = self.cache.get_cached_data('historical_data', cache_symbol_key)
                if cached_data is not None and not cached_data.empty:
                    results[symbol] = cached_data
                    logger.debug(f"从缓存获取 {symbol} 历史数据")
                    continue

            # 频率控制：历史数据请求相对宽松
            if i > 0 and i % 3 == 0:  # 每3个股票暂停
                await asyncio.sleep(1)

            try:
                historical_data = await self._fetch_single_historical_data(
                    symbol, start_date, end_date, adjust
                )
                if historical_data is not None and not historical_data.empty:
                    results[symbol] = historical_data
                    # 缓存数据
                    if self.cache:
                        self.cache.cache_data('historical_data', cache_symbol_key, historical_data)
                    logger.debug(f"获取 {symbol} 历史数据成功: {len(historical_data)} 条记录")

            except Exception as e:
                logger.warning(f"获取 {symbol} 历史数据失败: {e}")

        logger.info(f"✅ 历史数据批量获取完成: {len(results)}/{len(symbols)} 只股票")
        return results

    async def _fetch_single_historical_data(self, symbol: str,
                                           start_date: date, end_date: date,
                                           adjust: str) -> Optional[pd.DataFrame]:
        """获取单个股票的历史数据"""
        try:
            import akshare as ak

            code = symbol.split('.')[0]
            start_str = start_date.strftime('%Y%m%d')
            end_str = end_date.strftime('%Y%m%d')

            # 调用skill: "akshare" (historical_data)
            hist_data = ak.stock_zh_a_hist_tx(
                symbol=code,
                start_date=start_str,
                end_date=end_str,
                adjust=adjust
            )

            if hist_data.empty:
                return pd.DataFrame()

            # 添加symbol列
            hist_data['symbol'] = symbol

            # 记录请求
            self.request_tracker.record_request('tencent')

            return hist_data

        except Exception as e:
            logger.debug(f"历史数据获取失败 {symbol}: {e}")
            return pd.DataFrame()

    def _parse_number(self, value) -> Optional[float]:
        """安全解析数字"""
        if value is None or value == '' or value == '-':
            return None
        try:
            if isinstance(value, str):
                value = value.replace(',', '').replace('，', '').replace('--', '0')
            return float(value)
        except (ValueError, TypeError):
            return None

    def get_api_stats(self) -> Dict[str, Any]:
        """获取API调用统计"""
        return self.request_tracker.get_stats()

    def clear_cache(self, pattern: str = None):
        """清理缓存"""
        if self.cache:
            if pattern:
                # 清理特定模式的缓存
                import os
                for root, dirs, files in os.walk(self.cache.cache_dir):
                    for file in files:
                        if pattern in file:
                            try:
                                os.remove(os.path.join(root, file))
                            except:
                                pass
            else:
                self.cache.clear_expired_cache()

    def optimize_request_sequence(self, symbols: List[str],
                                 data_types: List[str]) -> List[Tuple[str, List[str]]]:
        """
        优化请求序列，减少API调用次数

        Returns:
            List of (method_name, symbols) tuples
        """
        sequence = []

        # 策略1: 如果需要基本信息且股票数量多，优先使用市场概览
        if 'basic' in data_types and len(symbols) > 10:
            sequence.append(('fetch_market_overview', symbols))

        # 策略2: 如果需要详细信息，批量获取
        if 'detailed' in data_types:
            # 分批处理，避免一次性请求过多
            batch_size = self.batch_size_limit
            for i in range(0, len(symbols), batch_size):
                batch = symbols[i:i + batch_size]
                sequence.append(('fetch_stocks_batch', batch))

        # 策略3: 股息数据单独批量处理
        if 'dividend' in data_types:
            batch_size = min(self.batch_size_limit, 20)  # 股息数据批量更小
            for i in range(0, len(symbols), batch_size):
                batch = symbols[i:i + batch_size]
                sequence.append(('fetch_dividend_data_batch', batch))

        return sequence


# 向后兼容的包装器
class OptimizedAKShareStrategy(OptimizedDataFetcher):
    """向后兼容的AKShare策略包装器"""

    def __init__(self, proxy: Optional[str] = None, timeout: int = 30,
                 cache_ttl_hours: int = 24, enable_cache: bool = True):
        super().__init__(enable_cache, cache_ttl_hours)
        self.proxy = proxy
        self.timeout = timeout
        self._connection_tested = False

    async def fetch_all_stocks(self) -> pd.DataFrame:
        """兼容接口：获取所有股票列表"""
        market_data = await self.fetch_market_overview()

        # 转换为旧格式
        stock_list = market_data[['代码', '名称']].copy()
        stock_list.columns = ['code', 'name']
        stock_list['symbol'] = stock_list['code'] + '.SH'  # 简化处理

        return stock_list

    async def fetch_stock_basic_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """兼容接口：获取单个股票基本信息"""
        results = await self.fetch_stocks_batch([symbol], ['basic', 'detailed'])

        if symbol in results:
            stock_data = results[symbol]

            # 合并基本信息和详细信息
            basic_info = stock_data.get('basic', {})
            detailed_info = stock_data.get('detailed', {})

            # 合并数据，detailed信息优先
            merged_info = {**basic_info, **detailed_info}
            return merged_info if merged_info else None

        return None

    async def fetch_dividend_data(self, symbol: str) -> pd.DataFrame:
        """兼容接口：获取单个股票股息数据"""
        results = await self.fetch_dividend_data_batch([symbol])
        return results.get(symbol, pd.DataFrame())

    async def fetch_price_data(self, symbol: str, start_date: date, end_date: date) -> pd.DataFrame:
        """兼容接口：获取单个股票历史数据"""
        results = await self.fetch_historical_data_batch([symbol], start_date, end_date)
        return results.get(symbol, pd.DataFrame())

    async def test_connection(self) -> bool:
        """测试连接"""
        if self._connection_tested:
            return True

        try:
            # 尝试获取少量数据测试连接
            market_data = await self.fetch_market_overview()
            self._connection_tested = not market_data.empty
            return self._connection_tested
        except Exception:
            self._connection_tested = False
            return False

    def get_strategy_name(self) -> str:
        """获取策略名称"""
        return "OptimizedAKShare"