"""
性能和兼容性集成测试
验证系统的性能指标和向后兼容性
"""

import sys
import os
import unittest
import time
import gc
import psutil
from pathlib import Path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from tests.integration.test_framework import IntegrationTestBase, TestDataGenerator, PerformanceMonitor
from src.buffett.core.multi_factor_scoring import MultiFactorScorer
from src.buffett.core.scoring import InvestmentScorer
from src.buffett.strategies.technical_analysis import TechnicalSignalGenerator
from src.buffett.core.market_environment import MarketEnvironmentIdentifier
from src.buffett.core.risk_management import RiskManager, RiskConfig
from src.buffett.models.stock import StockInfo


class TestPerformanceCompatibility(IntegrationTestBase):
    """性能和兼容性集成测试"""
    
    def setUp(self):
        """测试前准备"""
        super().setUp()
        
        # 性能监控器
        self.performance_monitor = PerformanceMonitor()
        
        # 记录初始内存使用
        self.initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        # 创建测试数据
        self.small_dataset = self._create_test_dataset(10)
        self.medium_dataset = self._create_test_dataset(100)
        self.large_dataset = self._create_test_dataset(1000)
        
        # 创建系统组件
        self.multi_factor_scorer = MultiFactorScorer.with_default_factors()
        self.legacy_scorer = InvestmentScorer()
        self.signal_generator = TechnicalSignalGenerator()
        self.environment_identifier = MarketEnvironmentIdentifier()
        self.risk_manager = RiskManager(RiskConfig())
    
    def _create_test_dataset(self, size: int) -> list:
        """创建指定大小的测试数据集"""
        dataset = []
        for i in range(size):
            stock = TestDataGenerator.create_test_stock(
                f"STOCK{i:04d}", f"测试股票{i}",
                price=10.0 + i * 0.01,
                dividend_yield=5.0 + (i % 10) * 0.1,
                pe_ratio=15.0 + (i % 20) * 0.1,
                pb_ratio=2.0 + (i % 10) * 0.1
            )
            dataset.append(stock)
        return dataset
    
    def test_backward_compatibility(self):
        """测试向后兼容性"""
        print("\n=== 测试向后兼容性 ===")
        
        # 测试数据：小数据集
        test_stocks = self.small_dataset
        
        print(f"测试数据集大小: {len(test_stocks)}")
        
        # 兼容性测试1：评分结果格式兼容性
        print("\n1. 评分结果格式兼容性测试")
        
        compatibility_errors = []
        
        for stock in test_stocks:
            # 新系统评分
            new_score = self.multi_factor_scorer.calculate_score(stock)
            
            # 旧系统评分
            legacy_score = self.legacy_scorer.calculate_total_score(stock) / 100
            
            # 验证评分范围
            if not (0 <= new_score <= 1):
                compatibility_errors.append(f"新系统评分超出范围: {stock.code} = {new_score}")
            
            if not (0 <= legacy_score <= 1):
                compatibility_errors.append(f"旧系统评分超出范围: {stock.code} = {legacy_score}")
            
            # 验证评分趋势一致性（允许一定差异）
            score_diff = abs(new_score - legacy_score)
            if score_diff > 0.4:
                compatibility_errors.append(f"评分差异过大: {stock.code}, 新={new_score:.3f}, 旧={legacy_score:.3f}, 差异={score_diff:.3f}")
        
        # 兼容性测试2：排序结果兼容性
        print("\n2. 排序结果兼容性测试")
        
        # 新系统排序
        new_ranked = self.multi_factor_scorer.rank_stocks(test_stocks.copy())
        
        # 旧系统排序
        legacy_ranked = self.legacy_scorer.rank_stocks(test_stocks.copy())
        
        # 验证排序结果数量
        if len(new_ranked) != len(legacy_ranked):
            compatibility_errors.append(f"排序结果数量不匹配: 新={len(new_ranked)}, 旧={len(legacy_ranked)}")
        
        # 验证排序方向（都应该是降序）
        for i in range(len(new_ranked) - 1):
            if new_ranked[i].total_score < new_ranked[i+1].total_score:
                compatibility_errors.append(f"新系统排序不是降序: 位置{i}")
        
        for i in range(len(legacy_ranked) - 1):
            if legacy_ranked[i].total_score < legacy_ranked[i+1].total_score:
                compatibility_errors.append(f"旧系统排序不是降序: 位置{i}")
        
        # 兼容性测试3：数据结构兼容性
        print("\n3. 数据结构兼容性测试")
        
        for stock in test_stocks:
            # 验证StockInfo数据结构
            required_fields = ['code', 'name', 'price', 'dividend_yield', 'pe_ratio', 'pb_ratio', 
                           'change_pct', 'volume', 'market_cap', 'eps', 'book_value', 
                           'week_52_high', 'week_52_low', 'total_score']
            
            for field in required_fields:
                if not hasattr(stock, field):
                    compatibility_errors.append(f"StockInfo缺少字段: {field}")
                    break
        
        # 显示兼容性测试结果
        print(f"\n兼容性测试结果:")
        print(f"  测试股票数量: {len(test_stocks)}")
        print(f"  兼容性错误数量: {len(compatibility_errors)}")
        
        if compatibility_errors:
            print("\n兼容性错误详情:")
            for error in compatibility_errors:
                print(f"  - {error}")
        
        # 验证兼容性
        self.assertLessEqual(len(compatibility_errors), len(test_stocks) * 0.1, 
                           "兼容性错误数量应少于10%")
        
        # 记录兼容性测试结果
        self.test_results["compatibility_test"] = {
            "dataset_size": len(test_stocks),
            "error_count": len(compatibility_errors),
            "error_rate": len(compatibility_errors) / len(test_stocks),
            "errors": compatibility_errors[:5]  # 只记录前5个错误
        }
    
    def test_performance_scalability(self):
        """测试性能可扩展性"""
        print("\n=== 测试性能可扩展性 ===")
        
        # 测试不同数据量下的性能
        datasets = [
            ("小数据集", self.small_dataset),
            ("中数据集", self.medium_dataset),
            ("大数据集", self.large_dataset)
        ]
        
        performance_results = {}
        
        for dataset_name, dataset in datasets:
            print(f"\n{dataset_name}性能测试 ({len(dataset)}只股票):")
            
            # 多因子评分性能
            self.performance_monitor.start_timer(f"scoring_{dataset_name}")
            ranked_stocks = self.multi_factor_scorer.rank_stocks(dataset.copy())
            scoring_time = self.performance_monitor.end_timer(f"scoring_{dataset_name}")
            
            # 技术分析性能（只测试前10只）
            tech_dataset = dataset[:10]
            self.performance_monitor.start_timer(f"technical_{dataset_name}")
            tech_results = []
            for stock in tech_dataset:
                prices = TestDataGenerator.create_test_price_history(stock.code, days=30)
                volumes = TestDataGenerator.create_test_volume_history(days=30)
                signals = self.signal_generator.generate_signals(prices, volumes)
                tech_results.append(signals)
            technical_time = self.performance_monitor.end_timer(f"technical_{dataset_name}")
            
            # 风险评估性能
            portfolio = {stock.code: 1.0 / len(tech_dataset) for stock in tech_dataset}
            self.performance_monitor.start_timer(f"risk_{dataset_name}")
            self.risk_manager.update_portfolio_data(tech_dataset, portfolio)
            risk_metrics, risk_alerts = self.risk_manager.assess_portfolio_risk()
            risk_time = self.performance_monitor.end_timer(f"risk_{dataset_name}")
            
            # 内存使用
            current_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            memory_usage = current_memory - self.initial_memory
            
            # 记录性能结果
            performance_results[dataset_name] = {
                "dataset_size": len(dataset),
                "scoring_time": scoring_time,
                "technical_time": technical_time,
                "risk_time": risk_time,
                "total_time": scoring_time + technical_time + risk_time,
                "memory_usage": memory_usage,
                "scoring_throughput": len(dataset) / scoring_time if scoring_time > 0 else 0,
                "technical_throughput": len(tech_dataset) / technical_time if technical_time > 0 else 0
            }
            
            print(f"  多因子评分: {scoring_time:.4f}秒 ({len(dataset) / scoring_time:.0f}股/秒)")
            print(f"  技术分析: {technical_time:.4f}秒 ({len(tech_dataset) / technical_time:.0f}股/秒)")
            print(f"  风险评估: {risk_time:.4f}秒")
            print(f"  总耗时: {scoring_time + technical_time + risk_time:.4f}秒")
            print(f"  内存使用: {memory_usage:.2f}MB")
            
            # 验证性能结果
            self.assertGreater(len(ranked_stocks), 0, f"{dataset_name}评分结果不应为空")
            self.assertEqual(len(ranked_stocks), len(dataset), f"{dataset_name}评分结果数量应匹配")
            self.assertEqual(len(tech_results), len(tech_dataset), f"{dataset_name}技术分析结果数量应匹配")
            self.assertIsNotNone(risk_metrics, f"{dataset_name}风险评估结果不应为None")
            
            # 清理内存
            del ranked_stocks, tech_results, risk_metrics, risk_alerts
            gc.collect()
        
        # 验证性能扩展性
        print(f"\n性能扩展性分析:")
        
        # 评分性能分析
        small_scoring = performance_results["小数据集"]["scoring_throughput"]
        medium_scoring = performance_results["中数据集"]["scoring_throughput"]
        large_scoring = performance_results["大数据集"]["scoring_throughput"]
        
        print(f"  评分吞吐量: 小={small_scoring:.0f}股/秒, 中={medium_scoring:.0f}股/秒, 大={large_scoring:.0f}股/秒")
        
        # 验证性能不应大幅下降
        if large_scoring > 0:
            performance_degradation = (small_scoring - large_scoring) / small_scoring
            self.assertLessEqual(performance_degradation, 0.5, "大数据量性能下降不应超过50%")
        
        # 内存使用分析
        small_memory = performance_results["小数据集"]["memory_usage"]
        medium_memory = performance_results["中数据集"]["memory_usage"]
        large_memory = performance_results["大数据集"]["memory_usage"]
        
        print(f"  内存使用: 小={small_memory:.2f}MB, 中={medium_memory:.2f}MB, 大={large_memory:.2f}MB")
        
        # 验证内存使用合理性
        self.assertLess(large_memory, 500, "大数据集内存使用不应超过500MB")
        
        # 记录性能测试结果
        self.test_results["performance_scalability"] = performance_results
    
    def test_concurrent_processing(self):
        """测试并发处理能力"""
        print("\n=== 测试并发处理能力 ===")
        
        import threading
        import queue
        
        # 创建任务队列
        task_queue = queue.Queue()
        result_queue = queue.Queue()
        
        # 测试数据
        test_stocks = self.medium_dataset[:50]  # 50只股票
        batch_size = 10
        num_batches = len(test_stocks) // batch_size
        
        # 工作函数
        def worker(batch_id, stocks):
            """处理一批股票的worker函数"""
            try:
                start_time = time.time()
                
                # 多因子评分
                ranked_stocks = self.multi_factor_scorer.rank_stocks(stocks)
                
                # 技术分析
                tech_results = []
                for stock in stocks[:5]:  # 每批只分析前5只
                    prices = TestDataGenerator.create_test_price_history(stock.code, days=20)
                    volumes = TestDataGenerator.create_test_volume_history(days=20)
                    signals = self.signal_generator.generate_signals(prices, volumes)
                    tech_results.append(signals)
                
                end_time = time.time()
                processing_time = end_time - start_time
                
                result_queue.put({
                    'batch_id': batch_id,
                    'stocks_processed': len(stocks),
                    'processing_time': processing_time,
                    'success': True,
                    'ranked_count': len(ranked_stocks),
                    'tech_count': len(tech_results)
                })
                
            except Exception as e:
                result_queue.put({
                    'batch_id': batch_id,
                    'success': False,
                    'error': str(e)
                })
        
        # 分批处理
        self.performance_monitor.start_timer("concurrent_processing")
        
        threads = []
        for i in range(num_batches):
            start_idx = i * batch_size
            end_idx = start_idx + batch_size
            batch_stocks = test_stocks[start_idx:end_idx]
            
            thread = threading.Thread(target=worker, args=(i, batch_stocks))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        self.performance_monitor.end_timer("concurrent_processing")
        
        # 收集结果
        results = []
        while not result_queue.empty():
            results.append(result_queue.get())
        
        # 分析并发处理结果
        print(f"\n并发处理结果:")
        print(f"  总批次数: {num_batches}")
        print(f"  成功批次数: {len([r for r in results if r['success']])}")
        print(f"  失败批次数: {len([r for r in results if not r['success']])}")
        
        successful_results = [r for r in results if r['success']]
        
        if successful_results:
            total_processed = sum(r['stocks_processed'] for r in successful_results)
            total_time = sum(r['processing_time'] for r in successful_results)
            avg_time = total_time / len(successful_results)
            
            print(f"  总处理股票数: {total_processed}")
            print(f"  平均处理时间: {avg_time:.4f}秒")
            print(f"  并发吞吐量: {total_processed / total_time:.0f}股/秒")
            
            # 验证并发处理结果
            self.assertEqual(len(successful_results), num_batches, "所有批次都应成功")
            self.assertEqual(total_processed, len(test_stocks), "处理股票数量应匹配")
            
            # 验证每批的结果
            for result in successful_results:
                self.assertEqual(result['ranked_count'], batch_size, "每批排序结果数量应匹配")
                self.assertEqual(result['tech_count'], 5, "每批技术分析结果数量应匹配")
        
        # 性能检查
        concurrent_time = self.performance_monitor.get_metric("concurrent_processing")
        self.assert_performance_metric("concurrent_processing", concurrent_time, 5.0, "并发处理性能")
        
        # 记录并发测试结果
        self.test_results["concurrent_processing"] = {
            "total_batches": num_batches,
            "successful_batches": len(successful_results),
            "total_stocks": len(test_stocks),
            "processing_time": concurrent_time,
            "throughput": len(test_stocks) / concurrent_time if concurrent_time > 0 else 0
        }
    
    def test_memory_efficiency(self):
        """测试内存效率"""
        print("\n=== 测试内存效率 ===")
        
        # 记录初始内存
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        # 内存压力测试
        memory_test_results = []
        
        for size in [100, 500, 1000]:
            print(f"\n内存效率测试 - {size}只股票:")
            
            # 创建测试数据
            test_stocks = self._create_test_dataset(size)
            
            # 记录处理前内存
            before_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            
            # 处理数据
            ranked_stocks = self.multi_factor_scorer.rank_stocks(test_stocks)
            
            # 技术分析（只处理前20只）
            tech_stocks = test_stocks[:20]
            for stock in tech_stocks:
                prices = TestDataGenerator.create_test_price_history(stock.code, days=30)
                volumes = TestDataGenerator.create_test_volume_history(days=30)
                signals = self.signal_generator.generate_signals(prices, volumes)
            
            # 记录处理后内存
            after_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            
            # 计算内存使用
            memory_used = after_memory - before_memory
            memory_per_stock = memory_used / size
            
            print(f"  处理前内存: {before_memory:.2f}MB")
            print(f"  处理后内存: {after_memory:.2f}MB")
            print(f"  内存增长: {memory_used:.2f}MB")
            print(f"  每只股票内存: {memory_per_stock:.4f}MB")
            
            # 验证内存效率
            self.assertLess(memory_per_stock, 1.0, f"每只股票内存使用应小于1MB: {size}只股票")
            self.assertLess(memory_used, 200, f"总内存使用应小于200MB: {size}只股票")
            
            memory_test_results.append({
                "stock_count": size,
                "memory_used": memory_used,
                "memory_per_stock": memory_per_stock
            })
            
            # 清理内存
            del ranked_stocks, test_stocks, tech_stocks
            gc.collect()
        
        # 内存效率分析
        print(f"\n内存效率分析:")
        for result in memory_test_results:
            print(f"  {result['stock_count']}只股票: {result['memory_per_stock']:.4f}MB/股")
        
        # 验证内存扩展性
        large_memory_per_stock = memory_test_results[-1]["memory_per_stock"]
        small_memory_per_stock = memory_test_results[0]["memory_per_stock"]
        
        memory_growth = (large_memory_per_stock - small_memory_per_stock) / small_memory_per_stock
        self.assertLessEqual(memory_growth, 0.5, "大数据量时每只股票内存增长不应超过50%")
        
        # 记录内存测试结果
        self.test_results["memory_efficiency"] = memory_test_results
    
    def test_system_stress(self):
        """测试系统压力"""
        print("\n=== 测试系统压力 ===")
        
        # 压力测试参数
        stress_iterations = 10
        stocks_per_iteration = 100
        
        stress_results = []
        
        for iteration in range(stress_iterations):
            print(f"\n压力测试 - 迭代 {iteration + 1}/{stress_iterations}:")
            
            # 创建测试数据
            test_stocks = self._create_test_dataset(stocks_per_iteration)
            
            # 记录开始时间和内存
            start_time = time.time()
            start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            
            # 执行完整工作流程
            # 1. 多因子评分
            ranked_stocks = self.multi_factor_scorer.rank_stocks(test_stocks)
            
            # 2. 技术分析（前20只）
            for stock in ranked_stocks[:20]:
                prices = TestDataGenerator.create_test_price_history(stock.code, days=30)
                volumes = TestDataGenerator.create_test_volume_history(days=30)
                signals = self.signal_generator.generate_signals(prices, volumes)
            
            # 3. 风险评估
            portfolio = {stock.code: 0.05 for stock in ranked_stocks[:20]}
            self.risk_manager.update_portfolio_data(ranked_stocks[:20], portfolio)
            risk_metrics, risk_alerts = self.risk_manager.assess_portfolio_risk()
            
            # 记录结束时间和内存
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            
            # 计算性能指标
            processing_time = end_time - start_time
            memory_used = end_memory - start_memory
            throughput = stocks_per_iteration / processing_time
            
            print(f"  处理时间: {processing_time:.4f}秒")
            print(f"  内存使用: {memory_used:.2f}MB")
            print(f"  吞吐量: {throughput:.0f}股/秒")
            print(f"  风险预警: {len(risk_alerts)}个")
            
            # 验证压力测试结果
            self.assertGreater(len(ranked_stocks), 0, f"迭代{iteration+1}评分结果不应为空")
            self.assertIsNotNone(risk_metrics, f"迭代{iteration+1}风险指标不应为None")
            
            stress_results.append({
                "iteration": iteration + 1,
                "processing_time": processing_time,
                "memory_used": memory_used,
                "throughput": throughput,
                "risk_alerts": len(risk_alerts)
            })
            
            # 清理内存
            del ranked_stocks, test_stocks, portfolio, risk_metrics, risk_alerts
            gc.collect()
        
        # 压力测试分析
        print(f"\n压力测试分析:")
        
        avg_processing_time = sum(r["processing_time"] for r in stress_results) / len(stress_results)
        avg_memory_used = sum(r["memory_used"] for r in stress_results) / len(stress_results)
        avg_throughput = sum(r["throughput"] for r in stress_results) / len(stress_results)
        max_processing_time = max(r["processing_time"] for r in stress_results)
        min_throughput = min(r["throughput"] for r in stress_results)
        
        print(f"  平均处理时间: {avg_processing_time:.4f}秒")
        print(f"  最大处理时间: {max_processing_time:.4f}秒")
        print(f"  平均内存使用: {avg_memory_used:.2f}MB")
        print(f"  平均吞吐量: {avg_throughput:.0f}股/秒")
        print(f"  最低吞吐量: {min_throughput:.0f}股/秒")
        
        # 验证系统稳定性
        performance_variance = (max_processing_time - avg_processing_time) / avg_processing_time
        self.assertLessEqual(performance_variance, 0.5, "处理时间方差不应超过50%")
        
        # 验证最低性能要求
        self.assertGreater(min_throughput, 50, "最低吞吐量应大于50股/秒")
        
        # 记录压力测试结果
        self.test_results["system_stress"] = {
            "iterations": stress_iterations,
            "stocks_per_iteration": stocks_per_iteration,
            "avg_processing_time": avg_processing_time,
            "max_processing_time": max_processing_time,
            "avg_memory_used": avg_memory_used,
            "avg_throughput": avg_throughput,
            "min_throughput": min_throughput,
            "performance_variance": performance_variance
        }
    
    def tearDown(self):
        """测试后清理"""
        # 记录最终内存使用
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        memory_growth = final_memory - self.initial_memory
        
        print(f"\n内存使用统计:")
        print(f"  初始内存: {self.initial_memory:.2f}MB")
        print(f"  最终内存: {final_memory:.2f}MB")
        print(f"  内存增长: {memory_growth:.2f}MB")
        
        # 保存测试结果
        result_file = self.save_test_result()
        print(f"\n测试结果已保存到: {result_file}")
        
        super().tearDown()


if __name__ == '__main__':
    unittest.main()