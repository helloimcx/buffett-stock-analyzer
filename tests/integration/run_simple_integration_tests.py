"""
简化的集成测试运行器
运行核心集成测试并生成报告
"""

import sys
import os
import unittest
import time
import json
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

def main():
    """主函数：运行简化的集成测试"""
    print("=" * 80)
    print("巴菲特投资系统 - 简化集成测试套件")
    print("=" * 80)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 创建报告目录
    reports_dir = Path("reports/integration")
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    # 测试结果
    test_results = []
    test_start_time = time.time()
    
    try:
        # 测试1：多因子评分系统基本功能
        print("\n🧮 测试1：多因子评分系统基本功能")
        print("-" * 60)
        
        try:
            from buffett.core.multi_factor_scoring import MultiFactorScorer, ValueFactor, GrowthFactor
            
            # 创建评分器
            scorer = MultiFactorScorer()
            scorer.add_factor(ValueFactor(weight=0.5))
            scorer.add_factor(GrowthFactor(weight=0.5))
            
            # 创建测试股票
            from tests.integration.test_framework import TestDataGenerator
            test_stock = TestDataGenerator.create_test_stock("TEST001", "测试股票", 10.0, 5.0, 15.0, 2.0)
            
            # 计算评分
            score = scorer.calculate_score(test_stock)
            
            # 验证结果
            assert 0 <= score <= 1, f"评分应在0-1范围内: {score}"
            
            print(f"✅ 多因子评分测试通过: {score:.3f}")
            test_results.append({
                "test_name": "多因子评分系统基本功能",
                "status": "PASSED",
                "message": f"评分: {score:.3f}",
                "duration": 0.1
            })
            
        except Exception as e:
            print(f"❌ 多因子评分测试失败: {e}")
            test_results.append({
                "test_name": "多因子评分系统基本功能",
                "status": "FAILED",
                "message": str(e),
                "duration": 0.1
            })
        
        # 测试2：技术分析模块基本功能
        print("\n📈 测试2：技术分析模块基本功能")
        print("-" * 60)
        
        try:
            from buffett.strategies.technical_analysis import TechnicalSignalGenerator
            
            # 创建技术分析器
            signal_generator = TechnicalSignalGenerator()
            
            # 创建测试数据
            prices = [10.0 + i * 0.1 for i in range(30)]
            volumes = [1000000 + i * 10000 for i in range(30)]
            
            # 生成信号
            signals = signal_generator.generate_signals(prices, volumes)
            signal_strength = signal_generator.calculate_signal_strength(prices, volumes)
            
            # 验证结果
            assert isinstance(signals, dict), "信号结果应为字典"
            assert 'buy_signals' in signals, "应包含买入信号"
            assert 'sell_signals' in signals, "应包含卖出信号"
            assert -1 <= signal_strength <= 1, f"信号强度应在-1到1范围内: {signal_strength}"
            
            print(f"✅ 技术分析测试通过: 买入信号={len(signals['buy_signals'])}, 卖出信号={len(signals['sell_signals'])}, 强度={signal_strength:.3f}")
            test_results.append({
                "test_name": "技术分析模块基本功能",
                "status": "PASSED",
                "message": f"买入信号={len(signals['buy_signals'])}, 卖出信号={len(signals['sell_signals'])}, 强度={signal_strength:.3f}",
                "duration": 0.1
            })
            
        except Exception as e:
            print(f"❌ 技术分析测试失败: {e}")
            test_results.append({
                "test_name": "技术分析模块基本功能",
                "status": "FAILED",
                "message": str(e),
                "duration": 0.1
            })
        
        # 测试3：市场环境识别基本功能
        print("\n🌡️ 测试3：市场环境识别基本功能")
        print("-" * 60)
        
        try:
            from buffett.core.market_environment import MarketEnvironmentIdentifier
            
            # 创建环境识别器
            identifier = MarketEnvironmentIdentifier()
            
            # 创建测试数据
            market_data = {
                "prices": [100 + i * 0.5 for i in range(60)],
                "volumes": [1000000 + i * 10000 for i in range(60)],
                "current_volume": 1000000 + 59 * 10000,
                "avg_volume": 1000000 + 30 * 10000,
                "advancing_stocks": 150,
                "declining_stocks": 50,
                "momentum": 0.03
            }
            
            # 识别环境
            environment = identifier.identify_environment(market_data)
            
            # 验证结果
            assert hasattr(environment, 'environment_type'), "应包含环境类型"
            assert hasattr(environment, 'confidence'), "应包含置信度"
            assert 0 <= environment.confidence <= 1, f"置信度应在0-1范围内: {environment.confidence}"
            
            print(f"✅ 市场环境识别测试通过: 类型={environment.environment_type.value}, 置信度={environment.confidence:.3f}")
            test_results.append({
                "test_name": "市场环境识别基本功能",
                "status": "PASSED",
                "message": f"类型={environment.environment_type.value}, 置信度={environment.confidence:.3f}",
                "duration": 0.1
            })
            
        except Exception as e:
            print(f"❌ 市场环境识别测试失败: {e}")
            test_results.append({
                "test_name": "市场环境识别基本功能",
                "status": "FAILED",
                "message": str(e),
                "duration": 0.1
            })
        
        # 测试4：风险管理基本功能
        print("\n⚠️ 测试4：风险管理基本功能")
        print("-" * 60)
        
        try:
            from buffett.core.risk_management import RiskManager, RiskConfig
            
            # 创建风险管理器
            risk_config = RiskConfig()
            risk_manager = RiskManager(risk_config)
            
            # 创建测试股票
            test_stock = TestDataGenerator.create_test_stock("RISK001", "风险测试股票", 10.0, 5.0, 15.0, 2.0)
            
            # 计算止损价格
            purchase_price = 9.0
            stop_loss_price = risk_manager.calculate_stop_loss(test_stock, purchase_price)
            
            # 验证结果
            assert stop_loss_price > 0, "止损价格应大于0"
            assert stop_loss_price < purchase_price, "止损价格应小于买入价格"
            
            print(f"✅ 风险管理测试通过: 买入价={purchase_price:.2f}, 止损价={stop_loss_price:.2f}")
            test_results.append({
                "test_name": "风险管理基本功能",
                "status": "PASSED",
                "message": f"买入价={purchase_price:.2f}, 止损价={stop_loss_price:.2f}",
                "duration": 0.1
            })
            
        except Exception as e:
            print(f"❌ 风险管理测试失败: {e}")
            test_results.append({
                "test_name": "风险管理基本功能",
                "status": "FAILED",
                "message": str(e),
                "duration": 0.1
            })
        
        # 测试5：模块集成测试
        print("\n🔗 测试5：模块集成测试")
        print("-" * 60)
        
        try:
            # 创建所有组件
            scorer = MultiFactorScorer()
            scorer.add_factor(ValueFactor(weight=0.4))
            scorer.add_factor(GrowthFactor(weight=0.3))
            
            signal_generator = TechnicalSignalGenerator()
            identifier = MarketEnvironmentIdentifier()
            risk_manager = RiskManager(RiskConfig())
            
            # 创建测试股票
            test_stock = TestDataGenerator.create_test_stock("INTEGRATION001", "集成测试股票", 10.0, 5.0, 15.0, 2.0)
            
            # 综合评分
            base_score = scorer.calculate_score(test_stock)
            
            # 技术分析
            prices = [10.0 + i * 0.1 for i in range(30)]
            volumes = [1000000 + i * 10000 for i in range(30)]
            signals = signal_generator.generate_signals(prices, volumes)
            signal_strength = signal_generator.calculate_signal_strength(prices, volumes)
            
            # 市场环境
            market_data = {
                "prices": prices,
                "volumes": volumes,
                "current_volume": volumes[-1],
                "avg_volume": sum(volumes) / len(volumes),
                "advancing_stocks": 120,
                "declining_stocks": 80,
                "momentum": 0.02
            }
            environment = identifier.identify_environment(market_data)
            
            # 风险控制
            purchase_price = 9.5
            stop_loss_price = risk_manager.calculate_stop_loss(test_stock, purchase_price)
            
            # 综合决策
            integrated_score = base_score + signal_strength * 0.1
            if environment.environment_type.value == "bull":
                integrated_score += 0.05
            elif environment.environment_type.value == "bear":
                integrated_score -= 0.05
            
            final_decision = "买入" if integrated_score > 0.6 else "持有" if integrated_score > 0.4 else "卖出"
            
            # 验证集成结果
            assert 0 <= base_score <= 1, f"基础评分应在0-1范围内: {base_score}"
            assert -1 <= signal_strength <= 1, f"信号强度应在-1到1范围内: {signal_strength}"
            assert 0 <= integrated_score <= 1, f"综合评分应在0-1范围内: {integrated_score}"
            
            print(f"✅ 模块集成测试通过:")
            print(f"   基础评分: {base_score:.3f}")
            print(f"   信号强度: {signal_strength:.3f}")
            print(f"   市场环境: {environment.environment_type.value}")
            print(f"   综合评分: {integrated_score:.3f}")
            print(f"   最终决策: {final_decision}")
            
            test_results.append({
                "test_name": "模块集成测试",
                "status": "PASSED",
                "message": f"基础评分={base_score:.3f}, 信号强度={signal_strength:.3f}, 环境={environment.environment_type.value}, 决策={final_decision}",
                "duration": 0.2
            })
            
        except Exception as e:
            print(f"❌ 模块集成测试失败: {e}")
            test_results.append({
                "test_name": "模块集成测试",
                "status": "FAILED",
                "message": str(e),
                "duration": 0.2
            })
        
        # 测试6：性能测试
        print("\n⚡ 测试6：性能测试")
        print("-" * 60)
        
        try:
            # 大量数据测试
            large_dataset = []
            for i in range(100):
                stock = TestDataGenerator.create_test_stock(
                    f"PERF{i:03d}", f"性能测试股票{i}",
                    price=10.0 + i * 0.01,
                    dividend_yield=5.0 + (i % 10) * 0.1,
                    pe_ratio=15.0 + (i % 20) * 0.1,
                    pb_ratio=2.0 + (i % 10) * 0.1
                )
                large_dataset.append(stock)
            
            # 性能测试
            start_time = time.time()
            ranked_stocks = scorer.rank_stocks(large_dataset)
            end_time = time.time()
            
            processing_time = end_time - start_time
            throughput = len(large_dataset) / processing_time
            
            # 验证性能
            assert len(ranked_stocks) == len(large_dataset), "排序结果数量应匹配"
            assert processing_time < 5.0, f"处理时间应少于5秒: {processing_time}"
            assert throughput > 10, f"吞吐量应大于10股/秒: {throughput}"
            
            print(f"✅ 性能测试通过:")
            print(f"   数据量: {len(large_dataset)}只股票")
            print(f"   处理时间: {processing_time:.3f}秒")
            print(f"   吞吐量: {throughput:.0f}股/秒")
            
            test_results.append({
                "test_name": "性能测试",
                "status": "PASSED",
                "message": f"数据量={len(large_dataset)}, 时间={processing_time:.3f}秒, 吞吐量={throughput:.0f}股/秒",
                "duration": processing_time
            })
            
        except Exception as e:
            print(f"❌ 性能测试失败: {e}")
            test_results.append({
                "test_name": "性能测试",
                "status": "FAILED",
                "message": str(e),
                "duration": 0.1
            })
    
    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")
        test_results.append({
            "test_name": "模块导入",
            "status": "FAILED",
            "message": f"导入错误: {e}",
            "duration": 0.1
        })
    
    # 计算总体结果
    total_time = time.time() - test_start_time
    total_tests = len(test_results)
    passed_tests = len([r for r in test_results if r["status"] == "PASSED"])
    failed_tests = total_tests - passed_tests
    success_rate = passed_tests / total_tests if total_tests > 0 else 0
    
    print(f"\n{'='*80}")
    print("集成测试汇总")
    print(f"{'='*80}")
    print(f"总测试数: {total_tests}")
    print(f"通过测试: {passed_tests}")
    print(f"失败测试: {failed_tests}")
    print(f"成功率: {success_rate:.1%}")
    print(f"总耗时: {total_time:.2f}秒")
    print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 生成报告
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # JSON报告
    report_data = {
        "report_type": "integration_test_summary",
        "timestamp": datetime.now().isoformat(),
        "test_summary": {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": success_rate,
            "total_time": total_time
        },
        "test_results": test_results
    }
    
    summary_file = reports_dir / f"integration_test_summary_{timestamp}.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
    
    # HTML报告
    html_file = reports_dir / f"integration_test_report_{timestamp}.html"
    generate_html_report(report_data, html_file)
    
    print(f"\n📋 报告文件:")
    print(f"  JSON报告: {summary_file}")
    print(f"  HTML报告: {html_file}")
    
    # 返回退出码
    if failed_tests > 0:
        print(f"\n⚠️  集成测试未完全通过，请检查失败详情")
        return 1
    else:
        print(f"\n✅ 所有集成测试通过！")
        return 0


def generate_html_report(report_data, output_file):
    """生成HTML格式的测试报告"""
    html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>巴菲特投资系统 - 集成测试报告</title>
    <style>
        body {{
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1, h2 {{
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }}
        h1 {{ font-size: 2.5em; }}
        h2 {{ font-size: 1.8em; margin-top: 30px; }}
        .summary {{
            background-color: #ecf0f1;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .test-result {{
            border: 1px solid #ddd;
            margin: 15px 0;
            padding: 15px;
            border-radius: 5px;
        }}
        .success {{ border-left: 5px solid #27ae60; background-color: #f9f9f9; }}
        .failure {{ border-left: 5px solid #e74c3c; background-color: #fdf2f2; }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            text-align: center;
            border: 1px solid #e9ecef;
        }}
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            color: #2c3e50;
        }}
        .stat-label {{
            color: #7f8c8d;
            font-size: 0.9em;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{ background-color: #f2f2f2; font-weight: bold; }}
        .pass {{ color: #27ae60; }}
        .fail {{ color: #e74c3c; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 巴菲特投资系统 - 集成测试报告</h1>
        
        <div class="summary">
            <h2>📊 测试概览</h2>
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-value">{report_data['test_summary']['total_tests']}</div>
                    <div class="stat-label">总测试数</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{report_data['test_summary']['passed_tests']}</div>
                    <div class="stat-label">通过数</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{report_data['test_summary']['failed_tests']}</div>
                    <div class="stat-label">失败数</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{report_data['test_summary']['success_rate']:.1%}</div>
                    <div class="stat-label">成功率</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{report_data['test_summary']['total_time']:.2f}秒</div>
                    <div class="stat-label">总耗时</div>
                </div>
            </div>
        </div>
        
        <h2>📋 详细测试结果</h2>
        {generate_test_results_html(report_data['test_results'])}
        
        <div class="summary">
            <p><strong>报告生成时间:</strong> {report_data['timestamp']}</p>
        </div>
    </div>
</body>
</html>
    """
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)


def generate_test_results_html(test_results):
    """生成测试结果的HTML"""
    html = ""
    for result in test_results:
        status_class = "success" if result["status"] == "PASSED" else "failure"
        
        html += f"""
        <div class="test-result {status_class}">
            <h3>{result['test_name']}</h3>
            <p><strong>状态:</strong> <span class="{status_class}">{result['status']}</span></p>
            <p><strong>消息:</strong> {result['message']}</p>
            <p><strong>耗时:</strong> {result['duration']:.3f}秒</p>
        </div>
        """
    
    return html


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)