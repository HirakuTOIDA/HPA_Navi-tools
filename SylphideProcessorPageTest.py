import unittest
from SylphideProcessor import *

class TestPage(unittest.TestCase):
    def test_constructor(self):
        page = Page()
        self.assertEqual(page.payload_format, "")
        self.assertEqual(page.payload, [])

    def test_not_implemented_error(self):
        page = Page()
        with self.assertRaises(NotImplementedError):
            page.unpack(b"dummy data")

    def test_page_size(self):
        page = Page()
        self.assertEqual(page.size, 32)

class MockPage(Page):
    def unpack(self, dat: bytes):
        return dat.decode()

class TestMockPage(unittest.TestCase):
    def test_unpack(self):
        page = MockPage()
        self.assertEqual(page.unpack(b"hello"), "hello")

    def test_append(self):
        page = MockPage()
        page.append(b"hello")
        self.assertIn("hello", page.payload)

if __name__ == "__main__":
    unittest.main()
