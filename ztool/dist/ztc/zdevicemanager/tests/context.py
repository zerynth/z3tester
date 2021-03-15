# -*- coding: utf-8 -*-

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

os.environ['ZERYNTH_TESTMODE'] = '2'

from zdevicemanager.base import init_all
from zdevicemanager.base.tools import tools
from zdevicemanager.base.base import cli
from zdevicemanager.client.client import ZdmClient

init_all()
tools.init()
