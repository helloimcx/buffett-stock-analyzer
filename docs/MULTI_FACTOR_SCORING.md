# 多因子评分系统

## 概述

多因子评分系统是巴菲特股息筛选器的新一代评分框架，采用模块化设计，支持灵活的因子组合和权重配置。系统遵循测试驱动开发（TDD）方法，确保代码质量和可靠性。

## 主要特性

### 🎯 核心功能
- **模块化因子设计**：每个因子独立实现，易于扩展和维护
- **灵活权重配置**：支持动态调整因子权重
- **多种配置方式**：支持代码配置、文件配置和运行时配置
- **向后兼容**：与现有InvestmentScorer完全兼容

### 📊 内置因子
- **价值因子（Value）**：基于P/E、P/B比率评估股票价值
- **成长因子（Growth）**：基于EPS等指标评估成长性
- **质量因子（Quality）**：基于账面价值等评估公司质量
- **动量因子（Momentum）**：基于价格变化评估市场动量
- **股息因子（Dividend）**：基于股息率评估收益能力
- **技术因子（Technical）**：基于52周高低点评估技术位置
- **情绪因子（Sentiment）**：基于成交量等评估市场情绪

### 🔧 扩展性
- **自定义因子**：支持注册和使用自定义因子
- **动态加载**：支持运行时动态创建和加载因子
- **性能跟踪**：内置因子性能统计和分析功能

## 快速开始

### 基本使用

```python
from src.buffett.core.multi_factor_scoring import MultiFactorScorer
from src.buffett.models.stock import StockInfo

# 创建默认配置的多因子评分器
scorer = MultiFactorScorer.with_default_factors()

# 创建股票数据
stock = StockInfo(
    code="TEST", name="测试股票", price=10.0, dividend_yield=3.0,
    pe_ratio=20.0, pb_ratio=2.0, change_pct=1.0, volume=1000000,
    market_cap=1000000000.0, eps=1.5, book_value=12.0,
    week_52_high=12.0, week_52_low=8.0
)

# 计算评分
score = scorer.calculate_score(stock)
print(f"股票评分: {score * 100:.2f}分")

# 批量排序
stocks = [stock1, stock2, stock3]
ranked_stocks = scorer.rank_stocks(stocks)
```

### 自定义权重

```python
# 创建自定义权重配置
custom_weights = {
    "dividend": 0.5,    # 股息因子权重50%
    "value": 0.3,       # 价值因子权重30%
    "technical": 0.2     # 技术因子权重20%
}

# 使用自定义权重
scorer = MultiFactorScorer.with_custom_weights(custom_weights)
```

### 配置文件

```python
from src.buffett.core.multi_factor_scoring import MultiFactorConfig, MultiFactorScorer

# 从配置文件创建评分器
config = MultiFactorConfig.from_file("config.json")
scorer = MultiFactorScorer.from_config(config)
```

配置文件格式（JSON）：
```json
{
    "dividend": {"weight": 0.4, "enabled": true},
    "value": {"weight": 0.3, "enabled": true},
    "growth": {"weight": 0.2, "enabled": true},
    "technical": {"weight": 0.1, "enabled": true},
    "quality": {"weight": 0.0, "enabled": false},
    "momentum": {"weight": 0.0, "enabled": false},
    "sentiment": {"weight": 0.0, "enabled": false}
}
```

## 高级功能

### 自定义因子

```python
from src.buffett.core.multi_factor_scoring import Factor, FactorRegistry

class CustomFactor(Factor):
    def __init__(self, weight=1.0):
        super().__init__("custom", weight)
    
    def calculate(self, stock: StockInfo) -> float:
        # 自定义计算逻辑
        return 0.8

# 注册自定义因子
FactorRegistry.register("custom", CustomFactor)

# 使用自定义因子
scorer = MultiFactorScorer()
scorer.add_factor(CustomFactor(weight=0.3))
```

### 兼容模式

```python
# 创建与旧系统兼容的评分器
legacy_scorer = MultiFactorScorer.with_legacy_weights()

# 完全替代旧系统
from src.buffett.core.scoring import InvestmentScorer

old_scorer = InvestmentScorer()
new_scorer = MultiFactorScorer.with_legacy_weights()

# 两个评分器会产生相似的结果
```

### 性能跟踪

```python
from src.buffett.core.multi_factor_scoring import FactorPerformanceTracker

tracker = FactorPerformanceTracker()

# 记录因子性能
tracker.record_factor_performance("dividend", 0.8, 0.05)
tracker.record_factor_performance("value", 0.6, 0.03)

# 获取统计信息
stats = tracker.get_factor_stats("dividend")
best_factor = tracker.get_best_factor()
```

## 架构设计

### 核心组件

1. **Factor（因子基类）**：定义因子接口和基本功能
2. **MultiFactorScorer（多因子评分器）**：协调多个因子进行综合评分
3. **FactorRegistry（因子注册表）**：管理因子类的注册和创建
4. **MultiFactorConfig（配置管理）**：处理配置文件和验证
5. **FactorPerformanceTracker（性能跟踪）**：统计和分析因子性能

### 设计原则

- **单一职责**：每个类只负责一个特定功能
- **开闭原则**：对扩展开放，对修改封闭
- **依赖倒置**：依赖抽象而非具体实现
- **接口隔离**：提供最小化的接口

## 测试

系统采用TDD开发，包含全面的测试覆盖：

```bash
# 运行所有多因子评分相关测试
uv run python -m pytest tests/unit/test_multi_factor_scoring.py tests/unit/test_multi_factor_config.py tests/unit/test_compatibility.py -v

# 运行示例
uv run python examples/multi_factor_example.py
```

### 测试覆盖范围

- **单元测试**：每个因子和功能的独立测试
- **集成测试**：多因子协同工作的测试
- **配置测试**：各种配置方式的测试
- **兼容性测试**：与现有系统的兼容性验证
- **性能测试**：系统性能和稳定性测试
- **边界测试**：异常情况和边界值处理

## 性能优化

### 优化策略

1. **延迟计算**：只在需要时计算因子得分
2. **缓存机制**：缓存重复计算的结果
3. **并行处理**：支持多线程并发评分
4. **内存优化**：减少不必要的对象创建

### 性能指标

- **单股票评分**：< 1ms
- **批量评分（100只）**：< 50ms
- **内存使用**：< 10MB（1000只股票）
- **并发支持**：支持多线程安全操作

## 迁移指南

### 从旧系统迁移

1. **渐进式迁移**：先在测试环境验证新系统
2. **兼容模式**：使用`with_legacy_weights()`保持一致性
3. **逐步调整**：根据实际效果调整因子权重
4. **监控对比**：持续对比新旧系统结果

### 迁移步骤

```python
# 1. 创建兼容包装器
class CompatibilityWrapper:
    def __init__(self):
        self.new_scorer = MultiFactorScorer.with_legacy_weights()
    
    def calculate_total_score(self, stock: StockInfo) -> float:
        return self.new_scorer.calculate_score(stock) * 100
    
    def rank_stocks(self, stocks: list[StockInfo]) -> list[StockInfo]:
        return self.new_scorer.rank_stocks(stocks)

# 2. 替换旧评分器
old_scorer = InvestmentScorer()
new_scorer = CompatibilityWrapper()

# 3. 验证结果一致性
# 4. 逐步调整权重和因子
# 5. 完全切换到新系统
```

## 最佳实践

### 因子选择

1. **理解业务需求**：根据投资策略选择合适因子
2. **避免过度拟合**：不要使用过多相关因子
3. **定期评估**：定期评估因子有效性
4. **权重平衡**：合理分配因子权重

### 配置管理

1. **版本控制**：对配置文件进行版本管理
2. **环境隔离**：不同环境使用不同配置
3. **验证机制**：加载配置时进行验证
4. **回滚机制**：配置错误时能够快速回滚

### 性能优化

1. **批量处理**：尽量使用批量接口
2. **缓存策略**：合理使用缓存提高性能
3. **监控指标**：持续监控系统性能
4. **资源管理**：及时释放不需要的资源

## 常见问题

### Q: 如何添加新的因子？
A: 继承Factor基类，实现calculate方法，然后注册到FactorRegistry。

### Q: 如何调整因子权重？
A: 使用with_custom_weights()方法或配置文件来设置权重。

### Q: 新系统与旧系统有什么区别？
A: 新系统更加模块化、可扩展，支持更多配置选项，同时保持向后兼容。

### Q: 如何处理缺失数据？
A: 系统内置了缺失数据处理机制，会自动处理异常值和缺失数据。

### Q: 如何提高评分性能？
A: 使用批量处理、启用缓存、合理配置因子数量。

## 贡献指南

欢迎贡献代码和建议！请遵循以下步骤：

1. Fork项目
2. 创建功能分支
3. 编写测试（TDD）
4. 提交代码
5. 创建Pull Request

## 许可证

本项目采用MIT许可证，详见LICENSE文件。