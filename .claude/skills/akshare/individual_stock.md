---
name: akshare-individual-stock
description: Get detailed real-time information for specific Chinese stocks using AKShare's stock_individual_spot_xq function from Xueqiu. Use this skill when you need comprehensive financial metrics, valuation data, and detailed analysis for individual stocks.
---

# Individual Stock Analysis - Detailed Stock Information

## Instructions
This skill retrieves comprehensive stock information for individual Chinese stocks from Xueqiu (雪球). It provides detailed financial metrics, valuation data, and analysis-specific information that goes beyond basic price data.

### Usage Steps:
1. Ensure AKShare is installed (`pip install akshare`)
2. Prepare the stock symbol (e.g., "SH600000", "SZ000001")
3. Call the `stock_individual_spot_xq()` function with the symbol
4. Process the returned data for analysis

### Important Notes:
- Data source: Xueqiu (雪球) - reliable financial data provider
- More comprehensive than basic market data
- Better rate limiting compared to Sina Finance
- Ideal for detailed stock analysis and valuation

## Examples

### Basic Stock Information
```python
import akshare as ak

# Get detailed data for a specific stock
symbol = "SH600000"  # Pudong Development Bank
stock_data = ak.stock_individual_spot_xq(symbol=symbol)

print(f"Stock data for {symbol}:")
for _, row in stock_data.iterrows():
    print(f"{row['item']}: {row['value']}")
```

### Analyze Key Financial Metrics
```python
import akshare as ak

def analyze_stock(symbol):
    """Analyze key financial metrics for a stock"""
    try:
        # Get stock data
        df = ak.stock_individual_spot_xq(symbol=symbol)

        # Convert to dictionary for easier access
        data = dict(zip(df['item'], df['value']))

        # Extract key information
        name = data.get('名称', 'Unknown')
        current_price = float(data.get('现价', 0))
        pe_ratio = float(data.get('市盈率(动)', 0))
        pb_ratio = float(data.get('市净率', 0))
        dividend_yield = float(data.get('股息率(TTM)', 0))
        eps = float(data.get('每股收益', 0))
        book_value = float(data.get('每股净资产', 0))

        print(f"📊 {name} ({symbol}) Analysis:")
        print(f"Current Price: ¥{current_price:.2f}")
        print(f"P/E Ratio: {pe_ratio:.2f}")
        print(f"P/B Ratio: {pb_ratio:.2f}")
        print(f"Dividend Yield: {dividend_yield:.2f}%")
        print(f"Earnings per Share: ¥{eps:.2f}")
        print(f"Book Value per Share: ¥{book_value:.2f}")

        # Basic valuation assessment
        if pe_ratio > 0 and pe_ratio < 15:
            print("✅ P/E suggests potential value")
        elif pe_ratio > 30:
            print("⚠️  High P/E - potential overvaluation")

        if dividend_yield > 3:
            print("✅ Good dividend yield")
        elif dividend_yield > 0:
            print("📝 Moderate dividend yield")
        else:
            print("❌ No dividend")

        return data

    except Exception as e:
        print(f"Error analyzing {symbol}: {e}")
        return None

# Analyze a stock
analyze_stock("SH600000")
```

### Compare Multiple Stocks
```python
import akshare as ak
import pandas as pd

def compare_stocks(symbols):
    """Compare financial metrics across multiple stocks"""
    comparison_data = []

    for symbol in symbols:
        try:
            df = ak.stock_individual_spot_xq(symbol=symbol)
            data = dict(zip(df['item'], df['value']))

            stock_info = {
                'Symbol': symbol,
                'Name': data.get('名称', 'Unknown'),
                'Price': float(data.get('现价', 0)),
                'P/E': float(data.get('市盈率(动)', 0)),
                'P/B': float(data.get('市净率', 0)),
                'Dividend Yield %': float(data.get('股息率(TTM)', 0)),
                'EPS': float(data.get('每股收益', 0)),
                'Book Value': float(data.get('每股净资产', 0)),
                '52W High': float(data.get('52周最高', 0)),
                '52W Low': float(data.get('52周最低', 0))
            }

            comparison_data.append(stock_info)

        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")

    # Create comparison DataFrame
    comparison_df = pd.DataFrame(comparison_data)

    if not comparison_df.empty:
        print("📈 Stock Comparison:")
        print(comparison_df.to_string(index=False))

        # Find best values
        if len(comparison_df) > 1:
            print("\n🏆 Best by Category:")

            # Lowest P/E (value)
            lowest_pe = comparison_df.loc[comparison_df['P/E'].idxmin()]
            print(f"Best Value (Low P/E): {lowest_pe['Name']} ({lowest_pe['P/E']:.2f})")

            # Highest Dividend Yield
            highest_dividend = comparison_df.loc[comparison_df['Dividend Yield %'].idxmax()]
            print(f"Highest Dividend: {highest_dividend['Name']} ({highest_dividend['Dividend Yield %']:.2f}%)")

            # Closest to 52-week low
            comparison_df['Distance to Low %'] = (
                (comparison_df['Price'] - comparison_df['52W Low']) /
                comparison_df['52W Low'] * 100
            )
            near_low = comparison_df.loc[comparison_df['Distance to Low %'].idxmin()]
            print(f"Near 52W Low: {near_low['Name']} ({near_low['Distance to Low %']:.1f}%)")

    return comparison_df

# Compare major banks
bank_symbols = ["SH600000", "SH601398", "SH601939", "SH601288", "SH600016"]
compare_stocks(bank_symbols)
```

### 52-Week Range Analysis
```python
import akshare as ak

def analyze_52_week_range(symbol):
    """Analyze stock position relative to 52-week range"""
    try:
        df = ak.stock_individual_spot_xq(symbol=symbol)
        data = dict(zip(df['item'], df['value']))

        name = data.get('名称', 'Unknown')
        current_price = float(data.get('现价', 0))
        week_52_high = float(data.get('52周最高', 0))
        week_52_low = float(data.get('52周最低', 0))

        # Calculate position in range
        range_size = week_52_high - week_52_low
        if range_size > 0:
            position_in_range = (current_price - week_52_low) / range_size * 100
        else:
            position_in_range = 50

        # Distance from extremes
        distance_from_high = (week_52_high - current_price) / week_52_high * 100
        distance_from_low = (current_price - week_52_low) / week_52_low * 100

        print(f"📊 {name} ({symbol}) - 52-Week Range Analysis:")
        print(f"Current Price: ¥{current_price:.2f}")
        print(f"52-Week Range: ¥{week_52_low:.2f} - ¥{week_52_high:.2f}")
        print(f"Position in Range: {position_in_range:.1f}%")
        print(f"Distance from High: {distance_from_high:.1f}%")
        print(f"Distance from Low: {distance_from_low:.1f}%")

        # Trading signals based on range position
        if position_in_range < 20:
            print("🟢 Near 52-week low - Potential buying opportunity")
        elif position_in_range > 80:
            print("🔴 Near 52-week high - Consider taking profits")
        else:
            print("🟡 Mid-range - Wait for clearer signals")

        return {
            'name': name,
            'current_price': current_price,
            'week_52_high': week_52_high,
            'week_52_low': week_52_low,
            'position_in_range': position_in_range
        }

    except Exception as e:
        print(f"Error analyzing 52-week range for {symbol}: {e}")
        return None

# Analyze 52-week range
analyze_52_week_range("SH600000")
```

### Dividend Analysis
```python
import akshare as ak

def analyze_dividend(symbol):
    """Analyze dividend-related metrics"""
    try:
        df = ak.stock_individual_spot_xq(symbol=symbol)
        data = dict(zip(df['item'], df['value']))

        name = data.get('名称', 'Unknown')
        current_price = float(data.get('现价', 0))
        dividend_ttm = float(data.get('股息(TTM)', 0))
        dividend_yield = float(data.get('股息率(TTM)', 0))
        eps = float(data.get('每股收益', 0))

        print(f"💰 {name} ({symbol}) - Dividend Analysis:")
        print(f"Current Price: ¥{current_price:.2f}")
        print(f"Dividend (TTM): ¥{dividend_ttm:.3f}")
        print(f"Dividend Yield (TTM): {dividend_yield:.2f}%")
        print(f"Earnings per Share: ¥{eps:.2f}")

        # Payout ratio (if we have EPS data)
        if eps > 0:
            payout_ratio = (dividend_ttm / eps) * 100
            print(f"Payout Ratio: {payout_ratio:.1f}%")

            if payout_ratio < 30:
                print("✅ Low payout ratio - Sustainable dividends")
            elif payout_ratio > 70:
                print("⚠️  High payout ratio - May not be sustainable")
            else:
                print("🟡 Moderate payout ratio")

        # Dividend quality assessment
        if dividend_yield > 5:
            print("🔥 High dividend yield - Verify sustainability")
        elif dividend_yield > 3:
            print("✅ Good dividend yield")
        elif dividend_yield > 1:
            print("📝 Moderate dividend yield")
        else:
            print("❌ Low or no dividend")

        return {
            'name': name,
            'dividend_yield': dividend_yield,
            'dividend_ttm': dividend_ttm,
            'payout_ratio': payout_ratio if eps > 0 else None
        }

    except Exception as e:
        print(f"Error analyzing dividend for {symbol}: {e}")
        return None

# Analyze dividend
analyze_dividend("SH600000")
```

### Comprehensive Stock Analysis
```python
import akshare as ak
import time

def comprehensive_analysis(symbol):
    """Perform comprehensive stock analysis"""
    print(f"🔍 Starting comprehensive analysis for {symbol}...")

    try:
        # Get stock data
        df = ak.stock_individual_spot_xq(symbol=symbol)
        data = dict(zip(df['item'], df['value']))

        name = data.get('名称', 'Unknown')
        print(f"\n📊 {name} ({symbol}) - Comprehensive Analysis")
        print("="*60)

        # Basic Information
        print("\n📈 Basic Information:")
        print(f"Current Price: ¥{float(data.get('现价', 0)):.2f}")
        print(f"Today's Change: {float(data.get('涨跌', 0)):+.2f} ({float(data.get('涨幅', 0)):+.2f}%)")
        print(f"52-Week Range: ¥{float(data.get('52周最低', 0)):.2f} - ¥{float(data.get('52周最高', 0)):.2f}")

        # Valuation Metrics
        print("\n💰 Valuation Metrics:")
        print(f"P/E Ratio (Dynamic): {float(data.get('市盈率(动)', 0)):.2f}")
        print(f"P/E Ratio (Static): {float(data.get('市盈率(静)', 0)):.2f}")
        print(f"P/E Ratio (TTM): {float(data.get('市盈率(TTM)', 0)):.2f}")
        print(f"P/B Ratio: {float(data.get('市净率', 0)):.3f}")

        # Financial Health
        print("\n🏥 Financial Health:")
        print(f"Earnings per Share: ¥{float(data.get('每股收益', 0)):.2f}")
        print(f"Book Value per Share: ¥{float(data.get('每股净资产', 0)):.2f}")
        print(f"Return on Equity: {float(data.get('净资产中的商誉', 0)):.3f}")

        # Dividend Information
        print("\n💸 Dividend Information:")
        print(f"Dividend (TTM): ¥{float(data.get('股息(TTM)', 0)):.3f}")
        print(f"Dividend Yield (TTM): {float(data.get('股息率(TTM)', 0)):.2f}%")

        # Trading Information
        print("\n📊 Trading Information:")
        print(f"Volume: {int(float(data.get('成交量', 0))):,}")
        print(f"Turnover Rate: {float(data.get('周转率', 0)):.2f}%")
        print(f"Average Price: ¥{float(data.get('均价', 0)):.2f}")

        # Market Information
        print("\n🌍 Market Information:")
        print(f"Market Cap: {float(data.get('流通值', 0)):.0f}")
        print(f"Shares Outstanding: {int(float(data.get('流通股', 0))):,}")
        print(f"Exchange: {data.get('交易所', 'Unknown')}")

        # Investment Summary
        print("\n📝 Investment Summary:")
        pe_ratio = float(data.get('市盈率(动)', 0))
        pb_ratio = float(data.get('市净率', 0))
        dividend_yield = float(data.get('股息率(TTM)', 0))
        current_price = float(data.get('现价', 0))
        week_52_high = float(data.get('52周最高', 0))
        week_52_low = float(data.get('52周最低', 0))

        # Value assessment
        if 0 < pe_ratio < 15:
            print("✅ Attractive valuation (Low P/E)")
        elif 15 <= pe_ratio < 25:
            print("🟡 Reasonable valuation (Moderate P/E)")
        elif pe_ratio >= 25:
            print("⚠️  High valuation (High P/E)")

        # P/B assessment
        if 0 < pb_ratio < 1:
            print("✅ Trading below book value")
        elif 1 <= pb_ratio < 3:
            print("🟡 Reasonable P/B ratio")
        elif pb_ratio >= 3:
            print("⚠️  High P/B ratio")

        # Dividend assessment
        if dividend_yield > 4:
            print("💰 High dividend yield - Income focused")
        elif 2 < dividend_yield <= 4:
            print("📝 Good dividend yield - Balanced")
        elif 0 < dividend_yield <= 2:
            print("📈 Low dividend - Growth focused")
        else:
            print("❌ No dividend")

        # 52-week position
        if week_52_high > 0 and week_52_low > 0:
            position = (current_price - week_52_low) / (week_52_high - week_52_low) * 100
            if position < 25:
                print("🟢 Near 52-week low - Potential opportunity")
            elif position > 75:
                print("🔴 Near 52-week high - Be cautious")
            else:
                print("🟡 Mid-range position")

        return data

    except Exception as e:
        print(f"Error in comprehensive analysis: {e}")
        return None

# Run comprehensive analysis
comprehensive_analysis("SH600000")
```

### Stock Screening with Custom Criteria
```python
import akshare as ak

def screen_stocks(symbols, criteria):
    """Screen stocks based on custom criteria"""
    results = []

    for symbol in symbols:
        try:
            df = ak.stock_individual_spot_xq(symbol=symbol)
            data = dict(zip(df['item'], df['value']))

            # Extract key metrics
            stock_info = {
                'symbol': symbol,
                'name': data.get('名称', 'Unknown'),
                'price': float(data.get('现价', 0)),
                'pe_ratio': float(data.get('市盈率(动)', 0)),
                'pb_ratio': float(data.get('市净率', 0)),
                'dividend_yield': float(data.get('股息率(TTM)', 0)),
                'eps': float(data.get('每股收益', 0))
            }

            # Apply screening criteria
            passes_screen = True

            if criteria.get('max_pe') and stock_info['pe_ratio'] > criteria['max_pe']:
                passes_screen = False
            if criteria.get('max_pb') and stock_info['pb_ratio'] > criteria['max_pb']:
                passes_screen = False
            if criteria.get('min_dividend') and stock_info['dividend_yield'] < criteria['min_dividend']:
                passes_screen = False
            if criteria.get('min_eps') and stock_info['eps'] < criteria['min_eps']:
                passes_screen = False
            if criteria.get('max_price') and stock_info['price'] > criteria['max_price']:
                passes_screen = False

            if passes_screen:
                results.append(stock_info)

        except Exception as e:
            print(f"Error screening {symbol}: {e}")

    return results

# Define screening criteria
value_criteria = {
    'max_pe': 15,      # Maximum P/E ratio
    'max_pb': 2,       # Maximum P/B ratio
    'min_dividend': 3, # Minimum dividend yield (%)
    'max_price': 50    # Maximum price
}

# Screen bank stocks
bank_symbols = ["SH600000", "SH601398", "SH601939", "SH601288", "SH600016", "SH601166", "SH601229"]
screened_stocks = screen_stocks(bank_symbols, value_criteria)

print(f"📊 Stocks passing value screen:")
for stock in screened_stocks:
    print(f"{stock['name']} ({stock['symbol']}): "
          f"¥{stock['price']:.2f}, P/E: {stock['pe_ratio']:.2f}, "
          f"P/B: {stock['pb_ratio']:.2f}, Div: {stock['dividend_yield']:.2f}%")
```

## Key Data Fields

The returned data includes comprehensive information:

### Basic Market Data
- `代码`: Stock code
- `名称`: Stock name
- `现价`: Current price
- `涨跌`: Price change
- `涨幅`: Percentage change

### Valuation Metrics
- `市盈率(动)`: Dynamic P/E ratio
- `市盈率(静)`: Static P/E ratio
- `市盈率(TTM)`: TTM P/E ratio
- `市净率`: P/B ratio

### Financial Metrics
- `每股收益`: Earnings per share (EPS)
- `每股净资产`: Book value per share
- `净资产中的商誉`: Goodwill in net assets

### Dividend Information
- `股息(TTM)`: Dividend per share (TTM)
- `股息率(TTM)`: Dividend yield (TTM)

### Trading Information
- `成交量`: Trading volume
- `成交额`: Trading value
- `周转率`: Turnover rate
- `均价`: Average price
- `振幅`: Price amplitude

### Price Range
- `52周最高`: 52-week high
- `52周最低`: 52-week low
- `最高`: Today's high
- `最低`: Today's low
- `今开`: Opening price
- `昨收`: Previous close

### Market Information
- `流通值`: Market cap of floating shares
- `流通股`: Number of floating shares
- `基金份额/总股本`: Total shares
- `交易所`: Exchange code

## Usage Recommendations

1. **Investment Analysis**: Use comprehensive analysis for investment decisions
2. **Stock Screening**: Apply custom criteria to find suitable stocks
3. **Value Investing**: Focus on low P/E, low P/B stocks with good dividends
4. **Risk Assessment**: Analyze 52-week ranges and volatility
5. **Portfolio Management**: Compare multiple stocks before adding to portfolio

For market-wide screening and finding investment candidates, use the [market_overview.md](market_overview.md) skill first, then use this skill for detailed analysis.