from __future__ import absolute_import, print_function, division

import pytest

from moto import mock_ec2

from dask_ec2 import Instance
from dask_ec2.exceptions import DaskEc2Exception
from .utils import remotetest, cluster, driver


def test_instance():
    instance = Instance("0.0.0.0")
    assert instance.ip == "0.0.0.0"
    assert instance.port == 22

    instance = Instance("1.1.1.1", uid="i-123", port=2222, username="user", keypair="~/.ssh/key")
    assert instance.ip == "1.1.1.1"
    assert instance.uid == "i-123"
    assert instance.port == 2222
    assert instance.username == "user"
    assert instance.keypair == "~/.ssh/key"


def test_dict_serde():
    instance = Instance("1.1.1.1", uid="i-123", port=2222, username="user", keypair="~/.ssh/key")

    data = instance.to_dict()

    instance2 = Instance.from_dict(data)
    assert instance2.ip == "1.1.1.1"
    assert instance2.uid == "i-123"
    assert instance2.port == 2222
    assert instance2.username == "user"
    assert instance2.keypair == "~/.ssh/key"


@remotetest
def test_check_ssh(cluster):
    head = cluster.head
    assert head.check_ssh() == True


@mock_ec2
def test_from_boto3(driver):
    from dask_ec2.ec2 import DEFAULT_SG_GROUP_NAME
    name = "test_launch"
    ami = "ami-d05e75b8"
    instance_type = "m3.2xlarge"
    keyname = "mykey"
    keypair = None    # Skip check
    volume_type = "gp2"
    volume_size = 500
    security_group = "another-sg"

    driver.ec2.create_key_pair(KeyName=keyname)
    instances = driver.launch(name=name,
                              image_id=ami,
                              instance_type=instance_type,
                              count=1,
                              keyname=keyname,
                              security_group_name=DEFAULT_SG_GROUP_NAME,
                              volume_type=volume_type,
                              volume_size=volume_size,
                              keypair=keypair,
                              check_ami=False)

    instance = Instance.from_boto3_instance(instances[0])
