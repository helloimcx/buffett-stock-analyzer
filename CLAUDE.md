# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a professional-grade Buffett dividend stock screening system for Chinese A-share markets. The system uses a layered architecture design following SOLID principles and design patterns, providing enterprise-level code quality and maintainability.

## Architecture Overview

### Layered Design

The system follows a standard N-tier architecture pattern:

```
├── CLI Layer (main.py)
├── Strategy Layer (src/buffett/strategies/)
├── Core Layer (src/buffett/core/) + Utils Layer (src/buffett/utils/)
├── Data Layer (src/buffett/data/)
└── Model Layer (src/buffett/models/)
```

### Key Components

- **Models Layer** (`src/buffett/models/`): Data structures and business entities
- **Core Layer** (`src/buffett/core/`): Business logic and scoring algorithms
- **Data Layer** (`src/buffett/data/`): Data access and API wrappers
- **Strategy Layer** (`src/buffett/strategies/`): Business strategies and workflows
- **Utils Layer** (`src/buffett/utils/`): Utilities and helper functions

### Design Patterns

- **Strategy Pattern**: Pluggable analysis strategies for different screening approaches
- **Repository Pattern**: Unified data access interface
- **Adapter Pattern**: Adapts different data sources (AKShare)
- **Factory Pattern**: Centralized object creation logic
- **Configuration Pattern**: Environment-based configuration management

## Common Development Commands

### Environment Setup
```bash
# Setup virtual environment
pip install uv
uv venv --python 3.13
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Install dependencies
uv sync

# Run with uv (recommended)
uv run python main.py <command>

# Or run directly with python
python main.py <command>
```

### Running the Application

```bash
# Screen high dividend stocks (default ≥4%)
uv run python main.py screen

# Screen with custom dividend threshold
uv run python main.py screen --min-dividend 6.0

# Analyze specific stocks
uv run python main.py target 600000 000001 601398

# Analyze stocks from file
uv run python main.py target --file sample_stocks.txt

# Use command aliases
uv run buffett screen
uv run buffett target --file sample_stocks.txt
```

### Code Quality

```bash
# Format code
uv run black src/
uv run isort src/

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=src/buffett --cov-report=html

# Run type checking
uv run mypy src/
```

## Architecture Deep Dive

### Data Models (`src/buffett/models/`)

- **StockInfo**: Core stock information dataclass with business logic methods
- **ScreeningCriteria**: Configurable screening parameters
- **ScreeningResult**: Comprehensive result container with export capabilities

### Core Business Logic (`src/buffett/core/`)

- **Configuration Management**: Environment-based and code-based configuration
- **Investment Scoring**: Modular scoring algorithm (dividend, valuation, technical, fundamental)
- **Configurable Weights**: Adjustable scoring weights and thresholds

### Data Access (`src/buffett/data/`)

- **StockDataProvider**: AKShare API wrapper with rate limiting and error handling
- **StockRepository**: High-level data operations with filtering and aggregation
- **Data Validation**: Safe type conversion and data integrity checks

### Business Strategies (`src/buffett/strategies/`)

- **DividendScreeningStrategy**: Implements the dividend stock screening workflow
- **TargetStockAnalysisStrategy**: Handles specific stock analysis workflows
- **Standardized Flows**: Consistent error handling and result formatting

### Utilities (`src/buffett/utils/`)

- **StockReporter**: Multi-format output generation (console, JSON, Excel)
- **File Operations**: Safe file loading and parsing utilities
- **User Experience**: Enhanced console display and progress reporting

## Data Sources

- **Market Data**: Sina Finance - Real-time stock market data via AKShare
- **Stock Details**: Xueqiu (雪球网) - Detailed fundamental and valuation data
- **Data Coverage**: All A-share stocks (沪深京 A 股)

## Key Development Patterns

### Configuration System
- **Environment Variables**: Override configuration for different environments
- **Code Configuration**: Runtime configuration changes
- **Default Values**: Sensible defaults for all parameters
- **Type Safety**: Pydantic models for configuration validation

### Error Handling Strategy
- **Graceful Degradation**: Failed stocks don't stop batch processing
- **Data Validation**: Comprehensive input validation and sanitization
- **Retry Logic**: Automatic retry with exponential backoff
- **User Feedback**: Clear error messages and progress indicators

### Performance Optimization
- **Request Rate Limiting**: Built-in delays to respect API limits
- **Caching Strategy**: Intelligent caching to avoid duplicate requests
- **Batch Processing**: Efficient bulk operations
- **Memory Management**: Streaming processing for large datasets

## Extension Points

### Adding New Data Sources
```python
# Create new provider
class NewDataProvider(StockDataProvider):
    def get_stock_detail(self, symbol: str) -> pd.DataFrame:
        # Implement new data source
        pass

# Register in factory
provider = NewDataProvider()
```

### Adding New Scoring Algorithms
```python
class CustomScorer(InvestmentScorer):
    def calculate_technical_score(self, stock: StockInfo) -> float:
        # Implement custom technical analysis
        pass

    def calculate_total_score(self, stock: StockInfo) -> float:
        base_score = super().calculate_total_score(stock)
        custom_score = self.calculate_technical_score(stock)
        return min(base_score + custom_score, 100.0)
```

### Adding New Output Formats
```python
class PDFReporter(StockReporter):
    def save_pdf(self, result: ScreeningResult) -> str:
        # Implement PDF report generation
        pass

# Use new reporter
reporter = PDFReporter()
```

## Testing Strategy

### Test Organization
- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test component interactions
- **End-to-End Tests**: Test complete workflows
- **Mocking**: Mock external dependencies

### Test Coverage Goals
- **Model Layer**: 100% coverage for data models
- **Core Layer**: 100% coverage for business logic
- **Data Layer**: 95%+ coverage for data operations
- **Utils Layer**: 90%+ coverage for utilities

### Running Tests
```bash
# Run all tests
uv run pytest

# Run specific test suites
uv run pytest tests/unit/
uv run pytest tests/integration/

# Generate coverage report
uv run pytest --cov=src/buffett --cov-report=html
```

## Configuration Management

### Environment Variables
- `BUFFETT_MIN_DIVIDEND_YIELD`: Minimum dividend yield threshold
- `BUFFETT_DIVIDEND_WEIGHT`: Dividend yield weight in scoring
- `BUFFETT_REQUEST_DELAY`: Delay between API requests
- `BUFFETT_REPORTS_DIR`: Reports output directory

### Code Configuration
```python
from src.buffett.core import config

# Modify scoring parameters
config.scoring.high_dividend_threshold = 5.0
config.data.request_delay = 0.15

# Change reports directory
config.reports_dir = "./analysis_results"
```

## Data Quality

### Input Validation
- **Type Safety**: Comprehensive type checking with Pydantic models
- **Range Validation**: Validate numeric ranges and constraints
- **Format Validation**: Ensure correct data formats
- **Business Rules**: Apply investment screening criteria

### Output Consistency
- **Standardized Format**: Consistent JSON structure across all outputs
- **Complete Metadata**: Timestamps, criteria, errors, statistics
- **Sorted Results**: Consistent ranking and sorting mechanisms
- **Export Compatibility**: Cross-format export capabilities

### Error Recovery
- **Individual Stock Failures**: Failed stocks don't affect batch processing
- **Partial Data**: Graceful handling of missing or incomplete data
- **Network Issues**: Retry logic with exponential backoff
- **API Limitations**: Rate limiting and graceful degradation

## Best Practices

### Code Organization
- **Single Responsibility**: Each class has one clear purpose
- **Clear Interfaces**: Well-defined method signatures and return types
- **Dependency Injection**: Use dependency injection where appropriate
- **Modular Design**: Components are independent and testable

### Performance Considerations
- **Efficient Data Access**: Minimize API calls through batching
- **Memory Management**: Process large datasets in streams
- **Background Processing**: Use async operations for long-running tasks
- **Cache Strategy**: Cache results appropriately

### Security Practices
- **Input Sanitization**: Validate all user inputs
- **Error Message Sanitization**: Avoid leaking sensitive information
- **Dependency Security**: Use trusted dependencies
- **Configuration Security**: Secure handling of configuration data

## Development Workflow

### Code Review Guidelines
- **Type Safety**: Use type hints for all function parameters and return values
- **Error Handling**: Implement comprehensive exception handling
- **Documentation**: Include docstrings for all public methods
- **Testing**: Write tests for all new functionality

### Deployment Considerations
- **Environment Isolation**: Use separate configurations for different environments
- **Configuration Management**: Use environment variables for deployment settings
- **Logging Strategy**: Appropriate logging levels for production debugging
- **Monitoring**: Set up monitoring for production observability

This system follows professional software engineering practices and is designed for long-term maintenance and extension.