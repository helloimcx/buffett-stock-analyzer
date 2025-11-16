# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Chinese A-share high dividend value stock screening and monitoring system that implements a four-step investment strategy:
1. **Eligibility Screening** - Hard metrics for high dividend leaders (4%+ dividend yield, stable payments)
2. **Valuation Assessment** - Comfort zone valuation (P/E < 30th percentile, P/B < 20th percentile)
3. **Trend Analysis** - Technical timing indicators (moving averages, Bollinger Bands, RSI)
4. **Risk Control** - Stop-loss and portfolio monitoring

The system targets high dividend blue-chip stocks in the Chinese A-share market using quantitative screening combined with technical analysis.

## Common Development Commands

### Setup and Installation
```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh
# or: pip install uv

# Create and activate virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv sync                    # Install all dependencies including dev dependencies
uv sync --no-dev          # Install only production dependencies

# Alternative: uv add for individual packages
uv add pandas numpy       # Add specific packages

# Verify installation and project structure
uv run python main.py config          # Show system configuration
```

### Running the Application

#### Command Line Interface
```bash
# Run complete screening and show results
uv run python main.py screen

# Run risk monitoring on existing positions
uv run python main.py monitor

# Start continuous monitoring mode (runs indefinitely)
uv run python main.py start

# Display current configuration
uv run python main.py config

# Verbose mode for debugging
uv run python main.py screen -v
```

### Testing and Validation
```bash
# Run tests with pytest
uv run pytest

# Run tests with coverage
uv run pytest --cov=src/buffett --cov-report=html

# Run specific test modules
uv run pytest tests/unit/test_models.py

# Code formatting and linting (development tools)
uv run black --check .
uv run isort --check-only .
uv run flake8 .
uv run mypy .
```

## High-Level Architecture

### Modern Enterprise Architecture

The system has been completely restructured as a modern enterprise-grade application following SOLID principles and design patterns:

#### Package Structure (`src/buffett/`)
- **`models/`** - Pydantic v2 data models with type safety and validation
- **`core/`** - Core business logic and dependency injection container
- **`data/`** - Data access layer with Repository pattern implementation
- **`strategies/`** - Strategy pattern for data fetching (AKShare, Mock, Multi-source)
- **`factories/`** - Factory pattern for creating repositories and strategies
- **`interfaces/`** - Abstract interfaces for dependency inversion
- **`exceptions/`** - Structured exception hierarchy with error codes
- **`config/`** - Configuration management with environment variables
- **`api/`** - REST API endpoints and monitoring interfaces

#### Key Design Patterns
- **Dependency Injection** - IoC container with lifecycle management
- **Repository Pattern** - Abstract data access with multiple implementations
- **Strategy Pattern** - Pluggable data fetching strategies
- **Factory Pattern** - Centralized object creation logic

#### Entry Points
- **`main.py`** - Modern CLI interface with argparse and async support

### Data Flow Architecture
1. **Data Ingestion** - AKShare API → local cache → pandas DataFrames
2. **Screening Pipeline** - Sequential filtering through 4-step strategy
3. **Scoring System** - Each module generates scores (0-100) for ranking
4. **Output Generation** - JSON data + HTML reports + Excel exports

### Modern Design Patterns Implementation
- **Dependency Injection** - IoC container with singleton/transient lifecycle management
- **Repository Pattern** - Abstract data access with factory creation
- **Strategy Pattern** - Pluggable data fetching (AKShare, Mock, Multi-source)
- **Factory Pattern** - Centralized repository and strategy creation
- **Caching Layer** - Repository-based caching with configurable backends
- **Configuration-Driven** - Environment-based configuration with Pydantic settings
- **Exception Handling** - Structured error hierarchy with error codes

## Important Configuration

### Key Screening Parameters
Configuration is managed through environment variables and Pydantic settings in `src/buffett/config/settings.py`:

- **Minimum dividend yield**: 4.0% (configurable via `BUFFETT_MIN_DIVIDEND_YIELD`)
- **Dividend history**: 3+ consecutive years (configurable via `BUFFETT_MIN_DIVIDEND_YEARS`)
- **Industry leadership**: Top 3 by market cap in sector (configurable via `BUFFETT_TOP_N_BY_MARKET_CAP`)
- **Valuation thresholds**: PE < 30th percentile, PB < 20th percentile
- **Technical indicators**: 30/60-week moving averages, RSI < 30 for oversold

### Industry Classification
Industry classification is managed through `src/buffett/config/industry.py` with structured Pydantic models for sector leadership analysis. Stocks are grouped into broad categories like banking, insurance, energy, consumer, etc.

### Modern Data Stack
- **Primary source**: AKShare library for Chinese A-share data (via Strategy pattern)
- **Technical analysis**: TA-Lib for moving averages, RSI, Bollinger Bands
- **Data persistence**: Repository-based caching with configurable backends
- **Data validation**: Pydantic v2 models with type safety
- **Async support**: asyncio for concurrent data fetching

## Development Notes

### Environment Management with UV
This project uses UV for fast Python environment and dependency management:

```bash
# Install UV (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Project setup
uv venv                    # Create virtual environment
source .venv/bin/activate # Activate (or let uv run handle it)
uv sync                   # Install all dependencies

# Development workflow
uv add pandas numpy       # Add new dependencies
uv remove pandas          # Remove dependencies
uv sync                   # Sync with pyproject.toml

# Run any command in the project environment
uv run python main.py screen
uv run pytest
```

### Cache Management
The system maintains caches through Repository pattern with configurable TTL. Clear cache if data seems stale:
```bash
# Cache locations depend on configured backend (file/memory/redis)
rm -rf data/cache/  # For file-based cache
# or configure through environment variables
export BUFFETT_CACHE_BACKEND=memory
```

### Scheduling and Monitoring
Automated scheduling is available through `main.py start` command:
- Continuous monitoring mode with configurable intervals
- Risk monitoring and alerting
- Integration with modern async patterns

### API Integration
The system provides REST API endpoints through `src/buffett/api/`:
- Real-time screening endpoints
- Monitoring dashboards
- Integration support for external systems

### Report Generation
Outputs are generated in multiple formats:
- **JSON**: Complete machine-readable results
- **HTML**: Visual investment reports with charts
- **Excel**: Structured data for further analysis

### Error Handling
The system includes robust error handling for data API failures with retry logic and graceful degradation. All operations are logged using loguru with structured logging.

### Performance Considerations
- First run requires extensive data download (can take 10+ minutes)
- Subsequent runs use cache and are much faster
- Screening processes are CPU-intensive due to historical percentile calculations