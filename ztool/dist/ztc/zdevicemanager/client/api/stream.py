class StreamApiMixin(object):

    def streams(self, workspace_id, type, status=""):
        """
        Get all the data stream associated with a workspace

        Args:
            workspace_id (str): the workspace Id.
            status (str): status ("active", "disabled")
        Returns:
            (list of dicts): a list of dictionaries

        Raises:
            :py:class:`zdevicemanager.errors.APIError`
                If the server returns an error.
        """
        params = {"status": status}
        if type == "data":
            params['type'] = "data_stream"
        elif type == "condition":
            params['type'] = "condition_stream"
        else:
            # TODO: raise an expection
            params['type'] = "data_stream"

        u = self._url("/gate/workspace/{0}", workspace_id)
        res = self._result(self._get(u, params=params))
        return res["gates"] if "gates" in res and res["gates"] is not None else []
