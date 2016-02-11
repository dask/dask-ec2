from __future__ import print_function, division, absolute_import

import time
import logging

import paramiko
import boto3
from botocore.exceptions import ClientError

from dec2.exceptions import DEC2Exception


logger = logging.getLogger(__name__)

DEFAULT_SG_GROUP_NAME = "dec2-default"


class EC2(object):

    def __init__(self, region):
        self.ec2 = boto3.resource('ec2', region_name=region)
        self.client = boto3.client('ec2', region_name=region)

    def check_keyname(self, keyname):
        try:
            key_pair = self.client.describe_key_pairs(KeyNames=[keyname])
            _ = [i for i in key_pair]
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "InvalidKeyPair.NotFound":
                raise DEC2Exception("The keyname '%s' does not exist, please create it in the EC2 console" % keyname)
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
        """Checks if the security groups exists, creates the default one if not
        """
        try:
            collection = self.ec2.security_groups.filter(GroupNames=[security_group])
            _ = [i for i in collection]
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if (error_code == "InvalidGroup.NotFound" and
               security_group == DEFAULT_SG_GROUP_NAME):
                logger.debug("Default security group '%s' not found, creating it", DEFAULT_SG_GROUP_NAME)
                self.create_default_sg()
            else:
                raise DEC2Exception("Security group '%s' not found, please create or use the default '%s'" % (security_group, DEFAULT_SG_GROUP_NAME))

    def create_default_sg(self):
        """Create the default security group
        """
        try:
            response = self.client.create_security_group(
                GroupName=DEFAULT_SG_GROUP_NAME,
                Description="Default security group for dec2",
            )
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "InvalidGroup.Duplicate":
                logger.debug("Default security group already exists")
            else:
                raise e

        logger.debug("Setting up default values for default security group")
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
            },
            {
                'IpProtocol': 'udp',
                'FromPort': 0,
                'ToPort': 65535,
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

    def get_security_group_ids(self, security_groups):
        """Get the security group ids for the security group names on
        `self.security_groups`
        """
        collection = self.ec2.security_groups.filter(GroupNames=security_groups)
        return [i.id for i in collection]

    def launch(self, name, image_id, instance_type, count, keyname,
                 security_group=DEFAULT_SG_GROUP_NAME, volume_type='gp2',
                 volume_size=500, keypair=None):
        self.check_keyname(keyname)
        if keypair:
            self.check_keypair(keyname, keypair)
        self.check_sg(security_group)
        return
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

        instances = self.ec2.create_instances(
            ImageId = image_id,
            KeyName = keyname,
            MinCount = count,
            MaxCount = count,
            InstanceType = instance_type,
            SecurityGroups = [security_group],
            SecurityGroupIds = self.get_security_group_ids([security_group]),
            BlockDeviceMappings = device_map,
        )
        time.sleep(5)

        ids = [i.id for i in instances]
        waiter = self.client.get_waiter('instance_running')
        waiter.wait(InstanceIds=ids)

        collection = self.ec2.instances.filter(InstanceIds=ids)
        instances = []
        for i, instance in enumerate(collection):
            instances.append(instance)
            if name:
                self.ec2.create_tags(
                    Resources=[instance.id],
                    Tags=[
                        {
                            'Key': 'Name',
                            'Value': '{}-{}'.format(name, i)
                        },
                    ]
                )

        return instances

    def destroy(self, ids):
        if ids is None or ids == []:
            raise DEC2Exception("Instances ids cannot be none or empty list")
        self.ec2.instances.filter(InstanceIds=ids).terminate()
        waiter = self.client.get_waiter('instance_terminated')
        waiter.wait(InstanceIds=ids)
