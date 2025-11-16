#!/usr/bin/env python3
"""
测试本地缓存机制
"""

import asyncio
import sys
import os
sys.path.append('src')

from buffett.strategies.data_fetch_strategies import AKShareStrategy, LocalCache


async def test_cache_mechanism():
    """测试缓存机制"""
    print("🧪 开始测试本地缓存机制...")

    # 1. 测试缓存初始化
    print("\n1. 测试缓存初始化")
    strategy = AKShareStrategy(cache_ttl_hours=1, enable_cache=True)
    print(f"✅ 缓存启用: {strategy.enable_cache}")
    print(f"✅ 缓存对象: {strategy.cache is not None}")

    # 2. 测试缓存统计
    print("\n2. 缓存统计信息")
    stats = strategy.get_cache_stats()
    if stats:
        print(f"📁 缓存目录: {stats['cache_dir']}")
        print(f"📊 股息文件数: {stats['dividend_files']}")
        print(f"📈 股票文件数: {stats['stock_files']}")
        print(f"💾 总大小: {stats['total_size_mb']:.2f} MB")
    else:
        print("❌ 无缓存统计信息")

    # 3. 测试数据获取和缓存
    print("\n3. 测试数据获取和缓存")
    test_symbol = "000001.SZ"  # 平安银行

    # 首次获取（应该从API获取并缓存）
    print(f"📡 首次获取 {test_symbol} 的股票信息...")
    stock_info = await strategy.fetch_stock_basic_info(test_symbol)
    if stock_info:
        print(f"✅ 获取成功: {stock_info.get('name', 'Unknown')}")
    else:
        print("❌ 获取失败")

    # 第二次获取（应该从缓存获取）
    print(f"📦 第二次获取 {test_symbol} 的股票信息...")
    stock_info_cached = await strategy.fetch_stock_basic_info(test_symbol)
    if stock_info_cached:
        print(f"✅ 从缓存获取成功: {stock_info_cached.get('name', 'Unknown')}")
    else:
        print("❌ 缓存获取失败")

    # 4. 测试股息数据缓存
    print(f"\n4. 测试股息数据缓存 {test_symbol}...")
    dividend_data = await strategy.fetch_dividend_data(test_symbol)
    if not dividend_data.empty:
        print(f"✅ 获取到 {len(dividend_data)} 条股息记录")
        print(dividend_data[['symbol', 'year', 'cash_dividend']].head())
    else:
        print("❌ 无股息数据")

    # 5. 再次测试股息数据（应该从缓存获取）
    print(f"\n5. 再次测试股息数据缓存 {test_symbol}...")
    dividend_data_cached = await strategy.fetch_dividend_data(test_symbol)
    if not dividend_data_cached.empty:
        print(f"✅ 从缓存获取到 {len(dividend_data_cached)} 条股息记录")
    else:
        print("❌ 缓存中无股息数据")

    # 6. 最终缓存统计
    print("\n6. 最终缓存统计")
    final_stats = strategy.get_cache_stats()
    if final_stats:
        print(f"📁 缓存目录: {final_stats['cache_dir']}")
        print(f"📊 股息文件数: {final_stats['dividend_files']}")
        print(f"📈 股票文件数: {final_stats['stock_files']}")
        print(f"💾 总大小: {final_stats['total_size_mb']:.2f} MB")

    # 7. 测试缓存清理
    print("\n7. 测试缓存清理")
    strategy.clear_cache("000001")
    print("✅ 清理特定股票缓存完成")

    print("\n🎉 缓存机制测试完成!")


if __name__ == "__main__":
    asyncio.run(test_cache_mechanism())