"""
Sylphide Processor.

Convert Sylphide format binary data into readable csv or ubx files.
"""

# Imports
import struct
import configparser
import numpy as np
import pandas as pd
from typing import Any, List


# Base class for handling pages of data
class Page:
    """
    Store and unpack abstract page data.

    Attributes
    ----------
    payload_format : str
        Description of format used in unpack.
    payload : list
        List of unpacked data.
    """

    def __init__(self) -> None:
        self.payload_format = ""
        self.payload: List[Any] = []

    def unpack(self, dat: bytes) -> Any:
        """
        Unpack raw binary data.

        Parameters
        ----------
        dat : bytes
            Input data to be unpacked.

        Returns
        -------
        Any
            Output data unpacked.
            @memo PageGがバイナリ列を出力するのでここはAny。
        """

        """Placeholder for unpack method to be overridden in derived classes."""
        raise NotImplementedError("Subclasses must implement this method.")

    def append(self, dat: bytes) -> None:
        """
        Append unpacked data to data list.

        Parameters
        ----------
        dat : bytes
            Input data to be unpacked and stored.

        Returns
        -------
        None.
        """
        unpacked_data = self.unpack(dat)
        self.payload.append(unpacked_data)

    @property
    def size(self) -> int:
        return 32


class PageCsv(Page):
    """
    Store and unpack page data.

    Attributes
    ----------
    csv_header : List[str]
        Header added to output csv file.
    filename_config : str
        Filename of configureation file.
    """

    def __init__(self, filename_config="config.ini"):
        super().__init__()
        self.csv_header: List[str] = []
        self.filename_config: str = filename_config

    def save_raw_csv(self, filename: str) -> None:
        """
        Save stored data to csv file.

        Parameters
        ----------
        filename : str
            保存するファイルの名前。

        Returns
        -------
        None.

        """
        # @todo 1を含めない理由は?
        if len(self.payload) > 0:
            df = pd.DataFrame(self.payload)
            header = self.csv_header
            if len(self.csv_header) > 0:
                header[0] = "# " + header[0]
                df.columns = header
            df.to_csv(filename, index=False)

    def unpack(self, dat: bytes) -> List[Any]:
        """
        バイナリデータを解凍します。

        Parameters
        ----------
        dat : bytes
            アンパックするデータ。

        Returns
        -------
        List[Any]
            アンパックされたデータリスト。
        """
        return list(struct.unpack(self.payload_format, dat))

    def millisec2sec(self, dat, column: int = 1) -> None:
        """
        Convert time from millisecond to second.

        Parameters
        ----------
        dat : np.ndarray
            変換するデータが含まれるNumPy配列。
        column : int, optional
            変換するデータの列番号。 The default is 1.

        Returns
        -------
        None.

        """
        dat[:, column] /= 1.0e3

    def raw2phys(self) -> None:
        # @todo 1を含めない理由は?
        if len(self.payload) > 0:
            unpacked_data = np.array(self.payload, dtype=np.float64)
            self.millisec2sec(unpacked_data)
            self.payload = unpacked_data.tolist()


class PageCsv24(PageCsv):
    """
    Store and unpack page data with 24 bit format.

    @memo 24ビットデータの変換は特殊。unpackをオーバーロード
    @todo uintとintを実装
    """

    def convert24bit(self, dat: List[int]) -> int:
        """
        Convert 24 bit data to unsigned int.

        Parameters
        ----------
        dat : List[int]
            24ビットデータを含むバイト列。

        Returns
        -------
        int
            変換された符号なし整数。

        """
        return dat[2] + dat[1] * 2**8 + dat[0] * 2**16


class PageBOL(PageCsv24):
    """
    Store and unpack B or O or L page data.

    - Output power
    @memo とりあえずscalingsはpending
    @todo OK
    @memo format
    [0]:     'B' or 'O' or 'L'
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
    [30-31]: LQI
    """

    def __init__(self):
        super().__init__()
        self.payload_format = "<1x1B1I24B1H"
        self.csv_header = [
            "Internal Time",
            "GNSS Time (s)",
            "Ch1",
            "Ch2",
            "Ch3",
            "Ch4",
            "LQI",
        ]

    def unpack(self, dat: bytes) -> List[List[Any]]:
        unpacked_data = list(struct.unpack(self.payload_format, dat))
        dat_conv = np.zeros(8)
        for i in range(8):
            start_index = 2 + 3 * i
            end_index = 5 + 3 * i
            dat_conv[i] = self.convert24bit(unpacked_data[start_index:end_index])
            if dat_conv[i] > 2**23:
                dat_conv[i] = -(2**24) + dat_conv[i]
        out: List[List[Any]] = []
        out.append(
            [unpacked_data[0], unpacked_data[1] - 20]
            + list(dat_conv[:4])
            + [unpacked_data[26]]
        )
        out.append(
            [unpacked_data[0], unpacked_data[1]]
            + list(dat_conv[4:])
            + [unpacked_data[26]]
        )
        return out

    def append(self, dat: bytes) -> None:
        unpacked_data = self.unpack(dat)
        for i in range(2):
            self.payload.append(unpacked_data[i])


class PageA(PageCsv24):
    """
    Store and unpack A page data.

    - Analog
    @memo OK
    """

    def __init__(self):
        super().__init__()
        self.payload_format: str = "<1x1B1I24B1H"
        self.csv_header: List[str] = [
            "Internal Time",
            "GNSS Time (s)",
            "Acc X (g)",
            "Acc Y (g)",
            "Acc Z (g)",
            "Gyr X (deg./s)",
            "Gyr Y (deg./s)",
            "Gyr Z (deg./s)",
            "Pressure (Pa)",
            "Temperature (deg. C)",
            "IMU Temperature (deg. C)",
        ]
        config = configparser.ConfigParser()
        config.read(self.filename_config)
        configA = config["A"]
        self.scaling_acc: List[float] = [
            float(configA["scaling_acc_x"]),
            float(configA["scaling_acc_y"]),
            float(configA["scaling_acc_z"]),
        ]
        self.offset_acc: List[float] = [
            float(configA["offset_acc_x"]),
            float(configA["offset_acc_y"]),
            float(configA["offset_acc_z"]),
        ]
        self.scaling_gyr: List[float] = [
            float(configA["scaling_gyr_x"]),
            float(configA["scaling_gyr_y"]),
            float(configA["scaling_gyr_z"]),
        ]
        self.offset_gyr: List[float] = [
            float(configA["offset_gyr_x"]),
            float(configA["offset_gyr_y"]),
            float(configA["offset_gyr_z"]),
        ]
        self.scaling_prs: float = float(configA["scaling_prs"])
        self.scaling_tmp_prs: float = float(configA["scaling_tmp_prs"])
        self.offset_tmp_prs: float = float(configA["offset_tmp_prs"])
        self.scaling_tmp_imu: float = float(configA["scaling_tmp_imu"])
        self.offset_tmp_imu: float = float(configA["offset_tmp_imu"])

    def raw2phys(self) -> None:
        if len(self.payload) > 1:
            unpacked_data = np.array(self.payload, dtype=np.float64)
            self.millisec2sec(unpacked_data)
            for i in range(3):
                unpacked_data[:, 2 + i] = (
                    unpacked_data[:, 2 + i] - self.offset_acc[i]
                ) / self.scaling_acc[i]
                unpacked_data[:, 5 + i] = (
                    unpacked_data[:, 5 + i] - self.offset_gyr[i]
                ) / self.scaling_gyr[i]
            unpacked_data[:, 8] = unpacked_data[:, 8] * self.scaling_prs
            unpacked_data[:, 9] = (
                unpacked_data[:, 9] * self.scaling_tmp_prs - self.offset_tmp_prs
            )
            unpacked_data[:, 10] = (
                unpacked_data[:, 10] * self.scaling_tmp_imu - self.offset_tmp_imu
            )
            self.payload = unpacked_data.tolist()

    def unpack(self, dat) -> List[Any]:
        unpacked_data = list(struct.unpack(self.payload_format, dat))
        dat_conv = np.zeros(8)
        for i in range(8):
            dat_conv[i] = self.convert24bit(unpacked_data[2 + 3 * i : 5 + 3 * i])
        return (
            [unpacked_data[0], unpacked_data[1]] + list(dat_conv) + [unpacked_data[26]]
        )


class PageB(PageBOL):
    """
    Store and unpack B page data.

    - 張力
    @memo とりあえずscalingsはpending
    @todo OK
    @memo format
    [0]:     'B'
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
    [30-31]: LQI
    """

    def __init__(self):
        super().__init__()


class PageC:
    """
    コマンド用として定義済み
    """

    pass


class PageF(PageCsv):
    """
    Store and unpack F page data.

    - FPGA
    @memo 12ビットデータの変換は特殊。unpackをオーバーロード
    @todo OK
    """

    def __init__(self):
        super().__init__()
        self.payload_format: str = "1x2x1B1I24B"
        self.csv_header: List[str] = [
            "Internal Time",
            "GNSS Time (s)",
            "In0 (us)",
            "Out0 (us)",
            "In1 (us)",
            "Out1 (us)",
            "In2 (us)",
            "Out2 (us)",
            "In3 (us)",
            "Out3 (us)",
            "In4 (us)",
            "Out4 (us)",
            "In5 (us)",
            "Out5 (us)",
            "In6 (us)",
            "Out6 (us)",
            "In7 (us)",
            "Out7 (us)",
        ]

    def convert2x12bit(self, dat: bytes) -> List[int]:
        """
        Convert 3 bytes data to two 12 bit data.

        Parameters
        ----------
        dat : bytes
            input data.

        Returns
        -------
        List[int, int]
            converted data.

        """
        return [(dat[1] & 0xF0) >> 4 | (dat[0] << 4), (dat[1] & 0x0F) << 8 | dat[2]]

    def unpack(self, dat: bytes) -> List[int]:
        unpacked_data = list(struct.unpack(self.payload_format, dat))
        dat_conv = np.zeros(16)
        for i in range(8):
            start_index = 2 + 3 * i
            end_index = 5 + 3 * i
            dat_conv[i * 2], dat_conv[i * 2 + 1] = self.convert2x12bit(
                unpacked_data[start_index:end_index]
            )
        return [unpacked_data[0], unpacked_data[1]] + list(dat_conv)


class PageG(Page):
    """
    Store and unpack G page data.

    - GNSS
    @memo バイナリをそのまま出力。unpackをオーバーロード
    @todo OK
    """

    def __init__(self):
        super().__init__()

    def save_raw_ubx(self, filename: str) -> None:
        """
        Save raw ubx binary file.

        Parameters
        ----------
        filename : str
            保存するファイルの名前。

        Returns
        -------
        None.

        """
        if len(self.payload) > 0:
            with open(filename, mode="wb") as f:
                for dat in self.payload:
                    f.write(dat)

    def unpack(self, dat: bytes) -> bytes:
        """
        データをアンパックします。この場合、データの先頭1バイトを除いて返します。

        Parameters
        ----------
        dat : bytes
            アンパックするデータ。

        Returns
        -------
        bytes
            アンパックされたデータ。
        """
        return dat[1:]


class PageH(PageCsv):
    """
    Store and unpack H page data.

    - Human powered airplane
    @memo OK
    """

    def __init__(self):
        super().__init__()
        self.payload_format: str = "<1x2x1B1I12H"
        self.csv_header: List[str] = [
            "Internal Time",
            "GNSS Time (s)",
            "Cadence (rpm)",
            "Cadence (rpm)",
            "Airspeed (m/s)",
            "Altitude (m)",
            "ADC0 (deg.)",
            "ADC1 (deg.)",
            "ADC2 (deg.)",
            "ADC3",
            "ADC4",
            "ADC5",
            "ADC6",
            "ADC7",
        ]
        config = configparser.ConfigParser()
        config.read(self.filename_config)
        configH = config["H"]
        self.scaling_cadence: List[float] = [
            float(configH["scaling_cadence0"]),
            float(configH["scaling_cadence1"]),
        ]
        self.scaling_ias: float = float(configH["scaling_ias"])
        self.offset_ias: float = float(configH["offset_ias"])
        self.scaling_alt: float = float(configH["scaling_alt"])
        self.scaling_adc: List[float] = [
            float(configH["scaling_adc0"]),
            float(configH["scaling_adc1"]),
            float(configH["scaling_adc2"]),
            float(configH["scaling_adc3"]),
            float(configH["scaling_adc4"]),
            float(configH["scaling_adc5"]),
            float(configH["scaling_adc6"]),
            float(configH["scaling_adc7"]),
        ]
        self.offset_adc: List[float] = [
            float(configH["offset_adc0"]),
            float(configH["offset_adc1"]),
            float(configH["offset_adc2"]),
            float(configH["offset_adc3"]),
            float(configH["offset_adc4"]),
            float(configH["offset_adc5"]),
            float(configH["offset_adc6"]),
            float(configH["offset_adc7"]),
        ]

    def raw2phys(self) -> None:
        if len(self.payload) > 1:
            unpacked_data = np.array(self.payload, dtype=np.float64)
            self.millisec2sec(unpacked_data)
            for i in range(2):
                unpacked_data[:, 2 + i] = (
                    self.scaling_cadence[i] / unpacked_data[:, 2 + i]
                )
            unpacked_data[:, 4] = (
                unpacked_data[:, 4] * self.scaling_ias + self.offset_ias
            )
            unpacked_data[:, 5] = unpacked_data[:, 5] * self.scaling_alt
            for i in range(8):
                unpacked_data[:, 6 + i] = (
                    unpacked_data[:, 6 + i] * self.scaling_adc[i] - self.offset_adc[i]
                )
            self.payload = unpacked_data.tolist()


class PageL(PageBOL):
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
    [30-31]: LQI
    """

    def __init__(self):
        super().__init__()


class PageM(PageCsv):
    """
    Store and unpack M page data.

    - Magnetometer
    @todo OK
    """

    def __init__(self):
        super().__init__()
        self.payload_format_LE: str = "<1x2x1B1I12h"
        self.payload_format_BE: str = ">1x2x1B1I12h"
        self.csv_header: List[str] = [
            "Internal Time",
            "GNSS Time (s)",
            "Mag X",
            "Mag Y",
            "Mag Z",
        ]
        config = configparser.ConfigParser()
        config.read(self.filename_config)
        configM = config["M"]
        self.sampling_interval: float = float(configM["sampling_interval"])
        self.scaling: np.ndarray = np.array(
            [
                float(configM["scaling_x"]),
                float(configM["scaling_y"]),
                float(configM["scaling_z"]),
            ]
        )
        self.offset: np.ndarray = np.array(
            [
                float(configM["offset_x"]),
                float(configM["offset_y"]),
                float(configM["offset_z"]),
            ]
        )

    def raw2phys(self) -> None:
        """
        ペイロードデータを物理単位に変換します。
        """
        if len(self.payload) > 1:
            unpacked_data: np.ndarray = np.array(self.payload, dtype=np.float64)
            self.millisec2sec(unpacked_data)
            for i in range(3):
                unpacked_data[:, 2 + i] = (
                    unpacked_data[:, 2 + i] * self.scaling[i] - self.offset[i]
                )
            self.payload = unpacked_data.tolist()

    def unpack(self, dat: bytes) -> List[List[float]]:
        """
        バイナリデータを解析し、リスト形式でマグネトメータデータを返します。

        Parameters
        ----------
        dat : bytes
            解析するバイナリデータ。

        Returns
        -------
        List[List[float]]
            解析後のデータリスト。
        """
        unpacked_data_LE = list(struct.unpack(self.payload_format_LE, dat))
        unpacked_data_BE = list(struct.unpack(self.payload_format_BE, dat))
        out: List[List[float]] = []
        for i in range(4):
            out.append(
                [
                    unpacked_data_LE[0],
                    unpacked_data_LE[1] - self.sampling_interval * (3 - i),
                    *unpacked_data_BE[2 + i * 3 : 5 + i * 3],
                ]
            )
        return out

    def append(self, dat):
        """
        アンパックされたデータをペイロードに追加します。
        """
        unpacked_data = self.unpack(dat)
        for i in range(4):
            self.payload.append(unpacked_data[i])


class PageN(PageCsv):
    """
    Store and unpack N page data.

    - Navigation
    @todo OK
    """

    def __init__(self):
        super().__init__()
        self.payload_format: str = "<1x1B2x4i6h"
        self.csv_header: List[str] = [
            "Data Number",
            "GNSS Time (s)",
            "Latitude (deg.)",
            "Longitude (deg.)",
            "Altitude (m)",
            "Velocity N (m/s)",
            "Velocity E (m/s)",
            "Velocity D (m/s)",
            "Yaw (deg.)",
            "Roll (deg.)",
            "Pitch (deg.)",
        ]

    def raw2phys(self) -> None:
        if len(self.payload) > 1:
            unpacked_data = np.array(self.payload, dtype=np.float64)
            self.millisec2sec(unpacked_data)
            unpacked_data[:, 2] /= 1.0e7  # Longitude
            unpacked_data[:, 3] /= 1.0e7  # Latitude
            unpacked_data[:, 4] /= 1.0e4  # Altitude

            for i in np.arange(5, 11):  # Velocity and orientation
                unpacked_data[:, i] /= 1.0e2
            self.payload = unpacked_data.tolist()


class PageO(PageBOL):
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
    [30-31]: LQI
    """

    def __init__(self):
        super().__init__()


class PageP(PageCsv):
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
        self.payload_format: List[str] = ["<1x2x1B1I", ">6I"]
        self.csv_header: List[str] = [
            "Internal Time",
            "GNSS Time (s)",
            "Pressure (Pa)",
            "Temperature (deg. C)",
        ]
        config = configparser.ConfigParser()
        config.read(self.filename_config)
        configP = config["P"]
        self.sampling_interval: float = float(configP["sampling_interval"])
        self.scaling_tmp: float = float(configP["scaling_tmp"])

    def unpack(self, dat: bytes) -> List[List[Any]]:
        unpacked_data_1 = list(struct.unpack(self.payload_format[0], dat[:8]))
        unpacked_data_2 = list(struct.unpack(self.payload_format[1], dat[8:]))
        out: List[List[Any]] = []
        for i in range(3):
            out.append(
                [
                    unpacked_data_1[0],
                    unpacked_data_1[1] - self.sampling_interval * (2 - i),
                    unpacked_data_2[0 + i * 2],
                    unpacked_data_2[1 + i * 2],
                ]
            )
        return out

    def append(self, dat: bytes) -> None:
        unpacked_data = self.unpack(dat)
        for i in range(3):
            self.payload.append(unpacked_data[i])

    def raw2phys(self) -> None:
        if len(self.payload) > 1:
            unpacked_data = np.array(self.payload, dtype=np.float64)
            self.millisec2sec(unpacked_data)
            unpacked_data[:, 3] *= self.scaling_tmp
            self.payload = unpacked_data.tolist()


class PageR(PageCsv):
    """
    Store and unpack R page data.

    - RSC series

    Attributes:
        payload_format (str): データパケットのフォーマットを指定する文字列。
        csv_header (List[str]): CSVファイルのヘッダーリスト。
        sampling_interval (float): サンプリング間隔。
        scaling_prs (float): 圧力データのスケーリング係数。
        scaling_tmp (float): 温度データのスケーリング係数。

    @todo OK
    @memo
    ...
    [00]:    'R'
    [01-02]: Reserved
    [03]:    Internal time
    [04-07]: GNSS time
    [08-09]: Pressure 1 (Signed, little endian)
    [10-11]: Pressure 2 (Signed, little endian)
    [12-13]: Pressure 3 (Signed, little endian)
    [14-15]: Temperature 1 (Signed, little endian)
    [16-17]: Temperature 2 (Signed, little endian)
    [18-19]: Temperature 3 (Signed, little endian)
    [20-21]: Pressure 1 (Signed, little endian)
    [22-23]: Pressure 2 (Signed, little endian)
    [24-25]: Pressure 3 (Signed, little endian)
    [26-27]: Temperature 1 (Signed, little endian)
    [28-29]: Temperature 2 (Signed, little endian)
    [30-31]: Temperature 3 (Signed, little endian)
    """

    def __init__(self):
        super().__init__()
        self.payload_format: str = ["<1x2x1B1I", "<12h"]
        self.csv_header: List[str] = [
            "Internal Time",
            "GNSS Time (s)",
            "Pressure 1 (inH2O)",
            "Pressure 2 (inH2O)",
            "Pressure 3 (inH2O)",
            "Temperature 1 (deg. C)",
            "Temperature 2 (deg. C)",
            "Temperature 3 (deg. C)",
        ]
        config = configparser.ConfigParser()
        config.read(self.filename_config)
        configR = config["R"]
        self.sampling_interval: float = float(configR["sampling_interval"])
        self.scaling_prs: float = float(configR["scaling_prs"])
        self.scaling_tmp: float = float(configR["scaling_tmp"])

    def unpack(self, dat: bytes) -> List[List[Any]]:
        unpacked_data_1 = list(struct.unpack(self.payload_format[0], dat[:8]))
        unpacked_data_2 = list(struct.unpack(self.payload_format[1], dat[8:]))
        out: List[List[Any]] = []
        for i in range(2):
            out.append(
                [
                    unpacked_data_1[0],
                    unpacked_data_1[1] - self.sampling_interval * (2 - i),
                    *unpacked_data_2[0 + i * 6 : 6 + i * 6],
                ]
            )
        return out

    def append(self, dat: bytes) -> None:
        """
        アンパックしたデータをペイロードに追加します。
        """
        unpacked_data = self.unpack(dat)
        for i in range(2):
            self.payload.append(unpacked_data[i])

    def raw2phys(self) -> None:
        """
        ペイロードデータを物理単位に変換します。
        """
        if len(self.payload) > 1:
            unpacked_data = np.array(self.payload, dtype=np.float64)
            self.millisec2sec(unpacked_data)
            unpacked_data[:, 2:5] *= self.scaling_prs
            unpacked_data[:, 5:] *= self.scaling_tmp
            self.payload = unpacked_data.tolist()


class PageS(PageCsv):
    """
    Store and unpack S page data.

    - System supervisor

    Attributes:
        payload_format (str): Format string for struct unpacking.
        csv_header (List[str]): Headers for the CSV output.
        scaling factors (float): Scaling factors for voltage and current measurements.

    @todo OK
    """

    def __init__(self):
        super().__init__()
        self.payload_format: str = "<1x2x1B1I12H"
        self.csv_header: List[str] = [
            "Internal Time",
            "GNSS Time (s)",
            "3.3V (V)",
            "Power (V)",
            "5.0V (V)",
            "Battery current (mA)",
            "USB current (mA)",
        ] + ["reserved"] * 7
        config = configparser.ConfigParser()
        config.read(self.filename_config)
        configS = config["S"]
        self.scaling_3V3_Vol: float = float(configS["scaling_3V3_Vol"])
        self.scaling_Pow_Vol: float = float(configS["scaling_Pow_Vol"])
        self.scaling_5V0_Vol: float = float(configS["scaling_5V0_Vol"])
        self.scaling_Bat_Cur: float = float(configS["scaling_Bat_Cur"])
        self.scaling_USB_Cur: float = float(configS["scaling_USB_Cur"])

    def raw2phys(self) -> None:
        if len(self.payload) > 1:
            unpacked_data = np.array(self.payload, dtype=np.float64)
            self.millisec2sec(unpacked_data)
            unpacked_data[:, 2] *= self.scaling_3V3_Vol
            unpacked_data[:, 3] *= self.scaling_Pow_Vol
            unpacked_data[:, 4] *= self.scaling_5V0_Vol
            unpacked_data[:, 5] *= self.scaling_Bat_Cur
            unpacked_data[:, 6] *= self.scaling_USB_Cur
            self.payload = unpacked_data.tolist()


class PageT(PageCsv):
    """
    Store and unpack T page data.

    - ANT+

    Attributes:
        payload_format (str): Basic unpack format string.
        payload_format_format (str): Unpack format string for formatted data.
        payload_format_dump (str): Unpack format string for dump mode.
        csv_header (List[str]): Headers for the CSV output.

    @todo OK
    """

    def __init__(self):
        super().__init__()
        self.payload_format: str = "<1x1B"
        self.payload_format_format: str = "<1x1B1I8B"  # フォーマットモード
        # self.payload_format_dump:str = '<1B30B'  # ダンプモード
        self.payload_format_dump: str = "<30B"  # ダンプモード
        self.csv_header: List[str] = [
            "Mode",
            "Internal Time/dat",
            "GNSS Time (s)/dat",
        ] + ["dat"] * 8

    def raw2phys(self) -> None:
        """
        Convert the raw data in the payload to physical units.
        """
        if len(self.payload) > 1:
            for i, pl in enumerate(self.payload):
                if len(pl) == 11:
                    # pl_temp = list(pl)
                    pl[2] *= 1.0e-3
                    self.payload[i] = pl

    def unpack(self, dat: bytes):
        unpacked_data = list(struct.unpack(self.payload_format, dat[:2]))
        if unpacked_data[0] == 70:  # 'F'
            out = []
            out.append(
                [70] + list(struct.unpack(self.payload_format_format, dat[2:16]))
            )
            out.append([70] + list(struct.unpack(self.payload_format_format, dat[18:])))
            return out
        elif unpacked_data[0] == 68:  # 'D'
            # print(["#"] + list(struct.unpack(self.payload_format_dump, dat[1:])))
            return ["# 68"] + list(struct.unpack(self.payload_format_dump, dat[2:]))
        return None

    def append(self, dat: bytes) -> None:
        """
        Append unpacked data to the payload if it's valid.

        Args:
            dat (bytes): The data to be unpacked and possibly appended.
        """
        unpacked_data = self.unpack(dat)
        if unpacked_data != None:
            if len(unpacked_data) == 2:
                for i in range(2):
                    self.payload.append(unpacked_data[i])
            else:
                self.payload.append(unpacked_data)


class PageU(PageCsv):
    """
    Store and unpack U page data. "U" stands for "mu", friction coefficient.

    - Brake by wire

    Attributes:
        payload_format (str): データアンパック用のフォーマット文字列。
        csv_header (List[str]): CSV出力用のヘッダー。
        scaling_* (float): 各種センサーのスケーリング係数。
        offset_* (float): 電圧計算のためのオフセット値。

    Format
    [0]: "U"
    [1-2]: Reserved
    [3]: internal time, uint8_t
    [4-7]: gnss time, uint32_t
    [8-9]: Sensor input 0, Brake I/F input?, uint16_t
    [10-11]: Sensor input 1, Unused, uint16_t
    [12-13]: Sensor input 2, Wheel, uint16_t
    [14-15]: Servo output 0, uint16_t
    [16-17]: Servo output 1, uint16_t
    [18-19]: Sensor current 0, int16_t
    [20-21]: Sensor current 1, int16_t
    [22-23]: Sensor current 2, int16_t
    [24-25]: Servo current 0, int16_t
    [26-27]: Servo current 1, int16_t
    [28]: Voltage 0, V_BUS, 0 - 20.480 V, 5.0 V nominal, V_BUS =  5.0 * ADCout [mV], (ADCout - 1000) / 1 count, int8_t, 4360 - 5640 mV,  5 mV step
    [29]: Voltage 1, V_BAT, 0 - 10.240 V, 7.4 V nominal, V_BAT =  2.5 * ADCout [mV], (ADCout - 2880) / 4 count, int8_t, 5920 - 8480 mV, 10 mV step
    [30]: Voltage 2, V_CAN, 0 -  4.096 V, 3.3 V nominal, V_CAN =  1.0 * ADCout [mV], (ADCout - 3300) / 1 count, int8_t, 3172 - 3428 mV,  1 mV step
    [31]: Voltage 3, V_SYS, 0 -  4.096 V, 3.3 V nominal, V_SYS =  1.0 * ADCout [mV], (ADCout - 3300) / 1 count, int8_t, 3172 - 3428 mV,  1 mV step
    """

    def __init__(self):
        super().__init__()
        self.payload_format: str = "<1x2x1B1I5H5h4b"
        self.csv_header: List[str] = [
            "Internal Time",
            "GNSS Time (s)",
            "Sensor input 0",
            "Sensor input 1",
            "Sensor input 2",
            "Servo output 0",
            "Servo output 1",
            "Sensor current 0",
            "Sensor current 1",
            "Sensor current 2",
            "Servo current 0",
            "Servo current 1",
            "Voltage 0",
            "Voltage 1",
            "Voltage 2",
            "Voltage 3",
        ]
        config = configparser.ConfigParser()
        config.read(self.filename_config)
        configU = config["U"]
        self.scaling_sensor_current_0: float = float(
            configU["scaling_sensor_current_0"]
        )
        self.scaling_sensor_current_1: float = float(
            configU["scaling_sensor_current_1"]
        )
        self.scaling_sensor_current_2: float = float(
            configU["scaling_sensor_current_2"]
        )
        self.scaling_servo_current_0: float = float(configU["scaling_servo_current_0"])
        self.scaling_servo_current_1: float = float(configU["scaling_servo_current_1"])
        self.scaling_voltage_0: float = float(configU["scaling_voltage_0"])
        self.scaling_voltage_1: float = float(configU["scaling_voltage_1"])
        self.scaling_voltage_2: float = float(configU["scaling_voltage_2"])
        self.scaling_voltage_3: float = float(configU["scaling_voltage_3"])
        self.offset_voltage_0: float = float(configU["offset_voltage_0"])
        self.offset_voltage_1: float = float(configU["offset_voltage_1"])
        self.offset_voltage_2: float = float(configU["offset_voltage_2"])
        self.offset_voltage_3: float = float(configU["offset_voltage_3"])

    def raw2phys(self):
        """
        ペイロードデータを物理単位に変換します。
        """
        if len(self.payload) > 1:
            unpacked_data = np.array(self.payload, dtype=np.float64)
            self.millisec2sec(unpacked_data, 2)
            unpacked_data[:, 2] *= self.scaling_sensor_current_0
            unpacked_data[:, 3] *= self.scaling_sensor_current_1
            unpacked_data[:, 4] *= self.scaling_sensor_current_2
            unpacked_data[:, 5] *= self.scaling_servo_current_0
            unpacked_data[:, 6] *= self.scaling_servo_current_1
            unpacked_data[:, 12] = (
                unpacked_data[:, 12] - self.offset_voltage_0
            ) * self.scaling_voltage_0
            unpacked_data[:, 13] = (
                unpacked_data[:, 13] - self.offset_voltage_1
            ) * self.scaling_voltage_1
            unpacked_data[:, 14] = (
                unpacked_data[:, 14] - self.offset_voltage_2
            ) * self.scaling_voltage_2
            unpacked_data[:, 15] = (
                unpacked_data[:, 15] - self.offset_voltage_3
            ) * self.scaling_voltage_3
            self.payload = unpacked_data.tolist()


class PageV(PageCsv):
    """
    Store and unpack V page data.

    - Variable pitch propeller

    Attributes:
        payload_format (str): ペイロードのフォーマット指定。
        csv_header (List[str]): CSVヘッダー。
        scaling_bat_motor (float): モータ用バッテリのスケーリング係数。
        scaling_cur (float): 電流のスケーリング係数。
        scaling_bat_control (float): 制御用バッテリのスケーリング係数。

    Format
    [0]: "V"
    [1-2]: "TX" or "RX"
    [3]: internal time
    [4-7]: gnss time
    [8-9]: lost packet, uint16（受信側で書き込み）
    [10-11]: crc error, uint16（受信側で書き込み）
    [12-13]: LQI (Link Quality Indicator), uint16（無線モジュールで書き込み）
    [14-15]: offset, int16（送信側で書き込み）
    [16-17]: 目標値adc, uint16（送信側で書き込み）
    [18-19]: 現在位置のAD変換値, uint16（受信側で書き込み）
    [20-21]: モータ電圧, uint16（受信側で書き込み）
    [22-23]: モータ電流, uint16（受信側で書き込み）
    [24-25]: HPA_Navi電圧, uint16（受信側で書き込み）
    [26]: プロペラピッチ遷移風速, 低速側, uint8（x 0.1 m/s）
    [27]: プロペラピッチ遷移風速, 高速側, uint8（x 0.1 m/s）
    [28-29]: 低速側プロペラピッチ, int16（x 0.001 deg.）
    [30-31]: 高速側プロペラピッチ, int16（x 0.001 deg.）
    @todo OK
    """

    def __init__(self):
        super().__init__()
        # self.payload_rx = [] # ファイルを送受信で分割する場合必要
        self.payload_format: str = "<1x1H1B1I3H1h8H"
        self.csv_header: List[str] = [
            "TX or RX",
            "Internal Time",
            "GNSS Time (s)",
            "Lost packet",
            "CRC error",
            "LQI",
            "Offset",
            "ADC target",
            "ADC read",
            "Battery voltage (Motor)",
            "Motor current",
            "Battery voltage (Control)",
        ] + ["reserved"] * 3
        config = configparser.ConfigParser()
        config.read(self.filename_config)
        configV = config["V"]
        self.scaling_bat_motor: float = float(configV["scaling_bat_motor"])
        self.scaling_cur: float = float(configV["scaling_cur"])
        self.scaling_bat_control: float = float(configV["scaling_bat_control"])

    def raw2phys(self) -> None:
        """
        ペイロードデータを物理単位に変換します。
        """
        if len(self.payload) > 1:
            unpacked_data = np.array(self.payload, dtype=np.float64)
            self.millisec2sec(unpacked_data, 2)
            unpacked_data[:, 9] *= self.scaling_bat_motor
            unpacked_data[:, 10] *= self.scaling_cur
            unpacked_data[:, 11] *= self.scaling_bat_control
            self.payload = unpacked_data.tolist()

    # ファイルを送受信で分割するコード
    """
    def raw2phys(self):
        if len(self.payload) > 0:
            unpacked_data = np.array(self.payload, dtype=np.float64)
            self.millisec2sec(unpacked_data)
            self.payload = unpacked_data
        if len(self.payload_rx) > 0:
            unpacked_data = np.array(self.payload_rx, dtype=np.float64)
            self.millisec2sec(unpacked_data)
            self.payload_rx = unpacked_data
    def append(self, dat):
        unpacked_data = self.unpack(dat)
        if unpacked_data[0] == 22612:
            self.payload.append(unpacked_data)
            # print("tx")
        elif unpacked_data[0] == 22610:
            self.payload_rx.append(unpacked_data)
            # print("rx")
        # else:
            # print(unpacked_data[0])
    def save_raw_csv(self, filename):
        if len(self.payload) > 0:
            np.savetxt(filename+"_TX", np.array(self.payload), fmt='%.7f',
                        delimiter = ', ', header=self.csv_header)
        if len(self.payload_rx) > 0:
            np.savetxt(filename+"_RX", np.array(self.payload_rx), fmt='%.7f',
                        delimiter = ', ', header=self.csv_header)
    """


class PageW(PageCsv):
    """
    Page W
    - HeartRateMonitor
    @memo 今後使う予定なしなので実装しない。
    """

    pass
