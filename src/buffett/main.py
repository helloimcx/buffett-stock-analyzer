"""
巴菲特股息筛选系统主程序
分层架构的命令行入口
"""

import argparse
import sys
from pathlib import Path
from typing import List

# 添加src目录到Python路径
current_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(current_dir))

from src.buffett.models import ScreeningResult, MonitoringConfig
from src.buffett.strategies import DividendScreeningStrategy, TargetStockAnalysisStrategy
from src.buffett.utils import StockReporter, load_symbols_from_file
from src.buffett.core import config
from src.buffett.core.monitor import StockMonitor
from src.buffett.utils.reporter import MonitoringReporter
import signal
import time
import threading


class BuffettScreener:
    """巴菲特股息筛选器主类"""

    def __init__(self):
        self.reporter = StockReporter(config.reports_dir)
        self.monitoring_reporter = MonitoringReporter(config.reports_dir)
        self.errors: List[str] = []
        self.monitor: StockMonitor = None

    def screen_dividend_stocks(self, min_dividend_yield: float = 4.0) -> ScreeningResult:
        """筛选高股息股票"""
        print(f"🔍 筛选股息率≥{min_dividend_yield}%的股票...")

        strategy = DividendScreeningStrategy()
        result = strategy.screen_dividend_stocks(min_dividend_yield)

        # 显示结果
        self.reporter.display_results(result.passed_stocks, f"股息率≥{min_dividend_yield}%的股票")
        self.reporter.display_summary(result)

        # 保存结果
        self.reporter.save_results(result, f"dividend_{min_dividend_yield}pct")

        return result

    def analyze_target_stocks(self, symbols: List[str]) -> ScreeningResult:
        """分析指定股票列表"""
        strategy = TargetStockAnalysisStrategy()
        result = strategy.analyze_target_stocks(symbols)

        # 显示结果
        self.reporter.display_results(result.passed_stocks, "指定股票分析结果")
        self.reporter.display_summary(result)

        # 保存结果
        self.reporter.save_results(result, "target_analysis")

        return result

    def _create_empty_result(self, error_message: str) -> ScreeningResult:
        """创建空结果对象"""
        self.errors.append(error_message)
        from src.buffett.models import ScreeningCriteria
        from datetime import datetime

        criteria = ScreeningCriteria()
        return ScreeningResult(
            timestamp=datetime.now(),
            criteria=criteria,
            total_stocks_analyzed=0,
            passed_stocks=[],
            errors=self.errors
        )

    def start_monitoring(self, stock_file: str = "sample_stocks.txt", interval: int = 30):
        """启动股票监控"""
        print(f"🚀 启动股票监控系统...")
        print(f"📋 监控股票文件: {stock_file}")
        print(f"⏰ 监控间隔: {interval}分钟")

        # 加载股票列表
        try:
            symbols = load_symbols_from_file(stock_file)
            if not symbols:
                print(f"❌ 无法从文件 {stock_file} 加载股票代码")
                return None

            print(f"📊 将监控 {len(symbols)} 只股票")
            for symbol in symbols[:5]:  # 只显示前5个
                print(f"   - {symbol}")
            if len(symbols) > 5:
                print(f"   ... 还有 {len(symbols) - 5} 只股票")

        except Exception as e:
            print(f"❌ 加载股票文件失败: {e}")
            return None

        # 创建监控配置
        monitoring_config = MonitoringConfig(
            stock_symbols=symbols,
            monitoring_interval=interval,
            buy_score_threshold=70.0,
            buy_dividend_threshold=4.0,
            sell_score_threshold=30.0,
            sell_dividend_threshold=2.0,
            price_change_threshold=0.05,
            enable_notifications=True,
            notification_methods=['console', 'file']
        )

        # 创建并启动监控器
        try:
            self.monitor = StockMonitor(monitoring_config)

            # 设置信号处理
            def signal_handler(signum, frame):
                print("\n🛑 收到停止信号，正在停止监控...")
                if self.monitor:
                    self.monitor.stop_monitoring()
                sys.exit(0)

            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)

            print("🔥 监控系统已启动，按 Ctrl+C 停止监控")
            print("📺 监控状态将实时显示，交易信号将自动通知")
            print("-" * 60)

            self.monitor.start_monitoring()

            # 保持主线程运行
            while self.monitor and self.monitor.scheduler.is_monitoring_active():
                time.sleep(1)

        except Exception as e:
            print(f"❌ 监控启动失败: {e}")
            return None

        return self.monitor

    def stop_monitoring(self):
        """停止股票监控"""
        if self.monitor:
            print("🛑 正在停止股票监控...")
            self.monitor.stop_monitoring()
            print("✅ 监控已停止")

            # 生成最终报告
            try:
                session = self.monitor.current_session
                stock_states = self.monitor.get_stock_states()

                if session and session.signals_detected:
                    print(f"📊 监控会话摘要:")
                    print(f"   会话ID: {session.session_id}")
                    print(f"   检测到信号: {len(session.signals_detected)} 个")
                    print(f"   执行检查: {session.checks_performed} 次")

                    # 生成报告
                    self.monitoring_reporter.generate_daily_report(
                        session.signals_detected, session, stock_states
                    )
                    self.monitoring_reporter.generate_signal_summary(session.signals_detected)

                    print("📄 监控报告已生成")
                else:
                    print("📊 本次监控未检测到信号")

            except Exception as e:
                print(f"⚠️ 生成报告失败: {e}")

            self.monitor = None
        else:
            print("ℹ️  监控未在运行")

    def get_monitoring_status(self):
        """获取监控状态"""
        if self.monitor:
            status = self.monitor.get_monitoring_status()
            print("📊 监控状态:")
            print(f"   状态: {status['status']}")
            print(f"   会话ID: {status['session_id']}")
            print(f"   监控股票: {status['stocks_monitoring']} 只")
            print(f"   检查次数: {status['checks_performed']}")
            print(f"   检测信号: {status['signals_detected']} 个")
            if status['last_check_time']:
                from datetime import datetime
                last_check = datetime.fromisoformat(status['last_check_time'])
                print(f"   最后检查: {last_check.strftime('%H:%M:%S')}")
            print(f"   系统活跃: {'是' if status['is_active'] else '否'}")
        else:
            print("ℹ️  监控未在运行")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="优化后的巴菲特股息筛选系统 - 分层架构版本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  %(prog)s screen                    # 筛选所有高股息股票
  %(prog)s screen --min-dividend 6.0  # 筛选股息率≥6%%的股票
  %(prog)s target 600000 000001     # 分析指定股票
  %(prog)s target --file stocks.txt # 从文件读取股票代码
  %(prog)s monitor start            # 启动监控(默认sample_stocks.txt)
  %(prog)s monitor start --file custom.txt --interval 15  # 自定义文件和间隔
  %(prog)s monitor status           # 查看监控状态
  %(prog)s monitor stop             # 停止监控
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # 筛选命令
    screen_parser = subparsers.add_parser('screen', help='筛选高股息股票')
    screen_parser.add_argument('--min-dividend', type=float, default=4.0, help='最低股息率 (%)')

    # 指定股票分析命令
    target_parser = subparsers.add_parser('target', help='分析指定股票')
    target_parser.add_argument('symbols', nargs='*', help='股票代码列表')
    target_parser.add_argument('--file', type=str, help='包含股票代码的文件')

    # 监控命令
    monitor_parser = subparsers.add_parser('monitor', help='股票监控')
    monitor_subparsers = monitor_parser.add_subparsers(dest='monitor_action', help='监控操作')

    # 启动监控
    start_parser = monitor_subparsers.add_parser('start', help='启动监控')
    start_parser.add_argument('--file', type=str, default='sample_stocks.txt', help='股票文件路径')
    start_parser.add_argument('--interval', type=int, default=30, help='监控间隔(分钟)')

    # 停止监控
    monitor_subparsers.add_parser('stop', help='停止监控')

    # 查看监控状态
    monitor_subparsers.add_parser('status', help='查看监控状态')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    # 创建筛选器实例
    screener = BuffettScreener()

    try:
        if args.command == 'screen':
            print("🚀 启动巴菲特股息筛选系统...")
            print(f"📋 筛选条件: 股息率≥{args.min_dividend}%")

            screener.screen_dividend_stocks(args.min_dividend)

        elif args.command == 'target':
            print("🚀 启动指定股票分析...")

            # 获取股票列表
            symbols = []
            if args.symbols:
                symbols.extend(args.symbols)
            if args.file:
                symbols.extend(load_symbols_from_file(args.file))

            if not symbols:
                print("❌ 请提供股票代码")
                return 1

            screener.analyze_target_stocks(symbols)

        elif args.command == 'monitor':
            if not args.monitor_action:
                monitor_parser.print_help()
                return 1

            if args.monitor_action == 'start':
                screener.start_monitoring(args.file, args.interval)

            elif args.monitor_action == 'stop':
                screener.stop_monitoring()

            elif args.monitor_action == 'status':
                screener.get_monitoring_status()

            else:
                monitor_parser.print_help()
                return 1

        else:
            parser.print_help()
            return 1

    except KeyboardInterrupt:
        print("\n👋 程序已停止")
        return 0
    except Exception as e:
        print(f"❌ 程序执行失败: {e}")
        return 1

    # 显示错误信息
    if screener.errors:
        print(f"\n⚠️  执行过程中发生 {len(screener.errors)} 个错误:")
        for error in screener.errors[:5]:  # 只显示前5个错误
            print(f"   - {error}")

    return 0


if __name__ == "__main__":
    sys.exit(main())