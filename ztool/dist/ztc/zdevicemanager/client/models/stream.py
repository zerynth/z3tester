from .gate import GateModel
from .base import Collection


class StreamModel(GateModel):

    @property
    def period(self):
        return self.type_configuration.get("period")

    @property
    def tags(self):
        return self.type_configuration.get("tags")

    @property
    def fleets(self):
        return self.type_configuration.get("fleets")


class StreamCollection(Collection):
    model = StreamModel

    def list(self, workspace_id, type, status=""):
        """
        List the  streams of a workspace of type "data" or "condition"
        """
        resp = self.client.api.streams(workspace_id, type, status=status)
        return [self.prepare_model(r) for r in resp]

