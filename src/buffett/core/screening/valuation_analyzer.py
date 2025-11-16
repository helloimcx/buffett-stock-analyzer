"""
Valuation Analyzer - 估值分析器

实现四步投资策略的第二步：估值评估
分析标准：
- PE比率 ≤ 30百分位
- PB比率 ≤ 20百分位
- 股息率 ≥ 70百分位
- 综合估值评分
"""

import asyncio
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from loguru import logger

from ...models.stock import Stock, StockInfo
from ...models.screening import ValuationResult, ScreeningCriteria, EligibilityResult
from ...interfaces.repositories import IStockRepository, IDividendRepository, IPriceRepository
from ...exceptions.screening import ScreeningError


class ValuationAnalyzer:
    """估值分析器 - 负责股票的估值评估"""

    def __init__(
        self,
        stock_repository: IStockRepository,
        dividend_repository: IDividendRepository,
        price_repository: IPriceRepository
    ):
        self.stock_repo = stock_repository
        self.dividend_repo = dividend_repository
        self.price_repo = price_repository
        self._valuation_cache = {}  # 缓存历史估值数据

    async def analyze_stocks(
        self,
        eligibility_results: List[EligibilityResult],
        criteria: ScreeningCriteria
    ) -> List[ValuationResult]:
        """
        对通过资格筛选的股票进行估值分析

        Args:
            eligibility_results: 通过资格筛选的股票列表
            criteria: 筛选条件

        Returns:
            估值分析结果列表
        """
        logger.info(f"开始估值分析，股票数量：{len(eligibility_results)}")

        try:
            # 并发分析股票估值
            analysis_tasks = []
            for result in eligibility_results:
                task = self._analyze_single_stock(result, criteria)
                analysis_tasks.append(task)

            results = await asyncio.gather(*analysis_tasks, return_exceptions=True)

            # 处理结果和异常
            valuation_results = []
            failed_count = 0

            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"股票 {eligibility_results[i].symbol} 估值分析失败: {result}")
                    failed_count += 1
                elif isinstance(result, ValuationResult):
                    valuation_results.append(result)

            # 按综合估值评分排序（评分越高表示越便宜）
            valuation_results.sort(key=lambda x: x.overall_valuation_score, reverse=True)

            logger.info(f"估值分析完成：成功 {len(valuation_results)} 只，失败 {failed_count} 只")

            return valuation_results

        except Exception as e:
            logger.error(f"估值分析过程发生错误: {e}")
            raise ScreeningError(f"估值分析失败: {e}") from e

    async def _analyze_single_stock(
        self,
        eligibility_result: EligibilityResult,
        criteria: ScreeningCriteria
    ) -> ValuationResult:
        """分析单只股票的估值"""
        try:
            symbol = eligibility_result.symbol

            # 获取股票基本信息
            stock_info = await self.stock_repo.get_stock_info(symbol)

            # 获取历史价格数据
            price_data = await self.price_repo.get_historical_prices(
                symbol,
                years=criteria.history_years
            )

            # 获取分红数据
            dividend_data = await self.dividend_repo.get_dividend_data(symbol)

            # 获取同行业股票数据用于百分位计算
            industry_stocks = await self._get_industry_peers(stock_info.industry, symbol)

            # 计算各项估值指标
            pe_analysis = await self._analyze_pe_ratio(stock_info, price_data, criteria)
            pb_analysis = await self._analyze_pb_ratio(stock_info, price_data, criteria)
            dividend_yield_analysis = await self._analyze_dividend_yield_valuation(
                dividend_data, criteria
            )

            # 计算历史百分位
            pe_percentile = await self._calculate_pe_percentile(symbol, pe_analysis[1], industry_stocks)
            pb_percentile = await self._calculate_pb_percentile(symbol, pb_analysis[1], industry_stocks)
            dividend_percentile = await self._calculate_dividend_percentile(
                symbol, dividend_yield_analysis[1], industry_stocks
            )

            # 计算各项评分
            pe_score = self._calculate_pe_score(pe_percentile, criteria.max_pe_percentile)
            pb_score = self._calculate_pb_score(pb_percentile, criteria.max_pb_percentile)
            dividend_score = self._calculate_dividend_yield_score(
                dividend_percentile, criteria.min_dividend_yield_percentile
            )

            # 综合估值评分
            overall_score = (
                pe_score * 0.35 +
                pb_score * 0.35 +
                dividend_score * 0.30
            )

            # 判断是否通过估值筛选
            valuation_passed = (
                pe_percentile <= criteria.max_pe_percentile and
                pb_percentile <= criteria.max_pb_percentile and
                dividend_percentile >= criteria.min_dividend_yield_percentile
            )

            # 估值等级评定
            valuation_level = self._determine_valuation_level(overall_score)

            return ValuationResult(
                symbol=symbol,
                name=eligibility_result.name,
                passed=valuation_passed,
                overall_valuation_score=round(overall_score, 2),
                pe_score=round(pe_score, 2),
                pb_score=round(pb_score, 2),
                dividend_yield_score=round(dividend_score, 2),
                current_pe=pe_analysis[1],
                current_pb=pb_analysis[1],
                current_dividend_yield=dividend_yield_analysis[1],
                pe_percentile=round(pe_percentile, 2),
                pb_percentile=round(pb_percentile, 2),
                dividend_yield_percentile=round(dividend_percentile, 2),
                valuation_level=valuation_level,
                analysis_time=datetime.now()
            )

        except Exception as e:
            logger.error(f"分析股票 {symbol} 估值时发生错误: {e}")
            raise ScreeningError(f"估值分析失败 {symbol}: {e}") from e

    async def _analyze_pe_ratio(
        self,
        stock_info: StockInfo,
        price_data: pd.DataFrame,
        criteria: ScreeningCriteria
    ) -> Tuple[bool, float]:
        """分析PE比率"""
        try:
            current_pe = stock_info.pe_ratio

            if current_pe is None or current_pe <= 0:
                return False, 0.0

            # 检查PE是否在合理范围内
            if current_pe > 100:  # 过高的PE可能表明数据问题
                return False, current_pe

            # PE>0 且不为负数
            return True, float(current_pe)

        except Exception as e:
            logger.warning(f"计算PE比率时发生错误: {e}")
            return False, 0.0

    async def _analyze_pb_ratio(
        self,
        stock_info: StockInfo,
        price_data: pd.DataFrame,
        criteria: ScreeningCriteria
    ) -> Tuple[bool, float]:
        """分析PB比率"""
        try:
            current_pb = stock_info.pb_ratio

            if current_pb is None or current_pb <= 0:
                return False, 0.0

            # 检查PB是否在合理范围内
            if current_pb > 50:  # 过高的PB可能表明数据问题
                return False, current_pb

            # PB>0 且不为负数
            return True, float(current_pb)

        except Exception as e:
            logger.warning(f"计算PB比率时发生错误: {e}")
            return False, 0.0

    async def _analyze_dividend_yield_valuation(
        self,
        dividend_data: pd.DataFrame,
        criteria: ScreeningCriteria
    ) -> Tuple[bool, float]:
        """分析股息率估值"""
        try:
            if dividend_data.empty:
                return False, 0.0

            # 使用最近一年的股息率
            recent_year = dividend_data.nlargest(1, 'year')
            if recent_year.empty:
                return False, 0.0

            current_dividend_yield = recent_year.iloc[0]['dividend_rate']

            if current_dividend_yield is None or current_dividend_yield <= 0:
                return False, 0.0

            return True, float(current_dividend_yield)

        except Exception as e:
            logger.warning(f"计算股息率时发生错误: {e}")
            return False, 0.0

    async def _get_industry_peers(
        self,
        industry: str,
        exclude_symbol: str
    ) -> List[StockInfo]:
        """获取同行业股票"""
        try:
            industry_stocks = await self.stock_repo.get_stocks_by_industry(industry)
            peer_infos = []

            for stock in industry_stocks:
                if stock.symbol != exclude_symbol:
                    stock_info = await self.stock_repo.get_stock_info(stock.symbol)
                    if stock_info.pe_ratio and stock_info.pb_ratio:
                        peer_infos.append(stock_info)

            return peer_infos

        except Exception as e:
            logger.warning(f"获取行业股票数据时发生错误: {e}")
            return []

    async def _calculate_pe_percentile(
        self,
        symbol: str,
        current_pe: float,
        industry_peers: List[StockInfo]
    ) -> float:
        """计算PE百分位"""
        try:
            if not industry_peers:
                return 50.0  # 缺少对比数据时返回中位数

            # 收集同行业PE数据
            peer_pes = [peer.pe_ratio for peer in industry_peers if peer.pe_ratio and peer.pe_ratio > 0]

            if not peer_pes:
                return 50.0

            # 添加当前股票的PE
            all_pes = peer_pes + [current_pe]

            # 计算百分位
            sorted_pes = sorted(all_pes)
            rank = sorted_pes.index(current_pe) + 1
            percentile = (rank / len(sorted_pes)) * 100

            return round(percentile, 2)

        except Exception as e:
            logger.warning(f"计算PE百分位时发生错误: {e}")
            return 50.0

    async def _calculate_pb_percentile(
        self,
        symbol: str,
        current_pb: float,
        industry_peers: List[StockInfo]
    ) -> float:
        """计算PB百分位"""
        try:
            if not industry_peers:
                return 50.0

            # 收集同行业PB数据
            peer_pbs = [peer.pb_ratio for peer in industry_peers if peer.pb_ratio and peer.pb_ratio > 0]

            if not peer_pbs:
                return 50.0

            # 添加当前股票的PB
            all_pbs = peer_pbs + [current_pb]

            # 计算百分位
            sorted_pbs = sorted(all_pbs)
            rank = sorted_pbs.index(current_pb) + 1
            percentile = (rank / len(sorted_pbs)) * 100

            return round(percentile, 2)

        except Exception as e:
            logger.warning(f"计算PB百分位时发生错误: {e}")
            return 50.0

    async def _calculate_dividend_percentile(
        self,
        symbol: str,
        current_dividend_yield: float,
        industry_peers: List[StockInfo]
    ) -> float:
        """计算股息率百分位"""
        try:
            if not industry_peers:
                return 50.0

            # 获取同行业股票的股息率
            peer_dividend_yields = []
            for peer in industry_peers:
                dividend_data = await self.dividend_repo.get_dividend_data(peer.symbol)
                if not dividend_data.empty:
                    recent_year = dividend_data.nlargest(1, 'year')
                    if not recent_year.empty:
                        dividend_yield = recent_year.iloc[0]['dividend_rate']
                        if dividend_yield and dividend_yield > 0:
                            peer_dividend_yields.append(dividend_yield)

            if not peer_dividend_yields:
                return 50.0

            # 添加当前股票的股息率
            all_yields = peer_dividend_yields + [current_dividend_yield]

            # 计算百分位（股息率越高越好，所以需要反向计算）
            sorted_yields = sorted(all_yields, reverse=True)
            rank = sorted_yields.index(current_dividend_yield) + 1
            percentile = ((len(sorted_yields) - rank + 1) / len(sorted_yields)) * 100

            return round(percentile, 2)

        except Exception as e:
            logger.warning(f"计算股息率百分位时发生错误: {e}")
            return 50.0

    def _calculate_pe_score(self, pe_percentile: float, max_percentile: float) -> float:
        """计算PE评分"""
        if pe_percentile <= max_percentile:
            return 100
        else:
            # 超出要求的百分位，评分递减
            excess = pe_percentile - max_percentile
            return max(100 - excess * 2, 0)

    def _calculate_pb_score(self, pb_percentile: float, max_percentile: float) -> float:
        """计算PB评分"""
        if pb_percentile <= max_percentile:
            return 100
        else:
            # 超出要求的百分位，评分递减
            excess = pb_percentile - max_percentile
            return max(100 - excess * 2, 0)

    def _calculate_dividend_yield_score(self, dividend_percentile: float, min_percentile: float) -> float:
        """计算股息率评分"""
        if dividend_percentile >= min_percentile:
            return 100
        else:
            # 低于要求的百分位，评分递减
            deficit = min_percentile - dividend_percentile
            return max(100 - deficit * 2, 0)

    def _determine_valuation_level(self, overall_score: float) -> str:
        """确定估值等级"""
        if overall_score >= 90:
            return "极度低估"
        elif overall_score >= 80:
            return "低估"
        elif overall_score >= 70:
            return "合理偏低"
        elif overall_score >= 60:
            return "合理"
        elif overall_score >= 50:
            return "合理偏高"
        elif overall_score >= 40:
            return "高估"
        else:
            return "极度高估"