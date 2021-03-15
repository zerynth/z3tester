# AWS IoT Thing Template
# Created at 2017-10-03 08:49:48.182639

import streams
import json
from wireless import wifi

from espressif.esp32net import esp32wifi as wifi_driver

from aws.iot import iot
import helpers

new_resource('private.pem.key')
new_resource('certificate.pem.crt')
new_resource('thing.conf.json')

streams.serial()
wifi_driver.auto_init()

wifi.link("SSID",wifi.WIFI_WPA2,"PSW")

pkey, clicert = helpers.load_key_cert('private.pem.key', 'certificate.pem.crt')
thing_conf = helpers.load_thing_conf()

thing = iot.Thing(thing_conf['endpoint'], thing_conf['mqttid'], clicert, pkey, thingname=thing_conf['thingname'])
thing.mqtt.connect()
thing.mqtt.loop()

while True:
    print('publish random sample...')
    thing.mqtt.publish("dev/samples", json.dumps({ 'asample': random(0,10) }))
    sleep(4000)