import xlwings as xw

def asdf():
    # 원하는 연산을 수행하고 결과를 리턴합니다.
    result = "Hello, world!"  # 예시 결과 값
    return result

def main():
    # RunPython으로 호출되었을 때, caller()를 통해 Excel에서 호출한 Workbook을 가져옵니다.
    wb = xw.Book.caller()  
    sht = wb.sheets['Sheet1']  # 시트명이 실제 Sheet1과 일치해야 합니다.
    sht.range("A5").value = asdf()

def receive_address(asa):
    wb = xw.Book.caller()  
    sht = wb.sheets['Sheet1']  # 시트명이 실제 Sheet1과 일치해야 합니다.
    sht.range("A5").value = asa
    print(f"VBA에서 넘어온 셀 주소: {asa}")
