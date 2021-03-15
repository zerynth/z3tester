import logging
import sys
import unittest

from click.testing import CliRunner
from datetime import datetime, timezone, timedelta
from .context import cli
from .utils import _result_to_json
from .utils import randomString

log = logging.getLogger("ZDM_cli_test")
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)


class ExportsTestSuite(unittest.TestCase):
    """exports test cases."""

    @classmethod
    def setUpClass(cls):
        cls.runner = CliRunner()
        cls.runner.invoke(cli, ['login', "--user", "testzdm@zerynth.com", "--passwd", "Pippo123"])

    def test_export_create(self):
        name = "test" + randomString()
        type = "json"
        local_time = datetime.now(timezone.utc).astimezone() + timedelta(hours=-5)
        start = local_time.isoformat()
        end = datetime.now(timezone.utc).astimezone().isoformat()
        result = self.runner.invoke(cli, ["-J", 'workspace', 'all'])
        self.assertEqual(result.exit_code, 0)
        rjson = _result_to_json(result)
        wks_id = rjson[0]['id']
        tag = "test"

        result = self.runner.invoke(cli, ["-J", 'export', 'create', name, type, wks_id, start, end, '--tag', tag])

        self.assertEqual(result.exit_code, 0)

    def test_export_get(self):
        name = "test" + randomString()
        type = "json"
        local_time = datetime.now(timezone.utc).astimezone() + timedelta(hours=-5)
        start = local_time.isoformat()
        end = datetime.now(timezone.utc).astimezone().isoformat()
        result = self.runner.invoke(cli, ["-J", 'workspace', 'all'])
        self.assertEqual(result.exit_code, 0)
        rjson = _result_to_json(result)
        wks_id = rjson[0]['id']
        tag = "test"

        result = self.runner.invoke(cli, ["-J", 'export', 'create', name, type, wks_id, start, end, '--tag', tag])
        jRes = _result_to_json(result)
        result = self.runner.invoke(cli, ["-J", 'export', 'get', jRes['id']])
        self.assertEqual(result.exit_code, 0)
