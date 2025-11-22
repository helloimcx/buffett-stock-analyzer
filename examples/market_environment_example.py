"""
市场环境识别系统示例
演示如何使用市场环境识别和自适应评分功能
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.buffett.core.market_environment import (
    MarketEnvironmentIdentifier, MarketEnvironmentStorage
)
from src.buffett.core.adaptive_scoring import (
    AdaptiveMultiFactorScorer, MarketEnvironmentMonitor
)
from src.buffett.models.stock import StockInfo


def create_sample_market_data(env_type="bull"):
    """创建示例市场数据"""
    if env_type == "bull":
        # 牛市数据
        return {
            "prices": list(range(100, 160)),  # 上涨趋势
            "current_volume": 180000000,
            "avg_volume": 100000000,
            "advancing_stocks": 2800,
            "declining_stocks": 1200,
            "momentum": 0.025
        }
    elif env_type == "bear":
        # 熊市数据
        return {
            "prices": list(range(200, 140, -1)),  # 下跌趋势
            "current_volume": 120000000,
            "avg_volume": 100000000,
            "advancing_stocks": 1200,
            "declining_stocks": 2800,
            "momentum": -0.025
        }
    else:
        # 震荡市数据
        import random
        prices = [150] * 60
        for i in range(len(prices)):
            prices[i] += random.uniform(-2, 2)  # 小幅随机波动
        
        return {
            "prices": prices,
            "current_volume": 100000000,
            "avg_volume": 100000000,
            "advancing_stocks": 2000,
            "declining_stocks": 2000,
            "momentum": 0.001
        }


def create_sample_stocks():
    """创建示例股票数据"""
    return [
        StockInfo(
            code="000001",
            name="平安银行",
            price=10.5,
            dividend_yield=4.2,
            pe_ratio=8.5,
            pb_ratio=0.8,
            change_pct=0.015,
            volume=15000000,
            market_cap=2000000000,
            eps=1.2,
            book_value=13.0,
            week_52_high=15.0,
            week_52_low=8.0
        ),
        StockInfo(
            code="000002",
            name="万科A",
            price=25.8,
            dividend_yield=2.1,
            pe_ratio=18.5,
            pb_ratio=1.5,
            change_pct=0.025,
            volume=25000000,
            market_cap=2800000000,
            eps=1.4,
            book_value=17.0,
            week_52_high=35.0,
            week_52_low=18.0
        ),
        StockInfo(
            code="000858",
            name="五粮液",
            price=185.5,
            dividend_yield=1.8,
            pe_ratio=25.5,
            pb_ratio=4.2,
            change_pct=0.035,
            volume=8000000,
            market_cap=72000000000,
            eps=7.3,
            book_value=44.0,
            week_52_high=220.0,
            week_52_low=150.0
        )
    ]


def demonstrate_market_environment_identification():
    """演示市场环境识别功能"""
    print("=" * 60)
    print("市场环境识别系统演示")
    print("=" * 60)
    
    # 创建识别器
    identifier = MarketEnvironmentIdentifier()
    
    # 测试不同市场环境
    for env_name in ["bull", "bear", "sideways"]:
        print(f"\n--- {env_name.upper()} 市场环境分析 ---")
        
        market_data = create_sample_market_data(env_name)
        environment = identifier.identify_environment(market_data)
        
        print(f"环境类型: {environment.environment_type.value}")
        print(f"置信度: {environment.confidence:.2f}")
        print(f"趋势方向: {environment.trend_direction}")
        print(f"波动率水平: {environment.volatility_level}")
        print(f"情绪得分: {environment.sentiment_score:.2f}")
        print(f"识别时间: {environment.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")


def demonstrate_adaptive_scoring():
    """演示自适应评分功能"""
    print("\n" + "=" * 60)
    print("自适应评分系统演示")
    print("=" * 60)
    
    # 创建自适应评分器
    adaptive_scorer = AdaptiveMultiFactorScorer()
    
    # 创建示例股票
    stocks = create_sample_stocks()
    
    # 测试不同市场环境下的评分
    for env_name in ["bull", "bear", "sideways"]:
        print(f"\n--- {env_name.upper()} 市场环境下的股票评分 ---")
        
        # 更新市场环境
        market_data = create_sample_market_data(env_name)
        environment = adaptive_scorer.update_market_environment(market_data)
        
        # 创建自适应评分器并排序股票
        ranked_stocks = adaptive_scorer.rank_stocks_adaptive(stocks)
        
        print(f"市场环境: {environment.environment_type.value} (置信度: {environment.confidence:.2f})")
        print("股票排序结果:")
        
        for i, stock in enumerate(ranked_stocks, 1):
            print(f"  {i}. {stock.name} ({stock.code}) - 评分: {stock.total_score:.2f}")
        
        # 显示权重变化
        analysis = adaptive_scorer.get_environment_analysis()
        current_weights = analysis["weights"]["current"]
        
        print("当前因子权重:")
        for factor, weight in current_weights.items():
            print(f"  {factor}: {weight:.3f}")


def demonstrate_environment_monitoring():
    """演示环境监控功能"""
    print("\n" + "=" * 60)
    print("市场环境监控演示")
    print("=" * 60)
    
    # 创建监控器
    adaptive_scorer = AdaptiveMultiFactorScorer()
    monitor = MarketEnvironmentMonitor(adaptive_scorer)
    
    # 添加预警回调
    def alert_callback(alert):
        print(f"\n🚨 环境变化预警!")
        print(f"   类型: {alert.alert_type}")
        print(f"   从 {alert.previous_environment.value} 转为 {alert.current_environment.value}")
        print(f"   置信度: {alert.confidence:.2f}")
        print(f"   消息: {alert.message}")
        print(f"   时间: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    
    monitor.add_alert_callback(alert_callback)
    
    # 模拟市场环境变化
    environments = ["bull", "sideways", "bear"]
    
    print("\n开始监控市场环境变化...")
    
    for i, env_name in enumerate(environments):
        print(f"\n--- 第{i+1}轮监控: {env_name.upper()} 市场 ---")
        
        market_data = create_sample_market_data(env_name)
        result = monitor.monitor_and_update(market_data)
        
        print(f"当前环境: {result['current_environment']['environment_type']}")
        print(f"置信度: {result['current_environment']['confidence']:.2f}")
        print(f"环境变化: {'是' if result['change_detected'] else '否'}")
        
        if result['change_detected']:
            print(f"预警信息: {result['alert']['message']}")


def demonstrate_environment_history():
    """演示环境历史记录功能"""
    print("\n" + "=" * 60)
    print("环境历史记录演示")
    print("=" * 60)
    
    # 创建存储和识别器
    storage = MarketEnvironmentStorage()
    identifier = MarketEnvironmentIdentifier()
    
    # 模拟历史数据
    print("\n生成历史环境数据...")
    for i in range(5):
        env_name = ["bull", "bear", "sideways"][i % 3]
        market_data = create_sample_market_data(env_name)
        environment = identifier.identify_environment(market_data)
        
        # 保存历史记录
        from src.buffett.core.market_environment import MarketEnvironmentHistory
        history = MarketEnvironmentHistory(
            index_code="000001",  # 上证指数
            environment=environment,
            raw_data=market_data,
            timestamp=environment.timestamp
        )
        
        storage.save_environment_record(history)
        print(f"  保存记录 {i+1}: {environment.environment_type.value}")
    
    # 读取历史记录
    print("\n读取历史环境记录...")
    history_records = storage.get_environment_history("000001", days=30)
    
    print(f"找到 {len(history_records)} 条历史记录:")
    for i, record in enumerate(history_records[:5], 1):
        env = record.environment
        print(f"  {i}. {env.timestamp.strftime('%Y-%m-%d %H:%M:%S')} - "
              f"{env.environment_type.value} (置信度: {env.confidence:.2f})")


def main():
    """主函数"""
    print("🚀 市场环境识别与自适应评分系统演示")
    
    try:
        # 演示各项功能
        demonstrate_market_environment_identification()
        demonstrate_adaptive_scoring()
        demonstrate_environment_monitoring()
        demonstrate_environment_history()
        
        print("\n" + "=" * 60)
        print("演示完成!")
        print("=" * 60)
        
        print("\n📊 系统功能总结:")
        print("1. ✅ 市场环境识别 (牛市/熊市/震荡市)")
        print("2. ✅ 趋势分析 (移动平均线、趋势强度)")
        print("3. ✅ 波动率分析 (低/中/高波动)")
        print("4. ✅ 市场情绪分析 (成交量、涨跌比例、动量)")
        print("5. ✅ 自适应权重调整 (根据市场环境动态调整)")
        print("6. ✅ 环境变化预警 (实时监控和通知)")
        print("7. ✅ 历史数据存储 (环境变化追踪)")
        
        print("\n🎯 投资策略建议:")
        print("• 牛市: 偏向成长因子，关注高成长性股票")
        print("• 熊市: 偏向价值和质量因子，关注防御性股票")
        print("• 震荡市: 均衡配置，增加技术因子权重")
        
    except Exception as e:
        print(f"❌ 演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()