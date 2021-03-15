from .base import Model, Collection


class ConditionModel(Model):
    @property
    def Uuid(self):
        return self.attrs.get("uuid")

    @property
    def Tag(self):
        return self.attrs.get("tag")

    @property
    def DeviceId(self):
        return self.attrs.get("device_id")

    @property
    def PayloadStart(self):
        return self.attrs.get("payload")

    @property
    def PayloadFinish(self):
        return self.attrs.get("payloadf")

    @property
    def Start(self):
        return self.attrs.get("start")

    @property
    def Finish(self):
        return self.attrs.get("finish")

    @property
    def Duration(self):
        return self.attrs.get("duration")


class ConditionCollection(Collection):
    model = ConditionModel

    def list(self, workspace_id, tag, device_id=None, threshold="0", status=""):
        """
        Get all the conditions associated to a tag workspace
        """

        resp = self.client.api.conditions(workspace_id, tag, device_id, threshold, status)
        return [self.prepare_model(condition) for condition in resp]

