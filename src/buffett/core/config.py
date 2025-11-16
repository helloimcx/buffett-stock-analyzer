"""
配置管理
统一管理应用配置和参数
"""

import os
from dataclasses import dataclass


@dataclass
class DataConfig:
    """数据源配置"""
    request_delay: float = 0.2  # 请求间隔（秒）
    timeout: int = 30  # 超时时间（秒）
    max_retries: int = 3  # 最大重试次数


@dataclass
class ScoringConfig:
    """评分系统配置"""
    dividend_weight: float = 0.5  # 股息率权重（提高）
    valuation_weight: float = 0.25  # 估值权重
    technical_weight: float = 0.15  # 技术权重
    fundamental_weight: float = 0.1  # 基本面权重

    # 股息率评分标准（降低阈值）
    high_dividend_threshold: float = 4.0  # 高股息阈值（降低）
    medium_dividend_threshold: float = 2.5  # 中等股息阈值（降低）
    low_dividend_threshold: float = 1.5  # 低股息阈值（新增）

    # 估值评分标准（放宽条件）
    low_pe_threshold: float = 20.0  # 低P/E阈值（放宽）
    medium_pe_threshold: float = 35.0  # 中等P/E阈值（放宽）
    low_pb_threshold: float = 2.0  # 低P/B阈值（放宽）
    medium_pb_threshold: float = 4.0  # 中等P/B阈值（放宽）

    # 技术位置评分标准
    oversold_threshold: float = 0.4  # 超卖阈值（放宽）
    neutral_threshold: float = 0.8  # 中性阈值（放宽）


@dataclass
class AppConfig:
    """应用配置"""
    data: DataConfig
    scoring: ScoringConfig
    reports_dir: str = "reports"

    @classmethod
    def default(cls) -> 'AppConfig':
        """创建默认配置"""
        return cls(
            data=DataConfig(),
            scoring=ScoringConfig()
        )

    @classmethod
    def from_env(cls) -> 'AppConfig':
        """从环境变量创建配置"""
        return cls(
            data=DataConfig(
                request_delay=float(os.getenv('BUFFETT_REQUEST_DELAY', '0.2')),
                timeout=int(os.getenv('BUFFETT_TIMEOUT', '30')),
                max_retries=int(os.getenv('BUFFETT_MAX_RETRIES', '3'))
            ),
            scoring=ScoringConfig(
                dividend_weight=float(os.getenv('BUFFETT_DIVIDEND_WEIGHT', '0.5')),
                valuation_weight=float(os.getenv('BUFFETT_VALUATION_WEIGHT', '0.25')),
                technical_weight=float(os.getenv('BUFFETT_TECHNICAL_WEIGHT', '0.15')),
                fundamental_weight=float(os.getenv('BUFFETT_FUNDAMENTAL_WEIGHT', '0.1'))
            ),
            reports_dir=os.getenv('BUFFETT_REPORTS_DIR', 'reports')
        )


# 全局配置实例
config = AppConfig.default()