class FleetApiMixin(object):

    def fleets(self):
        """
        Get all the fleets

        Returns:
            (list of dicts): a list of dictionaries

        Raises:
            :py:class:`adm.errors.APIError`
                If the server returns an error.
        """
        u = self._url("/fleet/")
        res = self._result(self._get(u))
        return  res["fleets"] if "fleets" in res and res["fleets"] is not None else []

    # @utils.check_resource('image')
    def get_fleet(self, device_id):
        """
        Get detailed information about a fleet by ID.

        Args:
            device_id (str): The fleet id to get

        Returns:
            (dict): a dictionary of details

        Raises:
            :py:class:`adm.errors.APIError`
                If the server returns an error.
        """
        res = self._result(self._get(self._url("/fleet/{0}", device_id)))
        return res["fleet"]

    def create_fleet(self, name, workspace_id=None):
        """
        Create e new fleet.

        Args:
           name (str): The name of the flett

        Returns:
           (dict): a dictionary of details

        Raises:
           :py:class:`adm.errors.APIError`
               If the server returns an error.
        """
        payload = {
             "name": name,
             "workspace_id": None if workspace_id is None else workspace_id
        }
        u = self._url("/fleet/")
        res = self._result(self._post(u, data=payload))
        return res["fleet"]

    def update_fleet(self, device_id, name, fleet_id=None):
        """
       Update a  fleet.

       Args:
          device_id (str): The fleet id to get
          name (str): the new name of the fleet
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
        u = self._url("/fleet/{0}/", device_id)
        res = self._result(self._put(u, data=payload))
        return res

