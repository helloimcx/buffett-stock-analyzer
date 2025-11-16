#!/usr/bin/env python3
"""
Buffett 股息筛选系统 - 主入口文件
现代化企业级架构的主程序入口
"""

import asyncio
import sys
import argparse
from pathlib import Path
import logging
from datetime import datetime

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from buffett.core.container import get_container
from buffett.factories.repository_factory import RepositoryFactory, RepositoryType
from buffett.factories.strategy_factory import StrategyFactory, DataSourceType
from buffett.strategies.data_fetch_strategies import DataFetchContext
from buffett.core.screening import ScreeningService
from buffett.models.screening import ScreeningCriteria
from buffett.config.settings import get_settings
from buffett.config.target_stocks import get_target_stocks_config
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Any
from buffett.config.target_stocks import TargetStock


def setup_logging():
    """配置日志落盘"""
    # 创建日志目录
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # 配置日志格式
    log_format = "%(asctime)s | %(levelname)s | %(name)s:%(lineno)d - %(message)s"

    # 设置日志文件名（按时间）
    log_file = log_dir / f"buffett_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    # 配置根日志器
    logging.basicConfig(
        level=logging.DEBUG,
        format=log_format,
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

    print(f"📝 日志已保存到: {log_file}")
    return log_file


async def run_targeted_screening(config_file: Optional[str] = None):
    """运行指定股票代码的筛选"""
    # 配置日志
    log_file = setup_logging()
    logger = logging.getLogger(__name__)

    print("🎯 Buffett 股息筛选系统 - 指定股票筛选模式...")
    logger.info("=== Buffett 股息筛选系统启动 (指定股票模式) ===")

    # 获取配置
    settings = get_settings()
    print(f"📋 筛选配置: 最低股息率 {settings.screening.min_dividend_yield}%")
    logger.info(f"筛选配置: 最低股息率 {settings.screening.min_dividend_yield}%")

    # 加载目标股票配置
    target_config = get_target_stocks_config(config_file)
    target_stocks = target_config.get_target_stocks()

    if not target_stocks:
        print("❌ 未找到目标股票配置，请检查配置文件")
        return

    print(f"🎯 目标股票: {len(target_stocks)} 只")
    for stock in target_stocks:
        print(f"   - {stock.symbol} {stock.name}")

    # 设置依赖注入容器
    container = get_container()

    # 创建依赖
    strategy_factory = StrategyFactory.create_for_production()
    repo_factory = RepositoryFactory.create_for_production()

    # 创建策略 - 使用优化的AKShare策略
    settings = get_settings()
    data_source = settings.data.data_source

    # 构建策略配置
    strategy_config = {
        "enable_cache": settings.data.optimized_enable_cache,
        "cache_ttl_hours": settings.data.optimized_cache_ttl_hours,
        "timeout": settings.data.timeout_seconds,
        "proxy": settings.data.akshare_proxy
    }

    strategy = strategy_factory.create_data_fetch_strategy(data_source, strategy_config)
    data_context = DataFetchContext(strategy)

    print(f"🚀 使用数据源: {data_source}")
    if data_source == "optimized_akshare":
        print("   ✅ 智能缓存: 已启用" if strategy_config["enable_cache"] else "   ⚠️  智能缓存: 已禁用")
        print(f"   ⏰ 缓存TTL: {strategy_config['cache_ttl_hours']} 小时")

    try:
        # 获取全量股票数据
        print("📊 正在获取股票列表...")
        stocks_data = await data_context.fetch_all_stocks()
        print(f"✅ 获取到 {len(stocks_data)} 只股票")

        if stocks_data.empty:
            print("⚠️  没有获取到股票数据，请检查数据源配置")
            return

        # 筛选目标股票
        print(f"🔍 筛选目标股票...")
        target_stocks_data = target_config.filter_stocks_by_codes(stocks_data)
        print(f"✅ 筛选出 {len(target_stocks_data)} 只目标股票")

        if target_stocks_data.empty:
            print("⚠️  没有找到目标股票数据")
            return

        # 创建并注册Repository，传入共享的strategy以支持缓存
        stock_repo = repo_factory.create_repository(RepositoryType.STOCK, config=None, strategy=strategy)
        dividend_repo = repo_factory.create_repository(RepositoryType.DIVIDEND)
        price_repo = repo_factory.create_repository(RepositoryType.PRICE)

        # 加载目标股票数据到Repository
        stock_repo.load_from_dataframe(target_stocks_data)
        stocks = await stock_repo.get_all_stocks()

        # Register by interface types, not concrete class types
        from buffett.interfaces.repositories import IStockRepository, IDividendRepository, IPriceRepository
        from buffett.models.industry import IndustryConfig, IndustryLeader

        # Create a default industry config
        default_industry_config = IndustryConfig(
            industry_name="默认行业",
            leaders=[IndustryLeader(symbol="000001.SZ", name="示例龙头", market_cap_tier=1)],
            default_top_n=3
        )

        # Register instances, not classes (use register_instance for existing objects)
        container.register_instance(IStockRepository, stock_repo)
        container.register_instance(IDividendRepository, dividend_repo)
        container.register_instance(IPriceRepository, price_repo)
        container.register_instance(IndustryConfig, default_industry_config)

        # 创建筛选条件
        criteria = ScreeningCriteria(
            min_dividend_yield=settings.screening.min_dividend_yield,
            min_dividend_years=settings.screening.min_dividend_years,
            industry_leader_priority=settings.screening.industry_leader_priority
        )

        # 创建筛选服务
        screening_service = ScreeningService(container=container)

        print(f"🎯 执行四步投资策略筛选 (目标股票)...")
        # 运行筛选
        results = await screening_service.run_complete_screening(criteria, stocks)

        # 输出结果
        await output_results(results, target_mode=True, target_stocks=target_stocks)

        print(f"\n🎉 指定股票筛选完成！")
        print(f"📊 筛选结果: 从 {len(target_stocks)} 只目标股票中筛选出 {len(results)} 只符合条件的股票")

    except Exception as e:
        logger.error(f"筛选过程中发生错误: {str(e)}")
        print(f"❌ 筛选失败: {str(e)}")
        raise


async def output_results(results: List[Any], target_mode: bool = False, target_stocks: Optional[List[TargetStock]] = None):
    """输出筛选结果"""
    logger = logging.getLogger(__name__)

    if not results:
        print("📊 筛选结果: 无符合条件的股票")
        return

    print(f"\n📊 筛选结果: {len(results)} 只符合条件的股票")
    print("=" * 80)

    # 输出结果表格
    print(f"{'序号':<4} {'股票代码':<10} {'股票名称':<12} {'股息率':<8} {'分红年数':<8} {'市值(亿)':<10} {'行业':<10}")
    print("-" * 80)

    for i, stock in enumerate(results, 1):
        code = getattr(stock, 'code', 'N/A')
        name = getattr(stock, 'name', 'N/A')
        dividend_yield = getattr(stock, 'dividend_yield', 0)
        dividend_years = getattr(stock, 'dividend_years', 0)
        market_cap = getattr(stock, 'market_cap', 0)
        industry = getattr(stock, 'industry', 'N/A')

        # 格式化显示
        market_cap_display = f"{market_cap/100000000:.0f}" if market_cap and market_cap > 0 else "N/A"
        dividend_yield_display = f"{dividend_yield:.2f}%" if dividend_yield else "N/A"
        dividend_years_display = f"{dividend_years}" if dividend_years else "N/A"

        print(f"{i:<4} {code:<10} {name:<12} {dividend_yield_display:<8} {dividend_years_display:<8} {market_cap_display:<10} {industry:<10}")

    print("=" * 80)

    # 如果是目标模式，显示统计信息
    if target_mode and target_stocks:
        target_count = len(target_stocks)
        passed_count = len(results)
        pass_rate = (passed_count / target_count * 100) if target_count > 0 else 0

        print(f"\n🎯 目标模式统计:")
        print(f"   目标股票数量: {target_count}")
        print(f"   通过筛选数量: {passed_count}")
        print(f"   通过率: {pass_rate:.1f}%")

    # 保存结果到文件
    try:
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if target_mode:
            filename = f"targeted_screening_results_{timestamp}.json"
        else:
            filename = f"screening_results_{timestamp}.json"

        filepath = reports_dir / filename

        # 转换结果为可序列化的格式
        results_data = []
        for stock in results:
            stock_dict = {
                'code': getattr(stock, 'code', 'N/A'),
                'name': getattr(stock, 'name', 'N/A'),
                'dividend_yield': getattr(stock, 'dividend_yield', 0),
                'dividend_years': getattr(stock, 'dividend_years', 0),
                'market_cap': getattr(stock, 'market_cap', 0),
                'industry': getattr(stock, 'industry', 'N/A'),
                'pe_ratio': getattr(stock, 'pe_ratio', 0),
                'pb_ratio': getattr(stock, 'pb_ratio', 0),
                'current_price': getattr(stock, 'current_price', 0),
                'eligibility_score': getattr(stock, 'eligibility_score', 0),
                'valuation_score': getattr(stock, 'valuation_score', 0),
                'trend_score': getattr(stock, 'trend_score', 0),
                'risk_score': getattr(stock, 'risk_score', 0),
                'total_score': getattr(stock, 'total_score', 0)
            }
            results_data.append(stock_dict)

        # 添加元数据
        output_data = {
            'timestamp': datetime.now().isoformat(),
            'screening_type': 'targeted' if target_mode else 'full',
            'criteria': {
                'min_dividend_yield': get_settings().screening.min_dividend_yield,
                'min_dividend_years': get_settings().screening.min_dividend_years,
                'industry_leader_priority': get_settings().screening.industry_leader_priority
            },
            'statistics': {
                'total_results': len(results),
                'target_stocks_count': len(target_stocks) if target_mode else None,
                'pass_rate': (len(results) / len(target_stocks) * 100) if target_mode and target_stocks else None
            },
            'results': results_data
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        print(f"\n💾 结果已保存到: {filepath}")
        logger.info(f"筛选结果已保存到: {filepath}")

    except Exception as e:
        logger.error(f"保存结果失败: {e}")
        print(f"⚠️  保存结果失败: {e}")


async def run_screening():
    """运行股票筛选"""
    # 配置日志
    log_file = setup_logging()
    logger = logging.getLogger(__name__)

    print("🚀 Buffett 股息筛选系统 - 启动筛选...")
    logger.info("=== Buffett 股息筛选系统启动 ===")

    # 获取配置
    settings = get_settings()
    print(f"📋 筛选配置: 最低股息率 {settings.screening.min_dividend_yield}%")
    logger.info(f"筛选配置: 最低股息率 {settings.screening.min_dividend_yield}%")

    # 设置依赖注入容器
    container = get_container()

    # 创建依赖
    strategy_factory = StrategyFactory.create_for_production()
    repo_factory = RepositoryFactory.create_for_production()

    # 创建策略 - 使用优化的AKShare策略
    data_source = settings.data.data_source

    # 构建策略配置
    strategy_config = {
        "enable_cache": settings.data.optimized_enable_cache,
        "cache_ttl_hours": settings.data.optimized_cache_ttl_hours,
        "timeout": settings.data.timeout_seconds,
        "proxy": settings.data.akshare_proxy
    }

    strategy = strategy_factory.create_data_fetch_strategy(data_source, strategy_config)
    data_context = DataFetchContext(strategy)

    print(f"🚀 使用数据源: {data_source}")
    if data_source == "optimized_akshare":
        print("   ✅ 智能缓存: 已启用" if strategy_config["enable_cache"] else "   ⚠️  智能缓存: 已禁用")
        print(f"   ⏰ 缓存TTL: {strategy_config['cache_ttl_hours']} 小时")

    try:
        # 获取股票数据
        print("📊 正在获取股票列表...")
        stocks_data = await data_context.fetch_all_stocks()
        print(f"✅ 获取到 {len(stocks_data)} 只股票")

        if stocks_data.empty:
            print("⚠️  没有获取到股票数据，请检查数据源配置")
            return

        # 创建并注册Repository，传入共享的strategy以支持缓存
        stock_repo = repo_factory.create_repository(RepositoryType.STOCK, config=None, strategy=strategy)
        dividend_repo = repo_factory.create_repository(RepositoryType.DIVIDEND)
        price_repo = repo_factory.create_repository(RepositoryType.PRICE)

        # 加载数据到Repository
        stock_repo.load_from_dataframe(stocks_data)
        stocks = await stock_repo.get_all_stocks()

        # Register by interface types, not concrete class types
        from buffett.interfaces.repositories import IStockRepository, IDividendRepository, IPriceRepository
        from buffett.models.industry import IndustryConfig, IndustryLeader

        # Create a default industry config
        default_industry_config = IndustryConfig(
            industry_name="默认行业",
            leaders=[IndustryLeader(symbol="000001.SZ", name="示例龙头", market_cap_tier=1)],
            default_top_n=3
        )

        # Register instances, not classes (use register_instance for existing objects)
        container.register_instance(IStockRepository, stock_repo)
        container.register_instance(IDividendRepository, dividend_repo)
        container.register_instance(IPriceRepository, price_repo)
        container.register_instance(IndustryConfig, default_industry_config)

        # 创建筛选条件
        criteria = ScreeningCriteria(
            min_dividend_yield=settings.screening.min_dividend_yield,
            min_dividend_years=settings.screening.min_dividend_years,
            industry_leader_priority=settings.screening.industry_leader_priority,
            top_n_per_industry=settings.screening.top_n_per_industry
        )

        print(f"🔍 开始筛选: 股息率≥{criteria.min_dividend_yield}%, 分红年数≥{criteria.min_dividend_years}年")

        # 创建并运行筛选服务
        screening_service = ScreeningService(container)

        print("🎯 执行四步投资策略筛选...")
        print("   第一步：资格筛选...")
        print("   第二步：估值评估...")
        print("   第三步：趋势分析...")
        print("   第四步：风险控制...")

        # 运行完整筛选
        result = await screening_service.run_complete_screening(criteria, stocks)

        print(f"✅ 筛选完成!")
        print(f"📊 筛选统计:")
        print(f"   - 资格筛选通过: {len(result.eligibility_results)} 只")
        print(f"   - 估值评估通过: {len(result.valuation_results)} 只")
        print(f"   - 趋势分析通过: {len(result.trend_results)} 只")
        print(f"   - 风险控制通过: {len(result.risk_results)} 只")
        print(f"   - 最终候选股票: {len(result.final_candidates)} 只")

        # 保存结果到报告目录
        await save_screening_results(result)

        print("📈 筛选结果已保存到报告目录")

        # 显示前5名候选股票
        if result.final_candidates:
            print("\n🏆 推荐股票前5名:")
            for i, candidate in enumerate(result.final_candidates[:5], 1):
                print(f"   {i}. {candidate['name']} ({candidate['symbol']}) - "
                      f"评分: {candidate['overall_score']:.1f} - "
                      f"等级: {candidate['investment_grade']}")
        else:
            print("\n⚠️  本次筛选没有找到符合所有条件的股票")

    except Exception as e:
        print(f"❌ 筛选失败: {e}")
        raise


async def run_monitoring():
    """运行风险监控"""
    print("⚠️  风险监控功能待实现...")
    print("💡 风险监控将基于新的Repository和Strategy架构实现")


async def show_config():
    """显示配置信息"""
    print("📋 Buffett 系统配置信息:")
    print("=" * 50)

    settings = get_settings()

    print(f"🏗️  架构版本: {settings.version}")
    print(f"🌍 运行环境: {settings.environment}")
    print(f"📁 数据目录: {settings.data_dir}")
    print(f"📄 报告目录: {settings.reports_dir}")

    print("\n🔍 筛选配置:")
    print(f"  最低股息率: {settings.screening.min_dividend_yield}%")
    print(f"  最少年限: {settings.screening.min_dividend_years}年")
    print(f"  优先龙头: {settings.screening.industry_leader_priority}")

    print("\n📊 数据配置:")
    print(f"  缓存时长: {settings.data.cache_duration_hours}小时")
    print(f"  更新频率: {settings.data.update_frequency_hours}小时")
    print(f"  超时时间: {settings.data.timeout_seconds}秒")

    print("\n🗂️  可用数据源:")
    strategy_factory = StrategyFactory()
    for source in strategy_factory.get_available_data_sources():
        print(f"  - {source}")


def install_dependencies():
    """安装项目依赖"""
    print("📦 正在安装项目依赖...")
    import subprocess
    try:
        result = subprocess.run([sys.executable, "-m", "uv", "sync"], check=True)
        print("✅ 依赖安装完成!")
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"❌ 依赖安装失败: {e}")
        return e.returncode


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Buffett 股息筛选系统 - 企业级股票筛选工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  %(prog)s screen          # 运行全量股票筛选
  %(prog)s target          # 运行指定股票筛选
  %(prog)s target -c my_stocks.conf  # 使用自定义配置文件
  %(prog)s monitor          # 运行风险监控
  %(prog)s config           # 显示配置信息
  %(prog)s install          # 安装依赖

环境变量:
  BUFFETT_ENVIRONMENT     # 运行环境 (development/production)
  BUFFETT_DATA_SOURCE     # 数据源 (akshare/mock/multi_source)
  BUFFETT_CACHE_BACKEND   # 缓存后端 (memory/file)
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # 筛选命令
    screen_parser = subparsers.add_parser('screen', help='运行全量股票筛选')
    screen_parser.add_argument('-v', '--verbose', action='store_true', help='详细输出')

    # 指定股票筛选命令
    target_parser = subparsers.add_parser('target', help='运行指定股票筛选')
    target_parser.add_argument('-c', '--config', type=str, help='指定股票配置文件路径')
    target_parser.add_argument('-v', '--verbose', action='store_true', help='详细输出')

    # 监控命令
    monitor_parser = subparsers.add_parser('monitor', help='运行风险监控')
    monitor_parser.add_argument('-v', '--verbose', action='store_true', help='详细输出')

    # 配置命令
    config_parser = subparsers.add_parser('config', help='显示配置信息')

    # 安装命令
    install_parser = subparsers.add_parser('install', help='安装项目依赖')

    # 启动命令（持续监控）
    start_parser = subparsers.add_parser('start', help='启动持续监控')
    start_parser.add_argument('-v', '--verbose', action='store_true', help='详细输出')

    args = parser.parse_args()

    # 如果没有指定命令，显示帮助
    if not args.command:
        parser.print_help()
        return 0

    try:
        if args.command == 'screen':
            asyncio.run(run_screening())
        elif args.command == 'target':
            asyncio.run(run_targeted_screening(args.config))
        elif args.command == 'monitor':
            asyncio.run(run_monitoring())
        elif args.command == 'config':
            asyncio.run(show_config())
        elif args.command == 'install':
            return install_dependencies()
        elif args.command == 'start':
            print("🔄 启动持续监控模式...")
            print("💡 按Ctrl+C停止监控")
            asyncio.run(run_monitoring())
        else:
            parser.print_help()
            return 1

    except KeyboardInterrupt:
        print("\n👋 程序已停止")
        return 0
    except Exception as e:
        print(f"❌ 程序执行失败: {e}")
        if args.verbose if hasattr(args, 'verbose') else False:
            import traceback
            traceback.print_exc()
        return 1

    return 0


async def save_screening_results(result):
    """保存筛选结果到JSON文件"""
    try:
        settings = get_settings()
        reports_dir = Path(settings.reports_dir)
        reports_dir.mkdir(parents=True, exist_ok=True)

        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"buffett_screening_{timestamp}.json"
        filepath = reports_dir / filename

        # 准备保存的数据
        save_data = {
            "screening_info": {
                "generated_at": datetime.now().isoformat(),
                "criteria": result.criteria.model_dump() if hasattr(result.criteria, 'model_dump') else str(result.criteria),
                "execution_time_seconds": result.execution_time
            },
            "summary": result.summary,
            "final_candidates": result.final_candidates,
            "statistics": {
                "total_stocks_input": result.summary["step_results"]["eligibility"].get("input_count", 0),
                "eligibility_passed": len(result.eligibility_results),
                "valuation_passed": len(result.valuation_results),
                "trend_passed": len(result.trend_results),
                "risk_passed": len(result.risk_results),
                "final_candidates": len(result.final_candidates)
            }
        }

        # 保存到文件
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2, default=str)

        print(f"📄 详细结果已保存到: {filepath}")

    except Exception as e:
        print(f"⚠️  保存筛选结果时发生错误: {e}")


if __name__ == "__main__":
    sys.exit(main())