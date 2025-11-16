"""
报告生成器
处理结果显示和文件输出
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List

from ..models import StockInfo, ScreeningResult


class StockReporter:
    """股票筛选报告生成器"""

    def __init__(self, reports_dir: str = "reports"):
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(exist_ok=True)

    def display_results(self, stocks: List[StockInfo], title: str = "筛选结果") -> None:
        """在控制台显示筛选结果"""
        if not stocks:
            print("📊 没有找到符合条件的股票")
            return

        print(f"\n📊 {title}: {len(stocks)} 只股票")
        print("=" * 120)
        print(f"{'排名':<4} {'股票代码':<10} {'股票名称':<12} {'价格':<8} {'股息率':<8} {'P/E':<8} {'P/B':<8} {'评分':<6} {'52周位置':<10}")
        print("-" * 120)

        for i, stock in enumerate(stocks, 1):
            # 计算52周位置
            position_text = self._calculate_52w_position_text(stock)

            print(
                f"{i:<4} {stock.code:<10} {stock.name:<12} "
                f"¥{stock.price:<7.2f} {stock.dividend_yield:<7.2f}% "
                f"{stock.pe_ratio:<7.2f} {stock.pb_ratio:<7.2f} "
                f"{stock.total_score:<6.1f} {position_text:<10}"
            )

        print("=" * 120)

    def _calculate_52w_position_text(self, stock: StockInfo) -> str:
        """计算52周位置文本"""
        if stock.week_52_high > 0 and stock.week_52_low > 0:
            position = (stock.price - stock.week_52_low) / (stock.week_52_high - stock.week_52_low)
            position_pct = position * 100

            if position_pct < 30:
                return f"低位({position_pct:.0f}%)"
            elif position_pct < 70:
                return f"中位({position_pct:.0f}%)"
            else:
                return f"高位({position_pct:.0f}%)"
        return "N/A"

    def save_results(self, result: ScreeningResult, filename_suffix: str = "") -> str:
        """保存筛选结果到JSON文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"buffett_screening_{filename_suffix}_{timestamp}.json" if filename_suffix else f"buffett_screening_{timestamp}.json"
        filepath = self.reports_dir / filename

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)

            print(f"💾 结果已保存到: {filepath}")
            return str(filepath)

        except Exception as e:
            print(f"⚠️  保存结果失败: {e}")
            return ""

    def create_screening_result(self, stocks: List[StockInfo], criteria, total_analyzed: int, errors: List[str]) -> ScreeningResult:
        """创建筛选结果对象"""
        return ScreeningResult(
            timestamp=datetime.now(),
            criteria=criteria,
            total_stocks_analyzed=total_analyzed,
            passed_stocks=stocks,
            errors=errors
        )

    def display_summary(self, result: ScreeningResult) -> None:
        """显示筛选摘要"""
        print(f"\n📊 筛选摘要:")
        print(f"   分析时间: {result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   总分析数量: {result.total_stocks_analyzed} 只")
        print(f"   通过数量: {len(result.passed_stocks)} 只")
        if result.total_stocks_analyzed > 0:
            print(f"   通过率: {len(result.passed_stocks) / result.total_stocks_analyzed * 100:.1f}%")

        if result.errors:
            print(f"   错误数量: {len(result.errors)}")

        if result.passed_stocks:
            avg_score = sum(stock.total_score for stock in result.passed_stocks) / len(result.passed_stocks)
            print(f"   平均评分: {avg_score:.1f}")
            print(f"   最高评分: {result.passed_stocks[0].total_score:.1f}" if result.passed_stocks else "")
            print(f"   最低评分: {result.passed_stocks[-1].total_score:.1f}" if result.passed_stocks else "")