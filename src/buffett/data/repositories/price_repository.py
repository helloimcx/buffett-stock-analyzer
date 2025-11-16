"""
Price repository implementation.

This module implements the IPriceRepository interface for managing price data
access operations following the Repository pattern.
"""

from typing import List, Optional, Dict
import pandas as pd
import asyncio
from datetime import datetime, date, timedelta
from loguru import logger

from ...interfaces.repositories import IPriceRepository
from ...models.stock import PriceData
from ...exceptions.data import DataFetchError, ValidationError


class PriceRepository(IPriceRepository):
    """Concrete implementation of IPriceRepository."""

    def __init__(self, data_source: pd.DataFrame = None):
        """Initialize repository with optional initial data."""
        self._price_data: Dict[str, pd.DataFrame] = {}
        if data_source is not None:
            # If data_source is provided, load it
            self._load_initial_data(data_source)

    def _load_initial_data(self, data_source: pd.DataFrame):
        """Load initial price data from DataFrame."""
        try:
            if not data_source.empty and 'symbol' in data_source.columns:
                for symbol in data_source['symbol'].unique():
                    symbol_data = data_source[data_source['symbol'] == symbol].copy()
                    self._price_data[symbol] = symbol_data
        except Exception as e:
            logger.warning(f"Failed to load initial price data: {e}")

    async def get_price_data(
        self,
        symbol: str,
        start_date: date,
        end_date: date
    ) -> pd.DataFrame:
        """Get price data for a stock within date range."""
        try:
            if symbol not in self._price_data:
                return pd.DataFrame()

            df = self._price_data[symbol].copy()
            if df.empty:
                return pd.DataFrame()

            # Convert date column if it exists
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                # Filter by date range
                mask = (df['date'] >= pd.Timestamp(start_date)) & (df['date'] <= pd.Timestamp(end_date))
                df = df[mask]

            return df

        except Exception as e:
            logger.error(f"Failed to get price data for {symbol}: {e}")
            raise DataFetchError(f"Failed to retrieve price data for {symbol}: {str(e)}")

    async def get_historical_prices(
        self,
        symbol: str,
        years: int = 5
    ) -> pd.DataFrame:
        """Get historical price data for a stock for specified number of years."""
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=years * 365)

            return await self.get_price_data(symbol, start_date, end_date)

        except Exception as e:
            logger.error(f"Failed to get historical prices for {symbol}: {e}")
            # Return empty DataFrame instead of raising to allow screening to continue
            return pd.DataFrame()

    async def get_latest_price(self, symbol: str) -> Optional[float]:
        """Get the latest price for a stock."""
        try:
            if symbol not in self._price_data:
                return None

            df = self._price_data[symbol]
            if df.empty:
                return None

            # Get the most recent price
            if 'close' in df.columns:
                if 'date' in df.columns:
                    df_sorted = df.sort_values('date', ascending=False)
                    return df_sorted.iloc[0]['close']
                else:
                    # If no date column, just get the last close price
                    return df.iloc[-1]['close']

            return None

        except Exception as e:
            logger.error(f"Failed to get latest price for {symbol}: {e}")
            return None

    async def save_price_data(self, symbol: str, price_data: pd.DataFrame) -> None:
        """Save price data for a stock."""
        try:
            if price_data.empty:
                return

            # Ensure the DataFrame has the required columns
            required_columns = ['date', 'close']
            if not all(col in price_data.columns for col in required_columns):
                raise ValidationError(f"Price data missing required columns: {required_columns}")

            # Store the data
            self._price_data[symbol] = price_data.copy()

        except Exception as e:
            logger.error(f"Failed to save price data for {symbol}: {e}")
            raise DataFetchError(f"Failed to save price data for {symbol}: {str(e)}")

    async def calculate_moving_averages(
        self,
        symbol: str,
        periods: List[int]
    ) -> Dict[int, float]:
        """Calculate moving averages for a stock."""
        try:
            if symbol not in self._price_data:
                return {}

            df = self._price_data[symbol]
            if df.empty or 'close' not in df.columns:
                return {}

            moving_averages = {}
            for period in periods:
                try:
                    if len(df) >= period:
                        ma = df['close'].rolling(window=period).mean().iloc[-1]
                        moving_averages[period] = float(ma)
                except Exception as e:
                    logger.warning(f"Failed to calculate MA{period} for {symbol}: {e}")
                    continue

            return moving_averages

        except Exception as e:
            logger.error(f"Failed to calculate moving averages for {symbol}: {e}")
            return {}

    async def get_stock_info(self, symbol: str) -> Optional[Dict]:
        """Get basic stock info for price data purposes."""
        try:
            if symbol not in self._price_data:
                return None

            df = self._price_data[symbol]
            if df.empty:
                return None

            # Extract basic info from price data
            info = {
                'symbol': symbol,
                'latest_price': await self.get_latest_price(symbol),
                'data_points': len(df),
                'has_volume': 'volume' in df.columns,
                'has_high_low': 'high' in df.columns and 'low' in df.columns
            }

            # Calculate some basic statistics if we have enough data
            if 'close' in df.columns and len(df) > 1:
                info['price_change'] = df['close'].iloc[-1] - df['close'].iloc[-2]
                info['price_change_pct'] = (info['price_change'] / df['close'].iloc[-2]) * 100

            return info

        except Exception as e:
            logger.error(f"Failed to get stock info for {symbol}: {e}")
            return None