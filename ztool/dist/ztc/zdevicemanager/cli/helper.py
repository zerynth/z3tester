import click
import zdevicemanager
from functools import wraps
from zdevicemanager.base.base import error, fatal

from ..client.client import ZdmClient

pass_adm = click.make_pass_decorator(ZdmClient, ensure=True)

def handle_error(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
             return f(*args, **kwargs)
        except zdevicemanager.client.errors.ForbiddenError as e:
            fatal("Access Denied. Run the command [zdm login]")
        except zdevicemanager.client.errors.NotFoundError as err:
            fatal("{}. {}.".format(err.title, err.msg))
        except zdevicemanager.client.errors.APIError as err:
            fatal("Internal Server error. Details: {}.".format(err.msg))
        except zdevicemanager.client.errors.ZdmException as err:
            fatal("ZDM general error. Details: {}.".format(err.message))
        except Exception as e:
            fatal("Unknown error. {}".format(e))
    return wrapper
