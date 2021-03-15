import string
import random
import json
import logging
import sys

og = logging.getLogger("ZDM_cli_test")
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

def randomString(stringLength=10):
    """Generate a random string of fixed length """
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))

def _result_to_json(click_result):
    #logging.debug(click_result.output)
    return json.loads(click_result.output)