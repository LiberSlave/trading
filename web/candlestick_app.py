import pandas as pd
import numpy as np
from datetime import datetime

from bokeh.plotting import figure, curdoc, show
from bokeh.models import ColumnDataSource, HoverTool, CustomJS, Range1d, Div
from bokeh.layouts import column

# --- 데이터 로드 및 전처리 ---
from load import *
data_load = DBload()
df = data_load.minute_candlestick('유일로보틱스')
data_load.close()



# --- 추가 컬럼 계산 ---
df["pct_oc"] = (df["Close"] - df["Open"]) / df["Open"] * 100
df["pct_oh"] = (df["High"] - df["Open"]) / df["Open"] * 100
df["pct_ol"] = (df["Low"] - df["Open"]) / df["Open"] * 100

# 캔들 색상: 상승이면 red, 하락이면 blue
df["color"] = np.where(df["Close"] >= df["Open"], "red", "blue")




# df.reset_index(inplace=True)
# # --- 순번(Trading Minute) 생성 ---
# # 인덱스가 0,1,2,... 순서이므로 이를 문자열로 변환하여 카테고리형 x축으로 사용합니다.
# df["trading_minute"] = df.index.astype(str)
# # --- x축 label 매핑 생성 ---
# # trading_minute 값과 실제 datetime을 HH:MM 형식으로 매핑합니다.
# time_map = {str(i): dt.strftime("%H:%M") for i, dt in enumerate(df["datetime"])}




# --- ColumnDataSource 준비 ---
source = ColumnDataSource(df)

# --- Figure 생성 ---
p = figure(x_axis_type="datetime", 
           title="candle.",
           plot_width=1600, outer_height=400,
           tools="pan,reset")  # pan은 드래그도 가능

# --- 캔들 그리기 ---
# 1. Wick: High ~ Low 선
p.segment(x0="datetime", x1="datetime", y0="Low", y1="High",
          color="color", source=source)

# 2. Body: Open ~ Close (폭은 30초, 즉 30000ms)
# 리턴값(vbar_renderer)을 저장해서 hover tool의 대상(renderer)로 지정합니다.
candle_width = 30000
vbar_renderer = p.vbar(x="datetime", width=candle_width, top="Close", bottom="Open",
       fill_color="color", line_color="black", source=source)

# 3. 거래량 차트 (하단 패널), x_range를 공유하여 동기화 가능
p_vol = figure(x_range=p.x_range, title="Volume", plot_width=1600, plot_height=150)
p_vol.vbar(x="datetime", top="TradingValue", width=30000, source=source, color="black")
p_vol.xaxis.axis_label = "Time"
p_vol.yaxis.axis_label = "Volume"




# --- HoverTool 추가 ---
hover = HoverTool(
    renderers=[vbar_renderer],
    tooltips=[
        ("Time", "@datetime{%F %H:%M}"),
        ("Open", "@Open"),
        ("High", "@High"),
        ("Low", "@Low"),
        ("Close", "@Close"),
        ("Volume", "@Volume"),
        ("Trading Value", "@TradingValue"),
        ("O->C (%)", "@pct_oc{0.2f}%"),
        ("O->H (%)", "@pct_oh{0.2f}%"),
        ("O->L (%)", "@pct_ol{0.2f}%")
    ],
    formatters={"@datetime": "datetime"},
    mode="vline"
)
p.add_tools(hover)

# --- Div: 마우스 이동 시 전일 종가 대비 등락률 표시 ---
prev_close = 65000  # 전일 종가 (예: 65000)
change_div = Div(text=f"Change from Prev Close ({prev_close}): 0.00%",
                 style={"font-size": "12px", "padding": "5px"})

# --- MouseMove 이벤트: 마우스가 차트 위에서 움직일 때 y 좌표에 따른 등락률 표시 ---
mouse_move_callback = CustomJS(args=dict(div=change_div, prev_close=prev_close), code="""
    // event.x, event.y는 데이터 좌표
    if (event.y == null) { return; }
    var change = ((event.y - prev_close) / prev_close) * 100;
    div.text = "Change from Prev Close (" + prev_close + "): " + change.toFixed(2) + "%";
""")
p.js_on_event("mousemove", mouse_move_callback)

# --- Wheel 이벤트: 확대/축소 및 Shift+Wheel 패닝 ---
# 기본적으로 마우스휠 동작은 아래 CustomJS에서 재정의됩니다.
wheel_callback = CustomJS(args=dict(source=source, x_range=p.x_range, y_range=p.y_range), code="""
    // cb_obj는 MouseWheelEvent 객체
    var event = cb_obj;
    // data 배열
    var data = source.data;
    var x = data["datetime"];
    var lows = data["Low"];
    var highs = data["High"];
    
    var start = x_range.start;
    var end = x_range.end;
    var width = end - start;
    
    // 만약 Shift키가 눌렸다면 좌우 패닝(panning)
    if (event.shiftKey) {
        var delta = width * 0.2;
        if (event.delta > 0) {
            // 마우스휠 위로: 왼쪽(이전 시간대)으로 이동
            x_range.start -= delta;
            x_range.end   -= delta;
        } else {
            // 마우스휠 아래로: 오른쪽(다음 시간대)으로 이동
            x_range.start += delta;
            x_range.end   += delta;
        }
    } else {
        // Shift키 미사용 시: 확대/축소 (zoom)
        var zoom = event.delta > 0 ? 1.1 : 0.9;
        var center = (start + end) / 2;
        var new_width = width * zoom;
        x_range.start = center - new_width / 2;
        x_range.end   = center + new_width / 2;
        
        // 현재 x_range에 포함되는 데이터의 최소 low, 최대 high 구하기
        var visible_lows = [];
        var visible_highs = [];
        for (var i = 0; i < x.length; i++) {
            if (x[i] >= x_range.start && x[i] <= x_range.end) {
                visible_lows.push(lows[i]);
                visible_highs.push(highs[i]);
            }
        }
        if (visible_lows.length > 0) {
            var min_low = Math.min.apply(Math, visible_lows);
            var max_high = Math.max.apply(Math, visible_highs);
            var margin = (max_high - min_low) * 0.05;
            y_range.start = min_low - margin;
            y_range.end   = max_high + margin;
        }
    }
""")
p.js_on_event("wheel", wheel_callback)

# --- Layout 구성 및 문서 등록 ---
layout = column(change_div, p)

# 두 차트를 수직으로 배치
layout = column(p, p_vol)

curdoc().add_root(layout)
curdoc().title = "Dynamic Candlestick Chart"



show(layout)

