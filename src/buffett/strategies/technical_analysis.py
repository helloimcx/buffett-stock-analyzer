"""
技术分析模块
实现各种技术指标计算和技术信号生成功能
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass
from datetime import datetime
import math


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