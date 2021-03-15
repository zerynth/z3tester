from ..constants import STATUS_KEY_PRIVATE, STATUS_KEY_STRONG_PRIVATE
from ..errors import ZdmException


class StatusApiMixin(object):

    def create_changeset(self, key, value, targets):
        """
        Return all the tags of a workspace

        Args:
            key (str): The key of the changeset.
            value (json): The Value to be associated to the key.
            targets (list of str): List of targets of the changest.

        Retunrs:
            id (str). The id of the created changeset

        Raises:
            :py:class:`zdm.errors.APIError`
                If the server returns an error.
        """
        payload = {"key": key,
                   "value": value,
                   "targets": targets}
        url = self._url("/status/changeset")
        res = self._result(self._post(url, data=payload))
        return res["id"]

    def get_current_device_status(self, device_id, filter_key_by_prefix=None):
        """
        Returns all the request of changeset sent by the device to the zdm.

        Args:
            device_id (str): The device id.
            filter_key_by_prefix (str): Filter the key by the prefix. Default None.
        Returns:
            (list of dicts): a list of changesets

        Raises:
            :py:class:`zdm.errors.APIError`
                If the server returns an error.

        Example:
            >>> from zdevicemanager import ZdmClient
            >>> c = ZdmClient(base_url="api.zdm.zerynth.com")
            >>> dev = c.devices.create("mydev")
            >>> c.get_current_device_status(dev.id)
             [
                {
                    "key": "@fota":
                    "value: { },
                    "version": 1582731641910
                },
                {
                    "key": "__manifest":
                    "value: { },
                    "version": 1582731641910
                }
             ]
        """
        u = self._url("/status/currentstatus/{0}", device_id)
        res = self._result(self._get(u))
        status = []
        if filter_key_by_prefix is not None and filter_key_by_prefix not in [STATUS_KEY_PRIVATE,
                                                                             STATUS_KEY_STRONG_PRIVATE]:
            raise ZdmException("Bad filter. '{}' is not a valid filter.".format(filter_key_by_prefix))
        if "status" in res and res["status"] is not None:
            for key, value in res["status"].items():
                if filter_key_by_prefix is None:
                    status.append({"key": key, "value": value['v'], "version": value['t']})
                elif filter_key_by_prefix is not None and key.startswith(filter_key_by_prefix):
                    status.append({"key": key, "value": value['v'], "version": value['t']})
                else:
                    pass
        return status

    def get_expected_device_status(self, device_id):
        """
        Returns all the request of changeset sent by the zdm to the device

        Args:
            device_id (str): The device id.

        Returns:
            (list of dicts): a list of changesets

        Raises:
            :py:class:`zdm.errors.APIError`
                If the server returns an error.

        Example:
            >>> from zdm import ZdmClient
            >>> c = ZdmClient(base_url="api.zdm.stage.zerynth.com")
            >>> dev = zcli.adm.devices.create("mydev")
            >>> c.get_expected_device_status(dev.id)
             [
                {
                    "key": "@led_on":
                    "value: {
                          "red": "on"
                    },
                    "version": 1582731641910
                },
                {
                    "key": "@set_temp":
                    "value: {
                         "temp": 23
                    },
                    "version": 1582731641910
                }
             ]
        """
        u = self._url("/status/expected/{0}", device_id)
        res = self._result(self._get(u))
        status = []
        if "status" in res and res["status"] is not None:
            for key, value in res["status"].items():
                status.append({"key": key, "value": value['v'], "version": value['t']})
        return status
