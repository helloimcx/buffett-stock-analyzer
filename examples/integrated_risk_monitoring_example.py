"""
集成风险监控示例
演示如何将风险管理系统与现有监控系统结合使用
"""

import sys
import os
import numpy as np
from datetime import datetime, timedelta

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.buffett.core.risk_management import RiskManager, RiskConfig, RiskStrategy
from src.buffett.core.monitor import StockMonitor
from src.buffett.models.monitoring import MonitoringConfig
from src.buffett.models.stock import StockInfo


def create_monitoring_config():
    """创建监控配置"""
    return MonitoringConfig(
        stock_symbols=["600519", "000858", "601318", "000002"],
        monitoring_interval=60,  # 60分钟
        buy_score_threshold=70.0,
        sell_score_threshold=30.0,
        enable_notifications=True,
        notification_methods=["console"]
    )


def create_risk_config(strategy_type=RiskStrategy.BALANCED):
    """创建风险管理配置"""
    return RiskConfig(
        strategy=strategy_type,
        lookback_days=30,
        enable_risk_alerts=True
    )


def simulate_market_data():
    """模拟市场数据"""
    stocks = [
        StockInfo(
            code="600519",
            name="贵州茅台",
            price=1800.0,
            dividend_yield=1.2,
            pe_ratio=35.0,
            pb_ratio=10.0,
            change_pct=0.02,
            volume=5000000,
            market_cap=2250000000000.0,
            eps=51.4,
            book_value=180.0,
            week_52_high=2150.0,
            week_52_low=1600.0
        ),
        StockInfo(
            code="000858",
            name="五粮液",
            price=200.0,
            dividend_yield=2.5,
            pe_ratio=25.0,
            pb_ratio=6.0,
            change_pct=0.01,
            volume=8000000,
            market_cap=780000000000.0,
            eps=8.0,
            book_value=33.3,
            week_52_high=250.0,
            week_52_low=170.0
        ),
        StockInfo(
            code="601318",
            name="中国平安",
            price=50.0,
            dividend_yield=4.0,
            pe_ratio=10.0,
            pb_ratio=1.2,
            change_pct=-0.01,
            volume=15000000,
            market_cap=910000000000.0,
            eps=5.0,
            book_value=41.7,
            week_52_high=65.0,
            week_52_low=45.0
        ),
        StockInfo(
            code="000002",
            name="万科A",
            price=20.0,
            dividend_yield=3.5,
            pe_ratio=8.0,
            pb_ratio=1.0,
            change_pct=-0.02,
            volume=20000000,
            market_cap=220000000000.0,
            eps=2.5,
            book_value=20.0,
            week_52_high=30.0,
            week_52_low=18.0
        )
    ]
    return stocks


def update_stock_prices(stocks, day):
    """更新股票价格（模拟市场变动）"""
    np.random.seed(day)  # 确保可重现性
    
    for stock in stocks:
        # 模拟日收益率
        daily_return = np.random.normal(0.001, 0.02)
        price_change = stock.price * daily_return
        stock.price += price_change
        stock.change_pct = daily_return
        
        # 模拟成交量变动
        volume_change = np.random.normal(0, 0.1)
        stock.volume = int(stock.volume * (1 + volume_change))
        
        # 更新52周高低点
        if stock.price > stock.week_52_high:
            stock.week_52_high = stock.price
        elif stock.price < stock.week_52_low:
            stock.week_52_low = stock.price


def demonstrate_integrated_monitoring():
    """演示集成监控"""
    print("=" * 60)
    print("巴菲特投资助手 - 集成风险监控系统演示")
    print("=" * 60)
    
    # 创建配置
    monitoring_config = create_monitoring_config()
    risk_config = create_risk_config(RiskStrategy.BALANCED)
    
    # 创建监控器和风险管理器
    stock_monitor = StockMonitor(monitoring_config)
    risk_manager = RiskManager(risk_config)
    
    # 获取初始股票数据
    stocks = simulate_market_data()
    
    # 设置投资组合权重
    portfolio_weights = {
        "600519": 0.3,
        "000858": 0.25,
        "601318": 0.25,
        "000002": 0.2
    }
    
    print(f"\n投资组合权重: {portfolio_weights}")
    print(f"风险策略: {risk_config.strategy.value}")
    
    # 模拟多日监控
    for day in range(1, 11):  # 模拟10天
        print(f"\n{'='*20} 第 {day} 天 {'='*20}")
        
        # 更新股票价格
        update_stock_prices(stocks, day)
        
        # 更新风险管理器数据
        risk_manager.update_portfolio_data(stocks, portfolio_weights)
        
        # 评估投资组合风险
        metrics, alerts = risk_manager.assess_portfolio_risk()
        
        print(f"\n当日股票价格:")
        for stock in stocks:
            print(f"  {stock.code}: ¥{stock.price:.2f} ({stock.change_pct:+.2%})")
        
        print(f"\n风险指标:")
        print(f"  VaR(95%): {metrics.var_95:.2%}")
        print(f"  最大回撤: {metrics.max_drawdown:.2%}")
        print(f"  波动率: {metrics.volatility:.2%}")
        print(f"  夏普比率: {metrics.sharpe_ratio:.2f}")
        print(f"  集中度风险: {metrics.concentration_risk:.2%}")
        
        # 显示风险预警
        if alerts:
            print(f"\n⚠️  风险预警 ({len(alerts)}个):")
            for alert in alerts:
                print(f"  [{alert.risk_level.value.upper()}] {alert.message}")
        else:
            print("\n✅ 无风险预警")
        
        # 检查止损
        print(f"\n止损检查:")
        for stock in stocks:
            # 假设购买价格为当前价格的90%
            purchase_price = stock.price * 0.9
            stop_loss_price = risk_manager.calculate_stop_loss(stock, purchase_price)
            
            # 更新移动止损
            risk_manager.update_trailing_stop(stock.code, stock.price)
            
            # 检查是否触发止损
            should_stop = risk_manager.check_stop_loss(stock.code, stock.price)
            
            if should_stop:
                print(f"  {stock.code}: ⚠️  触发止损！建议卖出")
            else:
                stop_distance = (stock.price - stop_loss_price) / stock.price
                print(f"  {stock.code}: ✓ 止损价¥{stop_loss_price:.2f} (距离{stop_distance:.1%})")
        
        # 生成每日风险报告
        if day % 3 == 0:  # 每3天生成一次报告
            print(f"\n📊 生成风险报告...")
            reports = risk_manager.generate_risk_reports(portfolio_weights, stocks)
            print(f"  已生成 {len(reports)} 个风险报告")
    
    # 生成最终风险报告
    print(f"\n{'='*20} 最终风险报告 {'='*20}")
    
    # 生成完整的风险报告
    reports = risk_manager.generate_risk_reports(portfolio_weights, stocks)
    
    print(f"\n已生成 {len(reports)} 个风险报告:")
    for report_type, report_path in reports.items():
        print(f"  {report_type}: {report_path}")
    
    # 显示风险建议
    metrics, _ = risk_manager.assess_portfolio_risk()
    
    print(f"\n风险建议:")
    if metrics.max_drawdown > 0.15:
        print("  - 建议降低仓位，控制最大回撤")
    if metrics.volatility > 0.25:
        print("  - 建议增加低波动率资产")
    if metrics.concentration_risk > 0.3:
        print("  - 建议分散投资，降低集中度风险")
    if metrics.sharpe_ratio < 0.5:
        print("  - 建议优化投资组合，提高风险调整后收益")
    if metrics.liquidity_risk > 0.6:
        print("  - 建议增加高流动性资产")
    
    if not any([
        metrics.max_drawdown > 0.15,
        metrics.volatility > 0.25,
        metrics.concentration_risk > 0.3,
        metrics.sharpe_ratio < 0.5,
        metrics.liquidity_risk > 0.6
    ]):
        print("  - 当前风险水平适中，建议保持现有投资策略")
    
    print(f"\n{'='*60}")
    print("集成风险监控系统演示完成")
    print("=" * 60)


if __name__ == "__main__":
    demonstrate_integrated_monitoring()