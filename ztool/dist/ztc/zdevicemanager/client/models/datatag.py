from .base import Model, Collection


class DataTagModel(Model):

    @property
    def Tag(self):
        return self.attrs.get("tag")

    @property
    def TimestampDevice(self):
        return self.attrs.get("timestamp_device")

    @property
    def TimestampCloud(self):
        return self.attrs.get("timestamp_in")

    @property
    def DeviceId(self):
        return self.attrs.get("device_id")

    @property
    def DeviceName(self):
        return self.attrs.get("device_name")

    @property
    def Payload(self):
        return self.attrs.get("payload")


class DataTagCollection(Collection):
    model = DataTagModel

    def list(self, workspace_id, page=None, page_size=None, sort=None):
        """
        List tags available in a workspace
        """
        resp = self.client.api.tags(workspace_id)
        return resp

    def get(self, workspace_id, tag, device_id=None, start=None, end=None):
        """
        Get all the data associated to a tag
        """
        resp = self.client.api.get_data(workspace_id, tag, device_id, start=start, end=end)
        return [self.prepare_model(datatag) for datatag in resp]

