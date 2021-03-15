class AlertsApiMixin(object):

    def alerts(self, workspace_id, status=""):
        """
        Get all the alerts associated with a workspace

        Args:
            workspace_id (str): the workspace Id.
            status (str): status ("active", "disabled")
        Returns:
            (list of dicts): a list of dictionaries

        Raises:
            :py:class:`zdevicemanager.errors.APIError`
                If the server returns an error.
        """
        params = {'type': "condition_alert"}
        if status:
            params['status'] = status

        u = self._url("/gate/workspace/{0}", workspace_id)
        res = self._result(self._get(u, params=params))
        return res["gates"] if "gates" in res and res["gates"] is not None else []
