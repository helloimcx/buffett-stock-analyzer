# 巴菲特股息筛选系统

🚀 **基于AKShare的专业级中国A股高股息筛选系统 - 分层架构版本**

## 简介

这是一个采用现代分层架构设计的巴菲特股息筛选系统，专注于高股息价值投资策略。系统基于SOLID原则和设计模式构建，具有企业级的代码质量和可维护性。

### 系统特点

- 🏗️ **分层架构** - 采用标准的N层架构模式
- 🎯 **专业级代码** - 完整的类型注解、错误处理和设计模式
- ⚡ **高性能** - 优化的数据获取和缓存机制
- 🔧 **高度可扩展** - 支持新数据源和评分算法的轻松扩展
- 📊 **灵活配置** - 支持环境变量和配置文件的配置管理
- 🧪 **可测试** - 完整的单元测试和集成测试支持

## 项目架构

### 📁 目录结构

```
buffett/
├── src/buffett/                 # 源代码包
│   ├── models/                 # 数据模型层
│   │   ├── stock.py           # 股票数据模型
│   │   └── __init__.py
│   ├── core/                   # 核心业务层
│   │   ├── config.py          # 配置管理
│   │   ├── scoring.py         # 评分算法
│   │   └── __init__.py
│   ├── data/                   # 数据访问层
│   │   ├── providers.py       # 数据提供者
│   │   ├── repository.py      # 数据仓储
│   │   └── __init__.py
│   ├── strategies/             # 业务策略层
│   │   ├── screening.py      # 筛选策略
│   │   ├── analysis.py       # 分析策略
│   │   └── __init__.py
│   ├── utils/                  # 工具层
│   │   ├── reporter.py        # 报告生成器
│   │   ├── file_loader.py     # 文件加载工具
│   │   └── __init__.py
│   ├── main.py                 # CLI主程序
│   └── __init__.py             # 包初始化
├── tests/                       # 测试目录
│   ├── unit/                   # 单元测试
│   └── integration/            # 集成测试
├── main.py                      # 项目入口脚本
├── sample_stocks.txt            # 示例股票列表
├── pyproject.toml               # 项目配置
├── README.md                    # 项目文档
├── ARCHITECTURE_LAYERS.md      # 架构文档
└── reports/                     # 结果输出目录
```

### 🏗️ 分层架构

#### 1. **数据模型层** (`models/`)
- 定义系统中的数据结构和业务实体
- 使用 `@dataclass` 实现类型安全
- 包含业务逻辑方法和数据验证

#### 2. **核心业务层** (`core/`)
- 实现核心业务逻辑和算法
- 配置管理和评分系统
- 支持可扩展的业务规则

#### 3. **数据访问层** (`data/`)
- 封装AKShare数据源访问
- 提供统一的数据操作接口
- 实现数据缓存和错误处理

#### 4. **业务策略层** (`strategies/`)
- 实现不同的筛选和分析策略
- 支持业务流程标准化
- 封装复杂的业务逻辑

#### 5. **工具层** (`utils/`)
- 提供报告生成和文件操作工具
- 用户界面优化
- 多格式输出支持

## 快速开始

### 1. 环境准备

```bash
# 使用uv安装依赖（推荐）
pip install uv
uv sync --python 3.13

# 或使用pip安装依赖
pip install akshare pandas requests
```

### 2. 基本使用

```bash
# 筛选所有高股息股票（默认股息率≥4%）
uv run python main.py screen

# 筛选股息率≥6%的股票
uv run python main.py screen --min-dividend 6.0

# 分析指定股票
uv run python main.py target 600000 000001 601398

# 从文件读取股票代码进行分析
uv run python main.py target --file sample_stocks.txt

# 使用新的命令别名
uv run buffett screen
uv run buffett target --file sample_stocks.txt
```

### 3. 高级用法

```bash
# 直接运行脚本
./main.py target 600000

# 使用环境变量配置
export BUFFETT_MIN_DIVIDEND_YIELD=5.0
export BUFFETT_REQUEST_DELAY=0.3
uv run python main.py screen

# 开发者模式
uv run python -m pytest tests/
uv run python -m black src/
uv run python -m isort src/
```

## 核心功能

### 1. 多维度筛选系统

#### 股息筛选
- **最低股息率**: 默认4%，可自定义
- **基本过滤**: 排除ST股票、价格异常股票
- **流动性要求**: 最低成交量要求
- **行业过滤**: 支持特定行业筛选

#### 估值分析
- **P/E比率**: 动态市盈率分析
- **P/B比率**: 市净率分析
- **相对估值**: 行业内估值比较
- **历史估值**: 历史估值分位数分析

#### 技术分析
- **52周位置**: 当前价格相对年度高低点位置
- **移动平均**: 多周期移动平均线分析
- **动量指标**: RSI、MACD等技术指标
- **趋势识别**: 支持趋势判断

### 2. 专业的评分系统（100分制）

| 评分维度 | 权重 | 评分标准 | 可配置 |
|----------|------|----------|--------|
| **股息率** | 50% | ≥4%: 50分, ≥2.5%: 40分, ≥1.5%: 25分 | ✅ |
| **估值水平** | 25% | P/E<20: 25分, P/B<2.0: 25分 | ✅ |
| **技术位置** | 15% | 52周低位: 50分, 中位: 30分 | ✅ |
| **基本面** | 10% | EPS>0: 5分, 安全边际: 5分 | ✅ |

### 3. 灵活的配置系统

#### 环境变量配置
```bash
export BUFFETT_MIN_DIVIDEND_YIELD=4.0
export BUFFETT_DIVIDEND_WEIGHT=0.5
export BUFFETT_VALUATION_WEIGHT=0.25
export BUFFETT_REQUEST_DELAY=0.2
export BUFFETT_REPORTS_DIR="./reports"
```

#### 代码配置
```python
from src.buffett.core import config

# 动态调整配置
config.scoring.high_dividend_threshold = 5.0
config.data.request_delay = 0.15
config.reports_dir = "./custom_reports"
```

## 输出示例

### 控制台输出
```
📊 指定股票分析结果: 21 只股票
========================================================================================================================
排名   股票代码       股票名称         价格       股息率      P/E      P/B      评分     52周位置
------------------------------------------------------------------------------------------------------------------------
1    SH600016   民生银行         ¥4.06    4.88   % 4.67    0.32    46.0   低位(27%)
2    SH601229   上海银行         ¥10.25   5.07   % 6.04    0.61    43.5   高位(78%)
3    SH601318   中国平安         ¥60.65   4.25   % 6.20    1.11    42.0   高位(91%)
========================================================================================================================
```

### JSON结果文件
```json
{
  "timestamp": "2025-11-16T16:11:36",
  "criteria": {
    "min_dividend_yield": 4.0,
    "min_price": 2.0,
    "max_price": 100.0,
    "min_volume": 1000000,
    "exclude_st": true
  },
  "total_stocks_analyzed": 1,
  "passed_stocks_count": 1,
  "passed_stocks": [...]
}
```

## 开发指南

### 项目设置

```bash
# 克隆项目
git clone <repository-url>
cd buffett

# 创建虚拟环境
uv venv --python 3.13
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# 安装依赖
uv sync

# 运行测试
uv run pytest tests/
```

### 开发工作流

```bash
# 代码格式化
uv run black src/
uv run isort src/

# 运行测试
uv run pytest tests/ -v
uv run pytest tests/ --cov=src/buffett

# 类型检查
uv run mypy src/

# 运行应用
uv run python main.py --help
uv run python main.py target 600000
```

### 扩展开发

#### 添加新的数据源
```python
# src/buffett/data/providers.py
class NewDataProvider:
    def get_stock_detail(self, symbol: str) -> pd.DataFrame:
        # 实现新的数据源
        return pd.DataFrame()

# 在工厂中注册
provider = NewDataProvider()
```

#### 添加新的评分算法
```python
# src/buffett/core/scoring.py
class CustomScorer(InvestmentScorer):
    def calculate_momentum_score(self, stock: StockInfo) -> float:
        # 实现动量评分算法
        return 0.0

    def calculate_total_score(self, stock: StockInfo) -> float:
        # 包含动量评分的综合计算
        base_score = super().calculate_total_score(stock)
        momentum_score = self.calculate_momentum_score(stock)
        return min(base_score + momentum_score, 100.0)
```

#### 添加新的输出格式
```python
# src/buffett/utils/reporter.py
class ExcelReporter(StockReporter):
    def save_excel(self, result: ScreeningResult, filename: str) -> str:
        # 实现Excel导出功能
        return filename

# 使用新的报告生成器
reporter = ExcelReporter()
reporter.save_excel(result, "analysis_report")
```

## 性能优化

### 数据获取优化
- **请求频率控制**: 自动延迟避免API限制
- **数据缓存**: 智能缓存机制
- **并发处理**: 支持批量数据获取
- **错误恢复**: 自动重试和降级处理

### 算法优化
- **延迟计算**: 只在需要时进行复杂计算
- **批量处理**: 支持批量评分计算
- **结果缓存**: 缓存评分结果避免重复计算

### 内存优化
- **流式处理**: 大数据集的流式处理
- **及时释放**: 及时释放不需要的资源
- **垃圾回收**: 避免内存泄漏

## 测试

### 单元测试
```bash
# 运行所有测试
uv run pytest

# 运行特定模块测试
uv run pytest tests/unit/
uv run pytest tests/unit/test_models.py

# 生成覆盖率报告
uv run pytest --cov=src/buffett --cov-report=html
```

### 集成测试
```bash
# 运行集成测试
uv run pytest tests/integration/

# 运行端到端测试
uv run pytest tests/integration/test_end_to_end.py
```

### 测试覆盖率
- **目标覆盖率**: ≥90%
- **核心模块**: 100%覆盖率
- **关键路径**: 完整测试覆盖

## 部署

### 本地部署
```bash
# 直接运行
./main.py target 600000

# 使用uv运行
uv run python main.py target 600000
```

### Docker部署
```dockerfile
FROM python:3.13-slim

WORKDIR /app
COPY . .
RUN pip install -e .
COPY requirements.txt .
CMD ["python", "main.py", "screen"]
```

### 生产环境配置
```bash
# 环境变量
export BUFFETT_ENVIRONMENT=production
export BUFFETT_LOG_LEVEL=INFO
export BUFFETT_CACHE_ENABLED=true
export BUFFETT_API_TIMEOUT=30
```

## 故障排除

### 常见问题

1. **依赖安装问题**
   ```bash
   # 重新安装依赖
   uv sync --python 3.13
   ```

2. **数据获取失败**
   ```bash
   # 检查网络连接
   ping akshare.readthedocs.io

   # 增加请求延迟
   export BUFFETT_REQUEST_DELAY=0.5
   ```

3. **内存不足**
   ```bash
   # 减少并发数量
   export BUFFETT_BATCH_SIZE=10

   # 启用缓存优化
   export BUFFETT_CACHE_ENABLED=true
   ```

4. **编码问题**
   ```bash
   # 设置正确编码
   export PYTHONIOENCODING=utf-8
   export LANG=zh_CN.UTF-8
   ```

## 更新日志

### v2.1.0 (2025-11-16) - 分层架构重构
- ✨ **架构重构**: 从单文件重构为分层架构
- ✅ **设计模式**: 应用SOLID原则和设计模式
- ✅ **模块化**: 6个专业模块，职责清晰
- ✅ **配置化**: 完整的配置管理系统
- ✅ **可测试性**: 支持单元测试和集成测试
- ✅ **文档完善**: 详细的架构文档和使用指南
- ✅ **企业级**: 符合企业级开发标准

### v2.0.0 (2025-11-16) - 模块化优化
- ✨ **模块化架构**: 从巨无霸单文件重构为模块化
- ✨ **配置管理**: 灵活的参数配置系统
- ✅ **错误处理**: 完善的异常处理机制
- ✅ **性能优化**: 数据获取和缓存优化

### v1.0.0 (2024-11-16) - 初始版本
- ✨ **基础功能**: 完整的股息筛选功能
- ✨ **评分系统**: 多维度投资价值评分
- ✅ **数据源**: 基于AKShare的数据获取

## 许可证

MIT License - 详见 LICENSE 文件

## 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 联系方式

- 📧 **项目仓库**: https://github.com/your-username/buffett
- 📧 **问题反馈**: https://github.com/your-username/buffett/issues

---

## 免责声明

本工具仅供学习和研究使用，不构成任何投资建议。投资有风险，入市需谨慎。使用者应当根据自己的风险承受能力和投资目标做出独立的投资决策。

**数据准确性提示**:
- 本系统数据仅供参考，可能存在更新延迟
- 建议在做出投资决策前验证关键信息
- 市场风险需要充分考虑