import pandas as pd
import plotly.graph_objects as go


# --- 데이터 로드 및 전처리 ---
from load import *
data_load = DBload()
df = data_load.minute_candlestick('유일로보틱스')
data_load.close()

# Previous day's closing price (as specified)
prev_close = 65000

# Function to calculate percentage change
def calculate_change_rate(current, base):
    return (current - base) / base * 100

# Add custom hover text with all requested details
df['hover_text'] = df.apply(lambda row: 
    f"Open: {row['Open']}<br>"
    f"High: {row['High']}<br>"
    f"Low: {row['Low']}<br>"
    f"Close: {row['Close']}<br>"
    f"Volume: {row['Volume']}<br>"
    f"Trading Value: {row['TradingValue']:.3f}<br>"
    f"Change from Prev Close: {calculate_change_rate(row['Close'], prev_close):.2f}%<br>"
    f"Open to Close Change: {calculate_change_rate(row['Close'], row['Open']):.2f}%<br>"
    f"Open to High Change: {calculate_change_rate(row['High'], row['Open']):.2f}%<br>"
    f"Open to Low Change: {calculate_change_rate(row['Low'], row['Open']):.2f}%",
    axis=1
)

# Create candlestick chart
fig = go.Figure(data=[go.Candlestick(
    x=df.index,
    open=df['Open'],
    high=df['High'],
    low=df['Low'],
    close=df['Close'],
    increasing_line_color='red',  # Red for rising candles
    decreasing_line_color='blue',  # Blue for falling candles
    text=df['hover_text'],  # Custom hover text
    hoverinfo='text'  # Display only the custom text
)])

# Update layout for better interactivity and appearance
fig.update_layout(
    title='Minute Candlestick Chart',
    xaxis_title='Time',
    xaxis_type='category',
    yaxis_title='Price',
    xaxis_rangeslider_visible=False,  # Disable the default range slider
    yaxis_autorange=True,  # Ensure no empty space when zooming
    template='plotly_white'  # Clean white background
)

# Show the chart
fig.show()