# tests/runner.py
import unittest
import logging

urllib3_logger = logging.getLogger('urllib3')
urllib3_logger.setLevel(logging.CRITICAL)

# import your test modules
from .test_auth import AuthTestSuite
from .test_device import DeviceTestSuite
from .test_event import EventTestSuite
from .test_fleet import FleetTestSuite
from .test_fota import FotaTestSuite
from .test_gates import GatesTestSuite
from .test_job import JobTestSuite
from .test_export import ExportsTestSuite
from .test_workspace import WorkspaceTestSuite

# initialize the test suite
loader = unittest.TestLoader()
suite  = unittest.TestSuite()

# add tests to the test suite
suite.addTests(loader.loadTestsFromTestCase(AuthTestSuite))
suite.addTests(loader.loadTestsFromTestCase(DeviceTestSuite))
suite.addTests(loader.loadTestsFromTestCase(FleetTestSuite))
suite.addTests(loader.loadTestsFromTestCase(WorkspaceTestSuite))
suite.addTests(loader.loadTestsFromTestCase(EventTestSuite))
suite.addTests(loader.loadTestsFromTestCase(FotaTestSuite))
suite.addTests(loader.loadTestsFromTestCase(GatesTestSuite))
suite.addTests(loader.loadTestsFromTestCase(JobTestSuite))
suite.addTests(loader.loadTestsFromTestCase(ExportsTestSuite))


# initialize a runner, pass it your suite and run it
if __name__ == '__main__':
    runner = unittest.TextTestRunner(verbosity=3)
    result = runner.run(suite)
