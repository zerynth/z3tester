import logging
import sys
import unittest

from click.testing import CliRunner

from .context import cli
from .utils import _result_to_json
from .utils import randomString

log = logging.getLogger("ZDM_cli_test")
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)


class DeviceTestSuite(unittest.TestCase):
    """device test cases."""

    @classmethod
    def setUpClass(cls):
        cls.runner = CliRunner()
        cls.runner.invoke(cli, ['login', "--user", "testzdm@zerynth.com", "--passwd", "Pippo123"])

    def test_device_all(self):
        result = self.runner.invoke(cli, ["-J", 'device', "all"])
        self.assertEqual(0, result.exit_code)
        self.assertIn("id", result.output)

    def test_device_get(self):
        result = self.runner.invoke(cli, ["-J", 'device', "all"])
        self.assertEqual(result.exit_code, 0)
        rjson = _result_to_json(result)
        self.assertGreater(len(rjson), 0)
        device_id = rjson[0]['id']
        result = self.runner.invoke(cli, ["-J", 'device', "get", device_id])
        self.assertIn(device_id, result.output)

    def test_device_create(self):
        name = "test" + randomString()
        result = self.runner.invoke(cli, ["-J", 'device', "create", name])
        self.assertEqual(result.exit_code, 0)
        rjson = _result_to_json(result)
        result = self.runner.invoke(cli, ["-J", 'device', "get", rjson['id']])
        self.assertEqual(result.exit_code, 0)
        self.assertIn(name, result.output)

    def test_device_update(self):
        name = "test" + randomString()
        result = self.runner.invoke(cli, ["-J", 'device', "create", name])
        self.assertEqual(result.exit_code, 0)
        rjson = _result_to_json(result)
        device_id = (rjson['id'])
        newname = "test" + randomString()
        upd_result = self.runner.invoke(cli, ["-J", 'device', "update", device_id, "--name", newname])
        self.assertEqual(upd_result.exit_code, 0)

    def test_device_key_create(self):
        name = "test" + randomString()
        result = self.runner.invoke(cli, ["-J", 'device', "create", name])
        self.assertEqual(result.exit_code, 0)
        rjson = _result_to_json(result)
        device_id = (rjson['id'])
        key_name = "key" + randomString()
        result = self.runner.invoke(cli, ["-J", 'device', 'key', 'create', device_id, key_name])
        self.assertEqual(result.exit_code, 0)

    def test_device_key_generate(self):
        name = "test" + randomString()
        result = self.runner.invoke(cli, ["-J", 'device', 'create', name])
        self.assertEqual(result.exit_code, 0)
        rjson = _result_to_json(result)
        device_id = rjson['id']
        key_name = "key" + randomString()
        result = self.runner.invoke(cli, ["-J", 'device', 'key', 'create', device_id, key_name])
        self.assertEqual(result.exit_code, 0)
        rjson = _result_to_json(result)
        key_id = rjson['id']
        result = self.runner.invoke(cli, ["-J", 'device', 'key', 'generate', device_id, str(key_id)])
        self.assertEqual(result.exit_code, 0)

    def test_device_key_all(self):
        name = "test" + randomString()
        result = self.runner.invoke(cli, ["-J", 'device', "create", name])
        self.assertEqual(result.exit_code, 0)
        rjson = _result_to_json(result)
        device_id = rjson['id']
        key_name = "key" + randomString()
        result = self.runner.invoke(cli, ["-J", 'device', 'key', 'create', device_id, key_name])
        self.assertEqual(result.exit_code, 0)
        rjson = _result_to_json(result)
        key1_id = (rjson['id'])
        key_name = "key" + randomString()
        result = self.runner.invoke(cli, ["-J", 'device', 'key', 'create', device_id, key_name])
        self.assertEqual(result.exit_code, 0)
        rjson = _result_to_json(result)
        key2_id = (rjson['id'])
        key_name = "key" + randomString()
        result = self.runner.invoke(cli, ["-J", 'device', 'key', 'create', device_id, key_name])
        self.assertEqual(result.exit_code, 0)
        rjson = _result_to_json(result)
        key3_id = rjson['id']
        result = self.runner.invoke(cli, ["-J", 'device', 'key', 'all', device_id])
        self.assertEqual(result.exit_code, 0)
        self.assertIn(str(key1_id), result.output)
        self.assertIn(str(key2_id), result.output)
        self.assertIn(str(key3_id), result.output)


    def test_device_provision(self):
        name = "test" + randomString()
        result = self.runner.invoke(cli, ["-J", 'device', "create", name])
        self.assertEqual(result.exit_code, 0)
        rjson = _result_to_json(result)
        device_id = rjson['id']
        result = self.runner.invoke(cli, ["-J", 'device', "credentials", device_id])
        print(result)
        self.assertEqual(0, result.exit_code)
        self.assertIn("id", result.output)
        self.assertIn("devinfo", result.output)
        self.assertIn("endpoint", result.output)
        self.assertIn("mode", result.output["devinfo"])
        self.assertEqual("cloud_token", result.output["devinfo"]["mode"])
        self.assertIn("mode", result.output["endpoint"])
        self.assertEqual("secure", result.output["endpoint"]["mode"])

