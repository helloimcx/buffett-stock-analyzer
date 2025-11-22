"""
多因子评分系统
实现基于因子的股票评分框架
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from enum import Enum
import json
from ..models.stock import StockInfo


class Factor(ABC):
    """因子基类"""
    
    def __init__(self, name: str, weight: float = 1.0):
        """
        初始化因子
        
        Args:
            name: 因子名称
            weight: 因子权重，默认为1.0
        """
        self.name = name
        self.weight = weight
    
    @abstractmethod
    def calculate(self, stock: StockInfo) -> float:
        """
        计算因子得分
        
        Args:
            stock: 股票信息
            
        Returns:
            因子得分，范围应该在0-1之间
        """
        pass


class ValueFactor(Factor):
    """价值因子"""
    
    def __init__(self, weight: float = 1.0):
        super().__init__("value", weight)
    
    def calculate(self, stock: StockInfo) -> float:
        """计算价值因子得分"""
        # 基于P/E和P/B比率计算价值得分
        pe_score = 0.0
        pb_score = 0.0
        
        # P/E评分 (越低越好)
        if stock.pe_ratio > 0:
            if stock.pe_ratio < 15:
                pe_score = 1.0
            elif stock.pe_ratio < 25:
                pe_score = 0.7
            elif stock.pe_ratio < 35:
                pe_score = 0.4
            else:
                pe_score = 0.1
        
        # P/B评分 (越低越好)
        if stock.pb_ratio > 0:
            if stock.pb_ratio < 1.5:
                pb_score = 1.0
            elif stock.pb_ratio < 2.5:
                pb_score = 0.7
            elif stock.pb_ratio < 4.0:
                pb_score = 0.4
            else:
                pb_score = 0.1
        
        # 综合价值得分
        return (pe_score + pb_score) / 2


class GrowthFactor(Factor):
    """成长因子"""
    
    def __init__(self, weight: float = 1.0):
        super().__init__("growth", weight)
    
    def calculate(self, stock: StockInfo) -> float:
        """计算成长因子得分"""
        # 简化实现，基于EPS计算成长得分
        if stock.eps > 0:
            if stock.eps > 2.0:
                return 1.0
            elif stock.eps > 1.0:
                return 0.7
            elif stock.eps > 0.5:
                return 0.4
            else:
                return 0.1
        return 0.0


class QualityFactor(Factor):
    """质量因子"""
    
    def __init__(self, weight: float = 1.0):
        super().__init__("quality", weight)
    
    def calculate(self, stock: StockInfo) -> float:
        """计算质量因子得分"""
        # 基于账面价值和价格的关系计算质量得分
        if stock.book_value > 0:
            ratio = stock.price / stock.book_value
            if ratio < 1.0:
                return 1.0  # 价格低于账面价值，质量高
            elif ratio < 2.0:
                return 0.7
            elif ratio < 3.0:
                return 0.4
            else:
                return 0.1
        return 0.0


class MomentumFactor(Factor):
    """动量因子"""
    
    def __init__(self, weight: float = 1.0):
        super().__init__("momentum", weight)
    
    def calculate(self, stock: StockInfo) -> float:
        """计算动量因子得分"""
        # 基于价格变化计算动量得分
        change_pct = stock.change_pct
        if change_pct > 0:
            if change_pct > 5.0:
                return 1.0
            elif change_pct > 2.0:
                return 0.7
            elif change_pct > 0.0:
                return 0.4
        else:
            if change_pct > -2.0:
                return 0.3
            elif change_pct > -5.0:
                return 0.1
            else:
                return 0.0
        return 0.0


class DividendFactor(Factor):
    """股息因子"""
    
    def __init__(self, weight: float = 1.0):
        super().__init__("dividend", weight)
    
    def calculate(self, stock: StockInfo) -> float:
        """计算股息因子得分"""
        # 基于股息率计算股息得分
        dividend_yield = stock.dividend_yield
        if dividend_yield >= 4.0:
            return 1.0
        elif dividend_yield >= 2.5:
            return 0.7
        elif dividend_yield >= 1.5:
            return 0.4
        elif dividend_yield > 0:
            return 0.1
        else:
            return 0.0


class TechnicalFactor(Factor):
    """技术因子"""
    
    def __init__(self, weight: float = 1.0):
        super().__init__("technical", weight)
    
    def calculate(self, stock: StockInfo) -> float:
        """计算技术因子得分"""
        # 基于52周高低点位置计算技术得分
        high_52w = stock.week_52_high
        low_52w = stock.week_52_low
        current_price = stock.price
        
        if high_52w > 0 and low_52w > 0:
            position = (current_price - low_52w) / (high_52w - low_52w)
            # 接近低点得分更高
            if position < 0.2:
                return 1.0
            elif position < 0.4:
                return 0.7
            elif position < 0.7:
                return 0.4
            else:
                return 0.1
        return 0.5  # 没有数据时给中等分数


class SentimentFactor(Factor):
    """情绪因子"""
    
    def __init__(self, weight: float = 1.0):
        super().__init__("sentiment", weight)
    
    def calculate(self, stock: StockInfo) -> float:
        """计算情绪因子得分"""
        # 基于成交量计算情绪得分
        volume = stock.volume
        market_cap = stock.market_cap
        
        if market_cap > 0:
            volume_ratio = volume / market_cap
            if volume_ratio > 0.05:
                return 1.0  # 高成交量，情绪积极
            elif volume_ratio > 0.02:
                return 0.7
            elif volume_ratio > 0.01:
                return 0.4
            else:
                return 0.2
        return 0.5


class MultiFactorScorer:
    """多因子评分器"""
    
    def __init__(self):
        """初始化多因子评分器"""
        self.factors = []
    
    def add_factor(self, factor: Factor):
        """
        添加因子到评分器
        
        Args:
            factor: 要添加的因子
        """
        self.factors.append(factor)
    
    def calculate_score(self, stock: StockInfo) -> float:
        """
        计算股票的多因子综合评分
        
        Args:
            stock: 股票信息
            
        Returns:
            综合评分，范围在0-1之间
        """
        if not self.factors:
            return 0.0
        
        total_weight = sum(factor.weight for factor in self.factors)
        if total_weight == 0:
            return 0.0
        
        weighted_score = 0.0
        for factor in self.factors:
            factor_score = factor.calculate(stock)
            weighted_score += factor_score * factor.weight
        
        return weighted_score / total_weight
    
    def rank_stocks(self, stocks: list[StockInfo]) -> list[StockInfo]:
        """
        对股票进行评分和排序
        
        Args:
            stocks: 股票列表
            
        Returns:
            按评分降序排序的股票列表
        """
        for stock in stocks:
            stock.total_score = self.calculate_score(stock) * 100  # 转换为0-100分制
        
        # 按评分降序排序
        return sorted(stocks, key=lambda x: x.total_score, reverse=True)
    
    @classmethod
    def with_default_factors(cls) -> 'MultiFactorScorer':
        """
        创建包含默认因子的评分器
        
        Returns:
            配置了默认因子的多因子评分器
        """
        scorer = cls()
        
        # 添加默认因子，使用均衡权重
        scorer.add_factor(ValueFactor(weight=0.15))
        scorer.add_factor(GrowthFactor(weight=0.15))
        scorer.add_factor(QualityFactor(weight=0.15))
        scorer.add_factor(MomentumFactor(weight=0.10))
        scorer.add_factor(DividendFactor(weight=0.20))
        scorer.add_factor(TechnicalFactor(weight=0.15))
        scorer.add_factor(SentimentFactor(weight=0.10))
        
        return scorer
    
    @classmethod
    def with_custom_weights(cls, weights: dict[str, float]) -> 'MultiFactorScorer':
        """
        创建使用自定义权重的评分器
        
        Args:
            weights: 因子权重字典，键为因子名称，值为权重
            
        Returns:
            配置了自定义权重的多因子评分器
        """
        scorer = cls()
        
        # 因子名称到因子类的映射
        factor_classes = {
            "value": ValueFactor,
            "growth": GrowthFactor,
            "quality": QualityFactor,
            "momentum": MomentumFactor,
            "dividend": DividendFactor,
            "technical": TechnicalFactor,
            "sentiment": SentimentFactor
        }
        
        # 根据权重配置添加因子
        for factor_name, weight in weights.items():
            if factor_name in factor_classes:
                factor_class = factor_classes[factor_name]
                scorer.add_factor(factor_class(weight=weight))
        
        return scorer


class MultiFactorConfig:
    """多因子评分配置类"""
    
    def __init__(self, factors: Dict[str, Dict[str, Any]]):
        """
        初始化配置
        
        Args:
            factors: 因子配置字典，格式为 {因子名: {weight: 权重, enabled: 是否启用}}
        """
        self.factors = factors
        self._validate_config()
    
    def _validate_config(self):
        """验证配置的有效性"""
        total_weight = 0.0
        
        for factor_name, config in self.factors.items():
            weight = config.get("weight", 0.0)
            enabled = config.get("enabled", True)
            
            # 验证权重范围
            if weight < 0 or weight > 1:
                raise ValueError(f"因子 {factor_name} 的权重必须在0-1之间，当前值: {weight}")
            
            # 只计算启用因子的权重
            if enabled:
                total_weight += weight
        
        # 验证总权重
        if total_weight > 1.0:
            raise ValueError(f"启用因子的权重总和不能超过1，当前值: {total_weight}")
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Dict[str, Any]]) -> 'MultiFactorConfig':
        """
        从字典创建配置
        
        Args:
            config_dict: 配置字典
            
        Returns:
            MultiFactorConfig实例
        """
        return cls(config_dict)
    
    @classmethod
    def from_file(cls, file_path: str) -> 'MultiFactorConfig':
        """
        从JSON文件创建配置
        
        Args:
            file_path: 配置文件路径
            
        Returns:
            MultiFactorConfig实例
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            config_dict = json.load(f)
        return cls.from_dict(config_dict)


class FactorRegistry:
    """因子注册表，用于管理和创建因子实例"""
    
    _factor_classes = {}
    
    @classmethod
    def register(cls, name: str, factor_class):
        """
        注册因子类
        
        Args:
            name: 因子名称
            factor_class: 因子类
        """
        cls._factor_classes[name] = factor_class
    
    @classmethod
    def get_factor_class(cls, name: str):
        """
        获取因子类
        
        Args:
            name: 因子名称
            
        Returns:
            因子类
        """
        return cls._factor_classes.get(name)
    
    @classmethod
    def create_factor(cls, name: str, weight: float = 1.0, **kwargs):
        """
        创建因子实例
        
        Args:
            name: 因子名称
            weight: 因子权重
            **kwargs: 其他参数
            
        Returns:
            因子实例
        """
        factor_class = cls.get_factor_class(name)
        if factor_class is None:
            raise ValueError(f"未找到因子类: {name}")
        return factor_class(weight=weight, **kwargs)
    
    @classmethod
    def get_available_factors(cls) -> List[str]:
        """
        获取所有可用的因子名称
        
        Returns:
            因子名称列表
        """
        return list(cls._factor_classes.keys())


class FactorCombinationStrategy(Enum):
    """因子组合策略枚举"""
    WEIGHTED_AVERAGE = "weighted_average"
    GEOMETRIC_MEAN = "geometric_mean"
    MAXIMUM = "maximum"


class FactorPerformanceTracker:
    """因子性能跟踪器"""
    
    def __init__(self):
        """初始化性能跟踪器"""
        self._performance_data = {}
    
    def record_factor_performance(self, factor_name: str, score: float, return_rate: float):
        """
        记录因子性能
        
        Args:
            factor_name: 因子名称
            score: 因子得分
            return_rate: 收益率
        """
        if factor_name not in self._performance_data:
            self._performance_data[factor_name] = {
                "scores": [],
                "returns": []
            }
        
        self._performance_data[factor_name]["scores"].append(score)
        self._performance_data[factor_name]["returns"].append(return_rate)
    
    def get_factor_stats(self, factor_name: str) -> Dict[str, float]:
        """
        获取因子统计信息
        
        Args:
            factor_name: 因子名称
            
        Returns:
            统计信息字典
        """
        if factor_name not in self._performance_data:
            return {"count": 0, "avg_score": 0.0, "avg_return": 0.0}
        
        data = self._performance_data[factor_name]
        count = len(data["scores"])
        
        if count == 0:
            return {"count": 0, "avg_score": 0.0, "avg_return": 0.0}
        
        avg_score = sum(data["scores"]) / count
        avg_return = sum(data["returns"]) / count
        
        return {
            "count": count,
            "avg_score": avg_score,
            "avg_return": avg_return
        }
    
    def get_best_factor(self) -> Optional[str]:
        """
        获取平均收益最高的因子
        
        Returns:
            最佳因子名称
        """
        best_factor = None
        best_return = -float('inf')
        
        for factor_name in self._performance_data:
            stats = self.get_factor_stats(factor_name)
            if stats["avg_return"] > best_return:
                best_return = stats["avg_return"]
                best_factor = factor_name
        
        return best_factor


# 注册内置因子
FactorRegistry.register("value", ValueFactor)
FactorRegistry.register("growth", GrowthFactor)
FactorRegistry.register("quality", QualityFactor)
FactorRegistry.register("momentum", MomentumFactor)
FactorRegistry.register("dividend", DividendFactor)
FactorRegistry.register("technical", TechnicalFactor)
FactorRegistry.register("sentiment", SentimentFactor)


# 扩展MultiFactorScorer类以支持配置
def _from_config(cls, config: MultiFactorConfig) -> 'MultiFactorScorer':
    """
    从配置创建多因子评分器
    
    Args:
        config: 多因子配置
        
    Returns:
        配置好的多因子评分器
    """
    scorer = cls()
    
    for factor_name, factor_config in config.factors.items():
        if factor_config.get("enabled", True):
            weight = factor_config.get("weight", 1.0)
            factor = FactorRegistry.create_factor(factor_name, weight=weight)
            scorer.add_factor(factor)
    
    return scorer


def _with_legacy_weights(cls) -> 'MultiFactorScorer':
    """
    创建与旧系统兼容的评分器
    
    Returns:
        配置了兼容权重的多因子评分器
    """
    # 使用与旧InvestmentScorer相似的权重配置
    legacy_weights = {
        "dividend": 0.5,    # 股息因子权重最高
        "value": 0.25,      # 估值因子
        "technical": 0.15,  # 技术因子
        "quality": 0.1      # 质量因子
    }
    
    return cls.with_custom_weights(legacy_weights)


# 动态添加方法到MultiFactorScorer类
MultiFactorScorer.from_config = classmethod(_from_config)
MultiFactorScorer.with_legacy_weights = classmethod(_with_legacy_weights)