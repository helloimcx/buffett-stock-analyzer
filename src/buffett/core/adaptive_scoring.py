"""
自适应评分系统
根据市场环境动态调整多因子评分权重
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import json
from pathlib import Path

from .market_environment import (
    MarketEnvironment, MarketEnvironmentType, MarketEnvironmentIdentifier,
    MarketEnvironmentStorage, MarketEnvironmentHistory
)
from .multi_factor_scoring import MultiFactorScorer, Factor, FactorRegistry
from ..models.stock import StockInfo
from ..utils.logger import get_logger

logger = get_logger(__name__)


class AdaptiveWeightConfig:
    """自适应权重配置"""
    
    def __init__(self):
        """初始化权重配置"""
        # 默认权重配置
        self.default_weights = {
            "value": 0.15,
            "growth": 0.15,
            "quality": 0.15,
            "momentum": 0.10,
            "dividend": 0.20,
            "technical": 0.15,
            "sentiment": 0.10
        }
        
        # 市场环境特定权重配置
        self.environment_weights = {
            MarketEnvironmentType.BULL: {
                "value": 0.10,      # 牛市降低价值因子权重
                "growth": 0.25,     # 牛市提高成长因子权重
                "quality": 0.10,    # 牛市降低质量因子权重
                "momentum": 0.20,   # 牛市提高动量因子权重
                "dividend": 0.15,   # 牛市降低股息因子权重
                "technical": 0.15,  # 保持技术因子权重
                "sentiment": 0.05   # 牛市降低情绪因子权重
            },
            MarketEnvironmentType.BEAR: {
                "value": 0.20,      # 熊市提高价值因子权重
                "growth": 0.05,     # 熊市降低成长因子权重
                "quality": 0.25,    # 熊市提高质量因子权重
                "momentum": 0.05,   # 熊市降低动量因子权重
                "dividend": 0.25,    # 熊市提高股息因子权重
                "technical": 0.10,   # 熊市降低技术因子权重
                "sentiment": 0.10   # 保持情绪因子权重
            },
            MarketEnvironmentType.SIDEWAYS: {
                "value": 0.15,      # 震荡市保持均衡
                "growth": 0.15,
                "quality": 0.15,
                "momentum": 0.15,    # 震荡市提高动量因子权重
                "dividend": 0.15,
                "technical": 0.15,   # 震荡市提高技术因子权重
                "sentiment": 0.10
            }
        }
    
    def get_weights_for_environment(self, environment: MarketEnvironmentType) -> Dict[str, float]:
        """
        根据市场环境获取权重配置
        
        Args:
            environment: 市场环境类型
            
        Returns:
            权重配置字典
        """
        return self.environment_weights.get(environment, self.default_weights)
    
    def calculate_adaptive_weights(self, environment: MarketEnvironment, confidence: float = 1.0) -> Dict[str, float]:
        """
        计算自适应权重
        
        Args:
            environment: 市场环境
            confidence: 环境识别置信度
            
        Returns:
            自适应权重字典
        """
        # 获取环境特定权重
        env_weights = self.get_weights_for_environment(environment.environment_type)
        
        # 根据置信度调整权重
        if confidence < 1.0:
            # 置信度低时，向默认权重回归
            adaptive_weights = {}
            for factor in self.default_weights:
                env_weight = env_weights.get(factor, 0.0)
                default_weight = self.default_weights[factor]
                # 线性插值
                adaptive_weights[factor] = env_weight * confidence + default_weight * (1 - confidence)
            return adaptive_weights
        
        return env_weights


class AdaptiveMultiFactorScorer:
    """自适应多因子评分器"""
    
    def __init__(self, market_identifier: Optional[MarketEnvironmentIdentifier] = None):
        """
        初始化自适应评分器
        
        Args:
            market_identifier: 市场环境识别器
        """
        self.market_identifier = market_identifier or MarketEnvironmentIdentifier()
        self.weight_config = AdaptiveWeightConfig()
        self.environment_storage = MarketEnvironmentStorage()
        self.current_environment: Optional[MarketEnvironment] = None
        self.last_update: Optional[datetime] = None
    
    def update_market_environment(self, market_data: Dict[str, Any]) -> MarketEnvironment:
        """
        更新市场环境
        
        Args:
            market_data: 市场数据
            
        Returns:
            当前市场环境
        """
        # 识别市场环境
        self.current_environment = self.market_identifier.identify_environment(market_data)
        self.last_update = datetime.now()
        
        # 保存环境记录
        history = MarketEnvironmentHistory(
            index_code="market",
            environment=self.current_environment,
            raw_data=market_data,
            timestamp=self.last_update
        )
        self.environment_storage.save_environment_record(history)
        
        logger.info(f"市场环境已更新: {self.current_environment.environment_type.value}, "
                   f"置信度: {self.current_environment.confidence:.2f}")
        
        return self.current_environment
    
    def create_adaptive_scorer(self, environment: Optional[MarketEnvironment] = None) -> MultiFactorScorer:
        """
        创建自适应评分器
        
        Args:
            environment: 市场环境，如果为None则使用当前环境
            
        Returns:
            配置好的多因子评分器
        """
        if environment is None:
            environment = self.current_environment
        
        if environment is None:
            # 如果没有环境信息，使用默认权重
            logger.warning("没有市场环境信息，使用默认权重")
            return MultiFactorScorer.with_custom_weights(self.weight_config.default_weights)
        
        # 计算自适应权重
        adaptive_weights = self.weight_config.calculate_adaptive_weights(
            environment, environment.confidence
        )
        
        # 创建评分器
        scorer = MultiFactorScorer.with_custom_weights(adaptive_weights)
        
        logger.info(f"创建自适应评分器，环境: {environment.environment_type.value}, "
                   f"权重: {adaptive_weights}")
        
        return scorer
    
    def calculate_adaptive_score(self, stock: StockInfo, 
                                 environment: Optional[MarketEnvironment] = None) -> float:
        """
        计算自适应评分
        
        Args:
            stock: 股票信息
            environment: 市场环境
            
        Returns:
            自适应评分
        """
        scorer = self.create_adaptive_scorer(environment)
        return scorer.calculate_score(stock)
    
    def rank_stocks_adaptive(self, stocks: List[StockInfo], 
                           environment: Optional[MarketEnvironment] = None) -> List[StockInfo]:
        """
        使用自适应评分对股票进行排序
        
        Args:
            stocks: 股票列表
            environment: 市场环境
            
        Returns:
            排序后的股票列表
        """
        scorer = self.create_adaptive_scorer(environment)
        return scorer.rank_stocks(stocks)
    
    def get_environment_analysis(self) -> Dict[str, Any]:
        """
        获取环境分析报告
        
        Returns:
            环境分析报告
        """
        if self.current_environment is None:
            return {
                "status": "no_environment_data",
                "message": "没有市场环境数据"
            }
        
        # 获取当前权重
        current_weights = self.weight_config.calculate_adaptive_weights(
            self.current_environment, self.current_environment.confidence
        )
        
        # 获取默认权重
        default_weights = self.weight_config.default_weights
        
        # 计算权重变化
        weight_changes = {}
        for factor in default_weights:
            current = current_weights.get(factor, 0.0)
            default = default_weights[factor]
            change = current - default
            weight_changes[factor] = {
                "default": default,
                "current": current,
                "change": change,
                "change_pct": (change / default * 100) if default > 0 else 0
            }
        
        return {
            "status": "active",
            "environment": self.current_environment.to_dict(),
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "weights": {
                "default": default_weights,
                "current": current_weights,
                "changes": weight_changes
            },
            "recommendations": self._generate_recommendations()
        }
    
    def _generate_recommendations(self) -> List[str]:
        """
        生成投资建议
        
        Returns:
            建议列表
        """
        if self.current_environment is None:
            return ["需要先识别市场环境"]
        
        recommendations = []
        env_type = self.current_environment.environment_type
        
        if env_type == MarketEnvironmentType.BULL:
            recommendations.extend([
                "牛市环境：建议增加成长因子和动量因子权重",
                "关注高成长性股票，但注意控制风险",
                "可适当降低对估值的要求，关注盈利增长"
            ])
        elif env_type == MarketEnvironmentType.BEAR:
            recommendations.extend([
                "熊市环境：建议增加价值因子和质量因子权重",
                "重点关注低估值、高质量、高股息的防御性股票",
                "提高安全边际，避免高估值股票"
            ])
        elif env_type == MarketEnvironmentType.SIDEWAYS:
            recommendations.extend([
                "震荡市环境：建议均衡配置各因子",
                "增加技术因子权重，把握短期交易机会",
                "保持适中仓位，灵活调整"
            ])
        
        # 根据置信度添加建议
        confidence = self.current_environment.confidence
        if confidence < 0.6:
            recommendations.append(
                f"环境识别置信度较低({confidence:.2f})，建议谨慎调整策略"
            )
        
        return recommendations
    
    def save_config(self, file_path: str) -> bool:
        """
        保存配置到文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否保存成功
        """
        try:
            config_data = {
                "default_weights": self.weight_config.default_weights,
                "environment_weights": {
                    env_type.value: weights 
                    for env_type, weights in self.weight_config.environment_weights.items()
                }
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"配置已保存到: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            return False
    
    def load_config(self, file_path: str) -> bool:
        """
        从文件加载配置
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否加载成功
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # 更新默认权重
            if "default_weights" in config_data:
                self.weight_config.default_weights = config_data["default_weights"]
            
            # 更新环境权重
            if "environment_weights" in config_data:
                env_weights = {}
                for env_str, weights in config_data["environment_weights"].items():
                    env_type = MarketEnvironmentType(env_str)
                    env_weights[env_type] = weights
                self.weight_config.environment_weights = env_weights
            
            logger.info(f"配置已从文件加载: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
            return False


class MarketEnvironmentMonitor:
    """市场环境监控器"""
    
    def __init__(self, adaptive_scorer: AdaptiveMultiFactorScorer):
        """
        初始化监控器
        
        Args:
            adaptive_scorer: 自适应评分器
        """
        self.adaptive_scorer = adaptive_scorer
        self.storage = MarketEnvironmentStorage()
        self.alert_callbacks = []
    
    def add_alert_callback(self, callback):
        """
        添加预警回调
        
        Args:
            callback: 回调函数
        """
        self.alert_callbacks.append(callback)
    
    def monitor_and_update(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        监控并更新市场环境
        
        Args:
            market_data: 市场数据
            
        Returns:
            监控结果
        """
        # 保存之前的环境
        previous_environment = self.adaptive_scorer.current_environment
        
        # 更新市场环境
        current_environment = self.adaptive_scorer.update_market_environment(market_data)
        
        # 检测环境变化
        change_detected = False
        alert = None
        
        if previous_environment is not None:
            change_detected = self.adaptive_scorer.market_identifier.detect_environment_change(
                previous_environment, current_environment
            )
            
            if change_detected:
                alert = self.adaptive_scorer.market_identifier.generate_change_alert(
                    previous_environment, current_environment
                )
                
                # 触发预警回调
                for callback in self.alert_callbacks:
                    try:
                        callback(alert)
                    except Exception as e:
                        logger.error(f"预警回调执行失败: {e}")
        
        return {
            "previous_environment": previous_environment.to_dict() if previous_environment else None,
            "current_environment": current_environment.to_dict(),
            "change_detected": change_detected,
            "alert": alert.to_dict() if alert else None,
            "adaptive_weights": self.adaptive_scorer.weight_config.calculate_adaptive_weights(
                current_environment, current_environment.confidence
            )
        }
    
    def get_environment_history(self, days: int = 30) -> List[MarketEnvironmentHistory]:
        """
        获取环境历史记录
        
        Args:
            days: 天数
            
        Returns:
            历史记录列表
        """
        return self.storage.get_environment_history("market", days)