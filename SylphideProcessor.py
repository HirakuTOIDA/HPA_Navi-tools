# -*- coding: utf-8 -*-
"""
Sylphide Processor.

Convert Sylphide format binary data into readable csv or ubx files.
"""
import struct
import configparser
import numpy as np
import pandas as pd
# import scipy.interpolate

# @todo tuple -> list


class page():
    """
    Store and unpack abstract page data.

    Attributes
    ----------
    payload_format : str
        Description of format used in unpack.
    payload : list
        List of unpacked data.

    @todo OK
    """

    size = 32

    def __init__(self):
        self.payload_format = ''
        self.payload = []

    def unpack(self, dat):
        """
        Unpack raw binary data.

        Parameters
        ----------
        dat : TYPE
            Input data to be unpacked.

        Returns
        -------
        dat : TYPE
            Output data unpacked.

        """
        return dat

    def append(self, dat):
        """
        Append unpacked data to data list.

        Parameters
        ----------
        dat : TYPE
            Input data to be unpacked and stored.

        Returns
        -------
        None.

        """
        py_data = self.unpack(dat)
        self.payload.append(py_data)


class pagecsv(page):
    """
    Store and unpack page data.

    Attributes
    ----------
    csv_header : str
        Header added to output csv file.
    filename_config : str
        Filename of configureation file.

    @todo OK
    """

    def __init__(self):
        super().__init__()
        self.csv_header = ''
        self.filename_config = 'config.ini'  # @todo ベタ書きでよい?

    def save_raw_csv(self, filename):
        """
        Save stored data to csv file.

        Parameters
        ----------
        filename : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        if len(self.payload) > 1:
            df = pd.DataFrame(self.payload)
            header = self.csv_header
            header[0] = "# " + header[0]
            df.columns = header
            df.to_csv(filename, index=False)
    # @todo check
    # def time_gps_lock(self):
    #     dat = np.array(self.payload)
    #     time_gps = dat[:,1]
    #     time_gps_diff = np.diff(time_gps)
    #     time_int = dat[:,0]
    #     time_int_diff = np.remainder(np.diff(time_int),2**8)
    #     time_int_gps_diff = time_gps_diff - time_int_diff
    #     time_gps_lock_index = np.where(time_int_gps_diff == np.max(time_int_gps_diff))
    #     return time_gps[time_gps_lock_index[0] + 1]
    # @todo check
    # def interporation(self, time_gps, dat):
    #     return scipy.interpolate.interp1d(time_gps, dat)

    def unpack(self, dat):
        return list(struct.unpack(self.payload_format, dat))

    def millisec2sec(self, dat, column=1):
        """
        Convert time from millisecond to second.

        Parameters
        ----------
        dat : TYPE
            DESCRIPTION.
        column : TYPE, optional
            DESCRIPTION. The default is 1.

        Returns
        -------
        None.

        """
        dat[:, column] /= 1.0e3

    def raw2phys(self):
        if len(self.payload) > 1:
            py_data = np.array(self.payload, dtype=np.float64)
            self.millisec2sec(py_data)
            self.payload = py_data


class pagecsv24(pagecsv):
    """
    Store and unpack page data with 24 bit format.

    @memo 24ビットデータの変換は特殊。unpackをオーバーロード
    @todo uintとintを実装
    """

    def convert24bit(self, dat):
        """
        Convert 24 bit data to unsigned int.

        Parameters
        ----------
        dat : TYPE
            DESCRIPTION.

        Returns
        -------
        TYPE
            DESCRIPTION.

        """
        return dat[2] + dat[1] * 2 ** 8 + dat[0] * 2 ** 16


class pagea(pagecsv24):
    """
    Store and unpack A page data.

    - Analog
    @todo OK
    """

    def __init__(self):
        super().__init__()
        self.payload_format = '<1x1B1I24B1H'
        self.csv_header = ['Internal Time', 'GNSS Time (s)',
                           'Acc X (g)', 'Acc Y (g)', 'Acc Z (g)',
                           'Gyr X (deg./s)', 'Gyr Y (deg./s)',
                           'Gyr Z (deg./s)',
                           'Pressure (Pa)', 'Temperature (deg. C)',
                           'IMU Temperature (deg. C)']
        config = configparser.ConfigParser()
        config.read(self.filename_config)
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

    def raw2phys(self):
        if len(self.payload) > 1:
            py_data = np.array(self.payload, dtype=np.float64)
            self.millisec2sec(py_data)
            for i in range(3):
                py_data[:, 2 + i] = (py_data[:, 2 + i] - self.offset_acc[i]) \
                                    / self.scaling_acc[i]
                py_data[:, 5 + i] = (py_data[:, 5 + i] - self.offset_gyr[i]) \
                    / self.scaling_gyr[i]
            py_data[:,  8] = py_data[:,  8] * self.scaling_prs
            py_data[:,  9] = py_data[:,  9] * self.scaling_tmp_prs \
                - self.offset_tmp_prs
            py_data[:, 10] = py_data[:, 10] * self.scaling_tmp_imu \
                - self.offset_tmp_imu
            self.payload = py_data

    def unpack(self, dat):
        py_data = list(struct.unpack(self.payload_format, dat))
        dat_conv = np.zeros([8])
        for i in range(8):
            dat_conv[i] = self.convert24bit(py_data[2 + 3 * i:5 + 3 * i])
        return [py_data[0], py_data[1]] + list(dat_conv) + [py_data[26]]


class pagef(pagecsv):
    """
    Store and unpack F page data.

    - FPGA
    @memo 12ビットデータの変換は特殊。unpackをオーバーロード
    @todo OK
    """

    def __init__(self):
        super().__init__()
        self.payload_format = '1x2x1B1I24B'
        self.csv_header = ['Internal Time', 'GNSS Time (s)',
                           'In0 (us)', 'Out0 (us)',
                           'In1 (us)', 'Out1 (us)',
                           'In2 (us)', 'Out2 (us)',
                           'In3 (us)', 'Out3 (us)',
                           'In4 (us)', 'Out4 (us)',
                           'In5 (us)', 'Out5 (us)',
                           'In6 (us)', 'Out6 (us)',
                           'In7 (us)', 'Out7 (us)']

    def convert2x12bit(self, dat):
        """
        Convert 3 bytes data to two 12 bit data.

        Parameters
        ----------
        dat : TYPE
            input data.

        Returns
        -------
        list
            converted data.

        """
        return [(dat[1] & 0xF0) * 2 ** 4 + dat[0],
                (dat[1] & 0x0F) * 2 ** 8 + dat[2]]

    def unpack(self, dat):
        py_data = list(struct.unpack(self.payload_format, dat))
        dat_conv = np.zeros([16])
        for i in range(8):
            dat_conv[i * 2] = \
                self.convert2x12bit(py_data[2 + 3 * i: 5 + 3 * i])[0]
            dat_conv[i * 2 + 1] = \
                self.convert2x12bit(py_data[2 + 3 * i: 5 + 3 * i])[1]
        return [py_data[0], py_data[1]] + list(dat_conv)


class pageg(page):
    """
    Store and unpack G page data.

    - GNSS
    @memo バイナリをそのまま出力。unpackをオーバーロード
    @todo OK
    """

    def __init__(self):
        super().__init__()

    def save_raw_ubx(self, filename):
        """
        Save raw ubx binary file.

        Parameters
        ----------
        filename : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        if len(self.payload) > 1:
            with open(filename, mode='wb') as f:
                for dat in self.payload:
                    f.write(dat)

    def unpack(self, dat):
        return dat[1:]


class pageh(pagecsv):
    """
    Store and unpack H page data.

    - Human powered airplane
    @todo OK
    """

    def __init__(self):
        super().__init__()
        self.payload_format = '<1x2x1B1I12H'
        self.csv_header = ['Internal Time', 'GNSS Time (s)',
                           'Cadence (rpm)', 'Cadence (rpm)', 'Airspeed (m/s)',
                           'Altitude (m)',
                           'ADC0 (deg.)', 'ADC1 (deg.)', 'ADC2 (deg.)', 'ADC3',
                           'ADC4', 'ADC5', 'ADC6', 'ADC7']
        config = configparser.ConfigParser()
        config.read(self.filename_config)
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
        if len(self.payload) > 1:
            py_data = np.array(self.payload, dtype=np.float64)
            self.millisec2sec(py_data)
            for i in range(2):
                py_data[:, 2 + i] = self.scaling_cadence[i] / py_data[:, 2 + i]
            py_data[:, 4] = py_data[:, 4] * self.scaling_ias + self.offset_ias
            py_data[:, 5] = py_data[:, 5] * self.scaling_alt
            for i in range(8):
                py_data[:, 6 + i] = py_data[:, 6 + i] * self.scaling_adc[i] \
                    - self.offset_adc[i]
            self.payload = py_data


class pagem(pagecsv):
    """
    Store and unpack M page data.

    - Magnetometer
    @todo OK
    """

    def __init__(self):
        super().__init__()
        self.payload_format = '<1x2x1B1I12h'
        self.csv_header = ['Internal Time', 'GNSS Time (s)',
                           'Mag X', 'Mag Y', 'Mag Z']
        config = configparser.ConfigParser()
        config.read(self.filename_config)
        configM = config['M']
        self.sampling_interval = float(configM['sampling_interval'])
        self.scaling = np.array([float(configM['scaling_x']),
                                 float(configM['scaling_y']),
                                 float(configM['scaling_z'])])
        self.offset = np.array([float(configM['offset_x']),
                                float(configM['offset_y']),
                                float(configM['offset_z'])])

    def raw2phys(self):
        if len(self.payload) > 1:
            py_data = np.array(self.payload, dtype=np.float64)
            self.millisec2sec(py_data)
            for i in range(3):
                py_data[:, 2 + i] = py_data[:, 2 + i] * self.scaling[i] \
                    - self.offset[i]
            self.payload = py_data

    def unpack(self, dat):
        py_data = list(struct.unpack(self.payload_format, dat))
        out = []
        for i in range(4):
            out.append([py_data[0],
                        py_data[1] - self.sampling_interval * (3 - i),
                        py_data[3 + i * 3],
                        py_data[2 + i * 3],
                        -py_data[4 + i * 3]])
        return out

    def append(self, dat):
        py_data = self.unpack(dat)
        for i in range(4):
            self.payload.append(py_data[i])


class pagen(pagecsv):
    """
    Store and unpack N page data.

    - Navigation
    @todo OK
    """

    def __init__(self):
        super().__init__()
        self.payload_format = '<1x1B2x4i6h'
        self.csv_header = ['Data Number', 'GNSS Time (s)',
                           'Longitude (deg.)', 'Latitude (deg.)',
                           'Altitude (m)',
                           'Velocity N (m/s)', 'Velocity E (m/s)',
                           'Velocity D (m/s)',
                           'Yaw (deg.)', 'Roll (deg.)', 'Pitch (deg.)']

    def raw2phys(self):
        if len(self.payload) > 1:
            py_data = np.array(self.payload, dtype=np.float64)
            self.millisec2sec(py_data)
            py_data[:, 2] /= 1.0e7
            py_data[:, 3] /= 1.0e7
            py_data[:, 4] /= 1.0e4

            for i in np.arange(5, 11):
                py_data[:, i] /= 1.0e2
            self.payload = py_data


class pageol(pagecsv24):
    """
    Store and unpack O or L page data.

    - Output power
    @memo とりあえずscalingsはpending
    @todo OK
    @memo format
    [0]:     'O'
    [1]:     internal time
    [2-5]:   time
    [6-8]:   ch0
    [9-11]:  ch1
    [12-14]: ch2
    [15-17]: ch3
    [18-20]: ch0
    [21-23]: ch1
    [24-26]: ch2
    [27-29]: ch3
    [30-31]: reserved
    """

    def __init__(self):
        super().__init__()
        self.payload_format = '<1x1B1I24B1H'
        self.csv_header = ['Internal Time', 'GNSS Time (s)',
                           'Ch1', 'Ch2', 'Ch3', 'Ch4']

    def unpack(self, dat):
        py_data = list(struct.unpack(self.payload_format, dat))
        dat_conv = np.zeros([8])
        for i in range(8):
            dat_conv[i] = self.convert24bit(py_data[2 + 3 * i:5 + 3 * i])
            if(dat_conv[i] > 2 ** 23):
                dat_conv[i] = -2 ** 24 + dat_conv[i]
        out = []
        out.append([py_data[0], py_data[1] - 20] + list(dat_conv[:4]))
        out.append([py_data[0], py_data[1]] + list(dat_conv[4:]))
        return out

    def append(self, dat):
        py_data = self.unpack(dat)
        for i in range(2):
            self.payload.append(py_data[i])

class pageo(pageol):
    """
    Store and unpack O page data.

    - Output power
    @memo とりあえずscalingsはpending
    @todo OK
    @memo format
    [0]:     'O'
    [1]:     internal time
    [2-5]:   time
    [6-8]:   ch0
    [9-11]:  ch1
    [12-14]: ch2
    [15-17]: ch3
    [18-20]: ch0
    [21-23]: ch1
    [24-26]: ch2
    [27-29]: ch3
    [30-31]: reserved
    """

    def __init__(self):
        super().__init__()

class pagel(pageol):
    """
    Store and unpack L page data.

    - Output power
    @memo とりあえずscalingsはpending
    @todo OK
    @memo format
    [0]:     'L'
    [1]:     internal time
    [2-5]:   time
    [6-8]:   ch0
    [9-11]:  ch1
    [12-14]: ch2
    [15-17]: ch3
    [18-20]: ch0
    [21-23]: ch1
    [24-26]: ch2
    [27-29]: ch3
    [30-31]: reserved
    """

    def __init__(self):
        super().__init__()

class pagep(pagecsv):
    """
    Store and unpack P page data.

    - Pressure
    @todo OK
    @memo
    NinjaScan版
    [0]: 'P'
    [1-2]: reserved
    [3]: internal time
    [4-7]: gnss time
    [8-9]: adc0
    ...
    TinyFeather版
    [0]: 'P'
    [1-2]: reserved
    [3]: internal time
    [4-7]: gnss time
    [8-11]: pressure (be)
    [12-15]:temperature
    [16-19]: pressure
    [20-23]:temperature
    [24-27]: pressure
    [28-31]:temperature
    """

    def __init__(self):
        super().__init__()
        self.payload_format = ['<1x2x1B1I', '>6I']
        self.csv_header = ['Internal Time', 'GNSS Time (s)',
                           'Pressure (Pa)', 'Temperature (deg. C)']
        config = configparser.ConfigParser()
        config.read(self.filename_config)
        configP = config['P']
        self.sampling_interval = float(configP['sampling_interval'])
        self.scaling_tmp = float(configP['scaling_tmp'])

    def unpack(self, dat):
        py_data_1 = list(struct.unpack(self.payload_format[0], dat[:8]))
        py_data_2 = list(struct.unpack(self.payload_format[1], dat[8:]))
        out = []
        for i in range(3):
            out.append([py_data_1[0],
                        py_data_1[1] - self.sampling_interval * (2 - i),
                        py_data_2[0 + i * 2],
                        py_data_2[1 + i * 2]])
        return out

    def append(self, dat):
        py_data = self.unpack(dat)
        for i in range(3):
            self.payload.append(py_data[i])

    def raw2phys(self):
        if len(self.payload) > 1:
            py_data = np.array(self.payload, dtype=np.float64)
            self.millisec2sec(py_data)
            py_data[:, 3] *= self.scaling_tmp
            self.payload = py_data


class pages(pagecsv):
    """
    Store and unpack S page data.

    - System supervisor
    @todo OK
    """

    def __init__(self):
        super().__init__()
        self.payload_format = '<1x2x1B1I12H'
        self.csv_header = ['Internal Time', 'GNSS Time (s)',
                           '3.3V (V)', 'Power (V)', '5.0V (V)',
                           'Battery current (mA)',
                           'USB current (mA)'] + ['reserved'] * 7
        config = configparser.ConfigParser()
        config.read(self.filename_config)
        configS = config['S']
        self.scaling_3V3_Vol = float(configS['scaling_3V3_Vol'])
        self.scaling_Pow_Vol = float(configS['scaling_Pow_Vol'])
        self.scaling_5V0_Vol = float(configS['scaling_5V0_Vol'])
        self.scaling_Bat_Cur = float(configS['scaling_Bat_Cur'])
        self.scaling_USB_Cur = float(configS['scaling_USB_Cur'])

    def raw2phys(self):
        if len(self.payload) > 1:
            py_data = np.array(self.payload, dtype=np.float64)
            self.millisec2sec(py_data)
            py_data[:, 2] *= self.scaling_3V3_Vol
            py_data[:, 3] *= self.scaling_Pow_Vol
            py_data[:, 4] *= self.scaling_5V0_Vol
            py_data[:, 5] *= self.scaling_Bat_Cur
            py_data[:, 6] *= self.scaling_USB_Cur
            self.payload = py_data


class paget(pagecsv):
    """
    Store and unpack T page data.

    - ANT+
    @todo OK
    """

    def __init__(self):
        super().__init__()
        self.payload_format = '<1x1B'
        self.payload_format_format = '<1x1B1I8B'  # フォーマットモード
        self.payload_format_dump = '<1B30B'  # ダンプモード
        self.csv_header = ['Mode', 'Internal Time/dat',
                           'GNSS Time (s)/dat'] + ['dat'] * 28

    def raw2phys(self):
        if len(self.payload) > 1:
            for i, pl in enumerate(self.payload):
                if len(pl) == 11:
                    # pl_temp = list(pl)
                    pl[2] *= 1.0e-3
                    self.payload[i] = pl

    def unpack(self, dat):
        py_data = list(struct.unpack(self.payload_format, dat[:2]))
        if py_data[0] == 70:  # 'F'
            out = []
            out.append([70] + list(struct.unpack(self.payload_format_format,
                                                 dat[2:16])))
            out.append([70] + list(struct.unpack(self.payload_format_format,
                                                 dat[18:])))
            return out
        elif py_data[0] == 68:  # 'D'
            return list(struct.unpack(self.payload_format_dump, dat[1:]))

    def append(self, dat):
        py_data = self.unpack(dat)
        if len(py_data) == 2:
            for i in range(2):
                self.payload.append(py_data[i])
        else:
            self.payload.append(py_data)


class pagev(pagecsv):
    """
    Store and unpack V page data.

    - Variable pitch propeller
    Format
    [0]: "V"
    [1-2]: "TX" or "RX"
    [3]: internal time
    [4-7]: gnss time
    [8-9]: lost packet, uint16（受信側で書き込み）
    [10-11]: crcerror, uint16（受信側で書き込み）
    [12-13]: reserved
    [14-15]: offset, int16（送信側で書き込み）
    [16-17]: 目標値adc, uint16（送信側で書き込み）
    [18-19]: 現在位置のAD変換値, uint16（受信側で書き込み）
    [20-21]: モータ電圧, uint16（受信側で書き込み）
    [22-23]: モータ電流, uint16（受信側で書き込み）
    [24-25]: HPA_Navi電圧, uint16（受信側で書き込み）
    [26-27]: reserved
    [28-29]: reserved
    [30-31]: reserved
    @todo OK
    """

    def __init__(self):
        super().__init__()
        # self.payload_rx = [] # ファイルを送受信で分割する場合必要
        self.payload_format = '<1x1H1B1I3H1h8H'
        self.csv_header = ['TX or RX', 'Internal Time', 'GNSS Time (s)',
                           'Lost packet', 'CRC error', 'reserved', 'Offset',
                           'ADC target', 'ADC read',
                           'Battery voltage (Motor)', 'Motor current',
                           'Battery voltage (Control)'] + ['reserved'] * 3
        config = configparser.ConfigParser()
        config.read(self.filename_config)
        configV = config['V']
        self.scaling_bat_motor = float(configV['scaling_bat_motor'])
        self.scaling_cur = float(configV['scaling_cur'])
        self.scaling_bat_control = float(configV['scaling_bat_control'])

    def raw2phys(self):
        if len(self.payload) > 1:
            py_data = np.array(self.payload, dtype=np.float64)
            self.millisec2sec(py_data, 2)
            py_data[:, 9] *= self.scaling_bat_motor
            py_data[:, 10] *= self.scaling_cur
            py_data[:, 11] *= self.scaling_bat_control
            self.payload = py_data
    # ファイルを送受信で分割するコード
    '''
    def raw2phys(self):
        if len(self.payload) > 0:
            py_data = np.array(self.payload, dtype=np.float64)
            self.millisec2sec(py_data)
            self.payload = py_data
        if len(self.payload_rx) > 0:
            py_data = np.array(self.payload_rx, dtype=np.float64)
            self.millisec2sec(py_data)
            self.payload_rx = py_data
    def append(self, dat):
        py_data = self.unpack(dat)
        if py_data[0] == 22612:
            self.payload.append(py_data)
            # print("tx")
        elif py_data[0] == 22610:
            self.payload_rx.append(py_data)
            # print("rx")
        # else:
            # print(py_data[0])
    def save_raw_csv(self, filename):
        if len(self.payload) > 0:
            np.savetxt(filename+"_TX", np.array(self.payload), fmt='%.7f',
                        delimiter = ', ', header=self.csv_header)
        if len(self.payload_rx) > 0:
            np.savetxt(filename+"_RX", np.array(self.payload_rx), fmt='%.7f',
                        delimiter = ', ', header=self.csv_header)
    '''


'''
Page W
- HeartRateMonitor
@memo 今後使う予定なしなので実装しない。
'''
'''
class pagew(pagecsv):
    def __init__(self):
        super().__init__()
        self.payload_format = '<1x2x1B1I24B'
        self.csv_header = 'Internal Time, GNSS Time (s), '
    def raw2phys(self):
        if len(self.payload) > 0:
            py_data = np.array(self.payload, dtype=np.float64)
            self.millisec2sec(py_data)
            self.payload = py_data
'''
