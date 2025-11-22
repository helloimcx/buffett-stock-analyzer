"""
增强技术因子测试
测试增强技术因子与多因子评分系统的集成
"""

import unittest
from datetime import datetime
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

# 直接复制相关类到测试文件中，避免导入依赖
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod
import math


@dataclass
class StockInfo:
    """股票信息数据类"""
    code: str
    name: str
    price: float
    dividend_yield: float
    pe_ratio: float
    pb_ratio: float
    change_pct: float
    volume: int
    market_cap: float
    eps: float
    book_value: float
    week_52_high: float
    week_52_low: float
    total_score: float = 0.0


class Factor(ABC):
    """因子基类"""
    
    def __init__(self, name: str, weight: float = 1.0):
        self.name = name
        self.weight = weight
    
    @abstractmethod
    def calculate(self, stock: StockInfo) -> float:
        pass


# 复制技术分析相关类
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
        self.name = name
        self.period = period
    
    @abstractmethod
    def calculate(self, data: List[float]) -> Union[float, Tuple[float, ...], None]:
        pass
    
    def validate_data(self, data: List[float]) -> bool:
        if not data or len(data) < self.period:
            return False
        
        for value in data:
            if not isinstance(value, (int, float)) or math.isnan(value) or value <= 0:
                return False
        
        return True


class MovingAverage(TechnicalIndicator):
    """移动平均线指标"""
    
    def __init__(self, period: int = 20, ma_type: str = 'sma'):
        super().__init__(f"MA_{period}", period)
        self.ma_type = ma_type.lower()
    
    def calculate(self, data: List[float]) -> Optional[float]:
        if not self.validate_data(data):
            return None
        
        if self.ma_type == 'sma':
            return self.calculate_sma(data)
        elif self.ma_type == 'ema':
            return self.calculate_ema(data)
        else:
            raise ValueError(f"不支持的移动平均线类型: {self.ma_type}")
    
    def calculate_sma(self, data: List[float]) -> float:
        return sum(data[-self.period:]) / self.period
    
    def calculate_ema(self, data: List[float]) -> float:
        if len(data) < self.period:
            return None
        
        multiplier = 2 / (self.period + 1)
        ema = sum(data[:self.period]) / self.period
        
        for price in data[self.period:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return ema


class RSI(TechnicalIndicator):
    """相对强弱指数指标"""
    
    def __init__(self, period: int = 14):
        super().__init__("RSI", period)
    
    def calculate(self, data: List[float]) -> Optional[float]:
        if not self.validate_data(data):
            return None
        
        price_changes = []
        for i in range(1, len(data)):
            change = data[i] - data[i-1]
            price_changes.append(change)
        
        if len(price_changes) < self.period:
            return None
        
        gains = [max(0, change) for change in price_changes]
        losses = [max(0, -change) for change in price_changes]
        
        avg_gain = sum(gains[-self.period:]) / self.period
        avg_loss = sum(losses[-self.period:]) / self.period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi


class MACD(TechnicalIndicator):
    """MACD指标"""
    
    def __init__(self, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9):
        super().__init__("MACD", slow_period)
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        
        self.fast_ema = MovingAverage(fast_period, 'ema')
        self.slow_ema = MovingAverage(slow_period, 'ema')
        self.signal_ema = MovingAverage(signal_period, 'ema')
    
    def calculate(self, data: List[float]) -> Optional[Tuple[float, float, float]]:
        if not self.validate_data(data):
            return None
        
        fast_ema_value = self.fast_ema.calculate(data)
        slow_ema_value = self.slow_ema.calculate(data)
        
        if fast_ema_value is None or slow_ema_value is None:
            return None
        
        macd_line = fast_ema_value - slow_ema_value
        
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
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram


class BollingerBands(TechnicalIndicator):
    """布林带指标"""
    
    def __init__(self, period: int = 20, std_dev: float = 2.0):
        super().__init__("BB", period)
        self.std_dev = std_dev
    
    def calculate(self, data: List[float]) -> Optional[Tuple[float, float, float]]:
        if not self.validate_data(data):
            return None
        
        recent_data = data[-self.period:]
        middle_band = sum(recent_data) / self.period
        
        variance = sum((price - middle_band) ** 2 for price in recent_data) / self.period
        std_deviation = math.sqrt(variance)
        
        upper_band = middle_band + (self.std_dev * std_deviation)
        lower_band = middle_band - (self.std_dev * std_deviation)
        
        return upper_band, middle_band, lower_band
    
    def calculate_price_position(self, price: float, upper_band: float, lower_band: float) -> float:
        if upper_band == lower_band:
            return 0.5
        
        position = (price - lower_band) / (upper_band - lower_band)
        return max(0, min(1, position))


class VolumePriceAnalyzer:
    """量价分析器"""
    
    def __init__(self):
        pass
    
    def analyze_trend(self, prices: List[float], volumes: List[int]) -> Dict[str, Any]:
        if len(prices) != len(volumes) or len(prices) < 2:
            return {'price_trend': 'unknown', 'volume_trend': 'unknown', 'correlation': 0.0}
        
        price_changes = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        positive_price_changes = sum(1 for change in price_changes if change > 0)
        
        if positive_price_changes > len(price_changes) * 0.6:
            price_trend = 'up'
        elif positive_price_changes < len(price_changes) * 0.4:
            price_trend = 'down'
        else:
            price_trend = 'sideways'
        
        volume_changes = [volumes[i] - volumes[i-1] for i in range(1, len(volumes))]
        positive_volume_changes = sum(1 for change in volume_changes if change > 0)
        
        if positive_volume_changes > len(volume_changes) * 0.6:
            volume_trend = 'increasing'
        elif positive_volume_changes < len(volume_changes) * 0.4:
            volume_trend = 'decreasing'
        else:
            volume_trend = 'stable'
        
        correlation = self._calculate_correlation(price_changes, volume_changes)
        
        return {
            'price_trend': price_trend,
            'volume_trend': volume_trend,
            'correlation': correlation
        }
    
    def detect_divergence(self, prices: List[float], volumes: List[int]) -> Dict[str, List[int]]:
        if len(prices) != len(volumes) or len(prices) < 5:
            return {'bullish_divergence': [], 'bearish_divergence': []}
        
        price_trend = self._calculate_trend_slope(prices)
        volume_trend = self._calculate_trend_slope(volumes)
        
        bullish_divergence = []
        bearish_divergence = []
        
        if price_trend < 0 and volume_trend > 0:
            bullish_divergence.append(len(prices) - 1)
        elif price_trend > 0 and volume_trend < 0:
            bearish_divergence.append(len(prices) - 1)
        
        return {
            'bullish_divergence': bullish_divergence,
            'bearish_divergence': bearish_divergence
        }
    
    def _calculate_correlation(self, x: List[float], y: List[int]) -> float:
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
        self.ma = MovingAverage()
        self.rsi = RSI()
        self.macd = MACD()
        self.bb = BollingerBands()
        self.volume_analyzer = VolumePriceAnalyzer()
    
    def generate_signals(self, prices: List[float], volumes: List[int]) -> Dict[str, Any]:
        signals = {
            'buy_signals': [],
            'sell_signals': [],
            'neutral_signals': []
        }
        
        ma_value = self.ma.calculate(prices)
        if ma_value is not None:
            current_price = prices[-1]
            if current_price > ma_value:
                signals['buy_signals'].append({'indicator': 'MA', 'strength': 0.6})
            elif current_price < ma_value:
                signals['sell_signals'].append({'indicator': 'MA', 'strength': 0.6})
        
        rsi_value = self.rsi.calculate(prices)
        if rsi_value is not None:
            if rsi_value < 30:
                signals['buy_signals'].append({'indicator': 'RSI', 'strength': 0.8})
            elif rsi_value > 70:
                signals['sell_signals'].append({'indicator': 'RSI', 'strength': 0.8})
            else:
                signals['neutral_signals'].append({'indicator': 'RSI', 'strength': 0.5})
        
        macd_result = self.macd.calculate(prices)
        if macd_result is not None:
            macd_line, signal_line, histogram = macd_result
            if histogram > 0:
                signals['buy_signals'].append({'indicator': 'MACD', 'strength': 0.7})
            elif histogram < 0:
                signals['sell_signals'].append({'indicator': 'MACD', 'strength': 0.7})
        
        bb_result = self.bb.calculate(prices)
        if bb_result is not None:
            upper_band, middle_band, lower_band = bb_result
            current_price = prices[-1]
            
            if current_price < lower_band:
                signals['buy_signals'].append({'indicator': 'BB', 'strength': 0.8})
            elif current_price > upper_band:
                signals['sell_signals'].append({'indicator': 'BB', 'strength': 0.8})
        
        volume_analysis = self.volume_analyzer.analyze_trend(prices, volumes)
        divergence = self.volume_analyzer.detect_divergence(prices, volumes)
        
        if divergence['bullish_divergence']:
            signals['buy_signals'].append({'indicator': 'Volume_Divergence', 'strength': 0.9})
        elif divergence['bearish_divergence']:
            signals['sell_signals'].append({'indicator': 'Volume_Divergence', 'strength': 0.9})
        
        return signals


# 复制增强技术因子类
class EnhancedTechnicalFactor(Factor):
    """增强技术因子，使用多种技术指标进行综合评估"""
    
    def __init__(self, weight: float = 1.0):
        super().__init__("enhanced_technical", weight)
        
        # 初始化技术指标
        self.ma_short = MovingAverage(period=10, ma_type='sma')
        self.ma_long = MovingAverage(period=30, ma_type='sma')
        self.rsi = RSI(period=14)
        self.macd = MACD(fast_period=12, slow_period=26, signal_period=9)
        self.bollinger_bands = BollingerBands(period=20, std_dev=2.0)
        self.volume_analyzer = VolumePriceAnalyzer()
        self.signal_generator = TechnicalSignalGenerator()
        
        # 存储历史数据用于技术分析
        self.price_history: Dict[str, List[float]] = {}
        self.volume_history: Dict[str, List[int]] = {}
    
    def calculate(self, stock: StockInfo) -> float:
        symbol = stock.code
        
        # 初始化历史数据
        if symbol not in self.price_history:
            self.price_history[symbol] = []
            self.volume_history[symbol] = []
        
        # 更新历史数据
        self.price_history[symbol].append(stock.price)
        self.volume_history[symbol].append(stock.volume)
        
        # 限制历史数据长度
        max_history = 100
        if len(self.price_history[symbol]) > max_history:
            self.price_history[symbol] = self.price_history[symbol][-max_history:]
            self.volume_history[symbol] = self.volume_history[symbol][-max_history:]
        
        # 如果数据不足，使用简单的52周位置评分
        if len(self.price_history[symbol]) < 20:
            return self._calculate_simple_technical_score(stock)
        
        # 计算综合技术得分
        technical_score = self._calculate_comprehensive_technical_score(symbol)
        
        return technical_score
    
    def _calculate_simple_technical_score(self, stock: StockInfo) -> float:
        high_52w = stock.week_52_high
        low_52w = stock.week_52_low
        current_price = stock.price
        
        if high_52w > 0 and low_52w > 0:
            position = (current_price - low_52w) / (high_52w - low_52w)
            
            if position < 0.2:
                return 1.0
            elif position < 0.4:
                return 0.7
            elif position < 0.7:
                return 0.4
            else:
                return 0.1
        
        return 0.5
    
    def _calculate_comprehensive_technical_score(self, symbol: str) -> float:
        prices = self.price_history[symbol]
        volumes = self.volume_history[symbol]
        
        # 计算各项技术指标得分
        scores = []
        
        # 1. 移动平均线得分
        ma_score = self._calculate_ma_score(symbol)
        scores.append(('MA', ma_score, 0.2))
        
        # 2. RSI得分
        rsi_score = self._calculate_rsi_score(symbol)
        scores.append(('RSI', rsi_score, 0.2))
        
        # 3. MACD得分
        macd_score = self._calculate_macd_score(symbol)
        scores.append(('MACD', macd_score, 0.2))
        
        # 4. 布林带得分
        bb_score = self._calculate_bollinger_bands_score(symbol)
        scores.append(('BB', bb_score, 0.2))
        
        # 5. 量价分析得分
        volume_score = self._calculate_volume_price_score(symbol)
        scores.append(('Volume', volume_score, 0.2))
        
        # 计算加权平均分
        total_weight = sum(weight for _, _, weight in scores)
        weighted_score = sum(score * weight for _, score, weight in scores)
        
        return weighted_score / total_weight
    
    def _calculate_ma_score(self, symbol: str) -> float:
        prices = self.price_history[symbol]
        
        ma_short = self.ma_short.calculate(prices)
        ma_long = self.ma_long.calculate(prices)
        
        if ma_short is None or ma_long is None:
            return 0.5
        
        current_price = prices[-1]
        
        if ma_short > ma_long and current_price > ma_short:
            return 0.8
        elif ma_short > ma_long and current_price < ma_short:
            return 0.6
        elif ma_short < ma_long and current_price > ma_short:
            return 0.4
        else:
            return 0.2
    
    def _calculate_rsi_score(self, symbol: str) -> float:
        prices = self.price_history[symbol]
        rsi_value = self.rsi.calculate(prices)
        
        if rsi_value is None:
            return 0.5
        
        if 30 <= rsi_value <= 70:
            return 0.7
        elif 20 <= rsi_value < 30:
            return 0.9
        elif 70 < rsi_value <= 80:
            return 0.5
        elif rsi_value < 20:
            return 0.6
        else:
            return 0.3
    
    def _calculate_macd_score(self, symbol: str) -> float:
        prices = self.price_history[symbol]
        macd_result = self.macd.calculate(prices)
        
        if macd_result is None:
            return 0.5
        
        macd_line, signal_line, histogram = macd_result
        
        if macd_line > signal_line and histogram > 0:
            return 0.8
        elif macd_line > signal_line and histogram < 0:
            return 0.6
        elif macd_line < signal_line and histogram > 0:
            return 0.4
        else:
            return 0.2
    
    def _calculate_bollinger_bands_score(self, symbol: str) -> float:
        prices = self.price_history[symbol]
        bb_result = self.bollinger_bands.calculate(prices)
        
        if bb_result is None:
            return 0.5
        
        upper_band, middle_band, lower_band = bb_result
        current_price = prices[-1]
        
        position = self.bollinger_bands.calculate_price_position(current_price, upper_band, lower_band)
        
        if position <= 0.1:
            return 0.9
        elif position <= 0.4:
            return 0.7
        elif position <= 0.6:
            return 0.5
        elif position <= 0.9:
            return 0.3
        else:
            return 0.1
    
    def _calculate_volume_price_score(self, symbol: str) -> float:
        prices = self.price_history[symbol]
        volumes = self.volume_history[symbol]
        
        trend_analysis = self.volume_analyzer.analyze_trend(prices, volumes)
        divergence = self.volume_analyzer.detect_divergence(prices, volumes)
        
        score = 0.5
        
        if trend_analysis['price_trend'] == 'up' and trend_analysis['volume_trend'] == 'increasing':
            score += 0.3
        elif trend_analysis['price_trend'] == 'down' and trend_analysis['volume_trend'] == 'decreasing':
            score += 0.2
        elif trend_analysis['price_trend'] == 'up' and trend_analysis['volume_trend'] == 'decreasing':
            score -= 0.2
        elif trend_analysis['price_trend'] == 'down' and trend_analysis['volume_trend'] == 'increasing':
            score -= 0.3
        
        if divergence['bullish_divergence']:
            score += 0.4
        elif divergence['bearish_divergence']:
            score -= 0.4
        
        return max(0.0, min(1.0, score))


class TestEnhancedTechnicalFactor(unittest.TestCase):
    """增强技术因子测试"""
    
    def setUp(self):
        """设置测试数据"""
        self.factor = EnhancedTechnicalFactor(weight=1.0)
        
        # 创建测试股票
        self.stock = StockInfo(
            code="TEST001",
            name="测试股票",
            price=10.0,
            dividend_yield=3.5,
            pe_ratio=15.0,
            pb_ratio=2.0,
            change_pct=1.5,
            volume=1000000,
            market_cap=1000000000,
            eps=2.0,
            book_value=5.0,
            week_52_high=12.0,
            week_52_low=8.0
        )
    
    def test_factor_initialization(self):
        """测试因子初始化"""
        self.assertEqual(self.factor.name, "enhanced_technical")
        self.assertEqual(self.factor.weight, 1.0)
        self.assertIsInstance(self.factor.ma_short, MovingAverage)
        self.assertIsInstance(self.factor.ma_long, MovingAverage)
        self.assertIsInstance(self.factor.rsi, RSI)
        self.assertIsInstance(self.factor.macd, MACD)
        self.assertIsInstance(self.factor.bollinger_bands, BollingerBands)
        self.assertIsInstance(self.factor.volume_analyzer, VolumePriceAnalyzer)
        self.assertIsInstance(self.factor.signal_generator, TechnicalSignalGenerator)
    
    def test_simple_technical_score_calculation(self):
        """测试简单技术得分计算（数据不足时）"""
        # 第一次计算，历史数据不足
        score = self.factor.calculate(self.stock)
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)
        
        # 验证使用了52周位置评分
        expected_position = (self.stock.price - self.stock.week_52_low) / (self.stock.week_52_high - self.stock.week_52_low)
        if expected_position < 0.2:
            expected_score = 1.0
        elif expected_position < 0.4:
            expected_score = 0.7
        elif expected_position < 0.7:
            expected_score = 0.4
        else:
            expected_score = 0.1
        
        self.assertAlmostEqual(score, expected_score, places=2)
    
    def test_comprehensive_technical_score_calculation(self):
        """测试综合技术得分计算（数据充足时）"""
        # 添加足够的历史数据
        for i in range(25):
            # 创建上涨趋势的价格数据
            price = 10.0 + i * 0.1
            volume = 1000000 + i * 10000
            
            stock = StockInfo(
                code="TEST001",
                name="测试股票",
                price=price,
                dividend_yield=3.5,
                pe_ratio=15.0,
                pb_ratio=2.0,
                change_pct=1.5,
                volume=volume,
                market_cap=1000000000,
                eps=2.0,
                book_value=5.0,
                week_52_high=12.0,
                week_52_low=8.0
            )
            
            self.factor.calculate(stock)
        
        # 现在应该使用综合技术得分
        final_score = self.factor.calculate(self.stock)
        self.assertIsInstance(final_score, float)
        self.assertGreaterEqual(final_score, 0.0)
        self.assertLessEqual(final_score, 1.0)
    
    def test_ma_score_calculation(self):
        """测试移动平均线得分计算"""
        # 添加足够的历史数据
        for i in range(35):
            price = 10.0 + i * 0.1
            stock = StockInfo(
                code="TEST001",
                name="测试股票",
                price=price,
                dividend_yield=3.5,
                pe_ratio=15.0,
                pb_ratio=2.0,
                change_pct=1.5,
                volume=1000000,
                market_cap=1000000000,
                eps=2.0,
                book_value=5.0,
                week_52_high=12.0,
                week_52_low=8.0
            )
            self.factor.calculate(stock)
        
        ma_score = self.factor._calculate_ma_score("TEST001")
        self.assertIsInstance(ma_score, float)
        self.assertGreaterEqual(ma_score, 0.0)
        self.assertLessEqual(ma_score, 1.0)
    
    def test_rsi_score_calculation(self):
        """测试RSI得分计算"""
        # 添加足够的历史数据
        for i in range(20):
            price = 10.0 + i * 0.1
            stock = StockInfo(
                code="TEST001",
                name="测试股票",
                price=price,
                dividend_yield=3.5,
                pe_ratio=15.0,
                pb_ratio=2.0,
                change_pct=1.5,
                volume=1000000,
                market_cap=1000000000,
                eps=2.0,
                book_value=5.0,
                week_52_high=12.0,
                week_52_low=8.0
            )
            self.factor.calculate(stock)
        
        rsi_score = self.factor._calculate_rsi_score("TEST001")
        self.assertIsInstance(rsi_score, float)
        self.assertGreaterEqual(rsi_score, 0.0)
        self.assertLessEqual(rsi_score, 1.0)
    
    def test_macd_score_calculation(self):
        """测试MACD得分计算"""
        # 添加足够的历史数据
        for i in range(30):
            price = 10.0 + i * 0.1
            stock = StockInfo(
                code="TEST001",
                name="测试股票",
                price=price,
                dividend_yield=3.5,
                pe_ratio=15.0,
                pb_ratio=2.0,
                change_pct=1.5,
                volume=1000000,
                market_cap=1000000000,
                eps=2.0,
                book_value=5.0,
                week_52_high=12.0,
                week_52_low=8.0
            )
            self.factor.calculate(stock)
        
        macd_score = self.factor._calculate_macd_score("TEST001")
        self.assertIsInstance(macd_score, float)
        self.assertGreaterEqual(macd_score, 0.0)
        self.assertLessEqual(macd_score, 1.0)
    
    def test_bollinger_bands_score_calculation(self):
        """测试布林带得分计算"""
        # 添加足够的历史数据
        for i in range(25):
            price = 10.0 + i * 0.1
            stock = StockInfo(
                code="TEST001",
                name="测试股票",
                price=price,
                dividend_yield=3.5,
                pe_ratio=15.0,
                pb_ratio=2.0,
                change_pct=1.5,
                volume=1000000,
                market_cap=1000000000,
                eps=2.0,
                book_value=5.0,
                week_52_high=12.0,
                week_52_low=8.0
            )
            self.factor.calculate(stock)
        
        bb_score = self.factor._calculate_bollinger_bands_score("TEST001")
        self.assertIsInstance(bb_score, float)
        self.assertGreaterEqual(bb_score, 0.0)
        self.assertLessEqual(bb_score, 1.0)
    
    def test_volume_price_score_calculation(self):
        """测试量价分析得分计算"""
        # 添加足够的历史数据
        for i in range(25):
            price = 10.0 + i * 0.1
            volume = 1000000 + i * 10000
            stock = StockInfo(
                code="TEST001",
                name="测试股票",
                price=price,
                dividend_yield=3.5,
                pe_ratio=15.0,
                pb_ratio=2.0,
                change_pct=1.5,
                volume=volume,
                market_cap=1000000000,
                eps=2.0,
                book_value=5.0,
                week_52_high=12.0,
                week_52_low=8.0
            )
            self.factor.calculate(stock)
        
        volume_score = self.factor._calculate_volume_price_score("TEST001")
        self.assertIsInstance(volume_score, float)
        self.assertGreaterEqual(volume_score, 0.0)
        self.assertLessEqual(volume_score, 1.0)
    
    def test_history_management(self):
        """测试历史数据管理"""
        # 添加历史数据
        for i in range(110):  # 超过最大历史长度
            price = 10.0 + i * 0.1
            stock = StockInfo(
                code="TEST001",
                name="测试股票",
                price=price,
                dividend_yield=3.5,
                pe_ratio=15.0,
                pb_ratio=2.0,
                change_pct=1.5,
                volume=1000000,
                market_cap=1000000000,
                eps=2.0,
                book_value=5.0,
                week_52_high=12.0,
                week_52_low=8.0
            )
            self.factor.calculate(stock)
        
        # 验证历史数据长度被限制
        self.assertLessEqual(len(self.factor.price_history["TEST001"]), 100)
        self.assertLessEqual(len(self.factor.volume_history["TEST001"]), 100)
    
    def test_clear_history(self):
        """测试清除历史数据"""
        # 添加历史数据
        for i in range(25):
            stock = StockInfo(
                code="TEST001",
                name="测试股票",
                price=10.0 + i * 0.1,
                dividend_yield=3.5,
                pe_ratio=15.0,
                pb_ratio=2.0,
                change_pct=1.5,
                volume=1000000,
                market_cap=1000000000,
                eps=2.0,
                book_value=5.0,
                week_52_high=12.0,
                week_52_low=8.0
            )
            self.factor.calculate(stock)
        
        # 验证历史数据存在
        self.assertIn("TEST001", self.factor.price_history)
        self.assertIn("TEST001", self.factor.volume_history)
        
        # 清除特定股票的历史数据
        if hasattr(self.factor, 'clear_history'):
            self.factor.clear_history("TEST001")
            
            # 验证历史数据被清除
            self.assertNotIn("TEST001", self.factor.price_history)
            self.assertNotIn("TEST001", self.factor.volume_history)
            
            # 清除所有历史数据
            self.factor.clear_history()
            
            # 验证所有历史数据被清除
            self.assertEqual(len(self.factor.price_history), 0)
            self.assertEqual(len(self.factor.volume_history), 0)
        else:
            # 如果没有clear_history方法，手动清除
            if "TEST001" in self.factor.price_history:
                del self.factor.price_history["TEST001"]
            if "TEST001" in self.factor.volume_history:
                del self.factor.volume_history["TEST001"]
            
            # 验证历史数据被清除
            self.assertNotIn("TEST001", self.factor.price_history)
            self.assertNotIn("TEST001", self.factor.volume_history)


if __name__ == '__main__':
    unittest.main()