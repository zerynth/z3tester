import logging
import sys
import unittest

from click.testing import CliRunner

from .context import cli
from .utils import _result_to_json
from .utils import randomString

log = logging.getLogger("ZDM_cli_test")
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)


class JobTestSuite(unittest.TestCase):
    """job test cases."""

    @classmethod
    def setUpClass(cls):
        cls.runner = CliRunner()
        cls.runner.invoke(cli, ['login', "--user", "testzdm@zerynth.com", "--passwd", "Pippo123"])


    def test_job_schedule(self):
        name = "test" + randomString()
        result = self.runner.invoke(cli, ["-J", 'device', "create", name])
        self.assertEqual(result.exit_code, 0)
        rjson = _result_to_json(result)
        device_id = (rjson['id'])
        job_name = "job" + randomString()
        result = self.runner.invoke(cli, ["-J", 'job', "schedule", job_name, device_id])
        self.assertEqual(result.exit_code, 0)

    def test_job_check(self):
        name = "test" + randomString()
        result = self.runner.invoke(cli, ["-J", 'device', "create", name])
        self.assertEqual(result.exit_code, 0)
        rjson = _result_to_json(result)
        device_id = (rjson['id'])
        job_name = "job" + randomString()
        result = self.runner.invoke(cli, ["-J", 'job', "schedule", job_name, device_id])
        self.assertEqual(result.exit_code, 0)

        result = self.runner.invoke(cli, ["-J", 'job', "check", job_name, device_id])
        self.assertEqual(result.exit_code, 0)

if __name__ == '__main__':
    unittest.main()
