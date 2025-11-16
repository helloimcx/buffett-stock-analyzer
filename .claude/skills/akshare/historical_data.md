---
name: akshare-historical-data
description: Get historical stock price data with adjustment options using AKShare's stock_zh_a_hist_tx function from Tencent Securities. Use this skill when you need to analyze historical price trends, calculate technical indicators, perform backtesting, or study price patterns.
---

# Historical Data Analysis - Stock Price History

## Instructions
This skill retrieves historical daily stock price data from Tencent Securities with comprehensive adjustment options. It provides OHLCV (Open, High, Low, Close, Volume) data suitable for technical analysis and research.

### Usage Steps:
1. Ensure AKShare is installed (`pip install akshare`)
2. Prepare stock symbol (e.g., "sz000001", "sh600000")
3. Set date range (start_date, end_date) in YYYYMMDD format
4. Choose adjustment type (forward, backward, or none)
5. Call the `stock_zh_a_hist_tx()` function with parameters

### Adjustment Types:
- **No adjustment (`""`)**: Raw historical prices (may have gaps from splits/dividends)
- **Forward adjustment (`"qfq"`)**: Adjusts historical prices, keeps current price unchanged
- **Backward adjustment (`"hfq"`)**: Adjusts current price, keeps historical prices unchanged

### Important Notes:
- Data frequency: Daily
- Update timing: After market close for current day data
- Recommended for quantitative research: Backward adjustment (hfq)
- Recommended for charting: Forward adjustment (qfq)

## Examples

### Basic Historical Data Retrieval
```python
import akshare as ak

# Get basic historical data (no adjustment)
symbol = "sz000001"  # Ping An Bank
start_date = "20230101"
end_date = "20231231"

hist_data = ak.stock_zh_a_hist_tx(
    symbol=symbol,
    start_date=start_date,
    end_date=end_date,
    adjust=""
)

print(f"Historical data for {symbol} from {start_date} to {end_date}:")
print(f"Total records: {len(hist_data)}")
print(hist_data.head())
```

### Forward Adjusted Data for Charting
```python
import akshare as ak

# Get forward-adjusted data (recommended for charting)
symbol = "sh600000"  # Pudong Development Bank
start_date = "20230101"
end_date = "20231231"

forward_adj_data = ak.stock_zh_a_hist_tx(
    symbol=symbol,
    start_date=start_date,
    end_date=end_date,
    adjust="qfq"  # Forward adjustment
)

print(f"Forward-adjusted data for {symbol}:")
print(forward_adj_data.head(10))

# Show price progression
print("\nPrice progression:")
for i, row in forward_adj_data.head(5).iterrows():
    print(f"{row['date']}: ¥{row['close']:.2f}")
```

### Backward Adjusted Data for Research
```python
import akshare as ak

# Get backward-adjusted data (recommended for research)
symbol = "sz000001"
start_date = "20200101"
end_date = "20231231"

backward_adj_data = ak.stock_zh_a_hist_tx(
    symbol=symbol,
    start_date=start_date,
    end_date=end_date,
    adjust="hfq"  # Backward adjustment
)

print(f"Backward-adjusted data for {symbol}:")
print(backward_adj_data.head())

# Compare with no adjustment to see the difference
no_adj_data = ak.stock_zh_a_hist_tx(
    symbol=symbol,
    start_date="20200101",
    end_date="20200110",
    adjust=""
)

print(f"\nComparison of adjustments:")
print("Date        | No Adj | Forward Adj | Backward Adj")
print("-" * 45)
for i, row in no_adj_data.iterrows():
    forward = forward_adj_data[forward_adj_data['date'] == row['date']]['close'].iloc[0]
    backward = backward_adj_data[backward_adj_data['date'] == row['date']]['close'].iloc[0]
    print(f"{row['date']} | {row['close']:6.2f} | {forward:11.2f} | {backward:12.2f}")
```

### Calculate Returns and Volatility
```python
import akshare as ak
import pandas as pd
import numpy as np

def calculate_returns_and_volatility(symbol, start_date, end_date):
    """Calculate returns and volatility for a stock"""

    # Get historical data
    df = ak.stock_zh_a_hist_tx(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        adjust="hfq"  # Use backward-adjusted for accurate returns
    )

    # Sort by date
    df = df.sort_values('date')
    df.reset_index(drop=True, inplace=True)

    # Calculate daily returns
    df['daily_return'] = df['close'].pct_change() * 100

    # Calculate cumulative returns
    df['cumulative_return'] = (1 + df['daily_return']/100).cumprod() - 1

    # Calculate rolling volatility (30-day)
    df['volatility_30d'] = df['daily_return'].rolling(window=30).std() * np.sqrt(252)

    # Basic statistics
    total_return = (df['close'].iloc[-1] / df['close'].iloc[0] - 1) * 100
    annual_return = total_return * (252 / len(df))
    avg_volatility = df['volatility_30d'].mean()
    max_drawdown = calculate_max_drawdown(df['close'])

    print(f"📊 {symbol} Performance Analysis:")
    print(f"Period: {start_date} to {end_date}")
    print(f"Trading Days: {len(df)}")
    print(f"Start Price: ¥{df['close'].iloc[0]:.2f}")
    print(f"End Price: ¥{df['close'].iloc[-1]:.2f}")
    print(f"Total Return: {total_return:.2f}%")
    print(f"Annualized Return: {annual_return:.2f}%")
    print(f"Average Volatility: {avg_volatility:.2f}%")
    print(f"Maximum Drawdown: {max_drawdown:.2f}%")

    return df

def calculate_max_drawdown(prices):
    """Calculate maximum drawdown"""
    peak = prices.expanding().max()
    drawdown = (prices - peak) / peak * 100
    return drawdown.min()

# Analyze a stock
symbol = "sz000001"
start_date = "20220101"
end_date = "20231231"

analysis_df = calculate_returns_and_volatility(symbol, start_date, end_date)

# Show recent performance
print(f"\nRecent Performance (Last 10 trading days):")
print(analysis_df[['date', 'close', 'daily_return', 'cumulative_return']].tail(10))
```

### Moving Averages Analysis
```python
import akshare as ak
import pandas as pd
import matplotlib.pyplot as plt

def analyze_moving_averages(symbol, start_date, end_date):
    """Analyze moving averages for a stock"""

    # Get historical data
    df = ak.stock_zh_a_hist_tx(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        adjust="qfq"  # Forward adjustment for charting
    )

    # Sort by date
    df = df.sort_values('date')
    df.reset_index(drop=True, inplace=True)

    # Calculate moving averages
    df['ma5'] = df['close'].rolling(window=5).mean()
    df['ma10'] = df['close'].rolling(window=10).mean()
    df['ma20'] = df['close'].rolling(window=20).mean()
    df['ma50'] = df['close'].rolling(window=50).mean()
    df['ma200'] = df['close'].rolling(window=200).mean()

    # Calculate moving average signals
    df['ma_signal'] = 0
    df.loc[df['ma5'] > df['ma20'], 'ma_signal'] = 1  # Bullish
    df.loc[df['ma5'] < df['ma20'], 'ma_signal'] = -1  # Bearish

    # Find crossover points
    df['crossover'] = 0
    df.loc[(df['ma_signal'] == 1) & (df['ma_signal'].shift(1) == -1), 'crossover'] = 1  # Golden cross
    df.loc[(df['ma_signal'] == -1) & (df['ma_signal'].shift(1) == 1), 'crossover'] = -1  # Death cross

    print(f"📈 {symbol} Moving Average Analysis:")
    print(f"Latest Price: ¥{df['close'].iloc[-1]:.2f}")
    print(f"MA5: ¥{df['ma5'].iloc[-1]:.2f}")
    print(f"MA20: ¥{df['ma20'].iloc[-1]:.2f}")
    print(f"MA50: ¥{df['ma50'].iloc[-1]:.2f}")
    print(f"MA200: ¥{df['ma200'].iloc[-1]:.2f}")

    # Current trend analysis
    latest = df.iloc[-1]
    if latest['ma5'] > latest['ma20'] > latest['ma50']:
        print("🟢 Strong uptrend - All shorter MAs above longer ones")
    elif latest['ma5'] < latest['ma20'] < latest['ma50']:
        print("🔴 Strong downtrend - All shorter MAs below longer ones")
    else:
        print("🟡 Mixed signals - Wait for clearer trend")

    # Show recent crossovers
    recent_crossovers = df[df['crossover'] != 0].tail(5)
    if not recent_crossovers.empty:
        print(f"\nRecent Crossovers:")
        for _, row in recent_crossovers.iterrows():
            signal = "🟢 Golden Cross" if row['crossover'] == 1 else "🔴 Death Cross"
            print(f"{row['date']}: {signal} at ¥{row['close']:.2f}")

    return df

# Analyze moving averages
symbol = "sh600000"
start_date = "20230101"
end_date = "20231231"

ma_df = analyze_moving_averages(symbol, start_date, end_date)

# Show recent MA data
print(f"\nRecent Moving Average Data (Last 10 days):")
print(ma_df[['date', 'close', 'ma5', 'ma20', 'ma50']].tail(10))
```

### Support and Resistance Analysis
```python
import akshare as ak
import pandas as pd
import numpy as np

def find_support_resistance(df, window=20):
    """Find potential support and resistance levels"""

    highs = df['high'].rolling(window=window, center=True).max()
    lows = df['low'].rolling(window=window, center=True).min()

    # Resistance levels (local highs)
    resistance_levels = []
    for i in range(window, len(df) - window):
        if df['high'].iloc[i] == highs.iloc[i]:
            resistance_levels.append({
                'date': df['date'].iloc[i],
                'price': df['high'].iloc[i],
                'type': 'resistance'
            })

    # Support levels (local lows)
    support_levels = []
    for i in range(window, len(df) - window):
        if df['low'].iloc[i] == lows.iloc[i]:
            support_levels.append({
                'date': df['date'].iloc[i],
                'price': df['low'].iloc[i],
                'type': 'support'
            })

    return support_levels, resistance_levels

def analyze_support_resistance(symbol, start_date, end_date):
    """Analyze support and resistance levels"""

    # Get historical data
    df = ak.stock_zh_a_hist_tx(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        adjust="qfq"
    )

    df = df.sort_values('date')

    # Find support and resistance levels
    support, resistance = find_support_resistance(df)

    print(f"🎯 {symbol} Support & Resistance Analysis:")
    print(f"Current Price: ¥{df['close'].iloc[-1]:.2f}")

    # Show recent resistance levels
    if resistance:
        print(f"\n📈 Recent Resistance Levels:")
        for level in sorted(resistance, key=lambda x: x['price'], reverse=True)[:5]:
            print(f"¥{level['price']:.2f} ({level['date']})")

    # Show recent support levels
    if support:
        print(f"\n📉 Recent Support Levels:")
        for level in sorted(support, key=lambda x: x['price'])[:5]:
            print(f"¥{level['price']:.2f} ({level['date']})")

    # Find closest support and resistance
    current_price = df['close'].iloc[-1]

    closest_resistance = min([r for r in resistance if r['price'] > current_price],
                            key=lambda x: x['price'], default=None)
    closest_support = max([s for s in support if s['price'] < current_price],
                         key=lambda x: x['price'], default=None)

    if closest_resistance:
        resistance_distance = (closest_resistance['price'] - current_price) / current_price * 100
        print(f"\nClosest Resistance: ¥{closest_resistance['price']:.2f} ({resistance_distance:.1f}% above)")

    if closest_support:
        support_distance = (current_price - closest_support['price']) / current_price * 100
        print(f"Closest Support: ¥{closest_support['price']:.2f} ({support_distance:.1f}% below)")

    return df, support, resistance

# Analyze support and resistance
symbol = "sz000001"
start_date = "20230101"
end_date = "20231231"

price_df, support_levels, resistance_levels = analyze_support_resistance(symbol, start_date, end_date)
```

### Volume Analysis
```python
import akshare as ak
import pandas as pd

def analyze_volume(symbol, start_date, end_date):
    """Analyze trading volume patterns"""

    # Get historical data
    df = ak.stock_zh_a_hist_tx(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        adjust="hfq"
    )

    df = df.sort_values('date')
    df.reset_index(drop=True, inplace=True)

    # Calculate volume metrics
    df['volume_ma20'] = df['amount'].rolling(window=20).mean()
    df['volume_ratio'] = df['amount'] / df['volume_ma20']
    df['price_change'] = df['close'].pct_change() * 100

    # Find high volume days (volume > 2x average)
    high_volume_days = df[df['volume_ratio'] > 2.0]

    # Find volume-price divergence
    df['volume_price_signal'] = 0
    # High volume + big price move = strong signal
    df.loc[(df['volume_ratio'] > 2) & (abs(df['price_change']) > 3), 'volume_price_signal'] = 1

    print(f"📊 {symbol} Volume Analysis:")
    print(f"Average Volume (20 days): {df['volume_ma20'].iloc[-1]:.0f}")
    print(f"Latest Volume: {df['amount'].iloc[-1]:.0f}")
    print(f"Volume Ratio: {df['volume_ratio'].iloc[-1]:.2f}")

    # Volume assessment
    latest_volume_ratio = df['volume_ratio'].iloc[-1]
    if latest_volume_ratio > 2:
        print("🔥 High volume day - Potential breakout or reversal")
    elif latest_volume_ratio < 0.5:
        print"📉 Low volume day - Lack of interest")
    else:
        print("📝 Normal volume - Continuation likely")

    # Show high volume days
    if not high_volume_days.empty:
        print(f"\n🚀 High Volume Days (>2x average):")
        for _, day in high_volume_days.tail(5).iterrows():
            direction = "📈" if day['price_change'] > 0 else "📉"
            print(f"{day['date']}: {direction} {day['price_change']:+.2f}% with {day['volume_ratio']:.1f}x volume")

    return df

# Analyze volume
symbol = "sh600000"
start_date = "20230101"
end_date = "20231231"

volume_df = analyze_volume(symbol, start_date, end_date)
```

### Multi-Stock Comparison
```python
import akshare as ak
import pandas as pd
import matplotlib.pyplot as plt

def compare_stocks_performance(symbols, start_date, end_date):
    """Compare performance of multiple stocks"""

    comparison_data = {}

    for symbol in symbols:
        try:
            # Get historical data
            df = ak.stock_zh_a_hist_tx(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                adjust="hfq"  # Use backward adjustment for fair comparison
            )

            df = df.sort_values('date')

            # Calculate normalized returns (starting from 100)
            df['normalized'] = (df['close'] / df['close'].iloc[0]) * 100

            # Calculate performance metrics
            total_return = (df['close'].iloc[-1] / df['close'].iloc[0] - 1) * 100
            max_price = df['high'].max()
            min_price = df['low'].min()
            volatility = df['close'].pct_change().std() * 100

            comparison_data[symbol] = {
                'data': df,
                'total_return': total_return,
                'max_price': max_price,
                'min_price': min_price,
                'volatility': volatility,
                'final_normalized': df['normalized'].iloc[-1]
            }

        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")

    # Print comparison results
    print("📊 Multi-Stock Performance Comparison:")
    print(f"Period: {start_date} to {end_date}")
    print("-" * 60)

    for symbol, data in comparison_data.items():
        print(f"{symbol}:")
        print(f"  Total Return: {data['total_return']:+.2f}%")
        print(f"  Volatility: {data['volatility']:.2f}%")
        print(f"  Price Range: ¥{data['min_price']:.2f} - ¥{data['max_price']:.2f}")
        print(f"  Final Normalized: {data['final_normalized']:.2f}")
        print()

    # Find best and worst performers
    if comparison_data:
        best_performer = max(comparison_data.items(), key=lambda x: x[1]['total_return'])
        worst_performer = min(comparison_data.items(), key=lambda x: x[1]['total_return'])

        print(f"🏆 Best Performer: {best_performer[0]} ({best_performer[1]['total_return']:+.2f}%)")
        print(f"📉 Worst Performer: {worst_performer[0]} ({worst_performer[1]['total_return']:+.2f}%)")

    return comparison_data

# Compare multiple bank stocks
bank_symbols = ["SH600000", "SH601398", "SH601939", "SH601288"]
start_date = "20230101"
end_date = "20231231"

comparison_results = compare_stocks_performance(bank_symbols, start_date, end_date)
```

### Backtest Simple Strategy
```python
import akshare as ak
import pandas as pd

def backtest_moving_average_strategy(symbol, start_date, end_date, short_window=5, long_window=20):
    """Backtest a simple moving average crossover strategy"""

    # Get historical data
    df = ak.stock_zh_a_hist_tx(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        adjust="hfq"
    )

    df = df.sort_values('date')
    df.reset_index(drop=True, inplace=True)

    # Calculate moving averages
    df['ma_short'] = df['close'].rolling(window=short_window).mean()
    df['ma_long'] = df['close'].rolling(window=long_window).mean()

    # Generate signals
    df['signal'] = 0
    df.loc[df['ma_short'] > df['ma_long'], 'signal'] = 1  # Buy signal

    # Find crossovers
    df['position'] = df['signal'].diff()

    # Backtest performance
    initial_capital = 100000
    capital = initial_capital
    position = 0
    trades = []

    for i in range(1, len(df)):
        if df['position'].iloc[i] == 1:  # Buy signal
            if position == 0:
                position = capital // df['close'].iloc[i]
                capital = capital % df['close'].iloc[i]
                trades.append({
                    'date': df['date'].iloc[i],
                    'action': 'BUY',
                    'price': df['close'].iloc[i],
                    'shares': position,
                    'capital': capital
                })

        elif df['position'].iloc[i] == -1:  # Sell signal
            if position > 0:
                capital = position * df['close'].iloc[i] + capital
                trades.append({
                    'date': df['date'].iloc[i],
                    'action': 'SELL',
                    'price': df['close'].iloc[i],
                    'shares': position,
                    'capital': capital
                })
                position = 0

    # Calculate final portfolio value
    final_value = capital + position * df['close'].iloc[-1]
    total_return = (final_value / initial_capital - 1) * 100

    # Buy and hold return for comparison
    buy_hold_return = (df['close'].iloc[-1] / df['close'].iloc[0] - 1) * 100

    print(f"📈 {symbol} Moving Average Strategy Backtest:")
    print(f"Period: {start_date} to {end_date}")
    print(f"Strategy: MA{short_window} vs MA{long_window}")
    print(f"Initial Capital: ¥{initial_capital:,.0f}")
    print(f"Final Value: ¥{final_value:,.0f}")
    print(f"Strategy Return: {total_return:+.2f}%")
    print(f"Buy & Hold Return: {buy_hold_return:+.2f}%")
    print(f"Outperformance: {total_return - buy_hold_return:+.2f}%")
    print(f"Total Trades: {len([t for t in trades if t['action'] == 'BUY'])}")

    # Show last few trades
    print(f"\nLast 5 Trades:")
    for trade in trades[-5:]:
        print(f"{trade['date']}: {trade['action']} {trade['shares']} shares at ¥{trade['price']:.2f}")

    return df, trades, final_value

# Backtest strategy
symbol = "sz000001"
start_date = "20230101"
end_date = "20231231"

backtest_df, trades, final_value = backtest_moving_average_strategy(symbol, start_date, end_date)
```

## Output Data Structure

The historical data DataFrame contains these columns:
- `date`: Trading date
- `open`: Opening price
- `close`: Closing price
- `high`: Highest price of the day
- `low`: Lowest price of the day
- `amount`: Trading volume (in hands, 1 hand = 100 shares)

## Best Practices

### Data Quality
1. **Use appropriate adjustment**:
   - Forward adjustment (`qfq`) for charting and visualization
   - Backward adjustment (`hfq`) for quantitative analysis and backtesting
   - No adjustment for dividend/split analysis

2. **Handle missing data**: Check for gaps in data, especially for older stocks

3. **Date validation**: Ensure start_date < end_date and use valid trading days

### Performance Analysis
1. **Benchmark comparison**: Always compare against buy-and-hold strategy
2. **Risk metrics**: Calculate volatility, drawdown, and Sharpe ratio
3. **Transaction costs**: Consider realistic trading fees in backtesting

### Rate Limiting
- Tencent Securities has reasonable rate limits
- Cache historical data when possible
- Avoid excessive requests for the same data

## Integration with Other Skills

1. **Use with [market_overview.md](market_overview.md)**: Find interesting stocks, then analyze their historical performance
2. **Use with [individual_stock.md](individual_stock.md)**: Combine fundamental analysis with historical price analysis
3. **Technical indicators**: Combine with libraries like TA-Lib for advanced technical analysis

This skill provides the foundation for comprehensive technical analysis and quantitative research using Chinese stock market data.