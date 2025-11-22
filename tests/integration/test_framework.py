"""
集成测试框架
提供集成测试的基础设施和工具类
"""

import unittest
import time
import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging

# 设置测试日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IntegrationTestBase(unittest.TestCase):
    """集成测试基类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建临时目录用于测试数据
        self.temp_dir = tempfile.mkdtemp()
        self.test_data_dir = Path(self.temp_dir) / "test_data"
        self.test_data_dir.mkdir(parents=True, exist_ok=True)
        
        # 测试开始时间
        self.start_time = time.time()
        
        # 测试结果收集
        self.test_results = {
            "test_name": self._testMethodName,
            "start_time": datetime.now().isoformat(),
            "assertions": [],
            "performance_metrics": {},
            "errors": [],
            "warnings": []
        }
        
        logger.info(f"开始集成测试: {self._testMethodName}")
    
    def tearDown(self):
        """测试后清理"""
        # 计算测试耗时
        elapsed_time = time.time() - self.start_time
        self.test_results["elapsed_time"] = elapsed_time
        self.test_results["end_time"] = datetime.now().isoformat()
        
        # 清理临时目录
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
        logger.info(f"完成集成测试: {self._testMethodName}, 耗时: {elapsed_time:.2f}秒")
    
    def assert_module_compatibility(self, module1_result: Any, module2_result: Any, 
                                  tolerance: float = 0.01, message: str = ""):
        """断言模块兼容性"""
        try:
            if isinstance(module1_result, (int, float)) and isinstance(module2_result, (int, float)):
                diff = abs(module1_result - module2_result)
                self.assertLessEqual(diff, tolerance, 
                    f"{message} - 数值差异超出容差: {diff} > {tolerance}")
            else:
                self.assertEqual(module1_result, module2_result, 
                    f"{message} - 结果不匹配")
            
            self.test_results["assertions"].append({
                "type": "compatibility",
                "message": message or "模块兼容性检查",
                "status": "passed"
            })
        except AssertionError as e:
            self.test_results["assertions"].append({
                "type": "compatibility",
                "message": message or "模块兼容性检查",
                "status": "failed",
                "error": str(e)
            })
            raise
    
    def assert_performance_metric(self, metric_name: str, value: float, 
                                threshold: float, message: str = ""):
        """断言性能指标"""
        try:
            self.assertLessEqual(value, threshold, 
                f"{message} - 性能指标 {metric_name}: {value} 超出阈值 {threshold}")
            
            self.test_results["performance_metrics"][metric_name] = {
                "value": value,
                "threshold": threshold,
                "status": "passed"
            }
        except AssertionError as e:
            self.test_results["performance_metrics"][metric_name] = {
                "value": value,
                "threshold": threshold,
                "status": "failed",
                "error": str(e)
            }
            raise
    
    def record_test_warning(self, message: str):
        """记录测试警告"""
        self.test_results["warnings"].append({
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
        logger.warning(f"测试警告 [{self._testMethodName}]: {message}")
    
    def record_test_error(self, message: str, error: Exception = None):
        """记录测试错误"""
        error_info = {
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        if error:
            error_info["error"] = str(error)
            error_info["error_type"] = type(error).__name__
        
        self.test_results["errors"].append(error_info)
        logger.error(f"测试错误 [{self._testMethodName}]: {message}")
    
    def save_test_result(self):
        """保存测试结果"""
        result_file = self.test_data_dir / f"result_{self._testMethodName}.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)
        return result_file


class TestDataGenerator:
    """测试数据生成器"""
    
    @staticmethod
    def create_test_stock(code: str = "TEST001", name: str = "测试股票",
                         price: float = 10.0, dividend_yield: float = 5.0,
                         pe_ratio: float = 15.0, pb_ratio: float = 2.0):
        """创建测试股票数据"""
        from src.buffett.models.stock import StockInfo
        
        return StockInfo(
            code=code,
            name=name,
            price=price,
            dividend_yield=dividend_yield,
            pe_ratio=pe_ratio,
            pb_ratio=pb_ratio,
            change_pct=0.02,
            volume=1000000,
            market_cap=1000000000,
            eps=1.0,
            book_value=5.0,
            week_52_high=15.0,
            week_52_low=8.0
        )
    
    @staticmethod
    def create_test_portfolio() -> Dict[str, float]:
        """创建测试投资组合"""
        return {
            "STOCK1": 0.3,
            "STOCK2": 0.25,
            "STOCK3": 0.2,
            "STOCK4": 0.15,
            "STOCK5": 0.1
        }
    
    @staticmethod
    def create_test_price_history(symbol: str, days: int = 30, 
                                base_price: float = 10.0, 
                                volatility: float = 0.02) -> List[float]:
        """创建测试价格历史"""
        import random
        
        prices = []
        current_price = base_price
        
        for _ in range(days):
            # 模拟价格波动
            change = random.gauss(0, volatility)
            current_price = current_price * (1 + change)
            prices.append(current_price)
        
        return prices
    
    @staticmethod
    def create_test_volume_history(days: int = 30, 
                                  base_volume: int = 1000000) -> List[int]:
        """创建测试成交量历史"""
        import random
        
        volumes = []
        for _ in range(days):
            # 模拟成交量波动
            volume = int(base_volume * (1 + random.gauss(0, 0.3)))
            volumes.append(max(volume, 100000))  # 确保最小成交量
        
        return volumes


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.metrics = {}
        self.start_times = {}
    
    def start_timer(self, operation: str):
        """开始计时"""
        self.start_times[operation] = time.time()
    
    def end_timer(self, operation: str) -> float:
        """结束计时并返回耗时"""
        if operation not in self.start_times:
            raise ValueError(f"操作 {operation} 未开始计时")
        
        elapsed = time.time() - self.start_times[operation]
        self.metrics[operation] = elapsed
        del self.start_times[operation]
        
        return elapsed
    
    def get_metric(self, operation: str) -> Optional[float]:
        """获取性能指标"""
        return self.metrics.get(operation)
    
    def get_all_metrics(self) -> Dict[str, float]:
        """获取所有性能指标"""
        return self.metrics.copy()
    
    def reset(self):
        """重置所有指标"""
        self.metrics.clear()
        self.start_times.clear()


class IntegrationTestReporter:
    """集成测试报告生成器"""
    
    def __init__(self, output_dir: str = "reports/integration"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.test_results = []
    
    def add_test_result(self, result: Dict[str, Any]):
        """添加测试结果"""
        self.test_results.append(result)
    
    def generate_summary_report(self) -> str:
        """生成汇总报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.output_dir / f"integration_test_summary_{timestamp}.json"
        
        # 统计信息
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if not r.get("errors")])
        failed_tests = total_tests - passed_tests
        
        # 性能统计
        performance_stats = {}
        for result in self.test_results:
            for metric_name, metric_data in result.get("performance_metrics", {}).items():
                if metric_name not in performance_stats:
                    performance_stats[metric_name] = []
                if metric_data.get("status") == "passed":
                    performance_stats[metric_name].append(metric_data["value"])
        
        # 计算性能统计
        performance_summary = {}
        for metric_name, values in performance_stats.items():
            if values:
                performance_summary[metric_name] = {
                    "count": len(values),
                    "average": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values)
                }
        
        # 构建报告
        report_data = {
            "report_type": "integration_test_summary",
            "timestamp": datetime.now().isoformat(),
            "test_summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": passed_tests / total_tests if total_tests > 0 else 0
            },
            "performance_summary": performance_summary,
            "test_results": self.test_results
        }
        
        # 保存报告
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"集成测试汇总报告已生成: {report_file}")
        return str(report_file)
    
    def generate_detailed_report(self) -> str:
        """生成详细报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.output_dir / f"integration_test_detailed_{timestamp}.json"
        
        # 按测试类型分组
        grouped_results = {}
        for result in self.test_results:
            test_name = result.get("test_name", "unknown")
            test_type = test_name.split("_")[0] if "_" in test_name else "general"
            
            if test_type not in grouped_results:
                grouped_results[test_type] = []
            grouped_results[test_type].append(result)
        
        # 构建详细报告
        report_data = {
            "report_type": "integration_test_detailed",
            "timestamp": datetime.now().isoformat(),
            "test_groups": grouped_results,
            "all_results": self.test_results
        }
        
        # 保存报告
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"集成测试详细报告已生成: {report_file}")
        return str(report_file)


def run_integration_tests(test_classes: List[type]) -> Dict[str, Any]:
    """运行集成测试套件"""
    # 创建测试套件
    suite = unittest.TestSuite()
    
    # 添加测试类
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 返回测试结果
    return {
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "success_rate": (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun if result.testsRun > 0 else 0,
        "failure_details": [{"test": str(f[0]), "error": f[1]} for f in result.failures],
        "error_details": [{"test": str(e[0]), "error": e[1]} for e in result.errors]
    }