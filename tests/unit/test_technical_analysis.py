"""
技术分析模块测试
测试技术指标计算和技术信号生成功能
"""

import unittest
from unittest.mock import Mock, patch
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

# 导入待测试的模块
from src.buffett.strategies.technical_analysis import (
    TechnicalIndicator,
    MovingAverage,
    RSI,
    MACD,
    BollingerBands,
    VolumePriceAnalyzer,
    TechnicalSignalGenerator,
    TechnicalAnalysisResult
)


class TestTechnicalIndicator(unittest.TestCase):
    """技术指标基类测试"""
    
    def setUp(self):
        """设置测试数据"""
        # 创建测试价格数据
        self.prices = [10.0, 10.5, 11.0, 10.8, 11.2, 11.5, 11.3, 11.8, 12.0, 11.9]
        self.volumes = [10000, 12000, 15000, 11000, 18000, 20000, 16000, 22000, 25000, 21000]
        self.dates = [
            datetime.now() - timedelta(days=i) for i in range(len(self.prices)-1, -1, -1)
        ]
    
    def test_technical_indicator_base_class_should_be_abstract(self):
        """测试技术指标基类应该是抽象的"""
        with self.assertRaises(TypeError):
            TechnicalIndicator()
    
    def test_technical_indicator_should_have_name_and_period(self):
        """测试技术指标应该有名称和周期属性"""
        # 这个测试将在实现具体指标时验证
        pass


class TestMovingAverage(unittest.TestCase):
    """移动平均线指标测试"""
    
    def setUp(self):
        """设置测试数据"""
        self.prices = [10.0, 10.5, 11.0, 10.8, 11.2, 11.5, 11.3, 11.8, 12.0, 11.9]
        self.ma = MovingAverage(period=5)
    
    def test_sma_calculation(self):
        """测试简单移动平均线计算"""
        # 测试SMA计算
        expected_sma = sum(self.prices[-5:]) / 5
        calculated_sma = self.ma.calculate_sma(self.prices)
        self.assertAlmostEqual(calculated_sma, expected_sma, places=4)
    
    def test_ema_calculation(self):
        """测试指数移动平均线计算"""
        # 测试EMA计算
        ema = self.ma.calculate_ema(self.prices)
        self.assertIsInstance(ema, float)
        self.assertGreater(ema, 0)
    
    def test_ma_with_insufficient_data(self):
        """测试数据不足时的移动平均线计算"""
        short_prices = [10.0, 11.0]  # 少于period
        result = self.ma.calculate(short_prices)
        self.assertIsNone(result)
    
    def test_ma_with_valid_data(self):
        """测试有效数据时的移动平均线计算"""
        result = self.ma.calculate(self.prices)
        self.assertIsInstance(result, float)
        self.assertGreater(result, 0)


class TestRSI(unittest.TestCase):
    """RSI指标测试"""
    
    def setUp(self):
        """设置测试数据"""
        # 创建有涨有跌的价格数据
        self.prices = [
            10.0, 10.5, 10.3, 10.8, 10.6, 11.0, 10.9, 11.2, 11.5, 11.3, 
            11.8, 11.6, 12.0, 11.9, 12.2, 12.5, 12.3, 12.8, 12.6, 13.0
        ]
        self.rsi = RSI(period=14)
    
    def test_rsi_calculation(self):
        """测试RSI计算"""
        rsi_value = self.rsi.calculate(self.prices)
        self.assertIsInstance(rsi_value, float)
        self.assertGreaterEqual(rsi_value, 0)
        self.assertLessEqual(rsi_value, 100)
    
    def test_rsi_with_insufficient_data(self):
        """测试数据不足时的RSI计算"""
        short_prices = [10.0, 11.0, 10.5]  # 少于period
        result = self.rsi.calculate(short_prices)
        self.assertIsNone(result)
    
    def test_rsi_overbought_oversold(self):
        """测试RSI超买超卖信号"""
        # 创建持续上涨的价格数据（应该产生高RSI）
        rising_prices = [10.0 + i * 0.1 for i in range(20)]
        rsi_value = self.rsi.calculate(rising_prices)
        self.assertGreater(rsi_value, 70)  # 超买区域
        
        # 创建持续下跌的价格数据（应该产生低RSI）
        falling_prices = [10.0 - i * 0.1 for i in range(20)]
        rsi_value = self.rsi.calculate(falling_prices)
        self.assertLess(rsi_value, 30)  # 超卖区域


class TestMACD(unittest.TestCase):
    """MACD指标测试"""
    
    def setUp(self):
        """设置测试数据"""
        # 创建足够长的价格数据用于MACD计算
        self.prices = [
            10.0, 10.2, 10.1, 10.3, 10.5, 10.4, 10.6, 10.8, 10.7, 10.9,
            11.0, 10.9, 11.1, 11.2, 11.0, 11.3, 11.4, 11.2, 11.5, 11.6,
            11.4, 11.7, 11.8, 11.6, 11.9, 12.0, 11.8, 12.1, 12.2, 12.0
        ]
        self.macd = MACD(fast_period=12, slow_period=26, signal_period=9)
    
    def test_macd_calculation(self):
        """测试MACD计算"""
        macd_line, signal_line, histogram = self.macd.calculate(self.prices)
        
        self.assertIsInstance(macd_line, float)
        self.assertIsInstance(signal_line, float)
        self.assertIsInstance(histogram, float)
        
        # 验证histogram = macd_line - signal_line
        self.assertAlmostEqual(histogram, macd_line - signal_line, places=4)
    
    def test_macd_with_insufficient_data(self):
        """测试数据不足时的MACD计算"""
        short_prices = [10.0, 11.0, 10.5]  # 少于slow_period
        result = self.macd.calculate(short_prices)
        self.assertIsNone(result)
    
    def test_macd_signal_generation(self):
        """测试MACD信号生成"""
        # 这个测试将在实现信号生成功能时完善
        pass


class TestBollingerBands(unittest.TestCase):
    """布林带指标测试"""
    
    def setUp(self):
        """设置测试数据"""
        self.prices = [
            10.0, 10.2, 10.1, 10.3, 10.5, 10.4, 10.6, 10.8, 10.7, 10.9,
            11.0, 10.9, 11.1, 11.2, 11.0, 11.3, 11.4, 11.2, 11.5, 11.6
        ]
        self.bb = BollingerBands(period=20, std_dev=2.0)
    
    def test_bollinger_bands_calculation(self):
        """测试布林带计算"""
        upper_band, middle_band, lower_band = self.bb.calculate(self.prices)
        
        self.assertIsInstance(upper_band, float)
        self.assertIsInstance(middle_band, float)
        self.assertIsInstance(lower_band, float)
        
        # 验证上轨 > 中轨 > 下轨
        self.assertGreater(upper_band, middle_band)
        self.assertGreater(middle_band, lower_band)
    
    def test_bollinger_bands_with_insufficient_data(self):
        """测试数据不足时的布林带计算"""
        short_prices = [10.0, 11.0, 10.5]  # 少于period
        result = self.bb.calculate(short_prices)
        self.assertIsNone(result)
    
    def test_bollinger_band_width(self):
        """测试布林带宽度计算"""
        upper, middle, lower = self.bb.calculate(self.prices)
        width = self.bb.calculate_band_width(upper, lower, middle)
        
        self.assertIsInstance(width, float)
        self.assertGreater(width, 0)
    
    def test_bollinger_band_position(self):
        """测试价格在布林带中的位置"""
        upper, middle, lower = self.bb.calculate(self.prices)
        current_price = self.prices[-1]
        position = self.bb.calculate_price_position(current_price, upper, lower)
        
        self.assertIsInstance(position, float)
        self.assertGreaterEqual(position, 0)
        self.assertLessEqual(position, 1)


class TestVolumePriceAnalyzer(unittest.TestCase):
    """量价分析测试"""
    
    def setUp(self):
        """设置测试数据"""
        self.prices = [10.0, 10.5, 11.0, 10.8, 11.2, 11.5, 11.3, 11.8, 12.0, 11.9]
        self.volumes = [10000, 12000, 15000, 11000, 18000, 20000, 16000, 22000, 25000, 21000]
        self.analyzer = VolumePriceAnalyzer()
    
    def test_volume_price_trend(self):
        """测试量价趋势分析"""
        trend = self.analyzer.analyze_trend(self.prices, self.volumes)
        self.assertIsInstance(trend, dict)
        self.assertIn('price_trend', trend)
        self.assertIn('volume_trend', trend)
        self.assertIn('correlation', trend)
    
    def test_volume_spike_detection(self):
        """测试成交量异常检测"""
        spikes = self.analyzer.detect_volume_spikes(self.volumes)
        self.assertIsInstance(spikes, list)
        
        # 验证检测到的异常点确实有较高的成交量
        avg_volume = sum(self.volumes) / len(self.volumes)
        for spike in spikes:
            self.assertGreater(self.volumes[spike], avg_volume * 1.5)
    
    def test_price_volume_divergence(self):
        """测试价量背离分析"""
        divergence = self.analyzer.detect_divergence(self.prices, self.volumes)
        self.assertIsInstance(divergence, dict)
        self.assertIn('bullish_divergence', divergence)
        self.assertIn('bearish_divergence', divergence)


class TestTechnicalSignalGenerator(unittest.TestCase):
    """技术信号生成器测试"""
    
    def setUp(self):
        """设置测试数据"""
        self.prices = [
            10.0, 10.2, 10.1, 10.3, 10.5, 10.4, 10.6, 10.8, 10.7, 10.9,
            11.0, 10.9, 11.1, 11.2, 11.0, 11.3, 11.4, 11.2, 11.5, 11.6,
            11.4, 11.7, 11.8, 11.6, 11.9, 12.0, 11.8, 12.1, 12.2, 12.0
        ]
        self.volumes = [10000 + i * 1000 for i in range(len(self.prices))]
        self.generator = TechnicalSignalGenerator()
    
    def test_signal_generation(self):
        """测试信号生成"""
        signals = self.generator.generate_signals(self.prices, self.volumes)
        self.assertIsInstance(signals, dict)
        self.assertIn('buy_signals', signals)
        self.assertIn('sell_signals', signals)
        self.assertIn('neutral_signals', signals)
    
    def test_signal_strength_calculation(self):
        """测试信号强度计算"""
        strength = self.generator.calculate_signal_strength(self.prices, self.volumes)
        self.assertIsInstance(strength, float)
        self.assertGreaterEqual(strength, -1)
        self.assertLessEqual(strength, 1)
    
    def test_signal_combination(self):
        """测试多指标信号组合"""
        ma_signal = {'direction': 'buy', 'strength': 0.7}
        rsi_signal = {'direction': 'buy', 'strength': 0.8}
        macd_signal = {'direction': 'sell', 'strength': 0.6}
        
        combined = self.generator.combine_signals([ma_signal, rsi_signal, macd_signal])
        self.assertIsInstance(combined, dict)
        self.assertIn('direction', combined)
        self.assertIn('strength', combined)
        self.assertIn('confidence', combined)


class TestTechnicalAnalysisResult(unittest.TestCase):
    """技术分析结果测试"""
    
    def test_result_creation(self):
        """测试结果创建"""
        result = TechnicalAnalysisResult(
            symbol='TEST',
            timestamp=datetime.now(),
            indicators={},
            signals={},
            score=0.75
        )
        
        self.assertEqual(result.symbol, 'TEST')
        self.assertIsInstance(result.timestamp, datetime)
        self.assertIsInstance(result.indicators, dict)
        self.assertIsInstance(result.signals, dict)
        self.assertIsInstance(result.score, float)
    
    def test_result_to_dict(self):
        """测试结果转换为字典"""
        result = TechnicalAnalysisResult(
            symbol='TEST',
            timestamp=datetime.now(),
            indicators={'MA': 11.5},
            signals={'buy': True},
            score=0.75
        )
        
        result_dict = result.to_dict()
        self.assertIsInstance(result_dict, dict)
        self.assertEqual(result_dict['symbol'], 'TEST')
        self.assertIn('timestamp', result_dict)
        self.assertIn('indicators', result_dict)
        self.assertIn('signals', result_dict)
        self.assertIn('score', result_dict)


if __name__ == '__main__':
    unittest.main()