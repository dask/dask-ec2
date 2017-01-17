from __future__ import print_function, division, absolute_import

import time
import logging

import boto3
from botocore.exceptions import ClientError, WaiterError

from dask_ec2.exceptions import DaskEc2Exception

logger = logging.getLogger(__name__)

DEFAULT_SG_GROUP_NAME = "dask-ec2-default"


class EC2(object):

    def __init__(self, region, vpc_id=None, subnet_id=None, default_vpc=True,
                 default_subnet=True, iaminstance_name=None, test=True):
        self.ec2 = boto3.resource("ec2", region_name=region)
        self.client = boto3.client("ec2", region_name=region)

        self.vpc_id = self.get_default_vpc() if default_vpc else vpc_id
        self.subnet_id = self.get_default_subnet() if default_subnet else subnet_id
        self.iaminstance_name = iaminstance_name

        if test:
            collection = self.ec2.instances.filter(Filters=[{"Name": "instance-state-name", "Values": ["running"]}])
            _ = list(collection)

    def get_default_vpc(self):
        """
        Get the default VPC of the account.

        Raises
        ------
            If there is not a default VPC
        """
        logger.debug("Searching for default VPC")
        for vpc in self.ec2.vpcs.all():
            if vpc.is_default:
                logger.debug("Default VPC found - Using VPC ID: %s", vpc.id)
                return vpc.id
        raise DaskEc2Exception("There is no default VPC, please pass VPC ID")

    def get_default_subnet(self, availability_zone=None):
        """
        Get the default subnet on the VPC ID.

        Raises
        ------
            If there is not a default subnet on the VPC
        """
        logger.debug("Searching for default subnet in VPC %s", self.vpc_id)
        for vpc in self.ec2.vpcs.all():
            if vpc.id == self.vpc_id:
                for subnet in vpc.subnets.all():
                    if availability_zone is None and subnet.default_for_az:
                        logger.debug("Default subnet found - Using Subnet ID: %s", subnet.id)
                        return subnet.id
                    else:
                        if subnet.availability_zone == availability_zone and subnet.default_for_az:
                            logger.debug("Default subnet found - Using Subnet ID: %s", subnet.id)
                            return subnet.id
        raise DaskEc2Exception("There is no default subnet on VPC %s, please pass a subnet ID" % self.vpc_id)

    def check_keyname(self, keyname):
        """Checks that a keyname exists on the EC2 account"

        Raises
        ------
            DaskEc2Exception if the keyname doesn't exists
        """
        logger.debug("Checking that keyname '%s' exists on EC2", keyname)
        try:
            key_pair = self.client.describe_key_pairs(KeyNames=[keyname])
            _ = [i for i in key_pair]
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "InvalidKeyPair.NotFound":
                raise DaskEc2Exception("The keyname '%s' does not exist, please create it in the EC2 console" % keyname)
            else:
                raise e

    def get_security_groups(self, security_group_name):
        """Get the security group (if exists) in the VPC ID

        Parameters
        ----------
        security_group_name : str
        """
        logger.debug("Getting all security groups and filtering by VPC ID %s and name %s", self.vpc_id,
                     security_group_name)
        collection = self.ec2.security_groups.all()
        matches = [i for i in collection]
        if self.vpc_id is not None:
            matches = [m for m in matches if m.vpc_id == self.vpc_id and m.group_name == security_group_name]
        else:
            matches = [m for m in matches if m.group_name == security_group_name]
        logger.debug("Found Security groups: %s", matches)
        return matches

    def get_security_groups_ids(self, security_groups):
        """Get the security group ids (if exists) for the security group names in the VPC
        """
        return [i.id for i in self.get_security_groups(security_groups)]

    def check_sg(self, security_group):
        """Checks if the security groups exists in the EC2 account
        If security_group is the default one it will create it.
        """
        logger.debug("Checking that security group '%s' exists on EC2", security_group)
        try:
            sg = self.get_security_groups(security_group)
            if not sg:
                if security_group == DEFAULT_SG_GROUP_NAME:
                    logger.debug("Default security group '%s' not found, creating it", DEFAULT_SG_GROUP_NAME)
                    self.create_default_sg()
                else:
                    raise DaskEc2Exception("Security group '%s' not found, please create or use the default '%s'" %
                                           (security_group, DEFAULT_SG_GROUP_NAME))
        except ClientError as e:
            raise DaskEc2Exception("Security group '%s' not found, please create or use the default '%s'" %
                                   (security_group, DEFAULT_SG_GROUP_NAME))

    def create_default_sg(self):
        """Create the default security group with very open settings.
        """
        logger.debug("Creating default (very open) security group '%s' on VPC %s", DEFAULT_SG_GROUP_NAME, self.vpc_id)
        try:
            if self.vpc_id is not None:
                _ = self.client.create_security_group(GroupName=DEFAULT_SG_GROUP_NAME,
                                                      Description="Default security group for adam",
                                                      VpcId=self.vpc_id)
            else:
                _ = self.client.create_security_group(GroupName=DEFAULT_SG_GROUP_NAME,
                                                      Description="Default security group for adam")
                print(_)
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "InvalidGroup.Duplicate":
                logger.debug("Default security group already exists")
            else:
                raise e

        logger.debug("Setting up default values for the '%s' security group", DEFAULT_SG_GROUP_NAME)
        security_group = self.get_security_groups(DEFAULT_SG_GROUP_NAME)[0]

        IpPermissions = [
            {
                "IpProtocol": "tcp",
                "FromPort": 0,
                "ToPort": 65535,
                "IpRanges": [
                    {
                        "CidrIp": "0.0.0.0/0"
                    },
                ],
            }, {
                "IpProtocol": "udp",
                "FromPort": 0,
                "ToPort": 65535,
                "IpRanges": [
                    {
                        "CidrIp": "0.0.0.0/0"
                    },
                ],
            }, {
                "IpProtocol": "icmp",
                "FromPort": -1,
                "ToPort": -1,
                "IpRanges": [
                    {
                        "CidrIp": "0.0.0.0/0"
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

    def check_image_is_ebs(self, image_id):
        """Check if AMI is EBS based and raises an exception if not
        """
        images = self.client.describe_images(ImageIds=[image_id])
        image = images["Images"][0]

        root_type = image["RootDeviceType"]
        if root_type != "ebs":
            raise DaskEc2Exception("The AMI {} Root Device Type is not EBS. Only EBS Root Device AMI are supported.".format(
                image_id))

    def launch(self, name, image_id, instance_type, count, keyname,
               security_group_name=DEFAULT_SG_GROUP_NAME,
               security_group_id=None,
               volume_type="gp2",
               volume_size=500,
               keypair=None,
               tags=None,
               check_ami=True):
        tags = tags or []
        self.check_keyname(keyname)
        if check_ami:
            self.check_image_is_ebs(image_id)
        self.check_sg(security_group_name)

        device_map = [
            {
                "DeviceName": "/dev/sda1",
                "Ebs": {
                    "VolumeSize": volume_size,
                    "DeleteOnTermination": True,
                    "VolumeType": volume_type,
                },
            },
        ]

        if security_group_id is not None:
            security_groups_ids = [security_group_id]
        else:
            security_groups_ids = self.get_security_groups_ids(security_group_name)

        logger.debug("Creating %i instances on EC2", count)
        kwargs = dict(ImageId=image_id,
                      KeyName=keyname,
                      MinCount=count,
                      MaxCount=count,
                      InstanceType=instance_type,
                      SecurityGroupIds=self.get_security_groups_ids(security_group_name),
                      BlockDeviceMappings=device_map)
        if self.subnet_id is not None and self.subnet_id != "":
            kwargs['SubnetId'] = self.subnet_id
        if self.iaminstance_name is not None and self.iaminstance_name != "":
            kwargs['IamInstanceProfile'] = {'Name': self.iaminstance_name}
        instances = self.ec2.create_instances(**kwargs)

        time.sleep(5)

        ids = [i.id for i in instances]
        waiter = self.client.get_waiter("instance_running")
        try:
            waiter.wait(InstanceIds=ids)
        except WaiterError:
            raise DaskEc2Exception(
                "An unexpected error occurred when launching the requested instances. Refer to the AWS Management Console for more information.")

        collection = self.ec2.instances.filter(InstanceIds=ids)
        instances = []
        for i, instance in enumerate(collection):
            instances.append(instance)
            if name:
                logger.debug("Tagging instance '%s'", instance.id)
                tags_ = [{"Key": "Name", "Value": "{0}-{1}".format(name, i)}]
                for tag_pair in tags:
                    parts = tag_pair.split(":")
                    if len(parts) == 2:
                        key = parts[0]
                        value = parts[1]
                    else:
                        key = "Tag"
                        value = tag_pair
                    tags_.append({"Key": key, "Value": value})
                self.ec2.create_tags(Resources=[instance.id], Tags=tags_)

        return instances

    def destroy(self, ids):
        """Terminate a set of EC2 instances by ID

        Parameters
        ----------
        ids : list of strings
            The EC2 ids of the instances that should be terminated
        """
        if ids is None or ids == []:
            raise DaskEc2Exception("Instances ids cannot be None or empty list")
        logger.debug("Terminating instances: %s", ids)
        self.ec2.instances.filter(InstanceIds=ids).terminate()
        waiter = self.client.get_waiter("instance_terminated")
        waiter.wait(InstanceIds=ids)
