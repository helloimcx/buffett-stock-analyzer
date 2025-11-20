"""
股票监控系统核心
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from ..models.stock import StockInfo
from ..models.monitoring import (
    MonitoringConfig, MonitoringSession, StockMonitoringState,
    TradingSignal
)
from ..data.repository import StockRepository
from ..strategies.signals import SignalDetector
from ..utils.scheduler import TradingScheduler
from ..utils.logger import get_logger

logger = get_logger(__name__)


class StockMonitor:
    """股票监控系统"""

    def __init__(self, config: MonitoringConfig):
        self.config = config
        self.repository = StockRepository()
        self.signal_detector = SignalDetector(config)
        self.scheduler = TradingScheduler()

        # 监控状态
        self.stock_states: Dict[str, StockMonitoringState] = {}
        self.current_session: Optional[MonitoringSession] = None

        # 数据文件路径
        self.data_dir = Path("data/monitoring")
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # 添加监控回调
        self.scheduler.add_callback(self._monitoring_check)

    def start_monitoring(self):
        """启动监控"""
        logger.info("启动股票监控系统")

        # 初始化股票状态
        self._initialize_stock_states()

        # 启动调度器
        self.scheduler.start_monitoring(self.config.monitoring_interval)

        # 获取会话状态
        self.current_session = self.scheduler.get_session_status()

        logger.info(f"监控已启动，覆盖 {len(self.config.stock_symbols)} 只股票")

    def stop_monitoring(self):
        """停止监控"""
        logger.info("停止股票监控系统")
        self.scheduler.stop_monitoring()

        if self.current_session:
            self._save_session()

        logger.info("监控已停止")

    def _initialize_stock_states(self):
        """初始化股票监控状态"""
        logger.info("初始化股票监控状态")

        for symbol in self.config.stock_symbols:
            try:
                # 获取股票信息
                stock_info = self._get_stock_info(symbol)
                if stock_info:
                    # 创建监控状态
                    state = StockMonitoringState(
                        stock_code=symbol,
                        last_price=stock_info.price,
                        last_score=0.0,  # 初始评分为0
                        last_dividend_yield=stock_info.dividend_yield,
                        last_update=datetime.now(),
                        price_history=[stock_info.price]
                    )
                    self.stock_states[symbol] = state
                    logger.info(f"初始化股票状态: {symbol} - {stock_info.name}")
                else:
                    logger.warning(f"无法获取股票信息: {symbol}")

            except Exception as e:
                logger.error(f"初始化股票状态失败 {symbol}: {e}")

    def _monitoring_check(self):
        """执行监控检查"""
        logger.info("开始执行监控检查")

        signals_detected = []

        for symbol in self.config.stock_symbols:
            try:
                # 获取当前股票信息
                current_stock = self._get_stock_info(symbol)
                if not current_stock:
                    logger.warning(f"无法获取股票信息: {symbol}")
                    continue

                # 获取之前的状态
                previous_state = self.stock_states.get(symbol)

                # 检测交易信号
                signals = self.signal_detector.detect_signals(current_stock, previous_state)

                if signals:
                    signals_detected.extend(signals)
                    logger.info(f"检测到 {len(signals)} 个信号: {symbol}")

                    # 更新状态
                    self._update_stock_state(symbol, current_stock, signals)

                    # 发送通知
                    if self.config.enable_notifications:
                        self._send_notifications(signals)

                else:
                    # 即使没有信号也要更新状态
                    self._update_stock_state(symbol, current_stock, [])

            except Exception as e:
                logger.error(f"监控检查失败 {symbol}: {e}")

        # 保存信号记录
        if signals_detected:
            self._save_signals(signals_detected)
            logger.info(f"本轮检查共检测到 {len(signals_detected)} 个信号")

        # 更新会话信息
        if self.current_session:
            self.current_session.signals_detected.extend(signals_detected)

    def _get_stock_info(self, symbol: str) -> Optional[StockInfo]:
        """获取股票信息"""
        try:
            stocks = self.repository.get_stocks_by_symbols([symbol])
            return stocks[0] if stocks else None
        except Exception as e:
            logger.error(f"获取股票信息失败 {symbol}: {e}")
            return None

    def _update_stock_state(self, symbol: str, stock: StockInfo, signals: List[TradingSignal]):
        """更新股票监控状态"""
        from ..core.scoring import InvestmentScorer

        # 计算评分
        scorer = InvestmentScorer()
        current_score = scorer.calculate_total_score(stock)

        # 更新或创建状态
        if symbol in self.stock_states:
            state = self.stock_states[symbol]
            state.last_price = stock.price
            state.last_score = current_score
            state.last_dividend_yield = stock.dividend_yield
            state.last_update = datetime.now()
            state.price_history.append(stock.price)

            # 保持价格历史在合理范围内（最多100个点）
            if len(state.price_history) > 100:
                state.price_history = state.price_history[-100:]

            # 更新信号触发状态
            for signal in signals:
                if signal.signal_type.value == "buy":
                    state.buy_signal_triggered = True
                elif signal.signal_type.value == "sell":
                    state.sell_signal_triggered = True

        else:
            # 创建新状态
            state = StockMonitoringState(
                stock_code=symbol,
                last_price=stock.price,
                last_score=current_score,
                last_dividend_yield=stock.dividend_yield,
                last_update=datetime.now(),
                price_history=[stock.price],
                buy_signal_triggered=any(s.signal_type.value == "buy" for s in signals),
                sell_signal_triggered=any(s.signal_type.value == "sell" for s in signals)
            )
            self.stock_states[symbol] = state

        # 保存状态
        self._save_stock_states()

    def _send_notifications(self, signals: List[TradingSignal]):
        """发送通知"""
        for method in self.config.notification_methods:
            try:
                if method == "console":
                    self._console_notification(signals)
                elif method == "file":
                    self._file_notification(signals)
                # 可以扩展其他通知方式：email, wechat, etc.

            except Exception as e:
                logger.error(f"发送通知失败 {method}: {e}")

    def _console_notification(self, signals: List[TradingSignal]):
        """控制台通知"""
        for signal in signals:
            signal_type = "🟢 买入" if signal.signal_type.value == "buy" else "🔴 卖出"
            strength = {"weak": "弱", "medium": "中", "strong": "强"}[signal.signal_strength.value]

            print(f"\n{signal_type} 信号 - {strength}信号")
            print(f"股票: {signal.stock_name} ({signal.stock_code})")
            print(f"价格: ¥{signal.price:.2f}")
            print(f"评分: {signal.score:.1f}")
            print(f"理由: {', '.join(signal.reasons)}")

            if signal.target_price:
                print(f"目标价: ¥{signal.target_price:.2f}")
            if signal.stop_loss:
                print(f"止损价: ¥{signal.stop_loss:.2f}")

            print("-" * 50)

    def _file_notification(self, signals: List[TradingSignal]):
        """文件通知"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.data_dir / f"signals_{timestamp}.json"

        signals_data = []
        for signal in signals:
            signals_data.append({
                "stock_code": signal.stock_code,
                "stock_name": signal.stock_name,
                "signal_type": signal.signal_type.value,
                "signal_strength": signal.signal_strength.value,
                "price": signal.price,
                "timestamp": signal.timestamp.isoformat(),
                "reasons": signal.reasons,
                "score": signal.score,
                "target_price": signal.target_price,
                "stop_loss": signal.stop_loss
            })

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(signals_data, f, ensure_ascii=False, indent=2)

        logger.info(f"信号已保存到文件: {filename}")

    def _save_signals(self, signals: List[TradingSignal]):
        """保存信号记录"""
        timestamp = datetime.now().strftime("%Y%m%d")
        filename = self.data_dir / f"all_signals_{timestamp}.json"

        # 读取现有信号
        existing_signals = []
        if filename.exists():
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    existing_signals = json.load(f)
            except Exception as e:
                logger.error(f"读取现有信号失败: {e}")

        # 添加新信号
        for signal in signals:
            signal_data = {
                "stock_code": signal.stock_code,
                "stock_name": signal.stock_name,
                "signal_type": signal.signal_type.value,
                "signal_strength": signal.signal_strength.value,
                "price": signal.price,
                "timestamp": signal.timestamp.isoformat(),
                "reasons": signal.reasons,
                "score": signal.score,
                "target_price": signal.target_price,
                "stop_loss": signal.stop_loss
            }
            existing_signals.append(signal_data)

        # 保存到文件
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(existing_signals, f, ensure_ascii=False, indent=2)

    def _save_stock_states(self):
        """保存股票状态"""
        filename = self.data_dir / "stock_states.json"

        states_data = {}
        for symbol, state in self.stock_states.items():
            states_data[symbol] = {
                "stock_code": state.stock_code,
                "last_price": state.last_price,
                "last_score": state.last_score,
                "last_dividend_yield": state.last_dividend_yield,
                "last_update": state.last_update.isoformat(),
                "buy_signal_triggered": state.buy_signal_triggered,
                "sell_signal_triggered": state.sell_signal_triggered,
                "price_history": state.price_history[-20:]  # 只保存最近20个价格点
            }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(states_data, f, ensure_ascii=False, indent=2)

    def _save_session(self):
        """保存监控会话"""
        if not self.current_session:
            return

        filename = self.data_dir / f"session_{self.current_session.session_id}.json"

        session_data = {
            "session_id": self.current_session.session_id,
            "start_time": self.current_session.start_time.isoformat(),
            "end_time": self.current_session.end_time.isoformat() if self.current_session.end_time else None,
            "status": self.current_session.status,
            "checks_performed": self.current_session.checks_performed,
            "signals_count": len(self.current_session.signals_detected)
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)

    def get_monitoring_status(self) -> Dict:
        """获取监控状态"""
        if not self.current_session:
            return {"status": "stopped"}

        return {
            "status": self.current_session.status,
            "session_id": self.current_session.session_id,
            "start_time": self.current_session.start_time.isoformat(),
            "last_check_time": self.current_session.last_check_time.isoformat() if self.current_session.last_check_time else None,
            "checks_performed": self.current_session.checks_performed,
            "signals_detected": len(self.current_session.signals_detected),
            "stocks_monitoring": len(self.stock_states),
            "is_active": self.scheduler.is_monitoring_active()
        }

    def get_stock_states(self) -> Dict[str, StockMonitoringState]:
        """获取所有股票状态"""
        return self.stock_states.copy()