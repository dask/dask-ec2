from __future__ import print_function, division, absolute_import

import logging

import boto3
from botocore.exceptions import ClientError

from dec2.exceptions import DEC2Exception


logger = logging.getLogger(__name__)

DEFAULT_SG_GROUP_NAME = "dec2-default"


class EC2(object):

    def __init__(self, image, instance_type, count, keyname,
                 security_groups=None, volume_type='gp2',
                 volume_size=500, name=None):
        self.image_id = image
        self.instance_type = instance_type
        self.count = count
        self.keyname = keyname
        self.security_groups = security_groups or []
        self.volume_type = volume_type
        self.volume_size = volume_size
        self.name = name

        self.ec2 = boto3.resource('ec2')
        self.client = boto3.client('ec2')
        self.waiter = self.client.get_waiter('instance_running')

    def check_keypair(self):
        try:
            key_pair = self.client.describe_key_pairs(KeyNames=[self.keyname])
            _ = [i for i in key_pair]
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "InvalidKeyPair.NotFound":
                raise DEC2Exception("The keyname '%s' does not exist, please create it in the EC2 console" % self.keyname)
            else:
                raise e

    def check_sg(self):
        """Checks if the security groups exists, creates the default one if not
        """
        try:
            collection = self.ec2.security_groups.filter(GroupNames=self.security_groups)
            _ = [i for i in collection]
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if (error_code == "InvalidGroup.NotFound" and
               self.security_groups[0] == DEFAULT_SG_GROUP_NAME):
                logger.debug("Default security group '%s' not found, creating it", DEFAULT_SG_GROUP_NAME)
                self.create_default_sg()
            else:
                raise DEC2Exception("Security group '%s' not found, please create or use the default '%s'" % (self.security_groups[0], DEFAULT_SG_GROUP_NAME))

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

    def get_security_group_ids(self):
        """Get the security group ids for the security group names on
        `self.security_groups`
        """
        collection = self.ec2.security_groups.filter(GroupNames=self.security_groups)
        return [i.id for i in collection]

    def launch(self):
        self.check_keypair()
        self.check_sg()
        # return
        device_map = [
            {
                # 'VirtualName': 'string',
                'DeviceName': '/dev/sda1',
                # 'NoDevice': 'string',
                'Ebs': {
                    # 'SnapshotId': 'string',
                    'VolumeSize': self.volume_size,
                    'DeleteOnTermination': True,
                    'VolumeType': self.volume_type,
                    # 'Iops': 123,
                    # 'Encrypted': False
                },
            },
        ]

        instances = self.ec2.create_instances(
            ImageId = self.image_id,
            KeyName = self.keyname,
            MinCount = self.count,
            MaxCount = self.count,
            InstanceType = self.instance_type,
            SecurityGroups = self.security_groups,
            SecurityGroupIds = self.get_security_group_ids(),
            BlockDeviceMappings = device_map,
        )

        ids = [i.id for i in instances]
        self.waiter.wait(InstanceIds=ids)

        collection = self.ec2.instances.filter(InstanceIds=ids)
        instances = []
        for i, instance in enumerate(collection):
            instances.append(instance)
            if self.name:
                self.ec2.create_tags(
                    Resources=[instance.id],
                    Tags=[
                        {
                            'Key': 'Name',
                            'Value': '{}-{}'.format(self.name, i)
                        },
                    ]
                )

        return instances
