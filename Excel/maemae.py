import xlwings as xw
import sys
from PyQt5.QtWidgets import QApplication
import pyqt5  # pyqt5 모듈에서 MyApp 클래스를 가져옴



def asdf():
    # 원하는 연산을 수행하고 결과를 리턴합니다.
    result = "Hello, world!"  # 예시 결과 값
    return result

def main():
    # RunPython으로 호출되었을 때, caller()를 통해 Excel에서 호출한 Workbook을 가져옵니다.
    wb = xw.Book.caller()  
    sht = wb.sheets['Sheet1']  # 시트명이 실제 Sheet1과 일치해야 합니다.
    sht.range("A5").value = asdf()

def receive_address(targetCell_Value):
    wb = xw.Book.caller()  
    sht = wb.sheets['Sheet1']  # 시트명이 실제 Sheet1과 일치해야 합니다.
    sht.range("H5").value = targetCell_Value
    print(f"VBA에서 넘어온 셀 주소: {targetCell_Value}")

#  a = pyqt5.add()  # 클래스 실험용코드드


if __name__ == '__main__':
    # 여기서는 pyqt5.py의 main() 함수 대신, 자신의 QApplication을 생성하여 사용합니다.
    app = QApplication(sys.argv)
    ex = pyqt5.MyApp()  # pyqt5 모듈에 정의된 MyApp 클래스로 창 생성
    sys.exit(app.exec_())
