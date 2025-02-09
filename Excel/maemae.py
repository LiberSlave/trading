import xlwings as xw
import sys
from PyQt5.QtWidgets import QApplication
import pyqt5  # pyqt5 모듈에서 MyApp 클래스를 가져옴



def receive_address(targetCell_Value):
    wb = xw.Book.caller()  
    sht = wb.sheets['Sheet1']  # 시트명이 실제 Sheet1과 일치해야 합니다.
    pyqt5.main(targetCell_Value)
    sht.range("H5").value = targetCell_Value



#  a = pyqt5.add()  # 클래스 실험용코드드


if __name__ == '__main__':
    pyqt5.main()
    
