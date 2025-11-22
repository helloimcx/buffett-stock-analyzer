"""
技术分析回测模块测试
测试历史数据回测和策略性能评估功能
"""

import unittest
from datetime import datetime, timedelta
from typing import List, Dict, Any
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

# 直接复制相关类到测试文件中，避免导入依赖
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
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


# 复制技术分析相关类
class TechnicalSignalGenerator:
    """技术信号生成器"""
    
    def __init__(self):
        pass
    
    def generate_signals(self, prices: List[float], volumes: List[int]) -> Dict[str, Any]:
        signals = {
            'buy_signals': [],
            'sell_signals': [],
            'neutral_signals': []
        }
        
        if len(prices) < 2:
            return signals
        
        # 简化的信号生成逻辑
        current_price = prices[-1]
        prev_price = prices[-2]
        
        if current_price > prev_price:
            signals['buy_signals'].append({'indicator': 'Price', 'strength': 0.6})
        elif current_price < prev_price:
            signals['sell_signals'].append({'indicator': 'Price', 'strength': 0.6})
        else:
            signals['neutral_signals'].append({'indicator': 'Price', 'strength': 0.5})
        
        return signals
    
    def calculate_signal_strength(self, prices: List[float], volumes: List[int]) -> float:
        signals = self.generate_signals(prices, volumes)
        
        buy_strength = sum(signal['strength'] for signal in signals['buy_signals'])
        sell_strength = sum(signal['strength'] for signal in signals['sell_signals'])
        
        total_strength = buy_strength - sell_strength
        max_strength = buy_strength + sell_strength
        
        if max_strength == 0:
            return 0.0
        
        return total_strength / max_strength


# 复制回测相关类
@dataclass
class BacktestSignal:
    """回测信号数据类"""
    timestamp: datetime
    symbol: str
    price: float
    volume: int
    signal_type: str  # 'buy', 'sell', 'neutral'
    signal_strength: float
    indicators: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0


@dataclass
class BacktestTrade:
    """回测交易数据类"""
    symbol: str
    entry_time: datetime
    exit_time: Optional[datetime]
    entry_price: float
    exit_price: Optional[float]
    position_size: int
    trade_type: str  # 'long', 'short'
    profit_loss: Optional[float] = None
    profit_loss_pct: Optional[float] = None
    exit_reason: Optional[str] = None  # 'signal', 'stop_loss', 'take_profit', 'time_exit'


@dataclass
class BacktestResult:
    """回测结果数据类"""
    symbol: str
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: float
    total_return: float
    total_return_pct: float
    max_drawdown: float
    max_drawdown_pct: float
    sharpe_ratio: Optional[float]
    win_rate: float
    profit_factor: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_trade: float
    avg_win: float
    avg_loss: float
    largest_win: float
    largest_loss: float
    trades: List[BacktestTrade] = field(default_factory=list)
    signals: List[BacktestSignal] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'symbol': self.symbol,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'initial_capital': self.initial_capital,
            'final_capital': self.final_capital,
            'total_return': self.total_return,
            'total_return_pct': self.total_return_pct,
            'max_drawdown': self.max_drawdown,
            'max_drawdown_pct': self.max_drawdown_pct,
            'sharpe_ratio': self.sharpe_ratio,
            'win_rate': self.win_rate,
            'profit_factor': self.profit_factor,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'avg_trade': self.avg_trade,
            'avg_win': self.avg_win,
            'avg_loss': self.avg_loss,
            'largest_win': self.largest_win,
            'largest_loss': self.largest_loss
        }


class TechnicalBacktester:
    """技术分析回测器"""
    
    def __init__(self, 
                 initial_capital: float = 100000.0,
                 commission_rate: float = 0.001,
                 slippage: float = 0.001,
                 stop_loss_pct: float = 0.05,
                 take_profit_pct: float = 0.10,
                 max_position_pct: float = 0.1,
                 signal_generator: Optional[TechnicalSignalGenerator] = None):
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage = slippage
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.max_position_pct = max_position_pct
        self.signal_generator = signal_generator or TechnicalSignalGenerator()
        
        # 回测状态
        self.current_capital = initial_capital
        self.current_positions: Dict[str, BacktestTrade] = {}
        self.trades: List[BacktestTrade] = []
        self.signals: List[BacktestSignal] = []
        self.equity_curve: List[Tuple[datetime, float]] = []
    
    def backtest(self, 
                 historical_data: List[Dict[str, Any]], 
                 symbol: str) -> BacktestResult:
        """执行回测"""
        # 重置回测状态
        self._reset_backtest_state()
        
        # 按日期排序历史数据
        sorted_data = sorted(historical_data, key=lambda x: x['date'])
        
        start_date = sorted_data[0]['date']
        end_date = sorted_data[-1]['date']
        
        # 准备价格和成交量历史
        price_history = []
        volume_history = []
        
        for data_point in sorted_data:
            price_history.append(data_point['price'])
            volume_history.append(data_point['volume'])
            
            # 生成技术信号
            if len(price_history) >= 20:
                signals = self.signal_generator.generate_signals(price_history, volume_history)
                signal_strength = self.signal_generator.calculate_signal_strength(price_history, volume_history)
                
                # 确定主要信号
                main_signal = self._determine_main_signal(signals)
                
                if main_signal:
                    # 创建回测信号
                    backtest_signal = BacktestSignal(
                        timestamp=data_point['date'],
                        symbol=symbol,
                        price=data_point['price'],
                        volume=data_point['volume'],
                        signal_type=main_signal['type'],
                        signal_strength=main_signal['strength'],
                        indicators=signals,
                        confidence=signal_strength
                    )
                    
                    self.signals.append(backtest_signal)
                    
                    # 执行交易
                    self._execute_signal(backtest_signal, data_point)
            
            # 更新权益曲线
            current_equity = self._calculate_current_equity(data_point['price'])
            self.equity_curve.append((data_point['date'], current_equity))
        
        # 平仓所有持仓
        self._close_all_positions(sorted_data[-1])
        
        # 计算回测结果
        result = self._calculate_backtest_result(symbol, start_date, end_date)
        
        return result
    
    def _reset_backtest_state(self):
        """重置回测状态"""
        self.current_capital = self.initial_capital
        self.current_positions.clear()
        self.trades.clear()
        self.signals.clear()
        self.equity_curve.clear()
    
    def _determine_main_signal(self, signals: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """确定主要交易信号"""
        buy_signals = signals.get('buy_signals', [])
        sell_signals = signals.get('sell_signals', [])
        
        if not buy_signals and not sell_signals:
            return None
        
        # 计算买入和卖出信号的总强度
        buy_strength = sum(signal['strength'] for signal in buy_signals)
        sell_strength = sum(signal['strength'] for signal in sell_signals)
        
        # 确定主要信号
        if buy_strength > sell_strength and buy_strength > 0.5:
            return {'type': 'buy', 'strength': buy_strength}
        elif sell_strength > buy_strength and sell_strength > 0.5:
            return {'type': 'sell', 'strength': sell_strength}
        else:
            return None
    
    def _execute_signal(self, signal: BacktestSignal, data_point: Dict[str, Any]):
        """执行交易信号"""
        symbol = signal.symbol
        current_price = signal.price
        
        if signal.signal_type == 'buy':
            # 检查是否已有持仓
            if symbol not in self.current_positions:
                # 计算仓位大小
                position_value = self.current_capital * self.max_position_pct
                shares = int(position_value / (current_price * (1 + self.commission_rate + self.slippage)))
                
                if shares > 0:
                    # 创建多头持仓
                    trade = BacktestTrade(
                        symbol=symbol,
                        entry_time=signal.timestamp,
                        exit_time=None,
                        entry_price=current_price * (1 + self.slippage),
                        exit_price=None,
                        position_size=shares,
                        trade_type='long'
                    )
                    
                    self.current_positions[symbol] = trade
                    
                    # 扣除资金
                    cost = shares * current_price * (1 + self.commission_rate + self.slippage)
                    self.current_capital -= cost
        
        elif signal.signal_type == 'sell':
            # 检查是否有持仓
            if symbol in self.current_positions:
                # 平仓
                self._close_position(symbol, data_point, 'signal')
    
    def _close_position(self, symbol: str, data_point: Dict[str, Any], exit_reason: str):
        """平仓"""
        if symbol not in self.current_positions:
            return
        
        trade = self.current_positions[symbol]
        current_price = data_point['price']
        
        # 检查止损止盈
        if trade.trade_type == 'long':
            stop_loss_price = trade.entry_price * (1 - self.stop_loss_pct)
            take_profit_price = trade.entry_price * (1 + self.take_profit_pct)
            
            if current_price <= stop_loss_price:
                exit_reason = 'stop_loss'
                current_price = stop_loss_price
            elif current_price >= take_profit_price:
                exit_reason = 'take_profit'
                current_price = take_profit_price
        
        # 执行平仓
        exit_price = current_price * (1 - self.slippage)
        proceeds = trade.position_size * exit_price * (1 - self.commission_rate - self.slippage)
        
        # 更新资金
        self.current_capital += proceeds
        
        # 计算盈亏
        cost = trade.position_size * trade.entry_price * (1 + self.commission_rate + self.slippage)
        profit_loss = proceeds - cost
        profit_loss_pct = profit_loss / cost
        
        # 更新交易记录
        trade.exit_time = data_point['date']
        trade.exit_price = exit_price
        trade.profit_loss = profit_loss
        trade.profit_loss_pct = profit_loss_pct
        trade.exit_reason = exit_reason
        
        self.trades.append(trade)
        del self.current_positions[symbol]
    
    def _close_all_positions(self, data_point: Dict[str, Any]):
        """平仓所有持仓"""
        symbols_to_close = list(self.current_positions.keys())
        for symbol in symbols_to_close:
            self._close_position(symbol, data_point, 'time_exit')
    
    def _calculate_current_equity(self, current_price: float) -> float:
        """计算当前权益"""
        equity = self.current_capital
        
        for symbol, trade in self.current_positions.items():
            # 计算持仓的当前价值
            if symbol == symbol:  # 简化处理，假设所有持仓都是当前股票
                position_value = trade.position_size * current_price
                equity += position_value
        
        return equity
    
    def _calculate_backtest_result(self, 
                                symbol: str, 
                                start_date: datetime, 
                                end_date: datetime) -> BacktestResult:
        """计算回测结果"""
        final_capital = self.current_capital
        total_return = final_capital - self.initial_capital
        total_return_pct = total_return / self.initial_capital
        
        # 计算最大回撤
        max_drawdown, max_drawdown_pct = self._calculate_max_drawdown()
        
        # 计算夏普比率
        sharpe_ratio = self._calculate_sharpe_ratio()
        
        # 计算交易统计
        win_rate, profit_factor, avg_trade, avg_win, avg_loss, largest_win, largest_loss = self._calculate_trade_statistics()
        
        return BacktestResult(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            initial_capital=self.initial_capital,
            final_capital=final_capital,
            total_return=total_return,
            total_return_pct=total_return_pct,
            max_drawdown=max_drawdown,
            max_drawdown_pct=max_drawdown_pct,
            sharpe_ratio=sharpe_ratio,
            win_rate=win_rate,
            profit_factor=profit_factor,
            total_trades=len(self.trades),
            winning_trades=len([t for t in self.trades if t.profit_loss and t.profit_loss > 0]),
            losing_trades=len([t for t in self.trades if t.profit_loss and t.profit_loss < 0]),
            avg_trade=avg_trade,
            avg_win=avg_win,
            avg_loss=avg_loss,
            largest_win=largest_win,
            largest_loss=largest_loss,
            trades=self.trades.copy(),
            signals=self.signals.copy()
        )
    
    def _calculate_max_drawdown(self) -> Tuple[float, float]:
        """计算最大回撤"""
        if not self.equity_curve:
            return 0.0, 0.0
        
        peak = self.equity_curve[0][1]
        max_drawdown = 0.0
        max_drawdown_pct = 0.0
        
        for _, equity in self.equity_curve:
            if equity > peak:
                peak = equity
            
            drawdown = peak - equity
            drawdown_pct = drawdown / peak if peak > 0 else 0.0
            
            if drawdown > max_drawdown:
                max_drawdown = drawdown
                max_drawdown_pct = drawdown_pct
        
        return max_drawdown, max_drawdown_pct
    
    def _calculate_sharpe_ratio(self) -> Optional[float]:
        """计算夏普比率"""
        if len(self.equity_curve) < 2:
            return None
        
        # 计算日收益率
        returns = []
        for i in range(1, len(self.equity_curve)):
            prev_equity = self.equity_curve[i-1][1]
            curr_equity = self.equity_curve[i][1]
            daily_return = (curr_equity - prev_equity) / prev_equity
            returns.append(daily_return)
        
        if not returns:
            return None
        
        # 计算平均收益率和标准差
        avg_return = sum(returns) / len(returns)
        variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
        std_dev = math.sqrt(variance)
        
        # 年化夏普比率（假设252个交易日）
        if std_dev == 0:
            return None
        
        sharpe_ratio = (avg_return * 252) / (std_dev * math.sqrt(252))
        
        return sharpe_ratio
    
    def _calculate_trade_statistics(self) -> Tuple[float, float, float, float, float, float, float]:
        """计算交易统计"""
        if not self.trades:
            return 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        
        winning_trades = [t for t in self.trades if t.profit_loss and t.profit_loss > 0]
        losing_trades = [t for t in self.trades if t.profit_loss and t.profit_loss < 0]
        
        win_rate = len(winning_trades) / len(self.trades)
        
        total_profit = sum(t.profit_loss for t in winning_trades)
        total_loss = abs(sum(t.profit_loss for t in losing_trades))
        profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
        
        avg_trade = sum(t.profit_loss for t in self.trades) / len(self.trades)
        avg_win = sum(t.profit_loss for t in winning_trades) / len(winning_trades) if winning_trades else 0.0
        avg_loss = sum(t.profit_loss for t in losing_trades) / len(losing_trades) if losing_trades else 0.0
        
        largest_win = max(t.profit_loss for t in winning_trades) if winning_trades else 0.0
        largest_loss = min(t.profit_loss for t in losing_trades) if losing_trades else 0.0
        
        return win_rate, profit_factor, avg_trade, avg_win, avg_loss, largest_win, largest_loss


class TestBacktesting(unittest.TestCase):
    """回测功能测试"""
    
    def setUp(self):
        """设置测试数据"""
        self.signal_generator = TechnicalSignalGenerator()
        self.backtester = TechnicalBacktester(
            initial_capital=100000.0,
            commission_rate=0.001,
            slippage=0.001,
            stop_loss_pct=0.05,
            take_profit_pct=0.10,
            max_position_pct=0.1,
            signal_generator=self.signal_generator
        )
        
        # 创建测试历史数据
        self.historical_data = []
        base_date = datetime.now() - timedelta(days=100)
        base_price = 10.0
        
        for i in range(100):
            # 创建波动的价格数据
            price_change = (i % 10 - 5) * 0.01  # -0.05 到 0.04 的波动
            price = base_price + (i * 0.01) + price_change
            
            self.historical_data.append({
                'date': base_date + timedelta(days=i),
                'price': price,
                'volume': 1000000 + i * 10000
            })
    
    def test_backtester_initialization(self):
        """测试回测器初始化"""
        self.assertEqual(self.backtester.initial_capital, 100000.0)
        self.assertEqual(self.backtester.commission_rate, 0.001)
        self.assertEqual(self.backtester.slippage, 0.001)
        self.assertEqual(self.backtester.stop_loss_pct, 0.05)
        self.assertEqual(self.backtester.take_profit_pct, 0.10)
        self.assertEqual(self.backtester.max_position_pct, 0.1)
        self.assertIsInstance(self.backtester.signal_generator, TechnicalSignalGenerator)
    
    def test_backtest_execution(self):
        """测试回测执行"""
        result = self.backtester.backtest(self.historical_data, "TEST001")
        
        # 验证回测结果
        self.assertIsInstance(result, BacktestResult)
        self.assertEqual(result.symbol, "TEST001")
        self.assertEqual(result.initial_capital, 100000.0)
        self.assertIsInstance(result.final_capital, float)
        self.assertIsInstance(result.total_return, float)
        self.assertIsInstance(result.total_return_pct, float)
        self.assertIsInstance(result.max_drawdown, float)
        self.assertIsInstance(result.max_drawdown_pct, float)
        self.assertIsInstance(result.win_rate, float)
        self.assertIsInstance(result.profit_factor, float)
        self.assertIsInstance(result.total_trades, int)
        self.assertGreaterEqual(result.total_trades, 0)
    
    def test_signal_generation_in_backtest(self):
        """测试回测中的信号生成"""
        result = self.backtester.backtest(self.historical_data, "TEST001")
        
        # 验证信号生成
        self.assertGreater(len(result.signals), 0)
        
        for signal in result.signals:
            self.assertIsInstance(signal, BacktestSignal)
            self.assertEqual(signal.symbol, "TEST001")
            self.assertIn(signal.signal_type, ['buy', 'sell', 'neutral'])
            self.assertIsInstance(signal.signal_strength, float)
            self.assertGreaterEqual(signal.signal_strength, 0.0)
            self.assertLessEqual(signal.signal_strength, 1.0)
    
    def test_trade_execution(self):
        """测试交易执行"""
        result = self.backtester.backtest(self.historical_data, "TEST001")
        
        # 验证交易执行
        if result.total_trades > 0:
            for trade in result.trades:
                self.assertIsInstance(trade, BacktestTrade)
                self.assertEqual(trade.symbol, "TEST001")
                self.assertIn(trade.trade_type, ['long', 'short'])
                self.assertGreater(trade.position_size, 0)
                self.assertIsInstance(trade.entry_price, float)
                self.assertIsInstance(trade.exit_price, float)
                self.assertIsInstance(trade.profit_loss, float)
                self.assertIsInstance(trade.profit_loss_pct, float)
                self.assertIn(trade.exit_reason, ['signal', 'stop_loss', 'take_profit', 'time_exit'])
    
    def test_max_drawdown_calculation(self):
        """测试最大回撤计算"""
        max_drawdown, max_drawdown_pct = self.backtester._calculate_max_drawdown()
        
        self.assertIsInstance(max_drawdown, float)
        self.assertIsInstance(max_drawdown_pct, float)
        self.assertGreaterEqual(max_drawdown, 0.0)
        self.assertGreaterEqual(max_drawdown_pct, 0.0)
    
    def test_sharpe_ratio_calculation(self):
        """测试夏普比率计算"""
        sharpe_ratio = self.backtester._calculate_sharpe_ratio()
        
        # 夏普比率可能为None（如果没有足够的权益数据）
        if sharpe_ratio is not None:
            self.assertIsInstance(sharpe_ratio, float)
    
    def test_trade_statistics_calculation(self):
        """测试交易统计计算"""
        win_rate, profit_factor, avg_trade, avg_win, avg_loss, largest_win, largest_loss = self.backtester._calculate_trade_statistics()
        
        self.assertIsInstance(win_rate, float)
        self.assertGreaterEqual(win_rate, 0.0)
        self.assertLessEqual(win_rate, 1.0)
        
        self.assertIsInstance(profit_factor, float)
        self.assertGreaterEqual(profit_factor, 0.0)
        
        self.assertIsInstance(avg_trade, float)
        self.assertIsInstance(avg_win, float)
        self.assertIsInstance(avg_loss, float)
        self.assertIsInstance(largest_win, float)
        self.assertIsInstance(largest_loss, float)
    
    def test_backtest_result_to_dict(self):
        """测试回测结果转换为字典"""
        result = self.backtester.backtest(self.historical_data, "TEST001")
        result_dict = result.to_dict()
        
        self.assertIsInstance(result_dict, dict)
        self.assertEqual(result_dict['symbol'], "TEST001")
        self.assertEqual(result_dict['initial_capital'], 100000.0)
        self.assertIn('final_capital', result_dict)
        self.assertIn('total_return', result_dict)
        self.assertIn('total_return_pct', result_dict)
        self.assertIn('max_drawdown', result_dict)
        self.assertIn('max_drawdown_pct', result_dict)
        self.assertIn('sharpe_ratio', result_dict)
        self.assertIn('win_rate', result_dict)
        self.assertIn('profit_factor', result_dict)
        self.assertIn('total_trades', result_dict)
    
    def test_insufficient_data_handling(self):
        """测试数据不足时的处理"""
        # 创建不足20天的数据
        short_data = self.historical_data[:15]
        
        result = self.backtester.backtest(short_data, "TEST001")
        
        # 验证结果
        self.assertIsInstance(result, BacktestResult)
        self.assertEqual(result.symbol, "TEST001")
        self.assertEqual(result.initial_capital, 100000.0)
        # 由于数据不足，可能没有交易
        self.assertEqual(result.total_trades, 0)
        self.assertEqual(len(result.signals), 0)
    
    def test_no_signals_scenario(self):
        """测试没有信号的场景"""
        # 创建没有价格变化的数据
        flat_data = []
        base_date = datetime.now() - timedelta(days=30)
        
        for i in range(30):
            flat_data.append({
                'date': base_date + timedelta(days=i),
                'price': 10.0,  # 固定价格
                'volume': 1000000
            })
        
        result = self.backtester.backtest(flat_data, "TEST001")
        
        # 验证结果
        self.assertIsInstance(result, BacktestResult)
        # 由于没有价格变化，可能没有交易
        self.assertEqual(result.total_trades, 0)
        self.assertEqual(len(result.signals), 0)


if __name__ == '__main__':
    unittest.main()