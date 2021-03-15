from .base import Model, Collection


class GateModel(Model):

    # @property
    # def period(self):
    #     return self.attrs.get("period")

    @property
    def status(self):
        return self.attrs.get("status")

    @property
    def workspace_id(self):
        return self.attrs.get("workspace_id")

    @property
    def is_enabled(self):
        return self.attrs.get("status") == "active"

    @property
    def is_disabled(self):
        return self.attrs.get("status") == "disabled"

    @property
    def last_time_scheduled(self):
        return self.attrs.get("last_time_schedule")

    @property
    def deleted_at(self):
        return self.attrs.get("deleted_at")

    @property
    def type(self):
        return self.attrs.get("type")

    @property
    def is_datastream(self):
        return self.attrs.get("type") == "data_stream"

    @property
    def is_conditionstream(self):
        return self.attrs.get("type") == "condition_stream"

    @property
    def type_configuration(self):
        return self.attrs.get("type_configuration")

    @property
    def subtype(self):
        return self.attrs.get("subtype")

    @property
    def subtype_configuration(self):
        return self.attrs.get("subtype_configuration")



class GateCollection(Collection):
    model = GateModel

    def list(self, workspace_id, status, gtype):
        """
        List all gates of a workspace.
        """
        resp = self.client.api.gates(workspace_id, status, gtype)
        return [self.prepare_model(r) for r in resp]

    def get(self, gate_id):
        """
        GetS an webhook gate.

        Args:
            gate_id (str): The id of the gate.
        Returns:
            (:py:class:`GateModel`): The gate.
        Raises:
            :py:class:`zdm.errors.NotFound`
                If the image does not exist.
            :py:class:`zdm.errors.APIError`
                If the server returns an error.
        """
        return self.prepare_model(self.client.api.get_webhook(gate_id))

    def delete(self, gate_id):
        return self.client.api.delete_gate(gate_id)

    def enable(self, gate_id):
        return self.client.api.update_gate_status(gate_id, "active")

    def disable(self, gate_id):
        return self.client.api.update_gate_status(gate_id, "disabled")

    def update_gate_status(self, gate_id, status):
        """
        Upadate a gate's status.

        Args:
            gate_id (str): The id of the gate.
            status (str): "active", "disabled".
        Returns:
            (:py:class:`GateModel`): The gate.
        Raises:
            :py:class:`zdm.errors.NotFound`
                If the image does not exist.
            :py:class:`zdm.errors.APIError`
                If the server returns an error.
        """
        return self.prepare_model(self.client.api.update_gate_status(gate_id, status))