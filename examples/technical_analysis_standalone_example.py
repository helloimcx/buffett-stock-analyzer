"""
技术分析模块独立示例
展示如何使用新的技术分析功能，不依赖其他模块
"""

import sys
import os
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 直接导入技术分析模块，避免其他依赖
from src.buffett.strategies.technical_analysis import (
    TechnicalIndicator,
    MovingAverage,
    RSI,
    MACD,
    BollingerBands,
    VolumePriceAnalyzer,
    TechnicalSignalGenerator,
    TechnicalAnalysisResult
)
from src.buffett.strategies.enhanced_technical_factor import EnhancedTechnicalFactor
from src.buffett.strategies.backtesting import TechnicalBacktester
from src.buffett.strategies.technical_visualization import TechnicalVisualizationGenerator


def create_sample_stock_data():
    """创建示例股票数据"""
    # 创建模拟的历史价格数据
    base_price = 10.0
    prices = []
    volumes = []
    
    for i in range(60):  # 60天的历史数据
        # 添加一些趋势和波动
        trend = i * 0.02  # 上涨趋势
        noise = (i % 7 - 3) * 0.1  # 随机波动
        price = base_price + trend + noise
        
        prices.append(price)
        volumes.append(1000000 + i * 10000)  # 逐渐增加的成交量
    
    return prices, volumes


def example_basic_indicators():
    """基础技术指标使用示例"""
    print("=== 基础技术指标示例 ===")
    
    # 创建示例数据
    prices, volumes = create_sample_stock_data()
    
    # 创建移动平均线指标
    ma_short = MovingAverage(period=10, ma_type='sma')
    ma_long = MovingAverage(period=30, ma_type='ema')
    
    # 计算移动平均线
    ma_short_value = ma_short.calculate(prices)
    ma_long_value = ma_long.calculate(prices)
    
    print(f"10日简单移动平均线: {ma_short_value:.4f}")
    print(f"30日指数移动平均线: {ma_long_value:.4f}")
    
    # 创建RSI指标
    rsi = RSI(period=14)
    rsi_value = rsi.calculate(prices)
    print(f"RSI(14): {rsi_value:.2f}")
    
    # 创建MACD指标
    macd = MACD(fast_period=12, slow_period=26, signal_period=9)
    macd_result = macd.calculate(prices)
    
    if macd_result:
        macd_line, signal_line, histogram = macd_result
        print(f"MACD线: {macd_line:.4f}")
        print(f"信号线: {signal_line:.4f}")
        print(f"柱状图: {histogram:.4f}")
    
    # 创建布林带指标
    bb = BollingerBands(period=20, std_dev=2.0)
    bb_result = bb.calculate(prices)
    
    if bb_result:
        upper_band, middle_band, lower_band = bb_result
        current_price = prices[-1]
        position = bb.calculate_price_position(current_price, upper_band, lower_band)
        
        print(f"布林带上轨: {upper_band:.4f}")
        print(f"布林带中轨: {middle_band:.4f}")
        print(f"布林带下轨: {lower_band:.4f}")
        print(f"当前价格位置: {position:.2f}")
    
    # 量价分析
    analyzer = VolumePriceAnalyzer()
    trend_analysis = analyzer.analyze_trend(prices, volumes)
    divergence = analyzer.detect_divergence(prices, volumes)
    
    print(f"价格趋势: {trend_analysis['price_trend']}")
    print(f"成交量趋势: {trend_analysis['volume_trend']}")
    print(f"相关性: {trend_analysis['correlation']:.4f}")
    print(f"价量背离: {divergence}")
    
    print()


def example_signal_generation():
    """技术信号生成示例"""
    print("=== 技术信号生成示例 ===")
    
    # 创建示例数据
    prices, volumes = create_sample_stock_data()
    
    # 创建信号生成器
    signal_generator = TechnicalSignalGenerator()
    
    # 生成信号
    signals = signal_generator.generate_signals(prices, volumes)
    signal_strength = signal_generator.calculate_signal_strength(prices, volumes)
    
    print("买入信号:")
    for signal in signals['buy_signals']:
        print(f"  - {signal['indicator']}: 强度 {signal['strength']:.2f}")
    
    print("卖出信号:")
    for signal in signals['sell_signals']:
        print(f"  - {signal['indicator']}: 强度 {signal['strength']:.2f}")
    
    print("中性信号:")
    for signal in signals['neutral_signals']:
        print(f"  - {signal['indicator']}: 强度 {signal['strength']:.2f}")
    
    print(f"综合信号强度: {signal_strength:.4f}")
    print()


def example_enhanced_technical_factor():
    """增强技术因子示例"""
    print("=== 增强技术因子示例 ===")
    
    # 创建增强技术因子
    enhanced_factor = EnhancedTechnicalFactor(weight=1.0)
    
    # 创建示例股票数据
    from dataclasses import dataclass
    
    @dataclass
    class MockStockInfo:
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
    
    stock = MockStockInfo(
        code="DEMO001",
        name="演示股票",
        price=12.5,
        dividend_yield=3.5,
        pe_ratio=15.0,
        pb_ratio=2.0,
        change_pct=1.5,
        volume=1500000,
        market_cap=1000000000,
        eps=2.0,
        book_value=6.0,
        week_52_high=15.0,
        week_52_low=8.0
    )
    
    # 模拟多次调用来积累历史数据
    for i in range(30):
        # 更新价格模拟历史数据
        stock.price = 12.5 + i * 0.1
        score = enhanced_factor.calculate(stock)
    
    # 获取最终得分和技术分析结果
    final_score = enhanced_factor.calculate(stock)
    technical_result = enhanced_factor.get_technical_analysis_result(stock)
    
    print(f"增强技术因子得分: {final_score:.4f}")
    
    if technical_result:
        print("技术分析结果:")
        print(f"  时间: {technical_result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  指标数量: {len(technical_result.indicators)}")
        print(f"  信号数量: {len(technical_result.signals.get('buy_signals', [])) + len(technical_result.signals.get('sell_signals', []))}")
        print(f"  综合得分: {technical_result.score:.4f}")
    
    print()


def example_backtesting():
    """回测示例"""
    print("=== 回测示例 ===")
    
    # 创建历史数据
    prices, volumes = create_sample_stock_data()
    
    # 转换为回测所需格式
    historical_data = []
    base_date = datetime.now() - timedelta(days=len(prices))
    
    for i, (price, volume) in enumerate(zip(prices, volumes)):
        historical_data.append({
            'date': base_date + timedelta(days=i),
            'price': price,
            'volume': volume
        })
    
    # 创建回测器
    backtester = TechnicalBacktester(
        initial_capital=100000.0,
        commission_rate=0.001,
        slippage=0.001,
        stop_loss_pct=0.05,
        take_profit_pct=0.10,
        max_position_pct=0.2
    )
    
    # 执行回测
    result = backtester.backtest(historical_data, "DEMO001")
    
    print("回测结果:")
    print(f"  初始资金: ¥{result.initial_capital:,.2f}")
    print(f"  最终资金: ¥{result.final_capital:,.2f}")
    print(f"  总收益: ¥{result.total_return:,.2f}")
    print(f"  总收益率: {result.total_return_pct:.2%}")
    print(f"  最大回撤: {result.max_drawdown_pct:.2%}")
    print(f"  胜率: {result.win_rate:.2%}")
    print(f"  盈亏比: {result.profit_factor:.2f}")
    print(f"  总交易次数: {result.total_trades}")
    print(f"  平均交易: ¥{result.avg_trade:,.2f}")
    
    if result.sharpe_ratio is not None:
        print(f"  夏普比率: {result.sharpe_ratio:.2f}")
    
    print()


def example_visualization():
    """可视化示例"""
    print("=== 可视化示例 ===")
    
    # 创建示例数据
    prices, volumes = create_sample_stock_data()
    
    # 创建技术分析结果
    technical_result = TechnicalAnalysisResult(
        symbol="DEMO001",
        timestamp=datetime.now(),
        indicators={
            'MA_10': sum(prices[-10:]) / 10,
            'MA_30': sum(prices[-30:]) / 30,
            'RSI': 45.2,
            'MACD': 0.15,
            'BB_position': 0.6
        },
        signals={
            'buy_signals': [
                {'indicator': 'MA', 'strength': 0.7},
                {'indicator': 'RSI', 'strength': 0.8}
            ],
            'sell_signals': [
                {'indicator': 'MACD', 'strength': 0.6}
            ],
            'neutral_signals': []
        },
        score=0.75
    )
    
    # 创建可视化生成器
    visualizer = TechnicalVisualizationGenerator(output_dir="reports/technical_analysis")
    
    # 生成HTML报告
    html_file = visualizer.generate_technical_analysis_chart(technical_result, chart_type="html")
    print(f"HTML报告已生成: {html_file}")
    
    # 生成JSON数据
    json_file = visualizer.generate_technical_analysis_chart(technical_result, chart_type="json")
    print(f"JSON数据已生成: {json_file}")
    
    # 生成数据文件
    data_file = visualizer.generate_technical_analysis_chart(technical_result, chart_type="data")
    print(f"数据文件已生成: {data_file}")
    
    print()


def main():
    """主函数"""
    print("巴菲特股息筛选系统 - 技术分析模块独立示例")
    print("=" * 50)
    
    try:
        # 运行各种示例
        example_basic_indicators()
        example_signal_generation()
        example_enhanced_technical_factor()
        example_backtesting()
        example_visualization()
        
        print("=" * 50)
        print("所有示例运行完成！")
        print("\n使用说明:")
        print("1. 基础技术指标提供了MA、RSI、MACD、布林带等常用指标")
        print("2. 技术信号生成器可以综合多个指标生成交易信号")
        print("3. 增强技术因子集成了多种技术指标，可以与现有多因子系统配合使用")
        print("4. 回测功能支持历史数据回测和策略性能评估")
        print("5. 可视化功能可以生成HTML、JSON和数据格式的分析报告")
        print("\n注意事项:")
        print("- 技术分析仅供参考，投资有风险，入市需谨慎")
        print("- 建议结合基本面分析进行投资决策")
        print("- 回测结果是历史表现，不代表未来收益")
        
    except Exception as e:
        print(f"运行示例时出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()