from .base import Model, Collection


class FirmwareModel(Model):
    @property
    def version(self):
        return self.attrs.get("version")

    @property
    def metadata(self):
        # json of metadata information of the firmware (e,g. "bc_slot": )
        return self.attrs.get("metadata")

    @property
    def workspace_id(self):
        return self.attrs.get("workspace_id")


class FirmwareCollection(Collection):
    model = FirmwareModel

    def list(self, workspace_id):
        """
        List the firmware for a workspace.
        """
        res = self.client.api.firmware_all(workspace_id)
        return [self.prepare_model(f) for f in res]

    def upload(self, workspace_id, version, file_paths, metadata={}, description=""):
        """
        Upload one or more firmware for a workspace and with a version.
        """
        res = self.client.api.firmwares_upload(workspace_id, version, file_paths, metadata, description)
        return self.prepare_model(res)
