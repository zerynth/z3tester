from .api.client import APIClient
from .logging import MyLogger
from .models.datatag import DataTagCollection
from .models.device import DeviceCollection
from .models.devicekey import DeviceKeyCollection
from .models.firmware import FirmwareCollection
from .models.fleet import FleetCollection
from .models.fota import FotaCollection
from .models.job import JobCollection
from .models.status import StatusCollection
from .models.workspace import WorkspaceCollection
from .models.export import ExportsCollection
from .models.condition import ConditionCollection
from .models.stream import StreamCollection
from .models.alert import AlertCollection

logger = MyLogger().get_logger()


class ZdmClient(object):
    """
    A client for communicating with a ZDM cloud.

    Example:

    Args:
        base_url (str): URL to the Docker server. For example,
            ``https://api.zdm.stage.zerynth.com``.
        version (str): The version of the API to use. Set to ``auto`` to
            automatically detect the server's version. Default: ``1``
        timeout (int): Default timeout for API calls, in seconds.
        user_agent (str): Set a custom user agent for requests to the server.

    """

    def __init__(self, *args, **kwargs):
        self.api = APIClient(*args, **kwargs)

    @property
    def workspaces(self):
        """
        An object for managing workspaces on the server.
        """
        return WorkspaceCollection(client=self)

    @property
    def devices(self):
        """
        An object for managing devices on the server.
        """
        return DeviceCollection(client=self)

    @property
    def fleets(self):
        """
        An object for managing fleets on the server.
        """
        return FleetCollection(client=self)

    @property
    def data(self):
        """
        An object for managing the data sent by the devices on the server.
        """
        return DataTagCollection(client=self)

    @property
    def keys(self):
        """
        An object for managing the keys of the devices on the server.
        """
        return DeviceKeyCollection(client=self)

    @property
    def jobs(self):
        """
        An object for managing the jobs.
        """
        return JobCollection(client=self)

    @property
    def fota(self):
        """
        An object for managing the fota.
        """
        return FotaCollection(client=self)

    @property
    def firmwares(self):
        """
        An object for managing the firmwares.
        """
        return FirmwareCollection(client=self)

    @property
    def status(self):
        """
        An object for managing the status of a device.
        """
        return StatusCollection(client=self)

    @property
    def conditions(self):
        """
        An object for managing the conditions.
        """
        return ConditionCollection(client=self)

    @property
    def streams(self):
        """
        An object for managing the streams.
        """
        return StreamCollection(client=self)

    @property
    def alerts(self):
        """
        An object for managing the alerts.
        """
        return AlertCollection(client=self)

    @property
    def exports(self):
        """
        An object for managing the exports.
        """
        return ExportsCollection(client=self)