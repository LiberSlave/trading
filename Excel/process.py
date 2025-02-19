import pandas as pd
import mplfinance as mpf
import matplotlib.pyplot as plt
import time
import pymysql
# Assuming TickerDict.py contains the tickers dictionary
import matplotlib.dates as mdates
import xlwings as xw
import json
from pykiwoom.kiwoom import *

###################################키움API 로그인#########################################

# Persistent Interpreter 환경에서는 모듈이 로드될 때 한 번만 로그인하도록 합니다.
def login_kiwoom():
    global kiwoom
    if 'kiwoom' not in globals():
        kiwoom = Kiwoom()
        kiwoom.CommConnect(block=True)
        print("Persistent 로그인 완료")

# 테스트용 엑셀 메세지 박스.

def test_messagebox():
    import ctypes
    global asdas
    if 'asdas' not in globals():
        asdas = ctypes.windll.user32.MessageBoxW(0, "안녕하세요, eeeExcel!", "메시지 박스", 0)

#########################################################################################

class GetData:
    
    with open("C:/workspace/systemtrading/excel/ticker.json", "r", encoding="utf-8") as f:
            tickers = json.load(f)
            
    def __init__(self, kiwoom_lab = None, tickers=tickers):
        """
        kiwoom API 객체초기화. json에서 딕셔너리를 읽어와 tickers변수에 저장. 
        """
        if kiwoom_lab is None:
            kiwoom_lab = kiwoom

        self.kiwoom = kiwoom_lab
        self.tickers = tickers

    def daily_candlestick(self, stock_name, date='20250211', max_requests=2):
        """
        주어진 주식(stock_name)과 날짜(date)에 대해, kiwoom API를 통해
        주식 데이터를 여러 번 요청하여 하나의 DataFrame으로 결합하여 반환합니다.
        """
        code = self.tickers.get(stock_name)
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
    
    def minute_candlestick(self, stock_name, tick=1, max_requests=1):
        """
        주어진 주식 이름(stock_name)과 틱 범위(tick)에 대해 데이터를 수집합니다.
        API를 통해 max_requests 만큼 데이터를 요청한 후, DataFrame으로 결합하여 반환합니다.
        """
        # self.tickers에서 stock_name에 해당하는 코드를 가져옴
        code = self.tickers.get(stock_name, None)
        if not code:
            raise ValueError(f"Stock name '{stock_name}' not found in tickers.")

        dfs = []
        for request_num in range(max_requests):
            next_flag = 1 if request_num == 0 else 2
            df = self.kiwoom.block_request(
                "opt10080",
                종목코드=code,
                틱범위=tick,
                표시구분=1,
                output="으아아아",
                next=next_flag
            )
            dfs.append(df)
            time.sleep(1)
        # 여러 요청으로 받은 DataFrame들을 하나로 결합
        df = pd.concat(dfs, ignore_index=True)
        return df


class Preprocess:
    def __init__(self):
        pass  # 초기화할 내용이 별도로 없으면 pass

    def daily_candlestick(self, stock_name, df):
        """
        주식 데이터 DataFrame을 정리하고 전처리합니다.
          - 불필요한 컬럼 제거, 값 치환, 데이터 타입 변환, 컬럼 이름 변경,
          - 행 순서 뒤집기, 인덱스 설정, 절대값 변환 등 수행.
        """
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
        # 두 번째 열(인덱스 1)에 'name' 열을 추가하고, 모든 행의 값을 stock_name으로 설정
        df.insert(1, 'name', stock_name)

        # Transform data: 역순 정렬 후 인덱스 설정
        df = df.iloc[::-1].reset_index(drop=True)
        df.set_index("datetime", inplace=True)
        df.index = pd.to_datetime(df.index)

        # Apply absolute value transformation to specific columns
        columns_to_transform = ["Open", "High", "Low", "Close"]
        df[columns_to_transform] = df[columns_to_transform].abs()

        return df
    
    def minute_candlestick(self, stock_name, df):
        """Clean and preprocess the stock data for minute data."""
        # 불필요한 열 제거
        columns_to_drop = ["수정주가구분", "수정비율", "대업종구분", "소업종구분", "종목정보", "수정주가이벤트", "전일종가"]
        df = df.drop(columns=columns_to_drop, errors='ignore')

        # 상위 420행만 남김 (즉, 420행 이후는 삭제)
        df = df.iloc[:420]

        # 데이터 타입 변환: "체결시간" 열을 datetime으로 변환
        df["체결시간"] = pd.to_datetime(df["체결시간"], format="%Y%m%d%H%M%S")

        # "체결시간"을 제외한 나머지 열은 정수형으로 변환
        columns_to_convert = df.columns.difference(["체결시간"])
        df[columns_to_convert] = df[columns_to_convert].astype(int, errors='ignore')

        # 열 순서 재배열
        df = df[["체결시간", "시가", "고가", "저가", "현재가", "거래량"]]

        # 열 이름 변경
        df = df.rename(columns={
            "체결시간": "datetime",
            "시가": "Open",
            "고가": "High",
            "저가": "Low",
            "현재가": "Close",
            "거래량": "Volume"
        })

        # 거래대금(TradingValue) 열 추가: Volume * ((Open+High+Low+Close)/4) / 100000000을 소수점 3번째 자리에서 반올림
        df['TradingValue'] = ((df['Volume'] * ((df['Open'] + df['High'] + df['Low'] + df['Close']) / 4)) / 100000000.0).round(3)

        # 두 번째 열(인덱스 1)에 'name' 열을 추가하고, 모든 행의 값을 stock_name으로 설정
        df.insert(1, 'name', stock_name)

        # datetime 열을 인덱스로 설정
        df.set_index("datetime", inplace=True)

        # Open, High, Low, Close 열에 대해 절대값 변환
        columns_to_transform = ["Open", "High", "Low", "Close"]
        df[columns_to_transform] = df[columns_to_transform].abs()

        # 필요한 경우 추가 데이터 변환 작업 수행 (예: 행 순서 뒤집기)
        # df = df.iloc[::-1].reset_index(drop=True)

        return df


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
    
    # def daily_candlestick_create_table(self, stock_name):
    #     """
    #     주어진 stock_name과 date를 조합하여 테이블을 생성합니다.
    #     예: date가 '20250210'이고 stock_name이 '현대힘스'이면 테이블 이름은 '20250210현대힘스'
    #     """
    #     table_query = f"""
    #     CREATE TABLE IF NOT EXISTS day_{stock_name} (
    #         datetime DATE,
    #         Open INT,
    #         High INT,
    #         Low INT,
    #         Close INT,
    #         Changes INT,
    #         ChangeRate FLOAT,
    #         Volume INT,
    #         TradingValue FLOAT,
    #         Program INT,
    #         ForeignNetBuy INT,
    #         InstitutionNetBuy INT,
    #         IndividualNetBuy INT,
    #         PRIMARY KEY (datetime)
    #     );
    #     """
    #     self.cur.execute(table_query)
    #     # 테이블 생성 쿼리 반환(디버깅용)
    #     return table_query

    def daily_candlestick(self, df):
        """
        주어진 DataFrame(df)의 데이터를 지정한 테이블에 삽입합니다.
        테이블 이름은 date와 stock_name을 조합한 것으로 가정합니다.
        DataFrame의 인덱스는 datetime 값이며, 각 컬럼은 테이블 컬럼과 일치해야 합니다.
        """
        insert_query = f"""
        INSERT IGNORE INTO daily_candlestick (
            datetime, name, Open, High, Low, Close, Changes, ChangeRate, Volume, TradingValue, Program,
            ForeignNetBuy, InstitutionNetBuy, IndividualNetBuy
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """
        # DataFrame의 각 행을 순회하며 데이터를 삽입합니다.
        for index, row in df.iterrows():
            self.cur.execute(insert_query, (
                index,  # DataFrame의 인덱스가 datetime 값
                row["name"],  
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

    def minute_candlestick(self, df):
    
        insert_query = f"""
        INSERT IGNORE INTO minute_candlestick (
            datetime, name, Open, High, Low, Close, Volume, TradingValue
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """
    # DataFrame의 각 행을 순회하며 데이터를 삽입합니다.
        for index, row in df.iterrows():
            self.cur.execute(insert_query, (
                index,  # DataFrame의 인덱스가 datetime 값
                row['name'],
                row["Open"],
                row["High"],
                row["Low"],
                row["Close"],
                row["Volume"],
                row["TradingValue"]
            ))
        # 모든 삽입 작업 후 commit
        self.conn.commit()

    ##################################################

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
        
    ###################################################
        
class DBload:
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
    
    def daily_candlestick(self, stock_name):
        """
        stock_name과 date를 조합한 테이블에서 데이터를 읽어 DataFrame으로 반환합니다.
        예를 들어, stock_name이 '현대힘스'이고 date가 '20250210'이면,
        '20250210현대힘스' 테이블에서 데이터를 읽어옵니다.
        """
        query = f"SELECT * FROM daily_candlestick WHERE name = %s"
        df = pd.read_sql(query, self.conn, params=(stock_name,))
        
        # datetime 컬럼을 인덱스로 설정하고 datetime 형식으로 변환
        df.set_index("datetime", inplace=True)
        df.index = pd.to_datetime(df.index)
        return df
    
    def minute_candlestick(self, stock_name):
        """
        stock_name과 date를 조합한 테이블에서 데이터를 읽어 DataFrame으로 반환합니다.
        예를 들어, stock_name이 '현대힘스'이고 date가 '20250210'이면,
        '20250210현대힘스' 테이블에서 데이터를 읽어옵니다.
        """
        query = f"SELECT * FROM minute_candlestick WHERE name = %s"
        df = pd.read_sql(query, self.conn, params=(stock_name,))
        
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

        
        
        

        
class Visualize:
    """
    주식 차트를 시각화하는 클래스입니다.
    데이터프레임에 10일 및 20일 이동평균을 추가하고,
    캔들스틱 차트와 거래량(또는 TradingValue)를 함께 플롯합니다.
    """
    def __init__(self):
        pass  # 필요한 초기화 작업이 있으면 여기에 작성
    
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

    def daily_candlestick(self, stock_name, df):
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
        custom_style = mpf.make_mpf_style(marketcolors=custom_colors, gridcolor="gray", gridstyle="--",rc={'font.family': 'Malgun Gothic'})

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
        fig, axlist = mpf.plot(
            df,
            type="candle",
            style=custom_style,
            ylabel="Price",
            ylabel_lower="Trading Value",
            volume=False,
            addplot=add_plots,
            returnfig=True
        )
        fig.suptitle(f"{stock_name}", fontsize=16)
        
        return fig, axlist   

    def minute_candlestick(self, stock_name, df):
        """Plot the candlestick chart with moving averages."""
        custom_colors = mpf.make_marketcolors(up="red", down="blue", wick="black", edge="black")
        custom_style = mpf.make_mpf_style(marketcolors=custom_colors, gridcolor="gray", gridstyle="--", rc={'font.family': 'Malgun Gothic'})

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

        # Create a Matplotlib Figure and Axes objects using mplfinance
        fig, axlist = mpf.plot(
            df,
            type="candle",
            style=custom_style,
            title="Interactive Candlestick Chart",
            ylabel="Price",
            ylabel_lower="Trading Value",
            volume=False,
            addplot=add_plots,
            returnfig=True,  # Return the figure and axes objects
            figratio=(25, 9),  # Aspect ratio (width:height)
            figscale=1      # Scale factor for figure size
        )
        fig.suptitle(f"{stock_name}", fontsize=16)

        ax = axlist[0] 
        ax.xaxis.set_major_locator(mdates.HourLocator(byhour=range(24),interval=1440)) 
        # ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y%m%d%H%M%S'))
        # fig.autofmt_xdate()  # 눈금 레이블이 겹치지 않도록 자동 회전

        # Enable interactive mode and display the plot
        # plt.ioff()
        # plt.show()

        return fig, axlist



######################################## 함수 ########################################################

def add1(a,b):
    return a+b

def add2(a,b):
    return add1(a,b)


def create_common_objects(kiwoom_lab=None):
    if kiwoom_lab is None:
        global kiwoom
        kiwoom_lab = kiwoom
    get_data = GetData(kiwoom_lab)
    prepro_data = Preprocess()
    data_save = DBsave()
    return get_data, prepro_data, data_save

def update_tickers(kiwoom_lab = None, json_path = "C:/workspace/systemtrading/excel/ticker.json"):
    if kiwoom_lab is None:
        global kiwoom
        kiwoom_lab = kiwoom
    """
    Kiwoom API를 사용하여 KOSPI와 KOSDAQ의 종목 코드를 ticker.json 파일에 업데이트하고,
    새로 추가된 종목들을 리스트로 반환합니다.
    
    Parameters:
        kiwoom: Kiwoom API 객체
        json_path (str): ticker.json 파일의 경로 (기본값: "ticker.json")
    
    Returns:
        new_stocks (list): 새로 추가된 종목들의 리스트. 예) ["동화약품: 000020", ...] 
                           추가된 종목이 없으면 ["추가된 종목이 없습니다"] 반환.
    """
    # JSON 파일에서 기존 tickers 딕셔너리 로드
    with open(json_path, "r", encoding="utf-8") as f:
        tickers = json.load(f)
    
    # KOSPI (시장코드 "0")와 KOSDAQ (시장코드 "10")의 종목 코드 목록을 가져옴
    kospi_tickers = kiwoom_lab.GetCodeListByMarket("0")  # KOSPI
    kosdaq_tickers = kiwoom_lab.GetCodeListByMarket("10")  # KOSDAQ
    stock_codes = kospi_tickers + kosdaq_tickers

    new_stocks = []  # 새로 추가된 종목들을 저장할 리스트

    # 새로운 종목을 tickers 딕셔너리에 추가
    for code in stock_codes:
        name = kiwoom_lab.GetMasterCodeName(code)
        if name not in tickers:
            tickers[name] = code
            new_stocks.append(f"{name}: {code}")
            # 기존에는 print(f"추가됨: {name}: {code}")로 출력했으나,
            # 앞으로 Excel에서 debug.print로 확인할 수 있도록 반환값으로 전달합니다.

    # 업데이트된 tickers 딕셔너리를 JSON 파일에 다시 저장
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(tickers, f, indent=4, ensure_ascii=False)
    
    if not new_stocks:
        new_stocks = ["추가된 종목이 없습니다"]
    
    return new_stocks

########################################################################################################

def several_candlestick_save(stock_name_list, kiwoom_lab = None, date='20250211'):
    get_data, prepro_data, data_save = create_common_objects(kiwoom_lab)

    for stock_name in stock_name_list:
        df = get_data.daily_candlestick(stock_name, date)
        df = prepro_data.daily_candlestick(stock_name, df)
        data_save.daily_candlestick(df)

        df = get_data.minute_candlestick(stock_name)
        df = prepro_data.minute_candlestick(stock_name, df)
        data_save.minute_candlestick(df)
        print(f"{stock_name} 저장완료")
    
    # 데이터베이스 연결 종료
    data_save.close()
    print('모두저장완료')

        
    
def several_daily_candlestick_save(stock_name_list, kiwoom_lab = None, date='20250211'):

    get_data, prepro_data, data_save = create_common_objects(kiwoom_lab)

    for stock_name in stock_name_list:
        df = get_data.daily_candlestick(stock_name, date)
        df = prepro_data.daily_candlestick(stock_name, df)
        data_save.daily_candlestick(df)
        
        
    data_save.close()   
    

def daily_candlestick_save(stock_name, kiwoom_lab = None, date='20250211'):
    """
    주어진 주식(stock_name)과 날짜(date)에 대해 일봉 데이터를 수집하고,
    전처리한 후, 데이터베이스에 테이블을 생성하고 데이터를 저장하는 전체
    워크플로우를 실행하는 함수입니다.
    
    Parameters:
        stock_name (str): 예) '삼성전자'
        date (str): 예) '20250212'
    """
    # 객체생성.
    get_data, prepro_data, data_save = create_common_objects(kiwoom_lab)

    df = get_data.daily_candlestick(stock_name, date)
    df = prepro_data.daily_candlestick(stock_name, df)
    data_save.daily_candlestick(df)

    data_save.close()

    
######## save와 close 분리 ##########
# def daily_candlestick_save_and_close(kiwoom, stock_name, date='20250211'):
    
#     data_save = daily_candlestick_save(kiwoom, stock_name, date='20250211')
#     data_save.close()
def several_minute_candlestick_save(stock_name_list, kiwoom_lab = None):
    get_data, prepro_data, data_save = create_common_objects(kiwoom_lab)

    for stock_name in stock_name_list:
        df = get_data.minute_candlestick(stock_name)
        df = prepro_data.minute_candlestick(stock_name, df)
        data_save.minute_candlestick(df)
        
    data_save.close()   


def minute_candlestick_save(stock_name, kiwoom_lab = None):
    
    #객체생성성
    get_data, prepro_data, data_save = create_common_objects(kiwoom_lab)

    df = get_data.minute_candlestick(stock_name)
    df = prepro_data.minute_candlestick(stock_name, df)
    data_save.minute_candlestick(df)
    
    # 데이터베이스 연결 종료
    data_save.close()

    return df #(df확인해보고 싶으면 주석 해제.)

################################# load ############################################

def daily_candlestick_load(stock_name):
    # 데이터 로딩: DBload 클래스의 인스턴스를 생성하여 데이터를 로드
    data_load = DBload()
    df = data_load.daily_candlestick(stock_name)
    data_load.close()
    
    # 시각화: Visualize 클래스의 인스턴스를 생성하여 이동평균 추가 및 차트 플롯
    visualization = Visualize()
    df = visualization.add_moving_averages(df)
    fig, axes = visualization.daily_candlestick(stock_name, df)
    plt.show()
    return fig, axes


def minute_candlestick_load(stock_name):
    # 데이터 로딩: DBload 클래스의 인스턴스를 생성하여 데이터를 로드
    data_load = DBload()
    df = data_load.minute_candlestick(stock_name)
    data_load.close()
    
    # 시각화: Visualize 클래스의 인스턴스를 생성하여 이동평균 추가 및 차트 플롯
    data_visualization = Visualize()
    fig, axes = data_visualization.minute_candlestick(stock_name, df)
    plt.show()
    return fig, axes


def combined_candlestick(stock_name):

    data_load = DBload()
    daily_df = data_load.daily_candlestick(stock_name)
    minute_df = data_load.minute_candlestick(stock_name)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))

    # 첫 번째 서브플롯에 daily_df의 차트 그리기, title 없이 그리기
    mpf.plot(daily_df,
            type="candle",
            ax=ax1,
            style="charles",
            returnfig=False)

    # 두 번째 서브플롯에 minute_df의 차트 그리기, title 없이 그리기
    mpf.plot(minute_df,
            type="candle",
            ax=ax2,
            style="charles",
            returnfig=False)

    

    fig.suptitle("Combined Candlestick Charts", fontsize=16)
    fig.autofmt_xdate()
        

    #plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.subplots_adjust(top=0.90, bottom=0.10, left=0.05, right=0.95)
    plt.show()




def combined_candlestick2(stock_name):
    import matplotlib.gridspec as gridspec
    # 데이터 로딩 (DBload 클래스 이용)
    data_load = DBload()
    daily_df = data_load.daily_candlestick(stock_name)
    minute_df = data_load.minute_candlestick(stock_name)
    data_load.close()
    
    # 하나의 Figure에 4개의 Axes를 생성 (4행 1열)
    fig = plt.figure(figsize=(14, 10))
    # 높이 비율: 메인 차트는 3, lower panel은 1의 비율로 설정 (총 4행)
    gs = gridspec.GridSpec(4, 1, height_ratios=[3, 1, 3, 1], hspace=0.05)
    
    # 일봉 차트: 메인 패널과 하단 패널 생성
    ax_daily = fig.add_subplot(gs[0])
    ax_daily_lower = fig.add_subplot(gs[1], sharex=ax_daily)
    
    # 분봉 차트: 메인 패널과 하단 패널 생성
    ax_minute = fig.add_subplot(gs[2])
    ax_minute_lower = fig.add_subplot(gs[3], sharex=ax_minute)
    
    # 일봉 차트 메인 패널에 캔들스틱 차트 그리기 (볼륨은 제외)
    mpf.plot(daily_df,
             type="candle",
             ax=ax_daily,
             style="charles",
             returnfig=False)
    
    # 일봉 lower panel: 거래량(또는 TradingValue) 데이터를 막대그래프로 그리기
    if "Volume" in daily_df.columns:
        ax_daily_lower.bar(daily_df.index, daily_df["Volume"], color="gray")
        ax_daily_lower.set_ylabel("Volume")
    elif "TradingValue" in daily_df.columns:
        ax_daily_lower.bar(daily_df.index, daily_df["TradingValue"], color="gray")
        ax_daily_lower.set_ylabel("Trading Value")
    else:
        ax_daily_lower.set_ylabel("Lower Panel")
    
    # 분봉 차트 메인 패널에 캔들스틱 차트 그리기 (추가 옵션 사용 예시)
    # 사용자 정의 스타일 적용
    custom_colors = mpf.make_marketcolors(up="red", down="blue", wick="black", edge="black")
    custom_style = mpf.make_mpf_style(marketcolors=custom_colors, gridcolor="gray", gridstyle="--")
    mpf.plot(minute_df,
             type="candle",
             ax=ax_minute,
             style=custom_style,
             returnfig=False)
    
    # 분봉 lower panel: 거래량(또는 TradingValue) 데이터를 막대그래프로 그리기
    if "Volume" in minute_df.columns:
        ax_minute_lower.bar(minute_df.index, minute_df["Volume"], color="gray")
        ax_minute_lower.set_ylabel("Volume")
    elif "TradingValue" in minute_df.columns:
        ax_minute_lower.bar(minute_df.index, minute_df["TradingValue"], color="gray")
        ax_minute_lower.set_ylabel("Trading Value")
    else:
        ax_minute_lower.set_ylabel("Lower Panel")
    
    # 전체 Figure 제목 및 x축 레이블 자동 회전
    fig.suptitle("Combined Candlestick Charts", fontsize=16)
    fig.autofmt_xdate()
    
    plt.show()





# # 사용 예제
if __name__ == '__main__':
    # fig1, ax1 = daily_candlestick_load('네오셈')
    # fig2, ax2 = minute_candlestick_load('네오셈')
    # plt.show()

    # fig,axes = combined_candlestick('네오셈')

    fig, axes = combined_candlestick('네오셈')
    plt.show()
#     # 플롯 창을 띄워서 확인 (예: plt.show() 사용)



#     fig, axes = minute_candlestick_load('대동기어')
#     plt.show()

