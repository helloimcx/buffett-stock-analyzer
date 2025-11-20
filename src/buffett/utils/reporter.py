"""
报告生成器
处理结果显示和文件输出
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict
import csv

from ..models import StockInfo, ScreeningResult
from ..models.monitoring import TradingSignal, MonitoringSession, StockMonitoringState


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


class MonitoringReporter:
    """监控报告生成器"""

    def __init__(self, output_dir: str = "reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def generate_daily_report(self,
                             signals: List[TradingSignal],
                             session: MonitoringSession,
                             stock_states: Dict[str, StockMonitoringState]) -> str:
        """生成每日监控报告"""
        today = datetime.now().strftime("%Y%m%d")
        report_file = self.output_dir / f"daily_report_{today}.html"

        # 统计信息
        buy_signals = [s for s in signals if s.signal_type.value == "buy"]
        sell_signals = [s for s in signals if s.signal_type.value == "sell"]

        # 生成HTML报告
        html_content = self._generate_html_report(
            title=f"股票监控日报 - {datetime.now().strftime('%Y年%m月%d日')}",
            signals=signals,
            session=session,
            stock_states=stock_states,
            buy_signals=buy_signals,
            sell_signals=sell_signals
        )

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return str(report_file)

    def generate_signal_summary(self, signals: List[TradingSignal]) -> str:
        """生成信号汇总报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_file = self.output_dir / f"signal_summary_{timestamp}.json"

        # 按股票分组信号
        signals_by_stock = {}
        for signal in signals:
            if signal.stock_code not in signals_by_stock:
                signals_by_stock[signal.stock_code] = []
            signals_by_stock[signal.stock_code].append({
                "type": signal.signal_type.value,
                "strength": signal.signal_strength.value,
                "time": signal.timestamp.isoformat(),
                "price": signal.price,
                "score": signal.score,
                "reasons": signal.reasons
            })

        # 生成汇总数据
        summary_data = {
            "timestamp": datetime.now().isoformat(),
            "total_signals": len(signals),
            "buy_signals": len([s for s in signals if s.signal_type.value == "buy"]),
            "sell_signals": len([s for s in signals if s.signal_type.value == "sell"]),
            "signals_by_stock": signals_by_stock,
            "strong_signals": [
                {
                    "stock_code": s.stock_code,
                    "stock_name": s.stock_name,
                    "signal_type": s.signal_type.value,
                    "reasons": s.reasons,
                    "score": s.score,
                    "price": s.price
                }
                for s in signals if s.signal_strength.value == "strong"
            ]
        }

        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, ensure_ascii=False, indent=2)

        return str(summary_file)

    def generate_csv_report(self, signals: List[TradingSignal]) -> str:
        """生成CSV报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_file = self.output_dir / f"signals_{timestamp}.csv"

        if not signals:
            return str(csv_file)

        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # 写入标题行
            writer.writerow([
                '时间', '股票代码', '股票名称', '信号类型', '信号强度',
                '价格', '评分', '目标价', '止损价', '触发原因'
            ])

            # 写入数据行
            for signal in signals:
                writer.writerow([
                    signal.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    signal.stock_code,
                    signal.stock_name,
                    '买入' if signal.signal_type.value == 'buy' else '卖出',
                    {'weak': '弱', 'medium': '中', 'strong': '强'}[signal.signal_strength.value],
                    f"{signal.price:.2f}",
                    f"{signal.score:.1f}",
                    f"{signal.target_price:.2f}" if signal.target_price else '',
                    f"{signal.stop_loss:.2f}" if signal.stop_loss else '',
                    '; '.join(signal.reasons)
                ])

        return str(csv_file)

    def display_signals(self, signals: List[TradingSignal]) -> None:
        """在控制台显示交易信号"""
        if not signals:
            print("📊 没有检测到交易信号")
            return

        # 按信号强度和类型分组显示
        strong_signals = [s for s in signals if s.signal_strength.value == "strong"]
        medium_signals = [s for s in signals if s.signal_strength.value == "medium"]
        weak_signals = [s for s in signals if s.signal_strength.value == "weak"]

        for strength_group, strength_name, title in [
            (strong_signals, "强", "🔥 强信号"),
            (medium_signals, "中等", "⚡ 中等信号"),
            (weak_signals, "弱", "💡 弱信号")
        ]:
            if strength_group:
                print(f"\n{title} ({len(strength_group)}个):")
                print("-" * 80)

                for signal in strength_group:
                    signal_type = "🟢 买入" if signal.signal_type.value == "buy" else "🔴 卖出"

                    print(f"{signal_type} {signal.stock_name} ({signal.stock_code})")
                    print(f"  价格: ¥{signal.price:.2f} | 评分: {signal.score:.1f}")

                    if signal.target_price:
                        print(f"  目标价: ¥{signal.target_price:.2f}")
                    if signal.stop_loss:
                        print(f"  止损价: ¥{signal.stop_loss:.2f}")

                    print(f"  理由: {', '.join(signal.reasons)}")
                    print(f"  时间: {signal.timestamp.strftime('%H:%M:%S')}")
                    print("-" * 80)

    def _generate_html_report(self,
                             title: str,
                             signals: List[TradingSignal],
                             session: MonitoringSession,
                             stock_states: Dict[str, StockMonitoringState],
                             buy_signals: List[TradingSignal],
                             sell_signals: List[TradingSignal]) -> str:
        """生成HTML报告内容"""

        # 统计信息
        strong_signals = [s for s in signals if s.signal_strength.value == "strong"]

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .stats {{ display: flex; gap: 20px; margin: 20px 0; }}
                .stat-box {{ background-color: #e8f4fd; padding: 15px; border-radius: 5px; text-align: center; min-width: 120px; }}
                .signal {{ border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }}
                .buy-signal {{ border-left: 5px solid #28a745; background-color: #f8fff9; }}
                .sell-signal {{ border-left: 5px solid #dc3545; background-color: #fff8f8; }}
                .strong {{ font-weight: bold; }}
                .reasons {{ color: #666; font-style: italic; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{title}</h1>
                <p>监控会话: {session.session_id}</p>
                <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>

            <div class="stats">
                <div class="stat-box">
                    <h3>总信号数</h3>
                    <h2>{len(signals)}</h2>
                </div>
                <div class="stat-box">
                    <h3>买入信号</h3>
                    <h2 style="color: #28a745;">{len(buy_signals)}</h2>
                </div>
                <div class="stat-box">
                    <h3>卖出信号</h3>
                    <h2 style="color: #dc3545;">{len(sell_signals)}</h2>
                </div>
                <div class="stat-box">
                    <h3>强信号</h3>
                    <h2 style="color: #ff6b35;">{len(strong_signals)}</h2>
                </div>
            </div>

            <h2>🔥 重点关注信号</h2>
        """

        # 强信号
        if strong_signals:
            for signal in strong_signals:
                signal_type = "🟢 买入" if signal.signal_type.value == "buy" else "🔴 卖出"
                html += f"""
                <div class="signal {'buy-signal' if signal.signal_type.value == 'buy' else 'sell-signal'}">
                    <h3>{signal_type} - {signal.stock_name} ({signal.stock_code})</h3>
                    <p><strong>价格:</strong> ¥{signal.price:.2f} | <strong>评分:</strong> {signal.score:.1f}</p>
                    {f'<p><strong>目标价:</strong> ¥{signal.target_price:.2f} | <strong>止损价:</strong> ¥{signal.stop_loss:.2f}</p>' if signal.target_price else ''}
                    <p class="reasons"><strong>触发原因:</strong> {', '.join(signal.reasons)}</p>
                    <p><small>触发时间: {signal.timestamp.strftime('%H:%M:%S')}</small></p>
                </div>
                """
        else:
            html += "<p>暂无强信号</p>"

        html += f"""
            <h2>📊 监控状态</h2>
            <table>
                <tr>
                    <th>指标</th>
                    <th>数值</th>
                </tr>
                <tr>
                    <td>监控股票数量</td>
                    <td>{len(stock_states)}</td>
                </tr>
                <tr>
                    <td>检查次数</td>
                    <td>{session.checks_performed}</td>
                </tr>
                <tr>
                    <td>监控时长</td>
                    <td>{self._format_duration(session.start_time, session.end_time or datetime.now())}</td>
                </tr>
                <tr>
                    <td>会话状态</td>
                    <td>{session.status}</td>
                </tr>
            </table>

        </body>
        </html>
        """

        return html

    def _format_duration(self, start: datetime, end: datetime) -> str:
        """格式化时间间隔"""
        duration = end - start
        hours = duration.total_seconds() / 3600
        if hours < 1:
            minutes = duration.total_seconds() / 60
            return f"{int(minutes)}分钟"
        else:
            return f"{hours:.1f}小时"