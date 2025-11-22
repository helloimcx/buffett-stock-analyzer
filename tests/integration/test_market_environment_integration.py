"""
市场环境识别集成测试
验证市场环境识别机制与评分系统和监控系统的集成功能
"""

import sys
import os
import unittest
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from tests.integration.test_framework import IntegrationTestBase, TestDataGenerator, PerformanceMonitor
from src.buffett.core.market_environment import (
    MarketEnvironmentIdentifier, TrendAnalyzer, VolatilityAnalyzer, SentimentAnalyzer,
    MarketEnvironment, MarketEnvironmentType, MarketEnvironmentHistory,
    MarketEnvironmentStorage
)
from src.buffett.core.multi_factor_scoring import MultiFactorScorer
from src.buffett.core.scoring import InvestmentScorer
from src.buffett.models.stock import StockInfo


class TestMarketEnvironmentIntegration(IntegrationTestBase):
    """市场环境识别集成测试"""
    
    def setUp(self):
        """测试前准备"""
        super().setUp()
        
        # 创建市场环境识别器
        self.environment_identifier = MarketEnvironmentIdentifier()
        
        # 创建分析器
        self.trend_analyzer = TrendAnalyzer()
        self.volatility_analyzer = VolatilityAnalyzer()
        self.sentiment_analyzer = SentimentAnalyzer()
        
        # 创建评分器
        self.multi_factor_scorer = MultiFactorScorer.with_default_factors()
        self.legacy_scorer = InvestmentScorer()
        
        # 性能监控器
        self.performance_monitor = PerformanceMonitor()
        
        # 创建测试市场数据
        self.test_market_data = self._create_test_market_data()
    
    def _create_test_market_data(self) -> dict:
        """创建测试市场数据"""
        # 牛市数据
        bull_market_prices = [100 + i * 0.5 + (i % 5) * 0.2 for i in range(60)]
        bull_market_volumes = [1000000 + i * 10000 for i in range(60)]
        
        # 熊市数据
        bear_market_prices = [100 - i * 0.3 - (i % 5) * 0.1 for i in range(60)]
        bear_market_volumes = [1000000 - i * 5000 for i in range(60)]
        
        # 震荡市数据
        sideways_market_prices = [100 + (i % 10) * 0.5 - 2.5 for i in range(60)]
        sideways_market_volumes = [1000000 + (i % 10) * 50000 - 250000 for i in range(60)]
        
        return {
            "bull": {
                "prices": bull_market_prices,
                "volumes": bull_market_volumes,
                "current_volume": bull_market_volumes[-1],
                "avg_volume": sum(bull_market_volumes) / len(bull_market_volumes),
                "advancing_stocks": 150,
                "declining_stocks": 50,
                "momentum": 0.03
            },
            "bear": {
                "prices": bear_market_prices,
                "volumes": bear_market_volumes,
                "current_volume": bear_market_volumes[-1],
                "avg_volume": sum(bear_market_volumes) / len(bear_market_volumes),
                "advancing_stocks": 30,
                "declining_stocks": 170,
                "momentum": -0.04
            },
            "sideways": {
                "prices": sideways_market_prices,
                "volumes": sideways_market_volumes,
                "current_volume": sideways_market_volumes[-1],
                "avg_volume": sum(sideways_market_volumes) / len(sideways_market_volumes),
                "advancing_stocks": 100,
                "declining_stocks": 100,
                "momentum": 0.001
            }
        }
    
    def test_trend_analysis(self):
        """测试趋势分析"""
        print("\n=== 测试趋势分析 ===")
        
        for market_type, data in self.test_market_data.items():
            print(f"\n{market_type.upper()}市场趋势分析:")
            
            # 趋势分析
            self.performance_monitor.start_timer("trend_analysis")
            trend_result = self.trend_analyzer.identify_trend(data["prices"])
            self.performance_monitor.end_timer("trend_analysis")
            
            print(f"  趋势方向: {trend_result['direction']}")
            print(f"  趋势强度: {trend_result['strength']:.3f}")
            print(f"  短期均线: {trend_result['short_ma']:.2f}" if trend_result['short_ma'] else "  短期均线: None")
            print(f"  中期均线: {trend_result['medium_ma']:.2f}" if trend_result['medium_ma'] else "  中期均线: None")
            print(f"  长期均线: {trend_result['long_ma']:.2f}" if trend_result['long_ma'] else "  长期均线: None")
            
            # 验证趋势分析结果
            self.assertIn('direction', trend_result, "应包含趋势方向")
            self.assertIn('strength', trend_result, "应包含趋势强度")
            self.assertIn(trend_result['direction'], ['bullish', 'bearish', 'sideways', 'undefined'], "趋势方向应为有效值")
            self.assertGreaterEqual(trend_result['strength'], 0.0, "趋势强度应大于等于0")
            self.assertLessEqual(trend_result['strength'], 1.0, "趋势强度应小于等于1")
            
            # 验证趋势识别的准确性
            if market_type == "bull":
                self.assertEqual(trend_result['direction'], 'bullish', "牛市应被识别为上涨趋势")
            elif market_type == "bear":
                self.assertEqual(trend_result['direction'], 'bearish', "熊市应被识别为下跌趋势")
            elif market_type == "sideways":
                self.assertIn(trend_result['direction'], ['sideways', 'undefined'], "震荡市应被识别为震荡趋势")
    
    def test_volatility_analysis(self):
        """测试波动率分析"""
        print("\n=== 测试波动率分析 ===")
        
        for market_type, data in self.test_market_data.items():
            print(f"\n{market_type.upper()}市场波动率分析:")
            
            # 波动率分析
            self.performance_monitor.start_timer("volatility_analysis")
            volatility_result = self.volatility_analyzer.analyze_volatility(data)
            self.performance_monitor.end_timer("volatility_analysis")
            
            print(f"  波动率水平: {volatility_result['level']}")
            print(f"  波动率得分: {volatility_result['score']:.3f}")
            print(f"  波动率值: {volatility_result['volatility']:.4f}")
            
            # 验证波动率分析结果
            self.assertIn('level', volatility_result, "应包含波动率水平")
            self.assertIn('score', volatility_result, "应包含波动率得分")
            self.assertIn('volatility', volatility_result, "应包含波动率值")
            self.assertIn(volatility_result['level'], ['low', 'medium', 'high', 'extreme', 'undefined'], "波动率水平应为有效值")
            self.assertGreaterEqual(volatility_result['score'], 0.0, "波动率得分应大于等于0")
            self.assertLessEqual(volatility_result['score'], 1.0, "波动率得分应小于等于1")
            self.assertGreaterEqual(volatility_result['volatility'], 0.0, "波动率值应大于等于0")
    
    def test_sentiment_analysis(self):
        """测试情绪分析"""
        print("\n=== 测试情绪分析 ===")
        
        for market_type, data in self.test_market_data.items():
            print(f"\n{market_type.upper()}市场情绪分析:")
            
            # 情绪分析
            self.performance_monitor.start_timer("sentiment_analysis")
            sentiment_score = self.sentiment_analyzer.calculate_overall_sentiment(data)
            self.performance_monitor.end_timer("sentiment_analysis")
            
            print(f"  综合情绪得分: {sentiment_score:.3f}")
            
            # 验证情绪分析结果
            self.assertGreaterEqual(sentiment_score, 0.0, "情绪得分应大于等于0")
            self.assertLessEqual(sentiment_score, 1.0, "情绪得分应小于等于1")
            
            # 验证情绪识别的合理性
            if market_type == "bull":
                self.assertGreater(sentiment_score, 0.5, "牛市情绪得分应较高")
            elif market_type == "bear":
                self.assertLess(sentiment_score, 0.5, "熊市情绪得分应较低")
    
    def test_market_environment_identification(self):
        """测试市场环境识别"""
        print("\n=== 测试市场环境识别 ===")
        
        for market_type, data in self.test_market_data.items():
            print(f"\n{market_type.upper()}市场环境识别:")
            
            # 市场环境识别
            self.performance_monitor.start_timer("environment_identification")
            environment = self.environment_identifier.identify_environment(data)
            self.performance_monitor.end_timer("environment_identification")
            
            print(f"  环境类型: {environment.environment_type.value}")
            print(f"  置信度: {environment.confidence:.3f}")
            print(f"  趋势方向: {environment.trend_direction}")
            print(f"  波动率水平: {environment.volatility_level}")
            print(f"  情绪得分: {environment.sentiment_score:.3f}")
            print(f"  识别时间: {environment.timestamp}")
            
            # 验证环境识别结果
            self.assertIsInstance(environment, MarketEnvironment, "应返回MarketEnvironment对象")
            self.assertIn(environment.environment_type, [MarketEnvironmentType.BULL, MarketEnvironmentType.BEAR, 
                                                 MarketEnvironmentType.SIDEWAYS, MarketEnvironmentType.UNDEFINED], 
                              "环境类型应为有效值")
            self.assertGreaterEqual(environment.confidence, 0.0, "置信度应大于等于0")
            self.assertLessEqual(environment.confidence, 1.0, "置信度应小于等于1")
            self.assertIn(environment.trend_direction, ['bullish', 'bearish', 'sideways', 'undefined'], "趋势方向应为有效值")
            self.assertIn(environment.volatility_level, ['low', 'medium', 'high', 'extreme', 'undefined'], "波动率水平应为有效值")
            self.assertGreaterEqual(environment.sentiment_score, 0.0, "情绪得分应大于等于0")
            self.assertLessEqual(environment.sentiment_score, 1.0, "情绪得分应小于等于1")
            self.assertIsNotNone(environment.timestamp, "时间戳不应为None")
            
            # 验证环境识别的准确性
            if market_type == "bull":
                self.assertEqual(environment.environment_type, MarketEnvironmentType.BULL, "牛市应被识别为牛市环境")
            elif market_type == "bear":
                self.assertEqual(environment.environment_type, MarketEnvironmentType.BEAR, "熊市应被识别为熊市环境")
            elif market_type == "sideways":
                self.assertIn(environment.environment_type, [MarketEnvironmentType.SIDEWAYS, MarketEnvironmentType.UNDEFINED], 
                              "震荡市应被识别为震荡市环境")
    
    def test_environment_change_detection(self):
        """测试环境变化检测"""
        print("\n=== 测试环境变化检测 ===")
        
        # 创建两个不同的市场环境
        bull_data = self.test_market_data["bull"]
        bear_data = self.test_market_data["bear"]
        
        # 识别两个环境
        bull_env = self.environment_identifier.identify_environment(bull_data)
        bear_env = self.environment_identifier.identify_environment(bear_data)
        
        # 检测环境变化
        has_changed = self.environment_identifier.detect_environment_change(bull_env, bear_env)
        
        print(f"牛市环境: {bull_env.environment_type.value}")
        print(f"熊市环境: {bear_env.environment_type.value}")
        print(f"环境是否变化: {has_changed}")
        
        # 验证变化检测
        self.assertTrue(has_changed, "牛市到熊市应被检测为环境变化")
        
        # 生成变化预警
        alert = self.environment_identifier.generate_change_alert(bull_env, bear_env)
        
        print(f"预警类型: {alert.alert_type}")
        print(f"预警消息: {alert.message}")
        print(f"预警时间: {alert.timestamp}")
        
        # 验证预警
        self.assertEqual(alert.alert_type, "market_change", "预警类型应为市场变化")
        self.assertEqual(alert.previous_environment, MarketEnvironmentType.BULL, "之前环境应为牛市")
        self.assertEqual(alert.current_environment, MarketEnvironmentType.BEAR, "当前环境应为熊市")
        self.assertGreater(len(alert.message), 0, "预警消息不应为空")
        self.assertIsNotNone(alert.timestamp, "预警时间不应为None")
    
    def test_environment_storage(self):
        """测试环境数据存储"""
        print("\n=== 测试环境数据存储 ===")
        
        # 创建存储实例
        storage = MarketEnvironmentStorage(self.test_data_dir)
        
        # 创建环境历史记录
        for market_type, data in self.test_market_data.items():
            environment = self.environment_identifier.identify_environment(data)
            
            history = MarketEnvironmentHistory(
                index_code="TEST_INDEX",
                environment=environment,
                raw_data=data,
                timestamp=environment.timestamp
            )
            
            # 保存记录
            success = storage.save_environment_record(history)
            self.assertTrue(success, f"环境记录保存应成功: {market_type}")
            
            print(f"已保存{market_type}市场环境记录")
        
        # 获取历史记录
        histories = storage.get_environment_history("TEST_INDEX", days=30)
        
        print(f"\n获取到 {len(histories)} 条历史记录")
        for history in histories:
            print(f"  {history.timestamp}: {history.environment.environment_type.value}")
        
        # 验证历史记录
        self.assertGreater(len(histories), 0, "应能获取到历史记录")
        self.assertEqual(len(histories), len(self.test_market_data), "历史记录数量应匹配")
        
        for history in histories:
            self.assertEqual(history.index_code, "TEST_INDEX", "指数代码应匹配")
            self.assertIsInstance(history.environment, MarketEnvironment, "环境应为MarketEnvironment对象")
            self.assertIsInstance(history.raw_data, dict, "原始数据应为字典")
            self.assertIsNotNone(history.timestamp, "时间戳不应为None")
    
    def test_environment_adaptive_scoring(self):
        """测试环境自适应评分"""
        print("\n=== 测试环境自适应评分 ===")
        
        # 创建测试股票
        test_stock = TestDataGenerator.create_test_stock("ADAPTIVE", "自适应测试股票", 10.0, 5.0, 15.0, 2.0)
        
        # 在不同市场环境下评分
        for market_type, data in self.test_market_data.items():
            environment = self.environment_identifier.identify_environment(data)
            
            print(f"\n{market_type.upper()}市场环境下的评分:")
            print(f"  环境类型: {environment.environment_type.value}")
            print(f"  置信度: {environment.confidence:.3f}")
            
            # 多因子评分
            multi_factor_score = self.multi_factor_scorer.calculate_score(test_stock)
            
            # 旧系统评分
            legacy_score = self.legacy_scorer.calculate_total_score(test_stock) / 100
            
            print(f"  多因子评分: {multi_factor_score:.3f}")
            print(f"  旧系统评分: {legacy_score:.3f}")
            
            # 验证评分
            self.assertGreaterEqual(multi_factor_score, 0.0, "多因子评分应大于等于0")
            self.assertLessEqual(multi_factor_score, 1.0, "多因子评分应小于等于1")
            self.assertGreaterEqual(legacy_score, 0.0, "旧系统评分应大于等于0")
            self.assertLessEqual(legacy_score, 1.0, "旧系统评分应小于等于1")
            
            # 验证评分一致性
            score_diff = abs(multi_factor_score - legacy_score)
            self.assertLessEqual(score_diff, 0.4, f"评分差异过大: {market_type}")
    
    def test_performance_benchmarks(self):
        """测试性能基准"""
        print("\n=== 测试性能基准 ===")
        
        # 大量市场数据
        large_prices = TestDataGenerator.create_test_price_history("LARGE", days=252)
        large_volumes = TestDataGenerator.create_test_volume_history(days=252)
        
        large_data = {
            "prices": large_prices,
            "volumes": large_volumes,
            "current_volume": large_volumes[-1],
            "avg_volume": sum(large_volumes) / len(large_volumes),
            "advancing_stocks": 150,
            "declining_stocks": 50,
            "momentum": 0.02
        }
        
        # 测试大数据量环境识别
        self.performance_monitor.start_timer("large_data_environment")
        large_env = self.environment_identifier.identify_environment(large_data)
        self.performance_monitor.end_timer("large_data_environment")
        
        print(f"\n大数据量性能测试结果:")
        print(f"  252日数据环境识别: {self.performance_monitor.get_metric('large_data_environment'):.4f}秒")
        print(f"  识别环境类型: {large_env.environment_type.value}")
        print(f"  置信度: {large_env.confidence:.3f}")
        
        # 验证大数据量处理
        self.assertIsNotNone(large_env, "大数据量环境识别结果不应为None")
        self.assertIsInstance(large_env, MarketEnvironment, "应返回MarketEnvironment对象")
        
        # 性能基准检查
        self.assert_performance_metric("large_data_environment", 
                                   self.performance_monitor.get_metric('large_data_environment'), 
                                   0.05, "大数据量环境识别性能")
    
    def tearDown(self):
        """测试后清理"""
        # 保存测试结果
        result_file = self.save_test_result()
        print(f"\n测试结果已保存到: {result_file}")
        
        super().tearDown()


if __name__ == '__main__':
    unittest.main()