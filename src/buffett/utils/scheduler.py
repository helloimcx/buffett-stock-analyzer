"""
交易时间调度器
实现只在交易日交易时间执行的调度机制
"""

import time
import schedule
from datetime import datetime, time as dt_time, timedelta
from typing import Callable, Optional, List
import threading

from ..models.monitoring import MonitoringSession
from .logger import get_logger

logger = get_logger(__name__)


class TradingScheduler:
    """交易时间调度器"""

    def __init__(self):
        self.is_running = False
        self.monitoring_thread: Optional[threading.Thread] = None
        self.current_session: Optional[MonitoringSession] = None
        self.callbacks: List[Callable] = []

    def add_callback(self, callback: Callable):
        """添加监控回调函数"""
        self.callbacks.append(callback)

    def start_monitoring(self, interval_minutes: int = 30):
        """启动监控"""
        if self.is_running:
            logger.warning("监控已经在运行中")
            return

        logger.info(f"启动股票监控，间隔: {interval_minutes}分钟")
        self.is_running = True

        # 创建监控会话
        self.current_session = MonitoringSession(
            session_id=f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            start_time=datetime.now()
        )

        # 启动监控线程
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, args=(interval_minutes,))
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()

    def stop_monitoring(self):
        """停止监控"""
        if not self.is_running:
            logger.warning("监控未在运行")
            return

        logger.info("停止股票监控")
        self.is_running = False

        if self.current_session:
            self.current_session.end_time = datetime.now()
            self.current_session.status = "stopped"

        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=5)

    def _monitoring_loop(self, interval_minutes: int):
        """监控主循环"""
        while self.is_running:
            try:
                # 检查是否为交易时间
                if self._is_trading_time():
                    logger.info("开始执行监控检查")

                    # 更新会话信息
                    if self.current_session:
                        self.current_session.last_check_time = datetime.now()
                        self.current_session.checks_performed += 1

                    # 执行所有回调函数
                    for callback in self.callbacks:
                        try:
                            callback()
                        except Exception as e:
                            logger.error(f"监控回调执行失败: {e}")

                else:
                    logger.debug("非交易时间，跳过监控")

                # 等待下次执行
                time.sleep(interval_minutes * 60)

            except Exception as e:
                logger.error(f"监控循环异常: {e}")
                time.sleep(60)  # 异常时等待1分钟后重试

    def _is_trading_time(self) -> bool:
        """检查是否为交易时间"""
        now = datetime.now()

        # 检查是否为工作日（周一到周五）
        if now.weekday() >= 5:  # 周六、周日
            return False

        # 检查是否为交易时间段
        current_time = now.time()
        morning_start = dt_time(9, 30)   # 上午开盘
        morning_end = dt_time(11, 30)    # 上午收盘
        afternoon_start = dt_time(13, 0)  # 下午开盘
        afternoon_end = dt_time(15, 0)   # 下午收盘

        # 上午交易时间
        if morning_start <= current_time <= morning_end:
            return True

        # 下午交易时间
        if afternoon_start <= current_time <= afternoon_end:
            return True

        return False

    def get_next_trading_time(self) -> Optional[datetime]:
        """获取下次交易时间"""
        now = datetime.now()

        # 今天
        trading_times = [
            dt_time(9, 30),
            dt_time(13, 0)
        ]

        for trading_time in trading_times:
            next_trading = datetime.combine(now.date(), trading_time)
            if next_trading > now and self._is_trading_time_at(next_trading):
                return next_trading

        # 明天
        tomorrow = now + timedelta(days=1)
        for trading_time in trading_times:
            next_trading = datetime.combine(tomorrow.date(), trading_time)
            if self._is_trading_time_at(next_trading):
                return next_trading

        return None

    def _is_trading_time_at(self, check_time: datetime) -> bool:
        """检查特定时间是否为交易时间"""
        # 检查是否为工作日
        if check_time.weekday() >= 5:  # 周六、周日
            return False

        # 检查是否为交易时间段
        current_time = check_time.time()
        morning_start = dt_time(9, 30)
        morning_end = dt_time(11, 30)
        afternoon_start = dt_time(13, 0)
        afternoon_end = dt_time(15, 0)

        return (morning_start <= current_time <= morning_end or
                afternoon_start <= current_time <= afternoon_end)

    def get_session_status(self) -> Optional[MonitoringSession]:
        """获取当前监控会话状态"""
        return self.current_session

    def is_monitoring_active(self) -> bool:
        """检查监控是否活跃"""
        return self.is_running


class TradingCalendar:
    """交易日历工具"""

    @staticmethod
    def is_holiday(date: datetime) -> bool:
        """检查是否为节假日"""
        # 简单实现，实际应该从API获取节假日信息
        # 这里只检查周末
        return date.weekday() >= 5

    @staticmethod
    def get_trading_days(start_date: datetime, end_date: datetime) -> List[datetime]:
        """获取指定时间范围内的交易日"""
        trading_days = []
        current_date = start_date

        while current_date <= end_date:
            if not TradingCalendar.is_holiday(current_date):
                trading_days.append(current_date)
            current_date += timedelta(days=1)

        return trading_days