# -*- coding: utf-8 -*-
# @Author: Lorenzo
# @Date:   2017-10-03 12:34:29
# @Last Modified by:   Lorenzo
# @Last Modified time: 2017-10-10 16:14:59

from base import *

thing_conf_filename = 'thing.conf.json'
certificate_filename = 'certificate.pem.crt'
private_key_filename = 'private.pem.key'

class Thing:

    def __init__(self, thingname, awscli, resource_folder):
        self.thingname = thingname
        self._awscli = awscli
        self.resource_folder = resource_folder

    def create_with_keys_and_certificate(self):
        self._awscli.create_thing(self.thingname)

        data = self._awscli.create_keys_and_certificate()
        self.cert_arn = data['certificateArn']
        self.certificate = data['certificatePem']
        self.private_key = data['keyPair']['PrivateKey']

        self._awscli.attach_thing_principal(self.thingname, self.cert_arn)
        info(self.thingname, 'created and certificate attached')

    def set_policy(self, policy_name):
        self.policy_name = policy_name
        self._awscli.attach_principal_policy(self.cert_arn, self.policy_name)

    def store(self):
        fs.makedirs(self.resource_folder)

        thing_conf = {}
        thing_conf['mqttid'] = self.thingname
        thing_conf['thingname'] = self.thingname
        thing_conf['cert_arn'] = self.cert_arn

        fs.set_json(thing_conf, fs.path(self.resource_folder, thing_conf_filename))
        fs.write_file(self.certificate, fs.path(self.resource_folder, certificate_filename))
        fs.write_file(self.private_key, fs.path(self.resource_folder, private_key_filename))

        info(self.thingname, 'ready')

    def delete(self):
        for principal in self._awscli.get_thing_principals(self.thingname)['principals']:
            for policy in self._awscli.get_principal_policies(principal)['policies']:
                self._awscli.detach_principal_policy(principal, policy['policyName'])
            self._awscli.detach_thing_principal(self.thingname, principal)
            self._awscli.delete_certificate(principal.split('/')[-1])
        self._awscli.delete_thing(self.thingname)

        fs.rmtree(self.resource_folder)

    @staticmethod
    def set_active(project_path, thing_base_name, thing_id):
        thingname = thing_base_name + '_' + str(thing_id)
        thing_resources = fs.path(project_path, '.aws_things_resources', thingname)

        _thing_conf = fs.get_json(fs.path(thing_resources, thing_conf_filename))

        conf_file = fs.path(project_path, 'thing.conf.json')
        thing_conf = fs.get_json(conf_file)
        thing_conf.update(_thing_conf)
        fs.set_json(thing_conf, conf_file)

        for resource in [certificate_filename, private_key_filename]:
            fs.copyfile(fs.path(thing_resources, resource), fs.path(project_path, resource))

        zawsconf_file = fs.path(project_path, '.zawsconf')
        zawsconf = fs.get_json(zawsconf_file)
        zawsconf['active_thing_id'] = thing_id
        fs.set_json(zawsconf, zawsconf_file)