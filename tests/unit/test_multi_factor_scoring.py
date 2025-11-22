"""
多因子评分系统测试
测试因子基类和接口定义
"""

import pytest
from unittest.mock import Mock
from src.buffett.models.stock import StockInfo


class TestFactorInterface:
    """测试因子接口定义"""

    def test_factor_base_class_should_exist(self):
        """测试因子基类应该存在"""
        # 这个测试会失败，因为我们还没有创建因子基类
        from src.buffett.core.multi_factor_scoring import Factor
        assert Factor is not None

    def test_factor_should_have_name_attribute(self):
        """测试因子应该有名称属性"""
        from src.buffett.core.multi_factor_scoring import Factor
        
        # 创建一个具体的因子实现来测试接口
        class TestFactor(Factor):
            def __init__(self):
                super().__init__("test_factor")
                
            def calculate(self, stock: StockInfo) -> float:
                return 0.5
        
        factor = TestFactor()
        assert factor.name == "test_factor"

    def test_factor_should_have_calculate_method(self):
        """测试因子应该有计算方法"""
        from src.buffett.core.multi_factor_scoring import Factor
        
        class TestFactor(Factor):
            def __init__(self):
                super().__init__("test_factor")
                
            def calculate(self, stock: StockInfo) -> float:
                return 0.5
        
        factor = TestFactor()
        # 创建一个模拟股票对象
        mock_stock = Mock(spec=StockInfo)
        
        # 测试calculate方法存在且可调用
        assert hasattr(factor, 'calculate')
        assert callable(factor.calculate)
        
        # 测试calculate方法返回浮点数
        result = factor.calculate(mock_stock)
        assert isinstance(result, float)

    def test_factor_should_have_weight_attribute(self):
        """测试因子应该有权重属性"""
        from src.buffett.core.multi_factor_scoring import Factor
        
        class TestFactor(Factor):
            def __init__(self):
                super().__init__("test_factor", weight=0.3)
                
            def calculate(self, stock: StockInfo) -> float:
                return 0.5
        
        factor = TestFactor()
        assert factor.weight == 0.3

    def test_factor_weight_should_default_to_1_0(self):
        """测试因子权重应该默认为1.0"""
        from src.buffett.core.multi_factor_scoring import Factor
        
        class TestFactor(Factor):
            def __init__(self):
                super().__init__("test_factor")
                
            def calculate(self, stock: StockInfo) -> float:
                return 0.5
        
        factor = TestFactor()
        assert factor.weight == 1.0


class TestSpecificFactors:
    """测试具体因子类型"""

    def test_value_factor_should_exist(self):
        """测试价值因子应该存在"""
        from src.buffett.core.multi_factor_scoring import ValueFactor
        assert ValueFactor is not None

    def test_growth_factor_should_exist(self):
        """测试成长因子应该存在"""
        from src.buffett.core.multi_factor_scoring import GrowthFactor
        assert GrowthFactor is not None

    def test_quality_factor_should_exist(self):
        """测试质量因子应该存在"""
        from src.buffett.core.multi_factor_scoring import QualityFactor
        assert QualityFactor is not None

    def test_momentum_factor_should_exist(self):
        """测试动量因子应该存在"""
        from src.buffett.core.multi_factor_scoring import MomentumFactor
        assert MomentumFactor is not None

    def test_dividend_factor_should_exist(self):
        """测试股息因子应该存在"""
        from src.buffett.core.multi_factor_scoring import DividendFactor
        assert DividendFactor is not None

    def test_technical_factor_should_exist(self):
        """测试技术因子应该存在"""
        from src.buffett.core.multi_factor_scoring import TechnicalFactor
        assert TechnicalFactor is not None

    def test_sentiment_factor_should_exist(self):
        """测试情绪因子应该存在"""
        from src.buffett.core.multi_factor_scoring import SentimentFactor
        assert SentimentFactor is not None


class TestFactorCalculation:
    """测试因子计算逻辑"""

    def test_value_factor_calculation(self):
        """测试价值因子计算"""
        from src.buffett.core.multi_factor_scoring import ValueFactor
        
        factor = ValueFactor()
        
        # 创建测试股票数据
        stock = StockInfo(
            code="TEST",
            name="Test Stock",
            price=10.0,
            dividend_yield=2.0,
            pe_ratio=15.0,
            pb_ratio=1.5,
            change_pct=0.0,
            volume=1000000,
            market_cap=1000000000.0,
            eps=2.0,
            book_value=15.0,
            week_52_high=12.0,
            week_52_low=8.0
        )
        
        result = factor.calculate(stock)
        assert isinstance(result, float)
        assert 0.0 <= result <= 1.0  # 评分应该在0-1范围内


class TestMultiFactorScorer:
    """测试多因子评分器"""

    def test_multi_factor_scorer_should_exist(self):
        """测试多因子评分器应该存在"""
        from src.buffett.core.multi_factor_scoring import MultiFactorScorer
        assert MultiFactorScorer is not None

    def test_multi_factor_scorer_should_have_add_factor_method(self):
        """测试多因子评分器应该有添加因子方法"""
        from src.buffett.core.multi_factor_scoring import MultiFactorScorer, ValueFactor
        
        scorer = MultiFactorScorer()
        factor = ValueFactor()
        
        # 测试add_factor方法存在且可调用
        assert hasattr(scorer, 'add_factor')
        assert callable(scorer.add_factor)
        
        # 测试添加因子
        scorer.add_factor(factor)
        assert len(scorer.factors) == 1
        assert scorer.factors[0] == factor

    def test_multi_factor_scorer_should_have_calculate_score_method(self):
        """测试多因子评分器应该有计算评分方法"""
        from src.buffett.core.multi_factor_scoring import MultiFactorScorer
        
        scorer = MultiFactorScorer()
        
        # 测试calculate_score方法存在且可调用
        assert hasattr(scorer, 'calculate_score')
        assert callable(scorer.calculate_score)

    def test_multi_factor_scorer_should_have_rank_stocks_method(self):
        """测试多因子评分器应该有排序股票方法"""
        from src.buffett.core.multi_factor_scoring import MultiFactorScorer
        
        scorer = MultiFactorScorer()
        
        # 测试rank_stocks方法存在且可调用
        assert hasattr(scorer, 'rank_stocks')
        assert callable(scorer.rank_stocks)

    def test_multi_factor_scorer_should_calculate_weighted_score(self):
        """测试多因子评分器应该计算加权评分"""
        from src.buffett.core.multi_factor_scoring import MultiFactorScorer, ValueFactor, DividendFactor
        
        scorer = MultiFactorScorer()
        
        # 添加不同权重的因子
        value_factor = ValueFactor(weight=0.6)
        dividend_factor = DividendFactor(weight=0.4)
        
        scorer.add_factor(value_factor)
        scorer.add_factor(dividend_factor)
        
        # 创建测试股票数据
        stock = StockInfo(
            code="TEST",
            name="Test Stock",
            price=10.0,
            dividend_yield=4.0,  # 高股息，应该得到高分
            pe_ratio=15.0,       # 低PE，应该得到高分
            pb_ratio=1.5,        # 低PB，应该得到高分
            change_pct=0.0,
            volume=1000000,
            market_cap=1000000000.0,
            eps=2.0,
            book_value=15.0,
            week_52_high=12.0,
            week_52_low=8.0
        )
        
        # 计算评分
        score = scorer.calculate_score(stock)
        
        # 验证评分是浮点数且在合理范围内
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_multi_factor_scorer_should_rank_stocks_correctly(self):
        """测试多因子评分器应该正确排序股票"""
        from src.buffett.core.multi_factor_scoring import MultiFactorScorer, ValueFactor, DividendFactor
        
        scorer = MultiFactorScorer()
        scorer.add_factor(ValueFactor(weight=0.5))
        scorer.add_factor(DividendFactor(weight=0.5))
        
        # 创建测试股票数据
        stock1 = StockInfo(
            code="GOOD",
            name="Good Stock",
            price=10.0,
            dividend_yield=4.0,  # 高股息
            pe_ratio=15.0,       # 低PE
            pb_ratio=1.5,        # 低PB
            change_pct=0.0,
            volume=1000000,
            market_cap=1000000000.0,
            eps=2.0,
            book_value=15.0,
            week_52_high=12.0,
            week_52_low=8.0
        )
        
        stock2 = StockInfo(
            code="BAD",
            name="Bad Stock",
            price=10.0,
            dividend_yield=0.5,  # 低股息
            pe_ratio=50.0,       # 高PE
            pb_ratio=5.0,        # 高PB
            change_pct=0.0,
            volume=1000000,
            market_cap=1000000000.0,
            eps=0.5,
            book_value=2.0,
            week_52_high=12.0,
            week_52_low=8.0
        )
        
        stocks = [stock2, stock1]  # 故意打乱顺序
        
        # 排序股票
        ranked_stocks = scorer.rank_stocks(stocks)
        
        # 验证排序结果
        assert len(ranked_stocks) == 2
        assert ranked_stocks[0].code == "GOOD"  # 好股票应该在前面
        assert ranked_stocks[1].code == "BAD"
        assert ranked_stocks[0].total_score > ranked_stocks[1].total_score

    def test_multi_factor_scorer_should_support_default_factors(self):
        """测试多因子评分器应该支持默认因子"""
        from src.buffett.core.multi_factor_scoring import MultiFactorScorer
        
        scorer = MultiFactorScorer.with_default_factors()
        
        # 验证默认因子已添加
        assert len(scorer.factors) > 0
        
        # 验证包含所有预期因子类型
        factor_names = [factor.name for factor in scorer.factors]
        expected_factors = ["value", "growth", "quality", "momentum", "dividend", "technical", "sentiment"]
        
        for expected_factor in expected_factors:
            assert expected_factor in factor_names

    def test_multi_factor_scorer_should_allow_custom_weights(self):
        """测试多因子评分器应该允许自定义权重"""
        from src.buffett.core.multi_factor_scoring import MultiFactorScorer
        
        # 创建自定义权重配置
        custom_weights = {
            "value": 0.3,
            "dividend": 0.5,
            "technical": 0.2
        }
        
        scorer = MultiFactorScorer.with_custom_weights(custom_weights)
        
        # 验证因子权重设置正确
        for factor in scorer.factors:
            if factor.name in custom_weights:
                assert factor.weight == custom_weights[factor.name]

    def test_multi_factor_scorer_should_handle_empty_factors(self):
        """测试多因子评分器应该处理空因子列表"""
        from src.buffett.core.multi_factor_scoring import MultiFactorScorer
        
        scorer = MultiFactorScorer()
        
        # 创建测试股票数据
        stock = StockInfo(
            code="TEST",
            name="Test Stock",
            price=10.0,
            dividend_yield=2.0,
            pe_ratio=20.0,
            pb_ratio=2.0,
            change_pct=0.0,
            volume=1000000,
            market_cap=1000000000.0,
            eps=1.0,
            book_value=10.0,
            week_52_high=12.0,
            week_52_low=8.0
        )
        
        # 测试空因子列表的情况
        score = scorer.calculate_score(stock)
        assert score == 0.0  # 没有因子时应该返回0

    def test_dividend_factor_calculation(self):
        """测试股息因子计算"""
        from src.buffett.core.multi_factor_scoring import DividendFactor
        
        factor = DividendFactor()
        
        # 创建测试股票数据
        stock = StockInfo(
            code="TEST",
            name="Test Stock",
            price=10.0,
            dividend_yield=4.0,
            pe_ratio=15.0,
            pb_ratio=1.5,
            change_pct=0.0,
            volume=1000000,
            market_cap=1000000000.0,
            eps=2.0,
            book_value=15.0,
            week_52_high=12.0,
            week_52_low=8.0
        )
        
        result = factor.calculate(stock)
        assert isinstance(result, float)
        assert 0.0 <= result <= 1.0  # 评分应该在0-1范围内