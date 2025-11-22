"""
增强技术因子
集成新的技术分析模块到现有的多因子评分系统
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from ..core.multi_factor_scoring import Factor
from ..models.stock import StockInfo
from .technical_analysis import (
    MovingAverage, 
    RSI, 
    MACD, 
    BollingerBands,
    VolumePriceAnalyzer,
    TechnicalSignalGenerator,
    TechnicalAnalysisResult
)


class EnhancedTechnicalFactor(Factor):
    """增强技术因子，使用多种技术指标进行综合评估"""
    
    def __init__(self, weight: float = 1.0):
        """
        初始化增强技术因子
        
        Args:
            weight: 因子权重
        """
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
        """
        计算增强技术因子得分
        
        Args:
            stock: 股票信息
            
        Returns:
            技术因子得分 (0-1)
        """
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
        """
        计算简单的技术得分（基于52周高低点）
        
        Args:
            stock: 股票信息
            
        Returns:
            技术得分 (0-1)
        """
        high_52w = stock.week_52_high
        low_52w = stock.week_52_low
        current_price = stock.price
        
        if high_52w > 0 and low_52w > 0:
            position = (current_price - low_52w) / (high_52w - low_52w)
            
            # 接近低点得分更高
            if position < 0.2:
                return 1.0
            elif position < 0.4:
                return 0.7
            elif position < 0.7:
                return 0.4
            else:
                return 0.1
        
        return 0.5  # 没有数据时给中等分数
    
    def _calculate_comprehensive_technical_score(self, symbol: str) -> float:
        """
        计算综合技术得分
        
        Args:
            symbol: 股票代码
            
        Returns:
            综合技术得分 (0-1)
        """
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
        """计算移动平均线得分"""
        prices = self.price_history[symbol]
        
        ma_short = self.ma_short.calculate(prices)
        ma_long = self.ma_long.calculate(prices)
        
        if ma_short is None or ma_long is None:
            return 0.5
        
        current_price = prices[-1]
        
        # 短期均线在长期均线之上，且价格在短期均线之上
        if ma_short > ma_long and current_price > ma_short:
            return 0.8
        # 短期均线在长期均线之上，但价格在短期均线之下
        elif ma_short > ma_long and current_price < ma_short:
            return 0.6
        # 短期均线在长期均线之下，但价格在短期均线之上
        elif ma_short < ma_long and current_price > ma_short:
            return 0.4
        # 短期均线在长期均线之下，且价格在短期均线之下
        else:
            return 0.2
    
    def _calculate_rsi_score(self, symbol: str) -> float:
        """计算RSI得分"""
        prices = self.price_history[symbol]
        rsi_value = self.rsi.calculate(prices)
        
        if rsi_value is None:
            return 0.5
        
        # RSI在30-70之间为中性，低于30为超买，高于70为超卖
        if 30 <= rsi_value <= 70:
            return 0.7  # 中性区域，稳定性好
        elif 20 <= rsi_value < 30:
            return 0.9  # 接近超卖，可能是买入机会
        elif 70 < rsi_value <= 80:
            return 0.5  # 接近超买，需要谨慎
        elif rsi_value < 20:
            return 0.6  # 超卖，但可能是基本面问题
        else:  # rsi_value > 80
            return 0.3  # 严重超买，风险高
    
    def _calculate_macd_score(self, symbol: str) -> float:
        """计算MACD得分"""
        prices = self.price_history[symbol]
        macd_result = self.macd.calculate(prices)
        
        if macd_result is None:
            return 0.5
        
        macd_line, signal_line, histogram = macd_result
        
        # MACD线在信号线之上，且柱状图为正
        if macd_line > signal_line and histogram > 0:
            return 0.8
        # MACD线在信号线之上，但柱状图为负
        elif macd_line > signal_line and histogram < 0:
            return 0.6
        # MACD线在信号线之下，但柱状图为正
        elif macd_line < signal_line and histogram > 0:
            return 0.4
        # MACD线在信号线之下，且柱状图为负
        else:
            return 0.2
    
    def _calculate_bollinger_bands_score(self, symbol: str) -> float:
        """计算布林带得分"""
        prices = self.price_history[symbol]
        bb_result = self.bollinger_bands.calculate(prices)
        
        if bb_result is None:
            return 0.5
        
        upper_band, middle_band, lower_band = bb_result
        current_price = prices[-1]
        
        # 计算价格在布林带中的位置
        position = self.bollinger_bands.calculate_price_position(current_price, upper_band, lower_band)
        
        # 价格在下轨附近或以下，可能是买入机会
        if position <= 0.1:
            return 0.9
        # 价格在下轨和中轨之间
        elif position <= 0.4:
            return 0.7
        # 价格在中轨附近
        elif position <= 0.6:
            return 0.5
        # 价格在中轨和上轨之间
        elif position <= 0.9:
            return 0.3
        # 价格在上轨附近或以上，可能是卖出信号
        else:
            return 0.1
    
    def _calculate_volume_price_score(self, symbol: str) -> float:
        """计算量价分析得分"""
        prices = self.price_history[symbol]
        volumes = self.volume_history[symbol]
        
        # 分析量价趋势
        trend_analysis = self.volume_analyzer.analyze_trend(prices, volumes)
        
        # 检测背离
        divergence = self.volume_analyzer.detect_divergence(prices, volumes)
        
        score = 0.5  # 基础分数
        
        # 根据趋势调整分数
        if trend_analysis['price_trend'] == 'up' and trend_analysis['volume_trend'] == 'increasing':
            score += 0.3  # 价涨量增，健康上涨
        elif trend_analysis['price_trend'] == 'down' and trend_analysis['volume_trend'] == 'decreasing':
            score += 0.2  # 价跌量缩，可能企稳
        elif trend_analysis['price_trend'] == 'up' and trend_analysis['volume_trend'] == 'decreasing':
            score -= 0.2  # 价涨量缩，上涨乏力
        elif trend_analysis['price_trend'] == 'down' and trend_analysis['volume_trend'] == 'increasing':
            score -= 0.3  # 价跌量增，可能继续下跌
        
        # 根据背离调整分数
        if divergence['bullish_divergence']:
            score += 0.4  # 看涨背离，买入信号
        elif divergence['bearish_divergence']:
            score -= 0.4  # 看跌背离，卖出信号
        
        # 确保分数在0-1之间
        return max(0.0, min(1.0, score))
    
    def get_technical_analysis_result(self, stock: StockInfo) -> Optional[TechnicalAnalysisResult]:
        """
        获取技术分析结果
        
        Args:
            stock: 股票信息
            
        Returns:
            技术分析结果
        """
        symbol = stock.code
        
        if symbol not in self.price_history or len(self.price_history[symbol]) < 20:
            return None
        
        prices = self.price_history[symbol]
        volumes = self.volume_history[symbol]
        
        # 计算各项指标
        indicators = {}
        
        # 移动平均线
        ma_short = self.ma_short.calculate(prices)
        ma_long = self.ma_long.calculate(prices)
        if ma_short is not None and ma_long is not None:
            indicators['MA_short'] = ma_short
            indicators['MA_long'] = ma_long
            indicators['MA_signal'] = 'bullish' if ma_short > ma_long else 'bearish'
        
        # RSI
        rsi_value = self.rsi.calculate(prices)
        if rsi_value is not None:
            indicators['RSI'] = rsi_value
            if rsi_value < 30:
                indicators['RSI_signal'] = 'oversold'
            elif rsi_value > 70:
                indicators['RSI_signal'] = 'overbought'
            else:
                indicators['RSI_signal'] = 'neutral'
        
        # MACD
        macd_result = self.macd.calculate(prices)
        if macd_result is not None:
            macd_line, signal_line, histogram = macd_result
            indicators['MACD_line'] = macd_line
            indicators['MACD_signal'] = signal_line
            indicators['MACD_histogram'] = histogram
            indicators['MACD_signal_type'] = 'bullish' if histogram > 0 else 'bearish'
        
        # 布林带
        bb_result = self.bollinger_bands.calculate(prices)
        if bb_result is not None:
            upper_band, middle_band, lower_band = bb_result
            indicators['BB_upper'] = upper_band
            indicators['BB_middle'] = middle_band
            indicators['BB_lower'] = lower_band
            indicators['BB_position'] = self.bollinger_bands.calculate_price_position(
                prices[-1], upper_band, lower_band
            )
        
        # 量价分析
        trend_analysis = self.volume_analyzer.analyze_trend(prices, volumes)
        divergence = self.volume_analyzer.detect_divergence(prices, volumes)
        indicators['price_trend'] = trend_analysis['price_trend']
        indicators['volume_trend'] = trend_analysis['volume_trend']
        indicators['volume_price_correlation'] = trend_analysis['correlation']
        indicators['divergence'] = divergence
        
        # 生成信号
        signals = self.signal_generator.generate_signals(prices, volumes)
        
        # 计算综合得分
        score = self.calculate(stock)
        
        return TechnicalAnalysisResult(
            symbol=symbol,
            timestamp=datetime.now(),
            indicators=indicators,
            signals=signals,
            score=score
        )
    
    def clear_history(self, symbol: Optional[str] = None):
        """
        清除历史数据
        
        Args:
            symbol: 股票代码，如果为None则清除所有历史数据
        """
        if symbol is None:
            self.price_history.clear()
            self.volume_history.clear()
        elif symbol in self.price_history:
            del self.price_history[symbol]
            del self.volume_history[symbol]