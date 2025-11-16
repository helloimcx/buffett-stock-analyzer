#!/usr/bin/env python3
"""
简化的巴菲特股息筛选系统
使用AKShare直接获取中国A股数据，去除复杂的企业架构
"""

import argparse
import time
from datetime import datetime
from pathlib import Path
import json
import pandas as pd
import akshare as ak

class SimpleBuffettScreener:
    def __init__(self):
        self.results = []
        self.errors = []

    def safe_float(self, value, default=0.0):
        """安全地将值转换为float，处理None和异常情况"""
        try:
            if value is None or value == '' or value == '-':
                return default
            return float(value)
        except (ValueError, TypeError):
            return default

    def get_all_stocks_data(self):
        """获取所有A股实时数据"""
        try:
            print("📊 正在获取A股市场数据...")
            df = ak.stock_zh_a_spot()
            print(f"✅ 成功获取 {len(df)} 只股票数据")
            return df
        except Exception as e:
            print(f"❌ 获取股票数据失败: {e}")
            return pd.DataFrame()

    def get_stock_detail(self, symbol):
        """获取单只股票详细信息"""
        try:
            # 标准化股票代码格式
            symbol = symbol.upper().strip()

            # 确定交易所前缀
            if symbol.startswith('6'):
                # 上海证券交易所，主板以6开头
                ak_symbol = f"SH{symbol}"
            elif symbol.startswith('0') or symbol.startswith('3'):
                # 深圳证券交易所，主板以0开头，创业板以3开头
                ak_symbol = f"SZ{symbol}"
            elif symbol.startswith('SH') or symbol.startswith('SZ'):
                # 已经有正确前缀
                ak_symbol = symbol
            else:
                # 默认尝试上海
                ak_symbol = f"SH{symbol}"

            return ak.stock_individual_spot_xq(symbol=ak_symbol)
        except Exception as e:
            print(f"⚠️  获取 {symbol} 详细信息失败: {e}")
            return pd.DataFrame()

    def screen_dividend_stocks(self, df, min_dividend_yield=4.0):
        """筛选高股息股票"""
        print(f"🔍 筛选股息率≥{min_dividend_yield}%的股票...")

        dividend_stocks = []

        # 从基础数据中筛选有潜力的股票
        # 过滤掉ST股票和价格过低的股票
        potential_stocks = df[
            (~df['名称'].str.contains('ST', na=False)) &  # 排除ST股票
            (df['最新价'] > 2) &  # 价格大于2元
            (df['最新价'] < 100) &  # 价格小于100元
            (df['成交量'] > 1000000)  # 成交量大于100万
        ].copy()

        print(f"🎯 从 {len(potential_stocks)} 只有潜力的股票中筛选...")

        # 获取详细信息进行股息率筛选
        for _, stock in potential_stocks.iterrows():
            try:
                symbol = stock['代码']
                name = stock['名称']

                # 获取详细信息
                detail_df = self.get_stock_detail(symbol)
                if detail_df.empty:
                    continue

                # 转换为字典便于访问
                detail_data = dict(zip(detail_df['item'], detail_df['value']))

                # 提取关键指标
                dividend_yield = self.safe_float(detail_data.get('股息率(TTM)'))
                pe_ratio = self.safe_float(detail_data.get('市盈率(动)'))
                pb_ratio = self.safe_float(detail_data.get('市净率'))
                current_price = self.safe_float(detail_data.get('现价'), stock['最新价'])

                # 筛选高股息股票
                if dividend_yield >= min_dividend_yield:
                    stock_info = {
                        'code': symbol,
                        'name': name,
                        'price': current_price,
                        'dividend_yield': dividend_yield,
                        'pe_ratio': pe_ratio,
                        'pb_ratio': pb_ratio,
                        'change_pct': stock['涨跌幅'],
                        'volume': stock['成交量'],
                        'market_cap': self.safe_float(detail_data.get('流通值')),
                        'eps': self.safe_float(detail_data.get('每股收益')),
                        'book_value': self.safe_float(detail_data.get('每股净资产')),
                        '52w_high': self.safe_float(detail_data.get('52周最高')),
                        '52w_low': self.safe_float(detail_data.get('52周最低')),
                    }

                    # 计算综合评分
                    score = self.calculate_investment_score(stock_info)
                    stock_info['total_score'] = score

                    dividend_stocks.append(stock_info)

                    # 显示进度
                    if len(dividend_stocks) % 10 == 0:
                        print(f"   已找到 {len(dividend_stocks)} 只符合条件的股票...")

                # 避免请求过快
                time.sleep(0.1)

            except Exception as e:
                self.errors.append(f"处理 {stock.get('代码', 'unknown')} 时出错: {e}")
                continue

        # 按综合评分排序
        dividend_stocks.sort(key=lambda x: x['total_score'], reverse=True)

        print(f"✅ 筛选完成，找到 {len(dividend_stocks)} 只高股息股票")
        return dividend_stocks

    def calculate_investment_score(self, stock_info):
        """计算投资评分 (0-100)"""
        score = 0

        # 股息率评分 (40%)
        dividend_yield = stock_info['dividend_yield']
        if dividend_yield >= 6:
            score += 40
        elif dividend_yield >= 4:
            score += 30
        elif dividend_yield >= 3:
            score += 20

        # 估值评分 (30%)
        pe_ratio = stock_info['pe_ratio']
        pb_ratio = stock_info['pb_ratio']

        if 0 < pe_ratio < 15:
            score += 15
        elif 15 <= pe_ratio < 25:
            score += 10

        if 0 < pb_ratio < 1.5:
            score += 15
        elif 1.5 <= pb_ratio < 3:
            score += 10

        # 52周位置评分 (20%)
        high_52w = stock_info['52w_high']
        low_52w = stock_info['52w_low']
        current_price = stock_info['price']

        if high_52w > 0 and low_52w > 0:
            position = (current_price - low_52w) / (high_52w - low_52w)
            if position < 0.3:  # 接近52周低点
                score += 20
            elif position < 0.5:
                score += 15
            elif position < 0.7:
                score += 10

        # 基本面评分 (10%)
        if stock_info['eps'] > 0:
            score += 5
        if stock_info['book_value'] > stock_info['price'] * 0.5:
            score += 5

        return min(score, 100)

    def analyze_specific_stocks(self, symbols):
        """分析指定的股票列表"""
        results = []

        print(f"🎯 分析 {len(symbols)} 只指定股票...")

        for symbol in symbols:
            try:
                # 获取详细信息
                detail_df = self.get_stock_detail(symbol)
                if detail_df.empty:
                    print(f"   ⚠️  跳过 {symbol}: 无法获取数据")
                    continue

                detail_data = dict(zip(detail_df['item'], detail_df['value']))

                # 基本数据验证
                stock_name = detail_data.get('名称', 'Unknown')
                if stock_name == 'Unknown' or not stock_name:
                    print(f"   ⚠️  跳过 {symbol}: 股票名称无效")
                    continue

                stock_info = {
                    'code': symbol,
                    'name': stock_name,
                    'price': self.safe_float(detail_data.get('现价')),
                    'dividend_yield': self.safe_float(detail_data.get('股息率(TTM)')),
                    'pe_ratio': self.safe_float(detail_data.get('市盈率(动)')),
                    'pb_ratio': self.safe_float(detail_data.get('市净率')),
                    'eps': self.safe_float(detail_data.get('每股收益')),
                    'book_value': self.safe_float(detail_data.get('每股净资产')),
                    '52w_high': self.safe_float(detail_data.get('52周最高')),
                    '52w_low': self.safe_float(detail_data.get('52周最低')),
                }

                # 价格验证
                if stock_info['price'] <= 0:
                    print(f"   ⚠️  跳过 {stock_name} ({symbol}): 价格数据异常")
                    continue

                # 计算评分
                stock_info['total_score'] = self.calculate_investment_score(stock_info)
                results.append(stock_info)

                print(f"   ✅ {stock_name} ({symbol}) - 评分: {stock_info['total_score']:.1f}")

                time.sleep(0.2)  # 避免请求过快

            except Exception as e:
                print(f"   ❌ 分析 {symbol} 失败: {e}")
                self.errors.append(f"分析 {symbol} 时出错: {str(e)}")
                continue

        return results

    def display_results(self, stocks, title="筛选结果"):
        """显示筛选结果"""
        if not stocks:
            print("📊 没有找到符合条件的股票")
            return

        print(f"\n📊 {title}: {len(stocks)} 只股票")
        print("=" * 100)
        print(f"{'排名':<4} {'股票代码':<10} {'股票名称':<12} {'价格':<8} {'股息率':<8} {'P/E':<8} {'P/B':<8} {'评分':<6} {'52周位置':<10}")
        print("-" * 100)

        for i, stock in enumerate(stocks, 1):
            # 计算52周位置
            position_text = "N/A"
            if stock['52w_high'] > 0 and stock['52w_low'] > 0:
                position = (stock['price'] - stock['52w_low']) / (stock['52w_high'] - stock['52w_low'])
                position_pct = position * 100
                if position_pct < 30:
                    position_text = f"低位({position_pct:.0f}%)"
                elif position_pct < 70:
                    position_text = f"中位({position_pct:.0f}%)"
                else:
                    position_text = f"高位({position_pct:.0f}%)"

            print(f"{i:<4} {stock['code']:<10} {stock['name']:<12} ¥{stock['price']:<7.2f} {stock['dividend_yield']:<7.2f}% {stock['pe_ratio']:<7.2f} {stock['pb_ratio']:<7.2f} {stock['total_score']:<6.1f} {position_text:<10}")

        print("=" * 100)

    def save_results(self, stocks, filename_suffix=""):
        """保存结果到文件"""
        if not stocks:
            return

        try:
            # 创建报告目录
            reports_dir = Path("reports")
            reports_dir.mkdir(exist_ok=True)

            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"buffett_screening_{filename_suffix}_{timestamp}.json"
            filepath = reports_dir / filename

            # 准备保存数据
            save_data = {
                'timestamp': datetime.now().isoformat(),
                'total_stocks': len(stocks),
                'criteria': {
                    'min_dividend_yield': 4.0,
                    'max_price': 100,
                    'min_price': 2
                },
                'stocks': stocks
            }

            # 保存到文件
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)

            print(f"💾 结果已保存到: {filepath}")

        except Exception as e:
            print(f"⚠️  保存结果失败: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="简化的巴菲特股息筛选系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  %(prog)s screen                    # 筛选所有高股息股票
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
        return

    # 创建筛选器实例
    screener = SimpleBuffettScreener()

    try:
        if args.command == 'screen':
            print("🚀 启动巴菲特股息筛选系统...")
            print(f"📋 筛选条件: 股息率≥{args.min_dividend}%")

            # 获取所有股票数据
            stocks_df = screener.get_all_stocks_data()
            if stocks_df.empty:
                print("❌ 无法获取股票数据")
                return

            # 筛选高股息股票
            dividend_stocks = screener.screen_dividend_stocks(stocks_df, args.min_dividend)

            # 显示结果
            screener.display_results(dividend_stocks, f"股息率≥{args.min_dividend}%的股票")

            # 保存结果
            screener.save_results(dividend_stocks, f"dividend_{args.min_dividend}pct")

        elif args.command == 'target':
            symbols = []

            # 从命令行参数获取股票代码
            if args.symbols:
                symbols.extend(args.symbols)

            # 从文件获取股票代码
            if args.file:
                try:
                    with open(args.file, 'r', encoding='utf-8') as f:
                        file_symbols = [line.strip() for line in f
                                      if line.strip() and not line.strip().startswith('#')]
                        symbols.extend(file_symbols)
                except Exception as e:
                    print(f"❌ 读取文件失败: {e}")
                    return

            if not symbols:
                print("❌ 请提供股票代码")
                return

            print("🚀 启动指定股票分析...")

            # 分析指定股票
            target_stocks = screener.analyze_specific_stocks(symbols)

            # 显示结果
            screener.display_results(target_stocks, "指定股票分析结果")

            # 保存结果
            screener.save_results(target_stocks, "target_analysis")

    except KeyboardInterrupt:
        print("\n👋 程序已停止")
    except Exception as e:
        print(f"❌ 程序执行失败: {e}")

    # 显示错误信息
    if screener.errors:
        print(f"\n⚠️  执行过程中发生 {len(screener.errors)} 个错误:")
        for error in screener.errors[:5]:  # 只显示前5个错误
            print(f"   - {error}")


if __name__ == "__main__":
    main()