import pandas as pd
import mplfinance as mpf
import time
from TickerDict import tickers  
import pymysql
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
    

import pymysql
import pandas as pd

class DBsave:
    def __init__(self, host='127.0.0.1', user='root', password='219423', db='trading', charset='utf8mb4'):
        """
        데이터베이스에 연결하고 커서를 초기화합니다.
        """
        self.conn = pymysql.connect(
            host=host,
            user=user,
            password=password,
            db=db,
            charset=charset
        )
        self.cur = self.conn.cursor()
    
    def create_table(self, stock_name, date):
        """
        주어진 stock_name과 date를 조합하여 테이블을 생성합니다.
        예: date가 '20250210'이고 stock_name이 '현대힘스'이면 테이블 이름은 '20250210현대힘스'
        """
        table_query = f"""
        CREATE TABLE IF NOT EXISTS {date}{stock_name} (
            datetime DATE,
            Open INT,
            High INT,
            Low INT,
            Close INT,
            Changes INT,
            ChangeRate FLOAT,
            Volume INT,
            TradingValue FLOAT,
            Program INT,
            ForeignNetBuy INT,
            InstitutionNetBuy INT,
            IndividualNetBuy INT,
            PRIMARY KEY (datetime)
        );
        """
        self.cur.execute(table_query)
        # 테이블 생성 쿼리 반환(디버깅용)
        return table_query

    def insert_table(self, stock_name, date, df):
        """
        주어진 DataFrame(df)의 데이터를 지정한 테이블에 삽입합니다.
        테이블 이름은 date와 stock_name을 조합한 것으로 가정합니다.
        DataFrame의 인덱스는 datetime 값이며, 각 컬럼은 테이블 컬럼과 일치해야 합니다.
        """
        insert_query = f"""
        INSERT IGNORE INTO {date}{stock_name} (
            datetime, Open, High, Low, Close, Changes, ChangeRate, Volume, TradingValue, Program,
            ForeignNetBuy, InstitutionNetBuy, IndividualNetBuy
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """
        # DataFrame의 각 행을 순회하며 데이터를 삽입합니다.
        for index, row in df.iterrows():
            self.cur.execute(insert_query, (
                index,  # DataFrame의 인덱스가 datetime 값
                row["Open"],
                row["High"],
                row["Low"],
                row["Close"],
                row["Changes"],
                row["ChangeRate"],
                row["Volume"],
                row["TradingValue"],
                row["Program"],
                row["ForeignNetBuy"],
                row["InstitutionNetBuy"],
                row["IndividualNetBuy"]
            ))
        # 모든 삽입 작업 후 commit
        self.conn.commit()
    
    def commit(self):
        """
        변경사항을 커밋합니다.
        """
        self.conn.commit()
    
    def close(self):
        """
        데이터베이스 연결과 커서를 종료합니다.
        """
        self.cur.close()
        self.conn.close()
        
        
class StockDataLoader:
    def __init__(self, host='127.0.0.1', user='root', password='219423', db='trading', charset='utf8mb4'):
        """
        데이터베이스 연결을 초기화합니다.
        """
        self.conn = pymysql.connect(
            host=host,
            user=user,
            password=password,
            db=db,
            charset=charset
        )
        self.cur = self.conn.cursor()
    
    def select_from(self, stock_name, date):
        """
        stock_name과 date를 조합한 테이블에서 데이터를 읽어 DataFrame으로 반환합니다.
        예를 들어, stock_name이 '현대힘스'이고 date가 '20250210'이면,
        '20250210현대힘스' 테이블에서 데이터를 읽어옵니다.
        """
        query = f"SELECT * FROM {date}{stock_name}"
        df = pd.read_sql(query, self.conn)
        
        # datetime 컬럼을 인덱스로 설정하고 datetime 형식으로 변환
        df.set_index("datetime", inplace=True)
        df.index = pd.to_datetime(df.index)
        return df
    
    def close(self):
        """
        데이터베이스 연결을 종료합니다.
        """
        self.cur.close()
        self.conn.close()

        
        
        

        
class StockChartVisualizer:
    """
    주식 차트를 시각화하는 클래스입니다.
    데이터프레임에 10일 및 20일 이동평균을 추가하고,
    캔들스틱 차트와 거래량(또는 TradingValue)를 함께 플롯합니다.
    """
    
    def add_moving_averages(self, df):
        """
        DataFrame에 10일 및 20일 이동평균을 추가합니다.
        
        인수:
            df (pandas.DataFrame): 'Close' 컬럼을 포함한 DataFrame
        
        반환:
            pandas.DataFrame: 이동평균 컬럼이 추가된 DataFrame
        """
        df["10DMA"] = df["Close"].rolling(window=10).mean()
        df["20DMA"] = df["Close"].rolling(window=20).mean()
        return df

    def plot_candlestick(self, df):
        """
        이동평균선이 포함된 캔들스틱 차트를 플롯하고,
        matplotlib의 Figure와 Axes 객체를 반환합니다.
        
        인수:
            df (pandas.DataFrame): 시계열 데이터를 포함하는 DataFrame. 
                                   'Close', 'TradingValue' 등의 컬럼이 필요합니다.
        
        반환:
            tuple: (fig, axes) - matplotlib Figure와 Axes 객체
        """
        # 사용자 정의 마켓 컬러와 스타일 설정
        custom_colors = mpf.make_marketcolors(up="red", down="blue", wick="black", edge="black")
        custom_style = mpf.make_mpf_style(marketcolors=custom_colors, gridcolor="gray", gridstyle="--")

        # DataFrame에 이동평균 컬럼이 있는지 확인하고, addplot 목록 구성
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

        # mplfinance를 이용해 차트를 플롯하고 Figure와 Axes 반환
        fig, axes = mpf.plot(
            df,
            type="candle",
            style=custom_style,
            title="Stock Chart",
            ylabel="Price",
            ylabel_lower="Trading Value",
            volume=False,
            addplot=add_plots,
            returnfig=True
        )
        return fig, axes