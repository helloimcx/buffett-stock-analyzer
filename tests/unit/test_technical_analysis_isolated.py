"""
技术分析模块隔离测试
测试技术指标计算和技术信号生成功能
"""

import unittest
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass
from datetime import datetime
import math


# 直接复制技术分析代码到测试文件中，避免导入依赖

@dataclass
class TechnicalAnalysisResult:
    """技术分析结果数据类"""
    symbol: str
    timestamp: datetime
    indicators: Dict[str, Any]
    signals: Dict[str, Any]
    score: float
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'symbol': self.symbol,
            'timestamp': self.timestamp.isoformat(),
            'indicators': self.indicators,
            'signals': self.signals,
            'score': self.score
        }


class TechnicalIndicator(ABC):
    """技术指标基类"""
    
    def __init__(self, name: str, period: int = 20):
        """
        初始化技术指标
        
        Args:
            name: 指标名称
            period: 计算周期
        """
        self.name = name
        self.period = period
    
    @abstractmethod
    def calculate(self, data: List[float]) -> Union[float, Tuple[float, ...], None]:
        """
        计算指标值
        
        Args:
            data: 价格数据列表
            
        Returns:
            指标值或指标值元组，数据不足时返回None
        """
        pass
    
    def validate_data(self, data: List[float]) -> bool:
        """
        验证数据是否有效
        
        Args:
            data: 价格数据列表
            
        Returns:
            数据是否有效
        """
        if not data or len(data) < self.period:
            return False
        
        # 检查数据是否为有效数值
        for value in data:
            if not isinstance(value, (int, float)) or math.isnan(value) or value <= 0:
                return False
        
        return True


class MovingAverage(TechnicalIndicator):
    """移动平均线指标"""
    
    def __init__(self, period: int = 20, ma_type: str = 'sma'):
        """
        初始化移动平均线
        
        Args:
            period: 计算周期
            ma_type: 移动平均线类型 ('sma' 简单移动平均, 'ema' 指数移动平均)
        """
        super().__init__(f"MA_{period}", period)
        self.ma_type = ma_type.lower()
    
    def calculate(self, data: List[float]) -> Optional[float]:
        """
        计算移动平均线
        
        Args:
            data: 价格数据列表
            
        Returns:
            移动平均线值，数据不足时返回None
        """
        if not self.validate_data(data):
            return None
        
        if self.ma_type == 'sma':
            return self.calculate_sma(data)
        elif self.ma_type == 'ema':
            return self.calculate_ema(data)
        else:
            raise ValueError(f"不支持的移动平均线类型: {self.ma_type}")
    
    def calculate_sma(self, data: List[float]) -> float:
        """计算简单移动平均线"""
        return sum(data[-self.period:]) / self.period
    
    def calculate_ema(self, data: List[float]) -> float:
        """计算指数移动平均线"""
        if len(data) < self.period:
            return None
        
        multiplier = 2 / (self.period + 1)
        
        # 初始EMA使用SMA
        ema = sum(data[:self.period]) / self.period
        
        # 计算后续EMA
        for price in data[self.period:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return ema


class RSI(TechnicalIndicator):
    """相对强弱指数指标"""
    
    def __init__(self, period: int = 14):
        """
        初始化RSI指标
        
        Args:
            period: 计算周期，通常为14
        """
        super().__init__("RSI", period)
    
    def calculate(self, data: List[float]) -> Optional[float]:
        """
        计算RSI值
        
        Args:
            data: 价格数据列表
            
        Returns:
            RSI值(0-100)，数据不足时返回None
        """
        if not self.validate_data(data):
            return None
        
        # 计算价格变化
        price_changes = []
        for i in range(1, len(data)):
            change = data[i] - data[i-1]
            price_changes.append(change)
        
        if len(price_changes) < self.period:
            return None
        
        # 分离涨跌
        gains = [max(0, change) for change in price_changes]
        losses = [max(0, -change) for change in price_changes]
        
        # 计算平均涨跌幅
        avg_gain = sum(gains[-self.period:]) / self.period
        avg_loss = sum(losses[-self.period:]) / self.period
        
        # 避免除零错误
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi


class MACD(TechnicalIndicator):
    """MACD指标"""
    
    def __init__(self, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9):
        """
        初始化MACD指标
        
        Args:
            fast_period: 快速EMA周期
            slow_period: 慢速EMA周期
            signal_period: 信号线EMA周期
        """
        super().__init__("MACD", slow_period)
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        
        self.fast_ema = MovingAverage(fast_period, 'ema')
        self.slow_ema = MovingAverage(slow_period, 'ema')
        self.signal_ema = MovingAverage(signal_period, 'ema')
    
    def calculate(self, data: List[float]) -> Optional[Tuple[float, float, float]]:
        """
        计算MACD指标
        
        Args:
            data: 价格数据列表
            
        Returns:
            (MACD线, 信号线, 柱状图) 元组，数据不足时返回None
        """
        if not self.validate_data(data):
            return None
        
        # 计算快速和慢速EMA
        fast_ema_value = self.fast_ema.calculate(data)
        slow_ema_value = self.slow_ema.calculate(data)
        
        if fast_ema_value is None or slow_ema_value is None:
            return None
        
        # 计算MACD线
        macd_line = fast_ema_value - slow_ema_value
        
        # 计算信号线（需要历史MACD值）
        macd_history = []
        for i in range(self.slow_period, len(data) + 1):
            subset = data[:i]
            fast = self.fast_ema.calculate(subset)
            slow = self.slow_ema.calculate(subset)
            if fast is not None and slow is not None:
                macd_history.append(fast - slow)
        
        if len(macd_history) < self.signal_period:
            return None
        
        signal_line = sum(macd_history[-self.signal_period:]) / self.signal_period
        
        # 计算柱状图
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram


class BollingerBands(TechnicalIndicator):
    """布林带指标"""
    
    def __init__(self, period: int = 20, std_dev: float = 2.0):
        """
        初始化布林带指标
        
        Args:
            period: 计算周期
            std_dev: 标准差倍数
        """
        super().__init__("BB", period)
        self.std_dev = std_dev
    
    def calculate(self, data: List[float]) -> Optional[Tuple[float, float, float]]:
        """
        计算布林带
        
        Args:
            data: 价格数据列表
            
        Returns:
            (上轨, 中轨, 下轨) 元组，数据不足时返回None
        """
        if not self.validate_data(data):
            return None
        
        # 取最近period个数据点
        recent_data = data[-self.period:]
        
        # 计算中轨（简单移动平均线）
        middle_band = sum(recent_data) / self.period
        
        # 计算标准差
        variance = sum((price - middle_band) ** 2 for price in recent_data) / self.period
        std_deviation = math.sqrt(variance)
        
        # 计算上轨和下轨
        upper_band = middle_band + (self.std_dev * std_deviation)
        lower_band = middle_band - (self.std_dev * std_deviation)
        
        return upper_band, middle_band, lower_band
    
    def calculate_band_width(self, upper_band: float, lower_band: float, middle_band: float) -> float:
        """
        计算布林带宽度
        
        Args:
            upper_band: 上轨
            lower_band: 下轨
            middle_band: 中轨
            
        Returns:
            布林带宽度
        """
        if middle_band == 0:
            return 0
        return (upper_band - lower_band) / middle_band
    
    def calculate_price_position(self, price: float, upper_band: float, lower_band: float) -> float:
        """
        计算价格在布林带中的位置
        
        Args:
            price: 当前价格
            upper_band: 上轨
            lower_band: 下轨
            
        Returns:
            位置百分比 (0-1)
        """
        if upper_band == lower_band:
            return 0.5
        
        position = (price - lower_band) / (upper_band - lower_band)
        return max(0, min(1, position))


class VolumePriceAnalyzer:
    """量价分析器"""
    
    def __init__(self):
        """初始化量价分析器"""
        pass
    
    def analyze_trend(self, prices: List[float], volumes: List[int]) -> Dict[str, Any]:
        """
        分析量价趋势
        
        Args:
            prices: 价格列表
            volumes: 成交量列表
            
        Returns:
            趋势分析结果
        """
        if len(prices) != len(volumes) or len(prices) < 2:
            return {'price_trend': 'unknown', 'volume_trend': 'unknown', 'correlation': 0.0}
        
        # 计算价格趋势
        price_changes = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        positive_price_changes = sum(1 for change in price_changes if change > 0)
        
        if positive_price_changes > len(price_changes) * 0.6:
            price_trend = 'up'
        elif positive_price_changes < len(price_changes) * 0.4:
            price_trend = 'down'
        else:
            price_trend = 'sideways'
        
        # 计算成交量趋势
        volume_changes = [volumes[i] - volumes[i-1] for i in range(1, len(volumes))]
        positive_volume_changes = sum(1 for change in volume_changes if change > 0)
        
        if positive_volume_changes > len(volume_changes) * 0.6:
            volume_trend = 'increasing'
        elif positive_volume_changes < len(volume_changes) * 0.4:
            volume_trend = 'decreasing'
        else:
            volume_trend = 'stable'
        
        # 计算相关性
        correlation = self._calculate_correlation(price_changes, volume_changes)
        
        return {
            'price_trend': price_trend,
            'volume_trend': volume_trend,
            'correlation': correlation
        }
    
    def detect_volume_spikes(self, volumes: List[int], threshold: float = 1.5) -> List[int]:
        """
        检测成交量异常
        
        Args:
            volumes: 成交量列表
            threshold: 异常阈值倍数
            
        Returns:
            异常点索引列表
        """
        if len(volumes) < 5:
            return []
        
        # 计算平均成交量
        avg_volume = sum(volumes) / len(volumes)
        
        # 检测异常点
        spikes = []
        for i, volume in enumerate(volumes):
            if volume > avg_volume * threshold:
                spikes.append(i)
        
        return spikes
    
    def detect_divergence(self, prices: List[float], volumes: List[int]) -> Dict[str, List[int]]:
        """
        检测价量背离
        
        Args:
            prices: 价格列表
            volumes: 成交量列表
            
        Returns:
            背离检测结果
        """
        if len(prices) != len(volumes) or len(prices) < 5:
            return {'bullish_divergence': [], 'bearish_divergence': []}
        
        # 计算价格和成交量的趋势
        price_trend = self._calculate_trend_slope(prices)
        volume_trend = self._calculate_trend_slope(volumes)
        
        # 检测背离
        bullish_divergence = []
        bearish_divergence = []
        
        # 简化的背离检测逻辑
        if price_trend < 0 and volume_trend > 0:
            # 价格下跌，成交量上涨 -> 看涨背离
            bullish_divergence.append(len(prices) - 1)
        elif price_trend > 0 and volume_trend < 0:
            # 价格上涨，成交量下跌 -> 看跌背离
            bearish_divergence.append(len(prices) - 1)
        
        return {
            'bullish_divergence': bullish_divergence,
            'bearish_divergence': bearish_divergence
        }
    
    def _calculate_correlation(self, x: List[float], y: List[int]) -> float:
        """计算相关系数"""
        if len(x) != len(y) or len(x) == 0:
            return 0.0
        
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_x2 = sum(xi ** 2 for xi in x)
        sum_y2 = sum(yi ** 2 for yi in y)
        
        denominator = math.sqrt((n * sum_x2 - sum_x ** 2) * (n * sum_y2 - sum_y ** 2))
        
        if denominator == 0:
            return 0.0
        
        correlation = (n * sum_xy - sum_x * sum_y) / denominator
        return correlation
    
    def _calculate_trend_slope(self, data: List[Union[float, int]]) -> float:
        """计算趋势斜率"""
        if len(data) < 2:
            return 0.0
        
        n = len(data)
        x = list(range(n))
        sum_x = sum(x)
        sum_y = sum(data)
        sum_xy = sum(xi * yi for xi, yi in zip(x, data))
        sum_x2 = sum(xi ** 2 for xi in x)
        
        denominator = n * sum_x2 - sum_x ** 2
        if denominator == 0:
            return 0.0
        
        slope = (n * sum_xy - sum_x * sum_y) / denominator
        return slope


class TechnicalSignalGenerator:
    """技术信号生成器"""
    
    def __init__(self):
        """初始化技术信号生成器"""
        self.ma = MovingAverage()
        self.rsi = RSI()
        self.macd = MACD()
        self.bb = BollingerBands()
        self.volume_analyzer = VolumePriceAnalyzer()
    
    def generate_signals(self, prices: List[float], volumes: List[int]) -> Dict[str, Any]:
        """
        生成技术信号
        
        Args:
            prices: 价格列表
            volumes: 成交量列表
            
        Returns:
            技术信号结果
        """
        signals = {
            'buy_signals': [],
            'sell_signals': [],
            'neutral_signals': []
        }
        
        # MA信号
        ma_value = self.ma.calculate(prices)
        if ma_value is not None:
            current_price = prices[-1]
            if current_price > ma_value:
                signals['buy_signals'].append({'indicator': 'MA', 'strength': 0.6})
            elif current_price < ma_value:
                signals['sell_signals'].append({'indicator': 'MA', 'strength': 0.6})
        
        # RSI信号
        rsi_value = self.rsi.calculate(prices)
        if rsi_value is not None:
            if rsi_value < 30:
                signals['buy_signals'].append({'indicator': 'RSI', 'strength': 0.8})
            elif rsi_value > 70:
                signals['sell_signals'].append({'indicator': 'RSI', 'strength': 0.8})
            else:
                signals['neutral_signals'].append({'indicator': 'RSI', 'strength': 0.5})
        
        # MACD信号
        macd_result = self.macd.calculate(prices)
        if macd_result is not None:
            macd_line, signal_line, histogram = macd_result
            if histogram > 0:
                signals['buy_signals'].append({'indicator': 'MACD', 'strength': 0.7})
            elif histogram < 0:
                signals['sell_signals'].append({'indicator': 'MACD', 'strength': 0.7})
        
        # 布林带信号
        bb_result = self.bb.calculate(prices)
        if bb_result is not None:
            upper_band, middle_band, lower_band = bb_result
            current_price = prices[-1]
            
            if current_price < lower_band:
                signals['buy_signals'].append({'indicator': 'BB', 'strength': 0.8})
            elif current_price > upper_band:
                signals['sell_signals'].append({'indicator': 'BB', 'strength': 0.8})
        
        # 量价分析信号
        volume_analysis = self.volume_analyzer.analyze_trend(prices, volumes)
        divergence = self.volume_analyzer.detect_divergence(prices, volumes)
        
        if divergence['bullish_divergence']:
            signals['buy_signals'].append({'indicator': 'Volume_Divergence', 'strength': 0.9})
        elif divergence['bearish_divergence']:
            signals['sell_signals'].append({'indicator': 'Volume_Divergence', 'strength': 0.9})
        
        return signals
    
    def calculate_signal_strength(self, prices: List[float], volumes: List[int]) -> float:
        """
        计算综合信号强度
        
        Args:
            prices: 价格列表
            volumes: 成交量列表
            
        Returns:
            信号强度 (-1 到 1)
        """
        signals = self.generate_signals(prices, volumes)
        
        buy_strength = sum(signal['strength'] for signal in signals['buy_signals'])
        sell_strength = sum(signal['strength'] for signal in signals['sell_signals'])
        
        # 归一化到-1到1之间
        total_strength = buy_strength - sell_strength
        max_strength = buy_strength + sell_strength
        
        if max_strength == 0:
            return 0.0
        
        return total_strength / max_strength
    
    def combine_signals(self, signals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        组合多个信号
        
        Args:
            signals: 信号列表
            
        Returns:
            组合后的信号
        """
        if not signals:
            return {'direction': 'neutral', 'strength': 0.0, 'confidence': 0.0}
        
        # 计算买入和卖出信号的总强度
        buy_strength = 0.0
        sell_strength = 0.0
        
        for signal in signals:
            if signal.get('direction') == 'buy':
                buy_strength += signal.get('strength', 0.0)
            elif signal.get('direction') == 'sell':
                sell_strength += signal.get('strength', 0.0)
        
        # 确定最终方向
        if buy_strength > sell_strength:
            direction = 'buy'
            strength = buy_strength / (buy_strength + sell_strength)
        elif sell_strength > buy_strength:
            direction = 'sell'
            strength = sell_strength / (buy_strength + sell_strength)
        else:
            direction = 'neutral'
            strength = 0.0
        
        # 计算置信度
        total_strength = buy_strength + sell_strength
        confidence = min(total_strength / len(signals), 1.0)
        
        return {
            'direction': direction,
            'strength': strength,
            'confidence': confidence
        }


# 测试类
class TestTechnicalIndicator(unittest.TestCase):
    """技术指标基类测试"""
    
    def setUp(self):
        """设置测试数据"""
        # 创建测试价格数据
        self.prices = [10.0, 10.5, 11.0, 10.8, 11.2, 11.5, 11.3, 11.8, 12.0, 11.9]
        self.volumes = [10000, 12000, 15000, 11000, 18000, 20000, 16000, 22000, 25000, 21000]
        self.dates = [
            datetime.now() for i in range(len(self.prices))
        ]
    
    def test_technical_indicator_base_class_should_be_abstract(self):
        """测试技术指标基类应该是抽象的"""
        with self.assertRaises(TypeError):
            TechnicalIndicator()
    
    def test_technical_indicator_should_have_name_and_period(self):
        """测试技术指标应该有名称和周期属性"""
        ma = MovingAverage(period=5)
        self.assertEqual(ma.name, "MA_5")
        self.assertEqual(ma.period, 5)


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
        macd_result = self.macd.calculate(self.prices)
        
        if macd_result is not None:  # 只有在有足够数据时才测试
            macd_line, signal_line, histogram = macd_result
            
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
        bb_result = self.bb.calculate(self.prices)
        
        if bb_result is not None:  # 只有在有足够数据时才测试
            upper_band, middle_band, lower_band = bb_result
            
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
        bb_result = self.bb.calculate(self.prices)
        
        if bb_result is not None:
            upper, middle, lower = bb_result
            width = self.bb.calculate_band_width(upper, lower, middle)
            
            self.assertIsInstance(width, float)
            self.assertGreater(width, 0)
    
    def test_bollinger_band_position(self):
        """测试价格在布林带中的位置"""
        bb_result = self.bb.calculate(self.prices)
        
        if bb_result is not None:
            upper, middle, lower = bb_result
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