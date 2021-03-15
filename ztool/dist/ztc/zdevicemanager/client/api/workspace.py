import base64


class WorkspaceApiMixin(object):

    def containers(self, all=False, limit=-1, size=False, filters=None):
        u = self._url("/workspace/")
        res = self._result(self._get(u))
        return res["workspaces"]

    # @utils.check_resource('image')
    def get_workspace(self, workspace):
        """
        Get detailed information about a workspace.

        Args:
            workspace (str): The workspace to get

        Returns:
            (dict): a dictionary of details

        Raises:
            :py:class:`adm.errors.APIError`
                If the server returns an error.
        """
        res = self._result(self._get(self._url("/workspace/{0}", workspace)))
        return res["workspace"]

    def list_fleets(self, workspace):
        res = self._result(self._get(self._url("/workspace/{0}/fleets", workspace)))
        return res["fleets"]

    def create_workspace(self, name, description=""):
        """
        Create a new workspace.

        Args:
            name (str): The name of the workspace.
            description (str): A short description.

        Returns:
            (dict): a dictionary of details

        Raises:
            :py:class:`adm.errors.APIError`
                If the server returns an error.
        """
        data = {"name": name, "description": description}
        u = self._url("/workspace/")
        res = self._result(self._post(u, data=data))
        return res["workspace"]

    def firmware_all(self, workspace_id):
        """
        Return all the firmwares uploaded for a workspace.

        Args:
            workspace_id (str): The workspace id.

        Returns:
            (list of dict): a list of dictionary

        Raises:
            :py:class:`adm.errors.APIError`
                If the server returns an error.
        """
        res = self._result(self._get(self._url("/workspace/{0}/firmware", workspace_id)))
        return res["firmwares"] if "firmwares" in res and res["firmwares"] is not None else []

    def firmwares_upload(self, workspace_id, version, fw_bins, metadata={}, description=""):
        """
        Upload a firmware with a version associated to a workspace.

        Args:
            workspace_id (str): The workspace id.
            version (str): the version of the firmware.
            fw_bins (list of str): path of the binary firmwares in base64 to upload.
            metadata (dict): any other info as dict.
            description (str): short description of the fiirmware.

        Returns:
            (list of dict): a list of dictionary

        Raises:
            :py:class:`adm.errors.APIError`
                If the server returns an error.
        """
        u = self._url("/workspace/{0}/firmware/{1}", workspace_id, version)
        # binsbase64 = []
        # for filename in file_paths:
        #     #print("reading file", filename)
        #     with open(filename, "rb") as image_file:
        #         enc64 = base64.b64encode(image_file.read())
        #         binsbase64.append(enc64.decode("utf8"))
        payload = {"bin": fw_bins,  #binsbase64,
                   "metadata": metadata,
                   "description": ""}
        res = self._result(self._post(u, data=payload))
        return res["firmware"]
