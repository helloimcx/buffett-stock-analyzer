"""
Trend Analyzer - 趋势分析器

实现四步投资策略的第三步：趋势分析
分析标准：
- 移动平均线分析（30/60周线）
- RSI技术指标分析
- 布林带分析
- 综合趋势评分
"""

import asyncio
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from loguru import logger

try:
    import talib
    TALIB_AVAILABLE = True
except ImportError:
    logger.warning("TA-Lib not available, using pandas-based calculations")
    TALIB_AVAILABLE = False

from ...models.stock import Stock
from ...models.screening import TrendResult, ValuationResult, ScreeningCriteria
from ...interfaces.repositories import IPriceRepository
from ...exceptions.screening import ScreeningError


class TrendAnalyzer:
    """趋势分析器 - 负责股票的技术趋势分析"""

    def __init__(self, price_repository: IPriceRepository):
        self.price_repo = price_repository

    async def analyze_stocks(
        self,
        valuation_results: List[ValuationResult],
        criteria: ScreeningCriteria
    ) -> List[TrendResult]:
        """
        对通过估值分析的股票进行趋势分析

        Args:
            valuation_results: 通过估值分析的股票列表
            criteria: 筛选条件

        Returns:
            趋势分析结果列表
        """
        logger.info(f"开始趋势分析，股票数量：{len(valuation_results)}")

        try:
            # 并发分析股票趋势
            analysis_tasks = []
            for result in valuation_results:
                task = self._analyze_single_stock(result, criteria)
                analysis_tasks.append(task)

            results = await asyncio.gather(*analysis_tasks, return_exceptions=True)

            # 处理结果和异常
            trend_results = []
            failed_count = 0

            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"股票 {valuation_results[i].symbol} 趋势分析失败: {result}")
                    failed_count += 1
                elif isinstance(result, TrendResult):
                    trend_results.append(result)

            # 按综合趋势评分排序
            trend_results.sort(key=lambda x: x.overall_trend_score, reverse=True)

            logger.info(f"趋势分析完成：成功 {len(trend_results)} 只，失败 {failed_count} 只")

            return trend_results

        except Exception as e:
            logger.error(f"趋势分析过程发生错误: {e}")
            raise ScreeningError(f"趋势分析失败: {e}") from e

    async def _analyze_single_stock(
        self,
        valuation_result: ValuationResult,
        criteria: ScreeningCriteria
    ) -> TrendResult:
        """分析单只股票的趋势"""
        try:
            symbol = valuation_result.symbol

            # 获取历史价格数据（需要足够的数据进行技术分析）
            price_data = await self.price_repo.get_historical_prices(
                symbol,
                years=max(2, criteria.ma_week_60 // 26)  # 确保有足够的数据
            )

            if price_data.empty or len(price_data) < 60:
                # 数据不足，返回默认结果
                return TrendResult(
                    symbol=symbol,
                    name=valuation_result.name,
                    passed=False,
                    overall_trend_score=0.0,
                    ma_score=0.0,
                    rsi_score=0.0,
                    bollinger_score=0.0,
                    current_price=0.0,
                    ma30_price=0.0,
                    ma60_price=0.0,
                    rsi_value=50.0,
                    bollinger_position="未知",
                    trend_direction="中性",
                    analysis_time=datetime.now()
                )

            # 计算技术指标
            ma_analysis = await self._analyze_moving_averages(price_data, criteria)
            rsi_analysis = await self._analyze_rsi(price_data, criteria)
            bollinger_analysis = await self._analyze_bollinger_bands(price_data, criteria)

            # 计算各项评分
            ma_score = self._calculate_ma_score(ma_analysis[0], criteria.ma_distance_threshold)
            rsi_score = self._calculate_rsi_score(rsi_analysis[1], criteria.rsi_oversold, criteria.rsi_overbought)
            bollinger_score = self._calculate_bollinger_score(bollinger_analysis[0])

            # 综合趋势评分
            overall_score = (
                ma_score * 0.4 +
                rsi_score * 0.3 +
                bollinger_score * 0.3
            )

            # 判断趋势方向
            trend_direction = self._determine_trend_direction(ma_analysis, rsi_analysis[1])

            # 判断是否通过趋势筛选
            trend_passed = (
                ma_score >= 60 and  # 移动平均线评分≥60
                rsi_score >= 50 and  # RSI评分≥50
                overall_score >= 60   # 综合评分≥60
            )

            return TrendResult(
                symbol=symbol,
                name=valuation_result.name,
                passed=trend_passed,
                overall_trend_score=round(overall_score, 2),
                ma_score=round(ma_score, 2),
                rsi_score=round(rsi_score, 2),
                bollinger_score=round(bollinger_score, 2),
                current_price=float(price_data['close'].iloc[-1]),
                ma30_price=ma_analysis[1] if ma_analysis[1] else 0.0,
                ma60_price=ma_analysis[2] if ma_analysis[2] else 0.0,
                rsi_value=round(rsi_analysis[1], 2) if rsi_analysis[1] else 50.0,
                bollinger_position=bollinger_analysis[1],
                trend_direction=trend_direction,
                analysis_time=datetime.now()
            )

        except Exception as e:
            logger.error(f"分析股票 {symbol} 趋势时发生错误: {e}")
            raise ScreeningError(f"趋势分析失败 {symbol}: {e}") from e

    async def _analyze_moving_averages(
        self,
        price_data: pd.DataFrame,
        criteria: ScreeningCriteria
    ) -> Tuple[bool, Optional[float], Optional[float]]:
        """分析移动平均线"""
        try:
            closing_prices = price_data['close'].values

            # 计算移动平均线
            if TALIB_AVAILABLE:
                ma30 = talib.SMA(closing_prices, timeperiod=criteria.ma_week_30)
                ma60 = talib.SMA(closing_prices, timeperiod=criteria.ma_week_60)
            else:
                ma30 = self._calculate_sma(closing_prices, criteria.ma_week_30)
                ma60 = self._calculate_sma(closing_prices, criteria.ma_week_60)

            current_price = closing_prices[-1]
            current_ma30 = ma30[-1] if not np.isnan(ma30[-1]) else None
            current_ma60 = ma60[-1] if not np.isnan(ma60[-1]) else None

            if current_ma30 is None or current_ma60 is None:
                return False, None, None

            # 分析移动平均线状态
            # 1. 价格在30周线上方
            price_above_ma30 = current_price > current_ma30

            # 2. 30周线在60周线上方（金叉）
            ma30_above_ma60 = current_ma30 > current_ma60

            # 3. 价格与移动平均线的距离
            ma30_distance = abs(current_price - current_ma30) / current_ma30 * 100

            # 4. 移动平均线趋势
            ma30_trend = self._calculate_ma_trend(ma30)

            # 综合判断
            passed = (
                price_above_ma30 and
                ma30_above_ma60 and
                ma30_distance <= criteria.ma_distance_threshold and
                ma30_trend > 0
            )

            return passed, current_ma30, current_ma60

        except Exception as e:
            logger.warning(f"计算移动平均线时发生错误: {e}")
            return False, None, None

    async def _analyze_rsi(
        self,
        price_data: pd.DataFrame,
        criteria: ScreeningCriteria
    ) -> Tuple[bool, Optional[float]]:
        """分析RSI指标"""
        try:
            closing_prices = price_data['close'].values

            # 计算RSI
            if TALIB_AVAILABLE:
                rsi_values = talib.RSI(closing_prices, timeperiod=criteria.rsi_period)
            else:
                rsi_values = self._calculate_rsi(closing_prices, criteria.rsi_period)

            current_rsi = rsi_values[-1] if not np.isnan(rsi_values[-1]) else None

            if current_rsi is None:
                return False, None

            # RSI分析
            # 1. RSI在合理范围内（不过度超买或超卖）
            in_good_range = criteria.rsi_oversold <= current_rsi <= criteria.rsi_overbought

            # 2. RSI超卖区域（买入机会）
            is_oversold = current_rsi < criteria.rsi_oversold

            # 3. RSI趋势
            rsi_trend = self._calculate_rsi_trend(rsi_values)

            # 综合判断：在超卖区域或合理范围内且趋势向好
            passed = (is_oversold or in_good_range) and rsi_trend > -5

            return passed, current_rsi

        except Exception as e:
            logger.warning(f"计算RSI时发生错误: {e}")
            return False, None

    async def _analyze_bollinger_bands(
        self,
        price_data: pd.DataFrame,
        criteria: ScreeningCriteria
    ) -> Tuple[bool, str]:
        """分析布林带"""
        try:
            closing_prices = price_data['close'].values

            # 计算布林带
            if TALIB_AVAILABLE:
                upper_band, middle_band, lower_band = talib.BBANDS(
                    closing_prices,
                    timeperiod=criteria.bollinger_period,
                    nbdevup=criteria.bollinger_std,
                    nbdevdn=criteria.bollinger_std
                )
            else:
                upper_band, middle_band, lower_band = self._calculate_bollinger_bands(
                    closing_prices,
                    criteria.bollinger_period,
                    criteria.bollinger_std
                )

            current_price = closing_prices[-1]
            current_upper = upper_band[-1] if not np.isnan(upper_band[-1]) else None
            current_middle = middle_band[-1] if not np.isnan(middle_band[-1]) else None
            current_lower = lower_band[-1] if not np.isnan(lower_band[-1]) else None

            if None in [current_upper, current_middle, current_lower]:
                return False, "未知"

            # 判断价格在布林带中的位置
            if current_price >= current_upper:
                position = "上轨上方"
                passed = False  # 价格过高，不适合买入
            elif current_price >= current_middle:
                position = "中轨上方"
                passed = True   # 价格在合理区间
            elif current_price >= current_lower:
                position = "下轨上方"
                passed = True   # 价格偏低，适合关注
            else:
                position = "下轨下方"
                passed = True   # 价格超跌，可能是买入机会

            return passed, position

        except Exception as e:
            logger.warning(f"计算布林带时发生错误: {e}")
            return False, "未知"

    def _calculate_sma(self, prices: np.ndarray, period: int) -> np.ndarray:
        """计算简单移动平均线"""
        sma = np.zeros(len(prices))
        for i in range(period - 1, len(prices)):
            sma[i] = np.mean(prices[i - period + 1:i + 1])
        return sma

    def _calculate_rsi(self, prices: np.ndarray, period: int = 14) -> np.ndarray:
        """计算RSI指标"""
        deltas = np.diff(prices)
        seed = deltas[:period + 1]
        up = seed[seed >= 0].sum() / period
        down = -seed[seed < 0].sum() / period
        rs = up / down
        rsi = np.zeros_like(prices)
        rsi[:period] = 100.0 - (100.0 / (1.0 + rs))

        for i in range(period, len(prices)):
            delta = deltas[i - 1]
            if delta > 0:
                upval = delta
                downval = 0.0
            else:
                upval = 0.0
                downval = -delta

            up = (up * (period - 1) + upval) / period
            down = (down * (period - 1) + downval) / period
            rs = up / down
            rsi[i] = 100.0 - (100.0 / (1.0 + rs))

        return rsi

    def _calculate_bollinger_bands(
        self,
        prices: np.ndarray,
        period: int = 20,
        std_dev: float = 2.0
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """计算布林带"""
        middle_band = self._calculate_sma(prices, period)

        upper_band = np.zeros_like(prices)
        lower_band = np.zeros_like(prices)

        for i in range(period - 1, len(prices)):
            window = prices[i - period + 1:i + 1]
            std = np.std(window)
            upper_band[i] = middle_band[i] + (std_dev * std)
            lower_band[i] = middle_band[i] - (std_dev * std)

        return upper_band, middle_band, lower_band

    def _calculate_ma_trend(self, ma_values: np.ndarray, lookback: int = 10) -> float:
        """计算移动平均线趋势"""
        if len(ma_values) < lookback + 1:
            return 0.0

        recent_ma = ma_values[-lookback:]
        if len(recent_ma) < 2:
            return 0.0

        # 计算趋势线的斜率
        x = np.arange(len(recent_ma))
        slope = np.polyfit(x, recent_ma, 1)[0]

        # 归一化斜率
        current_ma = ma_values[-1]
        normalized_slope = (slope / current_ma) * 100 if current_ma > 0 else 0.0

        return normalized_slope

    def _calculate_rsi_trend(self, rsi_values: np.ndarray, lookback: int = 5) -> float:
        """计算RSI趋势"""
        if len(rsi_values) < lookback + 1:
            return 0.0

        recent_rsi = rsi_values[-lookback:]
        if len(recent_rsi) < 2:
            return 0.0

        # 简单的线性趋势
        trend = recent_rsi[-1] - recent_rsi[0]
        return trend

    def _calculate_ma_score(self, ma_passed: bool, distance_threshold: float) -> float:
        """计算移动平均线评分"""
        if ma_passed:
            return 90
        else:
            return 40

    def _calculate_rsi_score(
        self,
        rsi_value: float,
        oversold_threshold: int,
        overbought_threshold: int
    ) -> float:
        """计算RSI评分"""
        if rsi_value <= oversold_threshold:
            return 95  # 超卖，买入机会
        elif rsi_value <= oversold_threshold + 10:
            return 85  # 接近超卖
        elif rsi_value <= overbought_threshold:
            return 75  # 合理区间
        elif rsi_value <= overbought_threshold + 10:
            return 50  # 接近超买
        else:
            return 20  # 超买，避免买入

    def _calculate_bollinger_score(self, bollinger_passed: bool) -> float:
        """计算布林带评分"""
        if bollinger_passed:
            return 80
        else:
            return 30

    def _determine_trend_direction(
        self,
        ma_analysis: Tuple[bool, Optional[float], Optional[float]],
        rsi_value: Optional[float]
    ) -> str:
        """确定趋势方向"""
        passed, ma30, ma60 = ma_analysis

        if rsi_value is None or ma30 is None or ma60 is None:
            return "未知"

        if passed and rsi_value < 30:
            return "强势买入"
        elif passed and rsi_value < 50:
            return "买入"
        elif not passed and rsi_value > 70:
            return "强势卖出"
        elif not passed and rsi_value > 50:
            return "卖出"
        else:
            return "中性"