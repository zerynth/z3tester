
*****************************
Zerynth Device Manager Client
*****************************

Zerynth Device Manager can be used for orchestrating both MCU (micro-controller) and CPU (micro-processor) based devices.
If you want to connect a MCU device like a RapsberryPI, a SBC (Single Board Computer) a PC and any Python application general,
the ZDM Client Python Library is what you need.


The Zerynth ZDM Client is a Python implementation of a client of the ZDM.
It can be used to emulate a Zerynth device and connect it to the ZDM.


================
The ZDMClient class
================

.. class:: ZDMClient(cred=None, cfg=None,  jobs_dict={}, condition_tags=[], on_timestamp=None, on_open_conditions=None, verbose=False, )

    Creates a ZDM client instance.

    * :samp:`cred` is the object that contains the credentials of the device. If None the configurations are read from zdevice.json file.
    * :samp:`cfg` is the object that contains the mqtt configurations. If None set the default configurations.
    * :samp:`jobs_dict` is the dictionary that defines the device's available jobs (default None).
    * :samp:`condition_tags` is the list of condition tags that the device can open and close (default []).
    * :samp:`verbose` boolean flag for verbose output (default False).
    * :samp:`on_timestamp` callback called when the ZDM responds to the timestamp request. on_timestamp(client, timestamp)
    * :samp:`on_open_conditions` callback called when the ZDM responds to the open conditions request. on_open_conditions(client, conditions)

    
.. method:: id(pw)

        Return the device id.
        
.. method:: connect()

        Connect your device to the ZDM.
        
.. method:: publish(payload, tag)

    Publish a message to the ZDM.

    * :samp:`payload` is a dictionary containing the payload.
    * :samp:`tag` is the tag associated to the published payload.
    
.. method:: request_timestamp()

    Request the timestamp to the ZDM.
    When the timestamp is received, the callback  :samp:`on_timestamp` is called.
.. method:: request_open_conditions()

    Request all the open conditions of the device not yet closed.
    When the open conditions are received, the callback :samp:`on_open_conditions` is called.
.. method:: new_condition(condition_tag)

    Create and return a new condition.

     * :samp:`condition_tag` the tag as string of the new condition.
====================
The Conditions class
=====================

.. class:: Condition(client, tag)

   Creates a Condition on a tag.

   * :samp:`client` is the object ZDMClient object used to open and close the condition.
   * :samp:`tag` is the tag associated with the condition.
   
.. method:: open(payload, finish)

Open a condition.

* :samp:`payload` is a dictionary containing custom data to associated with the open operation.
* :samp:`start` is a time (RFC3339) used to set the opening time. If None is automatically set with the current time.
.. method:: close(payload, finish)

Close a condition.

* :samp:`payload` is a dictionary containing custom data to associated with the close operation.
* :samp:`finish` is a time (RFC3339) used to set the closing time. If None is automatically set with the current time.
.. method:: reset()

    Reset the condition by generating a new id.
.. method:: is_open()

    Return True if the condition is open. False otherwise.
