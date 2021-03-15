class ConditionApiMixin(object):

    def conditions(self, workspace_id, tag, device_id=None, threshold="0", status=""):
        """
        Get all conditions.

        Args:
            workspace_id (str): the  workspace id
            tag (str): the conditions tag
            device_id (str): the device id
            threshold (str): the min duration of conditions
            status (str): the status of conditions (open, closed)

        Raises:
            :py:class:`zdm.errors.APIError`
                If the server returns an error.
        """

        params = {
            "tag": tag,
            "threshold": threshold,
            "status": status,
            "device": device_id
        }
        url = self._url("/tsmanager/workspace/{0}/condition?sort=-start&size=50", workspace_id)
        res = self._result(self._get(url, params=params))
        return res["conditions"] if "conditions" in res and res["conditions"] is not None else []
