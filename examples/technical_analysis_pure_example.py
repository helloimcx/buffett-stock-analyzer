"""
技术分析模块纯示例
展示技术分析功能的核心逻辑，不依赖任何其他模块
"""

import math
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, field


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


class MovingAverage:
    """移动平均线指标"""
    
    def __init__(self, period: int = 20, ma_type: str = 'sma'):
        self.period = period
        self.ma_type = ma_type.lower()
    
    def calculate(self, data: List[float]) -> Optional[float]:
        """计算移动平均线"""
        if not data or len(data) < self.period:
            return None
        
        if self.ma_type == 'sma':
            return sum(data[-self.period:]) / self.period
        elif self.ma_type == 'ema':
            return self._calculate_ema(data)
        else:
            raise ValueError(f"不支持的移动平均线类型: {self.ma_type}")
    
    def _calculate_ema(self, data: List[float]) -> float:
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


class RSI:
    """相对强弱指数指标"""
    
    def __init__(self, period: int = 14):
        self.period = period
    
    def calculate(self, data: List[float]) -> Optional[float]:
        """计算RSI值"""
        if not data or len(data) < self.period + 1:
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


class MACD:
    """MACD指标"""
    
    def __init__(self, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9):
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        
        self.fast_ema = MovingAverage(fast_period, 'ema')
        self.slow_ema = MovingAverage(slow_period, 'ema')
        self.signal_ema = MovingAverage(signal_period, 'sma')
    
    def calculate(self, data: List[float]) -> Optional[Tuple[float, float, float]]:
        """计算MACD指标"""
        if not data or len(data) < self.slow_period:
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


class BollingerBands:
    """布林带指标"""
    
    def __init__(self, period: int = 20, std_dev: float = 2.0):
        self.period = period
        self.std_dev = std_dev
    
    def calculate(self, data: List[float]) -> Optional[Tuple[float, float, float]]:
        """计算布林带"""
        if not data or len(data) < self.period:
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
    
    def calculate_price_position(self, price: float, upper_band: float, lower_band: float) -> float:
        """计算价格在布林带中的位置"""
        if upper_band == lower_band:
            return 0.5
        
        position = (price - lower_band) / (upper_band - lower_band)
        return max(0, min(1, position))


class VolumePriceAnalyzer:
    """量价分析器"""
    
    def __init__(self):
        pass
    
    def analyze_trend(self, prices: List[float], volumes: List[int]) -> Dict[str, Any]:
        """分析量价趋势"""
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
    
    def detect_divergence(self, prices: List[float], volumes: List[int]) -> Dict[str, List[int]]:
        """检测价量背离"""
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
        self.ma = MovingAverage()
        self.rsi = RSI()
        self.macd = MACD()
        self.bb = BollingerBands()
        self.volume_analyzer = VolumePriceAnalyzer()
    
    def generate_signals(self, prices: List[float], volumes: List[int]) -> Dict[str, Any]:
        """生成技术信号"""
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
        divergence = self.volume_analyzer.detect_divergence(prices, volumes)
        
        if divergence['bullish_divergence']:
            signals['buy_signals'].append({'indicator': 'Volume_Divergence', 'strength': 0.9})
        elif divergence['bearish_divergence']:
            signals['sell_signals'].append({'indicator': 'Volume_Divergence', 'strength': 0.9})
        
        return signals
    
    def calculate_signal_strength(self, prices: List[float], volumes: List[int]) -> float:
        """计算综合信号强度"""
        signals = self.generate_signals(prices, volumes)
        
        buy_strength = sum(signal['strength'] for signal in signals['buy_signals'])
        sell_strength = sum(signal['strength'] for signal in signals['sell_signals'])
        
        # 归一化到-1到1之间
        total_strength = buy_strength - sell_strength
        max_strength = buy_strength + sell_strength
        
        if max_strength == 0:
            return 0.0
        
        return total_strength / max_strength


def create_sample_stock_data():
    """创建示例股票数据"""
    # 创建模拟的历史价格数据
    base_price = 10.0
    prices = []
    volumes = []
    
    for i in range(60):  # 60天的历史数据
        # 添加一些趋势和波动
        trend = i * 0.02  # 上涨趋势
        noise = (i % 7 - 3) * 0.1  # 随机波动
        price = base_price + trend + noise
        
        prices.append(price)
        volumes.append(1000000 + i * 10000)  # 逐渐增加的成交量
    
    return prices, volumes


def example_basic_indicators():
    """基础技术指标使用示例"""
    print("=== 基础技术指标示例 ===")
    
    # 创建示例数据
    prices, volumes = create_sample_stock_data()
    
    # 创建移动平均线指标
    ma_short = MovingAverage(period=10, ma_type='sma')
    ma_long = MovingAverage(period=30, ma_type='ema')
    
    # 计算移动平均线
    ma_short_value = ma_short.calculate(prices)
    ma_long_value = ma_long.calculate(prices)
    
    print(f"10日简单移动平均线: {ma_short_value:.4f}")
    print(f"30日指数移动平均线: {ma_long_value:.4f}")
    
    # 创建RSI指标
    rsi = RSI(period=14)
    rsi_value = rsi.calculate(prices)
    print(f"RSI(14): {rsi_value:.2f}")
    
    # 创建MACD指标
    macd = MACD(fast_period=12, slow_period=26, signal_period=9)
    macd_result = macd.calculate(prices)
    
    if macd_result:
        macd_line, signal_line, histogram = macd_result
        print(f"MACD线: {macd_line:.4f}")
        print(f"信号线: {signal_line:.4f}")
        print(f"柱状图: {histogram:.4f}")
    
    # 创建布林带指标
    bb = BollingerBands(period=20, std_dev=2.0)
    bb_result = bb.calculate(prices)
    
    if bb_result:
        upper_band, middle_band, lower_band = bb_result
        current_price = prices[-1]
        position = bb.calculate_price_position(current_price, upper_band, lower_band)
        
        print(f"布林带上轨: {upper_band:.4f}")
        print(f"布林带中轨: {middle_band:.4f}")
        print(f"布林带下轨: {lower_band:.4f}")
        print(f"当前价格位置: {position:.2f}")
    
    # 量价分析
    analyzer = VolumePriceAnalyzer()
    trend_analysis = analyzer.analyze_trend(prices, volumes)
    divergence = analyzer.detect_divergence(prices, volumes)
    
    print(f"价格趋势: {trend_analysis['price_trend']}")
    print(f"成交量趋势: {trend_analysis['volume_trend']}")
    print(f"相关性: {trend_analysis['correlation']:.4f}")
    print(f"价量背离: {divergence}")
    
    print()


def example_signal_generation():
    """技术信号生成示例"""
    print("=== 技术信号生成示例 ===")
    
    # 创建示例数据
    prices, volumes = create_sample_stock_data()
    
    # 创建信号生成器
    signal_generator = TechnicalSignalGenerator()
    
    # 生成信号
    signals = signal_generator.generate_signals(prices, volumes)
    signal_strength = signal_generator.calculate_signal_strength(prices, volumes)
    
    print("买入信号:")
    for signal in signals['buy_signals']:
        print(f"  - {signal['indicator']}: 强度 {signal['strength']:.2f}")
    
    print("卖出信号:")
    for signal in signals['sell_signals']:
        print(f"  - {signal['indicator']}: 强度 {signal['strength']:.2f}")
    
    print("中性信号:")
    for signal in signals['neutral_signals']:
        print(f"  - {signal['indicator']}: 强度 {signal['strength']:.2f}")
    
    print(f"综合信号强度: {signal_strength:.4f}")
    print()


def example_technical_analysis_result():
    """技术分析结果示例"""
    print("=== 技术分析结果示例 ===")
    
    # 创建示例数据
    prices, volumes = create_sample_stock_data()
    
    # 创建技术分析结果
    technical_result = TechnicalAnalysisResult(
        symbol="DEMO001",
        timestamp=datetime.now(),
        indicators={
            'MA_10': sum(prices[-10:]) / 10,
            'MA_30': sum(prices[-30:]) / 30,
            'RSI': 45.2,
            'MACD': 0.15,
            'BB_position': 0.6
        },
        signals={
            'buy_signals': [
                {'indicator': 'MA', 'strength': 0.7},
                {'indicator': 'RSI', 'strength': 0.8}
            ],
            'sell_signals': [
                {'indicator': 'MACD', 'strength': 0.6}
            ],
            'neutral_signals': []
        },
        score=0.75
    )
    
    print("技术分析结果:")
    print(f"  股票代码: {technical_result.symbol}")
    print(f"  分析时间: {technical_result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  综合得分: {technical_result.score:.4f}")
    print(f"  指标数量: {len(technical_result.indicators)}")
    print(f"  信号数量: {len(technical_result.signals.get('buy_signals', [])) + len(technical_result.signals.get('sell_signals', []))}")
    
    print("主要指标:")
    for key, value in technical_result.indicators.items():
        print(f"    {key}: {value}")
    
    print("主要信号:")
    for signal_type, signal_list in technical_result.signals.items():
        if signal_list:
            print(f"    {signal_type}:")
            for signal in signal_list:
                print(f"      - {signal['indicator']}: 强度 {signal['strength']:.2f}")
    
    print()


def main():
    """主函数"""
    print("巴菲特股息筛选系统 - 技术分析模块纯示例")
    print("=" * 50)
    
    try:
        # 运行各种示例
        example_basic_indicators()
        example_signal_generation()
        example_technical_analysis_result()
        
        print("=" * 50)
        print("所有示例运行完成！")
        print("\n功能说明:")
        print("1. 移动平均线(MA): 支持SMA和EMA，用于识别趋势")
        print("2. RSI: 相对强弱指数，用于识别超买超卖")
        print("3. MACD: 指数平滑异同移动平均线，用于识别趋势变化")
        print("4. 布林带: 基于移动平均线和标准差，用于识别价格相对位置")
        print("5. 量价分析: 分析价格和成交量的关系，识别背离")
        print("6. 技术信号生成: 综合多个指标生成交易信号")
        print("\n注意事项:")
        print("- 技术分析仅供参考，投资有风险，入市需谨慎")
        print("- 建议结合基本面分析进行投资决策")
        print("- 不同指标可能产生矛盾信号，需要综合判断")
        
    except Exception as e:
        print(f"运行示例时出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()