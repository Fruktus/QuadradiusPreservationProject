import unittest

from QRServer.cli import QRCmd


class CliTest(unittest.TestCase):
    def test_complete_config_se(self):
        cmd = QRCmd()
        complete = cmd.complete_config('se', 'config  se', 8, 10)
        self.assertEqual(['set'], complete)

    def test_complete_config(self):
        cmd = QRCmd()
        complete = cmd.complete_config('', 'config ', 7, 7)
        self.assertEqual(['get', 'set', 'list'], complete)

    def test_complete_config_x(self):
        cmd = QRCmd()
        complete = cmd.complete_config('x', 'config x', 7, 8)
        self.assertEqual([], complete)
