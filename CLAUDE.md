# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a simplified Buffett dividend stock screening system for Chinese A-share markets. The system has been completely refactored from a complex enterprise architecture to a single-file implementation focused on core functionality.

## Development Commands

### Environment Setup
```bash
# Install Python 3.13 and sync dependencies
uv python install 3.13
uv sync --python 3.13

# Alternative: Use pip directly
pip install akshare pandas requests
```

### Running the Application
```bash
# Screen all high-dividend stocks (default ≥4%)
uv run python main.py screen

# Screen with custom dividend threshold
uv run python main.py screen --min-dividend 6.0

# Analyze specific stocks
uv run python main.py target 600000 000001 601398

# Analyze stocks from file
uv run python main.py target --file sample_stocks.txt

# Show help
uv run python main.py --help
```

### Code Quality
```bash
# Format code
uv run black main.py

# Sort imports
uv run isort main.py

# Run tests (if any)
uv run pytest
```

## Architecture

### Single-File Design Philosophy
This project intentionally uses a minimalist architecture with a single `main.py` file containing all functionality. This was a deliberate simplification from a complex enterprise-grade system with 50+ files to focus on core investment screening functionality.

### Core Components

#### SimpleBuffettScreener Class
The main class encapsulates all screening logic:

- **Data Sources**: Uses AKShare library for direct Chinese stock market data access
  - `ak.stock_zh_a_spot()` for market overview data (Sina Finance)
  - `ak.stock_individual_spot_xq()` for detailed stock data (Xueqiu)

- **Data Processing Pipeline**:
  1. Market data retrieval → Basic filtering → Detailed analysis
  2. Dividend yield screening → Valuation analysis → Technical scoring
  3. Results ranking and JSON export

#### Key Methods
- `get_all_stocks_data()`: Fetches all A-share real-time data
- `get_stock_detail(symbol)`: Gets detailed stock information with automatic exchange detection
- `screen_dividend_stocks()`: Main screening logic for high-dividend stocks
- `analyze_specific_stocks()`: Analyzes user-specified stocks
- `calculate_investment_score()`: 100-point scoring system

### Data Flow
1. **Input**: Stock symbols (6-digit codes) or file with symbol list
2. **Symbol Normalization**: Automatic SH/SZ prefix detection based on first digit
3. **Data Fetching**: AKShare API calls with rate limiting
4. **Safe Data Processing**: `safe_float()` method handles None/invalid values
5. **Scoring**: Multi-factor investment scoring (dividend, valuation, technical, fundamentals)
6. **Output**: Console display + JSON files in `reports/` directory

### Error Handling Strategy
- **Graceful Degradation**: Failed stock analysis doesn't stop batch processing
- **Data Validation**: Price and name validation before processing
- **Network Resilience**: Built-in retry mechanisms and rate limiting
- **Safe Type Conversion**: `safe_float()` prevents crashes on bad data

### Investment Screening Criteria

#### Scoring System (100 points total):
- **Dividend Yield (40%)**: ≥6%: 40pts, ≥4%: 30pts, ≥3%: 20pts
- **Valuation (30%)**: P/E<15: 15pts, P/B<1.5: 15pts
- **Technical Position (20%)**: 52-week low proximity
- **Fundamentals (10%)**: EPS>0, book value safety margin

#### Default Filters:
- Minimum dividend yield: 4%
- Exclude ST stocks
- Price range: ¥2-¥100
- Minimum volume: 1M shares

## File Structure
```
├── main.py              # Complete application (400 lines)
├── sample_stocks.txt    # Example stock symbols
├── pyproject.toml      # Modern Python project config
├── README.md           # User documentation
├── .python-version     # Python 3.13 specification
└── reports/            # JSON output files
```

## Important Implementation Notes

### Stock Code Format Handling
The system automatically detects exchange based on stock code:
- Codes starting with '6' → Shanghai Stock Exchange (SH prefix)
- Codes starting with '0' or '3' → Shenzhen Stock Exchange (SZ prefix)
- Existing SH/SZ prefixes are preserved

### Data Source Limitations
- **Rate Limiting**: Built-in delays (0.1-0.2s) to avoid IP blocking
- **Data Quality**: Real-time data but may have delays; verify critical information
- **Market Hours**: Best performance during Chinese market hours

### Key Dependencies
- `akshare>=1.13.0`: Chinese stock market data
- `pandas>=2.0.0`: Data processing
- `requests>=2.31.0`: HTTP requests

## Development Philosophy

This project prioritizes:
1. **Simplicity over complexity**: Single file vs enterprise architecture
2. **Functionality over features**: Core screening vs comprehensive platform
3. **Reliability over perfection**: Graceful error handling vs data completeness
4. **Usability over configuration**: Direct commands vs complex setup

When making changes, maintain the minimalist approach and avoid re-introducing unnecessary complexity.