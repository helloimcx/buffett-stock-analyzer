---
name: akshare-market-overview
description: Get real-time market data for all Chinese A-share stocks using AKShare's stock_zh_a_spot function. Use this skill when you need to screen the entire market, find top gainers/losers, or analyze market-wide trends.
---

# Market Overview - Real-time A-share Data

## Instructions
This skill retrieves real-time stock market data for all Chinese A-share stocks from Sina Finance. It provides comprehensive market coverage with basic trading metrics for market screening and analysis.

### Usage Steps:
1. Ensure AKShare is installed (`pip install akshare`)
2. Call the `stock_zh_a_spot()` function from AKShare
3. Process the returned DataFrame for analysis
4. **IMPORTANT**: Add delays (30+ seconds) between requests to avoid IP blocking

### Important Notes:
- Returns data for 5300+ stocks from Shanghai, Shenzhen, and Beijing exchanges
- Sina Finance may temporarily block IPs for repeated calls
- Ideal for market screening, not high-frequency monitoring
- Use for finding investment opportunities and market trends

## Examples

### Basic Market Overview
```python
import akshare as ak

# Get all real-time stock data
market_data = ak.stock_zh_a_spot()
print(f"Total stocks: {len(market_data)}")
print(market_data.head())
```

### Find Top Gainers
```python
import akshare as ak

# Get market data
df = ak.stock_zh_a_spot()

# Filter for stocks with meaningful price changes and volume
active_stocks = df[
    (df['成交量'] > 1000000) &  # Minimum 1M shares volume
    (df['最新价'] > 1) &        # Minimum 1 yuan price
    (df['涨跌幅'] != 0)         # Exclude unchanged stocks
]

# Get top 10 gainers
top_gainers = active_stocks.nlargest(10, '涨跌幅')
print("🔥 Top 10 Gainers:")
for _, stock in top_gainers.iterrows():
    print(f"{stock['名称']} ({stock['代码']}): "
          f"¥{stock['最新价']:.2f} (+{stock['涨跌幅']:.2f}%)")
```

### Find Top Losers
```python
import akshare as ak

# Get market data
df = ak.stock_zh_a_spot()

# Filter active stocks
active_stocks = df[df['成交量'] > 1000000]

# Get top 10 losers
top_losers = active_stocks.nsmallest(10, '涨跌幅')
print("📉 Top 10 Losers:")
for _, stock in top_losers.iterrows():
    print(f"{stock['名称']} ({stock['代码']}): "
          f"¥{stock['最新价']:.2f} ({stock['涨跌幅']:.2f}%)")
```

### Filter by Price Range
```python
import akshare as ak

# Get market data
df = ak.stock_zh_a_spot()

# Filter for stocks in different price ranges
penny_stocks = df[(df['最新价'] >= 1) & (df['最新价'] < 10)]
mid_range = df[(df['最新价'] >= 10) & (df['最新价'] < 50)]
premium = df[df['最新价'] >= 50]

print(f"Penny stocks (1-10 yuan): {len(penny_stocks)}")
print(f"Mid-range stocks (10-50 yuan): {len(mid_range)}")
print(f"Premium stocks (50+ yuan): {len(premium)}")
```

### Market Analysis
```python
import akshare as ak
import pandas as pd

# Get market data
df = ak.stock_zh_a_spot()

# Market statistics
total_stocks = len(df)
active_stocks = df[df['成交量'] > 0]
gainers = len(active_stocks[active_stocks['涨跌幅'] > 0])
losers = len(active_stocks[active_stocks['涨跌幅'] < 0])

# Calculate totals
total_volume = active_stocks['成交量'].sum()
total_value = active_stocks['成交额'].sum()
avg_price = active_stocks['最新价'].mean()

print("📊 Market Summary:")
print(f"Total Stocks: {total_stocks:,}")
print(f"Active Stocks: {len(active_stocks):,}")
print(f"Gainers: {gainers} ({gainers/len(active_stocks)*100:.1f}%)")
print(f"Losers: {losers} ({losers/len(active_stocks)*100:.1f}%)")
print(f"Average Price: ¥{avg_price:.2f}")
print(f"Total Volume: {total_volume:,.0f} shares")
print(f"Total Value: ¥{total_value:,.0f}")

# Find most active stocks by volume
most_active = active_stocks.nlargest(5, '成交量')
print("\n🔥 Most Active by Volume:")
for _, stock in most_active.iterrows():
    print(f"{stock['名称']}: {stock['成交量']:,.0f} shares")
```

### Export Market Data
```python
import akshare as ak
from datetime import datetime

# Get market data
df = ak.stock_zh_a_spot()

# Generate filename with timestamp
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"market_data_{timestamp}.csv"

# Export to CSV
df.to_csv(filename, index=False, encoding='utf-8-sig')
print(f"Market data exported to {filename}")
print(f"Total stocks exported: {len(df)}")
```

### Search for Specific Stocks
```python
import akshare as ak

# Get market data
df = ak.stock_zh_a_spot()

# Search for banks
banks = df[df['名称'].str.contains('银行', na=False)]
print(f"Found {len(banks)} bank stocks:")
print(banks[['代码', '名称', '最新价', '涨跌幅']].head())

# Search for specific stock by name
search_term = "平安"
ping_an = df[df['名称'].str.contains(search_term, na=False)]
print(f"\nFound {len(ping_an)} stocks containing '{search_term}':")
for _, stock in ping_an.iterrows():
    print(f"{stock['名称']} ({stock['代码']}): ¥{stock['最新价']:.2f}")
```

### Real-time Market Monitoring
```python
import akshare as ak
import time
from datetime import datetime

def monitor_market():
    """Monitor market with rate limiting"""
    while True:
        try:
            print(f"\n{'='*50}")
            print(f"Market Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

            # Get market data
            df = ak.stock_zh_a_spot()

            # Basic statistics
            active_stocks = df[df['成交量'] > 0]
            gainers = len(active_stocks[active_stocks['涨跌幅'] > 0])
            losers = len(active_stocks[active_stocks['涨跌幅'] < 0])

            print(f"Active: {len(active_stocks)} | Gainers: {gainers} | Losers: {losers}")

            # Top 3 gainers and losers
            top_gainers = active_stocks.nlargest(3, '涨跌幅')
            top_losers = active_stocks.nsmallest(3, '涨跌幅')

            print("\n🔥 Top Gainers:")
            for _, stock in top_gainers.iterrows():
                print(f"  {stock['名称']}: +{stock['涨跌幅']:.2f}%")

            print("\n📉 Top Losers:")
            for _, stock in top_losers.iterrows():
                print(f"  {stock['名称']}: {stock['涨跌幅']:.2f}%")

            print(f"{'='*50}")

            # Wait 60 seconds before next update (IMPORTANT for rate limiting)
            time.sleep(60)

        except Exception as e:
            print(f"Error: {e}")
            time.sleep(120)  # Wait longer on error

# Run monitoring (uncomment to start)
# monitor_market()
```

### Filter by Exchange
```python
import akshare as ak

# Get market data
df = ak.stock_zh_a_spot()

# Filter by exchange
sh_stocks = df[df['代码'].str.startswith('sh')]
sz_stocks = df[df['代码'].str.startswith('sz')]
bj_stocks = df[df['代码'].str.startswith('bj')]

print(f"Shanghai Stock Exchange: {len(sh_stocks)} stocks")
print(f"Shenzhen Stock Exchange: {len(sz_stocks)} stocks")
print(f"Beijing Stock Exchange: {len(bj_stocks)} stocks")

# Show top performers from each exchange
print("\nShanghai Top Gainer:")
sh_top = sh_stocks.nlargest(1, '涨跌幅')
if not sh_top.empty:
    stock = sh_top.iloc[0]
    print(f"{stock['名称']} ({stock['代码']}): +{stock['涨跌幅']:.2f}%")

print("\nShenzhen Top Gainer:")
sz_top = sz_stocks.nlargest(1, '涨跌幅')
if not sz_top.empty:
    stock = sz_top.iloc[0]
    print(f"{stock['名称']} ({stock['代码']}): +{stock['涨跌幅']:.2f}%")
```

## Output Columns Description

The returned DataFrame contains these columns:
- `代码`: Stock code (e.g., "sz000001", "sh600000")
- `名称`: Stock name
- `最新价`: Current price
- `涨跌额`: Price change amount
- `涨跌幅`: Price change percentage
- `买入`: Bid price
- `卖出`: Ask price
- `昨收`: Yesterday's closing price
- `今开`: Today's opening price
- `最高`: Today's highest price
- `最低`: Today's lowest price
- `成交量`: Trading volume (shares)
- `成交额`: Trading value (yuan)
- `时间戳`: Update timestamp

## Rate Limiting Guidelines

**CRITICAL**: Sina Finance strictly limits request frequency:
- **Minimum interval**: 30-60 seconds between requests
- **Recommended interval**: 60+ seconds for continuous monitoring
- **Consequences**: Temporary IP blocking for excessive requests

**Best Practices**:
- Cache results when possible
- Use batch operations instead of individual stock queries
- Implement exponential backoff on errors
- Consider using the individual stock skill for detailed analysis

For more detailed analysis of specific stocks, use the [individual_stock.md](individual_stock.md) skill.