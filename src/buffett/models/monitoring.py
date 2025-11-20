"""
监控相关的数据模型
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

from .stock import StockInfo


class SignalType(Enum):
    """信号类型"""
    BUY = "buy"
    SELL = "sell"


class SignalStrength(Enum):
    """信号强度"""
    WEAK = "weak"      # 弱信号
    MEDIUM = "medium"  # 中等信号
    STRONG = "strong"  # 强信号


@dataclass
class TradingSignal:
    """交易信号"""
    stock_code: str
    stock_name: str
    signal_type: SignalType
    signal_strength: SignalStrength
    price: float
    timestamp: datetime
    reasons: List[str]
    score: float
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None


@dataclass
class MonitoringConfig:
    """监控配置"""
    # 监控股票列表
    stock_symbols: List[str]

    # 监控频率（分钟）
    monitoring_interval: int = 30

    # 买入信号阈值
    buy_score_threshold: float = 70.0
    buy_dividend_threshold: float = 4.0

    # 卖出信号阈值
    sell_score_threshold: float = 30.0
    sell_dividend_threshold: float = 2.0

    # 价格变动阈值
    price_change_threshold: float = 0.05  # 5%

    # 通知设置
    enable_notifications: bool = True
    notification_methods: List[str] = None  # ['console', 'file', 'email']

    def __post_init__(self):
        if self.notification_methods is None:
            self.notification_methods = ['console', 'file']


@dataclass
class MonitoringSession:
    """监控会话"""
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = "running"  # running, stopped, error
    signals_detected: List[TradingSignal] = None
    last_check_time: Optional[datetime] = None
    checks_performed: int = 0

    def __post_init__(self):
        if self.signals_detected is None:
            self.signals_detected = []


@dataclass
class StockMonitoringState:
    """股票监控状态"""
    stock_code: str
    last_price: float
    last_score: float
    last_dividend_yield: float
    last_update: datetime
    buy_signal_triggered: bool = False
    sell_signal_triggered: bool = False
    price_history: List[float] = None

    def __post_init__(self):
        if self.price_history is None:
            self.price_history = []