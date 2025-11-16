"""
Data fetch strategy implementations using the Strategy pattern.

This module defines different strategies for fetching stock data from various sources,
allowing the system to easily switch between data providers.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import pandas as pd
import re
import os
import json
import pickle
from datetime import datetime, date, timedelta
import hashlib

from ..interfaces.providers import IDataProvider
from ..models.stock import StockInfo, DividendData
from ..exceptions.data import DataFetchError


class LocalCache:
    """本地缓存管理类，用于减少API调用"""

    def __init__(self, cache_dir: str = "data/cache", default_ttl_hours: int = 24):
        """
        初始化缓存管理器

        Args:
            cache_dir: 缓存目录
            default_ttl_hours: 默认缓存过期时间（小时）
        """
        self.cache_dir = cache_dir
        self.default_ttl = timedelta(hours=default_ttl_hours)
        self._ensure_cache_dir()

    def _ensure_cache_dir(self):
        """确保缓存目录存在"""
        os.makedirs(self.cache_dir, exist_ok=True)
        os.makedirs(os.path.join(self.cache_dir, "stocks"), exist_ok=True)
        os.makedirs(os.path.join(self.cache_dir, "dividends"), exist_ok=True)

    def _get_cache_path(self, cache_type: str, key: str) -> str:
        """获取缓存文件路径"""
        if cache_type == "dividends":
            return os.path.join(self.cache_dir, "dividends", f"{key}.pkl")
        elif cache_type == "stocks":
            return os.path.join(self.cache_dir, "stocks", f"{key}.json")
        else:
            return os.path.join(self.cache_dir, f"{key}.pkl")

    def _is_cache_valid(self, cache_path: str, ttl: timedelta = None) -> bool:
        """检查缓存是否有效"""
        if not os.path.exists(cache_path):
            return False

        if ttl is None:
            ttl = self.default_ttl

        # 检查文件修改时间
        file_time = datetime.fromtimestamp(os.path.getmtime(cache_path))
        return datetime.now() - file_time < ttl

    def get_cached_dividends(self, symbol: str, ttl: timedelta = None) -> Optional[pd.DataFrame]:
        """获取缓存的股息数据"""
        cache_path = self._get_cache_path("dividends", symbol)

        if self._is_cache_valid(cache_path, ttl):
            try:
                with open(cache_path, 'rb') as f:
                    data = pickle.load(f)
                return data
            except Exception:
                # 缓存文件损坏，删除并返回None
                try:
                    os.remove(cache_path)
                except:
                    pass
        return None

    def cache_dividends(self, symbol: str, data: pd.DataFrame):
        """缓存股息数据"""
        cache_path = self._get_cache_path("dividends", symbol)
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(data, f)
        except Exception as e:
            print(f"缓存股息数据失败 {symbol}: {e}")

    def get_cached_stock_info(self, symbol: str, ttl: timedelta = None) -> Optional[Dict[str, Any]]:
        """获取缓存的股票信息"""
        cache_path = self._get_cache_path("stocks", symbol)

        if self._is_cache_valid(cache_path, ttl):
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return data
            except Exception:
                # 缓存文件损坏，删除并返回None
                try:
                    os.remove(cache_path)
                except:
                    pass
        return None

    def cache_stock_info(self, symbol: str, data: Dict[str, Any]):
        """缓存股票信息"""
        cache_path = self._get_cache_path("stocks", symbol)
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"缓存股票信息失败 {symbol}: {e}")

    def clear_cache(self, pattern: str = None):
        """清理缓存"""
        if pattern:
            # 清理特定模式的缓存
            for root, dirs, files in os.walk(self.cache_dir):
                for file in files:
                    if pattern in file:
                        try:
                            os.remove(os.path.join(root, file))
                        except:
                            pass
        else:
            # 清理所有缓存
            for root, dirs, files in os.walk(self.cache_dir):
                for file in files:
                    try:
                        os.remove(os.path.join(root, file))
                    except:
                        pass

    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        stats = {
            "cache_dir": self.cache_dir,
            "dividend_files": 0,
            "stock_files": 0,
            "total_size_mb": 0
        }

        try:
            for root, dirs, files in os.walk(self.cache_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    stats["total_size_mb"] += os.path.getsize(file_path) / (1024 * 1024)

                    if "dividends" in root:
                        stats["dividend_files"] += 1
                    elif "stocks" in root:
                        stats["stock_files"] += 1
        except Exception:
            pass

        return stats


class DataFetchStrategy(ABC):
    """Abstract base class for data fetch strategies."""

    @abstractmethod
    async def fetch_all_stocks(self) -> pd.DataFrame:
        """Fetch all available stocks."""
        pass

    @abstractmethod
    async def fetch_stock_basic_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch basic stock information."""
        pass

    @abstractmethod
    async def fetch_dividend_data(self, symbol: str) -> pd.DataFrame:
        """Fetch dividend data for a stock."""
        pass

    @abstractmethod
    async def fetch_price_data(
        self,
        symbol: str,
        start_date: date,
        end_date: date
    ) -> pd.DataFrame:
        """Fetch price data for a stock."""
        pass

    @abstractmethod
    async def test_connection(self) -> bool:
        """Test if the data source is accessible."""
        pass

    @abstractmethod
    def get_strategy_name(self) -> str:
        """Get the name of this strategy."""
        pass


class AKShareStrategy(DataFetchStrategy):
    """AKShare data fetch strategy with local caching."""

    def __init__(self, proxy: Optional[str] = None, timeout: int = 30,
                 cache_ttl_hours: int = 24, enable_cache: bool = True):
        """Initialize AKShare strategy with caching."""
        self.proxy = proxy
        self.timeout = timeout
        self._connection_tested = False
        self.enable_cache = enable_cache

        # 初始化缓存
        if self.enable_cache:
            self.cache = LocalCache(default_ttl_hours=cache_ttl_hours)
        else:
            self.cache = None

    async def fetch_all_stocks(self) -> pd.DataFrame:
        """Fetch all stocks using AKShare."""
        try:
            import akshare as ak

            # Fetch A-share stock list
            stock_list = ak.stock_info_a_code_name()
            if stock_list.empty:
                raise DataFetchError("No stock data returned from AKShare")

            # Clean and format data
            stock_list.columns = ['code', 'name']
            stock_list['symbol'] = stock_list['code'] + '.SH'  # Default to SH

            return stock_list

        except ImportError:
            raise DataFetchError("AKShare library not installed")
        except Exception as e:
            raise DataFetchError(f"Failed to fetch stocks from AKShare: {str(e)}")

    async def fetch_stock_basic_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch basic stock information using AKShare with caching."""
        import logging
        logger = logging.getLogger(__name__)

        # 尝试从缓存获取
        if self.cache:
            cached_data = self.cache.get_cached_stock_info(symbol)
            if cached_data:
                logger.debug(f"从缓存获取股票信息: {symbol}")
                return cached_data

        try:
            import akshare as ak
            import time

            # Extract stock code from symbol
            code = symbol.split('.')[0]

            # 多次重试机制，增加成功率
            max_retries = 3
            retry_delay = 1.0

            for attempt in range(max_retries):
                try:
                    # 添加延迟避免频率限制
                    if attempt > 0:
                        time.sleep(retry_delay)
                        retry_delay *= 1.5  # 指数退避

                    # Fetch basic info
                    info = ak.stock_individual_info_em(symbol=code)

                    if not info.empty:
                        break
                    else:
                        logger.debug(f"股票 {symbol} 第{attempt+1}次尝试获取到空数据")

                except Exception as api_error:
                    logger.warning(f"股票 {symbol} 第{attempt+1}次API调用失败: {str(api_error)}")
                    if attempt == max_retries - 1:
                        raise
                    continue

            if info.empty:
                logger.debug(f"股票 {symbol} 多次重试后仍无基本信息")
                return None

            # Convert to dictionary
            info_dict = info.set_index('item')['value'].to_dict()

            # Map Chinese field names to English field names for compatibility
            field_mapping = {
                '总市值': 'market_cap',
                '流通市值': 'circulating_market_cap',
                '总股本': 'total_shares',
                '流通股': 'circulating_shares',
                '最新': 'current_price',
                '股票代码': 'code',
                '股票简称': 'name',
                '行业': 'industry',
                '上市时间': 'listing_date'
            }

            # Add English field mappings
            for chinese_field, english_field in field_mapping.items():
                if chinese_field in info_dict:
                    info_dict[english_field] = info_dict[chinese_field]
                    # Also keep the original Chinese field for reference

            # Add basic fields
            info_dict['symbol'] = symbol
            info_dict['code'] = code
            info_dict['fetch_time'] = datetime.now().isoformat()  # 添加获取时间

            # Convert market cap to numeric value if it's a string
            if 'market_cap' in info_dict and isinstance(info_dict['market_cap'], str):
                try:
                    # Remove commas and convert to float
                    market_cap_str = info_dict['market_cap'].replace(',', '')
                    info_dict['market_cap'] = float(market_cap_str)

                    # 数据合理性检查：市值应该在100万到10万亿之间
                    if info_dict['market_cap'] < 1_000_000 or info_dict['market_cap'] > 10_000_000_000_000:
                        logger.warning(f"股票 {symbol} 市值数据不合理: {info_dict['market_cap']:.2f}元，设置为None")
                        info_dict['market_cap'] = None

                except (ValueError, AttributeError):
                    logger.warning(f"无法解析市值数据: {info_dict['market_cap']}")
                    info_dict['market_cap'] = None

            # 缓存数据
            if self.cache:
                self.cache.cache_stock_info(symbol, info_dict)

            logger.debug(f"获取并缓存股票信息: {symbol}")
            return info_dict

        except Exception as e:
            logger.warning(f"主要方法获取股票信息失败 {symbol}: {str(e)}")
            # 尝试备用数据源
            return await self._fetch_stock_info_backup(symbol, code if 'code' in locals() else symbol.split('.')[0])

    async def _fetch_stock_info_backup(self, symbol: str, code: str) -> Optional[Dict[str, Any]]:
        """备用数据源获取股票信息 - 改进版多源策略"""
        import logging
        logger = logging.getLogger(__name__)

        try:
            import akshare as ak

            # 数据源优先级策略
            data_sources = [
                self._try_xueqiu_data,      # 雪球接口 - 公司基本面信息
                self._try_quote_data,        # 实时行情数据 - 市值信息
                self._try_alternative_aks,   # 其他AKShare方法
            ]

            for source_func in data_sources:
                try:
                    result = await source_func(symbol, code)
                    if result and self._validate_stock_info(result):
                        logger.debug(f"成功从 {source_func.__name__} 获取 {symbol} 信息")
                        # 缓存数据
                        if self.cache:
                            self.cache.cache_stock_info(symbol, result)
                        return result
                except Exception as e:
                    logger.debug(f"数据源 {source_func.__name__} 失败 {symbol}: {str(e)}")
                    continue

            logger.debug(f"所有备用数据源都失败 {symbol}")
            return None

        except Exception as e:
            logger.debug(f"备用数据源获取异常 {symbol}: {str(e)}")
            return None

    async def _try_xueqiu_data(self, symbol: str, code: str) -> Optional[Dict[str, Any]]:
        """尝试雪球接口获取公司基本信息"""
        import logging
        logger = logging.getLogger(__name__)

        try:
            import akshare as ak

            # 雪球接口需要带交易所前缀的股票代码
            xq_symbol = self._convert_to_xq_symbol(symbol, code)

            logger.debug(f"尝试雪球接口获取 {symbol} (雪球代码: {xq_symbol})")

            info = ak.stock_individual_basic_info_xq(symbol=xq_symbol)

            if info.empty:
                logger.debug(f"雪球接口返回空数据 {symbol}")
                return None

            info_dict = info.set_index('item')['value'].to_dict()

            # 映射雪球字段到标准字段
            xq_info = {
                'symbol': symbol,
                'code': code,
                'name': info_dict.get('org_short_name_cn', ''),
                'full_name': info_dict.get('org_name_cn', ''),
                'english_name': info_dict.get('org_name_en', ''),
                'main_business': info_dict.get('main_operation_business', ''),
                'business_scope': info_dict.get('operating_scope', ''),
                'registered_capital': self._parse_number(info_dict.get('reg_asset')),
                'staff_num': self._parse_number(info_dict.get('staff_num')),
                'listed_date': self._parse_timestamp(info_dict.get('listed_date')),
                'actual_controller': info_dict.get('actual_controller', ''),
                'company_type': info_dict.get('classi_name', ''),
                'chairman': info_dict.get('chairman', ''),
                'legal_representative': info_dict.get('legal_representative', ''),
                'address': info_dict.get('reg_address_cn', ''),
                'telephone': info_dict.get('telephone', ''),
                'email': info_dict.get('email', ''),
                'website': info_dict.get('org_website', ''),
                'fetch_time': datetime.now().isoformat(),
                'data_source': 'xueqiu_basic'
            }

            # 雪球接口不提供市值信息，但提供丰富的公司基本面信息
            logger.debug(f"雪球接口成功获取 {symbol} 基本信息")
            return xq_info

        except Exception as e:
            logger.debug(f"雪球接口失败 {symbol}: {str(e)}")
            return None

    async def _try_quote_data(self, symbol: str, code: str) -> Optional[Dict[str, Any]]:
        """尝试实时行情数据获取市值信息"""
        import logging
        logger = logging.getLogger(__name__)

        try:
            import akshare as ak

            logger.debug(f"尝试实时行情数据获取 {symbol} 市值")

            # 获取实时行情数据
            quote_data = ak.stock_zh_a_spot_em()
            if quote_data.empty:
                return None

            stock_data = quote_data[quote_data['代码'] == code]
            if stock_data.empty:
                return None

            row = stock_data.iloc[0]
            quote_info = {
                'symbol': symbol,
                'code': code,
                'name': row.get('名称', ''),
                'current_price': self._parse_number(row.get('最新价')),
                'market_cap': self._parse_number(row.get('总市值')),
                'circulating_market_cap': self._parse_number(row.get('流通市值')),
                'pe_ratio': self._parse_number(row.get('市盈率-动态')),
                'pb_ratio': self._parse_number(row.get('市净率')),
                'turnover_rate': self._parse_number(row.get('换手率')),
                'volume': self._parse_number(row.get('成交量')),
                'amount': self._parse_number(row.get('成交额')),
                'fetch_time': datetime.now().isoformat(),
                'data_source': 'quote_realtime'
            }

            # 验证市值数据
            if quote_info['market_cap'] and quote_info['market_cap'] > 0:
                logger.debug(f"实时行情成功获取 {symbol} 市值: {quote_info['market_cap']/100_000_000:.0f}亿")
                return quote_info

        except Exception as e:
            logger.debug(f"实时行情数据失败 {symbol}: {str(e)}")
            return None

    async def _try_alternative_aks(self, symbol: str, code: str) -> Optional[Dict[str, Any]]:
        """尝试其他AKShare方法"""
        import logging
        logger = logging.getLogger(__name__)

        backup_methods = [
            ('stock_individual_info_name', '股票名称'),
            ('stock_individual_basic_info', '基本信息'),
            ('stock_a_all', 'A股实时数据'),
            ('stock_zh_a_spot_em', 'A股实时行情'),
        ]

        for method_name, method_desc in backup_methods:
            try:
                logger.debug(f"尝试备用方法 {method_desc} 获取 {symbol}")

                # 动态调用AKShare方法
                method = getattr(ak, method_name, None)
                if method and callable(method):
                    # 根据不同方法传入不同参数
                    try:
                        if 'name' in method_name:
                            result = method(symbol=symbol)
                        elif 'all' in method_name or 'spot' in method_name:
                            # 对于实时数据方法，尝试找到对应股票
                            result = method()
                            if result is not None and not result.empty:
                                # 在实时数据中查找对应股票
                                stock_data = result[result['代码'] == code]
                                if not stock_data.empty:
                                    result = stock_data
                        else:
                            result = method(symbol=code)

                        if result is not None and not result.empty:
                            # 处理不同格式的结果
                            backup_info = self._extract_market_cap_from_data(result, symbol, code)
                            if backup_info and backup_info.get('market_cap'):
                                logger.debug(f"备用方法 {method_desc} 成功获取 {symbol} 市值: {backup_info['market_cap']/100_000_000:.0f}亿")
                                return backup_info

                    except Exception as method_error:
                        logger.debug(f"备用方法 {method_desc} 参数错误 {symbol}: {str(method_error)}")
                        continue

            except Exception as e:
                logger.debug(f"备用方法 {method_desc} 失败 {symbol}: {str(e)}")
                continue

        return None

    def _convert_to_xq_symbol(self, symbol: str, code: str) -> str:
        """转换为雪球股票代码格式"""
        if symbol.startswith(('SH', 'SZ')):
            return symbol
        elif code.startswith('6'):
            return f"SH{code}"
        else:
            return f"SZ{code}"

    def _parse_number(self, value) -> Optional[float]:
        """安全解析数字"""
        if value is None or value == '':
            return None
        try:
            if isinstance(value, str):
                # 移除逗号等格式字符
                value = value.replace(',', '').replace('，', '')
            return float(value)
        except (ValueError, TypeError):
            return None

    def _parse_timestamp(self, value) -> Optional[str]:
        """解析时间戳为日期字符串"""
        if value is None or value == '':
            return None
        try:
            import datetime
            if isinstance(value, (int, float)):
                # 毫秒时间戳转换
                dt = datetime.datetime.fromtimestamp(value / 1000)
                return dt.strftime('%Y-%m-%d')
            return str(value)
        except (ValueError, TypeError, OSError):
            return None

    def _validate_stock_info(self, info: Dict[str, Any]) -> bool:
        """验证股票信息的基本有效性"""
        if not info or not isinstance(info, dict):
            return False

        # 至少需要有股票代码
        if not info.get('code'):
            return False

        # 如果有市值数据，必须为正数
        market_cap = info.get('market_cap')
        if market_cap is not None and (not isinstance(market_cap, (int, float)) or market_cap <= 0):
            return False

        return True

    def _extract_market_cap_from_data(self, data, symbol: str, code: str) -> Optional[Dict[str, Any]]:
        """从不同格式的数据中提取市值信息"""
        try:
            if hasattr(data, 'empty') and data.empty:
                return None

            # 处理DataFrame格式
            if hasattr(data, 'columns'):
                # 查找市值相关字段
                market_cap_fields = ['总市值', 'market_cap', '市值', '总股本', '流通市值']
                price_fields = ['最新价', 'current_price', '最新', '价格']
                name_fields = ['名称', 'name', '股票名称', '简称']

                result = {'symbol': symbol, 'code': code}

                # 提取市值
                for field in market_cap_fields:
                    if field in data.columns:
                        value = data[field].iloc[0] if len(data) > 0 else None
                        if value is not None:
                            result['market_cap'] = self._parse_number(value)
                            break

                # 提取价格
                for field in price_fields:
                    if field in data.columns:
                        value = data[field].iloc[0] if len(data) > 0 else None
                        if value is not None:
                            result['current_price'] = self._parse_number(value)
                            break

                # 提取名称
                for field in name_fields:
                    if field in data.columns:
                        value = data[field].iloc[0] if len(data) > 0 else None
                        if value is not None:
                            result['name'] = str(value)
                            break

                result['fetch_time'] = datetime.now().isoformat()
                result['data_source'] = 'alternative_method'

                return result

            # 处理字典格式
            elif isinstance(data, dict):
                return {
                    'symbol': symbol,
                    'code': code,
                    'market_cap': self._parse_number(data.get('总市值')),
                    'current_price': self._parse_number(data.get('最新价')),
                    'name': str(data.get('名称', '')),
                    'fetch_time': datetime.now().isoformat(),
                    'data_source': 'alternative_method'
                }

        except Exception as e:
            logger.debug(f"提取市值信息失败 {symbol}: {str(e)}")
            return None
    async def fetch_dividend_data(self, symbol: str) -> pd.DataFrame:
        """Fetch dividend data using AKShare with caching and multiple fallback methods."""
        import logging
        import asyncio
        logger = logging.getLogger(__name__)

        # 首先尝试从缓存获取
        if self.cache:
            cached_data = self.cache.get_cached_dividends(symbol)
            if cached_data is not None and not cached_data.empty:
                logger.debug(f"从缓存获取股息数据: {symbol}, {len(cached_data)} 条记录")
                return cached_data

        try:
            import akshare as ak

            code = symbol.split('.')[0]
            logger.debug(f"获取股息数据: {symbol} -> code: {code}")

            result_data = None

            # Method 1: 优先使用工作正常的 AKShare history dividend detail (WORKING!)
            try:
                await asyncio.sleep(0.05)  # Brief delay to avoid rate limiting
                dividend_data = ak.stock_history_dividend_detail(symbol=code)
                if not dividend_data.empty:
                    logger.debug(f"股票 {symbol} 获取到 {len(dividend_data)} 条股息记录 (history_detail)")
                    result_data = self._process_history_detail_dividend_data(symbol, dividend_data)
            except Exception as e:
                logger.debug(f"history_detail source failed for {symbol}: {e}")

            # Method 2: 仅在AKShare失败时尝试cninfo（避免大量999 None错误）
            if result_data is None or result_data.empty:
                try:
                    await asyncio.sleep(0.1)  # 避免频率限制
                    dividend_data = ak.stock_dividend_cninfo(symbol=code)
                    if not dividend_data.empty:
                        logger.debug(f"股票 {symbol} 获取到 {len(dividend_data)} 条股息记录 (cninfo)")
                        result_data = self._process_dividend_data(symbol, dividend_data)
                except Exception as e:
                    logger.debug(f"cninfo source failed for {symbol}: {e}")

            # 如果获取到数据，进行缓存
            if result_data is not None and not result_data.empty:
                if self.cache:
                    self.cache.cache_dividends(symbol, result_data)
                logger.debug(f"获取并缓存股息数据: {symbol}, {len(result_data)} 条记录")
                return result_data
            else:
                logger.debug(f"股票 {symbol} 所有股息数据源均失败")
                return pd.DataFrame()

        except Exception as e:
            logger.warning(f"Failed to fetch dividend data for {symbol}: {str(e)}")
            return pd.DataFrame()

    def _process_dividend_data(self, symbol: str, dividend_data: pd.DataFrame) -> pd.DataFrame:
        """Process dividend data from cninfo source."""
        import logging
        import re
        logger = logging.getLogger(__name__)

        try:
            # Map AKShare columns to our expected format
            mapped_data = pd.DataFrame()
            mapped_data['symbol'] = [symbol] * len(dividend_data)

            # Extract year from report date
            years = []
            for report_time in dividend_data['报告时间']:
                if pd.isna(report_time):
                    years.append(0)
                elif isinstance(report_time, str):
                    # Handle formats like "1998半年报", "2000年报"
                    try:
                        year_match = re.search(r'(\d{4})', report_time)
                        years.append(int(year_match.group(1)) if year_match else 0)
                    except Exception:
                        years.append(0)
                else:
                    try:
                        years.append(pd.to_datetime(report_time).year)
                    except Exception:
                        years.append(0)
            mapped_data['year'] = years

            # Extract cash dividend from 派息比例
            cash_dividends = []
            for ratio in dividend_data['派息比例']:
                if pd.isna(ratio):
                    cash_dividends.append(0.0)
                else:
                    # AKShare returns dividend per 10 shares, so divide by 10
                    cash_dividends.append(float(ratio) / 10.0)

            mapped_data['cash_dividend'] = cash_dividends

            # Extract stock dividend from 送股比例 and 转增比例
            stock_dividends = []
            for send_ratio, bonus_ratio in zip(dividend_data['送股比例'], dividend_data['转增比例']):
                total_stock_dividend = 0.0

                for ratio in [send_ratio, bonus_ratio]:
                    if pd.notna(ratio) and isinstance(ratio, (int, float)):
                        # AKShare returns ratio per 10 shares, so divide by 10
                        total_stock_dividend += float(ratio) / 10.0
                    elif pd.notna(ratio) and isinstance(ratio, str):
                        try:
                            match = re.search(r'(\d+\.?\d*)', ratio)
                            if match:
                                total_stock_dividend += float(match.group(1)) / 10.0
                        except Exception:
                            pass

                stock_dividends.append(total_stock_dividend)

            mapped_data['stock_dividend'] = stock_dividends
            mapped_data['is_annual_report'] = dividend_data['分红类型'].str.contains('年度', na=False)

            # Convert dates
            mapped_data['record_date'] = pd.to_datetime(dividend_data['股权登记日'], errors='coerce')
            mapped_data['ex_dividend_date'] = pd.to_datetime(dividend_data['除权日'], errors='coerce')
            mapped_data['payment_date'] = pd.to_datetime(dividend_data['派息日'], errors='coerce')

            return mapped_data

        except Exception as e:
            logger.error(f"Error processing dividend data for {symbol}: {e}")
            return pd.DataFrame()

    def _process_sina_dividend_data(self, symbol: str, dividend_data: pd.DataFrame) -> pd.DataFrame:
        """Process dividend data from sina source."""
        import logging
        logger = logging.getLogger(__name__)

        try:
            # Sina data format may be different, adapt accordingly
            mapped_data = pd.DataFrame()
            mapped_data['symbol'] = [symbol] * len(dividend_data)

            # Basic processing - adjust based on actual Sina data format
            if '分红年度' in dividend_data.columns:
                mapped_data['year'] = pd.to_numeric(dividend_data['分红年度'], errors='coerce').fillna(0).astype(int)
            else:
                mapped_data['year'] = [2023] * len(dividend_data)  # Default year

            if '每股派息' in dividend_data.columns:
                mapped_data['cash_dividend'] = pd.to_numeric(dividend_data['每股派息'], errors='coerce').fillna(0.0)
            else:
                mapped_data['cash_dividend'] = [0.0] * len(dividend_data)

            mapped_data['stock_dividend'] = [0.0] * len(dividend_data)
            mapped_data['is_annual_report'] = [True] * len(dividend_data)

            # Add placeholder dates
            mapped_data['record_date'] = pd.NaT
            mapped_data['ex_dividend_date'] = pd.NaT
            mapped_data['payment_date'] = pd.NaT

            return mapped_data

        except Exception as e:
            logger.error(f"Error processing sina dividend data for {symbol}: {e}")
            return pd.DataFrame()

    def _process_em_dividend_data(self, symbol: str, dividend_data: pd.DataFrame) -> pd.DataFrame:
        """Process dividend data from eastmoney source."""
        import logging
        logger = logging.getLogger(__name__)

        try:
            # Eastmoney data format processing
            mapped_data = pd.DataFrame()
            mapped_data['symbol'] = [symbol] * len(dividend_data)

            # Basic processing - adjust based on actual Eastmoney data format
            if '分红年度' in dividend_data.columns:
                mapped_data['year'] = pd.to_numeric(dividend_data['分红年度'], errors='coerce').fillna(0).astype(int)
            else:
                mapped_data['year'] = [2023] * len(dividend_data)

            if '每股派息' in dividend_data.columns:
                mapped_data['cash_dividend'] = pd.to_numeric(dividend_data['每股派息'], errors='coerce').fillna(0.0)
            elif '派息比例' in dividend_data.columns:
                mapped_data['cash_dividend'] = pd.to_numeric(dividend_data['派息比例'], errors='coerce').fillna(0.0)
            else:
                mapped_data['cash_dividend'] = [0.0] * len(dividend_data)

            mapped_data['stock_dividend'] = [0.0] * len(dividend_data)
            mapped_data['is_annual_report'] = [True] * len(dividend_data)

            # Add placeholder dates
            mapped_data['record_date'] = pd.NaT
            mapped_data['ex_dividend_date'] = pd.NaT
            mapped_data['payment_date'] = pd.NaT

            return mapped_data

        except Exception as e:
            logger.error(f"Error processing eastmoney dividend data for {symbol}: {e}")
            return pd.DataFrame()

    
    def _process_history_detail_dividend_data(self, symbol: str, dividend_data: pd.DataFrame) -> pd.DataFrame:
        """Process dividend data from AKShare history detail source (WORKING!)."""
        import logging
        import pandas as pd
        from datetime import datetime
        logger = logging.getLogger(__name__)

        try:
            # Map AKShare columns to our expected format
            mapped_data = pd.DataFrame()
            mapped_data['symbol'] = [symbol] * len(dividend_data)

            # Extract year from announcement date
            years = []
            for announce_date in dividend_data['公告日期']:
                if pd.isna(announce_date):
                    years.append(0)
                else:
                    try:
                        # Handle date format like "2025-11-06"
                        if isinstance(announce_date, str):
                            year = int(announce_date.split('-')[0])
                        else:
                            year = announce_date.year
                        years.append(year)
                    except Exception:
                        years.append(0)
            mapped_data['year'] = years

            # Extract cash dividend from 派息 (already in correct format per 10 shares)
            cash_dividends = []
            for amount in dividend_data['派息']:
                if pd.isna(amount):
                    cash_dividends.append(0.0)
                else:
                    # AKShare returns dividend per 10 shares, so divide by 10
                    try:
                        cash_dividends.append(float(amount) / 10.0)
                    except (ValueError, TypeError):
                        cash_dividends.append(0.0)

            mapped_data['cash_dividend'] = cash_dividends

            # Extract stock dividend from 送股 and 转增
            stock_dividends = []
            for send_stock, bonus_stock in zip(dividend_data['送股'], dividend_data['转增']):
                total_stock_dividend = 0.0

                # Process 送股
                if pd.notna(send_stock):
                    try:
                        if isinstance(send_stock, (int, float)):
                            total_stock_dividend += float(send_stock) / 10.0
                        elif isinstance(send_stock, str):
                            # Handle cases like "0.0" or "0"
                            stock_float = float(send_stock)
                            total_stock_dividend += stock_float / 10.0
                    except (ValueError, TypeError):
                        pass

                # Process 转增
                if pd.notna(bonus_stock):
                    try:
                        if isinstance(bonus_stock, (int, float)):
                            total_stock_dividend += float(bonus_stock) / 10.0
                        elif isinstance(bonus_stock, str):
                            # Handle cases like "0.0" or "0"
                            bonus_float = float(bonus_stock)
                            total_stock_dividend += bonus_float / 10.0
                    except (ValueError, TypeError):
                        pass

                stock_dividends.append(total_stock_dividend)

            mapped_data['stock_dividend'] = stock_dividends

            # Mark annual reports (assume all are annual unless quarterly pattern detected)
            # For simplicity, mark records from Q4 (Oct-Dec) as annual reports
            is_annual = []
            for i, year in enumerate(years):
                # Simple heuristic: assume latest record each year is annual report
                is_annual.append(True)  # Default to annual report

            mapped_data['is_annual_report'] = is_annual

            # Convert dates (handle Chinese date formats)
            mapped_data['record_date'] = pd.to_datetime(dividend_data['股权登记日'], errors='coerce')
            mapped_data['ex_dividend_date'] = pd.to_datetime(dividend_data['除权除息日'], errors='coerce')
            mapped_data['payment_date'] = pd.to_datetime(dividend_data['红股上市日'], errors='coerce')

            logger.debug(f"成功处理 {symbol} 的历史详细股息数据: {len(mapped_data)} 条记录")
            return mapped_data

        except Exception as e:
            logger.error(f"Error processing history detail dividend data for {symbol}: {e}")
            return pd.DataFrame()

    async def fetch_price_data(
        self,
        symbol: str,
        start_date: date,
        end_date: date
    ) -> pd.DataFrame:
        """Fetch price data using AKShare."""
        try:
            import akshare as ak

            code = symbol.split('.')[0]
            start_str = start_date.strftime('%Y%m%d')
            end_str = end_date.strftime('%Y%m%d')

            # Fetch daily price data
            price_data = ak.stock_zh_a_hist(
                symbol=code,
                period="daily",
                start_date=start_str,
                end_date=end_str
            )

            if price_data.empty:
                return pd.DataFrame()

            # Add symbol column
            price_data['symbol'] = symbol
            return price_data

        except Exception as e:
            raise DataFetchError(f"Failed to fetch price data for {symbol}: {str(e)}")

    async def test_connection(self) -> bool:
        """Test AKShare connection."""
        if self._connection_tested:
            return True

        try:
            import akshare as ak
            # Try to fetch a small amount of data
            test_data = ak.stock_info_a_code_name()
            self._connection_tested = not test_data.empty
            return self._connection_tested
        except Exception:
            self._connection_tested = False
            return False

    def get_strategy_name(self) -> str:
        """Get strategy name."""
        return "AKShare"

    def get_cache_stats(self) -> Optional[Dict[str, Any]]:
        """获取缓存统计信息"""
        if self.cache:
            return self.cache.get_cache_stats()
        return None

    def clear_cache(self, pattern: str = None):
        """清理缓存"""
        if self.cache:
            self.cache.clear_cache(pattern)

    def set_cache_ttl(self, hours: int):
        """设置缓存过期时间"""
        if self.cache:
            self.cache.default_ttl = timedelta(hours=hours)


class MockStrategy(DataFetchStrategy):
    """Mock data fetch strategy for testing."""

    def __init__(self):
        """Initialize mock strategy with sample data."""
        self.mock_stocks = pd.DataFrame([
            {'code': '000001', 'name': '平安银行', 'symbol': '000001.SZ'},
            {'code': '000002', 'name': '万科A', 'symbol': '000002.SZ'},
            {'code': '600036', 'name': '招商银行', 'symbol': '600036.SH'},
        ])

        self.mock_dividends = {
            '000001.SZ': pd.DataFrame([
                {'symbol': '000001.SZ', 'year': 2024, 'cash_dividend': 2.0, 'is_annual_report': True},
                {'symbol': '000001.SZ', 'year': 2023, 'cash_dividend': 1.8, 'is_annual_report': True},
            ])
        }

    async def fetch_all_stocks(self) -> pd.DataFrame:
        """Return mock stock list."""
        return self.mock_stocks.copy()

    async def fetch_stock_basic_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Return mock stock info."""
        stock = self.mock_stocks[self.mock_stocks['symbol'] == symbol]
        if stock.empty:
            return None
        return stock.iloc[0].to_dict()

    async def fetch_dividend_data(self, symbol: str) -> pd.DataFrame:
        """Return mock dividend data."""
        return self.mock_dividends.get(symbol, pd.DataFrame()).copy()

    async def fetch_price_data(
        self,
        symbol: str,
        start_date: date,
        end_date: date
    ) -> pd.DataFrame:
        """Return mock price data."""
        import numpy as np

        # Generate simple mock price data
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        prices = np.random.uniform(10, 20, len(date_range))

        price_df = pd.DataFrame({
            'date': date_range,
            'symbol': symbol,
            'close': prices,
            'open': prices * 0.98,
            'high': prices * 1.02,
            'low': prices * 0.96,
            'volume': np.random.randint(1000000, 5000000, len(date_range))
        })

        return price_df

    async def test_connection(self) -> bool:
        """Mock connection test always succeeds."""
        return True

    def get_strategy_name(self) -> str:
        """Get strategy name."""
        return "Mock"


class MultiSourceStrategy(DataFetchStrategy):
    """Multi-source data fetch strategy with fallback."""

    def __init__(self, strategies: List[DataFetchStrategy]):
        """Initialize with multiple strategies in priority order."""
        self.strategies = strategies
        self._primary_strategy_index = 0

    async def fetch_all_stocks(self) -> pd.DataFrame:
        """Fetch stocks using the first available strategy."""
        for i, strategy in enumerate(self.strategies):
            try:
                if await strategy.test_connection():
                    self._primary_strategy_index = i
                    return await strategy.fetch_all_stocks()
            except Exception:
                continue
        raise DataFetchError("All data sources are unavailable")

    async def fetch_stock_basic_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch stock info using available strategies."""
        for i, strategy in enumerate(self.strategies):
            try:
                if await strategy.test_connection():
                    result = await strategy.fetch_stock_basic_info(symbol)
                    if result:
                        return result
            except Exception:
                continue
        return None

    async def fetch_dividend_data(self, symbol: str) -> pd.DataFrame:
        """Fetch dividend data using available strategies."""
        for strategy in self.strategies:
            try:
                if await strategy.test_connection():
                    result = await strategy.fetch_dividend_data(symbol)
                    if not result.empty:
                        return result
            except Exception:
                continue
        return pd.DataFrame()

    async def fetch_price_data(
        self,
        symbol: str,
        start_date: date,
        end_date: date
    ) -> pd.DataFrame:
        """Fetch price data using available strategies."""
        for strategy in self.strategies:
            try:
                if await strategy.test_connection():
                    result = await strategy.fetch_price_data(symbol, start_date, end_date)
                    if not result.empty:
                        return result
            except Exception:
                continue
        return pd.DataFrame()

    async def test_connection(self) -> bool:
        """Test if any strategy is available."""
        for strategy in self.strategies:
            try:
                if await strategy.test_connection():
                    return True
            except Exception:
                continue
        return False

    def get_strategy_name(self) -> str:
        """Get strategy name."""
        if self.strategies:
            return f"MultiSource(Primary: {self.strategies[self._primary_strategy_index].get_strategy_name()})"
        return "MultiSource(Empty)"


class DataFetchContext:
    """Context class for using data fetch strategies."""

    def __init__(self, strategy: DataFetchStrategy):
        """Initialize with a strategy."""
        self._strategy = strategy

    def set_strategy(self, strategy: DataFetchStrategy) -> None:
        """Change the current strategy."""
        self._strategy = strategy

    async def fetch_all_stocks(self) -> pd.DataFrame:
        """Delegate to strategy."""
        return await self._strategy.fetch_all_stocks()

    async def fetch_stock_basic_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Delegate to strategy."""
        return await self._strategy.fetch_stock_basic_info(symbol)

    async def fetch_dividend_data(self, symbol: str) -> pd.DataFrame:
        """Delegate to strategy."""
        return await self._strategy.fetch_dividend_data(symbol)

    async def fetch_price_data(
        self,
        symbol: str,
        start_date: date,
        end_date: date
    ) -> pd.DataFrame:
        """Delegate to strategy."""
        return await self._strategy.fetch_price_data(symbol, start_date, end_date)

    async def test_connection(self) -> bool:
        """Delegate to strategy."""
        return await self._strategy.test_connection()

    def get_current_strategy_name(self) -> str:
        """Get current strategy name."""
        return self._strategy.get_strategy_name()