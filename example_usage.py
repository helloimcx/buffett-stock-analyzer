#!/usr/bin/env python3
"""
优化策略使用示例

展示如何使用新的优化数据获取策略
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from buffett.factories.strategy_factory import create_data_fetch_context


async def basic_usage_example():
    """基本使用示例"""
    print("🚀 基本使用示例")
    print("=" * 50)

    # 创建优化策略的数据获取上下文
    # 默认使用 optimized_akshare 策略
    context = create_data_fetch_context("optimized_akshare")

    # 获取单只股票的基本信息
    print("\n📊 获取单只股票信息:")
    try:
        stock_info = await context.fetch_stock_basic_info("600036.SH")  # 招商银行
        if stock_info:
            print(f"  股票名称: {stock_info.get('name', '未知')}")
            print(f"  当前价格: ¥{stock_info.get('current_price', 0):.2f}")
            print(f"  市盈率: {stock_info.get('pe_ratio', 0):.2f}")
            print(f"  数据源: {stock_info.get('data_source', '未知')}")
        else:
            print("  ❌ 获取失败")
    except Exception as e:
        print(f"  ⚠️  示例仅展示用法，未实际调用API: {e}")

    print("\n📈 批量获取股票信息:")
    test_symbols = ["600036.SH", "000001.SZ", "600000.SH"]
    print(f"  目标股票: {', '.join(test_symbols)}")

    try:
        # 批量获取 - 这是优化策略的核心功能
        strategy = context._strategy
        if hasattr(strategy, 'fetch_stocks_batch'):
            batch_results = await strategy.fetch_stocks_batch(test_symbols, ['basic'])
            print(f"  ✅ 批量获取完成，预期返回 {len(test_symbols)} 只股票信息")
        else:
            print("  ⚠️  当前策略不支持批量获取")
    except Exception as e:
        print(f"  ⚠️  示例仅展示用法，未实际调用API: {e}")


async def cache_example():
    """缓存使用示例"""
    print("\n🚀 缓存使用示例")
    print("=" * 50)

    # 创建带缓存的数据获取器
    from buffett.strategies.optimized_data_fetch import OptimizedDataFetcher

    fetcher = OptimizedDataFetcher(enable_cache=True, cache_ttl_hours=24)

    print("\n📊 缓存机制说明:")
    print("  • 市场概览数据: 15分钟缓存")
    print("  • 个股详细信息: 2小时缓存")
    print("  • 股息数据: 24小时缓存")
    print("  • 历史数据: 7天缓存")

    print("\n🚀 使用缓存的好处:")
    print("  1. 减少API调用次数")
    print("  2. 提高响应速度")
    print("  3. 避免频率限制")
    print("  4. 降低被封IP风险")


async def frequency_control_example():
    """频率控制示例"""
    print("\n🚀 频率控制示例")
    print("=" * 50)

    from buffett.strategies.optimized_data_fetch import APIRequestTracker

    # 创建请求跟踪器
    tracker = APIRequestTracker()

    print("\n📊 频率限制设置:")
    rate_limits = {
        'sina': "30秒间隔",
        'xueqiu': "5秒间隔",
        'tencent': "10秒间隔"
    }

    for source, limit in rate_limits.items():
        print(f"  {source}: {limit}")

    print("\n🚀 频率控制机制:")
    print("  1. 请求前检查是否可以发起")
    print("  2. 自动等待避免频率过高")
    print("  3. 记录每次API调用")
    print("  4. 提供调用统计信息")


def configuration_example():
    """配置示例"""
    print("\n🚀 配置示例")
    print("=" * 50)

    print("\n📊 策略工厂配置:")
    print("  # 使用优化策略")
    print("  context = create_data_fetch_context('optimized_akshare')")
    print()
    print("  # 自定义配置")
    print("  config = {")
    print("      'cache_ttl_hours': 48,  # 缓存48小时")
    print("      'enable_cache': True,    # 启用缓存")
    print("      'timeout': 60            # 超时60秒")
    print("  }")
    print("  context = create_data_fetch_context('optimized_akshare', config)")

    print("\n🚀 生产环境配置:")
    print("  # 生产环境使用多源策略")
    print("  context = create_data_fetch_context({")
    print("      'strategies': ['optimized_akshare', 'mock'],")
    print("      'enable_fallback': True")
    print("  })")


async def main():
    """主函数"""
    print("🎯 优化策略使用示例")
    print("=" * 80)
    print("展示如何使用基于AKShare技能的优化数据获取策略")
    print("=" * 80)

    await basic_usage_example()
    await cache_example()
    await frequency_control_example()
    configuration_example()

    print("\n🎉 使用总结")
    print("=" * 80)
    print("✅ 默认使用优化策略")
    print("✅ 向后兼容现有代码")
    print("✅ 智能缓存减少API调用")
    print("✅ 批量处理提高效率")
    print("✅ 频率控制避免被封")
    print("✅ 技能化数据获取更稳定")

    print(f"\n⚠️  注意事项:")
    print(f"  • 首次运行需要下载依赖包")
    print(f"  • 避免短时间内频繁运行")
    print(f"  • 生产环境建议使用优化策略")
    print(f"  • 可以通过环境变量配置")


if __name__ == "__main__":
    asyncio.run(main())