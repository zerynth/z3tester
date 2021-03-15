from .status import StatusModel, StatusCollection
from ..constants import JOB_FOTA_NAME


class FotaModel(StatusModel):

    @property
    def status(self):
        return self.value.get("status") if "status" in self.value else "<not set>"

    @property
    def name(self):
        return self.key


class FotaCollection(StatusCollection):
    model = FotaModel

    def schedule(self, fw_version, devices, on_time=""):
        """
        Schedule a FOTA.

        Args:
            fw_version (str): Firmware version.
            devices (list of str): Targets devices.
            on_time (datetime): When to schedule the fota.

        Returns:
            A :py:class:`FotaModel` object.

        Raises:
            :py:class:`adm.errors.APIError`
                If the server returns an error.
        """
        value = {"fw_version": fw_version, "on_schedule": on_time}
        id = self.client.api.create_changeset(JOB_FOTA_NAME, value, devices)
        return id

    def status_current(self, device_id):
        """
        Returns the current status of the FOTA.

        Args:
            device_id (str): The Device id.

        Returns:
            A :py:class:`FotaModel` object.

        Raises:
            :py:class:`adm.errors.APIError`
                If the server returns an error.
        """
        status = self.client.api.get_current_device_status(device_id)
        mstatus = [self.prepare_model(s) for s in status]
        for s in mstatus:
            if s.name == JOB_FOTA_NAME:
                return s
        return None

    def status_expected(self, device_id):
        """
       Returns the expected status of the FOTA.

       Args:
           name (str): Name of the job.
           device_id (str): The Device id.

       Returns:
           A :py:class:`FotaModel` object.

       Raises:
           :py:class:`adm.errors.APIError`
               If the server returns an error.
       """
        status = self.client.api.get_expected_device_status(device_id)
        mstatus = [self.prepare_model(s) for s in status]
        for s in mstatus:
            if s.name == JOB_FOTA_NAME:
                return s
        return None
