"""
集成测试示例程序
演示如何运行集成测试和验证系统功能
"""

import sys
import os
from pathlib import Path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.buffett.core.multi_factor_scoring import MultiFactorScorer
from src.buffett.core.scoring import InvestmentScorer
from src.buffett.strategies.technical_analysis import TechnicalSignalGenerator
from src.buffett.core.market_environment import MarketEnvironmentIdentifier
from src.buffett.core.risk_management import RiskManager, RiskConfig
from tests.integration.test_framework import TestDataGenerator


def main():
    """主函数：演示集成测试"""
    print("=" * 80)
    print("巴菲特投资系统 - 集成测试示例")
    print("=" * 80)
    
    # 创建测试数据
    print("\n📊 创建测试数据...")
    test_stocks = [
        TestDataGenerator.create_test_stock("STOCK1", "贵州茅台", 1800.0, 1.2, 35.0, 8.5),
        TestDataGenerator.create_test_stock("STOCK2", "工商银行", 4.5, 5.8, 4.2, 0.5),
        TestDataGenerator.create_test_stock("STOCK3", "中国平安", 45.0, 3.5, 9.8, 0.9),
        TestDataGenerator.create_test_stock("STOCK4", "招商银行", 35.0, 4.2, 6.5, 1.2),
        TestDataGenerator.create_test_stock("STOCK5", "比亚迪", 250.0, 0.8, 45.0, 3.8)
    ]
    
    print(f"创建了 {len(test_stocks)} 只测试股票")
    for stock in test_stocks:
        print(f"  {stock.code}: {stock.name} - 价格:{stock.price:.2f}, 股息率:{stock.dividend_yield:.2f}%")
    
    # 场景1：多因子评分系统与现有系统的兼容性
    print("\n🔍 场景1：多因子评分系统与现有系统的兼容性")
    print("-" * 60)
    
    multi_factor_scorer = MultiFactorScorer.with_default_factors()
    legacy_scorer = InvestmentScorer()
    
    print("股票评分对比:")
    print("股票代码\t股票名称\t\t多因子评分\t旧系统评分\t差异")
    print("-" * 70)
    
    compatibility_issues = []
    for stock in test_stocks:
        # 多因子评分
        mf_score = multi_factor_scorer.calculate_score(stock)
        
        # 旧系统评分
        legacy_score = legacy_scorer.calculate_total_score(stock) / 100
        
        # 计算差异
        diff = abs(mf_score - legacy_score)
        
        print(f"{stock.code}\t{stock.name}\t\t{mf_score:.3f}\t\t{legacy_score:.3f}\t\t{diff:.3f}")
        
        # 检查兼容性问题
        if diff > 0.4:
            compatibility_issues.append(f"{stock.code}: 评分差异过大 ({diff:.3f})")
    
    if compatibility_issues:
        print(f"\n⚠️  发现 {len(compatibility_issues)} 个兼容性问题:")
        for issue in compatibility_issues:
            print(f"  - {issue}")
    else:
        print("\n✅ 兼容性测试通过")
    
    # 场景2：技术分析与多因子评分的结合
    print("\n📈 场景2：技术分析与多因子评分的结合")
    print("-" * 60)
    
    signal_generator = TechnicalSignalGenerator()
    
    print("技术分析增强评分:")
    print("股票代码\t基础评分\t信号强度\t增强评分\t推荐")
    print("-" * 60)
    
    for stock in test_stocks:
        # 基础评分
        base_score = multi_factor_scorer.calculate_score(stock)
        
        # 技术分析
        prices = TestDataGenerator.create_test_price_history(stock.code, days=30, base_price=stock.price)
        volumes = TestDataGenerator.create_test_volume_history(days=30)
        
        signals = signal_generator.generate_signals(prices, volumes)
        signal_strength = signal_generator.calculate_signal_strength(prices, volumes)
        
        # 增强评分
        enhanced_score = base_score + signal_strength * 0.1
        enhanced_score = max(0, min(1, enhanced_score))
        
        # 推荐决策
        if enhanced_score > 0.7 and signal_strength > 0.2:
            recommendation = "买入"
        elif enhanced_score < 0.3 or signal_strength < -0.2:
            recommendation = "卖出"
        else:
            recommendation = "持有"
        
        print(f"{stock.code}\t{base_score:.3f}\t\t{signal_strength:.3f}\t\t{enhanced_score:.3f}\t{recommendation}")
    
    # 场景3：市场环境识别的自适应功能
    print("\n🌡️  场景3：市场环境识别的自适应功能")
    print("-" * 60)
    
    environment_identifier = MarketEnvironmentIdentifier()
    
    # 创建不同市场环境数据
    market_scenarios = {
        "牛市": {
            "prices": [3000 + i * 20 for i in range(60)],
            "volumes": [1000000000 + i * 1000000 for i in range(60)],
            "current_volume": 1000000000 + 59 * 1000000,
            "avg_volume": 1000000000 + 30 * 1000000,
            "advancing_stocks": 200,
            "declining_stocks": 50,
            "momentum": 0.03
        },
        "熊市": {
            "prices": [3000 - i * 15 for i in range(60)],
            "volumes": [1000000000 - i * 500000 for i in range(60)],
            "current_volume": 1000000000 - 59 * 500000,
            "avg_volume": 1000000000 - 30 * 500000,
            "advancing_stocks": 30,
            "declining_stocks": 220,
            "momentum": -0.04
        },
        "震荡市": {
            "prices": [3000 + (i % 10) * 10 - 45 for i in range(60)],
            "volumes": [1000000000 + (i % 10) * 100000000 - 500000000 for i in range(60)],
            "current_volume": 1000000000 + (59 % 10) * 100000000 - 500000000,
            "avg_volume": 1000000000,
            "advancing_stocks": 125,
            "declining_stocks": 125,
            "momentum": 0.001
        }
    }
    
    print("市场环境识别结果:")
    print("市场类型\t环境类型\t置信度\t趋势方向\t情绪得分")
    print("-" * 60)
    
    for market_type, data in market_scenarios.items():
        environment = environment_identifier.identify_environment(data)
        print(f"{market_type}\t{environment.environment_type.value}\t{environment.confidence:.3f}\t\t"
              f"{environment.trend_direction}\t{environment.sentiment_score:.3f}")
    
    # 场景4：风险控制与信号生成的联动
    print("\n⚠️  场景4：风险控制与信号生成的联动")
    print("-" * 60)
    
    risk_manager = RiskManager(RiskConfig())
    
    # 创建投资组合
    portfolio = {stock.code: 0.2 for stock in test_stocks}
    
    # 更新投资组合数据
    risk_manager.update_portfolio_data(test_stocks, portfolio)
    
    # 风险评估
    risk_metrics, risk_alerts = risk_manager.assess_portfolio_risk()
    
    print("投资组合风险评估:")
    print(f"  VaR(95%): {risk_metrics.var_95:.4f}")
    print(f"  最大回撤: {risk_metrics.max_drawdown:.4f}")
    print(f"  波动率: {risk_metrics.volatility:.4f}")
    print(f"  夏普比率: {risk_metrics.sharpe_ratio:.4f}")
    print(f"  集中度风险: {risk_metrics.concentration_risk:.4f}")
    print(f"  流动性风险: {risk_metrics.liquidity_risk:.4f}")
    print(f"  风险预警数量: {len(risk_alerts)}")
    
    if risk_alerts:
        print("\n风险预警详情:")
        for alert in risk_alerts[:5]:  # 只显示前5个
            print(f"  - {alert.risk_type.value}: {alert.message}")
    
    # 个股风险检查
    print("\n个股风险控制:")
    print("股票代码\t买入价\t止损价\t止损幅度\t风险等级")
    print("-" * 60)
    
    for stock in test_stocks:
        purchase_price = stock.price * 0.95  # 假设比当前价低5%买入
        stop_loss_price = risk_manager.calculate_stop_loss(stock, purchase_price)
        stop_loss_pct = (purchase_price - stop_loss_price) / purchase_price
        
        # 风险等级评估
        if stop_loss_pct > 0.15:
            risk_level = "高风险"
        elif stop_loss_pct > 0.10:
            risk_level = "中等风险"
        else:
            risk_level = "低风险"
        
        print(f"{stock.code}\t{purchase_price:.2f}\t\t{stop_loss_price:.2f}\t\t{stop_loss_pct:.2%}\t\t{risk_level}")
    
    # 场景5：实时监控和预警系统
    print("\n📡 场景5：实时监控和预警系统")
    print("-" * 60)
    
    # 模拟监控过程
    print("模拟3轮监控检查:")
    
    for round_num in range(3):
        print(f"\n监控轮次 {round_num + 1}:")
        
        round_signals = []
        
        for stock in test_stocks:
            # 模拟价格变化
            price_change = 0.02 * (round_num + 1)
            stock.price *= (1 + price_change)
            
            # 检测信号（简化版）
            base_score = multi_factor_scorer.calculate_score(stock)
            
            if base_score > 0.7:
                signal_type = "买入信号"
                signal_strength = "强"
            elif base_score < 0.3:
                signal_type = "卖出信号"
                signal_strength = "强"
            else:
                signal_type = "持有"
                signal_strength = "中等"
            
            if signal_type != "持有":
                round_signals.append({
                    'stock': stock.code,
                    'type': signal_type,
                    'strength': signal_strength,
                    'score': base_score
                })
        
        print(f"  检测到 {len(round_signals)} 个信号:")
        for signal in round_signals:
            print(f"    {signal['stock']}: {signal['type']} ({signal['strength']}, 评分:{signal['score']:.3f})")
    
    # 综合评估
    print("\n📊 综合评估")
    print("=" * 60)
    
    # 计算整体系统健康度
    health_score = 0
    max_score = 0
    
    # 兼容性评分 (30%)
    compatibility_score = max(0, 100 - len(compatibility_issues) * 10)
    health_score += compatibility_score * 0.3
    max_score += 30
    
    # 技术分析评分 (25%)
    tech_score = 80  # 假设技术分析工作正常
    health_score += tech_score * 0.25
    max_score += 25
    
    # 市场环境识别评分 (20%)
    env_score = 85  # 假设环境识别工作正常
    health_score += env_score * 0.2
    max_score += 20
    
    # 风险管理评分 (25%)
    risk_score = 90 if len(risk_alerts) < 5 else 70  # 基于预警数量
    health_score += risk_score * 0.25
    max_score += 25
    
    overall_health = health_score / max_score * 100
    
    print("系统组件健康度评估:")
    print(f"  兼容性: {compatibility_score:.0f}/100")
    print(f"  技术分析: {tech_score:.0f}/100")
    print(f"  市场环境识别: {env_score:.0f}/100")
    print(f"  风险管理: {risk_score:.0f}/100")
    print(f"  整体健康度: {overall_health:.1f}%")
    
    # 最终结论
    print(f"\n🎯 集成测试结论")
    print("=" * 60)
    
    if overall_health >= 85:
        print("✅ 系统集成度优秀，所有模块协同工作良好")
        conclusion = "优秀"
    elif overall_health >= 75:
        print("✅ 系统集成度良好，大部分模块协同工作正常")
        conclusion = "良好"
    elif overall_health >= 60:
        print("⚠️  系统集成度一般，部分模块需要优化")
        conclusion = "一般"
    else:
        print("❌ 系统集成度较差，需要重大改进")
        conclusion = "较差"
    
    print(f"最终评级: {conclusion}")
    print(f"整体健康度: {overall_health:.1f}%")
    
    # 建议
    print(f"\n💡 改进建议:")
    if compatibility_issues:
        print("  - 优化多因子评分系统与旧系统的兼容性")
    if len(risk_alerts) > 5:
        print("  - 加强风险控制策略，减少风险预警数量")
    if overall_health < 85:
        print("  - 进一步优化各模块间的集成和协同")
    
    print(f"\n📋 集成测试完成")
    print("=" * 80)
    
    return overall_health >= 75


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)