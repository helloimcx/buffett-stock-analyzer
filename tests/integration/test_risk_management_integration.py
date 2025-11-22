"""
风险控制集成测试
验证风险管理系统与评分系统和监控系统的集成功能
"""

import sys
import os
import unittest
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from tests.integration.test_framework import IntegrationTestBase, TestDataGenerator, PerformanceMonitor
from src.buffett.core.risk_management import (
    RiskManager, RiskConfig, RiskStrategy, VaRMethod, RiskType, RiskLevel,
    RiskIndicatorCalculator, RiskMonitor, DynamicStopLoss, RiskReportGenerator
)
from src.buffett.core.multi_factor_scoring import MultiFactorScorer
from src.buffett.core.scoring import InvestmentScorer
from src.buffett.models.stock import StockInfo


class TestRiskManagementIntegration(IntegrationTestBase):
    """风险控制集成测试"""
    
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
        
        # 创建测试投资组合
        self.test_portfolio = TestDataGenerator.create_test_portfolio()
        
        # 创建风险管理器
        self.risk_config = RiskConfig()
        self.risk_manager = RiskManager(self.risk_config)
        
        # 创建评分器
        self.multi_factor_scorer = MultiFactorScorer.with_default_factors()
        self.legacy_scorer = InvestmentScorer()
        
        # 性能监控器
        self.performance_monitor = PerformanceMonitor()
        
        # 创建价格和成交量历史数据
        self.price_histories = {}
        self.volume_histories = {}
        
        for stock in self.test_stocks:
            self.price_histories[stock.code] = TestDataGenerator.create_test_price_history(
                stock.code, days=60, base_price=stock.price
            )
            self.volume_histories[stock.code] = TestDataGenerator.create_test_volume_history(days=60)
    
    def test_risk_indicator_calculation(self):
        """测试风险指标计算"""
        print("\n=== 测试风险指标计算 ===")
        
        # 创建风险指标计算器
        calculator = RiskIndicatorCalculator(self.risk_config)
        
        # 测试VaR计算
        returns = [0.01, -0.02, 0.015, -0.01, 0.005, 0.02, -0.015, 0.01, -0.005, 0.008]
        
        self.performance_monitor.start_timer("var_calculation")
        var_95 = calculator.calculate_var(returns, 0.95)
        var_99 = calculator.calculate_var(returns, 0.99)
        self.performance_monitor.end_timer("var_calculation")
        
        print(f"VaR(95%): {var_95:.4f}")
        print(f"VaR(99%): {var_99:.4f}")
        
        # 验证VaR计算结果
        self.assertLessEqual(var_95, 0, "VaR(95%)应小于等于0")
        self.assertLessEqual(var_99, 0, "VaR(99%)应小于等于0")
        self.assertLessEqual(var_99, var_95, "VaR(99%)应小于等于VaR(95%)")
        
        # 测试最大回撤计算
        prices = [100, 105, 95, 110, 90, 115, 85, 120, 80, 125]
        
        self.performance_monitor.start_timer("max_drawdown_calculation")
        max_dd = calculator.calculate_max_drawdown(prices)
        self.performance_monitor.end_timer("max_drawdown_calculation")
        
        print(f"最大回撤: {max_dd:.4f}")
        
        # 验证最大回撤计算结果
        self.assertGreaterEqual(max_dd, 0, "最大回撤应大于等于0")
        self.assertLessEqual(max_dd, 1, "最大回撤应小于等于1")
        
        # 测试波动率计算
        self.performance_monitor.start_timer("volatility_calculation")
        volatility = calculator.calculate_volatility(returns)
        self.performance_monitor.end_timer("volatility_calculation")
        
        print(f"波动率: {volatility:.4f}")
        
        # 验证波动率计算结果
        self.assertGreaterEqual(volatility, 0, "波动率应大于等于0")
        
        # 测试夏普比率计算
        self.performance_monitor.start_timer("sharpe_calculation")
        sharpe_ratio = calculator.calculate_sharpe_ratio(returns)
        self.performance_monitor.end_timer("sharpe_calculation")
        
        print(f"夏普比率: {sharpe_ratio:.4f}")
        
        # 验证夏普比率计算结果
        self.assertIsInstance(sharpe_ratio, float, "夏普比率应为浮点数")
        
        # 测试集中度风险计算
        self.performance_monitor.start_timer("concentration_calculation")
        concentration = calculator.calculate_concentration_risk(self.test_portfolio)
        self.performance_monitor.end_timer("concentration_calculation")
        
        print(f"集中度风险: {concentration:.4f}")
        
        # 验证集中度风险计算结果
        self.assertGreaterEqual(concentration, 0, "集中度风险应大于等于0")
        self.assertLessEqual(concentration, 1, "集中度风险应小于等于1")
    
    def test_portfolio_risk_assessment(self):
        """测试投资组合风险评估"""
        print("\n=== 测试投资组合风险评估 ===")
        
        # 更新投资组合数据
        self.risk_manager.update_portfolio_data(self.test_stocks, self.test_portfolio)
        
        # 评估投资组合风险
        self.performance_monitor.start_timer("portfolio_risk_assessment")
        metrics, alerts = self.risk_manager.assess_portfolio_risk()
        self.performance_monitor.end_timer("portfolio_risk_assessment")
        
        print(f"\n投资组合风险指标:")
        print(f"  VaR(95%): {metrics.var_95:.4f}")
        print(f"  VaR(99%): {metrics.var_99:.4f}")
        print(f"  最大回撤: {metrics.max_drawdown:.4f}")
        print(f"  波动率: {metrics.volatility:.4f}")
        print(f"  夏普比率: {metrics.sharpe_ratio:.4f}")
        print(f"  集中度风险: {metrics.concentration_risk:.4f}")
        print(f"  流动性风险: {metrics.liquidity_risk:.4f}")
        print(f"  更新时间: {metrics.update_time}")
        
        print(f"\n风险预警数量: {len(alerts)}")
        for alert in alerts:
            print(f"  {alert.risk_type.value}: {alert.message}")
        
        # 验证风险指标
        self.assertLessEqual(metrics.var_95, 0, "VaR(95%)应小于等于0")
        self.assertLessEqual(metrics.var_99, 0, "VaR(99%)应小于等于0")
        self.assertGreaterEqual(metrics.max_drawdown, 0, "最大回撤应大于等于0")
        self.assertGreaterEqual(metrics.volatility, 0, "波动率应大于等于0")
        self.assertIsInstance(metrics.sharpe_ratio, float, "夏普比率应为浮点数")
        self.assertGreaterEqual(metrics.concentration_risk, 0, "集中度风险应大于等于0")
        self.assertLessEqual(metrics.concentration_risk, 1, "集中度风险应小于等于1")
        self.assertGreaterEqual(metrics.liquidity_risk, 0, "流动性风险应大于等于0")
        self.assertLessEqual(metrics.liquidity_risk, 1, "流动性风险应小于等于1")
        self.assertIsNotNone(metrics.update_time, "更新时间不应为None")
        
        # 验证预警
        for alert in alerts:
            self.assertIsInstance(alert.risk_type, RiskType, "风险类型应为RiskType枚举")
            self.assertIsInstance(alert.risk_level, RiskLevel, "风险等级应为RiskLevel枚举")
            self.assertGreater(len(alert.message), 0, "预警消息不应为空")
            self.assertIsNotNone(alert.timestamp, "预警时间不应为None")
    
    def test_dynamic_stop_loss(self):
        """测试动态止损策略"""
        print("\n=== 测试动态止损策略 ===")
        
        for stock in self.test_stocks:
            purchase_price = stock.price * 0.9  # 假设买入价比当前价低10%
            
            # 计算止损价格
            self.performance_monitor.start_timer("stop_loss_calculation")
            stop_loss_price = self.risk_manager.calculate_stop_loss(stock, purchase_price)
            self.performance_monitor.end_timer("stop_loss_calculation")
            
            print(f"\n股票 {stock.code}:")
            print(f"  买入价格: {purchase_price:.2f}")
            print(f"  当前价格: {stock.price:.2f}")
            print(f"  止损价格: {stop_loss_price:.2f}")
            print(f"  止损幅度: {((purchase_price - stop_loss_price) / purchase_price * 100):.2f}%")
            
            # 验证止损价格
            self.assertGreater(stop_loss_price, 0, "止损价格应大于0")
            self.assertLess(stop_loss_price, purchase_price, "止损价格应小于买入价格")
            
            # 测试移动止损
            current_price = stock.price
            self.risk_manager.update_trailing_stop(stock.code, current_price)
            
            # 检查是否触发止损
            should_stop = self.risk_manager.check_stop_loss(stock.code, current_price * 0.95)  # 价格下跌5%
            
            print(f"  移动止损触发: {should_stop}")
            
            # 验证移动止损
            self.assertIsInstance(should_stop, bool, "止损检查应返回布尔值")
    
    def test_risk_report_generation(self):
        """测试风险报告生成"""
        print("\n=== 测试风险报告生成 ===")
        
        # 更新投资组合数据
        self.risk_manager.update_portfolio_data(self.test_stocks, self.test_portfolio)
        
        # 生成风险报告
        self.performance_monitor.start_timer("risk_report_generation")
        reports = self.risk_manager.generate_risk_reports(self.test_portfolio, self.test_stocks)
        self.performance_monitor.end_timer("risk_report_generation")
        
        print(f"\n生成的风险报告:")
        for report_type, report_file in reports.items():
            print(f"  {report_type}: {report_file}")
            
            # 验证报告文件存在
            self.assertTrue(os.path.exists(report_file), f"报告文件应存在: {report_file}")
            
            # 验证报告文件内容
            with open(report_file, 'r', encoding='utf-8') as f:
                content = f.read()
                self.assertGreater(len(content), 0, f"报告文件内容不应为空: {report_file}")
        
        # 验证报告类型
        self.assertIn("summary", reports, "应包含风险摘要报告")
        self.assertIn("portfolio", reports, "应包含投资组合风险报告")
        
        # 验证个股报告
        for stock in self.test_stocks:
            self.assertIn(f"stock_{stock.code}", reports, f"应包含个股风险报告: {stock.code}")
    
    def test_risk_strategy_comparison(self):
        """测试不同风险策略的比较"""
        print("\n=== 测试不同风险策略的比较 ===")
        
        # 创建不同策略的风险管理器
        conservative_config = RiskConfig(strategy=RiskStrategy.CONSERVATIVE)
        balanced_config = RiskConfig(strategy=RiskStrategy.BALANCED)
        aggressive_config = RiskConfig(strategy=RiskStrategy.AGGRESSIVE)
        
        conservative_manager = RiskManager(conservative_config)
        balanced_manager = RiskManager(balanced_config)
        aggressive_manager = RiskManager(aggressive_config)
        
        # 测试股票
        test_stock = self.test_stocks[0]
        purchase_price = test_stock.price * 0.9
        
        # 计算不同策略的止损价格
        conservative_stop = conservative_manager.calculate_stop_loss(test_stock, purchase_price)
        balanced_stop = balanced_manager.calculate_stop_loss(test_stock, purchase_price)
        aggressive_stop = aggressive_manager.calculate_stop_loss(test_stock, purchase_price)
        
        print(f"\n股票 {test_stock.code} 的不同策略止损价格:")
        print(f"  保守策略: {conservative_stop:.2f} ({((purchase_price - conservative_stop) / purchase_price * 100):.2f}%)")
        print(f"  平衡策略: {balanced_stop:.2f} ({((purchase_price - balanced_stop) / purchase_price * 100):.2f}%)")
        print(f"  激进策略: {aggressive_stop:.2f} ({((purchase_price - aggressive_stop) / purchase_price * 100):.2f}%)")
        
        # 验证策略差异
        self.assertGreater(conservative_stop, balanced_stop, "保守策略止损价格应高于平衡策略")
        self.assertGreater(balanced_stop, aggressive_stop, "平衡策略止损价格应高于激进策略")
        
        # 验证止损幅度
        conservative_loss = (purchase_price - conservative_stop) / purchase_price
        balanced_loss = (purchase_price - balanced_stop) / purchase_price
        aggressive_loss = (purchase_price - aggressive_stop) / purchase_price
        
        self.assertLess(conservative_loss, balanced_loss, "保守策略止损幅度应小于平衡策略")
        self.assertLess(balanced_loss, aggressive_loss, "平衡策略止损幅度应小于激进策略")
    
    def test_var_method_comparison(self):
        """测试不同VaR计算方法的比较"""
        print("\n=== 测试不同VaR计算方法的比较 ===")
        
        # 创建不同VaR方法的配置
        historical_config = RiskConfig(var_method=VaRMethod.HISTORICAL)
        parametric_config = RiskConfig(var_method=VaRMethod.PARAMETRIC)
        monte_carlo_config = RiskConfig(var_method=VaRMethod.MONTE_CARLO)
        
        historical_calculator = RiskIndicatorCalculator(historical_config)
        parametric_calculator = RiskIndicatorCalculator(parametric_config)
        monte_carlo_calculator = RiskIndicatorCalculator(monte_carlo_config)
        
        # 测试收益率数据
        returns = [0.01, -0.02, 0.015, -0.01, 0.005, 0.02, -0.015, 0.01, -0.005, 0.008]
        
        # 计算不同方法的VaR
        historical_var = historical_calculator.calculate_var(returns, 0.95)
        parametric_var = parametric_calculator.calculate_var(returns, 0.95)
        monte_carlo_var = monte_carlo_calculator.calculate_var(returns, 0.95)
        
        print(f"\n不同VaR计算方法的结果:")
        print(f"  历史模拟法: {historical_var:.4f}")
        print(f"  参数法: {parametric_var:.4f}")
        print(f"  蒙特卡洛模拟: {monte_carlo_var:.4f}")
        
        # 验证VaR计算结果
        for var, method in [(historical_var, "历史模拟法"), 
                           (parametric_var, "参数法"), 
                           (monte_carlo_var, "蒙特卡洛模拟")]:
            self.assertLessEqual(var, 0, f"{method}VaR应小于等于0")
            self.assertIsInstance(var, float, f"{method}VaR应为浮点数")
    
    def test_risk_integration_with_scoring(self):
        """测试风险管理与评分系统的集成"""
        print("\n=== 测试风险管理与评分系统的集成 ===")
        
        for stock in self.test_stocks:
            # 多因子评分
            multi_factor_score = self.multi_factor_scorer.calculate_score(stock)
            
            # 旧系统评分
            legacy_score = self.legacy_scorer.calculate_total_score(stock) / 100
            
            # 计算止损价格
            purchase_price = stock.price * 0.9
            stop_loss_price = self.risk_manager.calculate_stop_loss(stock, purchase_price)
            
            # 计算风险指标
            returns = [0.01, -0.02, 0.015, -0.01, 0.005, 0.02, -0.015, 0.01, -0.005, 0.008]
            calculator = RiskIndicatorCalculator(self.risk_config)
            var_95 = calculator.calculate_var(returns, 0.95)
            volatility = calculator.calculate_volatility(returns)
            
            print(f"\n股票 {stock.code}:")
            print(f"  多因子评分: {multi_factor_score:.3f}")
            print(f"  旧系统评分: {legacy_score:.3f}")
            print(f"  止损价格: {stop_loss_price:.2f}")
            print(f"  VaR(95%): {var_95:.4f}")
            print(f"  波动率: {volatility:.4f}")
            
            # 验证评分与风险的关系
            # 高评分股票应该有较低的风险
            if multi_factor_score > 0.7:
                self.assertLessEqual(volatility, 0.3, f"高评分股票波动率应较低: {stock.code}")
            
            # 验证止损价格的合理性
            self.assertGreater(stop_loss_price, 0, f"止损价格应大于0: {stock.code}")
            self.assertLess(stop_loss_price, purchase_price, f"止损价格应小于买入价格: {stock.code}")
            
            # 验证风险指标
            self.assertLessEqual(var_95, 0, f"VaR应小于等于0: {stock.code}")
            self.assertGreaterEqual(volatility, 0, f"波动率应大于等于0: {stock.code}")
    
    def test_performance_benchmarks(self):
        """测试性能基准"""
        print("\n=== 测试性能基准 ===")
        
        # 大量股票数据
        large_stocks = []
        for i in range(100):
            stock = TestDataGenerator.create_test_stock(
                f"STOCK{i:03d}", f"股票{i}", 
                10.0 + i * 0.1, 5.0 + i * 0.01, 15.0 + i * 0.1, 2.0 + i * 0.01
            )
            large_stocks.append(stock)
        
        # 大量投资组合
        large_portfolio = {f"STOCK{i:03d}": 0.01 for i in range(100)}
        
        # 测试大数据量风险评估
        self.performance_monitor.start_timer("large_portfolio_risk_assessment")
        self.risk_manager.update_portfolio_data(large_stocks, large_portfolio)
        metrics, alerts = self.risk_manager.assess_portfolio_risk()
        self.performance_monitor.end_timer("large_portfolio_risk_assessment")
        
        print(f"\n大数据量性能测试结果:")
        print(f"  100只股票风险评估: {self.performance_monitor.get_metric('large_portfolio_risk_assessment'):.4f}秒")
        print(f"  风险预警数量: {len(alerts)}")
        
        # 验证大数据量处理
        self.assertIsNotNone(metrics, "大数据量风险评估结果不应为None")
        self.assertIsInstance(alerts, list, "预警结果应为列表")
        
        # 性能基准检查
        self.assert_performance_metric("large_portfolio_risk_assessment", 
                                   self.performance_monitor.get_metric('large_portfolio_risk_assessment'), 
                                   0.5, "大数据量风险评估性能")
    
    def tearDown(self):
        """测试后清理"""
        # 保存测试结果
        result_file = self.save_test_result()
        print(f"\n测试结果已保存到: {result_file}")
        
        super().tearDown()


if __name__ == '__main__':
    unittest.main()