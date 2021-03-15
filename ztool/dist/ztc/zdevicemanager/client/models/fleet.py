from .base import Model, Collection


class FleetModel(Model):
    @property
    def workspace_id(self):
        return self.attrs.get("workspace_id")


class FleetCollection(Collection):
    model = FleetModel

    def create(self, name, description=""):
        """
        Create a fleet

        Args:
            name (str): name of the device.
            fleet_id (str): fleet id where the device is associated.

        Returns:
            A :py:class:`Device` object.

        Raises:
            :py:class:`adm.errors.APIError`
                If the server returns an error.
        """
        resp = self.client.api.create_fleet(name, description)
        return self.prepare_model(resp)

    def get(self, device_id):
        """
        Get a device by ID.

        Args:
            device_id (str): device ID.

        Returns:
            A :py:class:`device` object.

        Raises:
            :py:class:`adm.errors.NotFound`
                If the device does not exist.
            :py:class:`adm.errors.APIError`
                If the server returns an error.
        """
        resp = self.client.api.get_fleet(device_id)
        return self.prepare_model(resp)

    def list(self, workspace_id):
        """
        List fleets of a workspace
        """
        resp = self.client.api.list_fleets(workspace_id)
        return [self.prepare_model(r) for r in resp]