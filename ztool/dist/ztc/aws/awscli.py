# -*- coding: utf-8 -*-
# @Author: Lorenzo
# @Date:   2017-10-03 10:34:40
# @Last Modified by:   Lorenzo
# @Last Modified time: 2017-10-10 15:53:40

from base import *

class AWSCli:

    def __init__(self):
        pass

    def create_thing(self, thingname):
        code, out, _ = proc.run('aws','iot','create-thing','--thing-name', thingname)

    def delete_thing(self, thingname):
        code, out, _ = proc.run('aws','iot','delete-thing','--thing-name', thingname)

    def create_keys_and_certificate(self):
        code, out, _ = proc.run('aws','iot','create-keys-and-certificate','--set-as-active')
        return json.loads(out)

    def attach_thing_principal(self, thingname, principal_arn):
        code, out, _ = proc.run('aws','iot','attach-thing-principal','--thing-name', thingname, 
                        '--principal', principal_arn)

    def detach_thing_principal(self, thingname, principal_arn):
        code, out, _ = proc.run('aws','iot','detach-thing-principal','--thing-name', thingname, 
                        '--principal', principal_arn)

    def get_thing_principals(self, thingname):
        code, out, _ = proc.run('aws','iot','list-thing-principals','--thing-name', thingname)
        return json.loads(out)

    def attach_principal_policy(self, principal_arn, policy_name):
        code, out, err = proc.run('aws','iot','attach-principal-policy','--principal', principal_arn, 
                        '--policy-name', policy_name)

    def detach_principal_policy(self, principal_arn, policy_name):
        code, out, err = proc.run('aws','iot','detach-principal-policy','--principal', principal_arn, 
                        '--policy-name', policy_name)

    def get_principal_policies(self, principal_arn):
        code, out, err = proc.run('aws','iot','list-principal-policies','--principal', principal_arn)
        return json.loads(out)

    def delete_certificate(self, certificate_id):
        code, out, _ = proc.run('aws','iot','update-certificate','--certificate-id', certificate_id, 
                        '--new-status', 'INACTIVE')
        code, out, _ = proc.run('aws','iot','delete-certificate','--certificate-id', certificate_id)

    def upload_to_s3(self,source,dest):
        code, out, _ = proc.run("aws","s3","sync",source,dest,outfn=log)
        return code==0

    def describe_thing(self,thing_name):
        code,out,_ = proc.run("aws","iot","describe-thing","--thing-name",thing_name)
        if code==0:
            return json.loads(out)
    def list_iam_roles(self,role_name=None):
        code,out,_ = proc.run("aws","iam","list-roles")
        if code!=0:
            return None
        roles = json.loads(out)
        if not role_name:
            return roles
        for role in roles["Roles"]:
            if role["RoleName"]==role_name:
                return role

    def create_iot_job(self,jobname,targets,job_source,s3_role):
        code,out,_ = proc.run("aws","iot","create-job","--job-id",jobname,"--targets"," ".join(targets),"--document-source",job_source,"--presigned-url-config",s3_role)
        return code==0
