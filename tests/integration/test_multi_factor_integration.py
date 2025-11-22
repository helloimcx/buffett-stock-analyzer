"""
多因子评分系统集成测试
验证多因子评分系统与现有系统的兼容性和集成功能
"""

import sys
import os
import unittest
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from tests.integration.test_framework import IntegrationTestBase, TestDataGenerator, PerformanceMonitor
from src.buffett.core.multi_factor_scoring import (
    MultiFactorScorer, ValueFactor, GrowthFactor, QualityFactor, 
    MomentumFactor, DividendFactor, TechnicalFactor, SentimentFactor,
    MultiFactorConfig, FactorRegistry
)
from src.buffett.core.scoring import InvestmentScorer
from src.buffett.models.stock import StockInfo


class TestMultiFactorIntegration(IntegrationTestBase):
    """多因子评分系统集成测试"""
    
    def setUp(self):
        """测试前准备"""
        super().setUp()
        
        # 创建测试股票数据
        self.test_stocks = [
            TestDataGenerator.create_test_stock("STOCK1", "股票1", 10.0, 6.0, 12.0, 1.5),
            TestDataGenerator.create_test_stock("STOCK2", "股票2", 15.0, 4.0, 18.0, 2.0),
            TestDataGenerator.create_test_stock("STOCK3", "股票3", 8.0, 8.0, 8.0, 0.8),
            TestDataGenerator.create_test_stock("STOCK4", "股票4", 20.0, 2.0, 25.0, 3.0),
            TestDataGenerator.create_test_stock("STOCK5", "股票5", 12.0, 5.0, 14.0, 1.8)
        ]
        
        # 创建评分器
        self.multi_factor_scorer = MultiFactorScorer.with_default_factors()
        self.legacy_scorer = InvestmentScorer()
        
        # 性能监控器
        self.performance_monitor = PerformanceMonitor()
    
    def test_multi_factor_vs_legacy_compatibility(self):
        """测试多因子评分系统与旧系统的兼容性"""
        print("\n=== 测试多因子评分系统与旧系统的兼容性 ===")
        
        # 对每只股票进行评分
        for stock in self.test_stocks:
            # 多因子评分
            self.performance_monitor.start_timer("multi_factor_scoring")
            multi_factor_score = self.multi_factor_scorer.calculate_score(stock)
            self.performance_monitor.end_timer("multi_factor_scoring")
            
            # 旧系统评分
            self.performance_monitor.start_timer("legacy_scoring")
            legacy_score = self.legacy_scorer.calculate_total_score(stock) / 100  # 转换为0-1范围
            self.performance_monitor.end_timer("legacy_scoring")
            
            print(f"股票 {stock.code}: 多因子评分={multi_factor_score:.3f}, 旧系统评分={legacy_score:.3f}")
            
            # 验证评分范围
            self.assertGreaterEqual(multi_factor_score, 0.0, f"多因子评分不应小于0: {stock.code}")
            self.assertLessEqual(multi_factor_score, 1.0, f"多因子评分不应大于1: {stock.code}")
            
            # 验证评分趋势一致性（允许一定差异）
            score_diff = abs(multi_factor_score - legacy_score)
            self.assertLessEqual(score_diff, 0.3, f"评分差异过大: {stock.code}, 差异={score_diff}")
        
        # 性能检查
        multi_factor_time = self.performance_monitor.get_metric("multi_factor_scoring")
        legacy_time = self.performance_monitor.get_metric("legacy_scoring")
        
        print(f"多因子评分平均耗时: {multi_factor_time:.4f}秒")
        print(f"旧系统评分平均耗时: {legacy_time:.4f}秒")
        
        # 性能应该在合理范围内
        self.assert_performance_metric("multi_factor_scoring", multi_factor_time, 0.01, "多因子评分性能")
    
    def test_factor_combination_strategies(self):
        """测试不同因子组合策略"""
        print("\n=== 测试不同因子组合策略 ===")
        
        # 创建不同配置的评分器
        conservative_scorer = MultiFactorScorer.with_custom_weights({
            "dividend": 0.4,
            "value": 0.3,
            "quality": 0.2,
            "technical": 0.1
        })
        
        aggressive_scorer = MultiFactorScorer.with_custom_weights({
            "growth": 0.4,
            "momentum": 0.3,
            "sentiment": 0.2,
            "value": 0.1
        })
        
        balanced_scorer = MultiFactorScorer.with_default_factors()
        
        # 对测试股票进行评分
        for stock in self.test_stocks:
            conservative_score = conservative_scorer.calculate_score(stock)
            aggressive_score = aggressive_scorer.calculate_score(stock)
            balanced_score = balanced_scorer.calculate_score(stock)
            
            print(f"股票 {stock.code}:")
            print(f"  保守策略评分: {conservative_score:.3f}")
            print(f"  激进策略评分: {aggressive_score:.3f}")
            print(f"  平衡策略评分: {balanced_score:.3f}")
            
            # 验证评分范围
            for score, strategy in [(conservative_score, "保守"), (aggressive_score, "激进"), (balanced_score, "平衡")]:
                self.assertGreaterEqual(score, 0.0, f"{strategy}策略评分不应小于0: {stock.code}")
                self.assertLessEqual(score, 1.0, f"{strategy}策略评分不应大于1: {stock.code}")
            
            # 验证策略差异
            score_diff = max(conservative_score, aggressive_score, balanced_score) - min(conservative_score, aggressive_score, balanced_score)
            self.assertGreater(score_diff, 0.01, f"不同策略应有显著差异: {stock.code}")
    
    def test_factor_registry_and_dynamic_loading(self):
        """测试因子注册表和动态加载"""
        print("\n=== 测试因子注册表和动态加载 ===")
        
        # 获取所有可用因子
        available_factors = FactorRegistry.get_available_factors()
        expected_factors = ["value", "growth", "quality", "momentum", "dividend", "technical", "sentiment"]
        
        print(f"可用因子: {available_factors}")
        
        # 验证所有预期因子都已注册
        for factor_name in expected_factors:
            self.assertIn(factor_name, available_factors, f"因子 {factor_name} 未注册")
        
        # 测试动态创建因子
        for factor_name in expected_factors:
            factor = FactorRegistry.create_factor(factor_name, weight=0.5)
            self.assertIsNotNone(factor, f"无法创建因子: {factor_name}")
            self.assertEqual(factor.weight, 0.5, f"因子权重设置错误: {factor_name}")
        
        # 测试创建评分器
        dynamic_scorer = MultiFactorScorer()
        for factor_name in expected_factors:
            factor = FactorRegistry.create_factor(factor_name, weight=0.1)
            dynamic_scorer.add_factor(factor)
        
        # 验证动态创建的评分器
        for stock in self.test_stocks:
            score = dynamic_scorer.calculate_score(stock)
            self.assertGreaterEqual(score, 0.0, f"动态评分器评分不应小于0: {stock.code}")
            self.assertLessEqual(score, 1.0, f"动态评分器评分不应大于1: {stock.code}")
    
    def test_multi_factor_ranking_consistency(self):
        """测试多因子排序一致性"""
        print("\n=== 测试多因子排序一致性 ===")
        
        # 使用多因子评分器排序
        self.performance_monitor.start_timer("multi_factor_ranking")
        multi_factor_ranked = self.multi_factor_scorer.rank_stocks(self.test_stocks.copy())
        self.performance_monitor.end_timer("multi_factor_ranking")
        
        # 使用旧系统排序
        self.performance_monitor.start_timer("legacy_ranking")
        legacy_ranked = self.legacy_scorer.rank_stocks(self.test_stocks.copy())
        self.performance_monitor.end_timer("legacy_ranking")
        
        print("多因子排序结果:")
        for i, stock in enumerate(multi_factor_ranked):
            print(f"  {i+1}. {stock.code}: {stock.total_score:.2f}")
        
        print("\n旧系统排序结果:")
        for i, stock in enumerate(legacy_ranked):
            print(f"  {i+1}. {stock.code}: {stock.total_score:.2f}")
        
        # 验证排序结果不为空
        self.assertEqual(len(multi_factor_ranked), len(self.test_stocks), "多因子排序结果数量不正确")
        self.assertEqual(len(legacy_ranked), len(self.test_stocks), "旧系统排序结果数量不正确")
        
        # 验证排序是降序的
        for i in range(len(multi_factor_ranked) - 1):
            self.assertGreaterEqual(
                multi_factor_ranked[i].total_score, multi_factor_ranked[i+1].total_score,
                "多因子排序不是降序的"
            )
        
        for i in range(len(legacy_ranked) - 1):
            self.assertGreaterEqual(
                legacy_ranked[i].total_score, legacy_ranked[i+1].total_score,
                "旧系统排序不是降序的"
            )
        
        # 性能检查
        multi_factor_ranking_time = self.performance_monitor.get_metric("multi_factor_ranking")
        legacy_ranking_time = self.performance_monitor.get_metric("legacy_ranking")
        
        print(f"\n多因子排序耗时: {multi_factor_ranking_time:.4f}秒")
        print(f"旧系统排序耗时: {legacy_ranking_time:.4f}秒")
        
        self.assert_performance_metric("multi_factor_ranking", multi_factor_ranking_time, 0.01, "多因子排序性能")
    
    def test_factor_performance_tracking(self):
        """测试因子性能跟踪"""
        print("\n=== 测试因子性能跟踪 ===")
        
        from src.buffett.core.multi_factor_scoring import FactorPerformanceTracker
        
        # 创建性能跟踪器
        tracker = FactorPerformanceTracker()
        
        # 模拟因子性能数据
        test_data = [
            ("value", 0.8, 0.05),
            ("growth", 0.6, 0.08),
            ("dividend", 0.7, 0.03),
            ("technical", 0.5, 0.12),
            ("value", 0.9, 0.06),
            ("growth", 0.4, -0.02),
            ("dividend", 0.8, 0.04)
        ]
        
        # 记录性能数据
        for factor_name, score, return_rate in test_data:
            tracker.record_factor_performance(factor_name, score, return_rate)
        
        # 获取因子统计
        for factor_name in ["value", "growth", "dividend", "technical"]:
            stats = tracker.get_factor_stats(factor_name)
            print(f"因子 {factor_name}:")
            print(f"  记录次数: {stats['count']}")
            print(f"  平均评分: {stats['avg_score']:.3f}")
            print(f"  平均收益: {stats['avg_return']:.3f}")
            
            # 验证统计数据的合理性
            self.assertGreaterEqual(stats['count'], 0, f"因子 {factor_name} 应有记录")
            self.assertGreaterEqual(stats['avg_score'], 0.0, f"因子 {factor_name} 平均评分应非负")
        
        # 获取最佳因子
        best_factor = tracker.get_best_factor()
        print(f"\n最佳因子: {best_factor}")
        
        # 验证最佳因子
        self.assertIsNotNone(best_factor, "应能找到最佳因子")
        self.assertIn(best_factor, ["value", "growth", "dividend", "technical"], "最佳因子应在预期范围内")
    
    def test_config_driven_scoring(self):
        """测试配置驱动的评分"""
        print("\n=== 测试配置驱动的评分 ===")
        
        # 创建测试配置
        config_dict = {
            "value": {"weight": 0.25, "enabled": True},
            "growth": {"weight": 0.20, "enabled": True},
            "quality": {"weight": 0.15, "enabled": True},
            "momentum": {"weight": 0.10, "enabled": True},
            "dividend": {"weight": 0.20, "enabled": True},
            "technical": {"weight": 0.10, "enabled": True},
            "sentiment": {"weight": 0.0, "enabled": False}  # 禁用情绪因子
        }
        
        # 从配置创建评分器
        config = MultiFactorConfig.from_dict(config_dict)
        config_scorer = MultiFactorScorer.from_config(config)
        
        # 对测试股票进行评分
        for stock in self.test_stocks:
            config_score = config_scorer.calculate_score(stock)
            default_score = self.multi_factor_scorer.calculate_score(stock)
            
            print(f"股票 {stock.code}:")
            print(f"  配置评分器: {config_score:.3f}")
            print(f"  默认评分器: {default_score:.3f}")
            print(f"  评分差异: {abs(config_score - default_score):.3f}")
            
            # 验证评分范围
            self.assertGreaterEqual(config_score, 0.0, f"配置评分器评分不应小于0: {stock.code}")
            self.assertLessEqual(config_score, 1.0, f"配置评分器评分不应大于1: {stock.code}")
            
            # 由于禁用了情绪因子，评分应该有差异
            score_diff = abs(config_score - default_score)
            self.assertGreater(score_diff, 0.0, f"禁用因子后评分应有差异: {stock.code}")
    
    def tearDown(self):
        """测试后清理"""
        # 保存测试结果
        result_file = self.save_test_result()
        print(f"\n测试结果已保存到: {result_file}")
        
        super().tearDown()


if __name__ == '__main__':
    unittest.main()