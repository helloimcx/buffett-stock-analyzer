# 风险管理系统

巴菲特投资助手的风险管理系统提供多层次风险管理功能，包括风险指标计算、实时风险监控、动态止损策略和风险报告生成。

## 功能概述

### 核心功能

1. **风险指标计算**
   - VaR（风险价值）计算：支持历史模拟法、参数法和蒙特卡洛模拟
   - 最大回撤监控：实时计算和监控投资组合最大回撤
   - 波动率分析：计算年化波动率和日波动率
   - 相关性分析：分析投资组合内股票的相关性矩阵
   - 集中度风险：使用赫芬达尔指数评估投资组合集中度
   - 流动性风险：基于成交额评估流动性风险

2. **风险监控**
   - 系统性风险监控：市场整体风险监控
   - 投资组合风险评估：多股票组合风险评估
   - 个股风险控制：单只股票风险控制
   - 操作风险管理：交易操作风险管理
   - 多级风险预警机制：低、中、高、严重四级预警

3. **动态止损策略**
   - 保守型策略：严格控制风险，低回撤目标
   - 平衡型策略：风险收益平衡管理
   - 激进型策略：承受较高风险追求高收益
   - 移动止损：根据价格上涨动态调整止损位

4. **风险报告生成**
   - 风险摘要报告：整体风险评估和预警统计
   - 投资组合风险报告：详细的投资组合风险分析
   - 个股风险报告：单只股票风险评估
   - 风险控制建议：基于风险指标的投资建议

## 使用方法

### 基本使用

```python
from src.buffett.core.risk_management import RiskManager, RiskConfig, RiskStrategy

# 创建风险管理配置
config = RiskConfig(
    strategy=RiskStrategy.BALANCED,  # 平衡型策略
    lookback_days=252,  # 回看天数
    enable_risk_alerts=True  # 启用风险预警
)

# 创建风险管理器
risk_manager = RiskManager(config)

# 更新投资组合数据
stocks = [...]  # 股票列表
weights = {"600519": 0.3, "000858": 0.25, ...}  # 投资组合权重
risk_manager.update_portfolio_data(stocks, weights)

# 评估投资组合风险
metrics, alerts = risk_manager.assess_portfolio_risk()

# 生成风险报告
reports = risk_manager.generate_risk_reports(weights, stocks)
```

### 风险策略配置

#### 保守型策略
```python
config = RiskConfig(strategy=RiskStrategy.CONSERVATIVE)
# 特点：
# - 严格的止损（5%移动止损）
# - 低风险阈值
# - 适合风险厌恶投资者
```

#### 平衡型策略
```python
config = RiskConfig(strategy=RiskStrategy.BALANCED)
# 特点：
# - 适中的止损（8%移动止损）
# - 平衡的风险阈值
# - 适合大多数投资者
```

#### 激进型策略
```python
config = RiskConfig(strategy=RiskStrategy.AGGRESSIVE)
# 特点：
# - 宽松的止损（12%移动止损）
# - 高风险阈值
# - 适合风险偏好投资者
```

### VaR计算方法

```python
from src.buffett.core.risk_management import VaRMethod

# 历史模拟法（默认）
config = RiskConfig(var_method=VaRMethod.HISTORICAL)

# 参数法（假设正态分布）
config = RiskConfig(var_method=VaRMethod.PARAMETRIC)

# 蒙特卡洛模拟
config = RiskConfig(var_method=VaRMethod.MONTE_CARLO)
```

### 风险阈值配置

```python
from src.buffett.core.risk_management import RiskThreshold

thresholds = RiskThreshold(
    max_var_95=0.05,      # 最大VaR(95%)阈值
    max_var_99=0.08,      # 最大VaR(99%)阈值
    max_drawdown=0.15,     # 最大回撤阈值
    max_volatility=0.25,    # 最大波动率阈值
    min_sharpe_ratio=0.5,   # 最小夏普比率阈值
    max_concentration=0.3,  # 最大集中度阈值
    min_liquidity=1000000   # 最小流动性阈值
)

config = RiskConfig(risk_thresholds=thresholds)
```

### 动态止损使用

```python
# 计算止损价格
stock = StockInfo(...)  # 股票信息
purchase_price = 100.0  # 购买价格
stop_loss_price = risk_manager.calculate_stop_loss(stock, purchase_price)

# 更新移动止损
risk_manager.update_trailing_stop("600519", current_price)

# 检查是否触发止损
should_stop = risk_manager.check_stop_loss("600519", current_price)
if should_stop:
    print("触发止损，建议卖出")
```

## 风险指标说明

### VaR（风险价值）
- **定义**：在给定置信水平下，投资组合在特定时间内的最大预期损失
- **计算方法**：历史模拟法、参数法、蒙特卡洛模拟
- **应用**：评估下行风险，设置风险限额

### 最大回撤
- **定义**：投资组合从历史最高点到最低点的最大跌幅
- **计算**：基于价格序列计算
- **应用**：评估历史最大损失，控制回撤风险

### 波动率
- **定义**：收益率的标准差，衡量价格波动程度
- **计算**：日波动率年化为年波动率
- **应用**：评估价格稳定性，风险定价

### 夏普比率
- **定义**：风险调整后收益，衡量单位风险获得的超额收益
- **计算**：(组合收益率 - 无风险利率) / 组合波动率
- **应用**：评估投资效率，组合优化

### 集中度风险
- **定义**：投资组合中单一资产或行业的集中程度
- **计算**：赫芬达尔指数
- **应用**：评估分散化程度，降低集中风险

### 流动性风险
- **定义**：资产变现的难易程度和价格影响
- **计算**：基于成交额和价格变动
- **应用**：评估市场冲击成本，设置流动性限额

## 风险预警机制

### 预警等级
- **低风险**：风险指标轻微超限，需要关注
- **中等风险**：风险指标明显超限，需要调整
- **高风险**：风险指标严重超限，需要立即行动
- **严重风险**：风险指标极度超限，需要紧急处理

### 预警类型
- **VaR预警**：VaR超过设定阈值
- **回撤预警**：最大回撤超过设定阈值
- **波动率预警**：波动率超过设定阈值
- **集中度预警**：集中度风险超过设定阈值
- **流动性预警**：流动性风险超过设定阈值

## 集成使用

### 与监控系统集成

```python
from src.buffett.core.monitor import StockMonitor
from src.buffett.core.risk_management import RiskManager

# 创建监控器和风险管理器
monitor = StockMonitor(monitoring_config)
risk_manager = RiskManager(risk_config)

# 在监控循环中集成风险评估
def monitoring_check():
    # 获取当前股票数据
    stocks = get_current_stocks()
    
    # 更新风险管理器
    risk_manager.update_portfolio_data(stocks, portfolio_weights)
    
    # 评估风险
    metrics, alerts = risk_manager.assess_portfolio_risk()
    
    # 处理风险预警
    for alert in alerts:
        handle_risk_alert(alert)
```

### 实时风险监控

```python
# 设置定时任务
import schedule

def hourly_risk_check():
    # 更新数据
    stocks = get_latest_stock_data()
    risk_manager.update_portfolio_data(stocks, weights)
    
    # 评估风险
    metrics, alerts = risk_manager.assess_portfolio_risk()
    
    # 发送预警通知
    if alerts:
        send_risk_notifications(alerts)

# 每小时执行一次风险检查
schedule.every().hour.do(hourly_risk_check)
```

## 最佳实践

### 1. 风险策略选择
- **保守型**：适合退休账户、风险厌恶投资者
- **平衡型**：适合长期投资、大多数投资者
- **激进型**：适合年轻投资者、风险偏好投资者

### 2. 风险阈值设置
- 根据个人风险承受能力调整阈值
- 考虑市场环境变化
- 定期回顾和调整阈值

### 3. 止损策略
- 严格执行止损纪律
- 结合移动止损保护利润
- 避免情绪化决策

### 4. 分散化投资
- 控制单一股票权重不超过30%
- 行业分散化
- 定期再平衡

### 5. 监控频率
- 正常市场：每日监控
- 波动市场：每小时监控
- 极端市场：实时监控

## 示例程序

- `examples/risk_management_example.py`：基本风险管理功能演示
- `examples/integrated_risk_monitoring_example.py`：集成监控演示

## 测试

运行风险管理模块测试：

```bash
python -m pytest tests/unit/test_risk_management.py -v
```

## 注意事项

1. **数据质量**：确保输入数据的准确性和完整性
2. **模型假设**：了解风险模型的假设和局限性
3. **市场环境**：考虑不同市场环境下的风险特征
4. **执行纪律**：严格执行风险控制策略
5. **定期回顾**：定期回顾和调整风险管理策略