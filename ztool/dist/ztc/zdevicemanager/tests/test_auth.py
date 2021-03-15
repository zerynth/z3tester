import logging
import sys
import unittest

from click.testing import CliRunner

from .context import cli

log = logging.getLogger("ZDM_cli_test")
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)


class AuthTestSuite(unittest.TestCase):
    """Auth test cases."""

    @classmethod
    def setUpClass(cls):
        cls.runner = CliRunner()

    def test_login(self):
        token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJqdGkiOiIxSkItdXZ0a1FCbWR3WjVzMDZrbUtBIiwibHRwIjpudWxsLCJpYXQiOjE1ODQ4MzAwOTUsInVpZCI6Ik9zYkRxNWp0U3dtbVBpNUk1Yk55WXciLCJleHAiOjE1ODc0MjIwOTUsImlzcyI6InplcnludGgiLCJvcmciOiIifQ.Zj61VE99FqSveYXEPx9FswHD2DhWxIYvGJEZbaY0n24"
        result = self.runner.invoke(cli, ['login'], input=token+"\n")
        log.info(result.output)
        assert result.exit_code == 0

    def test_logout(self):
        result = self.runner.invoke(cli, ['logout'])
        assert result.exit_code == 0
        result = self.runner.invoke(cli, ['workspace', "all"])
        assert "No authorization token! Please run 'zdm login' to get one" in result.output