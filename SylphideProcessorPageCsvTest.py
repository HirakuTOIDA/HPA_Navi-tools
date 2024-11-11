import unittest
from unittest.mock import patch, mock_open
import numpy as np
from SylphideProcessor import *


class TestPageCsv(unittest.TestCase):
    def setUp(self):
        self.page = PageCsv()
    #     self.page.csv_header = header_list
    #     self.page.payload = [[123456, 1], [123457, 2]]
    #     self.page.payload_format = "ii"

    def test_constructor(self):
        self.assertEqual(self.page.filename_config, "config.ini")
        self.assertEqual(self.page.csv_header, [])

    @patch("pandas.DataFrame.to_csv")
    def test_save_raw_csv(self, mock_to_csv):
        self.page.payload_format = "ii"
        data = b"\x01\x00\x00\x00\x02\x00\x00\x00"
        self.page.append(data)
        self.page.append(data)
        filename = "test.csv"
        self.page.save_raw_csv(filename)
        # Check if the DataFrame.to_csv was called correctly
        mock_to_csv.assert_called_once()
        # Check the first argument of the call (the filename)
        args, _ = mock_to_csv.call_args
        self.assertEqual(args[0], filename)

    def test_unpack(self):
        self.page.payload_format = "ii"
        data = b"\x01\x00\x00\x00\x02\x00\x00\x00"
        expected = [1, 2]
        result = self.page.unpack(data)
        self.assertEqual(result, expected)

    def test_millisec2sec(self):
        dat = np.array([[1000.0, 1500.0]])
        self.page.millisec2sec(dat)
        np.testing.assert_array_almost_equal(dat, [[1000.0, 1.5]])

    def test_raw2phys(self):
        self.page.payload_format = "ii"
        data = b"\x01\x00\x00\x00\x02\x00\x00\x00"
        self.page.append(data)
        self.page.append(data)
        self.page.raw2phys()
        expected = [[1.0, 2.0e-3], [1.0, 2.0e-3]]
        self.assertEqual(self.page.payload, expected)


if __name__ == "__main__":
    unittest.main()
