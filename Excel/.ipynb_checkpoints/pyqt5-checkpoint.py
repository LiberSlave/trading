# pyqt5.py
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout
from PyQt5.QtWidgets import QDial, QPushButton,QLCDNumber, QSlider
from PyQt5.QtCore import Qt

class MyApp(QWidget):
    def __init__(self, targetcell_value=None):
        super().__init__()
        self.targetcell_value = targetcell_value
        self.initUI()

    def initUI(self):
        self.setWindowTitle('My First Application')
        self.move(2000, 160)
        self.resize(400, 200)

        layout = QVBoxLayout()
        label = QLabel(f"Target Cell Value: {self.targetcell_value}",self)
        layout.addWidget(label)
        

        hbox = QHBoxLayout()
        hbox.addStretch(1)
        hbox.addLayout(layout)
        hbox.addStretch(1)

        self.setLayout(hbox) #ex객체(MyApp의 instance) layout을 hbox로 설정함. layout에 위젯을 전부추가후 완성된 layout을 layout으로 설정.

        self.show()


        
class test(QWidget):  
    def initUI(self):
        self.setWindowTitle('My First Application')
        self.move(2000, 160)
        self.resize(400, 200)

        layout = QVBoxLayout()
        label = QLabel(f"Target Cell Value: {self.targetcell_value}",self)
        layout.addWidget(label)
        

        hbox = QHBoxLayout()
        hbox.addStretch(1)
        hbox.addLayout(layout)
        hbox.addStretch(1)

        self.setLayout(hbox) #ex객체(MyApp의 instance) layout을 hbox로 설정함. layout에 위젯을 전부추가후 완성된 layout을 layout으로 설정.

        self.show()
        
        
    def receive_address(targetCell_Value):
        wb = xw.Book.caller()  
        sht = wb.sheets['Sheet1']  # 시트명이 실제 Sheet1과 일치해야 합니다.
        pyqt5.main(targetCell_Value)
        sht.range("H5").value = targetCell_Value
        



def main(targetcell_value=None):
    import sys
    app = QApplication(sys.argv)
    ex = MyApp(targetcell_value)
    sys.exit(app.exec_())



if __name__ == '__main__':
    main()

