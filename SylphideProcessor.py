# -*- coding: utf-8 -*-
import struct
import configparser
import numpy as np
import scipy.interpolate

'''
Page
'''
class page():
    size = 32
    def __init__(self):
        self.payload_format = ''
        self.payload = []
    def unpack(self, dat):
        return dat
    def append(self, dat):
        py_data = self.unpack(dat)
        self.payload.append(py_data)

'''
Page CSV
'''
class pagecsv(page):
    def __init__(self):
        page.__init__(self)
        self.csv_header = ''
    def save_raw_csv(self, filename):
        if len(self.payload) > 0:
            np.savetxt(filename, np.array(self.payload), fmt='%.7f',
                       delimiter = ', ', header=self.csv_header)
    def time_gps_lock(self):
        dat = np.array(self.payload)
        time_gps = dat[:,1] # sec
        time_gps_diff = np.diff(time_gps)
        time_int = dat[:,0] # sec
        time_int_diff = np.remainder(np.diff(time_int),2**8)
        time_int_gps_diff = time_gps_diff - time_int_diff
        time_gps_lock_index = np.where(time_int_gps_diff == np.max(time_int_gps_diff))
        return time_gps[time_gps_lock_index[0] + 1]
    def interporation(self, time_gps, dat):
        return scipy.interpolate.interp1d(time_gps, dat)
    def unpack(self, dat):
        py_data = struct.unpack(self.payload_format, dat)
        return py_data
    def millisec2sec(self, dat):
        if dat.ndim == 2:
            dat[:, 0] /= 1.0e3
            dat[:, 1] /= 1.0e3
        elif dat.ndim == 1:
            dat[0] /= 1.0e3
            dat[1] /= 1.0e3
        return
    def raw2phys(self):
        py_data = np.array(self.payload, dtype=np.float64)
        self.millisec2sec(py_data)
        return

'''
Page A
@memo: 24ビットデータの変換は特殊。unpackをオーバーロード
'''
class pagea(pagecsv):
    def __init__(self):
        page.__init__(self)
        self.payload_format = '<1x1B1I24B1H'
        self.csv_header = 'Internal Time (s), GNSS Time (s), \
Acc X (g), Acc Y (g), Acc Z (g), \
Gyr X (deg./s), Gyr Y (deg./s), Gyr Z (deg./s), \
Pressure (Pa), Temperature (deg. C), \
IMU Temperature (deg. C)'
        config = configparser.ConfigParser()
        config.read('config.ini')
        configA = config['A']
        self.scaling_acc = []
        self.scaling_acc.append(float(configA['scaling_acc_x']))
        self.scaling_acc.append(float(configA['scaling_acc_y']))
        self.scaling_acc.append(float(configA['scaling_acc_z']))
        self.offset_acc = []
        self.offset_acc.append(float(configA['offset_acc_x']))
        self.offset_acc.append(float(configA['offset_acc_y']))
        self.offset_acc.append(float(configA['offset_acc_z']))
        self.scaling_gyr = []
        self.scaling_gyr.append(float(configA['scaling_gyr_x']))
        self.scaling_gyr.append(float(configA['scaling_gyr_y']))
        self.scaling_gyr.append(float(configA['scaling_gyr_z']))
        self.offset_gyr = []
        self.offset_gyr.append(float(configA['offset_gyr_x']))
        self.offset_gyr.append(float(configA['offset_gyr_y']))
        self.offset_gyr.append(float(configA['offset_gyr_z']))
        self.scaling_prs = float(configA['scaling_prs'])
        self.scaling_tmp_prs = float(configA['scaling_tmp_prs'])
        self.offset_tmp_prs = float(configA['offset_tmp_prs'])
        self.scaling_tmp_imu = float(configA['scaling_tmp_imu'])
        self.offset_tmp_imu = float(configA['offset_tmp_imu'])
    def convert24bit(self, dat):
        return dat[2] + dat[1] * 2 ** 8 + dat[0] * 2 ** 16
    def raw2phys(self):
        py_data = np.array(self.payload, dtype=np.float64)
        self.millisec2sec(py_data)
        if py_data.ndim == 2:
            for i in range(3):
                py_data[:, 2 + i] = (py_data[:, 2 + i] - self.offset_acc[i]) / self.scaling_acc[i]
                py_data[:, 5 + i] = (py_data[:, 5 + i] - self.offset_gyr[i]) / self.scaling_gyr[i]
            py_data[:,  8] = py_data[:,  8] * self.scaling_prs
            py_data[:,  9] = py_data[:,  9] * self.scaling_tmp_prs - self.offset_tmp_prs
            py_data[:, 10] = py_data[:, 10] * self.scaling_tmp_imu - self.offset_tmp_imu
        if py_data.ndim == 1:
            for i in range(3):
                py_data[2 + i] = (py_data[2 + i] - self.offset_acc[i]) / self.scaling_acc[i]
                py_data[5 + i] = (py_data[5 + i] - self.offset_gyr[i]) / self.scaling_gyr[i]
            py_data[8] = py_data[8] * self.scaling_prs
            py_data[9] = py_data[9] * self.scaling_tmp_prs - self.offset_tmp_prs
            py_data[10] = py_data[10] * self.scaling_tmp_imu - self.offset_tmp_imu
        self.payload = py_data
        return
    def unpack(self, dat):
        py_data = struct.unpack(self.payload_format, dat)
        dat_conv = np.zeros([8])
        for i in range(8):
            dat_conv[i] = self.convert24bit(py_data[2 + 3 * i:5 + 3 * i])
        out = (py_data[0],py_data[1],) + tuple(dat_conv) + (py_data[26],)
        return out

'''
Page F
@memo: 12ビットデータの変換は特殊。unpackをオーバーロード
@todo: テストデータを用意
'''
class pagef(pagecsv):
    def __init__(self):
        page.__init__(self)
        self.payload_format = '1x3B1I24B'
        self.csv_header = 'Internal Time (ms), GNSS Time (ms), \
In0 (us), Out0 (us), \
In1 (us), Out1 (us), \
In2 (us), Out2 (us), \
In3 (us), Out3 (us), \
In4 (us), Out4 (us), \
In5 (us), Out5 (us), \
In6 (us), Out6 (us), \
In7 (us), Out7 (us)'
    def convert2x12bit(self, dat):
        return [(dat[0] * 2 ** 16 + (dat[1] & 0xF0)) / 2 ** 4, (dat[1] & 0x0F) * 2 ** 16 + dat[0]]
    def unpack(self, dat):
        py_data = struct.unpack(self.payload_format, dat)
        dat_conv = np.zeros([8, 2])
        for i in range(8):
            dat_conv[i,:] = self.convert2x12bit(py_data[2 + 3 * i: 5 + 3 * i])
        print(dat_conv)
        out = (py_data[0],py_data[1],) + tuple(dat_conv) + (py_data[26],)
        return out

'''
Page G
@memo: バイナリをそのまま出力。unpackをオーバーロード
@todo: OK
'''
class pageg(page):
    def __init__(self):
        page.__init__(self)
        self.payload_format = '1x31B'
    def save_raw_ubx(self, filename):
        if len(self.payload) > 0:
            with open(filename, mode='wb') as f:
                for dat in self.payload:
                    f.write(dat)
    def unpack(self, dat):
        return dat[1:]

'''
Page H
'''
class pageh(pagecsv):
    def __init__(self):
        page.__init__(self)
        self.payload_format = '<1x2x1B1I12H'
        self.csv_header = 'Internal Time (s), GNSS Time (s), \
Cadence (), Cadence, Airspeed, Altitude, \
ADC0, ADC1, ADC2, ADC3, ADC4, ADC5, ADC6, ADC7'
        config = configparser.ConfigParser()
        config.read('config.ini')
        configH = config['H']
        self.scaling_cadence = []
        self.scaling_cadence.append(float(configH['scaling_cadence0']))
        self.scaling_cadence.append(float(configH['scaling_cadence1']))
        self.scaling_ias = float(configH['scaling_ias'])
        self.offset_ias = float(configH['offset_ias'])
        self.scaling_alt = float(configH['scaling_alt'])
        self.scaling_adc = []
        self.scaling_adc.append(float(configH['scaling_adc0']))
        self.scaling_adc.append(float(configH['scaling_adc1']))
        self.scaling_adc.append(float(configH['scaling_adc2']))
        self.scaling_adc.append(float(configH['scaling_adc3']))
        self.scaling_adc.append(float(configH['scaling_adc4']))
        self.scaling_adc.append(float(configH['scaling_adc5']))
        self.scaling_adc.append(float(configH['scaling_adc6']))
        self.scaling_adc.append(float(configH['scaling_adc7']))
        self.offset_adc = []
        self.offset_adc.append(float(configH['offset_adc0']))
        self.offset_adc.append(float(configH['offset_adc1']))
        self.offset_adc.append(float(configH['offset_adc2']))
        self.offset_adc.append(float(configH['offset_adc3']))
        self.offset_adc.append(float(configH['offset_adc4']))
        self.offset_adc.append(float(configH['offset_adc5']))
        self.offset_adc.append(float(configH['offset_adc6']))
        self.offset_adc.append(float(configH['offset_adc7']))
    def raw2phys(self):
        py_data = np.array(self.payload, dtype=np.float64)
        self.millisec2sec(py_data)
        for i in range(2):
            py_data[:, 2 + i] = self.scaling_cadence[i] / py_data[:, 2 + i]
        py_data[:, 4] = py_data[:, 4] * self.scaling_ias + self.offset_ias
        py_data[:, 5] = py_data[:, 5] * self.scaling_alt
        for i in range(8):
            py_data[:, 6 + i] = py_data[:, 6 + i] * self.scaling_adc[i] - self.offset_adc[i]
        self.payload = py_data
        return

'''
Page M
'''
class pagem(pagecsv):
    def __init__(self):
        page.__init__(self)
        self.payload_format = '<1x2x1B1I12h'
        self.csv_header = 'Internal Time (s), GNSS Time (s), Mag X, Mag Y, Mag Z'
        config = configparser.ConfigParser()
        config.read('config.ini')
        configM = config['M']
        self.sampling_interval = float(configM['sampling_interval'])
        self.scaling = np.array([float(configM['scaling_x']),
                                 float(configM['scaling_y']),
                                 float(configM['scaling_z'])])
        self.offset = np.array([float(configM['offset_x']),
                                 float(configM['offset_y']),
                                 float(configM['offset_z'])])
    def raw2phys(self):
        py_data = np.array(self.payload, dtype=np.float64)
        self.millisec2sec(py_data)
        for i in range(3):
            py_data[:, 2 + i] = py_data[:, 2 + i] * self.scaling[i] - self.offset[i]
        self.payload = py_data
        return
    def unpack(self, dat):
        py_data = struct.unpack(self.payload_format, dat)
        out = []
        for i in range(4):
            out.append((py_data[0], py_data[1] - self.sampling_interval * (3 - i), py_data[3 + i * 3], py_data[2 + i * 3], -py_data[4 + i * 3],))
        return out
    def append(self, dat):
        py_data = self.unpack(dat)
        for i in range(4):
            self.payload.append(py_data[i])

'''
Page N
'''
class pagen(pagecsv):
    def __init__(self):
        page.__init__(self)
        self.payload_format = '<1x1B2x4i6h'
        self.csv_header = 'Internal Time (s), GNSS Time (s), \
Longitude (deg.), Latitude (deg.), Altitude (m), \
Velocity N (m/s), Velocity E (m/s), Velocity D (m/s), \
Yaw (deg.), Roll (deg.), Pitch (deg.)'
    def raw2phys(self):
        py_data = np.array(self.payload, dtype=np.float64)
        self.millisec2sec(py_data)
        py_data[:, 2] /= 1.0e7
        py_data[:, 3] /= 1.0e7
        py_data[:, 4] /= 1.0e4
        for i in np.arange(5,11):
            py_data[:, i] /= 1.0e2
        self.payload = py_data
        return

'''
Page O
@memo: 24ビットデータの変換は特殊。unpackをオーバーロード
'''
class pageo(pagecsv):
    def __init__(self):
        page.__init__(self)
        self.payload_format = '<1x1B1I24B1H'
        self.csv_header = 'Internal Time (s), GNSS Time (s), Ch1, Ch2, Ch3, Ch4'
#        config = configparser.ConfigParser()
#        config.read('config.ini')
#        configO = config['O']
#        self.scaling_acc = []
#        self.scaling_acc.append(float(configO['scaling_acc_x']))
#        self.scaling_acc.append(float(configO['scaling_acc_y']))
#        self.scaling_acc.append(float(configO['scaling_acc_z']))
#        self.offset_acc = []
#        self.offset_acc.append(float(configO['offset_acc_x']))
#        self.offset_acc.append(float(configO['offset_acc_y']))
#        self.offset_acc.append(float(configO['offset_acc_z']))
#        self.scaling_gyr = []
#        self.scaling_gyr.append(float(configO['scaling_gyr_x']))
#        self.scaling_gyr.append(float(configO['scaling_gyr_y']))
#        self.scaling_gyr.append(float(configO['scaling_gyr_z']))
#        self.offset_gyr = []
#        self.offset_gyr.append(float(configO['offset_gyr_x']))
#        self.offset_gyr.append(float(configO['offset_gyr_y']))
#        self.offset_gyr.append(float(configO['offset_gyr_z']))
#        self.scaling_prs = float(configO['scaling_prs'])
#        self.scaling_tmp_prs = float(configO['scaling_tmp_prs'])
#        self.offset_tmp_prs = float(configO['offset_tmp_prs'])
#        self.scaling_tmp_imu = float(configO['scaling_tmp_imu'])
#        self.offset_tmp_imu = float(configO['offset_tmp_imu'])
    def convert24bit(self, dat):
        return dat[2] + dat[1] * 2 ** 8 + dat[0] * 2 ** 16
    def raw2phys(self):
        py_data = np.array(self.payload, dtype=np.float64)
        self.millisec2sec(py_data)
#        if py_data.ndim == 2:
#            for i in range(3):
#                py_data[:, 2 + i] = (py_data[:, 2 + i] - self.offset_acc[i]) / self.scaling_acc[i]
#                py_data[:, 5 + i] = (py_data[:, 5 + i] - self.offset_gyr[i]) / self.scaling_gyr[i]
#            py_data[:,  8] = py_data[:,  8] * self.scaling_prs
#            py_data[:,  9] = py_data[:,  9] * self.scaling_tmp_prs - self.offset_tmp_prs
#            py_data[:, 10] = py_data[:, 10] * self.scaling_tmp_imu - self.offset_tmp_imu
#        if py_data.ndim == 1:
#            for i in range(3):
#                py_data[2 + i] = (py_data[2 + i] - self.offset_acc[i]) / self.scaling_acc[i]
#                py_data[5 + i] = (py_data[5 + i] - self.offset_gyr[i]) / self.scaling_gyr[i]
#            py_data[8] = py_data[8] * self.scaling_prs
#            py_data[9] = py_data[9] * self.scaling_tmp_prs - self.offset_tmp_prs
#            py_data[10] = py_data[10] * self.scaling_tmp_imu - self.offset_tmp_imu
        self.payload = py_data
        return
    def unpack(self, dat):
        py_data = struct.unpack(self.payload_format, dat)
        dat_conv = np.zeros([8])
        for i in range(8):
            dat_conv[i] = self.convert24bit(py_data[2 + 3 * i:5 + 3 * i])
            if(dat_conv[i] > 2 ** 23):
                dat_conv[i] = -2 ** 24 + dat_conv[i]
        out = []
        out.append((py_data[0],py_data[1] - 20,) + tuple(dat_conv[:4]))
        out.append((py_data[0],py_data[1],) + tuple(dat_conv[4:]))
        return out
    def append(self, dat):
        py_data = self.unpack(dat)
        for i in range(2):
            self.payload.append(py_data[i])
'''
Page P
'''
class pagep(pagecsv):
    def __init__(self):
        page.__init__(self)
        self.payload_format = '<1x3B1I12H'
        self.csv_header = 'Internal Time (s), GNSS Time (s), '
    def raw2phys(self):
        py_data = np.array(self.payload, dtype=np.float64)
        self.millisec2sec(py_data)
        self.payload = py_data
        return

'''
Page S
'''
class pages(pagecsv):
    def __init__(self):
        page.__init__(self)
        self.payload_format = '<1x2x1B1I12H'
        self.csv_header = 'Internal Time (s), GNSS Time (s), 3.3V (V), Power (V), 5.0V (V), Battery current (mA), USB current (mA)'
        config = configparser.ConfigParser()
        config.read('config.ini')
        configS = config['S']
        self.scaling_3V3_Vol = float(configS['scaling_3V3_Vol'])
        self.scaling_Pow_Vol = float(configS['scaling_Pow_Vol'])
        self.scaling_5V0_Vol = float(configS['scaling_5V0_Vol'])
        self.scaling_Bat_Cur = float(configS['scaling_Bat_Cur'])
        self.scaling_USB_Cur = float(configS['scaling_USB_Cur'])
    def raw2phys(self):
        py_data = np.array(self.payload, dtype=np.float64)
        self.millisec2sec(py_data)
        py_data[:, 2] = py_data[:, 2] * self.scaling_3V3_Vol
        py_data[:, 3] = py_data[:, 3] * self.scaling_Pow_Vol
        py_data[:, 4] = py_data[:, 4] * self.scaling_5V0_Vol
        py_data[:, 5] = py_data[:, 5] * self.scaling_Bat_Cur
        py_data[:, 6] = py_data[:, 6] * self.scaling_USB_Cur
        self.payload = py_data
        return
