"""
市场环境识别机制
实现牛市、熊市、震荡市等不同市场环境的识别和分析
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from enum import Enum
import json
import math
import statistics
from pathlib import Path

from ..utils.logger import get_logger

logger = get_logger(__name__)


class MarketEnvironmentType(Enum):
    """市场环境类型枚举"""
    BULL = "bull"         # 牛市
    BEAR = "bear"         # 熊市
    SIDEWAYS = "sideways" # 震荡市
    UNDEFINED = "undefined" # 未定义


@dataclass
class MarketIndex:
    """市场指数数据结构"""
    code: str                    # 指数代码
    name: str                    # 指数名称
    price: float                 # 当前价格
    change_pct: float            # 涨跌幅
    volume: int                  # 成交量
    timestamp: datetime           # 时间戳
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "code": self.code,
            "name": self.name,
            "price": self.price,
            "change_pct": self.change_pct,
            "volume": self.volume,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class MarketEnvironment:
    """市场环境数据结构"""
    environment_type: MarketEnvironmentType  # 环境类型
    confidence: float                        # 置信度 (0-1)
    trend_direction: str                     # 趋势方向 (bullish/bearish/sideways)
    volatility_level: str                    # 波动率水平 (low/medium/high)
    sentiment_score: float                   # 情绪得分 (0-1)
    timestamp: datetime                      # 识别时间
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "environment_type": self.environment_type.value,
            "confidence": self.confidence,
            "trend_direction": self.trend_direction,
            "volatility_level": self.volatility_level,
            "sentiment_score": self.sentiment_score,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class MarketEnvironmentAlert:
    """市场环境预警"""
    alert_type: str                    # 预警类型
    previous_environment: MarketEnvironmentType  # 之前环境
    current_environment: MarketEnvironmentType   # 当前环境
    confidence: float                  # 置信度
    message: str                       # 预警消息
    timestamp: datetime                # 预警时间
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "alert_type": self.alert_type,
            "previous_environment": self.previous_environment.value,
            "current_environment": self.current_environment.value,
            "confidence": self.confidence,
            "message": self.message,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class MarketEnvironmentHistory:
    """市场环境历史记录"""
    index_code: str                   # 指数代码
    environment: MarketEnvironment    # 环境信息
    raw_data: Dict[str, Any]          # 原始数据
    timestamp: datetime               # 记录时间
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "index_code": self.index_code,
            "environment": self.environment.to_dict(),
            "raw_data": self.raw_data,
            "timestamp": self.timestamp.isoformat()
        }


class TrendAnalyzer:
    """趋势分析器"""
    
    def __init__(self, short_period: int = 5, medium_period: int = 20, long_period: int = 60):
        """
        初始化趋势分析器
        
        Args:
            short_period: 短期均线周期
            medium_period: 中期均线周期
            long_period: 长期均线周期
        """
        self.short_period = short_period
        self.medium_period = medium_period
        self.long_period = long_period
    
    def _calculate_moving_averages(self, prices: List[float]) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        """
        计算移动平均线
        
        Args:
            prices: 价格列表
            
        Returns:
            (短期均线, 中期均线, 长期均线)
        """
        # 如果数据不足，使用可用数据计算
        if len(prices) < self.short_period:
            logger.warning(f"价格数据不足，需要至少{self.short_period}个数据点，当前只有{len(prices)}个")
            return None, None, None
        
        # 计算移动平均线，如果数据不足则使用可用数据
        short_ma = statistics.mean(prices[-min(self.short_period, len(prices)):])
        
        if len(prices) >= self.medium_period:
            medium_ma = statistics.mean(prices[-self.medium_period:])
        else:
            medium_ma = None
            
        if len(prices) >= self.long_period:
            long_ma = statistics.mean(prices[-self.long_period:])
        else:
            long_ma = None
        
        return short_ma, medium_ma, long_ma
    
    def _calculate_trend_strength(self, prices: List[float]) -> float:
        """
        计算趋势强度
        
        Args:
            prices: 价格列表
            
        Returns:
            趋势强度 (0-1)
        """
        if len(prices) < self.long_period:
            return 0.0
        
        # 使用线性回归计算趋势强度
        n = len(prices)
        x = list(range(n))
        y = prices
        
        # 计算线性回归斜率
        x_mean = statistics.mean(x)
        y_mean = statistics.mean(y)
        
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0.0
        
        slope = numerator / denominator
        
        # 计算R²
        y_pred = [slope * (x[i] - x_mean) + y_mean for i in range(n)]
        ss_tot = sum((y[i] - y_mean) ** 2 for i in range(n))
        ss_res = sum((y[i] - y_pred[i]) ** 2 for i in range(n))
        
        if ss_tot == 0:
            return 0.0
        
        r_squared = 1 - (ss_res / ss_tot)
        
        # 将R²转换为趋势强度
        return max(0.0, min(1.0, r_squared))
    
    def identify_trend(self, prices: List[float]) -> Dict[str, Any]:
        """
        识别价格趋势
        
        Args:
            prices: 价格列表
            
        Returns:
            趋势分析结果
        """
        if len(prices) < self.short_period:
            logger.warning(f"价格数据不足，无法进行趋势分析")
            return {
                "direction": "undefined",
                "strength": 0.0,
                "short_ma": None,
                "medium_ma": None,
                "long_ma": None
            }
        
        # 计算移动平均线
        short_ma, medium_ma, long_ma = self._calculate_moving_averages(prices)
        
        # 计算趋势强度
        strength = self._calculate_trend_strength(prices)
        
        # 判断趋势方向
        if short_ma is None:
            direction = "undefined"
        elif medium_ma is not None and long_ma is not None:
            # 完整的均线数据
            if short_ma > medium_ma > long_ma:
                direction = "bullish"  # 牛市排列
            elif short_ma < medium_ma < long_ma:
                direction = "bearish"  # 熊市排列
            else:
                direction = "sideways"  # 震荡
        elif medium_ma is not None:
            # 只有短期和中期均线
            if short_ma > medium_ma:
                direction = "bullish"
            elif short_ma < medium_ma:
                direction = "bearish"
            else:
                direction = "sideways"
        else:
            # 只有短期均线，使用价格趋势
            if len(prices) >= 10:
                recent_prices = prices[-10:]
                if recent_prices[-1] > recent_prices[0]:
                    direction = "bullish"
                elif recent_prices[-1] < recent_prices[0]:
                    direction = "bearish"
                else:
                    direction = "sideways"
            else:
                direction = "undefined"
        
        return {
            "direction": direction,
            "strength": strength,
            "short_ma": short_ma,
            "medium_ma": medium_ma,
            "long_ma": long_ma
        }


class VolatilityAnalyzer:
    """波动率分析器"""
    
    def __init__(self, period: int = 20, low_threshold: float = 0.015, 
                 medium_threshold: float = 0.025, high_threshold: float = 0.035):
        """
        初始化波动率分析器
        
        Args:
            period: 计算周期
            low_threshold: 低波动率阈值
            medium_threshold: 中等波动率阈值
            high_threshold: 高波动率阈值
        """
        self.period = period
        self.low_threshold = low_threshold
        self.medium_threshold = medium_threshold
        self.high_threshold = high_threshold
    
    def _calculate_volatility(self, prices: List[float]) -> float:
        """
        计算价格波动率
        
        Args:
            prices: 价格列表
            
        Returns:
            波动率
        """
        if len(prices) < self.period:
            logger.warning(f"价格数据不足，无法计算波动率")
            return 0.0
        
        # 计算日收益率
        returns = []
        for i in range(1, len(prices)):
            if prices[i-1] != 0:
                ret = (prices[i] - prices[i-1]) / prices[i-1]
                returns.append(ret)
        
        if len(returns) < self.period:
            return 0.0
        
        # 使用最近period天的收益率计算波动率
        recent_returns = returns[-self.period:]
        volatility = statistics.stdev(recent_returns) if len(recent_returns) > 1 else 0.0
        
        return volatility
    
    def analyze_volatility(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析市场波动率
        
        Args:
            market_data: 市场数据，包含价格等信息
            
        Returns:
            波动率分析结果
        """
        # 支持直接传入波动率或从价格计算
        if "volatility" in market_data:
            volatility = market_data["volatility"]
        else:
            prices = market_data.get("prices", [])
            if not prices:
                logger.warning("缺少价格数据，无法分析波动率")
                return {
                    "level": "undefined",
                    "score": 0.0,
                    "volatility": 0.0
                }
            volatility = self._calculate_volatility(prices)
        
        # 判断波动率水平
        if volatility < self.low_threshold:
            level = "low"
            score = 0.8
        elif volatility < self.medium_threshold:
            level = "medium"
            score = 0.5
        elif volatility < self.high_threshold:
            level = "high"
            score = 0.3
        else:
            level = "extreme"
            score = 0.1
        
        return {
            "level": level,
            "score": score,
            "volatility": volatility
        }


class SentimentAnalyzer:
    """市场情绪分析器"""
    
    def __init__(self, volume_weight: float = 0.4, advance_decline_weight: float = 0.3, momentum_weight: float = 0.3):
        """
        初始化情绪分析器
        
        Args:
            volume_weight: 成交量权重
            advance_decline_weight: 涨跌比例权重
            momentum_weight: 动量权重
        """
        self.volume_weight = volume_weight
        self.advance_decline_weight = advance_decline_weight
        self.momentum_weight = momentum_weight
    
    def _analyze_volume_sentiment(self, market_data: Dict[str, Any]) -> float:
        """
        分析成交量情绪
        
        Args:
            market_data: 市场数据
            
        Returns:
            成交量情绪得分 (0-1)
        """
        current_volume = market_data.get("current_volume", 0)
        avg_volume = market_data.get("avg_volume", 1)
        
        if avg_volume <= 0:
            return 0.5
        
        volume_ratio = current_volume / avg_volume
        
        # 成交量比率越高，情绪越积极
        if volume_ratio > 2.0:
            return 0.9
        elif volume_ratio > 1.5:
            return 0.7
        elif volume_ratio > 1.0:
            return 0.6
        elif volume_ratio > 0.8:
            return 0.5
        elif volume_ratio > 0.5:
            return 0.3
        else:
            return 0.1
    
    def _analyze_advance_decline(self, market_data: Dict[str, Any]) -> float:
        """
        分析涨跌比例情绪
        
        Args:
            market_data: 市场数据
            
        Returns:
            涨跌比例情绪得分 (0-1)
        """
        advancing = market_data.get("advancing_stocks", 0)
        declining = market_data.get("declining_stocks", 0)
        
        total = advancing + declining
        if total == 0:
            return 0.5
        
        advance_ratio = advancing / total
        
        # 上涨股票比例越高，情绪越积极
        if advance_ratio > 0.7:
            return 0.9
        elif advance_ratio > 0.6:
            return 0.7
        elif advance_ratio > 0.5:
            return 0.6
        elif advance_ratio > 0.4:
            return 0.4
        elif advance_ratio > 0.3:
            return 0.3
        else:
            return 0.1
    
    def _analyze_momentum_sentiment(self, market_data: Dict[str, Any]) -> float:
        """
        分析动量情绪
        
        Args:
            market_data: 市场数据
            
        Returns:
            动量情绪得分 (0-1)
        """
        momentum = market_data.get("momentum", 0.0)
        
        # 动量越高，情绪越积极
        if momentum > 0.03:
            return 0.9
        elif momentum > 0.02:
            return 0.8
        elif momentum > 0.01:
            return 0.7
        elif momentum > 0.0:
            return 0.6
        elif momentum > -0.01:
            return 0.4
        elif momentum > -0.02:
            return 0.3
        elif momentum > -0.03:
            return 0.2
        else:
            return 0.1
    
    def calculate_overall_sentiment(self, market_data: Dict[str, Any]) -> float:
        """
        计算综合市场情绪
        
        Args:
            market_data: 市场数据
            
        Returns:
            综合情绪得分 (0-1)
        """
        volume_sentiment = self._analyze_volume_sentiment(market_data)
        advance_decline_sentiment = self._analyze_advance_decline(market_data)
        momentum_sentiment = self._analyze_momentum_sentiment(market_data)
        
        # 加权平均
        overall_sentiment = (
            volume_sentiment * self.volume_weight +
            advance_decline_sentiment * self.advance_decline_weight +
            momentum_sentiment * self.momentum_weight
        )
        
        return max(0.0, min(1.0, overall_sentiment))


class MarketEnvironmentIdentifier:
    """市场环境识别器"""
    
    def __init__(self, bull_threshold: float = 0.7, bear_threshold: float = 0.3):
        """
        初始化市场环境识别器
        
        Args:
            bull_threshold: 牛市阈值
            bear_threshold: 熊市阈值
        """
        self.trend_analyzer = TrendAnalyzer()
        self.volatility_analyzer = VolatilityAnalyzer()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.bull_threshold = bull_threshold
        self.bear_threshold = bear_threshold
    
    def _calculate_environment_score(self, trend_direction: str, volatility_level: str, sentiment_score: float) -> float:
        """
        计算环境评分
        
        Args:
            trend_direction: 趋势方向
            volatility_level: 波动率水平
            sentiment_score: 情绪得分
            
        Returns:
            环境评分 (0-1)
        """
        # 趋势权重
        trend_weight = 0.6  # 增加趋势权重
        volatility_weight = 0.15
        sentiment_weight = 0.25
        
        # 趋势得分
        if trend_direction == "bullish":
            trend_score = 0.9
        elif trend_direction == "bearish":
            trend_score = 0.1
        elif trend_direction == "sideways":
            trend_score = 0.5
        else:
            trend_score = 0.5
        
        # 波动率得分
        if volatility_level == "low":
            volatility_score = 0.6
        elif volatility_level == "medium":
            volatility_score = 0.5
        elif volatility_level == "high":
            volatility_score = 0.4
        elif volatility_level == "extreme":
            volatility_score = 0.2
        else:
            volatility_score = 0.5
        
        # 综合评分
        total_score = (
            trend_score * trend_weight +
            volatility_score * volatility_weight +
            sentiment_score * sentiment_weight
        )
        
        return max(0.0, min(1.0, total_score))
    
    def identify_environment(self, market_data: Dict[str, Any]) -> MarketEnvironment:
        """
        识别市场环境
        
        Args:
            market_data: 市场数据
            
        Returns:
            市场环境
        """
        # 趋势分析
        trend_result = self.trend_analyzer.identify_trend(market_data.get("prices", []))
        
        # 波动率分析
        volatility_result = self.volatility_analyzer.analyze_volatility(market_data)
        
        # 情绪分析
        sentiment_score = self.sentiment_analyzer.calculate_overall_sentiment(market_data)
        
        # 计算环境评分
        environment_score = self._calculate_environment_score(
            trend_result["direction"],
            volatility_result["level"],
            sentiment_score
        )
        
        # 确定市场环境类型
        if environment_score >= self.bull_threshold:
            environment_type = MarketEnvironmentType.BULL
        elif environment_score <= self.bear_threshold:
            environment_type = MarketEnvironmentType.BEAR
        else:
            environment_type = MarketEnvironmentType.SIDEWAYS
        
        # 计算置信度，基于趋势强度和环境评分的一致性
        trend_strength = trend_result.get("strength", 0.0)
        base_confidence = max(0.5, environment_score)
        
        # 如果趋势强度高，提高置信度
        if trend_strength > 0.7:
            confidence = min(1.0, base_confidence + 0.2)
        elif trend_strength > 0.5:
            confidence = min(1.0, base_confidence + 0.1)
        else:
            confidence = base_confidence
        
        return MarketEnvironment(
            environment_type=environment_type,
            confidence=confidence,
            trend_direction=trend_result["direction"],
            volatility_level=volatility_result["level"],
            sentiment_score=sentiment_score,
            timestamp=datetime.now()
        )
    
    def detect_environment_change(self, previous_env: MarketEnvironment, current_env: MarketEnvironment) -> bool:
        """
        检测环境变化
        
        Args:
            previous_env: 之前环境
            current_env: 当前环境
            
        Returns:
            是否发生环境变化
        """
        return previous_env.environment_type != current_env.environment_type
    
    def generate_change_alert(self, previous_env: MarketEnvironment, current_env: MarketEnvironment) -> MarketEnvironmentAlert:
        """
        生成环境变化预警
        
        Args:
            previous_env: 之前环境
            current_env: 当前环境
            
        Returns:
            环境变化预警
        """
        # 生成预警消息
        prev_name = {
            MarketEnvironmentType.BULL: "牛市",
            MarketEnvironmentType.BEAR: "熊市",
            MarketEnvironmentType.SIDEWAYS: "震荡市",
            MarketEnvironmentType.UNDEFINED: "未定义"
        }.get(previous_env.environment_type, "未知")
        
        curr_name = {
            MarketEnvironmentType.BULL: "牛市",
            MarketEnvironmentType.BEAR: "熊市",
            MarketEnvironmentType.SIDEWAYS: "震荡市",
            MarketEnvironmentType.UNDEFINED: "未定义"
        }.get(current_env.environment_type, "未知")
        
        message = f"市场环境从{prev_name}转为{curr_name}，当前置信度为{current_env.confidence:.2f}"
        
        return MarketEnvironmentAlert(
            alert_type="market_change",
            previous_environment=previous_env.environment_type,
            current_environment=current_env.environment_type,
            confidence=current_env.confidence,
            message=message,
            timestamp=datetime.now()
        )


class MarketEnvironmentStorage:
    """市场环境历史数据存储"""
    
    def __init__(self, data_dir: str = "data/market_environment"):
        """
        初始化存储
        
        Args:
            data_dir: 数据目录
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def save_environment_record(self, record: MarketEnvironmentHistory) -> bool:
        """
        保存环境记录
        
        Args:
            record: 环境记录
            
        Returns:
            是否保存成功
        """
        try:
            # 按日期分组存储
            date_str = record.timestamp.strftime("%Y%m%d")
            filename = self.data_dir / f"environment_{date_str}.json"
            
            # 读取现有记录
            records = []
            if filename.exists():
                with open(filename, 'r', encoding='utf-8') as f:
                    records = json.load(f)
            
            # 添加新记录
            records.append(record.to_dict())
            
            # 保存到文件
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(records, f, ensure_ascii=False, indent=2)
            
            logger.info(f"环境记录已保存: {record.index_code} - {record.environment.environment_type.value}")
            return True
            
        except Exception as e:
            logger.error(f"保存环境记录失败: {e}")
            return False
    
    def get_environment_history(self, index_code: str, days: int = 30) -> List[MarketEnvironmentHistory]:
        """
        获取环境历史记录
        
        Args:
            index_code: 指数代码
            days: 天数
            
        Returns:
            环境历史记录列表
        """
        records = []
        
        try:
            # 获取最近几天的文件
            for i in range(days):
                date = datetime.now() - timedelta(days=i)
                date_str = date.strftime("%Y%m%d")
                filename = self.data_dir / f"environment_{date_str}.json"
                
                if filename.exists():
                    with open(filename, 'r', encoding='utf-8') as f:
                        day_records = json.load(f)
                    
                    # 筛选指定指数的记录
                    for record_data in day_records:
                        if record_data["index_code"] == index_code:
                            # 重建MarketEnvironment对象
                            env_data = record_data["environment"]
                            environment = MarketEnvironment(
                                environment_type=MarketEnvironmentType(env_data["environment_type"]),
                                confidence=env_data["confidence"],
                                trend_direction=env_data["trend_direction"],
                                volatility_level=env_data["volatility_level"],
                                sentiment_score=env_data["sentiment_score"],
                                timestamp=datetime.fromisoformat(env_data["timestamp"])
                            )
                            
                            # 重建历史记录对象
                            history = MarketEnvironmentHistory(
                                index_code=record_data["index_code"],
                                environment=environment,
                                raw_data=record_data["raw_data"],
                                timestamp=datetime.fromisoformat(record_data["timestamp"])
                            )
                            
                            records.append(history)
            
            # 按时间排序
            records.sort(key=lambda x: x.timestamp, reverse=True)
            
        except Exception as e:
            logger.error(f"获取环境历史记录失败: {e}")
        
        return records


# 导入timedelta用于日期计算
from datetime import timedelta