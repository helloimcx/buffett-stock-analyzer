"""
Stock repository implementation.

This module implements the IStockRepository interface for managing stock data
access operations following the Repository pattern.
"""

from typing import List, Optional, Dict, Any
import pandas as pd
import asyncio
from datetime import datetime

from ...interfaces.repositories import IStockRepository
from ...models.stock import Stock, StockInfo
from ...exceptions.data import DataFetchError, ValidationError


class StockRepository(IStockRepository):
    """Concrete implementation of IStockRepository."""

    def __init__(self, data_source: pd.DataFrame = None, strategy=None):
        """Initialize repository with optional initial data."""
        self._stocks_df = data_source if data_source is not None else pd.DataFrame()
        self._stocks_cache: dict = {}
        self._strategy = strategy  # Shared AKShare strategy for caching

    async def get_all_stocks(self) -> List[Stock]:
        """Get all stocks from the repository."""
        try:
            if self._stocks_df.empty:
                return []

            # Convert DataFrame to Stock objects
            stocks = []
            for _, row in self._stocks_df.iterrows():
                try:
                    stock = Stock(
                        symbol=row.get('symbol', ''),
                        name=row.get('name', ''),
                        code=row.get('code', row.get('symbol', '').split('.')[0] if '.' in str(row.get('symbol', '')) else '')
                        # Let model validator extract market from symbol
                    )
                    stocks.append(stock)
                except Exception as e:
                    # Log error but continue processing other stocks
                    continue

            return stocks

        except Exception as e:
            raise DataFetchError(f"Failed to retrieve stocks: {str(e)}")

    async def get_stock_by_symbol(self, symbol: str) -> Optional[Stock]:
        """Get a specific stock by symbol."""
        try:
            # Check cache first
            if symbol in self._stocks_cache:
                return self._stocks_cache[symbol]

            # Search in DataFrame
            mask = self._stocks_df['symbol'] == symbol
            matching_rows = self._stocks_df[mask]

            if matching_rows.empty:
                return None

            # Convert first match to Stock object
            row = matching_rows.iloc[0]

            # Handle market field conversion to valid Market enum
            market_value = row.get('market', '')
            if not market_value or market_value == '':
                # Extract market from symbol if not provided
                if '.' in symbol:
                    market_suffix = symbol.split('.')[1].upper()
                    try:
                        market_value = market_suffix
                    except ValueError:
                        market_value = 'UNKNOWN'
                else:
                    market_value = 'UNKNOWN'

            stock = Stock(
                symbol=row.get('symbol', ''),
                name=row.get('name', ''),
                code=row.get('code', symbol.split('.')[0]),
                market=market_value
            )

            # Cache the result
            self._stocks_cache[symbol] = stock
            return stock

        except Exception as e:
            raise DataFetchError(f"Failed to retrieve stock {symbol}: {str(e)}")

    async def get_stock_info(self, symbol: str) -> Optional[StockInfo]:
        """Get detailed stock information by symbol."""
        import logging
        logger = logging.getLogger(__name__)

        try:
            # Get basic stock first
            stock = await self.get_stock_by_symbol(symbol)
            if not stock:
                logger.debug(f"Stock {symbol} not found in repository")
                return None

            # Try to get additional info from the DataFrame if available
            stock_data = None
            mask = self._stocks_df['symbol'] == symbol
            matching_rows = self._stocks_df[mask]

            if not matching_rows.empty:
                stock_data = matching_rows.iloc[0].to_dict()

            # Try to fetch detailed stock info dynamically if market_cap is not available
            detailed_data = await self._fetch_detailed_stock_info(symbol, self._strategy)
            if detailed_data:
                # Merge the detailed data with existing stock data
                if stock_data is None:
                    stock_data = {}
                stock_data.update(detailed_data)

            # Create StockInfo with available data
            # Some fields might be None if not available in the basic data
            stock_info = StockInfo(
                symbol=stock.symbol,
                name=stock.name,
                industry=stock_data.get('industry') if stock_data and stock_data.get('industry') else '未知',
                market_cap=stock_data.get('market_cap') if stock_data and stock_data.get('market_cap') else None,
                total_assets=stock_data.get('total_assets') if stock_data and stock_data.get('total_assets') else None,
                total_liabilities=stock_data.get('total_liabilities') if stock_data and stock_data.get('total_liabilities') else None,
                current_price=stock_data.get('current_price') if stock_data and stock_data.get('current_price') else None,
                pe_ratio=stock_data.get('pe_ratio') if stock_data and stock_data.get('pe_ratio') else None,
                pb_ratio=stock_data.get('pb_ratio') if stock_data and stock_data.get('pb_ratio') else None,
                dividend_yield=stock_data.get('dividend_yield') if stock_data and stock_data.get('dividend_yield') else None,
                listing_date=stock_data.get('listing_date') if stock_data and stock_data.get('listing_date') else None
            )

            return stock_info

        except Exception as e:
            # Log the exception for debugging but don't raise it
            # This allows screening to continue even if detailed info is not available
            logger.debug(f"Error getting stock info for {symbol}: {str(e)}")
            return None

    async def _fetch_detailed_stock_info(self, symbol: str, strategy=None) -> Optional[Dict[str, Any]]:
        """Fetch detailed stock information dynamically using AKShare with multiple fallback methods."""
        import logging
        logger = logging.getLogger(__name__)

        # Try multiple approaches to get market cap data
        methods_to_try = []

        # Method 1: Use provided strategy
        if strategy is not None:
            methods_to_try.append(("shared_strategy", lambda: strategy.fetch_stock_basic_info(symbol)))

        # Method 2: Create new strategy
        from ...strategies.data_fetch_strategies import AKShareStrategy
        methods_to_try.append(("new_strategy", lambda: AKShareStrategy(cache_ttl_hours=24, enable_cache=True).fetch_stock_basic_info(symbol)))

        # Method 3: Direct AKShare with different parameters
        methods_to_try.append(("direct_akshare_full_symbol", lambda: self._direct_akshare_fetch(symbol, False)))
        methods_to_try.append(("direct_akshare_code_only", lambda: self._direct_akshare_fetch(symbol, True)))


        for method_name, fetch_method in methods_to_try:
            try:
                logger.debug(f"尝试方法 {method_name} 获取 {symbol} 市值")
                stock_info = await fetch_method()

                if stock_info and stock_info.get('market_cap'):
                    market_cap = stock_info['market_cap']

                    # 数据质量检查
                    if isinstance(market_cap, (int, float)) and market_cap > 0:
                        logger.debug(f"方法 {method_name} 成功获取 {symbol} 市值: {market_cap/100_000_000:.0f}亿")
                        return stock_info
                    else:
                        logger.debug(f"方法 {method_name} 获取的市值数据无效: {market_cap}")

            except Exception as e:
                logger.debug(f"方法 {method_name} 失败 {symbol}: {str(e)}")
                continue

        logger.debug(f"所有方法都无法获取 {symbol} 的市值数据")
        return None

    async def _direct_akshare_fetch(self, symbol: str, use_code_only: bool = False) -> Optional[Dict[str, Any]]:
        """Direct AKShare fetch with parameter control."""
        import logging
        import akshare as ak
        from datetime import datetime

        logger = logging.getLogger(__name__)

        try:
            if use_code_only:
                code = symbol.split('.')[0] if '.' in symbol else symbol
                info = ak.stock_individual_info_em(symbol=code)
            else:
                info = ak.stock_individual_info_em(symbol=symbol)

            if info is None or info.empty:
                return None

            info_dict = info.set_index('item')['value'].to_dict()

            # 字段映射
            field_mapping = {
                '总市值': 'market_cap',
                '流通市值': 'circulating_market_cap',
                '最新': 'current_price',
                '股票代码': 'code',
                '股票简称': 'name'
            }

            for chinese_field, english_field in field_mapping.items():
                if chinese_field in info_dict:
                    info_dict[english_field] = info_dict[chinese_field]

            info_dict['symbol'] = symbol
            info_dict['fetch_time'] = datetime.now().isoformat()

            # 处理市值数据
            if 'market_cap' in info_dict and isinstance(info_dict['market_cap'], str):
                try:
                    info_dict['market_cap'] = float(info_dict['market_cap'].replace(',', ''))
                except (ValueError, AttributeError):
                    pass

            return info_dict

        except Exception as e:
            logger.debug(f"直接AKShare获取失败 {symbol}: {str(e)}")
            return None

    
    async def get_stocks_by_market(self, market: str) -> List[Stock]:
        """Get all stocks from a specific market."""
        try:
            mask = self._stocks_df['market'] == market
            market_stocks_df = self._stocks_df[mask]

            if market_stocks_df.empty:
                return []

            stocks = []
            for _, row in market_stocks_df.iterrows():
                try:
                    stock = Stock(
                        symbol=row.get('symbol', ''),
                        name=row.get('name', ''),
                        code=row.get('code', ''),
                        market=row.get('market', '')
                    )
                    stocks.append(stock)
                except Exception:
                    continue

            return stocks

        except Exception as e:
            raise DataFetchError(f"Failed to retrieve stocks for market {market}: {str(e)}")

    async def get_stocks_by_industry(self, industry: str) -> List[Stock]:
        """Get all stocks from a specific industry."""
        try:
            # First, try to filter by industry column if it exists
            if 'industry' in self._stocks_df.columns:
                mask = self._stocks_df['industry'] == industry
                industry_stocks_df = self._stocks_df[mask]
            else:
                # If no industry column, we need to get stock info and filter
                industry_stocks_df = pd.DataFrame()

            if industry_stocks_df.empty:
                # Fallback: get all stocks and filter by industry info
                all_stocks = await self.get_all_stocks()
                stocks = []
                for stock in all_stocks:
                    stock_info = await self.get_stock_info(stock.symbol)
                    if stock_info and stock_info.industry == industry:
                        stocks.append(stock)
                return stocks

            stocks = []
            for _, row in industry_stocks_df.iterrows():
                try:
                    stock = Stock(
                        symbol=row.get('symbol', ''),
                        name=row.get('name', ''),
                        code=row.get('code', ''),
                        market=row.get('market', '')
                    )
                    stocks.append(stock)
                except Exception:
                    continue

            return stocks

        except Exception as e:
            raise DataFetchError(f"Failed to retrieve stocks for industry {industry}: {str(e)}")

    async def save_stock(self, stock: Stock) -> None:
        """Save a stock to the repository."""
        try:
            if not isinstance(stock, Stock):
                raise ValidationError("Invalid stock object provided")

            # Check if stock already exists
            mask = self._stocks_df['symbol'] == stock.symbol
            existing_index = self._stocks_df[mask].index

            stock_data = {
                'symbol': stock.symbol,
                'name': stock.name,
                'code': stock.code,
                'market': stock.market.value if hasattr(stock.market, 'value') else str(stock.market),
                'updated_at': datetime.now()
            }

            if len(existing_index) > 0:
                # Update existing stock
                self._stocks_df.loc[existing_index[0]] = stock_data
            else:
                # Add new stock
                new_row = pd.DataFrame([stock_data])
                self._stocks_df = pd.concat([self._stocks_df, new_row], ignore_index=True)

            # Update cache
            self._stocks_cache[stock.symbol] = stock

        except Exception as e:
            raise DataFetchError(f"Failed to save stock {stock.symbol}: {str(e)}")

    async def save_stocks(self, stocks: List[Stock]) -> None:
        """Save multiple stocks to the repository."""
        try:
            if not stocks:
                return

            # Validate all stocks first
            for stock in stocks:
                if not isinstance(stock, Stock):
                    raise ValidationError("Invalid stock object in list")

            # Process in batches to avoid memory issues
            batch_size = 100
            for i in range(0, len(stocks), batch_size):
                batch = stocks[i:i + batch_size]

                for stock in batch:
                    await self.save_stock(stock)

        except Exception as e:
            raise DataFetchError(f"Failed to save stocks: {str(e)}")

    def load_from_dataframe(self, df: pd.DataFrame) -> None:
        """Load stocks from a DataFrame."""
        try:
            # Validate required columns
            required_columns = ['symbol', 'name']
            missing_columns = [col for col in required_columns if col not in df.columns]

            if missing_columns:
                raise ValidationError(f"Missing required columns: {missing_columns}")

            # Copy data to internal DataFrame
            self._stocks_df = df.copy()

            # Clear cache
            self._stocks_cache.clear()

        except Exception as e:
            raise DataFetchError(f"Failed to load stocks from DataFrame: {str(e)}")

    def get_dataframe(self) -> pd.DataFrame:
        """Get internal DataFrame representation."""
        return self._stocks_df.copy()

    def clear_cache(self) -> None:
        """Clear the internal cache."""
        self._stocks_cache.clear()

    def get_cache_stats(self) -> dict:
        """Get cache statistics."""
        return {
            'cached_items': len(self._stocks_cache),
            'total_stocks': len(self._stocks_df)
        }