from datetime import datetime, timezone

class GateApiMixin(object):

    def gates(self, workspace_id, status="active", type=""):
        """
        Get all the gates associated to a workspace.

        Args:
            workspace_id (str): the workspace Id.
            status (str): Filter gates by status ['active', 'disabled']. Default "active".
            gtype (str): Filter gates by type ['webhook', 'dump', 'alarm']

        Returns:
            (list of dicts): a list of dictionaries

        Raises:
            :py:class:`zdevicemanager.errors.APIError`
                If the server returns an error.
        """
        params = {"status": status, "type": type}

        u = self._url("/gate/workspace/{0}", workspace_id)
        res = self._result(self._get(u, params=params))
        return res["gates"] if "gates" in res and res["gates"] is not None else []

    def get_webhook(self, gate_id):
        """
        Get detailed information about a webhook by ID.

        Args:
            gate_id (str): The gate id.

        Returns:
            (dict): a dictionary of details

        Raises:
            :py:class:`zdevicemanager.errors.APIError`
                If the server returns an error.
        """
        res = self._result(self._get(self._url("/gate/{0}/", gate_id)))
        return res["gate"]

    def create_webhook(self, name, url, token, period, workspace_id, tags=None, fleets=None, origin=None):
        """
        Create a new webhook.

        Args:
           name (str): The webhook name
           url (str): The webhook url for http post requests
           token (str): The webhook auth token
           period (int): The interval in seconds between two http requests
           workspace_id (str): The id of the workspace where to get data from
           tags ([]str): Optional tags to filter data
           fleets ([]str): Optional fleets id to filter data

        Returns:
           (dict): a dictionary of details

        Raises:
           :py:class:`zdevicemanager.errors.APIError`
               If the server returns an error.
        """
        body = {
            "name": name,
            "url": url,
            "content-type": "application/json",
            "period": period,
            "origin": "data",
            "payload": {
                "workspace_id": workspace_id},

            "tokens": {
                "X-Auth-Token": token
            }
        }

        if tags is not None:
            body["payload"]["tags"] = tags

        if fleets is not None:
            body["payload"]["fleets"] = fleets

        u = self._url("/gate/webhook/")
        res = self._result(self._post(u, data=body))
        return res

    def update_webhook(self, gate_id, name=None, period=None, url=None, tokens=None, tags=None, fleets=None):
        """
       Update an existing webhook.

       Args:
            gate_id (str): The webhook id
            name (str): Optional new name for the webhook
            period (int): Optional new period for the webhook
            url (str): Optional new url for the webhook
            tokens (dict): Optional dict containing webhook tokens
            tags (str[]): Optional new tags array to filter data
            fleets (str[]): Optional new fleets id array to filter data

       Returns:
          (dict): a dictionary of details

       Raises:
          :py:class:`zdevicemanager.errors.APIError`
              If the server returns an error.
       """

        body = {}
        if name is not None and name != "":
            body["name"] = name
        if period is not None:
            body["period"] = name
        if url is not None and url != "":
            body["url"] = url
        if tokens is not None:
            body["tokens"] = tokens
        if tags is not None:
            body["tags"] = tags
        if fleets is not None:
            body["fleets"] = fleets

        u = self._url("/gate/webhook/{0}", gate_id)
        res = self._result(self._put(u, data=body))
        return res

    def create_export_gate(self, name, dump_name, type, frequency, day, workspace_id, email, fleets=None, tags=None):
        """
        Create a new export gate.

        Args:
           name (str): The gate name
           dump_name (str): The export name
           type (str): The export format
           frequency (str): The frequency for the export generation
           day(int): the day of the week for weekòly frequency
           workspace_id (str): The workspace where to get data from
           email (str): The email address where to be notified
           fleets (str[]): Fleets id array to filter data
           tags (str[]): Tags array to filter data

        Returns:
           (dict): a dictionary of details

        Raises:
           :py:class:`zdevicemanager.errors.APIError`
               If the server returns an error.
        """

        cron = "9 *"

        if frequency == "weekly":
            cron = "9 " + day

        if frequency == "now":
            d = datetime.now(timezone.utc)
            h = d.hour
            cron = str(h) + " *"

        body = {
            "name": name,
            "dump_name": dump_name,
            "dump_type": type,
            "payload": {
                "cron": cron,
                "configurations": {
                    "workspace_id": workspace_id,
                    "compressed": "todo"
                },
                "notifications": {
                    "emails": [email]
                }
            }
        }

        if tags is not None:
            body["payload"]["configurations"]["tags"] = tags

        if fleets is not None:
            body["payload"]["configurations"]["fleets"] = fleets

        u = self._url("/gate/dump/")
        res = self._result(self._post(u, data=body))
        return res

    def update_export_gate(self, gate_id, name=None, cron=None, dump_type=None, email=None, tags=None):
        """
        Update an existing export gate.

        Args:
            gate_id(str): The gate id
            name (str): The optional new gate name
            cron (str): The new cron string for frequency
            dump_type (str): The export format
            email (str): The email address where to be notified
            tags (str[]): Tags array to filter data

        Returns:
           (dict): a dictionary of details

        Raises:
           :py:class:`zdevicemanager.errors.APIError`
               If the server returns an error.
        """

        body = {}
        if name is not None and name != "":
            body["name"] = name
        if cron is not None and cron != "":
            body["cron"] = name
        if dump_type is not None and (dump_type == "json" or dump_type == "csv"):
            body["dump_type"] = dump_type
        if email is not None:
            body["emails"] = [email]
        if tags is not None:
            body["tags"] = tags

        u = self._url("/gate/dump/{0}", gate_id)
        res = self._result(self._put(u, data=body))
        return res


    def update_gate_status(self, gate_id, status):
        """
       Update a gate status (active, disabled).

       Args:
          gate_id (str): The gate id to disable or enable
          status (str): the new status of the gate ("active" or "disabled")

       Returns:
          (dict): a dictionary of details

       Raises:
          :py:class:`zdevicemanager.errors.APIError`
              If the server returns an error.
       """
        payload = {}

        if status:
            payload["status"] = status

        u = self._url("/gate/status/{0}", gate_id)
        res = self._result(self._put(u, data=payload))
        return res

    def delete_gate(self, gate_id):
        """
       Delete a gate

       Args:
          gate_id (str): The gate id to disable or enable

       Returns:
          (dict): A dict of details

       Raises:
          :py:class:`zdevicemanager.errors.APIError`
              If the server returns an error.
       """

        u = self._url("/gate/{0}/", gate_id)
        res = self._result(self._delete(u))
        return res

    def create_datastream(self, name, url, token, period, workspace_id, tags=None, fleets=None, origin=None):
        """
        Create a new webhook.

        Args:
           name (str): The webhook name
           url (str): The webhook url for http post requests
           token (str): The webhook auth token
           period (int): The interval in seconds between two http requests
           workspace_id (str): The id of the workspace where to get data from
           tags ([]str): Optional tags to filter data
           fleets ([]str): Optional fleets id to filter data

        Returns:
           (dict): a dictionary of details

        Raises:
           :py:class:`zdevicemanager.errors.APIError`
               If the server returns an error.
        """
        body = {
            "name": name,
            "url": url,
            "content-type": "application/json",
            "period": period,
            "origin": "data",
            "payload": {
                "workspace_id": workspace_id},

            "tokens": {
                "X-Auth-Token": token
            }
        }

        if tags is not None:
            body["payload"]["tags"] = tags

        if fleets is not None:
            body["payload"]["fleets"] = fleets

        u = self._url("/gate/webhook/")
        res = self._result(self._post(u, data=body))
        return res
