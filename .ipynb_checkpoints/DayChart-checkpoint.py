import pandas as pd
import mplfinance as mpf
import time
from TickerDict import tickers  
# Assuming TickerDict.py contains the tickers dictionary

class StockDataProcessor:
    def __init__(self, kiwoom, s = tickers):
        self.kiwoom = kiwoom
        self.tickers = s  # Store tickers as a default attribute

    def get_stock_data(self, stock_name, date, max_requests=2):
        """Fetch stock data for a given stock name and date."""
        self.stock_name = stock_name
        code = self.tickers.get(stock_name, None)  # Use self.tickers by default
        if not code:
            raise ValueError(f"Stock name '{stock_name}' not found in tickers.")

        dfs = []
        for request_num in range(max_requests):
            next_flag = 1 if request_num == 0 else 2
            df = self.kiwoom.block_request(
                "opt10086",
                종목코드=code,
                기준일자=date,
                표시구분=1,
                output="일별주가요청",
                next=next_flag
            )
            dfs.append(df)
            time.sleep(1)
        return pd.concat(dfs, ignore_index=True)

    def preprocess_data(self, df):
        """Clean and preprocess the stock data."""
        # Drop unnecessary columns
        columns_to_drop = ["신용비", "개인", "기관", "외인수량", "외국계", "외인비", "외인보유", "외인비중", "신용잔고율"]
        df = df.drop(columns=columns_to_drop, errors='ignore')

        # Replace '--' with '-'
        columns_to_replace = ["프로그램", "외인순매수", "기관순매수", "개인순매수"]
        df[columns_to_replace] = df[columns_to_replace].replace("--", "-", regex=True)

        # Convert data types
        df["날짜"] = pd.to_datetime(df["날짜"], format="%Y%m%d")
        df["등락률"] = df["등락률"].astype(float)
        columns_to_convert = df.columns.difference(["날짜", "등락률"])
        df[columns_to_convert] = df[columns_to_convert].astype(int, errors='ignore')
        df["금액(백만)"] = df["금액(백만)"] / 100

        # Rename columns
        df = df.rename(columns={
            "날짜": "datetime",
            "시가": "Open",
            "고가": "High",
            "저가": "Low",
            "종가": "Close",
            "거래량": "Volume",
            "전일비": "Changes",
            "등락률": "ChangeRate",
            "금액(백만)": "TradingValue",
            "프로그램": "Program",
            "외인순매수": "ForeignNetBuy",
            "기관순매수": "InstitutionNetBuy",
            "개인순매수": "IndividualNetBuy"
        })
        

        # Transform data
        df = df.iloc[::-1].reset_index(drop=True)
        
        # Set datetime as the index
        df.set_index("datetime", inplace=True)
        
        # Apply absolute value transformation to specific columns
        columns_to_transform = ["Open", "High", "Low", "Close"]
        df[columns_to_transform] = df[columns_to_transform].abs()

        return df

    def add_moving_averages(self, df):
        """Add 10-day and 20-day moving averages to the DataFrame."""
        df["10DMA"] = df["Close"].rolling(window=10).mean()
        df["20DMA"] = df["Close"].rolling(window=20).mean()
        return df

    def plot_candlestick(self, df):
        """Plot the candlestick chart with moving averages."""
        custom_colors = mpf.make_marketcolors(up="red", down="blue", wick="black", edge="black")
        custom_style = mpf.make_mpf_style(marketcolors=custom_colors, gridcolor="gray", gridstyle="--")

        # Check if the DataFrame contains 10DMA and 20DMA columns
        if "10DMA" in df.columns and "20DMA" in df.columns:
            add_plots = [
                mpf.make_addplot(df["10DMA"], color="navy", width=1.0, linestyle="solid"),
                mpf.make_addplot(df["20DMA"], color="gold", width=2.0, linestyle="solid"),
                mpf.make_addplot(df["TradingValue"], panel=1, color="gray", type="bar")
            ]
        else:
            add_plots = [
                mpf.make_addplot(df["TradingValue"], panel=1, color="gray", type="bar")
            ]

        mpf.plot(
            df,
            type="candle",
            style=custom_style,
            title="name",
            ylabel="Price",
            ylabel_lower="Trading Value",
            volume=False,
            addplot=add_plots
        )
