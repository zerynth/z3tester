class DeviceApiMixin(object):

    def devices(self):
        """
        Get all the devices

        Returns:
            (list of dicts): a list of dictionaries

        Raises:
            :py:class:`adm.errors.APIError`
                If the server returns an error.
        """
        u = self._url("/device/")
        res = self._result(self._get(u))
        return res["devices"] if "devices" in res and res["devices"] is not None else []

    def get_device(self, device_id):
        """
        Get detailed information about a device by ID.

        Args:
            device_id (str): The device id to get

        Returns:
            (dict): a dictionary of details

        Raises:
            :py:class:`adm.errors.APIError`
                If the server returns an error.
        """
        res = self._result(self._get(self._url("/device/{0}", device_id)))
        return res["device"]

    def create_device(self, name, fleet_id=None):
        """
        Create e new device.

        Args:
           device_id (str): The device id to get

        Returns:
           (dict): a dictionary of details

        Raises:
           :py:class:`adm.errors.APIError`
               If the server returns an error.
        """
        payload = {
            "name": name,
            "fleet_id": None if fleet_id is None else fleet_id
        }
        u = self._url("/device/")
        res = self._result(self._post(u, data=payload))
        return res["device"]

    def update_device(self, device_id, name, fleet_id=None):
        """
       Update a  device.

       Args:
          device_id (str): The device id to get
          name (str): the new name of the device
          fleet_id (str): the fleet id to be assigned [Default: None]

       Returns:
          (dict): a dictionary of details

       Raises:
          :py:class:`adm.errors.APIError`
              If the server returns an error.
       """
        payload = {
            "name": name,
            "fleet_id": None if fleet_id is None else fleet_id
        }
        u = self._url("/device/{0}/", device_id)
        res = self._result(self._put(u, data=payload))
        return res

    def remove_device(self, device_id):
        """
       Remove a  device.

       Args:
          device_id (str): The device id to get

       Returns:
          (dict): a dictionary of details

       Raises:
          :py:class:`adm.errors.APIError`
              If the server returns an error.
       """

        u = self._url("/device/{0}/", device_id)
        res = self._result(self._delete(u))
        return res

    def workspace_of_device(self, device_id):
        """
        Get the Workspace ID of the Device

        Args:
           device_id (str): The device id.

        Returns:
           (dict): a dictionary of a workspace

        Raises:
           :py:class:`adm.errors.APIError`
               If the server returns an error.
        """
        u = self._url("/device/{0}/workspace", device_id)
        res = self._result(self._get(u))
        return res["workspace"]

    def create_device_key(self, device_id, name):
        """
        Create a authentication key for the device.

        Args:
          device_id (str): The device id.
          name (str): The name of the key.

        Returns:
          (dict): a dictionary of the created key.

        Raises:
          :py:class:`adm.errors.APIError`
              If the server returns an error.
        """
        payload = {"name": name}
        u = self._url("/device/{0}/key", device_id)
        res = self._result(self._post(u, data=payload))
        return res["key"]

    def list_device_keys(self, device_id):
        """
        Get all the keys of a device.

        Returns:
            (list of dicts): a list of keys dictionaries

        Raises:
            :py:class:`adm.errors.APIError`
                If the server returns an error.
        """
        u = self._url("/device/{0}/key", device_id)
        res = self._result(self._get(u))
        return res["keys"] if res["keys"] is not None else []

    def get_device_key(self, device_id, key_id):
        """
        Get a device key.

        Args:
            device_id (str): The Device id.
            key_id (str): The key id.

        Returns:
            (dict): a key dictionary

        Raises:
            :py:class:`adm.errors.APIError`
                If the server returns an error.
        """
        u = self._url("/device/{0}/key/{1}", device_id, key_id)
        res = self._result(self._get(u))
        return res["key"]

    def provision_device(self, device_id, mode, endpoint_mode):
        """
        Provision a device.

        Args:
            device_id (str): The Device id.
            mode (str): Credentials mode (cloud_token, device_token)
            endpoint_mode (str): TLS enabled (secure, insecure)

        Returns:
            (dict): a key dictionary

        Raises:
            :py:class:`adm.errors.APIError`
                If the server returns an error.
        """
        u = self._url("/device/{0}/credential", device_id)
        res = self._result(self._post(u, data={
	        "endpoint_mode": endpoint_mode,
            "provision_mode": mode
        }))
        return res["credential"]

