"""
风险管理示例程序
演示如何使用风险管理系统进行投资组合风险控制和动态止损
"""

import sys
import os
import numpy as np
from datetime import datetime, timedelta

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.buffett.core.risk_management import (
    RiskManager, RiskConfig, RiskStrategy, VaRMethod
)
from src.buffett.models.stock import StockInfo


def create_sample_stocks():
    """创建示例股票数据"""
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


def simulate_price_movement(stocks, days=30):
    """模拟价格变动"""
    price_history = {stock.code: [] for stock in stocks}
    
    for day in range(days):
        for stock in stocks:
            # 模拟日收益率
            daily_return = np.random.normal(0.001, 0.02)  # 平均0.1%日收益，2%波动率
            new_price = stock.price * (1 + daily_return)
            
            # 确保价格不会变成负数
            new_price = max(new_price, stock.price * 0.8)
            
            price_history[stock.code].append(new_price)
            
            # 更新股票价格
            stock.price = new_price
    
    return price_history


def demonstrate_risk_management():
    """演示风险管理功能"""
    print("=" * 60)
    print("巴菲特投资助手 - 风险管理系统演示")
    print("=" * 60)
    
    # 创建示例股票
    stocks = create_sample_stocks()
    print(f"\n创建了 {len(stocks)} 只示例股票:")
    for stock in stocks:
        print(f"  {stock.code} {stock.name}: ¥{stock.price:.2f} (PE:{stock.pe_ratio:.1f}, PB:{stock.pb_ratio:.1f})")
    
    # 创建不同策略的风险管理器
    strategies = [
        ("保守型", RiskStrategy.CONSERVATIVE),
        ("平衡型", RiskStrategy.BALANCED),
        ("激进型", RiskStrategy.AGGRESSIVE)
    ]
    
    for strategy_name, strategy_type in strategies:
        print(f"\n{'='*20} {strategy_name}策略 {'='*20}")
        
        # 创建风险管理配置
        config = RiskConfig(
            strategy=strategy_type,
            var_method=VaRMethod.HISTORICAL,
            lookback_days=30
        )
        
        # 创建风险管理器
        risk_manager = RiskManager(config)
        
        # 设置投资组合权重
        weights = {stock.code: 0.25 for stock in stocks}  # 等权重
        print(f"\n投资组合权重: {weights}")
        
        # 更新投资组合数据
        risk_manager.update_portfolio_data(stocks, weights)
        
        # 评估投资组合风险
        metrics, alerts = risk_manager.assess_portfolio_risk()
        
        print(f"\n风险指标:")
        print(f"  VaR(95%): {metrics.var_95:.2%}")
        print(f"  VaR(99%): {metrics.var_99:.2%}")
        print(f"  最大回撤: {metrics.max_drawdown:.2%}")
        print(f"  波动率: {metrics.volatility:.2%}")
        print(f"  夏普比率: {metrics.sharpe_ratio:.2f}")
        print(f"  集中度风险: {metrics.concentration_risk:.2%}")
        print(f"  流动性风险: {metrics.liquidity_risk:.2%}")
        
        # 显示风险预警
        if alerts:
            print(f"\n风险预警 ({len(alerts)}个):")
            for alert in alerts:
                print(f"  [{alert.risk_level.value.upper()}] {alert.message}")
        else:
            print("\n当前无风险预警")
        
        # 演示止损策略
        print(f"\n{strategy_name}止损策略:")
        for stock in stocks:
            purchase_price = stock.price * 0.9  # 假设购买价格为当前价格的90%
            stop_loss_price = risk_manager.calculate_stop_loss(stock, purchase_price)
            stop_loss_pct = (stop_loss_price - purchase_price) / purchase_price
            
            print(f"  {stock.code}: 购买价¥{purchase_price:.2f}, 止损价¥{stop_loss_price:.2f} ({stop_loss_pct:.1%})")
    
    # 演示动态止损
    print(f"\n{'='*20} 动态止损演示 {'='*20}")
    
    config = RiskConfig(strategy=RiskStrategy.BALANCED)
    risk_manager = RiskManager(config)
    
    # 选择一只股票进行演示
    stock = stocks[0]  # 贵州茅台
    purchase_price = stock.price
    
    print(f"\n演示股票: {stock.code} {stock.name}")
    print(f"初始价格: ¥{purchase_price:.2f}")
    
    # 计算初始止损
    stop_loss_price = risk_manager.calculate_stop_loss(stock, purchase_price)
    print(f"初始止损价: ¥{stop_loss_price:.2f}")
    
    # 模拟价格上涨和移动止损
    price_scenarios = [
        (purchase_price * 1.05, "上涨5%"),
        (purchase_price * 1.10, "上涨10%"),
        (purchase_price * 1.15, "上涨15%"),
        (purchase_price * 0.95, "下跌5%"),  # 测试止损触发
    ]
    
    for price, scenario in price_scenarios:
        print(f"\n{scenario}: ¥{price:.2f}")
        
        # 更新移动止损
        risk_manager.update_trailing_stop(stock.code, price)
        
        # 检查是否触发止损
        should_stop = risk_manager.check_stop_loss(stock.code, price)
        
        if should_stop:
            print(f"  ⚠️  触发止损！建议卖出")
        else:
            print(f"  ✓ 未触发止损，继续持有")
    
    # 演示风险报告生成
    print(f"\n{'='*20} 风险报告生成 {'='*20}")
    
    # 模拟历史价格数据
    price_history = simulate_price_movement(stocks.copy(), days=30)
    
    # 更新风险管理器
    weights = {stock.code: 0.25 for stock in stocks}
    risk_manager.update_portfolio_data(stocks, weights)
    
    # 生成风险报告
    reports = risk_manager.generate_risk_reports(weights, stocks)
    
    print(f"\n已生成 {len(reports)} 个风险报告:")
    for report_type, report_path in reports.items():
        print(f"  {report_type}: {report_path}")
    
    print(f"\n{'='*60}")
    print("风险管理系统演示完成")
    print("=" * 60)


if __name__ == "__main__":
    demonstrate_risk_management()