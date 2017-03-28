from __future__ import absolute_import, print_function, division

import pytest

from moto import mock_ec2

from dask_ec2.ec2 import DEFAULT_SG_GROUP_NAME
from dask_ec2.exceptions import DaskEc2Exception

# Some default values
name = "test_launch"
ami = "ami-d05e75b8"
instance_type = "m3.2xlarge"
count = 3
keyname = "mykey"
keypair = None  # Skip check
volume_type = "gp2"
volume_size = 500
security_group = "another-sg"
tags = ["key2:value2", "key1:value1"]


@mock_ec2
def test_get_default_vpc(driver):
    with pytest.raises(DaskEc2Exception) as e:
        driver.get_default_vpc()

    assert "There is no default VPC, please pass VPC ID" == str(e.value)


@mock_ec2
def test_get_default_subnet(driver):
    with pytest.raises(DaskEc2Exception) as e:
        driver.get_default_subnet()

    assert "There is no VPC, please pass VPC ID or assign a default VPC" == str(e.value)


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
                      check_ami=False,
                      tags=tags)

    assert ("The keyname 'mykey' does not exist, "
            "please create it in the EC2 console") == str(e.value)

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
                  check_ami=False,
                  tags=tags)

    collection = driver.ec2.instances.filter()
    instances = [i for i in collection]

    custom_tags = []
    for t in tags:
        k, v = t.split(":")
        custom_tags.append({"Value": v, "Key": k})
    for idx, inst in enumerate(instances):
        tags_ = [{"Value": "{0}-{1}".format(name, idx), "Key": "Name"}]
        tags_.extend(custom_tags)
        assert (len(inst.tags)) == 3
        assert (len(tags_)) == 3

        tags_dict = dict()
        # tags look like:
        # {'Value': 'value1', 'Key': 'key1'}
        for t in inst.tags:
            k = t['Key']
            v = t['Value']
            tags_dict[k] = v
        print(tags_dict)
        assert tags_dict['key1'] == "value1"
        assert tags_dict['key2'] == "value2"

    assert len(instances) == count


@mock_ec2
def test_create_default_security_group(driver):
    security_groups = driver.ec2.security_groups

    collection = security_groups.filter()
    sgs = [i for i in collection]
    assert len(sgs) == 1

    created_sg = driver.create_default_sg()
    collection = security_groups.filter()
    sgs = [i for i in collection]
    assert len(sgs) == 2

    collection = security_groups.filter(GroupNames=[DEFAULT_SG_GROUP_NAME])
    sgs = [i for i in collection]
    assert len(sgs) == 1

    default_sg = driver.ec2.SecurityGroup(created_sg.id)

    assert len(default_sg.ip_permissions) == 3
    ip_permission = default_sg.ip_permissions[0]
    assert ip_permission['FromPort'] == 0
    assert ip_permission['ToPort'] == 65535
    assert ip_permission['IpProtocol'] == 'tcp'
    assert ip_permission['IpRanges'] == [{'CidrIp': '0.0.0.0/0'}]

    assert len(default_sg.ip_permissions_egress) == 4
    ip_permission_egress = default_sg.ip_permissions_egress[1]
    assert ip_permission_egress['FromPort'] == 0
    assert ip_permission_egress['ToPort'] == 65535
    assert ip_permission_egress['IpProtocol'] == 'tcp'
    assert ip_permission_egress['IpRanges'] == [{'CidrIp': '0.0.0.0/0'}]


@mock_ec2
def test_check_sg(driver):
    collection = driver.ec2.security_groups.filter()
    sgs = [i for i in collection]
    assert len(sgs) == 1

    driver.check_sg(DEFAULT_SG_GROUP_NAME)
    # driver.check_sg("ANOTHER_FAKE_SG")

    with pytest.raises(DaskEc2Exception) as e:
        driver.check_sg("ANOTHER_FAKE_SG")

    assert ("Security group 'ANOTHER_FAKE_SG' not found, "
            "please create or use the default "
            "'dask-ec2-default'") == str(e.value)
