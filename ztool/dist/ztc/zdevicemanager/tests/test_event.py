import logging
import sys
import unittest

from click.testing import CliRunner

from .context import cli
from .utils import _result_to_json
from .utils import randomString

log = logging.getLogger("ZDM_cli_test")
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)


class EventTestSuite(unittest.TestCase):
    """gates test cases."""

    @classmethod
    def setUpClass(cls):
        cls.runner = CliRunner()
        cls.runner.invoke(cli, ['login', "--user", "testzdm@zerynth.com", "--passwd", "Pippo123"])

    def test_get_events(self):
        result = self.runner.invoke(cli, ["-J", 'workspace', 'all'])
        self.assertEqual(result.exit_code, 0)
        rjson = _result_to_json(result)
        wks_id = rjson[0]['id']

        result = self.runner.invoke(cli, ["-J", 'event', "list", wks_id])
        self.assertEqual(0, result.exit_code)
