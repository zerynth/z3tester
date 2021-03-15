from datetime import datetime

from .base import Model, Collection
from ..constants import MANIFEST_KEY, STATUS_KEY_STRONG_PRIVATE, VM_INFO_KEY


class StatusModel(Model):

    @property
    def version(self):
        ver = self.attrs.get("version")  # timestamp im milliseconds
        ver /= 1000
        return datetime.utcfromtimestamp(ver).strftime('%Y-%m-%d %H:%M:%S')

    @property
    def key(self):
        return self.attrs.get("key")

    @property
    def value(self):
        return self.attrs.get("value")

    @property
    def target(self):
        return self.attrs.get("target")


class StatusCollection(Collection):
    model = StatusModel

    def create(self, key, value, targets):
        """
        Create a new changeset

        Args:
            key (str): Key of the changeset.
            value (str): Value of the changeset.
            targets (list): Targets of the changeset (devices).

        Returns:
            A :py:class:`StatusModel` object.

        Raises:
            :py:class:`adm.errors.APIError`
                If the server returns an error.
        """
        id = self.client.api.create_changeset(key, value, targets)
        return id

    def _get_device_current_status(self, device_id, filter_key_by_prefix=None):
        """
        Get all the current status of the device.
        It returns a list of status object

        Args:
            device_id (str): id of the device
            filter_key_by_prefix (str): filter the status if the key start with the prefix.
        Returns:
            A list of py:class:`StatusModel` object.

        Raises:
            :py:class:`adm.errors.APIError`
                If the server returns an error.
        """
        raw_status = self.client.api.get_current_device_status(device_id, filter_key_by_prefix=filter_key_by_prefix)
        return [self.prepare_model(s) for s in raw_status]

    def get_device_current_status_strong_private(self, device_id):
        """
        Get the string private current status of the device.

        Args:
            device_id (str): id of the device

        Returns:
            A list of py:class:`StatusModel` object.
        Raises:
            :py:class:`adm.errors.APIError`
                If the server returns an error.
        """

        return self._get_device_current_status(device_id, filter_key_by_prefix=STATUS_KEY_STRONG_PRIVATE)

    def get_device_manifest(self, device_id):

        status = self.get_device_current_status_strong_private(device_id)
        for s in status:
            if s.key == MANIFEST_KEY:
                return s
        return None

    def get_device_vm_info(self, device_id):
        status = self.get_device_current_status_strong_private(device_id)
        for s in status:
            if s.key == VM_INFO_KEY:
                return s
        return None