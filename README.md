# SPOTRADE (Crypto Trading Bot Documentation)

## Description

This bot is designed to automate spot trading on Binance using the exchange's public API. It operates by analyzing market data through various technical indicators, specifically oscillators like MACD, RSI, and Bollinger Bands. Based on these indicators, the bot makes informed decisions on whether to execute spot buy or sell orders.

### How It Works:
1. **Data Retrieval**: The bot fetches real-time market data from Binance's public API for spot trading.
2. **Technical Analysis**: It calculates key technical indicators, including MACD, RSI, and Bollinger Bands.
3. **Trade Execution**: Based on predefined rules and thresholds, the bot decides whether to place a buy or sell order on the spot market.

## What is MACD?

**MACD (Moving Average Convergence Divergence)** is a trend-following momentum indicator that shows the relationship between two moving averages of an asset's price. 

- **How it works**: The MACD is calculated by subtracting the 26-period EMA (Exponential Moving Average) from the 12-period EMA. The result of this calculation is the MACD line. A nine-day EMA of the MACD, called the "signal line," is then plotted on top of the MACD line, which can act as a trigger for buy and sell signals.

- **Trading Signals**:
  - **Bullish Signal**: When the MACD line crosses above the signal line.
  - **Bearish Signal**: When the MACD line crosses below the signal line.

## What is RSI?

**RSI (Relative Strength Index)** is a momentum oscillator that measures the speed and change of price movements. It ranges from 0 to 100 and is typically used to identify overbought or oversold conditions in a market.

- **How it works**: RSI is calculated using the average gains and losses over a specified period (usually 14 periods). The formula is:
  
  \[
  RSI = 100 - \left(\frac{100}{1 + \frac{\text{Average Gain}}{\text{Average Loss}}}\right)
  \]

- **Trading Signals**:
  - **Overbought**: RSI above 70, indicating the asset may be overvalued.
  - **Oversold**: RSI below 30, indicating the asset may be undervalued.

## What are Bollinger Bands?

**Bollinger Bands** are a type of price envelope developed by John Bollinger. They are plotted at standard deviation levels above and below a simple moving average (SMA) of the asset's price.

- **How it works**: The default setting for Bollinger Bands uses a 20-day SMA with bands plotted 2 standard deviations above and below the SMA. The bands expand and contract based on market volatility.

- **Trading Signals**:
  - **Breakouts**: When the price moves outside the upper or lower band, it may signal a continuation in the direction of the breakout.
  - **Reversions**: Prices typically return to the SMA after touching or crossing a band, indicating a potential reversal.

## Conclusion

This bot leverages the power of these technical indicators to make calculated trading decisions on Binance's spot market. By automating the trading process and following a rules-based approach, the bot aims to improve trading efficiency and capitalize on market opportunities with precision.
