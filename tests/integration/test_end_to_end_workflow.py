"""
端到端工作流集成测试
验证完整的股票筛选、评分、技术分析、市场环境识别和风险控制的端到端工作流程
"""

import sys
import os
import unittest
import tempfile
import shutil
from pathlib import Path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from tests.integration.test_framework import IntegrationTestBase, TestDataGenerator, PerformanceMonitor
from src.buffett.core.multi_factor_scoring import MultiFactorScorer
from src.buffett.core.scoring import InvestmentScorer
from src.buffett.strategies.technical_analysis import TechnicalSignalGenerator
from src.buffett.core.market_environment import MarketEnvironmentIdentifier
from src.buffett.core.risk_management import RiskManager, RiskConfig
from src.buffett.strategies.screening import DividendScreeningStrategy
from src.buffett.core.monitor import StockMonitor
from src.buffett.models.stock import StockInfo
from src.buffett.models.monitoring import MonitoringConfig


class TestEndToEndWorkflow(IntegrationTestBase):
    """端到端工作流集成测试"""
    
    def setUp(self):
        """测试前准备"""
        super().setUp()
        
        # 创建大量测试股票数据
        self.test_stocks = []
        for i in range(20):
            stock = TestDataGenerator.create_test_stock(
                f"STOCK{i:03d}", f"测试股票{i}",
                price=10.0 + i * 0.5,
                dividend_yield=6.0 - i * 0.2,
                pe_ratio=12.0 + i * 0.5,
                pb_ratio=1.5 + i * 0.1
            )
            self.test_stocks.append(stock)
        
        # 创建价格和成交量历史数据
        self.price_histories = {}
        self.volume_histories = {}
        
        for stock in self.test_stocks:
            self.price_histories[stock.code] = TestDataGenerator.create_test_price_history(
                stock.code, days=60, base_price=stock.price
            )
            self.volume_histories[stock.code] = TestDataGenerator.create_test_volume_history(days=60)
        
        # 创建核心组件
        self.multi_factor_scorer = MultiFactorScorer.with_default_factors()
        self.legacy_scorer = InvestmentScorer()
        self.signal_generator = TechnicalSignalGenerator()
        self.environment_identifier = MarketEnvironmentIdentifier()
        self.risk_manager = RiskManager(RiskConfig())
        
        # 性能监控器
        self.performance_monitor = PerformanceMonitor()
        
        # 创建临时数据目录
        self.temp_data_dir = Path(self.temp_dir) / "data"
        self.temp_data_dir.mkdir(parents=True, exist_ok=True)
    
    def test_complete_stock_screening_workflow(self):
        """测试完整的股票筛选工作流程"""
        print("\n=== 测试完整的股票筛选工作流程 ===")
        
        # 场景1：完整的股票筛选和评分流程
        print("\n场景1：完整的股票筛选和评分流程")
        
        # 步骤1：股息筛选
        self.performance_monitor.start_timer("dividend_screening")
        screening_strategy = DividendScreeningStrategy()
        screening_result = screening_strategy.screen_dividend_stocks(min_dividend_yield=4.0)
        self.performance_monitor.end_timer("dividend_screening")
        
        print(f"筛选结果: 总分析股票数={screening_result.total_stocks_analyzed}, "
              f"通过股票数={len(screening_result.passed_stocks)}")
        
        # 验证筛选结果
        self.assertGreater(len(screening_result.passed_stocks), 0, "筛选结果不应为空")
        
        # 步骤2：多因子评分
        self.performance_monitor.start_timer("multi_factor_scoring")
        ranked_stocks = self.multi_factor_scorer.rank_stocks(screening_result.passed_stocks)
        self.performance_monitor.end_timer("multi_factor_scoring")
        
        print(f"多因子评分完成，排名前5的股票:")
        for i, stock in enumerate(ranked_stocks[:5]):
            print(f"  {i+1}. {stock.code}: {stock.total_score:.2f}")
        
        # 验证评分结果
        self.assertEqual(len(ranked_stocks), len(screening_result.passed_stocks), "评分结果数量应匹配")
        
        # 验证排序
        for i in range(len(ranked_stocks) - 1):
            self.assertGreaterEqual(
                ranked_stocks[i].total_score, ranked_stocks[i+1].total_score,
                "评分结果应为降序排列"
            )
        
        # 步骤3：技术分析
        self.performance_monitor.start_timer("technical_analysis")
        technical_results = {}
        for stock in ranked_stocks[:10]:  # 只分析前10只
            prices = self.price_histories[stock.code]
            volumes = self.volume_histories[stock.code]
            
            signals = self.signal_generator.generate_signals(prices, volumes)
            signal_strength = self.signal_generator.calculate_signal_strength(prices, volumes)
            
            technical_results[stock.code] = {
                'signals': signals,
                'signal_strength': signal_strength
            }
        
        self.performance_monitor.end_timer("technical_analysis")
        
        print(f"技术分析完成，前5只股票的信号强度:")
        for i, stock in enumerate(ranked_stocks[:5]):
            strength = technical_results[stock.code]['signal_strength']
            print(f"  {stock.code}: {strength:.3f}")
        
        # 验证技术分析结果
        self.assertEqual(len(technical_results), 10, "技术分析结果数量应匹配")
        
        for stock_code, result in technical_results.items():
            self.assertIn('signals', result, f"{stock_code}应包含信号")
            self.assertIn('signal_strength', result, f"{stock_code}应包含信号强度")
            self.assertGreaterEqual(result['signal_strength'], -1.0, f"{stock_code}信号强度应大于等于-1")
            self.assertLessEqual(result['signal_strength'], 1.0, f"{stock_code}信号强度应小于等于1")
        
        # 性能检查
        screening_time = self.performance_monitor.get_metric("dividend_screening")
        scoring_time = self.performance_monitor.get_metric("multi_factor_scoring")
        analysis_time = self.performance_monitor.get_metric("technical_analysis")
        
        print(f"\n性能统计:")
        print(f"  股息筛选: {screening_time:.4f}秒")
        print(f"  多因子评分: {scoring_time:.4f}秒")
        print(f"  技术分析: {analysis_time:.4f}秒")
        print(f"  总耗时: {screening_time + scoring_time + analysis_time:.4f}秒")
        
        self.assert_performance_metric("dividend_screening", screening_time, 1.0, "股息筛选性能")
        self.assert_performance_metric("multi_factor_scoring", scoring_time, 0.1, "多因子评分性能")
        self.assert_performance_metric("technical_analysis", analysis_time, 0.5, "技术分析性能")
    
    def test_market_environment_adaptive_workflow(self):
        """测试市场环境自适应工作流程"""
        print("\n=== 测试市场环境自适应工作流程 ===")
        
        # 场景2：市场环境变化时的自适应评分
        print("\n场景2：市场环境变化时的自适应评分")
        
        # 创建不同市场环境的数据
        market_data = {
            "bull": {
                "prices": [100 + i * 0.5 for i in range(60)],
                "volumes": [1000000 + i * 10000 for i in range(60)],
                "current_volume": 1000000 + 59 * 10000,
                "avg_volume": 1000000 + 30 * 10000,
                "advancing_stocks": 150,
                "declining_stocks": 50,
                "momentum": 0.03
            },
            "bear": {
                "prices": [100 - i * 0.3 for i in range(60)],
                "volumes": [1000000 - i * 5000 for i in range(60)],
                "current_volume": 1000000 - 59 * 5000,
                "avg_volume": 1000000 - 30 * 5000,
                "advancing_stocks": 30,
                "declining_stocks": 170,
                "momentum": -0.04
            }
        }
        
        # 在不同市场环境下评分
        for env_type, data in market_data.items():
            print(f"\n{env_type.upper()}市场环境下的评分:")
            
            # 识别市场环境
            self.performance_monitor.start_timer("environment_identification")
            environment = self.environment_identifier.identify_environment(data)
            self.performance_monitor.end_timer("environment_identification")
            
            print(f"  环境类型: {environment.environment_type.value}")
            print(f"  置信度: {environment.confidence:.3f}")
            
            # 对测试股票评分
            test_stock = self.test_stocks[0]
            
            self.performance_monitor.start_timer("adaptive_scoring")
            multi_factor_score = self.multi_factor_scorer.calculate_score(test_stock)
            legacy_score = self.legacy_scorer.calculate_total_score(test_stock) / 100
            self.performance_monitor.end_timer("adaptive_scoring")
            
            print(f"  多因子评分: {multi_factor_score:.3f}")
            print(f"  旧系统评分: {legacy_score:.3f}")
            
            # 验证评分一致性
            score_diff = abs(multi_factor_score - legacy_score)
            self.assertLessEqual(score_diff, 0.4, f"{env_type}市场下评分差异过大")
            
            # 验证环境识别
            if env_type == "bull":
                self.assertIn(environment.environment_type.value, ["bull", "sideways"], 
                              "牛市应被识别为牛市或震荡市")
            elif env_type == "bear":
                self.assertIn(environment.environment_type.value, ["bear", "sideways"], 
                              "熊市应被识别为熊市或震荡市")
        
        # 测试环境变化检测
        bull_env = self.environment_identifier.identify_environment(market_data["bull"])
        bear_env = self.environment_identifier.identify_environment(market_data["bear"])
        
        has_changed = self.environment_identifier.detect_environment_change(bull_env, bear_env)
        self.assertTrue(has_changed, "牛市到熊市应被检测为环境变化")
        
        # 生成变化预警
        alert = self.environment_identifier.generate_change_alert(bull_env, bear_env)
        self.assertIsNotNone(alert, "应能生成环境变化预警")
        self.assertEqual(alert.alert_type, "market_change", "预警类型应为市场变化")
        
        print(f"\n环境变化预警: {alert.message}")
        
        # 性能检查
        env_time = self.performance_monitor.get_metric("environment_identification")
        score_time = self.performance_monitor.get_metric("adaptive_scoring")
        
        print(f"\n性能统计:")
        print(f"  环境识别: {env_time:.4f}秒")
        print(f"  自适应评分: {score_time:.4f}秒")
        
        self.assert_performance_metric("environment_identification", env_time, 0.05, "环境识别性能")
        self.assert_performance_metric("adaptive_scoring", score_time, 0.01, "自适应评分性能")
    
    def test_technical_analysis_integration_workflow(self):
        """测试技术分析与多因子评分的结合工作流程"""
        print("\n=== 测试技术分析与多因子评分的结合工作流程 ===")
        
        # 场景3：技术分析与多因子评分的结合
        print("\n场景3：技术分析与多因子评分的结合")
        
        # 选择测试股票
        test_stocks = self.test_stocks[:10]
        
        # 步骤1：多因子评分
        self.performance_monitor.start_timer("workflow_multi_factor_scoring")
        ranked_stocks = self.multi_factor_scorer.rank_stocks(test_stocks)
        self.performance_monitor.end_timer("workflow_multi_factor_scoring")
        
        # 步骤2：技术分析
        self.performance_monitor.start_timer("workflow_technical_analysis")
        technical_signals = {}
        for stock in ranked_stocks:
            prices = self.price_histories[stock.code]
            volumes = self.volume_histories[stock.code]
            
            signals = self.signal_generator.generate_signals(prices, volumes)
            signal_strength = self.signal_generator.calculate_signal_strength(prices, volumes)
            
            technical_signals[stock.code] = {
                'buy_signals': len(signals['buy_signals']),
                'sell_signals': len(signals['sell_signals']),
                'signal_strength': signal_strength
            }
        
        self.performance_monitor.end_timer("workflow_technical_analysis")
        
        # 步骤3：综合评分（结合技术分析）
        self.performance_monitor.start_timer("integrated_scoring")
        integrated_ranking = []
        for stock in ranked_stocks:
            # 基础多因子评分
            base_score = stock.total_score / 100  # 转换为0-1范围
            
            # 技术分析加分
            tech_signals = technical_signals[stock.code]
            tech_bonus = 0
            
            if tech_signals['signal_strength'] > 0.3:  # 强买入信号
                tech_bonus = 0.1
            elif tech_signals['signal_strength'] < -0.3:  # 强卖出信号
                tech_bonus = -0.1
            
            # 综合评分
            integrated_score = base_score + tech_bonus
            integrated_score = max(0, min(1, integrated_score))  # 限制在0-1范围
            
            integrated_ranking.append({
                'stock': stock,
                'base_score': base_score,
                'tech_signals': tech_signals,
                'integrated_score': integrated_score
            })
        
        # 按综合评分排序
        integrated_ranking.sort(key=lambda x: x['integrated_score'], reverse=True)
        self.performance_monitor.end_timer("integrated_scoring")
        
        # 显示结果
        print(f"\n综合评分排名前5的股票:")
        for i, item in enumerate(integrated_ranking[:5]):
            stock = item['stock']
            base_score = item['base_score']
            tech_signals = item['tech_signals']
            integrated_score = item['integrated_score']
            
            print(f"  {i+1}. {stock.code}:")
            print(f"     基础评分: {base_score:.3f}")
            print(f"     买入信号: {tech_signals['buy_signals']}")
            print(f"     卖出信号: {tech_signals['sell_signals']}")
            print(f"     信号强度: {tech_signals['signal_strength']:.3f}")
            print(f"     综合评分: {integrated_score:.3f}")
        
        # 验证结果
        self.assertEqual(len(integrated_ranking), len(test_stocks), "综合评分结果数量应匹配")
        
        # 验证排序
        for i in range(len(integrated_ranking) - 1):
            self.assertGreaterEqual(
                integrated_ranking[i]['integrated_score'], 
                integrated_ranking[i+1]['integrated_score'],
                "综合评分应为降序排列"
            )
        
        # 验证评分范围
        for item in integrated_ranking:
            self.assertGreaterEqual(item['integrated_score'], 0.0, "综合评分应大于等于0")
            self.assertLessEqual(item['integrated_score'], 1.0, "综合评分应小于等于1")
        
        # 性能检查
        scoring_time = self.performance_monitor.get_metric("workflow_multi_factor_scoring")
        analysis_time = self.performance_monitor.get_metric("workflow_technical_analysis")
        integration_time = self.performance_monitor.get_metric("integrated_scoring")
        
        print(f"\n性能统计:")
        print(f"  多因子评分: {scoring_time:.4f}秒")
        print(f"  技术分析: {analysis_time:.4f}秒")
        print(f"  综合评分: {integration_time:.4f}秒")
        print(f"  总耗时: {scoring_time + analysis_time + integration_time:.4f}秒")
        
        self.assert_performance_metric("workflow_multi_factor_scoring", scoring_time, 0.05, "工作流多因子评分性能")
        self.assert_performance_metric("workflow_technical_analysis", analysis_time, 0.2, "工作流技术分析性能")
        self.assert_performance_metric("integrated_scoring", integration_time, 0.01, "综合评分性能")
    
    def test_risk_control_integration_workflow(self):
        """测试风险控制与信号生成的联动工作流程"""
        print("\n=== 测试风险控制与信号生成的联动工作流程 ===")
        
        # 场景4：风险控制与信号生成的联动
        print("\n场景4：风险控制与信号生成的联动")
        
        # 选择测试股票
        test_stocks = self.test_stocks[:5]
        
        # 创建投资组合
        portfolio = {stock.code: 0.2 for stock in test_stocks}
        
        # 步骤1：更新投资组合数据
        self.performance_monitor.start_timer("portfolio_data_update")
        self.risk_manager.update_portfolio_data(test_stocks, portfolio)
        self.performance_monitor.end_timer("portfolio_data_update")
        
        # 步骤2：风险评估
        self.performance_monitor.start_timer("portfolio_risk_assessment")
        risk_metrics, risk_alerts = self.risk_manager.assess_portfolio_risk()
        self.performance_monitor.end_timer("portfolio_risk_assessment")
        
        print(f"\n投资组合风险指标:")
        print(f"  VaR(95%): {risk_metrics.var_95:.4f}")
        print(f"  最大回撤: {risk_metrics.max_drawdown:.4f}")
        print(f"  波动率: {risk_metrics.volatility:.4f}")
        print(f"  集中度风险: {risk_metrics.concentration_risk:.4f}")
        print(f"  风险预警数量: {len(risk_alerts)}")
        
        # 步骤3：个股风险检查
        self.performance_monitor.start_timer("individual_risk_check")
        stock_risks = {}
        for stock in test_stocks:
            # 计算止损价格
            purchase_price = stock.price * 0.9
            stop_loss_price = self.risk_manager.calculate_stop_loss(stock, purchase_price)
            
            # 计算风险指标
            prices = self.price_histories[stock.code]
            volumes = self.volume_histories[stock.code]
            
            # 技术信号
            signals = self.signal_generator.generate_signals(prices, volumes)
            signal_strength = self.signal_generator.calculate_signal_strength(prices, volumes)
            
            stock_risks[stock.code] = {
                'purchase_price': purchase_price,
                'stop_loss_price': stop_loss_price,
                'stop_loss_pct': (purchase_price - stop_loss_price) / purchase_price,
                'signal_strength': signal_strength,
                'buy_signals': len(signals['buy_signals']),
                'sell_signals': len(signals['sell_signals'])
            }
        
        self.performance_monitor.end_timer("individual_risk_check")
        
        # 步骤4：风险调整后的决策
        self.performance_monitor.start_timer("risk_adjusted_decision")
        risk_adjusted_signals = []
        for stock in test_stocks:
            stock_risk = stock_risks[stock.code]
            
            # 基础评分
            base_score = self.multi_factor_scorer.calculate_score(stock)
            
            # 风险调整
            risk_adjustment = 0
            
            # 高风险股票降低评分
            if stock_risk['stop_loss_pct'] > 0.15:  # 止损幅度大于15%
                risk_adjustment -= 0.1
            
            # 强烈卖出信号降低评分
            if stock_risk['signal_strength'] < -0.3:
                risk_adjustment -= 0.2
            
            # 强烈买入信号提高评分
            if stock_risk['signal_strength'] > 0.3:
                risk_adjustment += 0.1
            
            # 最终评分
            final_score = base_score + risk_adjustment
            final_score = max(0, min(1, final_score))
            
            # 决策
            if final_score > 0.7 and stock_risk['signal_strength'] > 0.2:
                decision = "BUY"
            elif final_score < 0.3 or stock_risk['signal_strength'] < -0.2:
                decision = "SELL"
            else:
                decision = "HOLD"
            
            risk_adjusted_signals.append({
                'stock': stock,
                'base_score': base_score,
                'risk_adjustment': risk_adjustment,
                'final_score': final_score,
                'decision': decision,
                'risk_info': stock_risk
            })
        
        self.performance_monitor.end_timer("risk_adjusted_decision")
        
        # 显示结果
        print(f"\n风险调整后的交易信号:")
        for item in risk_adjusted_signals:
            stock = item['stock']
            decision = item['decision']
            final_score = item['final_score']
            risk_info = item['risk_info']
            
            print(f"  {stock.code}: {decision}")
            print(f"    最终评分: {final_score:.3f}")
            print(f"    止损幅度: {risk_info['stop_loss_pct']:.2%}")
            print(f"    信号强度: {risk_info['signal_strength']:.3f}")
        
        # 验证结果
        self.assertEqual(len(risk_adjusted_signals), len(test_stocks), "风险调整信号数量应匹配")
        
        for item in risk_adjusted_signals:
            self.assertIn(item['decision'], ['BUY', 'SELL', 'HOLD'], "决策应为有效值")
            self.assertGreaterEqual(item['final_score'], 0.0, "最终评分应大于等于0")
            self.assertLessEqual(item['final_score'], 1.0, "最终评分应小于等于1")
        
        # 性能检查
        update_time = self.performance_monitor.get_metric("portfolio_data_update")
        risk_time = self.performance_monitor.get_metric("portfolio_risk_assessment")
        individual_time = self.performance_monitor.get_metric("individual_risk_check")
        decision_time = self.performance_monitor.get_metric("risk_adjusted_decision")
        
        print(f"\n性能统计:")
        print(f"  投资组合更新: {update_time:.4f}秒")
        print(f"  风险评估: {risk_time:.4f}秒")
        print(f"  个股风险检查: {individual_time:.4f}秒")
        print(f"  风险调整决策: {decision_time:.4f}秒")
        print(f"  总耗时: {update_time + risk_time + individual_time + decision_time:.4f}秒")
        
        self.assert_performance_metric("portfolio_data_update", update_time, 0.1, "投资组合更新性能")
        self.assert_performance_metric("portfolio_risk_assessment", risk_time, 0.1, "风险评估性能")
        self.assert_performance_metric("individual_risk_check", individual_time, 0.2, "个股风险检查性能")
        self.assert_performance_metric("risk_adjusted_decision", decision_time, 0.05, "风险调整决策性能")
    
    def test_real_time_monitoring_simulation(self):
        """测试实时监控模拟"""
        print("\n=== 测试实时监控模拟 ===")
        
        # 场景5：实时监控和预警系统
        print("\n场景5：实时监控和预警系统")
        
        # 创建监控配置
        monitoring_config = MonitoringConfig(
            stock_symbols=[stock.code for stock in self.test_stocks[:5]],
            monitoring_interval=1,  # 1秒间隔（测试用）
            buy_score_threshold=70.0,
            sell_score_threshold=30.0,
            enable_notifications=True,
            notification_methods=['console']
        )
        
        # 创建监控器（使用临时目录）
        monitor = StockMonitor(monitoring_config)
        
        # 模拟监控过程
        self.performance_monitor.start_timer("monitoring_simulation")
        
        # 初始化监控状态
        monitor._initialize_stock_states()
        
        # 模拟3轮监控检查
        monitoring_rounds = 3
        total_signals = []
        
        for round_num in range(monitoring_rounds):
            print(f"\n监控轮次 {round_num + 1}:")
            
            round_signals = []
            
            for stock in self.test_stocks[:5]:
                # 模拟价格变化
                price_change = 0.02 * (round_num + 1)  # 每轮上涨2%
                stock.price *= (1 + price_change)
                
                # 检测信号
                previous_state = monitor.stock_states.get(stock.code)
                signals = monitor.signal_detector.detect_signals(stock, previous_state)
                
                if signals:
                    round_signals.extend(signals)
                    print(f"  {stock.code}: 检测到 {len(signals)} 个信号")
                    
                    # 更新状态
                    monitor._update_stock_state(stock.code, stock, signals)
            
            total_signals.extend(round_signals)
            print(f"  本轮总计: {len(round_signals)} 个信号")
        
        self.performance_monitor.end_timer("monitoring_simulation")
        
        # 显示监控结果
        print(f"\n监控模拟结果:")
        print(f"  监控轮次: {monitoring_rounds}")
        print(f"  监控股票: {len(self.test_stocks[:5])}")
        print(f"  总信号数: {len(total_signals)}")
        
        # 按信号类型统计
        buy_signals = [s for s in total_signals if s.signal_type.value == "buy"]
        sell_signals = [s for s in total_signals if s.signal_type.value == "sell"]
        
        print(f"  买入信号: {len(buy_signals)}")
        print(f"  卖出信号: {len(sell_signals)}")
        
        # 验证监控结果
        self.assertGreater(len(total_signals), 0, "应检测到信号")
        self.assertEqual(len(monitor.stock_states), len(self.test_stocks[:5]), "股票状态数量应匹配")
        
        # 验证信号
        for signal in total_signals:
            self.assertIsNotNone(signal.stock_code, "信号应包含股票代码")
            self.assertIsNotNone(signal.stock_name, "信号应包含股票名称")
            self.assertIn(signal.signal_type.value, ['buy', 'sell'], "信号类型应为有效值")
            self.assertGreater(len(signal.reasons), 0, "信号原因不应为空")
        
        # 验证状态更新
        for stock_code, state in monitor.stock_states.items():
            self.assertIsNotNone(state.last_price, "状态应包含最新价格")
            self.assertIsNotNone(state.last_update, "状态应包含更新时间")
            self.assertIsInstance(state.price_history, list, "状态应包含价格历史")
        
        # 性能检查
        monitoring_time = self.performance_monitor.get_metric("monitoring_simulation")
        
        print(f"\n性能统计:")
        print(f"  监控模拟: {monitoring_time:.4f}秒")
        print(f"  平均每轮: {monitoring_time / monitoring_rounds:.4f}秒")
        
        self.assert_performance_metric("monitoring_simulation", monitoring_time, 2.0, "监控模拟性能")
    
    def test_comprehensive_integration_workflow(self):
        """测试综合集成工作流程"""
        print("\n=== 测试综合集成工作流程 ===")
        
        # 综合测试：所有模块协同工作
        print("\n综合测试：所有模块协同工作")
        
        # 选择测试股票
        test_stocks = self.test_stocks[:10]
        
        # 创建市场环境数据
        market_data = {
            "prices": [100 + i * 0.2 for i in range(60)],
            "volumes": [1000000 + i * 5000 for i in range(60)],
            "current_volume": 1000000 + 59 * 5000,
            "avg_volume": 1000000 + 30 * 5000,
            "advancing_stocks": 120,
            "declining_stocks": 80,
            "momentum": 0.01
        }
        
        # 完整工作流程
        self.performance_monitor.start_timer("comprehensive_workflow")
        
        # 步骤1：市场环境识别
        environment = self.environment_identifier.identify_environment(market_data)
        
        # 步骤2：股票筛选和评分
        ranked_stocks = self.multi_factor_scorer.rank_stocks(test_stocks)
        
        # 步骤3：技术分析
        technical_results = {}
        for stock in ranked_stocks:
            prices = self.price_histories[stock.code]
            volumes = self.volume_histories[stock.code]
            
            signals = self.signal_generator.generate_signals(prices, volumes)
            signal_strength = self.signal_generator.calculate_signal_strength(prices, volumes)
            
            technical_results[stock.code] = {
                'signals': signals,
                'signal_strength': signal_strength
            }
        
        # 步骤4：风险评估
        portfolio = {stock.code: 0.1 for stock in ranked_stocks}
        self.risk_manager.update_portfolio_data(ranked_stocks, portfolio)
        risk_metrics, risk_alerts = self.risk_manager.assess_portfolio_risk()
        
        # 步骤5：综合决策
        final_recommendations = []
        for stock in ranked_stocks:
            # 基础评分
            base_score = stock.total_score / 100
            
            # 技术分析调整
            tech_result = technical_results[stock.code]
            tech_adjustment = tech_result['signal_strength'] * 0.1
            
            # 市场环境调整
            env_adjustment = 0
            if environment.environment_type.value == "bull":
                env_adjustment = 0.05
            elif environment.environment_type.value == "bear":
                env_adjustment = -0.05
            
            # 风险调整
            risk_adjustment = 0
            if risk_metrics.volatility > 0.2:
                risk_adjustment = -0.1
            
            # 最终评分
            final_score = base_score + tech_adjustment + env_adjustment + risk_adjustment
            final_score = max(0, min(1, final_score))
            
            # 推荐决策
            if final_score > 0.7:
                recommendation = "STRONG_BUY"
            elif final_score > 0.6:
                recommendation = "BUY"
            elif final_score > 0.4:
                recommendation = "HOLD"
            elif final_score > 0.3:
                recommendation = "SELL"
            else:
                recommendation = "STRONG_SELL"
            
            final_recommendations.append({
                'stock': stock,
                'base_score': base_score,
                'tech_adjustment': tech_adjustment,
                'env_adjustment': env_adjustment,
                'risk_adjustment': risk_adjustment,
                'final_score': final_score,
                'recommendation': recommendation
            })
        
        # 按最终评分排序
        final_recommendations.sort(key=lambda x: x['final_score'], reverse=True)
        
        self.performance_monitor.end_timer("comprehensive_workflow")
        
        # 显示结果
        print(f"\n综合工作流程结果:")
        print(f"  市场环境: {environment.environment_type.value} (置信度: {environment.confidence:.3f})")
        print(f"  投资组合波动率: {risk_metrics.volatility:.3f}")
        print(f"  风险预警数量: {len(risk_alerts)}")
        
        print(f"\n前5推荐股票:")
        for i, item in enumerate(final_recommendations[:5]):
            stock = item['stock']
            recommendation = item['recommendation']
            final_score = item['final_score']
            
            print(f"  {i+1}. {stock.code}: {recommendation} (评分: {final_score:.3f})")
        
        # 验证结果
        self.assertEqual(len(final_recommendations), len(test_stocks), "推荐结果数量应匹配")
        
        for item in final_recommendations:
            self.assertIn(item['recommendation'], 
                         ['STRONG_BUY', 'BUY', 'HOLD', 'SELL', 'STRONG_SELL'], 
                         "推荐应为有效值")
            self.assertGreaterEqual(item['final_score'], 0.0, "最终评分应大于等于0")
            self.assertLessEqual(item['final_score'], 1.0, "最终评分应小于等于1")
        
        # 验证排序
        for i in range(len(final_recommendations) - 1):
            self.assertGreaterEqual(
                final_recommendations[i]['final_score'], 
                final_recommendations[i+1]['final_score'],
                "最终评分应为降序排列"
            )
        
        # 性能检查
        workflow_time = self.performance_monitor.get_metric("comprehensive_workflow")
        
        print(f"\n性能统计:")
        print(f"  综合工作流程: {workflow_time:.4f}秒")
        print(f"  平均每只股票: {workflow_time / len(test_stocks):.4f}秒")
        
        self.assert_performance_metric("comprehensive_workflow", workflow_time, 1.0, "综合工作流程性能")
    
    def tearDown(self):
        """测试后清理"""
        # 保存测试结果
        result_file = self.save_test_result()
        print(f"\n测试结果已保存到: {result_file}")
        
        super().tearDown()


if __name__ == '__main__':
    unittest.main()