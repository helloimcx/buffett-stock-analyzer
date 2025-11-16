---
name: akshare
description: Query Chinese stock market data using AKShare library. Use this skill when you need to get real-time stock prices, detailed stock information, and market metrics for Chinese A-share stocks.
---

# AKShare Chinese Stock Market Data

## Instructions
This skill provides access to Chinese stock market data through the AKShare library. It includes capabilities for both broad market screening and detailed individual stock analysis.

### Available Sub-skills:
- **Market Overview**: Get real-time data for all A-share stocks
- **Individual Stock Analysis**: Get detailed information for specific stocks
- **Historical Data**: Get historical price data with adjustment options

### Usage Steps:
1. Choose the appropriate sub-skill based on your needs
2. Ensure AKShare is installed (`pip install akshare`)
3. Follow the specific instructions for the chosen sub-skill
4. Handle rate limiting appropriately for each data source

## Sub-skills

### 📊 Market Overview
For getting real-time market data for all Chinese A-share stocks.

**File**: [market_overview.md](market_overview.md)

Use this when you need to:
- Screen all stocks in the Chinese A-share market
- Find top gainers/losers
- Filter stocks by price ranges
- Export market data for analysis
- Monitor overall market activity

**Data Source**: Sina Finance
**Coverage**: 5300+ stocks from Shanghai, Shenzhen, and Beijing exchanges
**Key Features**: Real-time prices, volume, basic market metrics

### 🔍 Individual Stock Analysis
For getting detailed information about specific stocks.

**File**: [individual_stock.md](individual_stock.md)

Use this when you need to:
- Analyze a specific stock in detail
- Get comprehensive financial metrics
- Access 52-week high/low data
- View dividend yields and ratios
- Understand valuation metrics

**Data Source**: Xueqiu (雪球)
**Coverage**: Individual stocks with detailed metrics
**Key Features**: P/E ratios, dividend yields, market cap, turnover rates

### 📈 Historical Data Analysis
For getting historical price data with various adjustment options.

**File**: [historical_data.md](historical_data.md)

Use this when you need to:
- Analyze historical price trends
- Calculate technical indicators
- Perform backtesting
- Study price patterns
- Calculate returns and volatility

**Data Source**: Tencent Securities
**Coverage**: Historical daily data with forward/backward adjustment
**Key Features**: OHLCV data, multiple adjustment methods, date range queries

## Quick Examples

### Market Screening
```python
# Get all A-share real-time data
# See: market_overview.md
```

### Stock Analysis
```python
# Get detailed stock data
# See: individual_stock.md
```

### Historical Analysis
```python
# Get historical price data
# See: historical_data.md
```

## Important Notes

### Rate Limiting
- **Sina Finance**: Avoid frequent requests (< 30 seconds intervals)
- **Xueqiu**: Less restrictive but still use reasonable intervals
- **Tencent Securities**: Moderate restrictions, reasonable for historical queries

### Data Coverage
- **Market Overview**: All A-share stocks (沪深京 A 股)
- **Individual Stock**: Any stock symbol supported by Xueqiu
- **Historical Data**: Historical daily data for any A-share stock

### Usage Recommendations
- Use `market_overview.md` for market scanning and initial screening
- Use `individual_stock.md` for detailed analysis of promising stocks
- Use `historical_data.md` for trend analysis and technical research
- Consider caching results to avoid excessive API calls

## Data Sources Comparison

| Feature | Market Overview | Individual Stock | Historical Data |
|---------|----------------|-----------------|-----------------|
| Source | Sina Finance | Xueqiu | Tencent Securities |
| Coverage | All A-share stocks | Individual stocks | Historical daily data |
| Update Speed | Real-time | Real-time | Daily |
| Detail Level | Basic metrics | Comprehensive | OHLCV with adjustments |
| Rate Limits | Strict | Moderate | Reasonable |
| Time Range | Current only | Current only | Historical (years) |

For detailed usage examples and advanced features, refer to the specific sub-skill files.