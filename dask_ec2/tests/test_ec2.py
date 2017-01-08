from __future__ import absolute_import, print_function, division

import pytest

from moto import mock_ec2

from dask_ec2.ec2 import DEFAULT_SG_GROUP_NAME
from dask_ec2.exceptions import DaskEc2Exception
from .utils import driver

# Some default values
name = "test_launch"
ami = "ami-d05e75b8"
instance_type = "m3.2xlarge"
count = 3
keyname = "mykey"
keypair = None    # Skip check
volume_type = "gp2"
volume_size = 500
security_group = "another-sg"


@mock_ec2
def test_launch_no_keyname(driver):
    with pytest.raises(DaskEc2Exception) as e:
        driver.launch(name=name,
                      image_id=ami,
                      instance_type=instance_type,
                      count=count,
                      keyname=keyname,
                      security_group_name=DEFAULT_SG_GROUP_NAME,
                      volume_type=volume_type,
                      volume_size=volume_size,
                      keypair=keypair,
                      check_ami=False)
    assert "The keyname 'mykey' does not exist, please create it in the EC2 console" == str(e.value)

    collection = driver.ec2.instances.filter()
    instances = [i for i in collection]
    assert len(instances) == 0

    driver.ec2.create_key_pair(KeyName=keyname)

    driver.launch(name=name,
                  image_id=ami,
                  instance_type=instance_type,
                  count=count,
                  keyname=keyname,
                  security_group_name=DEFAULT_SG_GROUP_NAME,
                  volume_type=volume_type,
                  volume_size=volume_size,
                  keypair=keypair,
                  check_ami=False)

    collection = driver.ec2.instances.filter()
    instances = [i for i in collection]
    assert len(instances) == count


@mock_ec2
def test_create_default_security_group(driver):
    collection = driver.ec2.security_groups.filter()
    sgs = [i for i in collection]
    assert len(sgs) == 1

    created_sg = driver.create_default_sg()
    collection = driver.ec2.security_groups.filter()
    sgs = [i for i in collection]
    assert len(sgs) == 2

    collection = driver.ec2.security_groups.filter(GroupNames=[DEFAULT_SG_GROUP_NAME])
    sgs = [i for i in collection]
    assert len(sgs) == 1

    default_sg = driver.ec2.SecurityGroup(created_sg.id)

    assert len(default_sg.ip_permissions) == 3
    assert default_sg.ip_permissions[0]['FromPort'] == 0
    assert default_sg.ip_permissions[0]['ToPort'] == 65535
    assert default_sg.ip_permissions[0]['IpProtocol'] == 'tcp'
    assert default_sg.ip_permissions[0]['IpRanges'] == [{'CidrIp': '0.0.0.0/0'}]

    assert len(default_sg.ip_permissions_egress) == 4
    assert default_sg.ip_permissions_egress[1]['FromPort'] == 0
    assert default_sg.ip_permissions_egress[1]['ToPort'] == 65535
    assert default_sg.ip_permissions_egress[1]['IpProtocol'] == 'tcp'
    assert default_sg.ip_permissions_egress[1]['IpRanges'] == [{'CidrIp': '0.0.0.0/0'}]


@mock_ec2
def test_check_sg(driver):
    collection = driver.ec2.security_groups.filter()
    sgs = [i for i in collection]
    assert len(sgs) == 1

    driver.check_sg(DEFAULT_SG_GROUP_NAME)
    # driver.check_sg("ANOTHER_FAKE_SG")

    with pytest.raises(DaskEc2Exception) as e:
        driver.check_sg("ANOTHER_FAKE_SG")
    assert "Security group 'ANOTHER_FAKE_SG' not found, please create or use the default 'dask-ec2-default'" == str(
        e.value)
