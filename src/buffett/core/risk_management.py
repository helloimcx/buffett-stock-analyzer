"""
风险管理系统
实现多层次风险管理体系，包括风险指标计算、风险监控和动态止损策略
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging
from collections import defaultdict

from ..models.stock import StockInfo
from ..models.monitoring import TradingSignal, SignalType, SignalStrength
from ..utils.logger import get_logger

logger = get_logger(__name__)


class RiskType(Enum):
    """风险类型"""
    SYSTEMATIC = "systematic"      # 系统性风险
    PORTFOLIO = "portfolio"        # 投资组合风险
    INDIVIDUAL = "individual"      # 个股风险
    OPERATIONAL = "operational"    # 操作风险
    LIQUIDITY = "liquidity"        # 流动性风险
    CONCENTRATION = "concentration" # 集中度风险


class RiskLevel(Enum):
    """风险等级"""
    LOW = "low"        # 低风险
    MEDIUM = "medium"  # 中等风险
    HIGH = "high"      # 高风险
    CRITICAL = "critical"  # 严重风险


class RiskStrategy(Enum):
    """风险控制策略"""
    CONSERVATIVE = "conservative"  # 保守型
    BALANCED = "balanced"         # 平衡型
    AGGRESSIVE = "aggressive"     # 激进型


class VaRMethod(Enum):
    """VaR计算方法"""
    HISTORICAL = "historical"     # 历史模拟法
    PARAMETRIC = "parametric"     # 参数法
    MONTE_CARLO = "monte_carlo"   # 蒙特卡洛模拟


@dataclass
class RiskMetrics:
    """风险指标"""
    var_95: float = 0.0           # 95%置信度VaR
    var_99: float = 0.0           # 99%置信度VaR
    max_drawdown: float = 0.0     # 最大回撤
    volatility: float = 0.0       # 波动率
    sharpe_ratio: float = 0.0     # 夏普比率
    beta: float = 0.0             # 贝塔系数
    correlation_matrix: Dict[str, Dict[str, float]] = field(default_factory=dict)
    concentration_risk: float = 0.0  # 集中度风险
    liquidity_risk: float = 0.0   # 流动性风险
    update_time: datetime = field(default_factory=datetime.now)


@dataclass
class RiskThreshold:
    """风险阈值"""
    max_var_95: float = 0.05      # 最大VaR(95%)阈值
    max_var_99: float = 0.08      # 最大VaR(99%)阈值
    max_drawdown: float = 0.15    # 最大回撤阈值
    max_volatility: float = 0.25  # 最大波动率阈值
    min_sharpe_ratio: float = 0.5 # 最小夏普比率阈值
    max_concentration: float = 0.3 # 最大集中度阈值
    min_liquidity: float = 1000000  # 最小流动性阈值


@dataclass
class RiskAlert:
    """风险预警"""
    alert_id: str
    risk_type: RiskType
    risk_level: RiskLevel
    stock_code: Optional[str] = None
    message: str = ""
    current_value: float = 0.0
    threshold_value: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    is_resolved: bool = False


@dataclass
class RiskConfig:
    """风险管理配置"""
    strategy: RiskStrategy = RiskStrategy.BALANCED
    var_method: VaRMethod = VaRMethod.HISTORICAL
    var_confidence_levels: List[float] = field(default_factory=lambda: [0.95, 0.99])
    lookback_days: int = 252  # 回看天数（一年）
    rebalance_frequency: int = 30  # 再平衡频率（天）
    enable_risk_alerts: bool = True
    risk_thresholds: RiskThreshold = field(default_factory=RiskThreshold)


class RiskIndicatorCalculator:
    """风险指标计算器"""
    
    def __init__(self, config: RiskConfig):
        self.config = config
    
    def calculate_var(self, returns: List[float], confidence_level: float = 0.95) -> float:
        """计算风险价值(VaR)"""
        if not returns or len(returns) < 30:
            logger.warning("收益率数据不足，无法计算VaR")
            return 0.0
        
        returns_array = np.array(returns)
        
        if self.config.var_method == VaRMethod.HISTORICAL:
            # 历史模拟法
            return np.percentile(returns_array, (1 - confidence_level) * 100)
        
        elif self.config.var_method == VaRMethod.PARAMETRIC:
            # 参数法（假设正态分布）
            mean = np.mean(returns_array)
            std = np.std(returns_array)
            try:
                from scipy.stats import norm
                z_score = norm.ppf(1 - confidence_level)
                return mean + z_score * std
            except ImportError:
                # 如果没有scipy，使用近似值
                # 95%置信度对应1.645，99%置信度对应2.33
                if confidence_level >= 0.99:
                    z_score = 2.33
                elif confidence_level >= 0.95:
                    z_score = 1.645
                elif confidence_level >= 0.90:
                    z_score = 1.28
                else:
                    z_score = 1.0
                return mean - z_score * std  # 修正：应该是减法，因为VaR表示损失
        
        elif self.config.var_method == VaRMethod.MONTE_CARLO:
            # 蒙特卡洛模拟
            mean = np.mean(returns_array)
            std = np.std(returns_array)
            n_simulations = 10000
            simulated_returns = np.random.normal(mean, std, n_simulations)
            return np.percentile(simulated_returns, (1 - confidence_level) * 100)
        
        return 0.0
    
    def calculate_max_drawdown(self, prices: List[float]) -> float:
        """计算最大回撤"""
        if not prices or len(prices) < 2:
            return 0.0
        
        prices_array = np.array(prices)
        peak = np.maximum.accumulate(prices_array)
        drawdown = (prices_array - peak) / peak
        return abs(np.min(drawdown))
    
    def calculate_volatility(self, returns: List[float], annualize: bool = True) -> float:
        """计算波动率"""
        if not returns or len(returns) < 2:
            return 0.0
        
        returns_array = np.array(returns)
        volatility = np.std(returns_array)
        
        if annualize:
            # 假设日收益率，年化波动率
            volatility *= np.sqrt(252)
        
        return volatility
    
    def calculate_sharpe_ratio(self, returns: List[float], risk_free_rate: float = 0.02) -> float:
        """计算夏普比率"""
        if not returns or len(returns) < 2:
            return 0.0
        
        returns_array = np.array(returns)
        excess_returns = returns_array - risk_free_rate / 252  # 日化无风险利率
        
        if np.std(excess_returns) == 0:
            return 0.0
        
        sharpe = np.mean(excess_returns) / np.std(excess_returns)
        return sharpe * np.sqrt(252)  # 年化夏普比率
    
    def calculate_correlation_matrix(self, returns_dict: Dict[str, List[float]]) -> Dict[str, Dict[str, float]]:
        """计算相关性矩阵"""
        if not returns_dict or len(returns_dict) < 2:
            return {}
        
        # 确保所有收益率序列长度一致
        min_length = min(len(returns) for returns in returns_dict.values())
        if min_length < 30:
            logger.warning("收益率数据不足，无法计算相关性矩阵")
            return {}
        
        # 构建DataFrame
        data = {}
        for symbol, returns in returns_dict.items():
            data[symbol] = returns[:min_length]
        
        df = pd.DataFrame(data)
        correlation_matrix = df.corr()
        
        # 转换为字典格式
        result = {}
        for symbol1 in correlation_matrix.columns:
            result[symbol1] = {}
            for symbol2 in correlation_matrix.columns:
                result[symbol1][symbol2] = float(correlation_matrix.loc[symbol1, symbol2])
        
        return result
    
    def calculate_concentration_risk(self, weights: Dict[str, float]) -> float:
        """计算集中度风险（使用赫芬达尔指数）"""
        if not weights:
            return 0.0
        
        # 归一化权重
        total_weight = sum(weights.values())
        if total_weight == 0:
            return 0.0
        
        normalized_weights = {k: v / total_weight for k, v in weights.items()}
        
        # 计算赫芬达尔指数
        hhi = sum(w ** 2 for w in normalized_weights.values())
        return hhi
    
    def calculate_liquidity_risk(self, volumes: List[float], prices: List[float]) -> float:
        """计算流动性风险（基于平均成交额）"""
        if not volumes or not prices or len(volumes) != len(prices):
            return 0.0
        
        # 计算平均每日成交额
        daily_values = [v * p for v, p in zip(volumes, prices)]
        avg_daily_value = np.mean(daily_values)
        
        # 流动性风险与平均成交额成反比
        # 这里使用对数变换来平滑极端值
        if avg_daily_value <= 0:
            return 1.0  # 最高风险
        
        liquidity_score = 1.0 - np.log10(max(avg_daily_value, 1)) / 10.0
        return max(0.0, min(1.0, liquidity_score))


class RiskMonitor:
    """风险监控器"""
    
    def __init__(self, config: RiskConfig):
        self.config = config
        self.calculator = RiskIndicatorCalculator(config)
        self.risk_alerts: List[RiskAlert] = []
        self.portfolio_weights: Dict[str, float] = {}
        self.price_history: Dict[str, List[float]] = defaultdict(list)
        self.return_history: Dict[str, List[float]] = defaultdict(list)
        self.volume_history: Dict[str, List[float]] = defaultdict(list)
        
        # 数据目录
        self.data_dir = Path("data/risk_management")
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def update_portfolio_weights(self, weights: Dict[str, float]):
        """更新投资组合权重"""
        self.portfolio_weights = weights.copy()
        logger.info(f"更新投资组合权重: {weights}")
    
    def add_price_data(self, symbol: str, price: float, volume: float):
        """添加价格数据"""
        self.price_history[symbol].append(price)
        self.volume_history[symbol].append(volume)
        
        # 计算收益率
        if len(self.price_history[symbol]) > 1:
            prev_price = self.price_history[symbol][-2]
            if prev_price > 0:
                return_rate = (price - prev_price) / prev_price
                self.return_history[symbol].append(return_rate)
        
        # 保持历史数据在合理范围内
        max_length = self.config.lookback_days
        if len(self.price_history[symbol]) > max_length:
            self.price_history[symbol] = self.price_history[symbol][-max_length:]
        if len(self.return_history[symbol]) > max_length:
            self.return_history[symbol] = self.return_history[symbol][-max_length:]
        if len(self.volume_history[symbol]) > max_length:
            self.volume_history[symbol] = self.volume_history[symbol][-max_length:]
    
    def calculate_portfolio_risk_metrics(self) -> RiskMetrics:
        """计算投资组合风险指标"""
        if not self.return_history:
            logger.warning("没有收益率数据，无法计算风险指标")
            return RiskMetrics()
        
        # 计算投资组合收益率
        portfolio_returns = self._calculate_portfolio_returns()
        
        # 计算各项风险指标
        var_95 = self.calculator.calculate_var(portfolio_returns, 0.95)
        var_99 = self.calculator.calculate_var(portfolio_returns, 0.99)
        
        # 计算组合价格序列用于最大回撤
        portfolio_prices = self._calculate_portfolio_prices()
        max_drawdown = self.calculator.calculate_max_drawdown(portfolio_prices)
        
        volatility = self.calculator.calculate_volatility(portfolio_returns)
        sharpe_ratio = self.calculator.calculate_sharpe_ratio(portfolio_returns)
        
        # 计算相关性矩阵
        correlation_matrix = self.calculator.calculate_correlation_matrix(self.return_history)
        
        # 计算集中度风险
        concentration_risk = self.calculator.calculate_concentration_risk(self.portfolio_weights)
        
        # 计算流动性风险
        liquidity_risk = self._calculate_portfolio_liquidity_risk()
        
        return RiskMetrics(
            var_95=var_95,
            var_99=var_99,
            max_drawdown=max_drawdown,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            correlation_matrix=correlation_matrix,
            concentration_risk=concentration_risk,
            liquidity_risk=liquidity_risk,
            update_time=datetime.now()
        )
    
    def check_risk_thresholds(self, metrics: RiskMetrics) -> List[RiskAlert]:
        """检查风险阈值并生成预警"""
        alerts = []
        thresholds = self.config.risk_thresholds
        
        # 检查VaR
        if abs(metrics.var_95) > thresholds.max_var_95:
            alerts.append(RiskAlert(
                alert_id=f"var_95_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                risk_type=RiskType.PORTFOLIO,
                risk_level=RiskLevel.HIGH if abs(metrics.var_95) > thresholds.max_var_99 else RiskLevel.MEDIUM,
                message=f"投资组合VaR(95%)超限: {abs(metrics.var_95):.2%} > {thresholds.max_var_95:.2%}",
                current_value=abs(metrics.var_95),
                threshold_value=thresholds.max_var_95
            ))
        
        # 检查最大回撤
        if metrics.max_drawdown > thresholds.max_drawdown:
            alerts.append(RiskAlert(
                alert_id=f"drawdown_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                risk_type=RiskType.PORTFOLIO,
                risk_level=RiskLevel.HIGH if metrics.max_drawdown > thresholds.max_drawdown * 1.5 else RiskLevel.MEDIUM,
                message=f"最大回撤超限: {metrics.max_drawdown:.2%} > {thresholds.max_drawdown:.2%}",
                current_value=metrics.max_drawdown,
                threshold_value=thresholds.max_drawdown
            ))
        
        # 检查波动率
        if metrics.volatility > thresholds.max_volatility:
            alerts.append(RiskAlert(
                alert_id=f"volatility_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                risk_type=RiskType.PORTFOLIO,
                risk_level=RiskLevel.MEDIUM,
                message=f"波动率超限: {metrics.volatility:.2%} > {thresholds.max_volatility:.2%}",
                current_value=metrics.volatility,
                threshold_value=thresholds.max_volatility
            ))
        
        # 检查集中度风险
        if metrics.concentration_risk > thresholds.max_concentration:
            alerts.append(RiskAlert(
                alert_id=f"concentration_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                risk_type=RiskType.CONCENTRATION,
                risk_level=RiskLevel.HIGH,
                message=f"集中度风险超限: {metrics.concentration_risk:.2%} > {thresholds.max_concentration:.2%}",
                current_value=metrics.concentration_risk,
                threshold_value=thresholds.max_concentration
            ))
        
        # 检查流动性风险
        if metrics.liquidity_risk > 0.7:  # 流动性风险阈值使用固定值
            alerts.append(RiskAlert(
                alert_id=f"liquidity_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                risk_type=RiskType.LIQUIDITY,
                risk_level=RiskLevel.HIGH if metrics.liquidity_risk > 0.9 else RiskLevel.MEDIUM,
                message=f"流动性风险过高: {metrics.liquidity_risk:.2%}",
                current_value=metrics.liquidity_risk,
                threshold_value=0.7
            ))
        
        # 保存预警
        self.risk_alerts.extend(alerts)
        
        if alerts and self.config.enable_risk_alerts:
            self._save_risk_alerts(alerts)
            logger.warning(f"生成 {len(alerts)} 个风险预警")
        
        return alerts
    
    def _calculate_portfolio_returns(self) -> List[float]:
        """计算投资组合收益率"""
        if not self.return_history or not self.portfolio_weights:
            return []
        
        # 找出最短的收益率序列长度
        min_length = min(len(returns) for returns in self.return_history.values())
        if min_length == 0:
            return []
        
        portfolio_returns = []
        for i in range(min_length):
            daily_return = 0.0
            for symbol, weight in self.portfolio_weights.items():
                if symbol in self.return_history and i < len(self.return_history[symbol]):
                    daily_return += weight * self.return_history[symbol][i]
            portfolio_returns.append(daily_return)
        
        return portfolio_returns
    
    def _calculate_portfolio_prices(self) -> List[float]:
        """计算投资组合价格序列"""
        if not self.price_history or not self.portfolio_weights:
            return []
        
        # 找出最短的价格序列长度
        min_length = min(len(prices) for prices in self.price_history.values())
        if min_length == 0:
            return []
        
        portfolio_prices = []
        for i in range(min_length):
            daily_price = 0.0
            total_weight = 0.0
            for symbol, weight in self.portfolio_weights.items():
                if symbol in self.price_history and i < len(self.price_history[symbol]):
                    daily_price += weight * self.price_history[symbol][i]
                    total_weight += weight
            
            if total_weight > 0:
                portfolio_prices.append(daily_price / total_weight)
        
        return portfolio_prices
    
    def _calculate_portfolio_liquidity_risk(self) -> float:
        """计算投资组合流动性风险"""
        if not self.portfolio_weights:
            return 0.0
        
        weighted_liquidity_risk = 0.0
        total_weight = 0.0
        
        for symbol, weight in self.portfolio_weights.items():
            if symbol in self.price_history and symbol in self.volume_history:
                prices = self.price_history[symbol]
                volumes = self.volume_history[symbol]
                
                if prices and volumes:
                    liquidity_risk = self.calculator.calculate_liquidity_risk(volumes, prices)
                    weighted_liquidity_risk += weight * liquidity_risk
                    total_weight += weight
        
        if total_weight > 0:
            return weighted_liquidity_risk / total_weight
        
        return 0.0
    
    def _save_risk_alerts(self, alerts: List[RiskAlert]):
        """保存风险预警"""
        timestamp = datetime.now().strftime("%Y%m%d")
        filename = self.data_dir / f"risk_alerts_{timestamp}.json"
        
        # 读取现有预警
        existing_alerts = []
        if filename.exists():
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    existing_alerts = json.load(f)
            except Exception as e:
                logger.error(f"读取现有风险预警失败: {e}")
        
        # 添加新预警
        for alert in alerts:
            alert_data = {
                "alert_id": alert.alert_id,
                "risk_type": alert.risk_type.value,
                "risk_level": alert.risk_level.value,
                "stock_code": alert.stock_code,
                "message": alert.message,
                "current_value": alert.current_value,
                "threshold_value": alert.threshold_value,
                "timestamp": alert.timestamp.isoformat(),
                "is_resolved": alert.is_resolved
            }
            existing_alerts.append(alert_data)
        
        # 保存到文件
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(existing_alerts, f, ensure_ascii=False, indent=2)
        
        logger.info(f"风险预警已保存到文件: {filename}")


class DynamicStopLoss:
    """动态止损策略"""
    
    def __init__(self, config: RiskConfig):
        self.config = config
        self.stop_loss_levels: Dict[str, float] = {}
        self.trailing_stop_levels: Dict[str, float] = {}
        self.highest_prices: Dict[str, float] = {}
    
    def calculate_stop_loss_price(self, stock: StockInfo, purchase_price: float) -> float:
        """计算止损价格"""
        if self.config.strategy == RiskStrategy.CONSERVATIVE:
            # 保守型：严格止损
            return self._conservative_stop_loss(stock, purchase_price)
        elif self.config.strategy == RiskStrategy.BALANCED:
            # 平衡型：适中止损
            return self._balanced_stop_loss(stock, purchase_price)
        elif self.config.strategy == RiskStrategy.AGGRESSIVE:
            # 激进型：宽松止损
            return self._aggressive_stop_loss(stock, purchase_price)
        
        return purchase_price * 0.92  # 默认8%止损
    
    def update_trailing_stop(self, symbol: str, current_price: float):
        """更新移动止损"""
        # 初始化最高价
        if symbol not in self.highest_prices:
            self.highest_prices[symbol] = current_price
        
        # 更新最高价
        if current_price > self.highest_prices[symbol]:
            self.highest_prices[symbol] = current_price
            
            # 重新计算移动止损
            if self.config.strategy == RiskStrategy.CONSERVATIVE:
                trailing_percentage = 0.05  # 5%
            elif self.config.strategy == RiskStrategy.BALANCED:
                trailing_percentage = 0.08  # 8%
            else:  # AGGRESSIVE
                trailing_percentage = 0.12  # 12%
            
            self.trailing_stop_levels[symbol] = self.highest_prices[symbol] * (1 - trailing_percentage)
    
    def should_trigger_stop_loss(self, symbol: str, current_price: float) -> bool:
        """检查是否应该触发止损"""
        # 检查固定止损
        if symbol in self.stop_loss_levels and current_price <= self.stop_loss_levels[symbol]:
            return True
        
        # 检查移动止损
        if symbol in self.trailing_stop_levels and current_price <= self.trailing_stop_levels[symbol]:
            return True
        
        return False
    
    def _conservative_stop_loss(self, stock: StockInfo, purchase_price: float) -> float:
        """保守型止损策略"""
        # 基于技术位置和基本面的严格止损
        if stock.week_52_low > 0:
            # 止损设置在52周低点上方2%
            stop_loss = stock.week_52_low * 1.02
        else:
            # 默认5%止损
            stop_loss = purchase_price * 0.95
        
        # 如果估值过高，进一步收紧止损
        if stock.pe_ratio > 25 or stock.pb_ratio > 3:
            stop_loss = min(stop_loss, purchase_price * 0.93)
        
        return stop_loss
    
    def _balanced_stop_loss(self, stock: StockInfo, purchase_price: float) -> float:
        """平衡型止损策略"""
        # 基于技术位置和基本面的适中止损
        if stock.week_52_low > 0:
            # 止损设置在52周低点上方5%
            stop_loss = stock.week_52_low * 1.05
        else:
            # 默认8%止损
            stop_loss = purchase_price * 0.92
        
        # 如果估值过高，适度收紧止损
        if stock.pe_ratio > 30 or stock.pb_ratio > 4:
            stop_loss = min(stop_loss, purchase_price * 0.90)
        
        return stop_loss
    
    def _aggressive_stop_loss(self, stock: StockInfo, purchase_price: float) -> float:
        """激进型止损策略"""
        # 基于技术位置和基本面的宽松止损
        if stock.week_52_low > 0:
            # 止损设置在52周低点上方8%
            stop_loss = stock.week_52_low * 1.08
        else:
            # 默认12%止损
            stop_loss = purchase_price * 0.88
        
        # 只有在估值极高时才收紧止损
        if stock.pe_ratio > 40 or stock.pb_ratio > 6:
            stop_loss = min(stop_loss, purchase_price * 0.85)
        
        return stop_loss


class RiskReportGenerator:
    """风险报告生成器"""
    
    def __init__(self, config: RiskConfig):
        self.config = config
        
        # 报告目录
        self.reports_dir = Path("reports/risk_management")
        self.reports_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_risk_summary_report(self, metrics: RiskMetrics, alerts: List[RiskAlert]) -> str:
        """生成风险摘要报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.reports_dir / f"risk_summary_{timestamp}.json"
        
        # 统计预警信息
        alert_stats = {
            "total_alerts": len(alerts),
            "by_level": {},
            "by_type": {}
        }
        
        for alert in alerts:
            # 按风险等级统计
            level = alert.risk_level.value
            alert_stats["by_level"][level] = alert_stats["by_level"].get(level, 0) + 1
            
            # 按风险类型统计
            risk_type = alert.risk_type.value
            alert_stats["by_type"][risk_type] = alert_stats["by_type"].get(risk_type, 0) + 1
        
        # 构建报告数据
        report_data = {
            "report_type": "risk_summary",
            "timestamp": datetime.now().isoformat(),
            "risk_metrics": {
                "var_95": metrics.var_95,
                "var_99": metrics.var_99,
                "max_drawdown": metrics.max_drawdown,
                "volatility": metrics.volatility,
                "sharpe_ratio": metrics.sharpe_ratio,
                "concentration_risk": metrics.concentration_risk,
                "liquidity_risk": metrics.liquidity_risk
            },
            "risk_assessment": self._assess_overall_risk(metrics),
            "alert_statistics": alert_stats,
            "recent_alerts": [
                {
                    "alert_id": alert.alert_id,
                    "risk_type": alert.risk_type.value,
                    "risk_level": alert.risk_level.value,
                    "message": alert.message,
                    "timestamp": alert.timestamp.isoformat()
                }
                for alert in sorted(alerts, key=lambda x: x.timestamp, reverse=True)[:10]
            ]
        }
        
        # 保存报告
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"风险摘要报告已生成: {filename}")
        return str(filename)
    
    def generate_portfolio_risk_report(self, portfolio_weights: Dict[str, float], 
                                     metrics: RiskMetrics) -> str:
        """生成投资组合风险报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.reports_dir / f"portfolio_risk_{timestamp}.json"
        
        # 分析投资组合构成
        portfolio_analysis = {
            "total_positions": len(portfolio_weights),
            "top_holdings": sorted(portfolio_weights.items(), key=lambda x: x[1], reverse=True)[:10],
            "weight_distribution": {
                "largest_weight": max(portfolio_weights.values()) if portfolio_weights else 0,
                "smallest_weight": min(portfolio_weights.values()) if portfolio_weights else 0,
                "average_weight": sum(portfolio_weights.values()) / len(portfolio_weights) if portfolio_weights else 0
            }
        }
        
        # 构建报告数据
        report_data = {
            "report_type": "portfolio_risk",
            "timestamp": datetime.now().isoformat(),
            "portfolio_weights": portfolio_weights,
            "portfolio_analysis": portfolio_analysis,
            "risk_metrics": {
                "var_95": metrics.var_95,
                "var_99": metrics.var_99,
                "max_drawdown": metrics.max_drawdown,
                "volatility": metrics.volatility,
                "sharpe_ratio": metrics.sharpe_ratio,
                "beta": metrics.beta,
                "correlation_matrix": metrics.correlation_matrix,
                "concentration_risk": metrics.concentration_risk,
                "liquidity_risk": metrics.liquidity_risk
            },
            "risk_recommendations": self._generate_risk_recommendations(metrics)
        }
        
        # 保存报告
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"投资组合风险报告已生成: {filename}")
        return str(filename)
    
    def generate_individual_stock_risk_report(self, symbol: str, stock_info: StockInfo,
                                          price_history: List[float]) -> str:
        """生成个股风险报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.reports_dir / f"stock_risk_{symbol}_{timestamp}.json"
        
        # 计算个股风险指标
        calculator = RiskIndicatorCalculator(self.config)
        
        if len(price_history) > 1:
            returns = [(price_history[i] - price_history[i-1]) / price_history[i-1] 
                      for i in range(1, len(price_history))]
            
            var_95 = calculator.calculate_var(returns, 0.95)
            max_drawdown = calculator.calculate_max_drawdown(price_history)
            volatility = calculator.calculate_volatility(returns)
            sharpe_ratio = calculator.calculate_sharpe_ratio(returns)
        else:
            var_95 = max_drawdown = volatility = sharpe_ratio = 0.0
        
        # 构建报告数据
        report_data = {
            "report_type": "individual_stock_risk",
            "timestamp": datetime.now().isoformat(),
            "stock_info": {
                "code": stock_info.code,
                "name": stock_info.name,
                "price": stock_info.price,
                "dividend_yield": stock_info.dividend_yield,
                "pe_ratio": stock_info.pe_ratio,
                "pb_ratio": stock_info.pb_ratio,
                "eps": stock_info.eps,
                "book_value": stock_info.book_value,
                "week_52_high": stock_info.week_52_high,
                "week_52_low": stock_info.week_52_low
            },
            "risk_metrics": {
                "var_95": var_95,
                "max_drawdown": max_drawdown,
                "volatility": volatility,
                "sharpe_ratio": sharpe_ratio,
                "price_history_length": len(price_history)
            },
            "risk_assessment": self._assess_stock_risk(stock_info, var_95, max_drawdown, volatility)
        }
        
        # 保存报告
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"个股风险报告已生成: {filename}")
        return str(filename)
    
    def _assess_overall_risk(self, metrics: RiskMetrics) -> Dict[str, Any]:
        """评估整体风险水平"""
        risk_factors = []
        risk_score = 0
        
        # VaR评估
        if abs(metrics.var_95) > 0.08:
            risk_factors.append("VaR风险极高")
            risk_score += 30
        elif abs(metrics.var_95) > 0.05:
            risk_factors.append("VaR风险较高")
            risk_score += 20
        
        # 最大回撤评估
        if metrics.max_drawdown > 0.25:
            risk_factors.append("最大回撤风险极高")
            risk_score += 30
        elif metrics.max_drawdown > 0.15:
            risk_factors.append("最大回撤风险较高")
            risk_score += 20
        
        # 波动率评估
        if metrics.volatility > 0.30:
            risk_factors.append("波动率极高")
            risk_score += 20
        elif metrics.volatility > 0.20:
            risk_factors.append("波动率较高")
            risk_score += 10
        
        # 集中度风险评估
        if metrics.concentration_risk > 0.4:
            risk_factors.append("集中度风险极高")
            risk_score += 20
        elif metrics.concentration_risk > 0.25:
            risk_factors.append("集中度风险较高")
            risk_score += 10
        
        # 流动性风险评估
        if metrics.liquidity_risk > 0.8:
            risk_factors.append("流动性风险极高")
            risk_score += 20
        elif metrics.liquidity_risk > 0.6:
            risk_factors.append("流动性风险较高")
            risk_score += 10
        
        # 确定风险等级
        if risk_score >= 70:
            risk_level = "高风险"
        elif risk_score >= 40:
            risk_level = "中等风险"
        else:
            risk_level = "低风险"
        
        return {
            "risk_level": risk_level,
            "risk_score": risk_score,
            "risk_factors": risk_factors,
            "recommendation": "建议减仓" if risk_score >= 70 else "建议保持" if risk_score >= 40 else "可以加仓"
        }
    
    def _generate_risk_recommendations(self, metrics: RiskMetrics) -> List[str]:
        """生成风险控制建议"""
        recommendations = []
        
        if abs(metrics.var_95) > 0.05:
            recommendations.append("考虑降低投资组合风险暴露，减少高风险资产配置")
        
        if metrics.max_drawdown > 0.15:
            recommendations.append("设置更严格的止损策略，控制最大回撤")
        
        if metrics.volatility > 0.25:
            recommendations.append("增加低波动率资产，如债券或大盘蓝筹股")
        
        if metrics.sharpe_ratio < 0.5:
            recommendations.append("优化投资组合，提高风险调整后收益")
        
        if metrics.concentration_risk > 0.25:
            recommendations.append("分散投资，降低单一股票或行业集中度")
        
        if metrics.liquidity_risk > 0.6:
            recommendations.append("增加高流动性资产配置，降低流动性风险")
        
        if not recommendations:
            recommendations.append("当前风险水平适中，建议保持现有投资策略")
        
        return recommendations
    
    def _assess_stock_risk(self, stock_info: StockInfo, var_95: float, 
                         max_drawdown: float, volatility: float) -> Dict[str, Any]:
        """评估个股风险"""
        risk_factors = []
        risk_score = 0
        
        # 估值风险
        if stock_info.pe_ratio > 30:
            risk_factors.append("PE估值过高")
            risk_score += 15
        elif stock_info.pe_ratio > 20:
            risk_factors.append("PE估值偏高")
            risk_score += 10
        
        if stock_info.pb_ratio > 5:
            risk_factors.append("PB估值过高")
            risk_score += 15
        elif stock_info.pb_ratio > 3:
            risk_factors.append("PB估值偏高")
            risk_score += 10
        
        # 财务风险
        if stock_info.eps <= 0:
            risk_factors.append("每股收益为负")
            risk_score += 20
        
        # 技术风险
        if stock_info.week_52_low > 0 and stock_info.week_52_high > 0:
            position = (stock_info.price - stock_info.week_52_low) / (stock_info.week_52_high - stock_info.week_52_low)
            if position > 0.9:
                risk_factors.append("价格接近52周高点")
                risk_score += 10
            elif position < 0.1:
                risk_factors.append("价格接近52周低点")
                risk_score -= 5  # 接近低点降低风险评分
        
        # 统计风险
        if abs(var_95) > 0.06:
            risk_factors.append("个股VaR风险较高")
            risk_score += 15
        
        if max_drawdown > 0.30:
            risk_factors.append("历史最大回撤较大")
            risk_score += 15
        
        if volatility > 0.35:
            risk_factors.append("个股波动率较高")
            risk_score += 10
        
        # 确定风险等级
        if risk_score >= 50:
            risk_level = "高风险"
        elif risk_score >= 25:
            risk_level = "中等风险"
        else:
            risk_level = "低风险"
        
        return {
            "risk_level": risk_level,
            "risk_score": risk_score,
            "risk_factors": risk_factors,
            "recommendation": "建议回避" if risk_score >= 50 else "建议谨慎" if risk_score >= 25 else "可以考虑"
        }


# 风险管理器主类
class RiskManager:
    """风险管理器主类"""
    
    def __init__(self, config: Optional[RiskConfig] = None):
        self.config = config or RiskConfig()
        self.monitor = RiskMonitor(self.config)
        self.stop_loss = DynamicStopLoss(self.config)
        self.report_generator = RiskReportGenerator(self.config)
        
        logger.info(f"风险管理器初始化完成，策略: {self.config.strategy.value}")
    
    def update_portfolio_data(self, stocks: List[StockInfo], weights: Dict[str, float]):
        """更新投资组合数据"""
        # 更新权重
        self.monitor.update_portfolio_weights(weights)
        
        # 更新价格和成交量数据
        for stock in stocks:
            self.monitor.add_price_data(stock.code, stock.price, stock.volume)
    
    def assess_portfolio_risk(self) -> Tuple[RiskMetrics, List[RiskAlert]]:
        """评估投资组合风险"""
        # 计算风险指标
        metrics = self.monitor.calculate_portfolio_risk_metrics()
        
        # 检查风险阈值
        alerts = self.monitor.check_risk_thresholds(metrics)
        
        return metrics, alerts
    
    def generate_risk_reports(self, portfolio_weights: Dict[str, float], 
                            stocks: List[StockInfo]) -> Dict[str, str]:
        """生成风险报告"""
        # 评估投资组合风险
        metrics, alerts = self.assess_portfolio_risk()
        
        # 生成报告
        reports = {}
        
        # 生成风险摘要报告
        reports["summary"] = self.report_generator.generate_risk_summary_report(metrics, alerts)
        
        # 生成投资组合风险报告
        reports["portfolio"] = self.report_generator.generate_portfolio_risk_report(
            portfolio_weights, metrics
        )
        
        # 生成个股风险报告
        for stock in stocks:
            if stock.code in self.monitor.price_history:
                price_history = self.monitor.price_history[stock.code]
                reports[f"stock_{stock.code}"] = self.report_generator.generate_individual_stock_risk_report(
                    stock.code, stock, price_history
                )
        
        return reports
    
    def calculate_stop_loss(self, stock: StockInfo, purchase_price: float) -> float:
        """计算止损价格"""
        return self.stop_loss.calculate_stop_loss_price(stock, purchase_price)
    
    def update_trailing_stop(self, symbol: str, current_price: float):
        """更新移动止损"""
        self.stop_loss.update_trailing_stop(symbol, current_price)
    
    def check_stop_loss(self, symbol: str, current_price: float) -> bool:
        """检查是否触发止损"""
        return self.stop_loss.should_trigger_stop_loss(symbol, current_price)