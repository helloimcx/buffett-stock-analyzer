"""
Risk Manager - 风险管理器

实现四步投资策略的第四步：风险控制
风险控制标准：
- 止损价格计算
- 风险等级评估
- 仓位建议
- 综合风险评分
"""

import asyncio
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from loguru import logger

from ...models.stock import Stock, StockInfo
from ...models.screening import RiskResult, TrendResult, ScreeningCriteria
from ...interfaces.repositories import IStockRepository, IPriceRepository
from ...exceptions.screening import ScreeningError


class RiskManager:
    """风险管理器 - 负责股票的风险控制分析"""

    def __init__(
        self,
        stock_repository: IStockRepository,
        price_repository: IPriceRepository
    ):
        self.stock_repo = stock_repository
        self.price_repo = price_repository

    async def analyze_stocks(
        self,
        trend_results: List[TrendResult],
        criteria: ScreeningCriteria
    ) -> List[RiskResult]:
        """
        对通过趋势分析的股票进行风险分析

        Args:
            trend_results: 通过趋势分析的股票列表
            criteria: 筛选条件

        Returns:
            风险分析结果列表
        """
        logger.info(f"开始风险分析，股票数量：{len(trend_results)}")

        try:
            # 并发分析股票风险
            analysis_tasks = []
            for result in trend_results:
                task = self._analyze_single_stock(result, criteria)
                analysis_tasks.append(task)

            results = await asyncio.gather(*analysis_tasks, return_exceptions=True)

            # 处理结果和异常
            risk_results = []
            failed_count = 0

            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"股票 {trend_results[i].symbol} 风险分析失败: {result}")
                    failed_count += 1
                elif isinstance(result, RiskResult):
                    risk_results.append(result)

            # 按风险评分排序（评分越低风险越低）
            risk_results.sort(key=lambda x: x.risk_score)

            logger.info(f"风险分析完成：成功 {len(risk_results)} 只，失败 {failed_count} 只")

            return risk_results

        except Exception as e:
            logger.error(f"风险分析过程发生错误: {e}")
            raise ScreeningError(f"风险分析失败: {e}") from e

    async def _analyze_single_stock(
        self,
        trend_result: TrendResult,
        criteria: ScreeningCriteria
    ) -> RiskResult:
        """分析单只股票的风险"""
        try:
            symbol = trend_result.symbol

            # 获取股票基本信息
            stock_info = await self.stock_repo.get_stock_info(symbol)

            # 获取历史价格数据（用于波动率计算）
            price_data = await self.price_repo.get_historical_prices(symbol, years=2)

            # 计算各项风险指标
            volatility_analysis = await self._calculate_volatility(price_data)
            stop_loss_analysis = await self._calculate_stop_loss(price_data, criteria)
            valuation_risk = await self._assess_valuation_risk(trend_result)
            liquidity_risk = await self._assess_liquidity_risk(stock_info, price_data)
            concentration_risk = await self._assess_concentration_risk(stock_info)

            # 计算风险等级
            risk_level = self._determine_risk_level(
                volatility_analysis[1],
                stop_loss_analysis[1],
                valuation_risk[1],
                liquidity_risk[1],
                concentration_risk[1]
            )

            # 计算仓位建议
            position_recommendation = self._calculate_position_recommendation(
                risk_level,
                volatility_analysis[1],
                stop_loss_analysis[1]
            )

            # 综合风险评分（0-100，分数越低风险越低）
            risk_score = (
                volatility_analysis[1] * 0.25 +
                valuation_risk[1] * 0.20 +
                liquidity_risk[1] * 0.20 +
                concentration_risk[1] * 0.20 +
                (100 - stop_loss_analysis[1]) * 0.15  # 止损距离越大风险越高
            )

            # 判断是否通过风险控制
            risk_passed = (
                risk_score <= 70 and  # 风险评分≤70
                volatility_analysis[1] <= 80 and  # 波动率风险≤80
                position_recommendation['max_position'] >= 5  # 最小仓位≥5%
            )

            return RiskResult(
                symbol=symbol,
                name=trend_result.name,
                passed=risk_passed,
                risk_score=round(risk_score, 2),
                volatility_score=round(volatility_analysis[1], 2),
                valuation_risk_score=round(valuation_risk[1], 2),
                liquidity_risk_score=round(liquidity_risk[1], 2),
                concentration_risk_score=round(concentration_risk[1], 2),
                current_price=trend_result.current_price,
                stop_loss_price=stop_loss_analysis[0],
                stop_loss_distance=round(stop_loss_analysis[1], 2),
                volatility_pct=round(volatility_analysis[0], 2),
                risk_level=risk_level,
                position_recommendation=position_recommendation,
                risk_factors=self._identify_risk_factors(
                    volatility_analysis[1],
                    valuation_risk[1],
                    liquidity_risk[1],
                    concentration_risk[1]
                ),
                analysis_time=datetime.now()
            )

        except Exception as e:
            logger.error(f"分析股票 {symbol} 风险时发生错误: {e}")
            raise ScreeningError(f"风险分析失败 {symbol}: {e}") from e

    async def _calculate_volatility(self, price_data: pd.DataFrame) -> Tuple[float, float]:
        """计算波动率"""
        try:
            if price_data.empty or len(price_data) < 30:
                return 0.0, 100.0  # 数据不足，高风险

            # 计算日收益率
            price_data['returns'] = price_data['close'].pct_change()
            returns = price_data['returns'].dropna()

            if len(returns) < 20:
                return 0.0, 100.0

            # 计算年化波动率
            daily_volatility = returns.std()
            annualized_volatility = daily_volatility * np.sqrt(252) * 100

            # 波动率评分（波动率越高，风险评分越高）
            if annualized_volatility <= 20:
                volatility_score = 20
            elif annualized_volatility <= 30:
                volatility_score = 40
            elif annualized_volatility <= 40:
                volatility_score = 60
            elif annualized_volatility <= 50:
                volatility_score = 80
            else:
                volatility_score = 100

            return annualized_volatility, volatility_score

        except Exception as e:
            logger.warning(f"计算波动率时发生错误: {e}")
            return 0.0, 100.0

    async def _calculate_stop_loss(
        self,
        price_data: pd.DataFrame,
        criteria: ScreeningCriteria
    ) -> Tuple[Optional[float], float]:
        """计算止损价格和止损距离"""
        try:
            if price_data.empty or len(price_data) < 60:
                return None, 100.0

            current_price = price_data['close'].iloc[-1]

            # 多重止损策略
            stop_loss_prices = []

            # 1. 基于ATR的止损
            atr_stop_loss = await self._calculate_atr_stop_loss(price_data)
            if atr_stop_loss:
                stop_loss_prices.append(atr_stop_loss)

            # 2. 基于移动平均线的止损
            ma_stop_loss = await self._calculate_ma_stop_loss(price_data)
            if ma_stop_loss:
                stop_loss_prices.append(ma_stop_loss)

            # 3. 基于支撑位的止损
            support_stop_loss = await self._calculate_support_stop_loss(price_data)
            if support_stop_loss:
                stop_loss_prices.append(support_stop_loss)

            if not stop_loss_prices:
                return None, 100.0

            # 选择最保守（最高）的止损价格
            stop_loss_price = max(stop_loss_prices)
            stop_loss_distance = ((current_price - stop_loss_price) / current_price) * 100

            # 止损距离评分（距离越大，评分越高表示风险越大）
            if stop_loss_distance <= 5:
                distance_score = 20
            elif stop_loss_distance <= 10:
                distance_score = 40
            elif stop_loss_distance <= 15:
                distance_score = 60
            elif stop_loss_distance <= 20:
                distance_score = 80
            else:
                distance_score = 100

            return round(stop_loss_price, 2), distance_score

        except Exception as e:
            logger.warning(f"计算止损价格时发生错误: {e}")
            return None, 100.0

    async def _calculate_atr_stop_loss(self, price_data: pd.DataFrame) -> Optional[float]:
        """基于ATR计算止损价格"""
        try:
            high_low = price_data['high'] - price_data['low']
            high_close = abs(price_data['high'] - price_data['close'].shift())
            low_close = abs(price_data['low'] - price_data['close'].shift())

            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr = true_range.rolling(window=14).mean()

            if len(atr) < 2 or atr.iloc[-1] != atr.iloc[-1]:
                return None

            current_price = price_data['close'].iloc[-1]
            atr_multiplier = 2.0  # ATR倍数
            stop_loss = current_price - (atr.iloc[-1] * atr_multiplier)

            return stop_loss if stop_loss > 0 else None

        except Exception:
            return None

    async def _calculate_ma_stop_loss(self, price_data: pd.DataFrame) -> Optional[float]:
        """基于移动平均线计算止损价格"""
        try:
            # 使用60日移动平均线作为止损参考
            ma60 = price_data['close'].rolling(window=60).mean()
            current_ma60 = ma60.iloc[-1]

            if pd.isna(current_ma60):
                return None

            return current_ma60

        except Exception:
            return None

    async def _calculate_support_stop_loss(self, price_data: pd.DataFrame) -> Optional[float]:
        """基于支撑位计算止损价格"""
        try:
            # 简单的支撑位：最近60日的最低价
            recent_low = price_data['low'].rolling(window=60).min().iloc[-1]

            if pd.isna(recent_low):
                return None

            return recent_low

        except Exception:
            return None

    async def _assess_valuation_risk(self, trend_result: TrendResult) -> Tuple[bool, float]:
        """评估估值风险"""
        try:
            # 基于趋势分析结果评估估值风险
            if trend_result.overall_trend_score >= 80:
                return True, 20  # 低风险
            elif trend_result.overall_trend_score >= 60:
                return True, 40  # 中低风险
            elif trend_result.overall_trend_score >= 40:
                return True, 60  # 中高风险
            else:
                return False, 80  # 高风险

        except Exception:
            return False, 80

    async def _assess_liquidity_risk(self, stock_info: StockInfo, price_data: pd.DataFrame) -> Tuple[bool, float]:
        """评估流动性风险"""
        try:
            # 基于市值和交易量评估流动性风险
            market_cap = stock_info.market_cap if stock_info.market_cap else 0

            if market_cap >= 1000e8:  # ≥1000亿
                return True, 10  # 流动性极好
            elif market_cap >= 500e8:  # ≥500亿
                return True, 20  # 流动性好
            elif market_cap >= 100e8:  # ≥100亿
                return True, 40  # 流动性中等
            elif market_cap >= 50e8:   # ≥50亿
                return True, 60  # 流动性较差
            else:
                return False, 80  # 流动性差

        except Exception:
            return False, 80

    async def _assess_concentration_risk(self, stock_info: StockInfo) -> Tuple[bool, float]:
        """评估集中度风险"""
        try:
            # 基于行业集中度评估风险
            industry = stock_info.industry

            # 定义高风险行业
            high_risk_industries = ["房地产", "钢铁", "煤炭", "有色金属", "化工"]
            medium_risk_industries = ["银行", "保险", "证券", "建筑", "机械"]

            if industry in high_risk_industries:
                return False, 70  # 高风险行业
            elif industry in medium_risk_industries:
                return True, 50   # 中等风险行业
            else:
                return True, 30   # 低风险行业

        except Exception:
            return True, 50

    def _determine_risk_level(
        self,
        volatility_score: float,
        stop_loss_score: float,
        valuation_risk_score: float,
        liquidity_risk_score: float,
        concentration_risk_score: float
    ) -> str:
        """确定风险等级"""
        total_score = (
            volatility_score * 0.3 +
            stop_loss_score * 0.25 +
            valuation_risk_score * 0.2 +
            liquidity_risk_score * 0.15 +
            concentration_risk_score * 0.1
        )

        if total_score <= 30:
            return "低风险"
        elif total_score <= 50:
            return "中等风险"
        elif total_score <= 70:
            return "较高风险"
        else:
            return "高风险"

    def _calculate_position_recommendation(
        self,
        risk_level: str,
        volatility_score: float,
        stop_loss_score: float
    ) -> Dict:
        """计算仓位建议"""
        base_positions = {
            "低风险": {"min_position": 15, "max_position": 25},
            "中等风险": {"min_position": 10, "max_position": 20},
            "较高风险": {"min_position": 5, "max_position": 15},
            "高风险": {"min_position": 3, "max_position": 10}
        }

        base = base_positions.get(risk_level, {"min_position": 5, "max_position": 15})

        # 根据波动率和止损距离调整仓位
        volatility_adjustment = max(0, (50 - volatility_score) / 100)
        stop_loss_adjustment = max(0, (50 - stop_loss_score) / 100)

        adjustment = 1 + (volatility_adjustment + stop_loss_adjustment) / 2

        return {
            "min_position": round(base["min_position"] * adjustment, 1),
            "max_position": round(base["max_position"] * adjustment, 1),
            "recommended_position": round(
                (base["min_position"] + base["max_position"]) / 2 * adjustment, 1
            )
        }

    def _identify_risk_factors(
        self,
        volatility_score: float,
        valuation_risk_score: float,
        liquidity_risk_score: float,
        concentration_risk_score: float
    ) -> List[str]:
        """识别主要风险因素"""
        risk_factors = []

        if volatility_score >= 70:
            risk_factors.append("价格波动较大")
        if valuation_risk_score >= 70:
            risk_factors.append("估值偏高")
        if liquidity_risk_score >= 70:
            risk_factors.append("流动性不足")
        if concentration_risk_score >= 70:
            risk_factors.append("行业风险较高")

        return risk_factors if risk_factors else ["无明显风险因素"]