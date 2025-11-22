"""
技术分析模块集成测试
验证技术分析模块与评分系统和监控系统的集成功能
"""

import sys
import os
import unittest
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from tests.integration.test_framework import IntegrationTestBase, TestDataGenerator, PerformanceMonitor
from src.buffett.strategies.technical_analysis import (
    TechnicalSignalGenerator, MovingAverage, RSI, MACD, BollingerBands,
    VolumePriceAnalyzer, TechnicalAnalysisResult
)
from src.buffett.core.multi_factor_scoring import (
    MultiFactorScorer, TechnicalFactor, DividendFactor, ValueFactor
)
from src.buffett.core.scoring import InvestmentScorer
from src.buffett.models.stock import StockInfo


class TestTechnicalAnalysisIntegration(IntegrationTestBase):
    """技术分析模块集成测试"""
    
    def setUp(self):
        """测试前准备"""
        super().setUp()
        
        # 创建测试股票数据
        self.test_stocks = [
            TestDataGenerator.create_test_stock("STOCK1", "股票1", 10.0, 6.0, 12.0, 1.5),
            TestDataGenerator.create_test_stock("STOCK2", "股票2", 15.0, 4.0, 18.0, 2.0),
            TestDataGenerator.create_test_stock("STOCK3", "股票3", 8.0, 8.0, 8.0, 0.8)
        ]
        
        # 创建价格和成交量历史数据
        self.price_histories = {}
        self.volume_histories = {}
        
        for stock in self.test_stocks:
            self.price_histories[stock.code] = TestDataGenerator.create_test_price_history(
                stock.code, days=60, base_price=stock.price
            )
            self.volume_histories[stock.code] = TestDataGenerator.create_test_volume_history(days=60)
        
        # 创建技术分析器
        self.signal_generator = TechnicalSignalGenerator()
        self.volume_analyzer = VolumePriceAnalyzer()
        
        # 创建评分器
        self.multi_factor_scorer = MultiFactorScorer.with_default_factors()
        self.legacy_scorer = InvestmentScorer()
        
        # 性能监控器
        self.performance_monitor = PerformanceMonitor()
    
    def test_technical_indicators_calculation(self):
        """测试技术指标计算"""
        print("\n=== 测试技术指标计算 ===")
        
        # 测试移动平均线
        ma = MovingAverage(period=20)
        prices = self.price_histories["STOCK1"]
        
        self.performance_monitor.start_timer("ma_calculation")
        ma_value = ma.calculate(prices)
        self.performance_monitor.end_timer("ma_calculation")
        
        self.assertIsNotNone(ma_value, "移动平均线计算结果不应为None")
        self.assertGreater(ma_value, 0, "移动平均线值应大于0")
        print(f"20日移动平均线: {ma_value:.2f}")
        
        # 测试RSI
        rsi = RSI(period=14)
        
        self.performance_monitor.start_timer("rsi_calculation")
        rsi_value = rsi.calculate(prices)
        self.performance_monitor.end_timer("rsi_calculation")
        
        self.assertIsNotNone(rsi_value, "RSI计算结果不应为None")
        self.assertGreaterEqual(rsi_value, 0, "RSI值应大于等于0")
        self.assertLessEqual(rsi_value, 100, "RSI值应小于等于100")
        print(f"RSI(14): {rsi_value:.2f}")
        
        # 测试MACD
        macd = MACD()
        
        self.performance_monitor.start_timer("macd_calculation")
        macd_result = macd.calculate(prices)
        self.performance_monitor.end_timer("macd_calculation")
        
        self.assertIsNotNone(macd_result, "MACD计算结果不应为None")
        self.assertEqual(len(macd_result), 3, "MACD应返回3个值")
        macd_line, signal_line, histogram = macd_result
        print(f"MACD: 线={macd_line:.4f}, 信号线={signal_line:.4f}, 柱状图={histogram:.4f}")
        
        # 测试布林带
        bb = BollingerBands(period=20)
        
        self.performance_monitor.start_timer("bb_calculation")
        bb_result = bb.calculate(prices)
        self.performance_monitor.end_timer("bb_calculation")
        
        self.assertIsNotNone(bb_result, "布林带计算结果不应为None")
        self.assertEqual(len(bb_result), 3, "布林带应返回3个值")
        upper_band, middle_band, lower_band = bb_result
        print(f"布林带: 上轨={upper_band:.2f}, 中轨={middle_band:.2f}, 下轨={lower_band:.2f}")
        
        # 验证布林带关系
        self.assertGreater(upper_band, middle_band, "布林带上轨应大于中轨")
        self.assertGreater(middle_band, lower_band, "布林带中轨应大于下轨")
    
    def test_technical_signal_generation(self):
        """测试技术信号生成"""
        print("\n=== 测试技术信号生成 ===")
        
        for stock in self.test_stocks:
            prices = self.price_histories[stock.code]
            volumes = self.volume_histories[stock.code]
            
            # 生成技术信号
            self.performance_monitor.start_timer("signal_generation")
            signals = self.signal_generator.generate_signals(prices, volumes)
            self.performance_monitor.end_timer("signal_generation")
            
            print(f"\n股票 {stock.code} 的技术信号:")
            print(f"  买入信号数量: {len(signals['buy_signals'])}")
            print(f"  卖出信号数量: {len(signals['sell_signals'])}")
            print(f"  中性信号数量: {len(signals['neutral_signals'])}")
            
            # 验证信号结构
            self.assertIn('buy_signals', signals, "应包含买入信号")
            self.assertIn('sell_signals', signals, "应包含卖出信号")
            self.assertIn('neutral_signals', signals, "应包含中性信号")
            
            # 验证信号内容
            for signal in signals['buy_signals']:
                self.assertIn('indicator', signal, "买入信号应包含指标名称")
                self.assertIn('strength', signal, "买入信号应包含强度")
                self.assertGreater(signal['strength'], 0, "买入信号强度应大于0")
                self.assertLessEqual(signal['strength'], 1, "买入信号强度应小于等于1")
            
            for signal in signals['sell_signals']:
                self.assertIn('indicator', signal, "卖出信号应包含指标名称")
                self.assertIn('strength', signal, "卖出信号应包含强度")
                self.assertGreater(signal['strength'], 0, "卖出信号强度应大于0")
                self.assertLessEqual(signal['strength'], 1, "卖出信号强度应小于等于1")
            
            # 计算信号强度
            signal_strength = self.signal_generator.calculate_signal_strength(prices, volumes)
            print(f"  综合信号强度: {signal_strength:.3f}")
            
            self.assertGreaterEqual(signal_strength, -1.0, "信号强度应大于等于-1")
            self.assertLessEqual(signal_strength, 1.0, "信号强度应小于等于1")
    
    def test_volume_price_analysis(self):
        """测试量价分析"""
        print("\n=== 测试量价分析 ===")
        
        for stock in self.test_stocks:
            prices = self.price_histories[stock.code]
            volumes = self.volume_histories[stock.code]
            
            # 趋势分析
            self.performance_monitor.start_timer("trend_analysis")
            trend_result = self.volume_analyzer.analyze_trend(prices, volumes)
            self.performance_monitor.end_timer("trend_analysis")
            
            print(f"\n股票 {stock.code} 的量价分析:")
            print(f"  价格趋势: {trend_result['price_trend']}")
            print(f"  成交量趋势: {trend_result['volume_trend']}")
            print(f"  相关性: {trend_result['correlation']:.3f}")
            
            # 验证趋势分析结果
            self.assertIn('price_trend', trend_result, "应包含价格趋势")
            self.assertIn('volume_trend', trend_result, "应包含成交量趋势")
            self.assertIn('correlation', trend_result, "应包含相关性")
            self.assertIn(trend_result['price_trend'], ['up', 'down', 'sideways', 'unknown'], "价格趋势应为有效值")
            self.assertIn(trend_result['volume_trend'], ['increasing', 'decreasing', 'stable', 'unknown'], "成交量趋势应为有效值")
            self.assertGreaterEqual(trend_result['correlation'], -1.0, "相关性应大于等于-1")
            self.assertLessEqual(trend_result['correlation'], 1.0, "相关性应小于等于1")
            
            # 成交量异常检测
            self.performance_monitor.start_timer("volume_spike_detection")
            spikes = self.volume_analyzer.detect_volume_spikes(volumes)
            self.performance_monitor.end_timer("volume_spike_detection")
            
            print(f"  成交量异常点: {spikes}")
            
            # 验证异常检测结果
            self.assertIsInstance(spikes, list, "异常检测结果应为列表")
            for spike in spikes:
                self.assertIsInstance(spike, int, "异常点应为整数索引")
                self.assertGreaterEqual(spike, 0, "异常点索引应大于等于0")
                self.assertLess(spike, len(volumes), "异常点索引应小于数据长度")
            
            # 背离检测
            self.performance_monitor.start_timer("divergence_detection")
            divergence = self.volume_analyzer.detect_divergence(prices, volumes)
            self.performance_monitor.end_timer("divergence_detection")
            
            print(f"  看涨背离: {divergence['bullish_divergence']}")
            print(f"  看跌背离: {divergence['bearish_divergence']}")
            
            # 验证背离检测结果
            self.assertIn('bullish_divergence', divergence, "应包含看涨背离")
            self.assertIn('bearish_divergence', divergence, "应包含看跌背离")
            self.assertIsInstance(divergence['bullish_divergence'], list, "看涨背离应为列表")
            self.assertIsInstance(divergence['bearish_divergence'], list, "看跌背离应为列表")
    
    def test_technical_factor_integration(self):
        """测试技术因子与多因子评分系统的集成"""
        print("\n=== 测试技术因子与多因子评分系统的集成 ===")
        
        # 创建包含技术因子的评分器
        tech_scorer = MultiFactorScorer()
        tech_scorer.add_factor(TechnicalFactor(weight=0.3))
        tech_scorer.add_factor(DividendFactor(weight=0.4))
        tech_scorer.add_factor(ValueFactor(weight=0.3))
        
        for stock in self.test_stocks:
            # 计算技术因子得分
            technical_factor = TechnicalFactor()
            self.performance_monitor.start_timer("technical_factor_calculation")
            tech_score = technical_factor.calculate(stock)
            self.performance_monitor.end_timer("technical_factor_calculation")
            
            print(f"\n股票 {stock.code}:")
            print(f"  技术因子得分: {tech_score:.3f}")
            
            # 验证技术因子得分
            self.assertGreaterEqual(tech_score, 0.0, "技术因子得分应大于等于0")
            self.assertLessEqual(tech_score, 1.0, "技术因子得分应小于等于1")
            
            # 计算综合评分
            self.performance_monitor.start_timer("integrated_scoring")
            integrated_score = tech_scorer.calculate_score(stock)
            self.performance_monitor.end_timer("integrated_scoring")
            
            print(f"  综合评分: {integrated_score:.3f}")
            
            # 验证综合评分
            self.assertGreaterEqual(integrated_score, 0.0, "综合评分应大于等于0")
            self.assertLessEqual(integrated_score, 1.0, "综合评分应小于等于1")
            
            # 与旧系统比较
            legacy_score = self.legacy_scorer.calculate_total_score(stock) / 100
            print(f"  旧系统评分: {legacy_score:.3f}")
            
            # 验证评分趋势一致性
            score_diff = abs(integrated_score - legacy_score)
            self.assertLessEqual(score_diff, 0.4, f"评分差异过大: {stock.code}")
    
    def test_technical_analysis_result_format(self):
        """测试技术分析结果格式"""
        print("\n=== 测试技术分析结果格式 ===")
        
        for stock in self.test_stocks:
            prices = self.price_histories[stock.code]
            volumes = self.volume_histories[stock.code]
            
            # 生成技术分析结果
            signals = self.signal_generator.generate_signals(prices, volumes)
            signal_strength = self.signal_generator.calculate_signal_strength(prices, volumes)
            
            # 创建技术分析结果
            result = TechnicalAnalysisResult(
                symbol=stock.code,
                timestamp=self.test_results["start_time"],
                indicators={
                    "ma": MovingAverage().calculate(prices),
                    "rsi": RSI().calculate(prices),
                    "macd": MACD().calculate(prices),
                    "bb": BollingerBands().calculate(prices)
                },
                signals=signals,
                score=signal_strength
            )
            
            print(f"\n股票 {stock.code} 的技术分析结果:")
            print(f"  符号: {result.symbol}")
            print(f"  时间戳: {result.timestamp}")
            print(f"  信号强度: {result.score:.3f}")
            
            # 验证结果格式
            self.assertEqual(result.symbol, stock.code, "符号应匹配")
            self.assertIsNotNone(result.timestamp, "时间戳不应为None")
            self.assertIsInstance(result.indicators, dict, "指标应为字典")
            self.assertIsInstance(result.signals, dict, "信号应为字典")
            self.assertIsInstance(result.score, float, "评分应为浮点数")
            
            # 测试转换为字典
            result_dict = result.to_dict()
            self.assertIn('symbol', result_dict, "转换后的字典应包含符号")
            self.assertIn('timestamp', result_dict, "转换后的字典应包含时间戳")
            self.assertIn('indicators', result_dict, "转换后的字典应包含指标")
            self.assertIn('signals', result_dict, "转换后的字典应包含信号")
            self.assertIn('score', result_dict, "转换后的字典应包含评分")
    
    def test_performance_benchmarks(self):
        """测试性能基准"""
        print("\n=== 测试性能基准 ===")
        
        # 大量数据处理测试
        large_prices = TestDataGenerator.create_test_price_history("LARGE", days=252)
        large_volumes = TestDataGenerator.create_test_volume_history(days=252)
        
        # 测试大数据量的技术指标计算
        self.performance_monitor.start_timer("large_data_ma")
        ma_value = MovingAverage(period=50).calculate(large_prices)
        self.performance_monitor.end_timer("large_data_ma")
        
        self.performance_monitor.start_timer("large_data_rsi")
        rsi_value = RSI(period=14).calculate(large_prices)
        self.performance_monitor.end_timer("large_data_rsi")
        
        self.performance_monitor.start_timer("large_data_macd")
        macd_value = MACD().calculate(large_prices)
        self.performance_monitor.end_timer("large_data_macd")
        
        self.performance_monitor.start_timer("large_data_signals")
        signals = self.signal_generator.generate_signals(large_prices, large_volumes)
        self.performance_monitor.end_timer("large_data_signals")
        
        print(f"\n大数据量性能测试结果:")
        print(f"  252日数据移动平均线计算: {self.performance_monitor.get_metric('large_data_ma'):.4f}秒")
        print(f"  252日数据RSI计算: {self.performance_monitor.get_metric('large_data_rsi'):.4f}秒")
        print(f"  252日数据MACD计算: {self.performance_monitor.get_metric('large_data_macd'):.4f}秒")
        print(f"  252日数据信号生成: {self.performance_monitor.get_metric('large_data_signals'):.4f}秒")
        
        # 验证计算结果
        self.assertIsNotNone(ma_value, "大数据量移动平均线计算结果不应为None")
        self.assertIsNotNone(rsi_value, "大数据量RSI计算结果不应为None")
        self.assertIsNotNone(macd_value, "大数据量MACD计算结果不应为None")
        self.assertIsNotNone(signals, "大数据量信号生成结果不应为None")
        
        # 性能基准检查
        self.assert_performance_metric("large_data_ma", 
                                   self.performance_monitor.get_metric('large_data_ma'), 
                                   0.01, "大数据量移动平均线计算性能")
        self.assert_performance_metric("large_data_rsi", 
                                   self.performance_monitor.get_metric('large_data_rsi'), 
                                   0.01, "大数据量RSI计算性能")
        self.assert_performance_metric("large_data_signals", 
                                   self.performance_monitor.get_metric('large_data_signals'), 
                                   0.02, "大数据量信号生成性能")
    
    def tearDown(self):
        """测试后清理"""
        # 保存测试结果
        result_file = self.save_test_result()
        print(f"\n测试结果已保存到: {result_file}")
        
        super().tearDown()


if __name__ == '__main__':
    unittest.main()