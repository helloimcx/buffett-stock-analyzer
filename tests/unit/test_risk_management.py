"""
风险管理模块测试
采用TDD方法开发风险控制功能
"""

import pytest
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from typing import List, Dict, Any
import tempfile
import shutil
import os

from src.buffett.models.stock import StockInfo
from src.buffett.models.monitoring import TradingSignal, SignalType, SignalStrength
from src.buffett.core.risk_management import (
    RiskType, RiskLevel, RiskStrategy, VaRMethod,
    RiskMetrics, RiskThreshold, RiskAlert, RiskConfig,
    RiskIndicatorCalculator, RiskMonitor, DynamicStopLoss,
    RiskReportGenerator, RiskManager
)


class TestRiskIndicatorCalculator:
    """风险指标计算器测试"""
    
    def setup_method(self):
        """设置测试环境"""
        self.config = RiskConfig()
        self.calculator = RiskIndicatorCalculator(self.config)
    
    def test_calculate_var_historical_method(self):
        """测试历史方法计算VaR"""
        # 创建模拟收益率数据
        returns = np.random.normal(0, 0.02, 100).tolist()
        
        # 计算VaR
        var_95 = self.calculator.calculate_var(returns, 0.95)
        
        # 验证结果
        assert isinstance(var_95, float)
        assert var_95 < 0  # VaR应该是负值（表示损失）
    
    def test_calculate_var_parametric_method(self):
        """测试参数法计算VaR"""
        # 使用参数法配置
        self.config.var_method = VaRMethod.PARAMETRIC
        calculator = RiskIndicatorCalculator(self.config)
        
        # 创建模拟收益率数据
        returns = np.random.normal(0, 0.02, 100).tolist()
        
        # 计算VaR
        var_95 = calculator.calculate_var(returns, 0.95)
        
        # 验证结果
        assert isinstance(var_95, float)
        assert var_95 < 0  # VaR应该是负值（表示损失）
    
    def test_calculate_var_monte_carlo_method(self):
        """测试蒙特卡洛方法计算VaR"""
        # 使用蒙特卡洛法配置
        self.config.var_method = VaRMethod.MONTE_CARLO
        calculator = RiskIndicatorCalculator(self.config)
        
        # 创建模拟收益率数据
        returns = np.random.normal(0, 0.02, 100).tolist()
        
        # 计算VaR
        var_95 = calculator.calculate_var(returns, 0.95)
        
        # 验证结果
        assert isinstance(var_95, float)
        assert var_95 < 0  # VaR应该是负值（表示损失）
    
    def test_calculate_var_insufficient_data(self):
        """测试数据不足时的VaR计算"""
        # 数据不足的情况
        returns = [0.01, 0.02]  # 只有2个数据点
        
        var_95 = self.calculator.calculate_var(returns, 0.95)
        
        # 验证结果
        assert var_95 == 0.0  # 数据不足时应该返回0
    
    def test_calculate_max_drawdown(self):
        """测试最大回撤计算"""
        # 创建模拟价格序列（先上涨后下跌）
        prices = [100, 105, 110, 115, 120, 110, 100, 95, 90, 85]
        
        max_dd = self.calculator.calculate_max_drawdown(prices)
        
        # 验证结果
        assert isinstance(max_dd, float)
        assert max_dd > 0  # 最大回撤应该是正值
        # 从最高点120跌到最低点85，回撤应该是(120-85)/120 = 0.2917
        assert abs(max_dd - 0.2917) < 0.01
    
    def test_calculate_max_drawdown_insufficient_data(self):
        """测试数据不足时的最大回撤计算"""
        prices = [100]  # 只有一个数据点
        
        max_dd = self.calculator.calculate_max_drawdown(prices)
        
        # 验证结果
        assert max_dd == 0.0  # 数据不足时应该返回0
    
    def test_calculate_volatility(self):
        """测试波动率计算"""
        # 创建模拟收益率数据
        returns = np.random.normal(0, 0.02, 100).tolist()
        
        volatility = self.calculator.calculate_volatility(returns)
        
        # 验证结果
        assert isinstance(volatility, float)
        assert volatility > 0  # 波动率应该是正值
    
    def test_calculate_volatility_annualize(self):
        """测试年化波动率计算"""
        # 创建模拟日收益率数据
        returns = np.random.normal(0, 0.02, 100).tolist()
        
        # 计算年化波动率
        annual_volatility = self.calculator.calculate_volatility(returns, annualize=True)
        
        # 计算非年化波动率
        daily_volatility = self.calculator.calculate_volatility(returns, annualize=False)
        
        # 验证结果
        assert annual_volatility > daily_volatility
        # 年化因子应该是sqrt(252)
        assert abs(annual_volatility - daily_volatility * np.sqrt(252)) < 0.01
    
    def test_calculate_sharpe_ratio(self):
        """测试夏普比率计算"""
        # 创建模拟收益率数据（正收益）
        returns = np.random.normal(0.001, 0.02, 100).tolist()
        
        sharpe_ratio = self.calculator.calculate_sharpe_ratio(returns)
        
        # 验证结果
        assert isinstance(sharpe_ratio, float)
    
    def test_calculate_correlation_matrix(self):
        """测试相关性矩阵计算"""
        # 创建模拟收益率数据
        returns_dict = {
            "STOCK1": np.random.normal(0, 0.02, 100).tolist(),
            "STOCK2": np.random.normal(0, 0.02, 100).tolist(),
            "STOCK3": np.random.normal(0, 0.02, 100).tolist()
        }
        
        correlation_matrix = self.calculator.calculate_correlation_matrix(returns_dict)
        
        # 验证结果
        assert isinstance(correlation_matrix, dict)
        assert len(correlation_matrix) == 3  # 3只股票
        
        # 检查对角线元素（应该是1）
        for symbol in correlation_matrix:
            assert abs(correlation_matrix[symbol][symbol] - 1.0) < 0.01
    
    def test_calculate_concentration_risk(self):
        """测试集中度风险计算"""
        # 创建模拟权重数据
        weights = {"STOCK1": 0.5, "STOCK2": 0.3, "STOCK3": 0.2}
        
        concentration_risk = self.calculator.calculate_concentration_risk(weights)
        
        # 验证结果
        assert isinstance(concentration_risk, float)
        assert concentration_risk > 0
        
        # 计算期望的赫芬达尔指数
        expected_hhi = 0.5**2 + 0.3**2 + 0.2**2
        assert abs(concentration_risk - expected_hhi) < 0.01
    
    def test_calculate_liquidity_risk(self):
        """测试流动性风险计算"""
        # 创建模拟成交量和价格数据
        volumes = [1000000, 1200000, 800000, 1500000, 900000]
        prices = [10.0, 10.5, 9.8, 11.0, 10.2]
        
        liquidity_risk = self.calculator.calculate_liquidity_risk(volumes, prices)
        
        # 验证结果
        assert isinstance(liquidity_risk, float)
        assert 0 <= liquidity_risk <= 1  # 流动性风险应该在0-1之间


class TestRiskMonitor:
    """风险监控器测试"""
    
    def setup_method(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.config = RiskConfig()
        self.monitor = RiskMonitor(self.config)
    
    def teardown_method(self):
        """清理测试环境"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_update_portfolio_weights(self):
        """测试更新投资组合权重"""
        weights = {"STOCK1": 0.5, "STOCK2": 0.3, "STOCK3": 0.2}
        
        self.monitor.update_portfolio_weights(weights)
        
        # 验证结果
        assert self.monitor.portfolio_weights == weights
    
    def test_add_price_data(self):
        """测试添加价格数据"""
        symbol = "STOCK1"
        price = 100.0
        volume = 1000000
        
        self.monitor.add_price_data(symbol, price, volume)
        
        # 验证结果
        assert symbol in self.monitor.price_history
        assert self.monitor.price_history[symbol][-1] == price
        assert symbol in self.monitor.volume_history
        assert self.monitor.volume_history[symbol][-1] == volume
    
    def test_calculate_portfolio_risk_metrics(self):
        """测试计算投资组合风险指标"""
        # 添加测试数据
        weights = {"STOCK1": 0.6, "STOCK2": 0.4}
        self.monitor.update_portfolio_weights(weights)
        
        # 添加价格数据
        for i in range(50):
            price1 = 100 * (1 + np.random.normal(0, 0.02))
            price2 = 50 * (1 + np.random.normal(0, 0.02))
            self.monitor.add_price_data("STOCK1", price1, 1000000)
            self.monitor.add_price_data("STOCK2", price2, 800000)
        
        # 计算风险指标
        metrics = self.monitor.calculate_portfolio_risk_metrics()
        
        # 验证结果
        assert isinstance(metrics, RiskMetrics)
        assert metrics.var_95 != 0  # 应该计算出VaR
        assert metrics.volatility > 0  # 波动率应该大于0
    
    def test_check_risk_thresholds(self):
        """测试检查风险阈值"""
        # 创建高风险指标
        metrics = RiskMetrics(
            var_95=-0.1,  # 超过阈值
            max_drawdown=0.2,  # 超过阈值
            volatility=0.3,  # 超过阈值
            concentration_risk=0.4,  # 超过阈值
            liquidity_risk=0.8  # 超过阈值
        )
        
        alerts = self.monitor.check_risk_thresholds(metrics)
        
        # 验证结果
        assert len(alerts) > 0  # 应该产生预警
        assert all(isinstance(alert, RiskAlert) for alert in alerts)


class TestDynamicStopLoss:
    """动态止损策略测试"""
    
    def setup_method(self):
        """设置测试环境"""
        self.config = RiskConfig()
        self.stop_loss = DynamicStopLoss(self.config)
    
    def test_conservative_stop_loss_strategy(self):
        """测试保守型止损策略"""
        self.config.strategy = RiskStrategy.CONSERVATIVE
        stop_loss = DynamicStopLoss(self.config)
        
        # 创建测试股票
        stock = create_mock_stock_info("STOCK1", 100.0, pe_ratio=15.0, pb_ratio=2.0, week_52_low=90.0)
        purchase_price = 100.0
        
        stop_price = stop_loss.calculate_stop_loss_price(stock, purchase_price)
        
        # 验证结果
        assert stop_price < purchase_price  # 止损价应该低于购买价
        # 保守型止损应该在52周低点上方2%
        assert abs(stop_price - 90.0 * 1.02) < 0.01
    
    def test_balanced_stop_loss_strategy(self):
        """测试平衡型止损策略"""
        self.config.strategy = RiskStrategy.BALANCED
        stop_loss = DynamicStopLoss(self.config)
        
        # 创建测试股票
        stock = create_mock_stock_info("STOCK1", 100.0, pe_ratio=15.0, pb_ratio=2.0, week_52_low=90.0)
        purchase_price = 100.0
        
        stop_price = stop_loss.calculate_stop_loss_price(stock, purchase_price)
        
        # 验证结果
        assert stop_price < purchase_price  # 止损价应该低于购买价
        # 平衡型止损应该在52周低点上方5%
        assert abs(stop_price - 90.0 * 1.05) < 0.01
    
    def test_aggressive_stop_loss_strategy(self):
        """测试激进型止损策略"""
        self.config.strategy = RiskStrategy.AGGRESSIVE
        stop_loss = DynamicStopLoss(self.config)
        
        # 创建测试股票
        stock = create_mock_stock_info("STOCK1", 100.0, pe_ratio=15.0, pb_ratio=2.0, week_52_low=90.0)
        purchase_price = 100.0
        
        stop_price = stop_loss.calculate_stop_loss_price(stock, purchase_price)
        
        # 验证结果
        assert stop_price < purchase_price  # 止损价应该低于购买价
        # 激进型止损应该在52周低点上方8%
        assert abs(stop_price - 90.0 * 1.08) < 0.01
    
    def test_update_trailing_stop(self):
        """测试更新移动止损"""
        symbol = "STOCK1"
        initial_price = 100.0
        higher_price = 110.0
        
        # 设置初始止损和初始最高价（低于当前价格）
        self.stop_loss.stop_loss_levels[symbol] = initial_price * 0.92
        self.stop_loss.highest_prices[symbol] = initial_price
        
        # 更新移动止损（价格高于历史最高价）
        self.stop_loss.update_trailing_stop(symbol, higher_price)
        
        # 验证结果
        assert symbol in self.stop_loss.highest_prices
        assert self.stop_loss.highest_prices[symbol] == higher_price
        assert symbol in self.stop_loss.trailing_stop_levels
        assert self.stop_loss.trailing_stop_levels[symbol] < higher_price
    
    def test_should_trigger_stop_loss(self):
        """测试是否应该触发止损"""
        symbol = "STOCK1"
        stop_price = 95.0
        current_price = 94.0  # 低于止损价
        
        # 设置止损价
        self.stop_loss.stop_loss_levels[symbol] = stop_price
        
        # 检查是否触发止损
        should_trigger = self.stop_loss.should_trigger_stop_loss(symbol, current_price)
        
        # 验证结果
        assert should_trigger == True  # 应该触发止损


class TestRiskReportGenerator:
    """风险报告生成器测试"""
    
    def setup_method(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.config = RiskConfig()
        self.report_generator = RiskReportGenerator(self.config)
    
    def teardown_method(self):
        """清理测试环境"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_generate_risk_summary_report(self):
        """测试生成风险摘要报告"""
        # 创建测试数据
        metrics = RiskMetrics(
            var_95=-0.05,
            var_99=-0.08,
            max_drawdown=0.15,
            volatility=0.2,
            sharpe_ratio=1.0,
            concentration_risk=0.3,
            liquidity_risk=0.5
        )
        
        alerts = [
            RiskAlert(
                alert_id="test1",
                risk_type=RiskType.PORTFOLIO,
                risk_level=RiskLevel.MEDIUM,
                message="测试预警"
            )
        ]
        
        # 生成报告
        report_path = self.report_generator.generate_risk_summary_report(metrics, alerts)
        
        # 验证结果
        assert os.path.exists(report_path)
        assert report_path.endswith('.json')
    
    def test_generate_portfolio_risk_report(self):
        """测试生成投资组合风险报告"""
        # 创建测试数据
        portfolio_weights = {"STOCK1": 0.6, "STOCK2": 0.4}
        metrics = RiskMetrics(
            var_95=-0.05,
            var_99=-0.08,
            max_drawdown=0.15,
            volatility=0.2,
            sharpe_ratio=1.0,
            concentration_risk=0.3,
            liquidity_risk=0.5
        )
        
        # 生成报告
        report_path = self.report_generator.generate_portfolio_risk_report(portfolio_weights, metrics)
        
        # 验证结果
        assert os.path.exists(report_path)
        assert report_path.endswith('.json')
    
    def test_generate_individual_stock_risk_report(self):
        """测试生成个股风险报告"""
        # 创建测试数据
        stock = create_mock_stock_info("STOCK1", 100.0)
        price_history = [100, 105, 110, 115, 120, 110, 100, 95, 90, 85]
        
        # 生成报告
        report_path = self.report_generator.generate_individual_stock_risk_report(
            stock.code, stock, price_history
        )
        
        # 验证结果
        assert os.path.exists(report_path)
        assert report_path.endswith('.json')


class TestRiskManager:
    """风险管理器测试"""
    
    def setup_method(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.config = RiskConfig()
        self.risk_manager = RiskManager(self.config)
    
    def teardown_method(self):
        """清理测试环境"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_update_portfolio_data(self):
        """测试更新投资组合数据"""
        # 创建测试数据
        stocks = [
            create_mock_stock_info("STOCK1", 100.0),
            create_mock_stock_info("STOCK2", 50.0)
        ]
        weights = {"STOCK1": 0.6, "STOCK2": 0.4}
        
        # 更新数据
        self.risk_manager.update_portfolio_data(stocks, weights)
        
        # 验证结果
        assert self.risk_manager.monitor.portfolio_weights == weights
        assert "STOCK1" in self.risk_manager.monitor.price_history
        assert "STOCK2" in self.risk_manager.monitor.price_history
    
    def test_assess_portfolio_risk(self):
        """测试评估投资组合风险"""
        # 添加测试数据
        stocks = [
            create_mock_stock_info("STOCK1", 100.0),
            create_mock_stock_info("STOCK2", 50.0)
        ]
        weights = {"STOCK1": 0.6, "STOCK2": 0.4}
        
        # 更新数据
        for i in range(50):
            stocks[0].price = 100 * (1 + np.random.normal(0, 0.02))
            stocks[1].price = 50 * (1 + np.random.normal(0, 0.02))
            self.risk_manager.update_portfolio_data(stocks, weights)
        
        # 评估风险
        metrics, alerts = self.risk_manager.assess_portfolio_risk()
        
        # 验证结果
        assert isinstance(metrics, RiskMetrics)
        assert isinstance(alerts, list)
    
    def test_calculate_stop_loss(self):
        """测试计算止损价格"""
        stock = create_mock_stock_info("STOCK1", 100.0, pe_ratio=15.0, pb_ratio=2.0, week_52_low=90.0)
        purchase_price = 100.0
        
        stop_price = self.risk_manager.calculate_stop_loss(stock, purchase_price)
        
        # 验证结果
        assert stop_price < purchase_price  # 止损价应该低于购买价


# 测试数据
def create_mock_stock_info(code: str, price: float, dividend_yield: float = 3.0,
                          pe_ratio: float = 15.0, pb_ratio: float = 2.0,
                          change_pct: float = 0.01, volume: int = 1000000,
                          market_cap: float = 1000000000.0, eps: float = 1.0,
                          book_value: float = 10.0, week_52_high: float = 20.0,
                          week_52_low: float = 10.0) -> StockInfo:
    """创建模拟股票信息"""
    return StockInfo(
        code=code,
        name=f"股票{code}",
        price=price,
        dividend_yield=dividend_yield,
        pe_ratio=pe_ratio,
        pb_ratio=pb_ratio,
        change_pct=change_pct,
        volume=volume,
        market_cap=market_cap,
        eps=eps,
        book_value=book_value,
        week_52_high=week_52_high,
        week_52_low=week_52_low
    )


def create_mock_price_series(start_price: float, days: int, volatility: float = 0.02) -> List[float]:
    """创建模拟价格序列"""
    prices = [start_price]
    for _ in range(days - 1):
        change = np.random.normal(0, volatility)
        new_price = prices[-1] * (1 + change)
        prices.append(max(new_price, 0.01))  # 确保价格为正
    return prices