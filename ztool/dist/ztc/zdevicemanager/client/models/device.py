from .base import Model, Collection

class DeviceModel(Model):

    @property
    def fleet_id(self):
        return self.attrs.get("fleet_id")

    @property
    def workspace_id(self):
        return self.attrs.get("workspace_id")

    @property
    def workspace_name(self):
        return self.attrs.get("workspace_name")

    def create_key(self, name):
        key = self.client.api.devices.create_device_key(self.id, name)


class DeviceCollection(Collection):
    model = DeviceModel

    def list(self):
        """
        List devices
        """
        resp = self.client.api.devices()
        return [self.prepare_model(r) for r in resp]

    def create(self, name, fleet_id=None):
        """
        Create a device

        Args:
            name (str): name of the device.
            fleet_id (str): fleet id where the device is associated.

        Returns:
            A :py:class:`Device` object.

        Raises:
            :py:class:`adm.errors.APIError`
                If the server returns an error.
        """
        resp = self.client.api.create_device(name, fleet_id)
        return self.prepare_model(resp)

    def get(self, device_id):
        """
        Get a device by ID.

        Args:
            device_id (str): Device ID.

        Returns:
            A :py:class:`Device` object.

        Raises:
            :py:class:`adm.errors.NotFound`
                If the device does not exist.
            :py:class:`adm.errors.APIError`
                If the server returns an error.
        """
        resp = self.client.api.get_device(device_id)
        return self.prepare_model(resp)

    def update(self, device_id, name, fleet_id=None):
        """
        Update a device.

        Args:
            device_id (str): Device ID.
            name (str): the new name of the device
            fleet_id (str): the fleet id to be assigned [Default: None]

        Returns:
            A :py:class:`Device` object.

        Raises:
            :py:class:`adm.errors.NotFound`
                If the device does not exist.
            :py:class:`adm.errors.APIError`
                If the server returns an error.
        """
        resp = self.client.api.update_device(device_id, name, fleet_id)
        return resp

    def remove(self, device_id):
        """
        Remove a device.

        Args:
            device_id (str): Device ID.

        Raises:
            :py:class:`adm.errors.NotFound`
                If the device does not exist.
            :py:class:`adm.errors.APIError`
                If the server returns an error.
        """
        resp = self.client.api.remove_device(device_id)

    def credentials(self, device_id, mode, endpoint_mode="secure"):
        """
        Provision a device.

        Args:
            device_id (str): Device ID.
            mode (str): Provisioning mode (cloud_token, device_token)

        Raises:
            :py:class:`adm.errors.NotFound`
                If the device does not exist.
            :py:class:`adm.errors.APIError`
                If the server returns an error.
        """
        resp = self.client.api.provision_device(device_id, mode, endpoint_mode)
        return resp

