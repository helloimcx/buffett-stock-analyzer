"""
交易信号检测策略
实现买入和卖出信号的检测逻辑
"""

from typing import List, Tuple, Optional
from datetime import datetime

from ..models.stock import StockInfo
from ..models.monitoring import (
    TradingSignal, SignalType, SignalStrength,
    StockMonitoringState, MonitoringConfig
)
from ..core.scoring import InvestmentScorer


class SignalDetector:
    """交易信号检测器"""

    def __init__(self, config: MonitoringConfig):
        self.config = config
        self.scorer = InvestmentScorer()

    def detect_signals(self,
                      current_stock: StockInfo,
                      previous_state: Optional[StockMonitoringState] = None) -> List[TradingSignal]:
        """检测交易信号"""
        signals = []

        # 计算当前评分
        current_score = self.scorer.calculate_total_score(current_stock)

        # 检测买入信号
        buy_signal = self._detect_buy_signal(current_stock, current_score, previous_state)
        if buy_signal:
            signals.append(buy_signal)

        # 检测卖出信号
        sell_signal = self._detect_sell_signal(current_stock, current_score, previous_state)
        if sell_signal:
            signals.append(sell_signal)

        return signals

    def _detect_buy_signal(self,
                          stock: StockInfo,
                          current_score: float,
                          previous_state: Optional[StockMonitoringState]) -> Optional[TradingSignal]:
        """检测买入信号"""

        # 买入信号条件
        conditions = []
        signal_strength = SignalStrength.WEAK

        # 1. 评分条件
        if current_score >= self.config.buy_score_threshold:
            if current_score >= 85:
                signal_strength = SignalStrength.STRONG
                conditions.append(f"评分优异({current_score:.1f}≥85)")
            elif current_score >= 75:
                signal_strength = SignalStrength.MEDIUM
                conditions.append(f"评分良好({current_score:.1f}≥75)")
            else:
                conditions.append(f"评分达标({current_score:.1f}≥{self.config.buy_score_threshold})")

        # 2. 股息率条件
        if stock.dividend_yield >= self.config.buy_dividend_threshold:
            if stock.dividend_yield >= 6:
                signal_strength = SignalStrength.STRONG
                conditions.append(f"高股息率({stock.dividend_yield:.2f}%≥6%)")
            elif stock.dividend_yield >= 5:
                conditions.append(f"良好股息率({stock.dividend_yield:.2f}%≥5%)")
            else:
                conditions.append(f"股息率达标({stock.dividend_yield:.2f}%≥{self.config.buy_dividend_threshold}%)")

        # 3. 估值条件（低PE、PB）
        if 0 < stock.pe_ratio < 15:
            conditions.append(f"低估值(PE={stock.pe_ratio:.2f}<15)")
            if signal_strength == SignalStrength.WEAK:
                signal_strength = SignalStrength.MEDIUM

        if 0 < stock.pb_ratio < 1.5:
            conditions.append(f"低估值(PB={stock.pb_ratio:.2f}<1.5)")
            if signal_strength == SignalStrength.WEAK:
                signal_strength = SignalStrength.MEDIUM

        # 4. 技术位置条件（接近52周低点）
        if stock.week_52_high > 0 and stock.week_52_low > 0:
            position = (stock.price - stock.week_52_low) / (stock.week_52_high - stock.week_52_low)
            if position < 0.2:  # 接近52周低点
                conditions.append(f"技术位置良好(距52周低点{(position*100):.1f}%)")
                if signal_strength == SignalStrength.WEAK:
                    signal_strength = SignalStrength.MEDIUM

        # 5. 价格变动条件（相比上次检测有显著下跌）
        if previous_state and previous_state.last_price > 0:
            price_change = (stock.price - previous_state.last_price) / previous_state.last_price
            if price_change < -self.config.price_change_threshold:
                conditions.append(f"价格回调{(price_change*100):.2f}%")
                signal_strength = SignalStrength.STRONG

        # 6. 连续监控条件（避免重复信号）
        if previous_state and previous_state.buy_signal_triggered:
            # 如果上次已经触发买入信号，降低再次触发的概率
            if current_score < previous_state.last_score + 5:  # 需要评分提升5分才再次触发
                return None

        # 必须至少满足2个条件才产生信号
        if len(conditions) >= 2:
            # 计算目标价和止损价
            target_price = self._calculate_target_price(stock)
            stop_loss = self._calculate_stop_loss(stock)

            return TradingSignal(
                stock_code=stock.code,
                stock_name=stock.name,
                signal_type=SignalType.BUY,
                signal_strength=signal_strength,
                price=stock.price,
                timestamp=datetime.now(),
                reasons=conditions,
                score=current_score,
                target_price=target_price,
                stop_loss=stop_loss
            )

        return None

    def _detect_sell_signal(self,
                           stock: StockInfo,
                           current_score: float,
                           previous_state: Optional[StockMonitoringState]) -> Optional[TradingSignal]:
        """检测卖出信号"""

        # 卖出信号条件
        conditions = []
        signal_strength = SignalStrength.WEAK

        # 1. 评分下降条件
        if current_score <= self.config.sell_score_threshold:
            if current_score <= 20:
                signal_strength = SignalStrength.STRONG
                conditions.append(f"评分恶化({current_score:.1f}≤20)")
            elif current_score <= 25:
                signal_strength = SignalStrength.MEDIUM
                conditions.append(f"评分较差({current_score:.1f}≤25)")
            else:
                conditions.append(f"评分偏低({current_score:.1f}≤{self.config.sell_score_threshold})")

        # 2. 股息率下降条件
        if stock.dividend_yield <= self.config.sell_dividend_threshold:
            conditions.append(f"股息率过低({stock.dividend_yield:.2f}%≤{self.config.sell_dividend_threshold}%)")
            if signal_strength == SignalStrength.WEAK:
                signal_strength = SignalStrength.MEDIUM

        # 3. 估值过高条件
        if stock.pe_ratio > 30:
            conditions.append(f"估值过高(PE={stock.pe_ratio:.2f}>30)")
            signal_strength = SignalStrength.MEDIUM

        if stock.pb_ratio > 5:
            conditions.append(f"估值过高(PB={stock.pb_ratio:.2f}>5)")
            if signal_strength == SignalStrength.WEAK:
                signal_strength = SignalStrength.MEDIUM

        # 4. 技术位置条件（接近52周高点）
        if stock.week_52_high > 0 and stock.week_52_low > 0:
            position = (stock.price - stock.week_52_low) / (stock.week_52_high - stock.week_52_low)
            if position > 0.9:  # 接近52周高点
                conditions.append(f"接近52周高点({(position*100):.1f}%)")
                if signal_strength == SignalStrength.WEAK:
                    signal_strength = SignalStrength.MEDIUM

        # 5. 价格上涨条件（相比买入价格有显著上涨）
        if previous_state and previous_state.last_price > 0:
            price_change = (stock.price - previous_state.last_price) / previous_state.last_price
            if price_change > 0.2:  # 上涨20%以上
                conditions.append(f"盈利{(price_change*100):.1f}%")
                signal_strength = SignalStrength.STRONG
            elif price_change > 0.1:  # 上涨10%以上
                conditions.append(f"盈利{(price_change*100):.1f}%")
                if signal_strength == SignalStrength.WEAK:
                    signal_strength = SignalStrength.MEDIUM

        # 6. 基本面恶化条件
        if stock.eps <= 0:
            conditions.append("每股收益为负")
            signal_strength = SignalStrength.STRONG

        # 必须至少满足2个条件才产生信号
        if len(conditions) >= 2:
            return TradingSignal(
                stock_code=stock.code,
                stock_name=stock.name,
                signal_type=SignalType.SELL,
                signal_strength=signal_strength,
                price=stock.price,
                timestamp=datetime.now(),
                reasons=conditions,
                score=current_score
            )

        return None

    def _calculate_target_price(self, stock: StockInfo) -> float:
        """计算目标价格"""
        # 基于估值和当前价格计算目标价
        # 简单策略：如果当前估值较低，给予15-25%的上涨预期
        if stock.pe_ratio < 10 and stock.pb_ratio < 1.0:
            return stock.price * 1.25  # 25%上涨预期
        elif stock.pe_ratio < 15 and stock.pb_ratio < 1.5:
            return stock.price * 1.20  # 20%上涨预期
        else:
            return stock.price * 1.15  # 15%上涨预期

    def _calculate_stop_loss(self, stock: StockInfo) -> float:
        """计算止损价格"""
        # 基于技术位置和基本面设置止损
        if stock.week_52_low > 0:
            # 止损设置在52周低点上方5%
            return stock.week_52_low * 1.05
        else:
            # 默认8%止损
            return stock.price * 0.92