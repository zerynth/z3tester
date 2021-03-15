from .base import Collection
from .status import StatusModel


class JobModel(StatusModel):

    @property
    def status(self):
        return self.value.get("status") if "status" in self.value else "<not set>"

    @property
    def name(self):
        # delete the "@" at the begining of the key
        return self.convert_job_to_name(self.key)

    @staticmethod
    def convert_name_into_job(name):
        if not name.startswith('@'):
            name = "@" + name
        return name

    @staticmethod
    def convert_job_to_name(name):
        if name.startswith('@'):
            return name[1:]
        return name


class JobCollection(Collection):
    model = JobModel

    def schedule(self, name, args, targets, on_time=None):
        """
        Schedule a new Job

        Args:
            name (str): Name of the job.
            args (dict): Arguments of the job as key, value.
            targets (list): Targets of the changeset (devices).

        Returns:
            A :py:class:`JobModel` object.

        Raises:
            :py:class:`adm.errors.APIError`
                If the server returns an error.
        """
        value = {"args": args,
                 "on_schedule": on_time}
        key = JobModel.convert_name_into_job(name)
        id = self.client.api.create_changeset(key, value, targets)
        return id

    def status_current(self, name, device_id):
        """
        Returns the current status of the job. The status of the job from the device to the zdm.

        Args:
            name (str): Name of the job.
            device_id (str): The Device id.

        Returns:
            A :py:class:`JobModel` object.

        Raises:
            :py:class:`adm.errors.APIError`
                If the server returns an error.
        """
        status = self.client.api.get_current_device_status(device_id)
        mstatus = [self.prepare_model(s) for s in status]
        for s in mstatus:
            if s.name == name:
                return s
        return None

    def status_expected(self, name, device_id):
        """
       Returns the expected status of the job. The status of the job requested by the zdm to the device.

       Args:
           name (str): Name of the job.
           device_id (str): The Device id.

       Returns:
           A :py:class:`JobModel` object.

       Raises:
           :py:class:`adm.errors.APIError`
               If the server returns an error.
       """
        status = self.client.api.get_expected_device_status(device_id)
        mstatus = [self.prepare_model(s) for s in status]
        for s in mstatus:
            if s.name == name:
                return s
        return None