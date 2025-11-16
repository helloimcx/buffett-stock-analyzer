"""
Screening Service - 筛选服务编排

负责协调四步投资策略的完整执行流程：
1. Eligibility Screening - 资格筛选
2. Valuation Assessment - 估值评估
3. Trend Analysis - 趋势分析
4. Risk Control - 风险控制

提供统一的筛选服务接口，并处理结果聚合和报告生成。
"""

import asyncio
from typing import Dict, List, Optional
from datetime import datetime
from loguru import logger

from ..container import Container
from ...models.stock import Stock
from ...models.screening import (
    ScreeningCriteria,
    ScreeningResult,
    CompleteScreeningResult,
    EligibilityResult,
    ValuationResult,
    TrendResult,
    RiskResult
)
from ...models.industry import IndustryConfig
from ...interfaces.repositories import IStockRepository, IDividendRepository, IPriceRepository
from ...exceptions.screening import ScreeningError
from .eligibility_screener import EligibilityScreener
from .valuation_analyzer import ValuationAnalyzer
from .trend_analyzer import TrendAnalyzer
from .risk_manager import RiskManager


class ScreeningService:
    """筛选服务 - 四步投资策略的完整执行服务"""

    def __init__(self, container: Optional[Container] = None):
        self.container = container or Container()

        # 初始化各个分析器
        self._init_analyzers()

    def _init_analyzers(self):
        """初始化分析器"""
        try:
            # 获取Repository依赖
            stock_repo = self.container.resolve(IStockRepository)

            # 获取其他Repository（假设已在容器中注册）
            dividend_repo = self.container.resolve(IDividendRepository)
            price_repo = self.container.resolve(IPriceRepository)
            industry_config = self.container.resolve(IndustryConfig)

            # 初始化分析器
            self.eligibility_screener = EligibilityScreener(
                stock_repository=stock_repo,
                dividend_repository=dividend_repo,
                industry_config=industry_config
            )

            self.valuation_analyzer = ValuationAnalyzer(
                stock_repository=stock_repo,
                dividend_repository=dividend_repo,
                price_repository=price_repo
            )

            self.trend_analyzer = TrendAnalyzer(price_repository=price_repo)

            self.risk_manager = RiskManager(
                stock_repository=stock_repo,
                price_repository=price_repo
            )

            logger.info("筛选服务初始化完成")

        except Exception as e:
            logger.error(f"筛选服务初始化失败: {e}")
            raise ScreeningError(f"筛选服务初始化失败: {e}") from e

    async def run_complete_screening(
        self,
        criteria: Optional[ScreeningCriteria] = None,
        stocks: Optional[List[Stock]] = None
    ) -> CompleteScreeningResult:
        """
        运行完整的四步投资策略筛选

        Args:
            criteria: 筛选条件，如果为None则使用默认条件
            stocks: 待筛选股票列表，如果为None则筛选所有股票

        Returns:
            完整的筛选结果
        """
        logger.info("开始运行完整的四步投资策略筛选")

        start_time = datetime.now()

        try:
            # 使用默认筛选条件（如果未提供）
            if criteria is None:
                criteria = ScreeningCriteria()

            # 第一步：资格筛选
            logger.info("第一步：资格筛选...")
            eligibility_results = await self.eligibility_screener.screen_stocks(criteria, stocks)
            logger.info(f"资格筛选完成，通过股票数量：{len(eligibility_results)}")

            if not eligibility_results:
                return CompleteScreeningResult(
                    criteria=criteria,
                    eligibility_results=[],
                    valuation_results=[],
                    trend_results=[],
                    risk_results=[],
                    final_candidates=[],
                    summary=self._create_empty_summary(start_time, datetime.now()),
                    execution_time=(datetime.now() - start_time).total_seconds()
                )

            # 第二步：估值评估
            logger.info("第二步：估值评估...")
            valuation_results = await self.valuation_analyzer.analyze_stocks(eligibility_results, criteria)
            logger.info(f"估值评估完成，通过股票数量：{len(valuation_results)}")

            if not valuation_results:
                return CompleteScreeningResult(
                    criteria=criteria,
                    eligibility_results=eligibility_results,
                    valuation_results=[],
                    trend_results=[],
                    risk_results=[],
                    final_candidates=[],
                    summary=self._create_summary(eligibility_results, [], [], [], start_time, datetime.now()),
                    execution_time=(datetime.now() - start_time).total_seconds()
                )

            # 第三步：趋势分析
            logger.info("第三步：趋势分析...")
            trend_results = await self.trend_analyzer.analyze_stocks(valuation_results, criteria)
            logger.info(f"趋势分析完成，通过股票数量：{len(trend_results)}")

            if not trend_results:
                return CompleteScreeningResult(
                    criteria=criteria,
                    eligibility_results=eligibility_results,
                    valuation_results=valuation_results,
                    trend_results=[],
                    risk_results=[],
                    final_candidates=[],
                    summary=self._create_summary(eligibility_results, valuation_results, [], [], start_time, datetime.now()),
                    execution_time=(datetime.now() - start_time).total_seconds()
                )

            # 第四步：风险控制
            logger.info("第四步：风险控制...")
            risk_results = await self.risk_manager.analyze_stocks(trend_results, criteria)
            logger.info(f"风险控制完成，通过股票数量：{len(risk_results)}")

            # 生成最终候选股票列表
            final_candidates = self._generate_final_candidates(risk_results)

            # 创建筛选摘要
            end_time = datetime.now()
            summary = self._create_summary(
                eligibility_results, valuation_results, trend_results, risk_results,
                start_time, end_time
            )

            execution_time = (end_time - start_time).total_seconds()

            logger.info(f"完整筛选完成，最终候选股票数量：{len(final_candidates)}，执行时间：{execution_time:.2f}秒")

            return CompleteScreeningResult(
                criteria=criteria,
                eligibility_results=eligibility_results,
                valuation_results=valuation_results,
                trend_results=trend_results,
                risk_results=risk_results,
                final_candidates=final_candidates,
                summary=summary,
                execution_time=execution_time
            )

        except Exception as e:
            logger.error(f"完整筛选过程发生错误: {e}")
            raise ScreeningError(f"完整筛选失败: {e}") from e

    async def run_eligibility_screening_only(
        self,
        criteria: Optional[ScreeningCriteria] = None,
        stocks: Optional[List[Stock]] = None
    ) -> List[EligibilityResult]:
        """仅运行资格筛选"""
        if criteria is None:
            criteria = ScreeningCriteria()

        return await self.eligibility_screener.screen_stocks(criteria, stocks)

    async def run_valuation_analysis_only(
        self,
        eligibility_results: List[EligibilityResult],
        criteria: Optional[ScreeningCriteria] = None
    ) -> List[ValuationResult]:
        """仅运行估值分析"""
        if criteria is None:
            criteria = ScreeningCriteria()

        return await self.valuation_analyzer.analyze_stocks(eligibility_results, criteria)

    async def run_trend_analysis_only(
        self,
        valuation_results: List[ValuationResult],
        criteria: Optional[ScreeningCriteria] = None
    ) -> List[TrendResult]:
        """仅运行趋势分析"""
        if criteria is None:
            criteria = ScreeningCriteria()

        return await self.trend_analyzer.analyze_stocks(valuation_results, criteria)

    async def run_risk_analysis_only(
        self,
        trend_results: List[TrendResult],
        criteria: Optional[ScreeningCriteria] = None
    ) -> List[RiskResult]:
        """仅运行风险分析"""
        if criteria is None:
            criteria = ScreeningCriteria()

        return await self.risk_manager.analyze_stocks(trend_results, criteria)

    def _generate_final_candidates(self, risk_results: List[RiskResult]) -> List[Dict]:
        """生成最终候选股票列表"""
        candidates = []

        for risk_result in risk_results:
            candidate = {
                "symbol": risk_result.symbol,
                "name": risk_result.name,
                "overall_score": self._calculate_overall_score(risk_result),
                "investment_grade": self._determine_investment_grade(risk_result),
                "position_recommendation": risk_result.position_recommendation,
                "risk_level": risk_result.risk_level,
                "stop_loss_price": risk_result.stop_loss_price,
                "current_price": risk_result.current_price,
                "reasoning": self._generate_investment_reasoning(risk_result)
            }
            candidates.append(candidate)

        # 按综合评分排序
        candidates.sort(key=lambda x: x["overall_score"], reverse=True)

        return candidates

    def _calculate_overall_score(self, risk_result: RiskResult) -> float:
        """计算综合评分"""
        # 综合考虑各个维度的评分
        score = (
            (100 - risk_result.risk_score) * 0.3 +  # 风险评分（越低越好）
            (100 - risk_result.volatility_score) * 0.2 +  # 波动率评分
            (100 - risk_result.valuation_risk_score) * 0.2 +  # 估值风险评分
            (100 - risk_result.liquidity_risk_score) * 0.15 +  # 流动性评分
            (100 - risk_result.concentration_risk_score) * 0.15  # 集中度评分
        )
        return round(score, 2)

    def _determine_investment_grade(self, risk_result: RiskResult) -> str:
        """确定投资等级"""
        overall_score = self._calculate_overall_score(risk_result)

        if overall_score >= 85:
            return "强烈推荐"
        elif overall_score >= 75:
            return "推荐"
        elif overall_score >= 65:
            return "适度推荐"
        elif overall_score >= 55:
            return "中性"
        elif overall_score >= 45:
            return "谨慎"
        else:
            return "不推荐"

    def _generate_investment_reasoning(self, risk_result: RiskResult) -> str:
        """生成投资理由"""
        reasons = []

        if risk_result.risk_score <= 30:
            reasons.append("风险控制良好")
        if risk_result.volatility_score <= 40:
            reasons.append("价格相对稳定")
        if risk_result.position_recommendation["max_position"] >= 15:
            reasons.append("建议仓位较高")
        if risk_result.stop_loss_distance <= 10:
            reasons.append("止损距离合理")
        if not risk_result.risk_factors or risk_result.risk_factors == ["无明显风险因素"]:
            reasons.append("无明显风险因素")

        return "；".join(reasons) if reasons else "符合基本投资要求"

    def _create_summary(
        self,
        eligibility_results: List[EligibilityResult],
        valuation_results: List[ValuationResult],
        trend_results: List[TrendResult],
        risk_results: List[RiskResult],
        start_time: datetime,
        end_time: datetime
    ) -> Dict:
        """创建筛选摘要"""
        return {
            "screening_time": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "duration_seconds": (end_time - start_time).total_seconds()
            },
            "step_results": {
                "eligibility": {
                    "input_count": 0,  # 需要从外部传入
                    "passed_count": len(eligibility_results),
                    "pass_rate": 0.0  # 需要计算
                },
                "valuation": {
                    "input_count": len(eligibility_results),
                    "passed_count": len(valuation_results),
                    "pass_rate": len(valuation_results) / len(eligibility_results) * 100 if eligibility_results else 0
                },
                "trend": {
                    "input_count": len(valuation_results),
                    "passed_count": len(trend_results),
                    "pass_rate": len(trend_results) / len(valuation_results) * 100 if valuation_results else 0
                },
                "risk": {
                    "input_count": len(trend_results),
                    "passed_count": len(risk_results),
                    "pass_rate": len(risk_results) / len(trend_results) * 100 if trend_results else 0
                }
            },
            "final_candidates": len(risk_results),
            "industry_distribution": self._calculate_industry_distribution(risk_results),
            "risk_distribution": self._calculate_risk_distribution(risk_results)
        }

    def _create_empty_summary(self, start_time: datetime, end_time: datetime) -> Dict:
        """创建空结果的摘要"""
        return {
            "screening_time": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "duration_seconds": (end_time - start_time).total_seconds()
            },
            "step_results": {
                "eligibility": {"input_count": 0, "passed_count": 0, "pass_rate": 0.0},
                "valuation": {"input_count": 0, "passed_count": 0, "pass_rate": 0.0},
                "trend": {"input_count": 0, "passed_count": 0, "pass_rate": 0.0},
                "risk": {"input_count": 0, "passed_count": 0, "pass_rate": 0.0}
            },
            "final_candidates": 0,
            "industry_distribution": {},
            "risk_distribution": {}
        }

    def _calculate_industry_distribution(self, risk_results: List[RiskResult]) -> Dict:
        """计算行业分布"""
        distribution = {}
        for result in risk_results:
            # 这里需要获取股票的行业信息，简化处理
            industry = "未知"  # 实际应从stock_info获取
            distribution[industry] = distribution.get(industry, 0) + 1
        return distribution

    def _calculate_risk_distribution(self, risk_results: List[RiskResult]) -> Dict:
        """计算风险分布"""
        distribution = {}
        for result in risk_results:
            risk_level = result.risk_level
            distribution[risk_level] = distribution.get(risk_level, 0) + 1
        return distribution