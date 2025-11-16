"""
Eligibility Screener - 资格筛选器

实现四步投资策略的第一步：资格筛选
筛选标准：
- 股息率 ≥ 4%
- 连续分红年数 ≥ 3年
- 行业龙头优先
- 分红稳定性评估
"""

import asyncio
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from loguru import logger

from ...models.stock import Stock, StockInfo
from ...models.screening import EligibilityResult, ScreeningCriteria, ScreeningStatus
from ...models.industry import IndustryLeader, IndustryConfig
from ...interfaces.repositories import IStockRepository, IDividendRepository
from ...exceptions.screening import ScreeningError


class EligibilityScreener:
    """资格筛选器 - 负责股票的初步资格筛选"""

    def __init__(
        self,
        stock_repository: IStockRepository,
        dividend_repository: IDividendRepository,
        industry_config: IndustryConfig
    ):
        self.stock_repo = stock_repository
        self.dividend_repo = dividend_repository
        self.industry_config = industry_config

        # 初始化带缓存的AKShare策略实例（禁用代理）
        from ...strategies.data_fetch_strategies import AKShareStrategy
        self.akshare_strategy = AKShareStrategy(cache_ttl_hours=24, enable_cache=True, proxy=None)

    async def screen_stocks(
        self,
        criteria: ScreeningCriteria,
        stocks: Optional[List[Stock]] = None
    ) -> List[EligibilityResult]:
        """
        对股票进行资格筛选

        Args:
            criteria: 筛选条件
            stocks: 待筛选股票列表，如果为None则获取所有股票

        Returns:
            通过资格筛选的股票结果列表
        """
        logger.info(f"开始资格筛选，条件：股息率≥{criteria.min_dividend_yield}%，分红年数≥{criteria.min_dividend_years}年")

        try:
            # 获取股票数据
            if stocks is None:
                stocks = await self.stock_repo.get_all_stocks()

            logger.info(f"待筛选股票数量：{len(stocks)}")

            # 并发筛选股票
            eligibility_tasks = []
            for stock in stocks:
                task = self._screen_single_stock(stock, criteria)
                eligibility_tasks.append(task)

            results = await asyncio.gather(*eligibility_tasks, return_exceptions=True)

            # 处理结果和异常
            passed_stocks = []
            failed_count = 0

            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"股票 {stocks[i].symbol} 筛选失败: {result}")
                    failed_count += 1
                elif isinstance(result, EligibilityResult) and result.status == ScreeningStatus.PASSED:
                    passed_stocks.append(result)

            logger.info(f"资格筛选完成：通过 {len(passed_stocks)} 只，失败 {failed_count} 只，不符合条件 {len(stocks) - len(passed_stocks) - failed_count} 只")

            # 按综合评分排序
            passed_stocks.sort(key=lambda x: x.overall_score, reverse=True)

            return passed_stocks

        except Exception as e:
            logger.error(f"资格筛选过程发生错误: {e}")
            raise ScreeningError(f"资格筛选失败: {e}") from e

    async def _screen_single_stock(
        self,
        stock: Stock,
        criteria: ScreeningCriteria
    ) -> EligibilityResult:
        """筛选单只股票"""
        try:
            logger.debug(f"开始筛选股票 {stock.symbol}")

            # 获取股票详细信息
            stock_info = await self.stock_repo.get_stock_info(stock.symbol)
            logger.debug(f"股票 {stock.symbol} 信息获取完成")

            # 动态获取分红数据（使用AKShare策略）
            dividend_data = await self._fetch_dividend_data_dynamically(stock.symbol)
            logger.debug(f"股票 {stock.symbol} 获取到 {len(dividend_data)} 条分红记录")

            # 执行各项筛选标准检查
            dividend_yield_check = await self._check_dividend_yield(dividend_data, criteria.min_dividend_yield)
            dividend_years_check = await self._check_dividend_years(dividend_data, criteria.min_dividend_years)
            market_cap_check = await self._check_market_cap(stock_info)
            stability_check = await self._check_dividend_stability(dividend_data)

            # 计算各项得分
            dividend_yield_score = self._calculate_dividend_yield_score(dividend_yield_check[1])
            dividend_years_score = self._calculate_dividend_years_score(dividend_years_check[1])
            market_cap_score = self._calculate_market_cap_score(market_cap_check[1])
            stability_score = self._calculate_stability_score(stability_check[1])

            # 综合评分计算
            overall_score = (
                dividend_yield_score * 0.3 +
                dividend_years_score * 0.3 +
                market_cap_score * 0.25 +
                stability_score * 0.15
            )

            # 判断是否通过筛选
            passed = (
                dividend_yield_check[0] and
                dividend_years_check[0] and
                market_cap_check[0] and
                stability_check[0]
            )

            return EligibilityResult(
                symbol=stock.symbol,
                name=stock.name,
                screening_stage="eligibility",
                status=ScreeningStatus.PASSED if passed else ScreeningStatus.FAILED,
                score=round(overall_score, 2),
                reason="Eligibility screening completed",
                dividend_yield=dividend_yield_check[1],
                dividend_years=dividend_years_check[1] if dividend_years_check[1] > 0 else None,
                avg_dividend_rate=dividend_yield_check[1],
                min_dividend_rate=dividend_yield_check[1],  # 暂时使用相同值
                stability_score=round(stability_score, 2),
                industry_rank=None,  # 暂时设为None
                is_industry_leader=market_cap_check[1],
                leadership_tier=1 if market_cap_check[1] else None,
                forced_inclusion=False,
                timestamp=datetime.now()
            )

        except Exception as e:
            logger.error(f"筛选股票 {stock.symbol} 时发生错误: {e}")
            raise ScreeningError(f"筛选股票 {stock.symbol} 失败: {e}") from e

    async def _fetch_dividend_data_dynamically(self, symbol: str) -> pd.DataFrame:
        """动态获取股息数据"""
        try:
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"开始动态获取股票 {symbol} 的股息数据（使用缓存策略）")

            # 使用实例的带缓存的AKShare策略
            dividend_df = await self.akshare_strategy.fetch_dividend_data(symbol)

            if dividend_df.empty:
                logger.debug(f"股票 {symbol} 无股息数据")
                return pd.DataFrame()

            # 转换为筛选器期望的格式
            dividend_data = pd.DataFrame([{
                'year': row['year'],
                'cash_dividend': row['cash_dividend'],
                'stock_dividend': row['stock_dividend'],
                'is_annual_report': row['is_annual_report'],
                'dividend_rate': row['cash_dividend']  # 使用现金股息作为股息率的代理
            } for _, row in dividend_df.iterrows()])

            logger.debug(f"股票 {symbol} 股息数据获取成功，记录数: {len(dividend_data)}")
            return dividend_data

        except Exception as e:
            logger.warning(f"动态获取股票 {symbol} 股息数据失败: {e}")
            return pd.DataFrame()

    async def _check_dividend_yield(self, dividend_data: pd.DataFrame, min_yield: float) -> Tuple[bool, float]:
        """检查股息率是否符合要求"""
        if dividend_data.empty:
            return False, 0.0

        try:
            # 计算平均股息率（使用最近3年数据）
            recent_years = dividend_data.nlargest(3, 'year')
            avg_yield = recent_years['dividend_rate'].mean()

            passed = avg_yield >= min_yield
            return passed, round(avg_yield, 2)

        except Exception as e:
            logger.warning(f"计算股息率时发生错误: {e}")
            return False, 0.0

    async def _check_dividend_years(self, dividend_data: pd.DataFrame, min_years: int) -> Tuple[bool, int]:
        """检查连续分红年数是否符合要求"""
        if dividend_data.empty:
            return False, 0

        try:
            # 按年份排序，检查连续分红年数
            sorted_data = dividend_data.sort_values('year', ascending=False)

            consecutive_years = 0
            current_year = datetime.now().year

            for _, row in sorted_data.iterrows():
                if row['year'] == current_year - consecutive_years:
                    if row['cash_dividend'] > 0:
                        consecutive_years += 1
                    else:
                        break
                else:
                    break

            passed = consecutive_years >= min_years
            return passed, consecutive_years

        except Exception as e:
            logger.warning(f"计算连续分红年数时发生错误: {e}")
            return False, 0

    async def _check_market_cap(
        self,
        stock_info: StockInfo
    ) -> Tuple[bool, bool]:
        """检查市值是否超过1000亿"""
        try:
            # 检查stock_info是否有效
            if stock_info is None:
                logger.warning(f"股票信息为空，无法检查市值")
                return False, False

            # 获取市值信息
            market_cap = getattr(stock_info, 'market_cap', 0)
            if market_cap is None or market_cap <= 0:
                logger.warning(f"股票 {stock_info.symbol} 市值信息为空或无效: {market_cap}")
                return False, False

            # 1000亿市值检查 (市值单位通常是元，1000亿 = 100,000,000,000)
            min_market_cap = 100_000_000_000  # 1000亿
            passes = market_cap >= min_market_cap

            logger.debug(f"股票 {stock_info.symbol} 市值: {market_cap/100_000_000:.0f}亿, 是否达标: {passes}")
            return passes, passes

        except Exception as e:
            logger.warning(f"检查市值时发生错误: {e}")
            return False, False

    async def _check_dividend_stability(self, dividend_data: pd.DataFrame) -> Tuple[bool, float]:
        """检查分红稳定性"""
        if dividend_data.empty or len(dividend_data) < 3:
            return False, 0.0

        try:
            # 计算分红稳定性评分
            # 1. 分红增长趋势（权重40%）
            # 2. 分红比率稳定性（权重30%）
            # 3. 分红连续性（权重30%）

            recent_years = dividend_data.sort_values('year', ascending=False).head(5)

            # 分红增长趋势
            if len(recent_years) >= 3:
                dividend_rates = recent_years['dividend_rate'].values
                growth_trend = np.polyfit(range(len(dividend_rates)), dividend_rates, 1)[0]
                growth_score = min(max(growth_trend * 10 + 50, 0), 100)  # 归一化到0-100
            else:
                growth_score = 30

            # 分红比率稳定性
            dividend_ratios = recent_years['dividend_rate'].dropna()
            if len(dividend_ratios) >= 2:
                ratio_std = dividend_ratios.std()
                ratio_stability = max(100 - ratio_std * 100, 0)  # 标准差越小越稳定
            else:
                ratio_stability = 40

            # 分红连续性
            consecutive_years = len(recent_years[recent_years['cash_dividend'] > 0])
            continuity_score = (consecutive_years / len(recent_years)) * 100

            # 综合稳定性评分
            stability_score = (
                growth_score * 0.4 +
                ratio_stability * 0.3 +
                continuity_score * 0.3
            )

            passed = stability_score >= 60  # 稳定性评分≥60分
            return passed, round(stability_score, 2)

        except Exception as e:
            logger.warning(f"计算分红稳定性时发生错误: {e}")
            return False, 0.0

    def _calculate_dividend_yield_score(self, dividend_yield: float) -> float:
        """计算股息率评分"""
        if dividend_yield >= 6:
            return 100
        elif dividend_yield >= 5:
            return 85
        elif dividend_yield >= 4:
            return 70
        elif dividend_yield >= 3:
            return 50
        else:
            return dividend_yield * 10  # 低于3%的线性评分

    def _calculate_dividend_years_score(self, years: int) -> float:
        """计算分红年数评分"""
        if years >= 10:
            return 100
        elif years >= 7:
            return 90
        elif years >= 5:
            return 80
        elif years >= 3:
            return 70
        elif years >= 1:
            return 40
        else:
            return 0

    def _calculate_market_cap_score(self, passes_threshold: bool) -> float:
        """计算市值评分"""
        return 90 if passes_threshold else 60

    def _calculate_stability_score(self, stability_rating: float) -> float:
        """计算稳定性评分"""
        return min(stability_rating, 100)  # 直接使用稳定性评分