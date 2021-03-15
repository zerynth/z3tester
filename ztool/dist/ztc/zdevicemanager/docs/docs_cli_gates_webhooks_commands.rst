.. _zdm-cmd-gates-webhook:


Webhook gates
============

List of commands:

* :ref:`Create webhook <zdm-cmd-gates-webhook-create>`
* :ref:`Update webhook <zdm-cmd-gates-webhook-update>`
* :ref:`List webhooks <zdm-cmd-gates-webhook-get-all>`

    
.. _zdm-cmd-gates-webhook-create:

Webhook creation
----------------

To create a new webhook use the command: ::

    zdm gate webhook create name url token period workspace_id

where :samp:`name` is the name that you want to give to your new webhook
:samp:`url` is your webhook url
:samp:`token` is the authentication token for your webhook (if needed)

:samp:`workspace_id` is the uid of the workspace you want to receive data from

You also have the possibility to add filters on data using the following options:

:option:`--tag` To specify a tag to filter data (you can specify more than one)
:option:`--fleet` To specify a fleet to filter data (you can specify more than one)
:option:`--token` Token used as value of the Authorization Bearer fot the webhook endpoint.

    
.. _zdm-cmd-gates-webhook-get-all:

List export gates
-----------------

To see a list of your webhooks use the command: ::

    zdm gate webhook all workspace_id

where :samp:`workspace_id` is the uid of the workspace

You also have the possibility to add filters on gates using the following options:

* :option:`--status active|disabled` to filter on gate's status

    
.. _zdm-cmd-gates-webhook-update

Update webhook
--------------

To update a webhook use the command: ::

    zdm gate webhook update gate_id

you can change gate's configuration using the following options: ::
* :option:`--name` to change the webhook name
* :option:`--period` to change the webhook period
* :option:`--url` to change the webhook url
* :option:`--tag` (multiple option) to replace webhook tag array
* :option:`--fleet` (multiple option) to replace webhook fleets array

    
