"""
集成测试运行器
运行所有集成测试并生成综合报告
"""

import sys
import os
import unittest
import time
import json
from pathlib import Path
from datetime import datetime
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from tests.integration.test_framework import IntegrationTestReporter, run_integration_tests
from tests.integration.test_multi_factor_integration import TestMultiFactorIntegration
from tests.integration.test_technical_analysis_integration import TestTechnicalAnalysisIntegration
from tests.integration.test_market_environment_integration import TestMarketEnvironmentIntegration
from tests.integration.test_risk_management_integration import TestRiskManagementIntegration
from tests.integration.test_end_to_end_workflow import TestEndToEndWorkflow
from tests.integration.test_performance_compatibility import TestPerformanceCompatibility


def main():
    """主函数：运行所有集成测试"""
    print("=" * 80)
    print("巴菲特投资系统 - 集成测试套件")
    print("=" * 80)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 创建报告目录
    reports_dir = Path("reports/integration")
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    # 测试类列表
    test_classes = [
        TestMultiFactorIntegration,
        TestTechnicalAnalysisIntegration,
        TestMarketEnvironmentIntegration,
        TestRiskManagementIntegration,
        TestEndToEndWorkflow,
        TestPerformanceCompatibility
    ]
    
    # 测试结果收集
    all_test_results = []
    test_start_time = time.time()
    
    # 运行每个测试类
    for i, test_class in enumerate(test_classes, 1):
        test_name = test_class.__name__
        print(f"\n{'='*20} 运行测试 {i}/{len(test_classes)}: {test_name} {'='*20}")
        
        # 创建测试套件
        suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
        
        # 运行测试
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        # 记录测试结果
        test_result = {
            "test_class": test_name,
            "tests_run": result.testsRun,
            "failures": len(result.failures),
            "errors": len(result.errors),
            "success_rate": (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun if result.testsRun > 0 else 0,
            "failure_details": [{"test": str(f[0]), "error": f[1]} for f in result.failures],
            "error_details": [{"test": str(e[0]), "error": e[1]} for e in result.errors]
        }
        
        all_test_results.append(test_result)
        
        print(f"\n{test_name} 测试完成:")
        print(f"  运行测试: {test_result['tests_run']}")
        print(f"  失败测试: {test_result['failures']}")
        print(f"  错误测试: {test_result['errors']}")
        print(f"  成功率: {test_result['success_rate']:.2%}")
    
    # 计算总体测试结果
    total_tests_run = sum(r["tests_run"] for r in all_test_results)
    total_failures = sum(r["failures"] for r in all_test_results)
    total_errors = sum(r["errors"] for r in all_test_results)
    total_success_rate = (total_tests_run - total_failures - total_errors) / total_tests_run if total_tests_run > 0 else 0
    total_time = time.time() - test_start_time
    
    print(f"\n{'='*80}")
    print("集成测试汇总")
    print(f"{'='*80}")
    print(f"总运行测试: {total_tests_run}")
    print(f"总失败测试: {total_failures}")
    print(f"总错误测试: {total_errors}")
    print(f"总体成功率: {total_success_rate:.2%}")
    print(f"总耗时: {total_time:.2f}秒")
    print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 生成详细报告
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 汇总报告
    summary_report = {
        "report_type": "integration_test_summary",
        "timestamp": datetime.now().isoformat(),
        "test_summary": {
            "total_tests_run": total_tests_run,
            "total_failures": total_failures,
            "total_errors": total_errors,
            "total_success_rate": total_success_rate,
            "total_time": total_time
        },
        "test_results": all_test_results
    }
    
    summary_file = reports_dir / f"integration_test_summary_{timestamp}.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary_report, f, ensure_ascii=False, indent=2)
    
    # 详细报告
    detailed_report = {
        "report_type": "integration_test_detailed",
        "timestamp": datetime.now().isoformat(),
        "test_environment": {
            "python_version": sys.version,
            "platform": sys.platform,
            "working_directory": os.getcwd()
        },
        "test_classes": [cls.__name__ for cls in test_classes],
        "test_results": all_test_results,
        "performance_summary": generate_performance_summary(all_test_results),
        "compatibility_summary": generate_compatibility_summary(all_test_results)
    }
    
    detailed_file = reports_dir / f"integration_test_detailed_{timestamp}.json"
    with open(detailed_file, 'w', encoding='utf-8') as f:
        json.dump(detailed_report, f, ensure_ascii=False, indent=2)
    
    # HTML报告
    html_file = reports_dir / f"integration_test_report_{timestamp}.html"
    generate_html_report(detailed_report, html_file)
    
    print(f"\n报告文件:")
    print(f"  汇总报告: {summary_file}")
    print(f"  详细报告: {detailed_file}")
    print(f"  HTML报告: {html_file}")
    
    # 返回退出码
    if total_failures > 0 or total_errors > 0:
        print(f"\n⚠️  集成测试未完全通过，请检查失败和错误详情")
        return 1
    else:
        print(f"\n✅ 所有集成测试通过！")
        return 0


def generate_performance_summary(test_results):
    """生成性能摘要"""
    performance_summary = {
        "test_classes_with_performance": [],
        "performance_issues": []
    }
    
    for result in test_results:
        test_class = result["test_class"]
        
        # 检查是否有性能相关的失败
        performance_failures = [
            f for f in result["failure_details"] 
            if "性能" in f["error"] or "performance" in f["error"].lower()
        ]
        
        performance_errors = [
            e for e in result["error_details"] 
            if "性能" in e["error"] or "performance" in e["error"].lower()
        ]
        
        if performance_failures or performance_errors:
            performance_summary["test_classes_with_performance"].append(test_class)
            performance_summary["performance_issues"].extend([
                {"test_class": test_class, "type": "failure", "detail": f}
                for f in performance_failures
            ])
            performance_summary["performance_issues"].extend([
                {"test_class": test_class, "type": "error", "detail": e}
                for e in performance_errors
            ])
    
    return performance_summary


def generate_compatibility_summary(test_results):
    """生成兼容性摘要"""
    compatibility_summary = {
        "test_classes_with_compatibility": [],
        "compatibility_issues": []
    }
    
    for result in test_results:
        test_class = result["test_class"]
        
        # 检查是否有兼容性相关的失败
        compatibility_failures = [
            f for f in result["failure_details"] 
            if "兼容" in f["error"] or "compatibility" in f["error"].lower()
        ]
        
        compatibility_errors = [
            e for e in result["error_details"] 
            if "兼容" in e["error"] or "compatibility" in e["error"].lower()
        ]
        
        if compatibility_failures or compatibility_errors:
            compatibility_summary["test_classes_with_compatibility"].append(test_class)
            compatibility_summary["compatibility_issues"].extend([
                {"test_class": test_class, "type": "failure", "detail": f}
                for f in compatibility_failures
            ])
            compatibility_summary["compatibility_issues"].extend([
                {"test_class": test_class, "type": "error", "detail": e}
                for e in compatibility_errors
            ])
    
    return compatibility_summary


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
        h1, h2, h3 {{
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }}
        h1 {{ font-size: 2.5em; }}
        h2 {{ font-size: 1.8em; margin-top: 30px; }}
        h3 {{ font-size: 1.4em; margin-top: 25px; }}
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
        .success {{ border-left: 5px solid #27ae60; }}
        .failure {{ border-left: 5px solid #e74c3c; }}
        .error {{ border-left: 5px solid #e67e22; }}
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
        .error {{ color: #e67e22; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 巴菲特投资系统 - 集成测试报告</h1>
        
        <div class="summary">
            <h2>📊 测试概览</h2>
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-value">{report_data['test_results'][0]['tests_run'] if report_data['test_results'] else 0}</div>
                    <div class="stat-label">总测试数</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{sum(r['failures'] for r in report_data['test_results'])}</div>
                    <div class="stat-label">失败数</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{sum(r['errors'] for r in report_data['test_results'])}</div>
                    <div class="stat-label">错误数</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{report_data['test_results'][0]['success_rate']:.1% if report_data['test_results'] else '0%'}</div>
                    <div class="stat-label">成功率</div>
                </div>
            </div>
        </div>
        
        <h2>📋 详细测试结果</h2>
        {generate_test_results_html(report_data['test_results'])}
        
        <h2>⚡ 性能摘要</h2>
        {generate_performance_html(report_data.get('performance_summary', {}))}
        
        <h2>🔄 兼容性摘要</h2>
        {generate_compatibility_html(report_data.get('compatibility_summary', {}))}
        
        <div class="summary">
            <p><strong>报告生成时间:</strong> {report_data['timestamp']}</p>
            <p><strong>测试环境:</strong> {report_data.get('test_environment', {}).get('platform', 'Unknown')}</p>
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
        status_class = "success" if result['failures'] == 0 and result['errors'] == 0 else "failure"
        if result['errors'] > 0:
            status_class = "error"
        
        html += f"""
        <div class="test-result {status_class}">
            <h3>{result['test_class']}</h3>
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-value">{result['tests_run']}</div>
                    <div class="stat-label">运行测试</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value fail">{result['failures']}</div>
                    <div class="stat-label">失败</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value error">{result['errors']}</div>
                    <div class="stat-label">错误</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value pass">{result['success_rate']:.1%}</div>
                    <div class="stat-label">成功率</div>
                </div>
            </div>
        </div>
        """
    
    return html


def generate_performance_html(performance_summary):
    """生成性能摘要的HTML"""
    if not performance_summary.get('test_classes_with_performance'):
        return "<p>✅ 所有性能测试通过</p>"
    
    html = "<div class='test-result failure'>"
    html += "<h3>⚠️ 性能问题</h3>"
    html += "<table><tr><th>测试类</th><th>问题类型</th><th>详情</th></tr>"
    
    for issue in performance_summary.get('performance_issues', []):
        html += f"""
        <tr>
            <td>{issue['test_class']}</td>
            <td>{issue['type']}</td>
            <td>{issue['detail'][:100]}...</td>
        </tr>
        """
    
    html += "</table></div>"
    return html


def generate_compatibility_html(compatibility_summary):
    """生成兼容性摘要的HTML"""
    if not compatibility_summary.get('test_classes_with_compatibility'):
        return "<p>✅ 所有兼容性测试通过</p>"
    
    html = "<div class='test-result failure'>"
    html += "<h3>⚠️ 兼容性问题</h3>"
    html += "<table><tr><th>测试类</th><th>问题类型</th><th>详情</th></tr>"
    
    for issue in compatibility_summary.get('compatibility_issues', []):
        html += f"""
        <tr>
            <td>{issue['test_class']}</td>
            <td>{issue['type']}</td>
            <td>{issue['detail'][:100]}...</td>
        </tr>
        """
    
    html += "</table></div>"
    return html


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)