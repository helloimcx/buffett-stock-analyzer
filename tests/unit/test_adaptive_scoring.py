"""
自适应评分系统测试
测试市场环境识别与多因子评分的集成功能
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from src.buffett.core.adaptive_scoring import (
    AdaptiveWeightConfig, AdaptiveMultiFactorScorer, MarketEnvironmentMonitor
)
from src.buffett.core.market_environment import (
    MarketEnvironment, MarketEnvironmentType, MarketEnvironmentIdentifier
)
from src.buffett.core.multi_factor_scoring import MultiFactorScorer
from src.buffett.models.stock import StockInfo


class TestAdaptiveWeightConfig:
    """测试自适应权重配置"""
    
    def test_default_weights(self):
        """测试默认权重"""
        config = AdaptiveWeightConfig()
        
        default_weights = config.default_weights
        assert "value" in default_weights
        assert "growth" in default_weights
        assert "quality" in default_weights
        assert "momentum" in default_weights
        assert "dividend" in default_weights
        assert "technical" in default_weights
        assert "sentiment" in default_weights
        
        # 验证权重总和为1
        assert abs(sum(default_weights.values()) - 1.0) < 0.001
    
    def test_bull_market_weights(self):
        """测试牛市权重配置"""
        config = AdaptiveWeightConfig()
        
        bull_weights = config.get_weights_for_environment(MarketEnvironmentType.BULL)
        
        # 牛市应该提高成长和动量因子权重
        assert bull_weights["growth"] > config.default_weights["growth"]
        assert bull_weights["momentum"] > config.default_weights["momentum"]
        
        # 牛市应该降低价值和质量因子权重
        assert bull_weights["value"] < config.default_weights["value"]
        assert bull_weights["quality"] < config.default_weights["quality"]
    
    def test_bear_market_weights(self):
        """测试熊市权重配置"""
        config = AdaptiveWeightConfig()
        
        bear_weights = config.get_weights_for_environment(MarketEnvironmentType.BEAR)
        
        # 熊市应该提高价值和质量因子权重
        assert bear_weights["value"] > config.default_weights["value"]
        assert bear_weights["quality"] > config.default_weights["quality"]
        assert bear_weights["dividend"] > config.default_weights["dividend"]
        
        # 熊市应该降低成长和动量因子权重
        assert bear_weights["growth"] < config.default_weights["growth"]
        assert bear_weights["momentum"] < config.default_weights["momentum"]
    
    def test_sideways_market_weights(self):
        """测试震荡市权重配置"""
        config = AdaptiveWeightConfig()
        
        sideways_weights = config.get_weights_for_environment(MarketEnvironmentType.SIDEWAYS)
        
        # 震荡市应该相对均衡
        for factor in config.default_weights:
            assert abs(sideways_weights[factor] - config.default_weights[factor]) <= 0.0501  # 允许浮点误差
    
    def test_adaptive_weights_with_confidence(self):
        """测试基于置信度的自适应权重"""
        config = AdaptiveWeightConfig()
        
        # 高置信度应该接近环境特定权重
        high_conf_env = MarketEnvironment(
            environment_type=MarketEnvironmentType.BULL,
            confidence=0.9,
            trend_direction="bullish",
            volatility_level="medium",
            sentiment_score=0.7,
            timestamp=datetime.now()
        )
        
        high_conf_weights = config.calculate_adaptive_weights(high_conf_env)
        bull_weights = config.get_weights_for_environment(MarketEnvironmentType.BULL)
        
        for factor in bull_weights:
            assert abs(high_conf_weights[factor] - bull_weights[factor]) < 0.1
        
        # 低置信度应该接近默认权重
        low_conf_env = MarketEnvironment(
            environment_type=MarketEnvironmentType.BULL,
            confidence=0.3,
            trend_direction="bullish",
            volatility_level="medium",
            sentiment_score=0.7,
            timestamp=datetime.now()
        )
        
        low_conf_weights = config.calculate_adaptive_weights(low_conf_env)
        
        for factor in config.default_weights:
            assert abs(low_conf_weights[factor] - config.default_weights[factor]) <= 0.1  # 允许等于0.1


class TestAdaptiveMultiFactorScorer:
    """测试自适应多因子评分器"""
    
    def test_initialization(self):
        """测试初始化"""
        scorer = AdaptiveMultiFactorScorer()
        
        assert scorer.market_identifier is not None
        assert scorer.weight_config is not None
        assert scorer.environment_storage is not None
        assert scorer.current_environment is None
        assert scorer.last_update is None
    
    def test_update_market_environment(self):
        """测试更新市场环境"""
        scorer = AdaptiveMultiFactorScorer()
        
        market_data = {
            "prices": list(range(100, 160)),  # 上涨趋势
            "current_volume": 180000000,
            "avg_volume": 100000000,
            "advancing_stocks": 2800,
            "declining_stocks": 1200,
            "momentum": 0.025
        }
        
        environment = scorer.update_market_environment(market_data)
        
        assert environment is not None
        assert scorer.current_environment == environment
        assert scorer.last_update is not None
        assert isinstance(environment, MarketEnvironment)
    
    def test_create_adaptive_scorer(self):
        """测试创建自适应评分器"""
        scorer = AdaptiveMultiFactorScorer()
        
        # 创建牛市环境
        bull_env = MarketEnvironment(
            environment_type=MarketEnvironmentType.BULL,
            confidence=0.8,
            trend_direction="bullish",
            volatility_level="medium",
            sentiment_score=0.7,
            timestamp=datetime.now()
        )
        
        adaptive_scorer = scorer.create_adaptive_scorer(bull_env)
        
        assert isinstance(adaptive_scorer, MultiFactorScorer)
        
        # 验证权重已调整
        # 这里需要检查内部因子权重，但由于封装限制，我们通过评分结果验证
        assert adaptive_scorer.factors is not None
    
    def test_create_adaptive_scorer_without_environment(self):
        """测试没有环境信息时创建评分器"""
        scorer = AdaptiveMultiFactorScorer()
        
        # 没有环境信息时应该使用默认权重
        adaptive_scorer = scorer.create_adaptive_scorer()
        
        assert isinstance(adaptive_scorer, MultiFactorScorer)
    
    def test_calculate_adaptive_score(self):
        """测试计算自适应评分"""
        scorer = AdaptiveMultiFactorScorer()
        
        # 创建测试股票
        stock = StockInfo(
            code="000001",
            name="测试股票",
            price=10.0,
            dividend_yield=3.0,
            pe_ratio=15.0,
            pb_ratio=2.0,
            change_pct=0.02,
            volume=1000000,
            market_cap=1000000000,
            eps=1.0,
            book_value=5.0,
            week_52_high=12.0,
            week_52_low=8.0
        )
        
        # 创建牛市环境
        bull_env = MarketEnvironment(
            environment_type=MarketEnvironmentType.BULL,
            confidence=0.8,
            trend_direction="bullish",
            volatility_level="medium",
            sentiment_score=0.7,
            timestamp=datetime.now()
        )
        
        score = scorer.calculate_adaptive_score(stock, bull_env)
        
        assert 0 <= score <= 1
        assert isinstance(score, float)
    
    def test_rank_stocks_adaptive(self):
        """测试自适应股票排序"""
        scorer = AdaptiveMultiFactorScorer()
        
        # 创建测试股票列表
        stocks = [
            StockInfo(
                code="000001",
                name="股票1",
                price=10.0,
                dividend_yield=3.0,
                pe_ratio=15.0,
                pb_ratio=2.0,
                change_pct=0.02,
                volume=1000000,
                market_cap=1000000000,
                eps=1.0,
                book_value=5.0,
                week_52_high=12.0,
                week_52_low=8.0
            ),
            StockInfo(
                code="000002",
                name="股票2",
                price=20.0,
                dividend_yield=2.0,
                pe_ratio=25.0,
                pb_ratio=3.0,
                change_pct=0.01,
                volume=2000000,
                market_cap=2000000000,
                eps=0.8,
                book_value=6.0,
                week_52_high=25.0,
                week_52_low=15.0
            )
        ]
        
        # 创建牛市环境
        bull_env = MarketEnvironment(
            environment_type=MarketEnvironmentType.BULL,
            confidence=0.8,
            trend_direction="bullish",
            volatility_level="medium",
            sentiment_score=0.7,
            timestamp=datetime.now()
        )
        
        ranked_stocks = scorer.rank_stocks_adaptive(stocks, bull_env)
        
        assert len(ranked_stocks) == 2
        assert hasattr(ranked_stocks[0], 'total_score')
        assert hasattr(ranked_stocks[1], 'total_score')
        # 排序后第一只股票的评分应该不低于第二只
        assert ranked_stocks[0].total_score >= ranked_stocks[1].total_score
    
    def test_get_environment_analysis(self):
        """测试获取环境分析"""
        scorer = AdaptiveMultiFactorScorer()
        
        # 没有环境数据时
        analysis = scorer.get_environment_analysis()
        assert analysis["status"] == "no_environment_data"
        
        # 有环境数据时
        market_data = {
            "prices": list(range(100, 160)),
            "current_volume": 180000000,
            "avg_volume": 100000000,
            "advancing_stocks": 2800,
            "declining_stocks": 1200,
            "momentum": 0.025
        }
        
        scorer.update_market_environment(market_data)
        analysis = scorer.get_environment_analysis()
        
        assert analysis["status"] == "active"
        assert "environment" in analysis
        assert "weights" in analysis
        assert "recommendations" in analysis
        assert "default" in analysis["weights"]
        assert "current" in analysis["weights"]
        assert "changes" in analysis["weights"]
    
    def test_save_and_load_config(self):
        """测试保存和加载配置"""
        import tempfile
        import os
        
        scorer = AdaptiveMultiFactorScorer()
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            # 保存配置
            success = scorer.save_config(temp_file)
            assert success is True
            
            # 修改配置
            original_growth_weight = scorer.weight_config.default_weights["growth"]
            scorer.weight_config.default_weights["growth"] = 0.99
            
            # 加载配置
            success = scorer.load_config(temp_file)
            assert success is True
            
            # 验证配置已恢复
            assert scorer.weight_config.default_weights["growth"] == original_growth_weight
            
        finally:
            # 清理临时文件
            if os.path.exists(temp_file):
                os.unlink(temp_file)


class TestMarketEnvironmentMonitor:
    """测试市场环境监控器"""
    
    def test_initialization(self):
        """测试初始化"""
        adaptive_scorer = AdaptiveMultiFactorScorer()
        monitor = MarketEnvironmentMonitor(adaptive_scorer)
        
        assert monitor.adaptive_scorer == adaptive_scorer
        assert monitor.storage is not None
        assert monitor.alert_callbacks == []
    
    def test_add_alert_callback(self):
        """测试添加预警回调"""
        adaptive_scorer = AdaptiveMultiFactorScorer()
        monitor = MarketEnvironmentMonitor(adaptive_scorer)
        
        # 创建模拟回调
        callback = Mock()
        monitor.add_alert_callback(callback)
        
        assert len(monitor.alert_callbacks) == 1
        assert monitor.alert_callbacks[0] == callback
    
    def test_monitor_and_update_no_change(self):
        """测试监控更新（无环境变化）"""
        adaptive_scorer = AdaptiveMultiFactorScorer()
        monitor = MarketEnvironmentMonitor(adaptive_scorer)
        
        market_data = {
            "prices": list(range(100, 160)),
            "current_volume": 180000000,
            "avg_volume": 100000000,
            "advancing_stocks": 2800,
            "declining_stocks": 1200,
            "momentum": 0.025
        }
        
        # 第一次更新
        result1 = monitor.monitor_and_update(market_data)
        assert result1["previous_environment"] is None
        assert result1["current_environment"] is not None
        assert result1["change_detected"] is False
        assert result1["alert"] is None
        
        # 第二次更新（相同数据）
        result2 = monitor.monitor_and_update(market_data)
        assert result2["previous_environment"] is not None
        assert result2["current_environment"] is not None
        assert result2["change_detected"] is False
        assert result2["alert"] is None
    
    def test_monitor_and_update_with_change(self):
        """测试监控更新（有环境变化）"""
        adaptive_scorer = AdaptiveMultiFactorScorer()
        monitor = MarketEnvironmentMonitor(adaptive_scorer)
        
        # 创建回调
        callback = Mock()
        monitor.add_alert_callback(callback)
        
        # 牛市数据
        bull_data = {
            "prices": list(range(100, 160)),
            "current_volume": 180000000,
            "avg_volume": 100000000,
            "advancing_stocks": 2800,
            "declining_stocks": 1200,
            "momentum": 0.025
        }
        
        # 熊市数据
        bear_data = {
            "prices": list(range(200, 140, -1)),
            "current_volume": 120000000,
            "avg_volume": 100000000,
            "advancing_stocks": 1200,
            "declining_stocks": 2800,
            "momentum": -0.025
        }
        
        # 第一次更新（牛市）
        result1 = monitor.monitor_and_update(bull_data)
        assert result1["change_detected"] is False
        
        # 第二次更新（熊市）
        result2 = monitor.monitor_and_update(bear_data)
        assert result2["change_detected"] is True
        assert result2["alert"] is not None
        assert result2["alert"]["alert_type"] == "market_change"
        
        # 验证回调被调用
        callback.assert_called_once()
    
    def test_get_environment_history(self):
        """测试获取环境历史"""
        adaptive_scorer = AdaptiveMultiFactorScorer()
        monitor = MarketEnvironmentMonitor(adaptive_scorer)
        
        market_data = {
            "prices": list(range(100, 160)),
            "current_volume": 180000000,
            "avg_volume": 100000000,
            "advancing_stocks": 2800,
            "declining_stocks": 1200,
            "momentum": 0.025
        }
        
        # 更新环境
        monitor.monitor_and_update(market_data)
        
        # 获取历史记录
        history = monitor.get_environment_history(days=7)
        
        assert isinstance(history, list)
        # 由于使用模拟存储，可能返回空列表
        # assert len(history) >= 0


class TestIntegration:
    """测试集成功能"""
    
    def test_end_to_end_adaptive_scoring(self):
        """测试端到端自适应评分"""
        # 创建自适应评分器
        scorer = AdaptiveMultiFactorScorer()
        
        # 模拟市场数据变化
        bull_data = {
            "prices": list(range(100, 160)),
            "current_volume": 180000000,
            "avg_volume": 100000000,
            "advancing_stocks": 2800,
            "declining_stocks": 1200,
            "momentum": 0.025
        }
        
        # 更新市场环境
        environment = scorer.update_market_environment(bull_data)
        assert environment.environment_type == MarketEnvironmentType.BULL
        
        # 创建测试股票
        stock = StockInfo(
            code="000001",
            name="测试股票",
            price=10.0,
            dividend_yield=3.0,
            pe_ratio=15.0,
            pb_ratio=2.0,
            change_pct=0.02,
            volume=1000000,
            market_cap=1000000000,
            eps=1.0,
            book_value=5.0,
            week_52_high=12.0,
            week_52_low=8.0
        )
        
        # 计算自适应评分
        score = scorer.calculate_adaptive_score(stock)
        assert 0 <= score <= 1
        
        # 获取环境分析
        analysis = scorer.get_environment_analysis()
        assert analysis["status"] == "active"
        assert "recommendations" in analysis
        assert len(analysis["recommendations"]) > 0
        
        # 验证牛市相关建议
        recommendations = " ".join(analysis["recommendations"])
        assert "牛市" in recommendations or "成长" in recommendations
    
    def test_environment_transition(self):
        """测试环境转换"""
        # 创建监控器
        scorer = AdaptiveMultiFactorScorer()
        monitor = MarketEnvironmentMonitor(scorer)
        
        # 添加预警回调
        alerts = []
        def alert_callback(alert):
            alerts.append(alert)
        
        monitor.add_alert_callback(alert_callback)
        
        # 牛市数据
        bull_data = {
            "prices": list(range(100, 160)),
            "current_volume": 180000000,
            "avg_volume": 100000000,
            "advancing_stocks": 2800,
            "declining_stocks": 1200,
            "momentum": 0.025
        }
        
        # 熊市数据
        bear_data = {
            "prices": list(range(200, 140, -1)),
            "current_volume": 120000000,
            "avg_volume": 100000000,
            "advancing_stocks": 1200,
            "declining_stocks": 2800,
            "momentum": -0.025
        }
        
        # 模拟环境转换
        monitor.monitor_and_update(bull_data)  # 牛市
        monitor.monitor_and_update(bear_data)  # 熊市
        
        # 验证预警
        assert len(alerts) == 1
        alert = alerts[0]
        assert alert.alert_type == "market_change"
        assert alert.previous_environment.value == "bull"
        assert alert.current_environment.value == "bear"