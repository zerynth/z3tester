import logging
import sys
import unittest

from click.testing import CliRunner

from .context import cli
from .utils import _result_to_json
from .utils import randomString

log = logging.getLogger("ZDM_cli_test")
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)


class FleetTestSuite(unittest.TestCase):
    """Fleet test cases."""

    @classmethod
    def setUpClass(cls):
        cls.runner = CliRunner()
        cls.runner.invoke(cli, ['login', "--user", "testzdm@zerynth.com", "--passwd", "Pippo123"])


    def test_fleet_all(self):
            result = self.runner.invoke(cli, ["-J", 'fleet', "all"])
            self.assertEqual(0, result.exit_code)
            self.assertIn("default", result.output)

    def test_fleet_get(self):
        result = self.runner.invoke(cli, ["-J", 'fleet', "all"])
        self.assertEqual(result.exit_code, 0)
        rjson = _result_to_json(result)
        self.assertGreater(len(rjson), 0)
        fleet_id = rjson[0]['id']
        result = self.runner.invoke(cli, ["-J", 'fleet', "get", fleet_id])
        self.assertIn(fleet_id, result.output)

    def test_fleet_create(self):
        result = self.runner.invoke(cli, ["-J", 'workspace', "all"])
        self.assertEqual(result.exit_code, 0)
        rjson = _result_to_json(result)
        self.assertGreater(len(rjson), 0)
        name = "test" + randomString()
        result = self.runner.invoke(cli, ["-J", 'fleet', "create", name , rjson[0]['id'] ])
        self.assertIn(name, result.output)
