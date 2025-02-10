import pymysql
import pandas as pd

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

# 클래스 사용 예시
if __name__ == '__main__':
    loader = StockDataLoader()
    df = loader.select_from('현대힘스', '20250210')
    print(df)
    loader.close()
