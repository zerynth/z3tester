import logging
import sys
import unittest

from click.testing import CliRunner

from .context import cli
from .utils import _result_to_json
from .utils import randomString

log = logging.getLogger("ZDM_cli_test")
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)


class GatesTestSuite(unittest.TestCase):
    """gates test cases."""

    @classmethod
    def setUpClass(cls):
        cls.runner = CliRunner()
        cls.runner.invoke(cli, ['login', "--user", "testzdm@zerynth.com", "--passwd", "Pippo123"])


    def test_webhook_start(self):
        name = "test" + randomString()
        url = "https://" + randomString() + ".com"
        period = 10

        result = self.runner.invoke(cli, ["-J", 'workspace', 'all'])
        self.assertEqual(result.exit_code, 0)
        rjson = _result_to_json(result)
        wks_id = rjson[0]['id']
        tag = "test"

        result = self.runner.invoke(cli, ["-J", 'gates', 'webhooks', 'start', name, url, str(period), wks_id, '--tag', tag])

        self.assertEqual(result.exit_code, 0)

    def test_webhook_all(self):
        result = self.runner.invoke(cli, ["-J", 'workspace', 'all'])
        self.assertEqual(result.exit_code, 0)
        rjson = _result_to_json(result)
        wks_id = rjson[0]['id']

        result = self.runner.invoke(cli, ['-J', 'gates', 'webhooks', 'all', wks_id])
        self.assertEqual(result.exit_code, 0)

    def test_gate_delete(self):
        result = self.runner.invoke(cli, ['-J', 'workspace', 'all'])
        self.assertEqual(result.exit_code, 0)
        rjson = _result_to_json(result)
        wks_id = rjson[0]['id']

        name = "test" + randomString()
        url = "https://" + randomString() + ".com"
        period = 10
        tag = "test"

        result = self.runner.invoke(cli, ['-J', 'gates', 'webhooks', 'start', name, url, str(period), wks_id, '--tag', tag])
        self.assertEqual(result.exit_code, 0)

        result = self.runner.invoke(cli, ['-J', 'gates', 'webhooks', 'all', wks_id])
        self.assertEqual(result.exit_code, 0)

        rjson = _result_to_json(result)

        wbhk_id = rjson[0]['id']

        result = self.runner.invoke(cli, ['-J', 'gates', 'delete', wbhk_id])
        self.assertEqual(result.exit_code, 0)

    def test_gate_get(self):
        result = self.runner.invoke(cli, ['-J', 'workspace', 'all'])
        self.assertEqual(result.exit_code, 0)
        rjson = _result_to_json(result)
        wks_id = rjson[0]['id']

        name = "test" + randomString()
        url = "https://" + randomString() + ".com"
        period = 10
        tag = "test"

        result = self.runner.invoke(cli, ['-J', 'gates', 'webhooks', 'start', name, url, str(period), wks_id, '--tag', tag])
        self.assertEqual(result.exit_code, 0)
        result = self.runner.invoke(cli, ['-J', 'gates', 'webhooks', 'all', wks_id])
        self.assertEqual(result.exit_code, 0)

        rjson = _result_to_json(result)

        wbhk_id = rjson[0]['id']

        result = self.runner.invoke(cli, ['-J', 'gates', 'get', wbhk_id])
        self.assertEqual(result.exit_code, 0)



    def test_webhook_enable(self):
        result = self.runner.invoke(cli, ['-J', 'workspace', 'all'])
        self.assertEqual(result.exit_code, 0)
        rjson = _result_to_json(result)
        wks_id = rjson[0]['id']

        name = "test" + randomString()
        url = "https://" + randomString() + ".com"
        period = 10
        tag = "test"

        result = self.runner.invoke(cli, ['-J', 'gates', 'webhooks', 'start', name, url, str(period), wks_id, '--tag', tag])
        self.assertEqual(result.exit_code, 0)

        result = self.runner.invoke(cli, ['-J', 'gates', 'webhooks', 'all', wks_id])
        self.assertEqual(result.exit_code, 0)

        rjson = _result_to_json(result)

        wbhk_id = rjson[0]['id']

        result = self.runner.invoke(cli, ['-J', 'gates', 'enable', wbhk_id])
        self.assertEqual(result.exit_code, 0)

    def test_webhook_disable(self):
        result = self.runner.invoke(cli, ['-J', 'workspace', 'all'])
        self.assertEqual(result.exit_code, 0)
        rjson = _result_to_json(result)
        wks_id = rjson[0]['id']

        name = "test" + randomString()
        url = "https://" + randomString() + ".com"
        period = 10
        tag = "test"

        result = self.runner.invoke(cli, ['-J', 'gates', 'webhooks', 'start', name, url, str(period), wks_id, '--tag', tag])
        self.assertEqual(result.exit_code, 0)

        result = self.runner.invoke(cli, ['-J', 'gates', 'webhooks', 'all', wks_id])
        self.assertEqual(result.exit_code, 0)

        rjson = _result_to_json(result)

        wbhk_id = rjson[0]['id']

        result = self.runner.invoke(cli, ['-J', 'gates', 'disable', wbhk_id])
        self.assertEqual(result.exit_code, 0)

    def test_export_gate_create(self):
        result = self.runner.invoke(cli, ['-J', 'workspace', 'all'])
        self.assertEqual(result.exit_code, 0)
        rjson = _result_to_json(result)
        wks_id = rjson[0]['id']

        result = self.runner.invoke(cli, ['-J', 'gates', 'export', 'create', 'test', 'json', 'daily', wks_id, 'testzdm@zerynth.com'])
        self.assertEqual(result.exit_code, 0)

    def test_alarm_gate_create(self):
        result = self.runner.invoke(cli, ['-J', 'workspace', 'all'])
        self.assertEqual(result.exit_code, 0)
        rjson = _result_to_json(result)
        wks_id = rjson[0]['id']

        result = self.runner.invoke(cli, ['-J', 'gates', 'alarm', 'create', 'test', wks_id, '10', 'testzdm@zerynth.com', 'tag1', 'tag2', 'tag3'])
        self.assertEqual(result.exit_code, 0)

    def test_webhook_update(self):
        result = self.runner.invoke(cli, ['-J', 'workspace', 'all'])
        self.assertEqual(result.exit_code, 0)
        rjson = _result_to_json(result)
        wks_id = rjson[0]['id']

        name = "test" + randomString()
        url = "https://" + randomString() + ".com"
        period = 10
        tag = "test"

        result = self.runner.invoke(cli, ['-J', 'gates', 'webhooks', 'start', name, url, str(period), wks_id, '--tag', tag])
        self.assertEqual(result.exit_code, 0)

        result = self.runner.invoke(cli, ['-J', 'gates', 'webhooks', 'all', wks_id])
        self.assertEqual(result.exit_code, 0)

        rjson = _result_to_json(result)

        wbhk_id = rjson[0]['id']

        result = self.runner.invoke(cli, ['-J', 'gates', 'webhooks', 'update', wbhk_id, '--name', 'newname', '--period', '20', '--url', 'newurl'])
        self.assertEqual(result.exit_code, 0)

    def test_export_update(self):
        result = self.runner.invoke(cli, ['-J', 'workspace', 'all'])
        self.assertEqual(result.exit_code, 0)
        rjson = _result_to_json(result)
        wks_id = rjson[0]['id']

        result = self.runner.invoke(cli, ['-J', 'gates', 'export', 'create', 'test', 'json', 'daily', wks_id, 'testzdm@zerynth.com'])
        self.assertEqual(result.exit_code, 0)

        result = self.runner.invoke(cli, ['-J', 'gates', 'export', 'all', wks_id])
        self.assertEqual(result.exit_code, 0)

        rjson = _result_to_json(result)

        exp_id = rjson[0]['id']

        result = self.runner.invoke(cli, ['-J', 'gates', 'export', 'update', exp_id, '--name', 'newname', '--email', 'newemail@zerynth.com'])
        self.assertEqual(result.exit_code, 0)

    def test_alarm_update(self):
        result = self.runner.invoke(cli, ['-J', 'workspace', 'all'])
        self.assertEqual(result.exit_code, 0)
        rjson = _result_to_json(result)
        wks_id = rjson[0]['id']

        result = self.runner.invoke(cli, ['-J', 'gates', 'alarm', 'create', 'test', wks_id, '10', 'testzdm@zerynth.com', 'tag1', 'tag2', 'tag3'])
        self.assertEqual(result.exit_code, 0)

        result = self.runner.invoke(cli, ['-J', 'gates', 'alarm', 'all', wks_id])
        self.assertEqual(result.exit_code, 0)

        rjson = _result_to_json(result)

        alrm_id = rjson[0]['id']

        result = self.runner.invoke(cli, ['-J', 'gates', 'alarm', 'update', alrm_id, '--name', 'newname', '--threshold', '20'])
        self.assertEqual(result.exit_code, 0)
