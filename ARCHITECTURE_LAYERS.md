# 巴菲特股息筛选系统 - 分层架构文档

## 架构概览

本项目采用标准的分层架构模式，将系统按职责分离为不同的层次，提高代码的可维护性、可扩展性和可测试性。

## 目录结构

```
buffett/
├── src/                          # 源代码根目录
│   └── buffett/                 # 项目包
│       ├── __init__.py          # 包初始化
│       ├── main.py              # CLI主程序
│       ├── models/              # 数据模型层
│       │   ├── __init__.py
│       │   └── stock.py           # 股票数据模型
│       ├── core/                # 核心业务层
│       │   ├── __init__.py
│       │   ├── config.py          # 配置管理
│       │   └── scoring.py         # 评分算法
│       ├── data/                # 数据访问层
│       │   ├── __init__.py
│       │   ├── providers.py       # 数据提供者
│       │   └── repository.py      # 数据仓储
│       ├── strategies/           # 业务策略层
│       │   ├── __init__.py
│       │   ├── screening.py      # 筛选策略
│       │   └── analysis.py       # 分析策略
│       └── utils/               # 工具层
│           ├── __init__.py
│           ├── reporter.py        # 报告生成
│           └── file_loader.py     # 文件加载
├── tests/                        # 测试目录
│   ├── unit/                   # 单元测试
│   └── integration/            # 集成测试
├── main.py                      # 项目入口脚本
├── sample_stocks.txt            # 示例股票列表
├── pyproject.toml               # 项目配置
├── README.md                    # 项目文档
└── reports/                     # 结果输出目录
```

## 分层架构详解

### 1. 数据模型层 (`src/buffett/models/`)

**职责**: 定义系统中所有的数据结构和业务实体

**核心组件**:
- **`StockInfo`**: 股票信息数据类，包含所有股票相关字段
- **`ScreeningCriteria`**: 筛选条件配置
- **`ScreeningResult`**: 筛选结果容器

**设计原则**:
- 使用 `@dataclass` 简化数据类定义
- 提供类型安全和数据验证
- 支持序列化和反序列化
- 包含业务逻辑方法（如 `from_akshare_data`）

### 2. 核心业务层 (`src/buffett/core/`)

**职责**: 包含核心业务逻辑和算法

**核心组件**:
- **`AppConfig`**: 应用全局配置管理
- **`DataConfig`**: 数据源配置
- **`ScoringConfig`**: 评分系统配置
- **`InvestmentScorer`**: 投资评分算法

**设计特点**:
- 支持环境变量覆盖配置
- 可配置的评分权重和阈值
- 模块化的评分算法（股息率、估值、技术、基本面）
- 策略模式支持不同的评分算法

### 3. 数据访问层 (`src/buffett/data/`)

**职责**: 负责数据获取、转换和缓存

**核心组件**:
- **`StockDataProvider`**: AKShare API 封装器
- **`StockRepository`**: 高级数据操作接口

**设计模式**:
- **适配器模式**: 适配不同数据源（AKShare）
- **仓储模式**: 统一的数据访问接口
- **单一职责**: 每个类只负责特定的数据操作

**功能特点**:
- 统一的错误处理和重试机制
- 请求频率控制
- 数据标准化和验证
- 安全的数据类型转换

### 4. 业务策略层 (`src/buffett/strategies/`)

**职责**: 实现不同的筛选和分析策略

**核心组件**:
- **`DividendScreeningStrategy`**: 股息筛选策略
- **`TargetStockAnalysisStrategy`**: 目标股票分析策略

**设计模式**:
- **策略模式**: 支持不同的分析策略
- **命令模式**: 封装业务操作
- **模板方法**: 标准化的分析流程

**业务流程**:
1. 数据获取 → 数据验证 → 业务逻辑处理 → 结果返回
2. 统一的错误处理和结果封装
3. 支持扩展新的业务策略

### 5. 工具层 (`src/buffett/utils/`)

**职责**: 提供各种辅助工具和功能

**核心组件**:
- **`StockReporter`**: 报告生成器
- **load_symbols_from_file`**: 文件加载工具

**功能特点**:
- 多格式输出支持（控制台、JSON）
- 文件管理和自动化
- 可配置的报告模板
- 用户体验优化

## 分层间的依赖关系

```
CLI Layer (main.py)
    ↓
Strategy Layer (strategies/)
    ↓
Core Layer (core/) + Utils Layer (utils/)
    ↓
Data Layer (data/)
    ↓
Model Layer (models/)
```

### 依赖方向

1. **模型层** - 被所有层依赖，定义基础数据结构
2. **数据层** - 依赖模型层，提供数据访问能力
3. **核心层** - 依赖模型层，实现核心业务逻辑
4. **策略层** - 依赖核心层和数据层，实现业务策略
5. **工具层** - 依赖模型层，提供辅助功能
6. **CLI层** - 依赖策略层和工具层，提供用户接口

## 设计原则应用

### 1. 单一职责原则 (SRP)
- 每个类只负责一个特定的功能
- 模块内聚，模块间低耦合

### 2. 开放封闭原则 (OCP)
- 策略层支持扩展新的分析策略
- 数据层支持扩展新的数据源
- 工具层支持扩展新的输出格式

### 3. 里氏替换原则 (LSP)
- 所有数据提供者都实现相同的接口
- 评分算法可以互相替换
- 报告生成器可以互相替换

### 4. 接口隔离原则 (ISP)
- 每层只依赖必要的接口
- 避免不必要的依赖传递

### 5. 依赖倒置原则 (DIP)
- 高层模块不依赖低层模块，都依赖抽象
- 通过依赖注入控制对象创建

## 扩展性设计

### 1. 数据源扩展
```python
# 添加新的数据源
class NewDataProvider:
    def get_stock_detail(self, symbol: str) -> pd.DataFrame:
        # 实现新的数据源
        pass

# 在工厂中注册
data_provider = NewDataProvider()
```

### 2. 评分算法扩展
```python
# 添加新的评分策略
class CustomScorer(InvestmentScorer):
    def calculate_custom_score(self, stock: StockInfo) -> float:
        # 实现自定义评分算法
        pass

# 使用自定义评分器
strategy = DividendScreeningStrategy()
strategy.scorer = CustomScorer()
```

### 3. 输出格式扩展
```python
# 添加新的报告格式
class ExcelReporter(StockReporter):
    def save_excel(self, result: ScreeningResult):
        # 实现Excel导出
        pass

# 使用新的报告生成器
reporter = ExcelReporter()
```

## 测试策略

### 1. 单元测试
- 每个模块独立测试
- Mock 外部依赖
- 覆盖核心逻辑

### 2. 集成测试
- 模块间交互测试
- 端到端流程测试
- 数据一致性测试

### 3. 测试覆盖
- 模型层: 数据验证和转换
- 数据层: API调用和错误处理
- 核心层: 评分算法和配置
- 策略层: 业务流程和结果
- 工具层: 输出格式和文件操作

## 部署架构

### 1. 开发环境
- 源代码直接运行
- 本地文件系统存储
- 配置文件管理

### 2. 生产环境
- Docker 容器化部署
- 环境变量配置
- 数据卷挂载

## 总结

这个分层架构具有以下优势：

1. **清晰的职责分离**: 每层只负责特定的功能
2. **良好的可测试性**: 每层都可以独立测试
3. **强大的扩展能力**: 支持轻松添加新功能
4. **统一的接口**: 层间通过标准接口通信
5. **灵活的配置**: 支持多种配置方式

这种架构为系统的长期维护和功能扩展奠定了坚实的基础。