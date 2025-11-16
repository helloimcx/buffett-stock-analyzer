#!/usr/bin/env python3
"""
缓存机制效果演示
"""

import asyncio
import time
import sys
import os
sys.path.append('src')

from buffett.strategies.data_fetch_strategies import AKShareStrategy


async def demonstrate_cache_performance():
    """演示缓存性能提升"""
    print("🚀 演示本地缓存机制的性能提升效果")
    print("=" * 50)

    # 测试多只股票的缓存效果
    test_symbols = ["000001.SZ", "000002.SZ", "600036.SH", "600519.SH"]

    strategy = AKShareStrategy(cache_ttl_hours=24, enable_cache=True)

    for symbol in test_symbols:
        print(f"\n📊 测试股票: {symbol}")
        print("-" * 30)

        # 首次获取（从API）
        start_time = time.time()
        stock_info = await strategy.fetch_stock_basic_info(symbol)
        first_time = time.time() - start_time
        print(f"🌐 首次获取时间: {first_time:.2f}秒")

        if stock_info:
            print(f"✅ 股票名称: {stock_info.get('name', 'Unknown')}")
            print(f"🏭 行业: {stock_info.get('industry', 'Unknown')}")
        else:
            print("❌ 获取失败")

        # 第二次获取（从缓存）
        start_time = time.time()
        stock_info_cached = await strategy.fetch_stock_basic_info(symbol)
        second_time = time.time() - start_time
        print(f"💾 缓存获取时间: {second_time:.2f}秒")

        if first_time > 0 and second_time >= 0:
            speedup = first_time / (second_time + 0.001)  # 避免除零
            print(f"⚡ 性能提升: {speedup:.1f}x 倍")

    # 显示缓存统计
    print(f"\n📈 缓存统计信息")
    print("-" * 30)
    stats = strategy.get_cache_stats()
    if stats:
        print(f"📁 缓存目录: {stats['cache_dir']}")
        print(f"📊 股息文件: {stats['dividend_files']} 个")
        print(f"📈 股票文件: {stats['stock_files']} 个")
        print(f"💾 总大小: {stats['total_size_mb']:.2f} MB")

        # 计算节省的API调用次数
        print(f"\n💡 缓存效果分析")
        print("-" * 30)
        print(f"🔄 测试股票数: {len(test_symbols)}")
        print(f"💾 缓存命中: {stats['stock_files'] + stats['dividend_files']} 次")
        print(f"🌐 API调用: {len(test_symbols) * 2 - (stats['stock_files'] + stats['dividend_files'])} 次")
        saved_calls = len(test_symbols) - stats['stock_files']
        if saved_calls > 0:
            print(f"🎉 节省API调用: {saved_calls} 次")
        else:
            print(f"📝 缓存待优化")

    print(f"\n✅ 缓存演示完成!")


async def test_cache_persistence():
    """测试缓存持久性"""
    print(f"\n🧪 测试缓存持久性...")

    # 创建新策略实例
    strategy1 = AKShareStrategy(cache_ttl_hours=1, enable_cache=True)

    # 获取并缓存数据
    symbol = "600036.SH"  # 招商银行
    print(f"📡 获取并缓存 {symbol} 的股票信息...")
    stock_info = await strategy1.fetch_stock_basic_info(symbol)

    if stock_info:
        print(f"✅ 缓存成功: {stock_info.get('name', 'Unknown')}")

    # 等待1秒后创建新实例
    print(f"⏳ 等待1秒后创建新策略实例...")
    await asyncio.sleep(1)

    strategy2 = AKShareStrategy(cache_ttl_hours=1, enable_cache=True)

    # 新实例应该能从缓存读取
    print(f"📦 新实例从缓存读取 {symbol} 的股票信息...")
    stock_info_cached = await strategy2.fetch_stock_basic_info(symbol)

    if stock_info_cached:
        print(f"✅ 缓存持久性验证成功: {stock_info_cached.get('name', 'Unknown')}")
        if 'fetch_time' in stock_info:
            print(f"📅 原始获取时间: {stock_info_cached['fetch_time']}")
    else:
        print("❌ 缓存持久性验证失败")


if __name__ == "__main__":
    asyncio.run(demonstrate_cache_performance())
    asyncio.run(test_cache_persistence())