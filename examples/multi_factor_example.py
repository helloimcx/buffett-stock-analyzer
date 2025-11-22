"""
多因子评分系统使用示例
演示如何使用新的多因子评分系统
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.buffett.models.stock import StockInfo
from src.buffett.core.multi_factor_scoring import (
    MultiFactorScorer, MultiFactorConfig, FactorRegistry
)
from src.buffett.core.scoring import InvestmentScorer


def main():
    """主函数演示多因子评分系统的使用"""
    
    print("=== 多因子评分系统示例 ===\n")
    
    # 创建示例股票数据
    stocks = [
        StockInfo(
            code="GOOD", name="优质股票", price=10.0, dividend_yield=4.0,
            pe_ratio=15.0, pb_ratio=1.5, change_pct=2.0, volume=2000000,
            market_cap=2000000000.0, eps=2.0, book_value=15.0,
            week_52_high=12.0, week_52_low=8.0
        ),
        StockInfo(
            code="AVERAGE", name="一般股票", price=10.0, dividend_yield=2.0,
            pe_ratio=25.0, pb_ratio=2.5, change_pct=0.0, volume=1000000,
            market_cap=1000000000.0, eps=1.0, book_value=10.0,
            week_52_high=12.0, week_52_low=8.0
        ),
        StockInfo(
            code="POOR", name="较差股票", price=10.0, dividend_yield=0.5,
            pe_ratio=50.0, pb_ratio=5.0, change_pct=-3.0, volume=500000,
            market_cap=500000000.0, eps=0.5, book_value=5.0,
            week_52_high=12.0, week_52_low=8.0
        )
    ]
    
    print("1. 使用默认配置的多因子评分器")
    print("-" * 40)
    
    # 创建默认配置的多因子评分器
    default_scorer = MultiFactorScorer.with_default_factors()
    ranked_stocks = default_scorer.rank_stocks(stocks)
    
    for i, stock in enumerate(ranked_stocks, 1):
        print(f"{i}. {stock.name} ({stock.code}): {stock.total_score:.2f}分")
    
    print("\n2. 使用自定义权重的多因子评分器")
    print("-" * 40)
    
    # 创建自定义权重配置
    custom_weights = {
        "dividend": 0.5,    # 股息因子权重50%
        "value": 0.3,       # 价值因子权重30%
        "technical": 0.2     # 技术因子权重20%
    }
    
    custom_scorer = MultiFactorScorer.with_custom_weights(custom_weights)
    custom_ranked = custom_scorer.rank_stocks(stocks)
    
    for i, stock in enumerate(custom_ranked, 1):
        print(f"{i}. {stock.name} ({stock.code}): {stock.total_score:.2f}分")
    
    print("\n3. 使用配置文件的多因子评分器")
    print("-" * 40)
    
    # 创建配置文件
    config_data = {
        "dividend": {"weight": 0.4, "enabled": True},
        "value": {"weight": 0.3, "enabled": True},
        "growth": {"weight": 0.2, "enabled": True},
        "technical": {"weight": 0.1, "enabled": True},
        "quality": {"weight": 0.0, "enabled": False},  # 禁用质量因子
        "momentum": {"weight": 0.0, "enabled": False}, # 禁用动量因子
        "sentiment": {"weight": 0.0, "enabled": False}  # 禁用情绪因子
    }
    
    # 保存配置到临时文件
    import json
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        config_file = f.name
    
    try:
        # 从配置文件创建评分器
        config = MultiFactorConfig.from_file(config_file)
        config_scorer = MultiFactorScorer.from_config(config)
        config_ranked = config_scorer.rank_stocks(stocks)
        
        for i, stock in enumerate(config_ranked, 1):
            print(f"{i}. {stock.name} ({stock.code}): {stock.total_score:.2f}分")
    finally:
        os.unlink(config_file)
    
    print("\n4. 与现有评分器对比")
    print("-" * 40)
    
    # 使用现有评分器
    old_scorer = InvestmentScorer()
    old_ranked = old_scorer.rank_stocks(stocks)
    
    # 使用兼容模式的多因子评分器
    legacy_scorer = MultiFactorScorer.with_legacy_weights()
    legacy_ranked = legacy_scorer.rank_stocks(stocks)
    
    print("现有评分器结果:")
    for i, stock in enumerate(old_ranked, 1):
        print(f"{i}. {stock.name} ({stock.code}): {stock.total_score:.2f}分")
    
    print("\n兼容模式多因子评分器结果:")
    for i, stock in enumerate(legacy_ranked, 1):
        print(f"{i}. {stock.name} ({stock.code}): {stock.total_score:.2f}分")
    
    print("\n5. 自定义因子示例")
    print("-" * 40)
    
    # 创建自定义因子
    class MarketCapFactor(Factor):
        """市值因子"""
        
        def __init__(self, weight=1.0):
            super().__init__("market_cap", weight)
        
        def calculate(self, stock: StockInfo) -> float:
            # 市值越大得分越高（假设大盘股更稳定）
            if stock.market_cap > 0:
                return min(stock.market_cap / 50000000000.0, 1.0)  # 500亿为满分
            return 0.0
    
    # 注册自定义因子
    FactorRegistry.register("market_cap", MarketCapFactor)
    
    # 使用自定义因子
    custom_factor_scorer = MultiFactorScorer()
    custom_factor_scorer.add_factor(MarketCapFactor(weight=0.3))
    custom_factor_scorer.add_factor(DividendFactor(weight=0.7))
    
    custom_factor_ranked = custom_factor_scorer.rank_stocks(stocks)
    
    print("自定义因子评分器结果:")
    for i, stock in enumerate(custom_factor_ranked, 1):
        print(f"{i}. {stock.name} ({stock.code}): {stock.total_score:.2f}分")
    
    print("\n6. 可用因子列表")
    print("-" * 40)
    
    available_factors = FactorRegistry.get_available_factors()
    print("当前可用的因子:")
    for factor_name in available_factors:
        print(f"- {factor_name}")
    
    print("\n=== 示例完成 ===")


if __name__ == "__main__":
    import tempfile
    from src.buffett.core.multi_factor_scoring import Factor, DividendFactor
    main()