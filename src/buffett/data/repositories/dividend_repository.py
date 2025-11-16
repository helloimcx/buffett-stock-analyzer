"""
Dividend repository implementation.

This module implements the IDividendRepository interface for managing dividend data
access operations following the Repository pattern.
"""

from typing import List, Optional, Dict
import pandas as pd
import numpy as np
from datetime import datetime, date

from ...interfaces.repositories import IDividendRepository
from ...models.stock import DividendData
from ...exceptions.data import DataFetchError, ValidationError


class DividendRepository(IDividendRepository):
    """Concrete implementation of IDividendRepository."""

    def __init__(self, data_source: pd.DataFrame = None):
        """Initialize repository with optional initial data."""
        self._dividends_df = data_source if data_source is not None else pd.DataFrame()
        self._dividends_cache: Dict[str, List[DividendData]] = {}

    async def get_dividend_history(
        self,
        symbol: str,
        start_year: int = None,
        end_year: int = None
    ) -> List[DividendData]:
        """Get dividend history for a stock."""
        try:
            # Check cache first
            cache_key = f"{symbol}_{start_year}_{end_year}"
            if cache_key in self._dividends_cache:
                return self._dividends_cache[cache_key]

            # Filter dividends for the symbol
            mask = self._dividends_df['symbol'] == symbol
            symbol_dividends_df = self._dividends_df[mask]

            if symbol_dividends_df.empty:
                return []

            # Apply year filters if specified
            if start_year is not None:
                mask = symbol_dividends_df['year'] >= start_year
                symbol_dividends_df = symbol_dividends_df[mask]

            if end_year is not None:
                mask = symbol_dividends_df['year'] <= end_year
                symbol_dividends_df = symbol_dividends_df[mask]

            # Convert to DividendData objects
            dividends = []
            for _, row in symbol_dividends_df.iterrows():
                try:
                    dividend = DividendData(
                        symbol=row.get('symbol', ''),
                        year=int(row.get('year', 0)),
                        cash_dividend=float(row.get('cash_dividend', 0)),
                        stock_dividend=float(row.get('stock_dividend', 0)),
                        is_annual_report=bool(row.get('is_annual_report', True)),
                        record_date=pd.to_datetime(row['record_date']).to_pydatetime() if pd.notna(row.get('record_date')) else None,
                        ex_dividend_date=pd.to_datetime(row['ex_dividend_date']).to_pydatetime() if pd.notna(row.get('ex_dividend_date')) else None,
                        payment_date=pd.to_datetime(row['payment_date']).to_pydatetime() if pd.notna(row.get('payment_date')) else None
                    )
                    dividends.append(dividend)
                except Exception:
                    continue

            # Sort by year (most recent first)
            dividends.sort(key=lambda x: x.year, reverse=True)

            # Cache the result
            self._dividends_cache[cache_key] = dividends
            return dividends

        except Exception as e:
            raise DataFetchError(f"Failed to retrieve dividend history for {symbol}: {str(e)}")

    async def save_dividend_data(self, dividend_data: DividendData) -> None:
        """Save dividend data."""
        try:
            if not isinstance(dividend_data, DividendData):
                raise ValidationError("Invalid dividend data provided")

            # Check if dividend record already exists
            mask = (
                (self._dividends_df['symbol'] == dividend_data.symbol) &
                (self._dividends_df['year'] == dividend_data.year)
            )
            existing_index = self._dividends_df[mask].index

            dividend_record = {
                'symbol': dividend_data.symbol,
                'year': dividend_data.year,
                'cash_dividend': dividend_data.cash_dividend,
                'stock_dividend': dividend_data.stock_dividend,
                'is_annual_report': dividend_data.is_annual_report,
                'record_date': dividend_data.record_date,
                'ex_dividend_date': dividend_data.ex_dividend_date,
                'payment_date': dividend_data.payment_date,
                'updated_at': datetime.now()
            }

            if len(existing_index) > 0:
                # Update existing record
                self._dividends_df.loc[existing_index[0]] = dividend_record
            else:
                # Add new record
                new_row = pd.DataFrame([dividend_record])
                self._dividends_df = pd.concat([self._dividends_df, new_row], ignore_index=True)

            # Clear relevant cache entries
            keys_to_remove = [key for key in self._dividends_cache.keys() if key.startswith(dividend_data.symbol)]
            for key in keys_to_remove:
                del self._dividends_cache[key]

        except Exception as e:
            raise DataFetchError(f"Failed to save dividend data for {dividend_data.symbol}: {str(e)}")

    async def get_stocks_with_consistent_dividends(
        self,
        min_years: int = 3,
        min_yield: float = 0.0
    ) -> List[str]:
        """Get stocks with consistent dividend payments."""
        try:
            # Group by symbol and count consecutive dividend years
            dividend_consistency = {}

            for symbol in self._dividends_df['symbol'].unique():
                symbol_dividends = self._dividends_df[
                    self._dividends_df['symbol'] == symbol
                ].sort_values('year', ascending=False)

                # Get annual report dividends only
                annual_dividends = symbol_dividends[
                    symbol_dividends['is_annual_report'] == True
                ]

                if len(annual_dividends) >= min_years:
                    # Check minimum yield
                    recent_dividends = annual_dividends.head(min_years)
                    avg_yield = recent_dividends['cash_dividend'].mean()

                    if avg_yield >= min_yield:
                        dividend_consistency[symbol] = len(annual_dividends)

            # Return symbols sorted by consistency (most consistent first)
            consistent_stocks = sorted(
                dividend_consistency.keys(),
                key=lambda x: dividend_consistency[x],
                reverse=True
            )

            return consistent_stocks

        except Exception as e:
            raise DataFetchError(f"Failed to get stocks with consistent dividends: {str(e)}")

    async def get_latest_dividend_yield(self, symbol: str) -> Optional[float]:
        """Get the latest dividend yield for a stock."""
        try:
            # Get the most recent dividend data
            dividends = await self.get_dividend_history(symbol, start_year=date.today().year - 1)

            if not dividends:
                return None

            # Find the most recent annual report dividend
            for dividend in dividends:
                if dividend.is_annual_report and dividend.cash_dividend > 0:
                    return dividend.cash_dividend

            return None

        except Exception as e:
            raise DataFetchError(f"Failed to get latest dividend yield for {symbol}: {str(e)}")

    def load_from_dataframe(self, df: pd.DataFrame) -> None:
        """Load dividends from a DataFrame."""
        try:
            # Validate required columns
            required_columns = ['symbol', 'year', 'cash_dividend']
            missing_columns = [col for col in required_columns if col not in df.columns]

            if missing_columns:
                raise ValidationError(f"Missing required columns: {missing_columns}")

            # Copy data to internal DataFrame
            self._dividends_df = df.copy()

            # Clear cache
            self._dividends_cache.clear()

        except Exception as e:
            raise DataFetchError(f"Failed to load dividends from DataFrame: {str(e)}")

    def get_dividend_statistics(self, symbol: str) -> Dict:
        """Get dividend statistics for a stock."""
        try:
            symbol_dividends = self._dividends_df[
                self._dividends_df['symbol'] == symbol
            ]

            if symbol_dividends.empty:
                return {}

            annual_dividends = symbol_dividends[
                symbol_dividends['is_annual_report'] == True
            ]

            stats = {
                'total_dividends': len(symbol_dividends),
                'annual_dividends': len(annual_dividends),
                'avg_cash_dividend': float(annual_dividends['cash_dividend'].mean()) if not annual_dividends.empty else 0,
                'max_cash_dividend': float(annual_dividends['cash_dividend'].max()) if not annual_dividends.empty else 0,
                'min_cash_dividend': float(annual_dividends['cash_dividend'].min()) if not annual_dividends.empty else 0,
                'dividend_growth': self._calculate_dividend_growth(annual_dividends),
                'consistency_years': len(annual_dividends)
            }

            return stats

        except Exception as e:
            raise DataFetchError(f"Failed to calculate dividend statistics for {symbol}: {str(e)}")

    def _calculate_dividend_growth(self, annual_dividends: pd.DataFrame) -> float:
        """Calculate dividend growth rate."""
        try:
            if len(annual_dividends) < 2:
                return 0.0

            # Sort by year (oldest first)
            sorted_dividends = annual_dividends.sort_values('year')
            values = sorted_dividends['cash_dividend'].values

            # Calculate compound annual growth rate (CAGR)
            years = len(values) - 1
            if years <= 0 or values[0] <= 0:
                return 0.0

            cagr = ((values[-1] / values[0]) ** (1/years)) - 1
            return float(cagr * 100)  # Return as percentage

        except Exception:
            return 0.0

    def clear_cache(self) -> None:
        """Clear the internal cache."""
        self._dividends_cache.clear()

    def get_dataframe(self) -> pd.DataFrame:
        """Get internal DataFrame representation."""
        return self._dividends_df.copy()