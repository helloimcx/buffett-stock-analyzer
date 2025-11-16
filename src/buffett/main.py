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

from src.buffett.models import ScreeningResult
from src.buffett.strategies import DividendScreeningStrategy, TargetStockAnalysisStrategy
from src.buffett.utils import StockReporter, load_symbols_from_file
from src.buffett.core import config


class BuffettScreener:
    """巴菲特股息筛选器主类"""

    def __init__(self):
        self.reporter = StockReporter(config.reports_dir)
        self.errors: List[str] = []

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