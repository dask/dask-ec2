from __future__ import print_function, division, absolute_import

import time
import logging

import paramiko
import boto3
from botocore.exceptions import ClientError

from dask_ec2.exceptions import DaskEc2Exception

logger = logging.getLogger(__name__)

DEFAULT_SG_GROUP_NAME = "dask-ec2-default"


class EC2(object):

    def __init__(self, region):
        self.ec2 = boto3.resource('ec2', region_name=region)
        self.client = boto3.client('ec2', region_name=region)

    def check_keyname(self, keyname):
        logger.debug("Checking that keyname '%s' exists on EC2", keyname)
        try:
            key_pair = self.client.describe_key_pairs(KeyNames=[keyname])
            _ = [i for i in key_pair]
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "InvalidKeyPair.NotFound":
                raise DaskEc2Exception(
                    "The keyname '%s' does not exist, please create it in the EC2 console" %
                    keyname)
            else:
                raise e

    def check_keypair(self, keyname, keypair):
        # TODO: Is this possible?
        return
        key_pair = self.ec2.KeyPair(keyname)
        print(key_pair.key_fingerprint)

        key = paramiko.RSAKey.from_private_key_file(keypair)
        print(key.get_fingerprint())

        # import hashlib
        # sha1digest = hashlib.sha1(key.exportKey('DER', pkcs=8)).hexdigest()
        # print(sha1digest)

    def check_sg(self, security_group):
        """Checks if the security groups exists.
        If security_group is the default one it will create it.
        """
        logger.debug("Checking that security group '%s' exists on EC2", security_group)
        try:
            collection = self.ec2.security_groups.filter(GroupNames=[security_group])
            matches = [i for i in collection]
            if len(matches) == 0:
                if security_group == DEFAULT_SG_GROUP_NAME:
                    logger.debug("Default security group '%s' not found, we will create it",
                                 DEFAULT_SG_GROUP_NAME)
                    self.create_default_sg()
                else:
                    raise DaskEc2Exception(
                        "Security group '%s' not found, please create or use the default '%s'" %
                        (security_group, DEFAULT_SG_GROUP_NAME))
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "InvalidGroup.NotFound":
                if security_group == DEFAULT_SG_GROUP_NAME:
                    logger.debug("Default security group '%s' not found, creating it",
                                 DEFAULT_SG_GROUP_NAME)
                    self.create_default_sg()
                else:
                    raise DaskEc2Exception(
                        "Security group '%s' not found, please create or use the default '%s'" %
                        (security_group, DEFAULT_SG_GROUP_NAME))
            else:
                raise e

    def create_default_sg(self):
        """Create the default security group
        """
        logger.debug("Creating default (very open) security group '%s'", DEFAULT_SG_GROUP_NAME)
        try:
            response = self.client.create_security_group(
                GroupName=DEFAULT_SG_GROUP_NAME,
                Description="Default security group for dask-ec2",)
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "InvalidGroup.Duplicate":
                logger.debug("Default security group already exists")
            else:
                raise e

        logger.debug("Setting up default values for the '%s' security group", DEFAULT_SG_GROUP_NAME)
        collection = self.ec2.security_groups.filter(GroupNames=[DEFAULT_SG_GROUP_NAME])
        security_group = [i for i in collection][0]

        IpPermissions = [
            {
                'IpProtocol': 'tcp',
                'FromPort': 0,
                'ToPort': 65535,
                'IpRanges': [
                    {
                        'CidrIp': '0.0.0.0/0'
                    },
                ],
            }, {
                'IpProtocol': 'udp',
                'FromPort': 0,
                'ToPort': 65535,
                'IpRanges': [
                    {
                        'CidrIp': '0.0.0.0/0'
                    },
                ],
            }, {
                'IpProtocol': 'icmp',
                'FromPort': -1,
                'ToPort': -1,
                'IpRanges': [
                    {
                        'CidrIp': '0.0.0.0/0'
                    },
                ],
            }
        ]

        try:
            security_group.authorize_egress(IpPermissions=IpPermissions)
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "InvalidPermission.Duplicate":
                logger.debug("Outbound Permissions for default security group already set")
            else:
                raise e

        try:
            security_group.authorize_ingress(IpPermissions=IpPermissions)
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "InvalidPermission.Duplicate":
                logger.debug("Inbound Permissions for default security group already set")
            else:
                raise e

        return security_group

    def get_security_group_ids(self, security_groups):
        """Get the security group ids for the security group names on
        `self.security_groups`
        """
        collection = self.ec2.security_groups.filter(GroupNames=security_groups)
        return [i.id for i in collection]

    def launch(self,
               name,
               image_id,
               instance_type,
               count,
               keyname,
               security_group=DEFAULT_SG_GROUP_NAME,
               volume_type='gp2',
               volume_size=500,
               keypair=None):
        self.check_keyname(keyname)
        if keypair:
            self.check_keypair(keyname, keypair)
        self.check_sg(security_group)

        device_map = [
            {
                'DeviceName': '/dev/sda1',
                'Ebs': {
                    'VolumeSize': volume_size,
                    'DeleteOnTermination': True,
                    'VolumeType': volume_type,
                },
            },
        ]

        logger.debug("Creating %i instances on EC2", count)
        instances = self.ec2.create_instances(
            ImageId=image_id,
            KeyName=keyname,
            MinCount=count,
            MaxCount=count,
            InstanceType=instance_type,
            SecurityGroups=[security_group],
            SecurityGroupIds=self.get_security_group_ids([security_group]),
            BlockDeviceMappings=device_map,)
        time.sleep(5)

        ids = [i.id for i in instances]
        waiter = self.client.get_waiter('instance_running')
        waiter.wait(InstanceIds=ids)

        collection = self.ec2.instances.filter(InstanceIds=ids)
        instances = []
        for i, instance in enumerate(collection):
            instances.append(instance)
            if name:
                logger.debug("Tagging instance '%s'", instance.id)
                self.ec2.create_tags(Resources=[instance.id],
                                     Tags=[
                                         {
                                             'Key': 'Name',
                                             'Value': '{}-{}'.format(name, i)
                                         },
                                     ])

        return instances

    def destroy(self, ids):
        if ids is None or ids == []:
            raise DaskEc2Exception("Instances ids cannot be None or empty list")
        logger.debug("Terminating instances: %s", ids)
        self.ec2.instances.filter(InstanceIds=ids).terminate()
        waiter = self.client.get_waiter('instance_terminated')
        waiter.wait(InstanceIds=ids)
