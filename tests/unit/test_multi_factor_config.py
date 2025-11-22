"""
多因子评分系统配置和扩展性测试
测试配置管理、权重调整和系统扩展性
"""

import pytest
from unittest.mock import Mock, patch
from src.buffett.models.stock import StockInfo
from src.buffett.core.multi_factor_scoring import (
    MultiFactorScorer, ValueFactor, GrowthFactor, QualityFactor, 
    MomentumFactor, DividendFactor, TechnicalFactor, SentimentFactor
)


class TestMultiFactorConfiguration:
    """测试多因子评分系统配置"""

    def test_configuration_from_dict(self):
        """测试从字典创建配置"""
        from src.buffett.core.multi_factor_scoring import MultiFactorConfig
        
        config_dict = {
            "value": {"weight": 0.3, "enabled": True},
            "dividend": {"weight": 0.4, "enabled": True},
            "technical": {"weight": 0.3, "enabled": True}
        }
        
        config = MultiFactorConfig.from_dict(config_dict)
        
        assert config.factors["value"]["weight"] == 0.3
        assert config.factors["value"]["enabled"] is True
        assert len(config.factors) == 3

    def test_configuration_from_json_file(self):
        """测试从JSON文件创建配置"""
        from src.buffett.core.multi_factor_scoring import MultiFactorConfig
        import json
        import tempfile
        import os
        
        config_data = {
            "value": {"weight": 0.25, "enabled": True},
            "growth": {"weight": 0.25, "enabled": True},
            "dividend": {"weight": 0.5, "enabled": True}
        }
        
        # 创建临时配置文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_file = f.name
        
        try:
            config = MultiFactorConfig.from_file(temp_file)
            assert config.factors["value"]["weight"] == 0.25
            assert config.factors["dividend"]["weight"] == 0.5
        finally:
            os.unlink(temp_file)

    def test_configuration_validation(self):
        """测试配置验证"""
        from src.buffett.core.multi_factor_scoring import MultiFactorConfig
        
        # 测试无效权重
        with pytest.raises(ValueError, match="权重必须在0-1之间"):
            config_dict = {"value": {"weight": 1.5, "enabled": True}}
            MultiFactorConfig.from_dict(config_dict)
        
        # 测试权重总和超过1
        with pytest.raises(ValueError, match="权重总和不能超过1"):
            config_dict = {
                "value": {"weight": 0.6, "enabled": True},
                "dividend": {"weight": 0.6, "enabled": True}
            }
            MultiFactorConfig.from_dict(config_dict)

    def test_disabled_factors(self):
        """测试禁用因子功能"""
        from src.buffett.core.multi_factor_scoring import MultiFactorConfig
        
        config_dict = {
            "value": {"weight": 0.3, "enabled": True},
            "growth": {"weight": 0.3, "enabled": False},  # 禁用
            "dividend": {"weight": 0.7, "enabled": True}
        }
        
        config = MultiFactorConfig.from_dict(config_dict)
        scorer = MultiFactorScorer.from_config(config)
        
        # 验证只有启用的因子被添加
        factor_names = [factor.name for factor in scorer.factors]
        assert "value" in factor_names
        assert "dividend" in factor_names
        assert "growth" not in factor_names  # 禁用的因子不应该被添加


class TestMultiFactorExtensibility:
    """测试多因子评分系统扩展性"""

    def test_custom_factor_registration(self):
        """测试自定义因子注册"""
        from src.buffett.core.multi_factor_scoring import Factor, FactorRegistry
        
        # 创建自定义因子
        class CustomFactor(Factor):
            def __init__(self, weight=1.0):
                super().__init__("custom", weight)
            
            def calculate(self, stock: StockInfo) -> float:
                return 0.8  # 固定高分
        
        # 注册自定义因子
        FactorRegistry.register("custom", CustomFactor)
        
        # 验证注册成功
        assert "custom" in FactorRegistry.get_available_factors()
        assert FactorRegistry.get_factor_class("custom") == CustomFactor

    def test_dynamic_factor_loading(self):
        """测试动态因子加载"""
        from src.buffett.core.multi_factor_scoring import FactorRegistry, Factor
        
        # 创建动态因子类
        def create_dynamic_factor(name: str, calculation_func):
            class DynamicFactor(Factor):
                def __init__(self, weight=1.0):
                    super().__init__(name, weight)
                
                def calculate(self, stock: StockInfo) -> float:
                    return calculation_func(stock)
            
            return DynamicFactor
        
        # 创建基于市值的因子
        market_cap_factor = create_dynamic_factor(
            "market_cap",
            lambda stock: min(stock.market_cap / 10000000000.0, 1.0)  # 100亿为满分
        )
        
        # 注册并使用
        FactorRegistry.register("market_cap", market_cap_factor)
        
        scorer = MultiFactorScorer()
        scorer.add_factor(FactorRegistry.create_factor("market_cap", weight=0.2))
        
        # 测试计算
        stock = StockInfo(
            code="TEST", name="Test", price=10.0, dividend_yield=2.0,
            pe_ratio=20.0, pb_ratio=2.0, change_pct=0.0, volume=1000000,
            market_cap=5000000000.0, eps=1.0, book_value=10.0,
            week_52_high=12.0, week_52_low=8.0
        )
        
        score = scorer.calculate_score(stock)
        assert score > 0

    def test_factor_combination_strategies(self):
        """测试因子组合策略"""
        from src.buffett.core.multi_factor_scoring import FactorCombinationStrategy
        
        # 测试加权平均策略（默认）
        weighted_strategy = FactorCombinationStrategy.WEIGHTED_AVERAGE
        assert weighted_strategy.value == "weighted_average"
        
        # 测试几何平均策略
        geometric_strategy = FactorCombinationStrategy.GEOMETRIC_MEAN
        assert geometric_strategy.value == "geometric_mean"
        
        # 测试最大值策略
        max_strategy = FactorCombinationStrategy.MAXIMUM
        assert max_strategy.value == "maximum"

    def test_factor_performance_tracking(self):
        """测试因子性能跟踪"""
        from src.buffett.core.multi_factor_scoring import FactorPerformanceTracker
        
        tracker = FactorPerformanceTracker()
        
        # 记录因子性能
        tracker.record_factor_performance("value", 0.8, 0.05)  # 得分0.8，收益5%
        tracker.record_factor_performance("dividend", 0.6, 0.03)  # 得分0.6，收益3%
        tracker.record_factor_performance("value", 0.7, 0.04)  # 另一次记录
        
        # 获取因子统计
        value_stats = tracker.get_factor_stats("value")
        assert value_stats["count"] == 2
        assert value_stats["avg_score"] == 0.75
        assert value_stats["avg_return"] == 0.045
        
        # 获取最佳因子
        best_factor = tracker.get_best_factor()
        assert best_factor == "value"  # 价值因子平均收益更高


class TestMultiFactorIntegration:
    """测试多因子评分系统集成"""

    def test_integration_with_existing_scorer(self):
        """测试与现有评分器的集成"""
        from src.buffett.core.scoring import InvestmentScorer
        from src.buffett.core.multi_factor_scoring import MultiFactorScorer
        
        # 创建测试股票数据
        stock = StockInfo(
            code="TEST", name="Test", price=10.0, dividend_yield=4.0,
            pe_ratio=15.0, pb_ratio=1.5, change_pct=0.0, volume=1000000,
            market_cap=1000000000.0, eps=2.0, book_value=15.0,
            week_52_high=12.0, week_52_low=8.0
        )
        
        # 使用现有评分器
        old_scorer = InvestmentScorer()
        old_score = old_scorer.calculate_total_score(stock)
        
        # 使用多因子评分器
        new_scorer = MultiFactorScorer.with_default_factors()
        new_score = new_scorer.calculate_score(stock) * 100  # 转换为相同分制
        
        # 验证两个评分器都能正常工作
        assert isinstance(old_score, float)
        assert isinstance(new_score, float)
        assert 0 <= old_score <= 100
        assert 0 <= new_score <= 100

    def test_backward_compatibility(self):
        """测试向后兼容性"""
        from src.buffett.core.multi_factor_scoring import MultiFactorScorer
        
        # 创建与旧系统兼容的评分器
        compatible_scorer = MultiFactorScorer.with_legacy_weights()
        
        # 验证权重配置与旧系统相似
        factor_weights = {factor.name: factor.weight for factor in compatible_scorer.factors}
        
        # 应该包含旧系统的核心因子
        assert "dividend" in factor_weights
        assert "value" in factor_weights
        assert "technical" in factor_weights
        
        # 股息因子权重应该最高（与旧系统一致）
        assert factor_weights["dividend"] > factor_weights["value"]
        assert factor_weights["dividend"] > factor_weights["technical"]

    def test_performance_comparison(self):
        """测试性能对比"""
        import time
        from src.buffett.core.scoring import InvestmentScorer
        from src.buffett.core.multi_factor_scoring import MultiFactorScorer
        
        # 创建测试股票数据
        stocks = []
        for i in range(100):  # 100只测试股票
            stock = StockInfo(
                code=f"TEST{i:03d}", name=f"Test Stock {i}", price=10.0 + i,
                dividend_yield=2.0 + (i % 5), pe_ratio=15.0 + (i % 20),
                pb_ratio=1.5 + (i % 5), change_pct=(i % 10) - 5,
                volume=1000000, market_cap=1000000000.0 + i * 10000000,
                eps=1.0 + (i % 3), book_value=10.0 + i,
                week_52_high=12.0, week_52_low=8.0
            )
            stocks.append(stock)
        
        # 测试旧系统性能
        old_scorer = InvestmentScorer()
        start_time = time.time()
        old_results = old_scorer.rank_stocks(stocks.copy())
        old_time = time.time() - start_time
        
        # 测试新系统性能
        new_scorer = MultiFactorScorer.with_default_factors()
        start_time = time.time()
        new_results = new_scorer.rank_stocks(stocks.copy())
        new_time = time.time() - start_time
        
        # 验证两个系统都能处理相同数量的股票
        assert len(old_results) == len(new_results) == 100
        
        # 性能差异不应该太大（新系统可能有轻微开销，但应该合理）
        performance_ratio = new_time / old_time if old_time > 0 else 1.0
        assert performance_ratio < 5.0  # 新系统不应该比旧系统慢5倍以上


class TestMultiFactorRobustness:
    """测试多因子评分系统健壮性"""

    def test_handling_missing_data(self):
        """测试处理缺失数据"""
        scorer = MultiFactorScorer.with_default_factors()
        
        # 创建有缺失数据的股票
        stock_with_missing = StockInfo(
            code="MISSING", name="Missing Data Stock", price=10.0,
            dividend_yield=0.0,  # 缺失股息数据
            pe_ratio=-1.0,       # 缺失PE数据
            pb_ratio=-1.0,       # 缺失PB数据
            change_pct=0.0, volume=0,  # 缺失交易数据
            market_cap=0.0,      # 缺失市值数据
            eps=0.0,             # 缺失EPS数据
            book_value=0.0,      # 缺失账面价值数据
            week_52_high=0.0,    # 缺失52周高点
            week_52_low=0.0      # 缺失52周低点
        )
        
        # 系统应该能处理缺失数据而不崩溃
        score = scorer.calculate_score(stock_with_missing)
        assert isinstance(score, float)
        assert 0 <= score <= 1

    def test_extreme_values_handling(self):
        """测试极端值处理"""
        scorer = MultiFactorScorer.with_default_factors()
        
        # 创建有极端值的股票
        extreme_stock = StockInfo(
            code="EXTREME", name="Extreme Values Stock", price=1000000.0,
            dividend_yield=999.9,  # 极高股息率
            pe_ratio=999999.0,     # 极高PE
            pb_ratio=999999.0,     # 极高PB
            change_pct=999.9,       # 极高涨幅
            volume=999999999999,   # 极高成交量
            market_cap=999999999999999.0,  # 极高市值
            eps=999999.0,          # 极高EPS
            book_value=999999.0,   # 极高账面价值
            week_52_high=999999.0, week_52_low=0.1
        )
        
        # 系统应该能处理极端值而不崩溃
        score = scorer.calculate_score(extreme_stock)
        assert isinstance(score, float)
        assert 0 <= score <= 1

    def test_concurrent_scoring(self):
        """测试并发评分"""
        import threading
        from src.buffett.core.multi_factor_scoring import MultiFactorScorer
        
        scorer = MultiFactorScorer.with_default_factors()
        results = []
        errors = []
        
        def score_stock(stock_id):
            try:
                stock = StockInfo(
                    code=f"THREAD{stock_id}", name=f"Thread Stock {stock_id}",
                    price=10.0, dividend_yield=2.0, pe_ratio=20.0, pb_ratio=2.0,
                    change_pct=0.0, volume=1000000, market_cap=1000000000.0,
                    eps=1.0, book_value=10.0, week_52_high=12.0, week_52_low=8.0
                )
                score = scorer.calculate_score(stock)
                results.append(score)
            except Exception as e:
                errors.append(e)
        
        # 创建多个线程同时评分
        threads = []
        for i in range(10):
            thread = threading.Thread(target=score_stock, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 验证没有错误且所有评分都成功
        assert len(errors) == 0
        assert len(results) == 10
        for score in results:
            assert isinstance(score, float)
            assert 0 <= score <= 1