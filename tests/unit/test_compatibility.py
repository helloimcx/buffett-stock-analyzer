"""
兼容性测试
验证多因子评分系统与现有InvestmentScorer的兼容性
"""

import pytest
from src.buffett.models.stock import StockInfo
from src.buffett.core.scoring import InvestmentScorer
from src.buffett.core.multi_factor_scoring import MultiFactorScorer


class TestInvestmentScorerCompatibility:
    """测试与现有InvestmentScorer的兼容性"""

    def test_interface_compatibility(self):
        """测试接口兼容性"""
        # 创建测试股票数据
        stock = StockInfo(
            code="TEST", name="Test Stock", price=10.0, dividend_yield=3.0,
            pe_ratio=20.0, pb_ratio=2.0, change_pct=1.0, volume=1000000,
            market_cap=1000000000.0, eps=1.5, book_value=12.0,
            week_52_high=12.0, week_52_low=8.0
        )
        
        # 使用现有评分器
        old_scorer = InvestmentScorer()
        old_score = old_scorer.calculate_total_score(stock)
        
        # 使用多因子评分器
        new_scorer = MultiFactorScorer.with_legacy_weights()
        new_score = new_scorer.calculate_score(stock) * 100  # 转换为相同分制
        
        # 验证两个评分器都能正常工作
        assert isinstance(old_score, float)
        assert isinstance(new_score, float)
        assert 0 <= old_score <= 100
        assert 0 <= new_score <= 100

    def test_ranking_method_compatibility(self):
        """测试排序方法兼容性"""
        # 创建测试股票数据
        stocks = [
            StockInfo(
                code="GOOD", name="Good Stock", price=10.0, dividend_yield=4.0,
                pe_ratio=15.0, pb_ratio=1.5, change_pct=2.0, volume=2000000,
                market_cap=2000000000.0, eps=2.0, book_value=15.0,
                week_52_high=12.0, week_52_low=8.0
            ),
            StockInfo(
                code="AVERAGE", name="Average Stock", price=10.0, dividend_yield=2.0,
                pe_ratio=25.0, pb_ratio=2.5, change_pct=0.0, volume=1000000,
                market_cap=1000000000.0, eps=1.0, book_value=10.0,
                week_52_high=12.0, week_52_low=8.0
            ),
            StockInfo(
                code="POOR", name="Poor Stock", price=10.0, dividend_yield=0.5,
                pe_ratio=50.0, pb_ratio=5.0, change_pct=-3.0, volume=500000,
                market_cap=500000000.0, eps=0.5, book_value=5.0,
                week_52_high=12.0, week_52_low=8.0
            )
        ]
        
        # 使用现有评分器排序
        old_scorer = InvestmentScorer()
        old_ranked = old_scorer.rank_stocks(stocks.copy())
        
        # 使用多因子评分器排序
        new_scorer = MultiFactorScorer.with_legacy_weights()
        new_ranked = new_scorer.rank_stocks(stocks.copy())
        
        # 验证排序结果数量相同
        assert len(old_ranked) == len(new_ranked) == 3
        
        # 验证都是按评分降序排列
        for i in range(len(old_ranked) - 1):
            assert old_ranked[i].total_score >= old_ranked[i + 1].total_score
            assert new_ranked[i].total_score >= new_ranked[i + 1].total_score
        
        # 验证好股票在前面，差股票在后面（趋势应该一致）
        assert old_ranked[0].code in ["GOOD", "AVERAGE"]
        assert old_ranked[-1].code in ["POOR", "AVERAGE"]
        assert new_ranked[0].code in ["GOOD", "AVERAGE"]
        assert new_ranked[-1].code in ["POOR", "AVERAGE"]

    def test_score_correlation(self):
        """测试评分相关性"""
        # 创建更多测试股票数据
        stocks = []
        for i in range(20):
            stock = StockInfo(
                code=f"TEST{i:02d}", name=f"Test Stock {i}", price=10.0 + i,
                dividend_yield=1.0 + (i % 5), pe_ratio=10.0 + (i % 30),
                pb_ratio=1.0 + (i % 4), change_pct=(i % 10) - 5,
                volume=1000000, market_cap=1000000000.0 + i * 100000000,
                eps=0.5 + (i % 3), book_value=8.0 + i,
                week_52_high=15.0, week_52_low=5.0
            )
            stocks.append(stock)
        
        # 计算两个评分器的评分
        old_scorer = InvestmentScorer()
        new_scorer = MultiFactorScorer.with_legacy_weights()
        
        old_scores = []
        new_scores = []
        
        for stock in stocks:
            old_score = old_scorer.calculate_total_score(stock)
            new_score = new_scorer.calculate_score(stock) * 100
            old_scores.append(old_score)
            new_scores.append(new_score)
        
        # 计算相关系数（简化版本）
        n = len(old_scores)
        old_mean = sum(old_scores) / n
        new_mean = sum(new_scores) / n
        
        old_variance = sum((x - old_mean) ** 2 for x in old_scores)
        new_variance = sum((x - new_mean) ** 2 for x in new_scores)
        covariance = sum((old_scores[i] - old_mean) * (new_scores[i] - new_mean) for i in range(n))
        
        if old_variance > 0 and new_variance > 0:
            correlation = covariance / (old_variance ** 0.5 * new_variance ** 0.5)
            # 验证相关性为正（两个评分器趋势应该一致）
            assert correlation > 0.3  # 至少中等正相关

    def test_edge_case_handling(self):
        """测试边界情况处理"""
        # 创建边界情况股票
        edge_stocks = [
            # 零股息股票
            StockInfo(
                code="ZERO_DIV", name="Zero Dividend", price=10.0, dividend_yield=0.0,
                pe_ratio=20.0, pb_ratio=2.0, change_pct=0.0, volume=1000000,
                market_cap=1000000000.0, eps=1.0, book_value=10.0,
                week_52_high=12.0, week_52_low=8.0
            ),
            # 负PE股票（亏损）
            StockInfo(
                code="NEG_PE", name="Negative PE", price=10.0, dividend_yield=2.0,
                pe_ratio=-1.0, pb_ratio=2.0, change_pct=0.0, volume=1000000,
                market_cap=1000000000.0, eps=-0.5, book_value=10.0,
                week_52_high=12.0, week_52_low=8.0
            ),
            # 极高估值股票
            StockInfo(
                code="HIGH_VAL", name="High Valuation", price=10.0, dividend_yield=1.0,
                pe_ratio=100.0, pb_ratio=10.0, change_pct=0.0, volume=1000000,
                market_cap=1000000000.0, eps=0.1, book_value=1.0,
                week_52_high=12.0, week_52_low=8.0
            )
        ]
        
        # 测试两个评分器都能处理边界情况
        old_scorer = InvestmentScorer()
        new_scorer = MultiFactorScorer.with_legacy_weights()
        
        for stock in edge_stocks:
            # 两个评分器都应该能处理而不崩溃
            old_score = old_scorer.calculate_total_score(stock)
            new_score = new_scorer.calculate_score(stock) * 100
            
            assert isinstance(old_score, float)
            assert isinstance(new_score, float)
            assert 0 <= old_score <= 100
            assert 0 <= new_score <= 100

    def test_performance_comparison(self):
        """测试性能对比"""
        import time
        
        # 创建大量测试股票
        stocks = []
        for i in range(100):
            stock = StockInfo(
                code=f"PERF{i:03d}", name=f"Performance Test {i}", price=10.0 + i,
                dividend_yield=2.0 + (i % 5), pe_ratio=15.0 + (i % 25),
                pb_ratio=1.5 + (i % 4), change_pct=(i % 11) - 5,
                volume=1000000, market_cap=1000000000.0 + i * 50000000,
                eps=1.0 + (i % 2), book_value=10.0 + i,
                week_52_high=15.0, week_52_low=5.0
            )
            stocks.append(stock)
        
        # 测试现有评分器性能
        old_scorer = InvestmentScorer()
        start_time = time.time()
        old_results = old_scorer.rank_stocks(stocks.copy())
        old_time = time.time() - start_time
        
        # 测试多因子评分器性能
        new_scorer = MultiFactorScorer.with_legacy_weights()
        start_time = time.time()
        new_results = new_scorer.rank_stocks(stocks.copy())
        new_time = time.time() - start_time
        
        # 验证结果一致性
        assert len(old_results) == len(new_results) == 100
        
        # 验证性能差异在合理范围内
        performance_ratio = new_time / old_time if old_time > 0 else 1.0
        assert performance_ratio < 10.0  # 新系统不应该比旧系统慢10倍以上
        
        # 验证排序趋势基本一致（前10名股票的重合度）
        old_top_10 = {stock.code for stock in old_results[:10]}
        new_top_10 = {stock.code for stock in new_results[:10]}
        overlap = len(old_top_10.intersection(new_top_10))
        
        # 至少有30%的重合度
        assert overlap >= 3

    def test_migration_path(self):
        """测试迁移路径"""
        # 创建兼容性包装器
        class CompatibilityWrapper:
            def __init__(self):
                self.new_scorer = MultiFactorScorer.with_legacy_weights()
            
            def calculate_total_score(self, stock: StockInfo) -> float:
                """兼容旧接口"""
                return self.new_scorer.calculate_score(stock) * 100
            
            def rank_stocks(self, stocks: list[StockInfo]) -> list[StockInfo]:
                """兼容旧接口"""
                return self.new_scorer.rank_stocks(stocks)
        
        # 测试包装器可以完全替代旧评分器
        wrapper = CompatibilityWrapper()
        old_scorer = InvestmentScorer()
        
        # 创建测试股票
        test_stock = StockInfo(
            code="MIGRATION", name="Migration Test", price=10.0, dividend_yield=3.0,
            pe_ratio=20.0, pb_ratio=2.0, change_pct=1.0, volume=1000000,
            market_cap=1000000000.0, eps=1.5, book_value=12.0,
            week_52_high=12.0, week_52_low=8.0
        )
        
        # 验证包装器可以正常工作
        wrapper_score = wrapper.calculate_total_score(test_stock)
        old_score = old_scorer.calculate_total_score(test_stock)
        
        assert isinstance(wrapper_score, float)
        assert 0 <= wrapper_score <= 100
        assert isinstance(old_score, float)
        assert 0 <= old_score <= 100
        
        # 验证排序功能
        test_stocks = [test_stock]
        wrapper_results = wrapper.rank_stocks(test_stocks)
        old_results = old_scorer.rank_stocks(test_stocks)
        
        assert len(wrapper_results) == len(old_results) == 1
        assert wrapper_results[0].code == old_results[0].code