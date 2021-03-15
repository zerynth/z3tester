from .gate import GateModel
from .base import Collection

class AlertModel(GateModel):

    @property
    def threshold(self):
        return self.type_configuration.get("threshold")


class AlertCollection(Collection):
    model = AlertModel

    def list(self, workspace_id, status=""):
        """
        List the alerts of a workspace of type "data" or "condition"
        """
        resp = self.client.api.alerts(workspace_id, status=status)
        return [self.prepare_model(r) for r in resp]

