import logging
import sys
import unittest

from click.testing import CliRunner

from .context import cli
from .utils import _result_to_json
from .utils import randomString

log = logging.getLogger("ZDM_cli_test")
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)


class WorkspaceTestSuite(unittest.TestCase):
    """Workspace test cases."""

    @classmethod
    def setUpClass(cls):
        cls.runner = CliRunner()
        cls.runner.invoke(cli, ['login', "--user", "testzdm@zerynth.com", "--passwd", "Pippo123"])

    def test_workspace_all(self):
        result = self.runner.invoke(cli, ["-J", 'workspace', "all"])
        self.assertEqual(0, result.exit_code)
        self.assertIn("default", result.output)

    def test_workspace_get(self):
        result = self.runner.invoke(cli, ["-J", 'workspace', "all"])
        self.assertEqual(result.exit_code, 0)
        rjson = _result_to_json(result)
        self.assertGreater(len(rjson), 0)
        wks_id = rjson[0]['id']
        result = self.runner.invoke(cli, ["-J", 'workspace', "get", wks_id])
        self.assertIn(wks_id, result.output)

    def test_workspace_create(self):
        result = self.runner.invoke(cli, ["-J", 'workspace', "all"])
        self.assertEqual(result.exit_code, 0)
        rjson = _result_to_json(result)
        self.assertGreater(len(rjson), 0)
        name = "test" + randomString()
        result = self.runner.invoke(cli, ["-J", 'workspace', "create", name])
        self.assertIn(name, result.output)

    def test_workspace_tags(self):
        name = "test" + randomString()
        result = self.runner.invoke(cli, ["-J", 'workspace', "create", name])
        self.assertIn(name, result.output)
        jres = _result_to_json(result)
        result = self.runner.invoke(cli, ["-J", 'workspace', "tags", jres['id']])
        self.assertEqual(result.exit_code, 0)
        rjson = _result_to_json(result)
        self.assertEqual(len(rjson), 0)

    def test_workspace_data(self):
        name = "test" + randomString()
        result = self.runner.invoke(cli, ["-J", 'workspace', "create", name])
        self.assertIn(name, result.output)
        jres = _result_to_json(result)
        result = self.runner.invoke(cli, ["-J", 'workspace', "data", jres['id'], "test"])
        self.assertEqual(result.exit_code, 0)
        rjson = _result_to_json(result)
        self.assertEqual(len(rjson), 0)
