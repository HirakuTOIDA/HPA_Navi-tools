# %%
"""
HPA_Navi Ground Station
@todo 
@memo PySerial + PySide6
"""
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore

import serial
import serial.tools.list_ports

import sys

import SylphideProcessor

# pyqtgraphが使用しているQtバインディングを確認
print(f"{pg.Qt.QT_LIB} is used.")

# Automated serial port search
print("***** Automated serial port(s) search *****")
ser = serial.Serial()
ser.baudrate = 9600
ser.timeout = 0.1

ports = serial.tools.list_ports.comports()
devices = []
for info in ports:
    print(info)
    if info[2].find("VID:PID=04B4:F232") > 0:
        devices.append(info)
    if info[2].find("VID:PID=0483:5740") > 0:
        devices.append(info)

if len(devices) == 0:
    print("-> HPA_Navi not found")
    sys.exit(0)
elif len(devices) == 1:
    print("-> HPA_Navi found")
    ser.port = devices[0][0]
else:
    print("-> Multiple HPA_Navi found")
    for i in range(len(devices)):
        print(str(i) + ": " + devices[i][0])
    print("Input number of target port")
    print(">> ", end="")
    num = int(input())
    ser.port = devices[num][0]

print("***** Start connection *****")
try:
    ser.open()
    print(ser.port + " opened")
except:
    print("Can't open " + ser.port)
    sys.exit(0)

# パーサの準備
print("***** Read pages *****")
pagea = SylphideProcessor.PageA()
pagef = SylphideProcessor.PageF()
pageg = SylphideProcessor.PageG()
pageh = SylphideProcessor.PageH()
pagel = SylphideProcessor.PageL()  # todo
pagem = SylphideProcessor.PageM()
pagen = SylphideProcessor.PageN()
pageo = SylphideProcessor.PageO()  # todo
pagep = SylphideProcessor.PageP()
pager = SylphideProcessor.PageR()
pages = SylphideProcessor.PageS()
paget = SylphideProcessor.PageT()
pageu = SylphideProcessor.PageU()

page_list = ["A", "H", "L", "M", "N", "O", "P", "R", "S", "U"]
page_syl_list = [pagea, pageh, pagel, pagem, pagen, pageo, pagep, pager, pages, pageu]
page = dict(zip(page_list, page_syl_list))
page_payloads_list = [9, 12, 4, 3, 9, 4, 6, 6, 12, 14]
page_payloads = dict(zip(page_list, page_payloads_list))
page_dat = {key: [[] * i for i in range(page_payloads[key] + 1)] for key in page_list}
page_updated = {key: False for key in page_list}

# function_str_list = []

# for p in page_list:
#     function_str = f'''def update_plot_{p}():
#         # global page_updated
#         if page_updated["{p}"]:
#             for i in range(page_payloads["{p}"]):
#                 curve["{p}"][i].setData(page_dat["{p}"][0], page_dat["{p}"][i+1])
#             page_updated["{p}"] = False
#     '''
#     function_str_list.append(function_str)

# update_plot_list = []
# function_dict = {}
# for i, p in enumerate(page_list):
#     exec(function_str_list[i], function_dict, locals(), globals())
#     update_plot_list.append(function_dict["update_plot_" + p])


def update_plot_a():
    global page_updated
    if page_updated["A"]:
        for i in range(page_payloads["A"]):
            curve["A"][i].setData(page_dat["A"][0], page_dat["A"][i + 1])
        page_updated["A"] = False


def update_plot_h():
    global page_updated
    if page_updated["H"]:
        for i in range(page_payloads["H"]):
            curve["H"][i].setData(page_dat["H"][0], page_dat["H"][i + 1])
        page_updated["H"] = False


def update_plot_l():
    global page_updated
    if page_updated["L"]:
        for i in range(page_payloads["L"]):
            curve["L"][i].setData(page_dat["L"][0], page_dat["L"][i + 1])
        page_updated["L"] = False


def update_plot_m():
    global page_updated
    if page_updated["M"]:
        for i in range(page_payloads["M"]):
            curve["M"][i].setData(page_dat["M"][0], page_dat["M"][i + 1])
        page_updated["M"] = False


def update_plot_n():
    global page_updated
    if page_updated["N"]:
        for i in range(page_payloads["N"]):
            curve["N"][i].setData(page_dat["N"][0], page_dat["N"][i + 1])
        page_updated["N"] = False


def update_plot_o():
    global page_updated
    if page_updated["O"]:
        for i in range(page_payloads["O"]):
            curve["O"][i].setData(page_dat["O"][0], page_dat["O"][i + 1])
        page_updated["O"] = False


def update_plot_p():
    global page_updated
    if page_updated["P"]:
        for i in range(page_payloads["P"]):
            curve["P"][i].setData(page_dat["P"][0], page_dat["P"][i + 1])
        page_updated["P"] = False


def update_plot_r():
    global page_updated
    if page_updated["R"]:
        for i in range(page_payloads["R"]):
            curve["R"][i].setData(page_dat["R"][0], page_dat["R"][i + 1])
        page_updated["R"] = False


def update_plot_s():
    global page_updated
    if page_updated["S"]:
        for i in range(page_payloads["S"]):
            curve["S"][i].setData(page_dat["S"][0], page_dat["S"][i + 1])
        page_updated["S"] = False


def update_plot_u():
    global page_updated
    if page_updated["U"]:
        for i in range(page_payloads["U"]):
            curve["U"][i].setData(page_dat["U"][0], page_dat["U"][i + 1])
        page_updated["U"] = False


# update_plot_list = [update_plot_base(key) for key in page_list]
update_plot_list = [
    update_plot_a,
    update_plot_h,
    update_plot_l,
    update_plot_m,
    update_plot_n,
    update_plot_o,
    update_plot_p,
    update_plot_r,
    update_plot_s,
    update_plot_u,
]
update_plot = dict(zip(page_list, update_plot_list))

unprocess_list = []

scaling = 1
offset = 0

scaling_u = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 5e-3, 10e-3, 1e-3, 1e-3]
offset_u = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5.0, 7.2, 3.3, 3.3]


def update_serial():
    global page_updated
    # print("Update Serial")
    while ser.in_waiting >= 38:
        raw = ser.read(38)
        header = chr(int(raw[4]))
        if header in page_list:
            dat = page[header].unpack(raw[4:36])
            page_updated[header] = True
            # 時刻の追加
            if header == "M":
                for j in range(4):
                    page_dat[header][0].append(float(dat[j][1]) / 1000)
            elif header == "R" or header =='O' or header == 'L':
                for j in range(2):
                    page_dat[header][0].append(float(dat[j][1]) / 1000)
            else:
                page_dat[header][0].append(float(dat[1]) / 1000)
            # データの追加
            if header == "U":
                for i in range(1, page_payloads[header] + 1):
                    page_dat[header][i].append(
                        float(dat[i + 1]) * scaling_u[i - 1] + offset_u[i - 1]
                    )
            elif header == "M":
                for j in range(4):
                    for i in range(1, page_payloads[header] + 1):
                        page_dat[header][i].append(
                            float(dat[j][i + 1]) * scaling + offset
                        )
            elif header == "R" or header =='O' or header == 'L':
                for j in range(2):
                    for i in range(1, page_payloads[header] + 1):
                        page_dat[header][i].append(
                            float(dat[j][i + 1]) * scaling + offset
                        )
            else:
                for i in range(1, page_payloads[header] + 1):
                    page_dat[header][i].append(float(dat[i + 1]) * scaling + offset)
        else:
            if header not in unprocess_list:
                print(f"Unprocessed: {header}")
            unprocess_list.append(header)


# Plot by PyQtGraph
app = pg.mkQApp("Plotting Example")
# Enable antialiasing for prettier plots
pg.setConfigOptions(antialias=True)

# Page A
win_a = pg.GraphicsLayoutWidget(show=True, title="Basic plotting examples")
win_a.resize(1000, 600)
win_a.setWindowTitle("Page A")

p_a1 = win_a.addPlot(title="Accelerometer")
p_a1.showGrid(x=True, y=True)
p_a1.setLabel("left", "Raw value", units="")
p_a1.setLabel("bottom", "Time", units="s")
legend = p_a1.addLegend(offset=(10, 10))

p_a2 = win_a.addPlot(title="Gyroscope")
p_a2.showGrid(x=True, y=True)
p_a2.setLabel("left", "Raw value", units="")
p_a2.setLabel("bottom", "Time", units="s")
legend = p_a2.addLegend(offset=(10, 10))

p_a3 = win_a.addPlot(title="Barometer")
p_a3.showGrid(x=True, y=True)
p_a3.setLabel("left", "Pressure", units="Pa")
p_a3.setLabel("bottom", "Time", units="s")

p_a4 = win_a.addPlot(title="Thermometer")
p_a4.showGrid(x=True, y=True)
p_a4.setLabel("left", "Tempereture", units="deg.C")
p_a4.setLabel("bottom", "Time", units="s")

curve_a = [
    p_a1.plot(pen="r", name="X"),
    p_a1.plot(pen="g", name="Y"),
    p_a1.plot(pen="b", name="Z"),
    p_a2.plot(pen="r", name="X"),
    p_a2.plot(pen="g", name="Y"),
    p_a2.plot(pen="b", name="Z"),
    p_a3.plot(pen="r"),
    p_a4.plot(pen="r"),
    p_a4.plot(pen="g"),
]

# Page H
win_h = pg.GraphicsLayoutWidget(show=True, title="Basic plotting examples h")
win_h.resize(1000, 600)
win_h.setWindowTitle("Page H")

p_hd = win_h.addPlot(title="Digital")
p_hd.showGrid(x=True, y=True)
p_hd.setLabel("left", "Raw value", units="")
p_hd.setLabel("bottom", "Time", units="s")
legend = p_hd.addLegend(offset=(10, 10))

p_ha = win_h.addPlot(title="Analog")
p_ha.showGrid(x=True, y=True)
p_ha.setLabel("left", "Raw value", units="")
p_ha.setLabel("bottom", "Time", units="s")
legend = p_ha.addLegend(offset=(10, 10))

curve_h = [
    p_hd.plot(pen="r", name="CH 1"),
    p_hd.plot(pen="g", name="CH 2"),
    p_hd.plot(pen="b", name="CH 3"),
    p_hd.plot(pen="w", name="CH 4"),
    p_ha.plot(pen="r", name="CH 1"),
    p_ha.plot(pen="g", name="CH 2"),
    p_ha.plot(pen="b", name="CH 3"),
    p_ha.plot(pen="w", name="CH 4"),
    p_ha.plot(pen=pg.mkPen("r", style=QtCore.Qt.DashLine), name="CH 5"),
    p_ha.plot(pen=pg.mkPen("g", style=QtCore.Qt.DashLine), name="CH 6"),
    p_ha.plot(pen=pg.mkPen("b", style=QtCore.Qt.DashLine), name="CH 7"),
    p_ha.plot(pen=pg.mkPen("w", style=QtCore.Qt.DashLine), name="CH 8"),
]

# Page L
win_l = pg.GraphicsLayoutWidget(show=True, title="Basic plotting examples l")
win_l.resize(1000, 600)
win_l.setWindowTitle("Page L")

p_l = win_l.addPlot(title="Strain")
p_l.showGrid(x=True, y=True)
p_l.setLabel("left", "Raw value", units="")
p_l.setLabel("bottom", "Time", units="s")
legend = p_l.addLegend(offset=(10, 10))

curve_l = [
    p_l.plot(pen="r", name="CH 1"),
    p_l.plot(pen="g", name="CH 2"),
    p_l.plot(pen="b", name="CH 3"),
    p_l.plot(pen="w", name="CH 4"),
]

# Page M
win_m = pg.GraphicsLayoutWidget(show=True, title="Basic plotting examples m")
win_m.resize(1000, 600)
win_m.setWindowTitle("Page M")

p_m = win_m.addPlot(title="Magnetometer")
p_m.showGrid(x=True, y=True)
p_m.setLabel("left", "Raw value", units="")
p_m.setLabel("bottom", "Time", units="s")
legend = p_m.addLegend(offset=(10, 10))

curve_m = [
    p_m.plot(pen="r", name="X"),
    p_m.plot(pen="g", name="Y"),
    p_m.plot(pen="b", name="Z"),
]

# Page N
win_n = pg.GraphicsLayoutWidget(show=True, title="Basic plotting examples n")
win_n.resize(1000, 600)
win_n.setWindowTitle("Page N")

p_n1 = win_n.addPlot(title="Navigation 1")
p_n1.showGrid(x=True, y=True)
p_n1.setLabel("left", "Raw value", units="")
p_n1.setLabel("bottom", "Time", units="s")
legend = p_n1.addLegend(offset=(10, 10))

p_n2 = win_n.addPlot(title="Navigation 2")
p_n2.showGrid(x=True, y=True)
p_n2.setLabel("left", "Velocity", units="m/s")
p_n2.setLabel("bottom", "Time", units="s")
legend = p_n2.addLegend(offset=(10, 10))

p_n3 = win_n.addPlot(title="Navigation 3")
p_n3.showGrid(x=True, y=True)
p_n3.setLabel("left", "Raw value", units="deg")
p_n3.setLabel("bottom", "Time", units="s")
legend = p_n3.addLegend(offset=(10, 10))

curve_n = [
    p_n1.plot(pen="r", name="Latitude"),
    p_n1.plot(pen="g", name="Longitude"),
    p_n1.plot(pen="b", name="Altitude"),
    p_n2.plot(pen="r", name="N"),
    p_n2.plot(pen="g", name="E"),
    p_n2.plot(pen="b", name="D"),
    p_n3.plot(pen="r", name="Yaw"),
    p_n3.plot(pen="g", name="Roll"),
    p_n3.plot(pen="b", name="Pitch"),
]

# Page O
win_o = pg.GraphicsLayoutWidget(show=True, title="Basic plotting examples o")
win_o.resize(1000, 600)
win_o.setWindowTitle("Page O")

p_o = win_o.addPlot(title="Strain")
p_o.showGrid(x=True, y=True)
p_o.setLabel("left", "Raw value", units="")
p_o.setLabel("bottom", "Time", units="s")
legend = p_o.addLegend(offset=(10, 10))

curve_o = [
    p_o.plot(pen="r", name="CH 1"),
    p_o.plot(pen="g", name="CH 2"),
    p_o.plot(pen="b", name="CH 3"),
    p_o.plot(pen="w", name="CH 4"),
]

# Page P
win_p = pg.GraphicsLayoutWidget(show=True, title="Basic plotting examples p")
win_p.resize(1000, 600)
win_p.setWindowTitle("Page P")

p_p1 = win_p.addPlot(title="Pressure")
p_p1.showGrid(x=True, y=True)
p_p1.setLabel("left", "Raw value", units="")
p_p1.setLabel("bottom", "Time", units="s")
legend = p_p1.addLegend(offset=(10, 10))

p_p2 = win_p.addPlot(title="Temperature")
p_p2.showGrid(x=True, y=True)
p_p2.setLabel("left", "Raw value", units="")
p_p2.setLabel("bottom", "Time", units="s")
legend = p_p2.addLegend(offset=(10, 10))

curve_p = [
    p_p1.plot(pen="r", name="CH 1"),
    p_p1.plot(pen="g", name="CH 2"),
    p_p1.plot(pen="b", name="CH 3"),
    p_p2.plot(pen="r", name="CH 1"),
    p_p2.plot(pen="g", name="CH 2"),
    p_p2.plot(pen="b", name="CH 3"),
]

# Page R
win_r = pg.GraphicsLayoutWidget(show=True, title="Basic plotting examples r")
win_r.resize(1000, 600)
win_r.setWindowTitle("Page R")

p_r1 = win_r.addPlot(title="Pressure")
p_r1.showGrid(x=True, y=True)
p_r1.setLabel("left", "Raw value", units="")
p_r1.setLabel("bottom", "Time", units="s")
legend = p_r1.addLegend(offset=(10, 10))

p_r2 = win_r.addPlot(title="Temperature")
p_r2.showGrid(x=True, y=True)
p_r2.setLabel("left", "Raw value", units="")
p_r2.setLabel("bottom", "Time", units="s")
legend = p_r2.addLegend(offset=(10, 10))

curve_r = [
    p_r1.plot(pen="r", name="CH 1"),
    p_r1.plot(pen="g", name="CH 2"),
    p_r1.plot(pen="b", name="CH 3"),
    p_r2.plot(pen="r", name="CH 1"),
    p_r2.plot(pen="g", name="CH 2"),
    p_r2.plot(pen="b", name="CH 3"),
]

# Page S
win_s = pg.GraphicsLayoutWidget(show=True, title="Basic plotting examples s")
win_s.resize(1000, 600)
win_s.setWindowTitle("Page S")

p_s1 = win_s.addPlot(title="System supervisor 1")
p_s1.showGrid(x=True, y=True)
p_s1.setLabel("left", "Raw value", units="")
p_s1.setLabel("bottom", "Time", units="s")
legend = p_s1.addLegend(offset=(10, 10))

p_s2 = win_s.addPlot(title="System supervisor 2")
p_s2.showGrid(x=True, y=True)
p_s2.setLabel("left", "Raw value", units="")
p_s2.setLabel("bottom", "Time", units="s")
legend = p_s2.addLegend(offset=(10, 10))

p_s3 = win_s.addPlot(title="System supervisor 3")
p_s3.showGrid(x=True, y=True)
p_s3.setLabel("left", "Raw value", units="")
p_s3.setLabel("bottom", "Time", units="s")
legend = p_s3.addLegend(offset=(10, 10))

curve_s = [
    p_s1.plot(pen="r", name="CH 1"),
    p_s1.plot(pen="g", name="CH 2"),
    p_s1.plot(pen="b", name="CH 3"),
    p_s1.plot(pen="w", name="CH 4"),
    p_s2.plot(pen="r", name="CH 5"),
    p_s2.plot(pen="g", name="CH 6"),
    p_s2.plot(pen="b", name="CH 7"),
    p_s2.plot(pen="w", name="CH 8"),
    p_s3.plot(pen="r", name="CH 9"),
    p_s3.plot(pen="g", name="CH 10"),
    p_s3.plot(pen="b", name="CH 11"),
    p_s3.plot(pen="w", name="CH 12"),
]

# Page U
win_u = pg.GraphicsLayoutWidget(show=True, title="Basic plotting examples u")
win_u.resize(1000, 600)
win_u.setWindowTitle("Page U")

p_u1 = win_u.addPlot(title="Sensor data")
p_u1.showGrid(x=True, y=True)
p_u1.setLabel("left", "Raw value", units="")
p_u1.setLabel("bottom", "Time", units="s")
legend = p_u1.addLegend(offset=(10, 10))

p_u2 = win_u.addPlot(title="Current")
p_u2.showGrid(x=True, y=True)
p_u2.setLabel("left", "Raw value", units="")
p_u2.setLabel("bottom", "Time", units="s")
legend = p_u2.addLegend(offset=(10, 10))

p_u3 = win_u.addPlot(title="Voltage")
p_u3.showGrid(x=True, y=True)
p_u3.setLabel("left", "Voltage", units="V")
p_u3.setLabel("bottom", "Time", units="s")
legend = p_u3.addLegend(offset=(10, 10))

curve_u = [
    p_u1.plot(pen="r", name="Input 1"),
    p_u1.plot(pen="g", name="Input 2"),
    p_u1.plot(pen="b", name="Input 3"),
    p_u1.plot(pen=pg.mkPen("r", style=QtCore.Qt.DashLine), name="Output 1"),
    p_u1.plot(pen=pg.mkPen("g", style=QtCore.Qt.DashLine), name="Output 2"),
    p_u2.plot(pen="r", name="Current 1"),
    p_u2.plot(pen="g", name="Current 2"),
    p_u2.plot(pen="b", name="Current 3"),
    p_u2.plot(pen="w", name="Current 4"),
    p_u2.plot(pen="c", name="Current 5"),
    p_u3.plot(pen="r", name="Voltage 1, V_BUS"),
    p_u3.plot(pen="g", name="Voltage 2, V_BAT"),
    p_u3.plot(pen="b", name="Voltage 3, V_CAN"),
    p_u3.plot(pen="w", name="Voltage 4, V_SYS"),
]

# curves
curve_list = [curve_a, curve_h, curve_l, curve_m, curve_n, curve_o, curve_p, curve_r, curve_s, curve_u]
curve = dict(zip(page_list, curve_list))

# reset buffer
ser.reset_input_buffer()

# Set timers
timer_plot = {key: QtCore.QTimer() for key in page_list}
graph_update_period = 33
for key in page_list:
    timer_plot[key].timeout.connect(update_plot[key])
    timer_plot[key].start(graph_update_period)

timer_serial = QtCore.QTimer()
timer_serial.timeout.connect(update_serial)
timer_serial.start(1)

if __name__ == "__main__":
    pg.exec()
