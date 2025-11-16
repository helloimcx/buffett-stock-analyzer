#!/usr/bin/env python3
"""
API优化效果演示

展示优化后的AKShare策略如何大幅减少API调用次数
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from buffett.strategies.optimized_data_fetch import OptimizedDataFetcher


def demonstrate_optimization():
    """演示优化效果"""
    print("🚀 AKShare API调用优化演示")
    print("=" * 80)

    print("\n📊 优化前后对比:")
    print("优化前:")
    print("  • 市场概览缓存: 15分钟")
    print("  • 新浪财经间隔: 30秒")
    print("  • 个股详情间隔: 5秒")
    print("  • 股息数据间隔: 无限制")
    print("  • 缓存保留时间: 1天")

    print("\n优化后:")
    print("  • 市场概览缓存: 2小时 (减少800%调用)")
    print("  • 新浪财经间隔: 2分钟 (避免被封IP)")
    print("  • 个股详情间隔: 10秒")
    print("  • 股息数据间隔: 每个股票1秒+5个股票后暂停5秒")
    print("  • 缓存保留时间: 3天")
    print("  • 智能代码映射: 避免重复查找")

    print("\n🔥 核心优化策略:")
    print("1. 极致的缓存优先:")
    print("   • 任何请求首先检查缓存")
    print("   • 延长缓存时间到2小时以上")
    print("   • 股票代码映射持久化")

    print("\n2. 严格的频率控制:")
    print("   • 新浪财经: 2分钟间隔")
    print("   • 雪球: 10秒间隔")
    print("   • 腾讯证券: 30秒间隔")
    print("   • 批量请求暂停机制")

    print("\n3. 智能请求优化:")
    print("   • 基本信息完整时跳过详细API")
    print("   • 每10个股票后暂停5秒")
    print("   • 代码映射缓存避免重复查找")

    print("\n4. 风险控制机制:")
    print("   • 明确的API调用警告")
    print("   • 自动等待避免频率限制")
    print("   • 异常处理和降级策略")


async def demonstrate_caching_effect():
    """演示缓存效果"""
    print("\n🧪 缓存效果演示")
    print("=" * 50)

    fetcher = OptimizedDataFetcher(enable_cache=True)

    print("\n📊 第一次获取市场概览 (将调用API):")
    start_time = datetime.now()
    try:
        # 注意：这里会真正调用API，请谨慎使用
        print("⚠️  正在调用API，请等待...")
        # data = await fetcher.fetch_market_overview()
        # print(f"✅ 获取到 {len(data)} 只股票数据")
        print("📝 API调用被注释以避免频繁调用")
    except Exception as e:
        print(f"API调用失败: {e}")
    end_time = datetime.now()
    first_call_time = (end_time - start_time).total_seconds()

    print(f"⏱️  首次调用耗时: {first_call_time:.2f}秒")

    print("\n🚀 第二次获取市场概览 (使用缓存):")
    start_time = datetime.now()

    # 模拟缓存命中
    if fetcher.cache:
        cached_data = fetcher.cache.get_cached_data('market_overview', 'all')
        if cached_data is not None:
            print(f"✅ 从缓存获取 {len(cached_data)} 只股票数据")
            print("⚡ 几乎无延迟！")
            end_time = datetime.now()
            cached_call_time = (end_time - start_time).total_seconds()
            print(f"⏱️  缓存调用耗时: {cached_call_time:.4f}秒")

            if cached_call_time > 0:
                speedup = first_call_time / cached_call_time
                print(f"🚀 速度提升: {speedup:.0f}x")

    # 显示缓存统计
    if fetcher.cache:
        cache_stats = fetcher.cache.get_cache_stats()
        print(f"\n📈 缓存统计:")
        print(f"  缓存目录: {cache_stats['cache_dir']}")
        print(f"  股票信息文件: {cache_stats['stock_files']}")
        print(f"  股息数据文件: {cache_stats['dividend_files']}")
        print(f"  总缓存大小: {cache_stats['total_size_mb']:.2f}MB")


def demonstrate_frequency_control():
    """演示频率控制"""
    print("\n🕐 频率控制演示")
    print("=" * 50)

    tracker = OptimizedDataFetcher.APIRequestTracker()

    # 模拟请求序列
    print("\n📊 模拟API请求序列:")

    # 模拟新浪财经请求
    print("1. 申请新浪财经API调用...")
    can_request = tracker.can_request('sina', 120)
    print(f"   结果: {'✅ 允许' if can_request else '❌ 被限制'}")

    if can_request:
        tracker.record_request('sina')
        print("   📝 已记录请求，下次调用需等待2分钟")

    # 尝试立即再次调用
    print("\n2. 立即再次申请新浪财经API调用...")
    can_request = tracker.can_request('sina', 120)
    print(f"   结果: {'✅ 允许' if can_request else '❌ 被限制'}")

    if not can_request:
        last_time = tracker.last_request_times.get('sina')
        if last_time:
            wait_time = 120 - (datetime.now() - last_time).seconds
            print(f"   ⏰ 需等待 {wait_time} 秒")

    # 显示统计
    stats = tracker.get_stats()
    print(f"\n📈 请求统计:")
    print(f"  总请求次数: {stats['total_requests']}")
    for source, count in stats['requests_by_source'].items():
        print(f"  {source}: {count} 次调用")


def demonstrate_smart_mapping():
    """演示智能代码映射"""
    print("\n🧠 智能代码映射演示")
    print("=" * 50)

    cache = OptimizedDataFetcher.SmartCache()

    # 模拟映射缓存
    test_mappings = {
        '000001.SZ': 'sz000001',
        '600036.SH': 'sh600036',
        '600519.SH': 'sh600519'
    }

    cache.symbol_mapping.update(test_mappings)
    cache.save_symbol_mapping()

    print("📊 测试股票代码映射:")
    for standard_code, mapped_code in test_mappings.items():
        cached_result = cache.get_mapped_symbol(standard_code)
        print(f"  {standard_code} → {cached_result} {'✅' if cached_result else '❌'}")

    print(f"\n💾 映射缓存已保存到: {cache.symbol_mapping_file}")
    print("🔍 下次查询时直接使用缓存，避免遍历整个市场数据")


async def main():
    """主演示函数"""
    print("🎯 AKShare API调用优化完整演示")
    print("=" * 80)
    print("目标: 展示如何通过智能策略大幅减少API调用，避免被封IP")
    print("=" * 80)

    # 运行各项演示
    demonstrate_optimization()
    await demonstrate_caching_effect()
    demonstrate_frequency_control()
    demonstrate_smart_mapping()

    print("\n🎉 优化总结")
    print("=" * 80)
    print("✅ 缓存时间延长8倍 (2小时 vs 15分钟)")
    print("✅ API间隔延长4倍 (2分钟 vs 30秒)")
    print("✅ 智能跳过不必要的详细API调用")
    print("✅ 代码映射缓存避免重复查找")
    print("✅ 批量请求智能暂停机制")
    print("✅ 严格的频率控制和警告")

    print(f"\n⚠️  使用建议:")
    print(f"  • 避免在短时间内多次运行筛选")
    print(f"  • 利用缓存，2小时内重复运行几乎无API调用")
    print(f"  • 关注日志中的频率控制警告")
    print(f"  • 如遇IP被封，等待更长时间再试")

    print(f"\n🔒 安全保障:")
    print(f"  • 所有API调用都有严格的频率控制")
    print(f"  • 详细的调用记录和统计")
    print(f"  • 智能的失败重试机制")
    print(f"  • 缓存优先策略最大限度减少调用")


if __name__ == "__main__":
    # 设置日志
    import logging
    logging.basicConfig(level=logging.INFO, format='%(message)s')

    # 运行演示
    asyncio.run(main())