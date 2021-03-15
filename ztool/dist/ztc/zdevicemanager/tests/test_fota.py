import logging
import sys
import unittest
import os
from click.testing import CliRunner

from .context import cli
from .utils import _result_to_json
from .utils import randomString
import os

log = logging.getLogger("ZDM_cli_test")
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)


class FotaTestSuite(unittest.TestCase):
    """Fota test cases."""

    @classmethod
    def setUpClass(cls):
        cls.runner = CliRunner()
        cls.runner.invoke(cli, ['login', "--user", "testzdm@zerynth.com", "--passwd", "Pippo123"])

    def test_fota_prepare(self):
        project_path = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__))), 'data', 'fota_firmware')
        name = "test" + randomString()
        result = self.runner.invoke(cli, ["-J", 'device', "create", name])
        self.assertEqual(result.exit_code, 0)
        rjson = _result_to_json(result)
        self.device_id = rjson['id']
        result = self.runner.invoke(cli, ["-J", 'fota', "prepare", project_path, self.device_id, "test"])
        log.info(result.output)
        self.assertEqual(1, result.exit_code)
        self.assertIn("Fota cannot be prepared", result.output)

