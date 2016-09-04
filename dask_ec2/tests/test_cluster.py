from __future__ import absolute_import, print_function, division

import pytest

from moto import mock_ec2

from dask_ec2 import Cluster, Instance
from dask_ec2.exceptions import DaskEc2Exception
from .utils import remotetest, cluster, driver


def test_cluster():
    cluster = Cluster()
    assert len(cluster.instances) == 0


def test_append_instance():
    cluster = Cluster()
    n = 5
    for i in range(n):
        instance = Instance(ip="%i" % i)
        cluster.append(instance)
    assert len(cluster.instances) == n

    assert cluster.head == cluster.instances[0]


def test_append_non_instance_type():
    cluster = Cluster()
    with pytest.raises(DaskEc2Exception) as excinfo:
        cluster.append({"wrong": "type"})


def test_set_username():
    cluster = Cluster()
    n = 5
    for i in range(n):
        instance = Instance(ip="%i" % i)
        cluster.append(instance)
        assert cluster.instances[i].username is None

    user = "ubuntu"
    cluster.set_username(user)

    for i in range(n):
        assert cluster.instances[i].username == user


def test_set_keypair():
    cluster = Cluster()
    n = 5
    for i in range(n):
        instance = Instance(ip="%i" % i)
        cluster.append(instance)
        assert cluster.instances[i].keypair is None

    pkey = "ubuntu"
    cluster.set_keypair(pkey)

    for i in range(n):
        assert cluster.instances[i].keypair == pkey


def test_dict_serde():
    cluster = Cluster()
    username = "user"
    keypair="~/.ssh/key"
    n = 5
    for i in range(n):
        instance = Instance(uid="%i" % i, ip="{0}.{0}.{0}.{0}".format(i), username=username, keypair=keypair)
        cluster.append(instance)

    data = cluster.to_dict()
    cluster2 = Cluster.from_dict(data)
    assert len(cluster2.instances) == n

    for i, instance in enumerate(cluster2.instances):
        assert instance.uid == "%i" % i
        assert instance.ip == "{0}.{0}.{0}.{0}".format(i)
        assert instance.username == username
        assert instance.keypair == keypair


def test_from_filepath(request, tmpdir):
    import os
    testname = request.node.name
    tempdir = tmpdir.mkdir("rootdir")
    fpath = os.path.join(tempdir.strpath, "{}.yaml".format(testname))

    cluster = Cluster()
    username = "user"
    keypair="~/.ssh/key"
    n = 5
    for i in range(n):
        instance = Instance(uid="%i" % i, ip="{0}.{0}.{0}.{0}".format(i), username=username, keypair=keypair)
        cluster.append(instance)

    cluster.to_file(fpath)

    cluster2 = Cluster.from_filepath(fpath)

    assert len(cluster2.instances) == n
    assert len(cluster.instances) == len(cluster2.instances)
    for i, instance in enumerate(cluster2.instances):
        assert instance.uid == "%i" % i
        assert instance.ip == "{0}.{0}.{0}.{0}".format(i)
        assert instance.username == username
        assert instance.keypair == keypair


@remotetest
def test_check_ssh(cluster):
    response = cluster.check_ssh()
    assert len(response) == len(cluster.instances)
    for address, status in response.items():
        assert status is True


@mock_ec2
def test_from_boto3(driver):
    from dask_ec2.ec2 import DEFAULT_SG_GROUP_NAME
    name = "test_launch"
    ami = "ami-d05e75b8"
    instance_type = "m3.2xlarge"
    count = 5
    keyname = "mykey"
    keypair = None    # Skip check
    volume_type = "gp2"
    volume_size = 500
    # security_group = "another-sg"

    driver.ec2.create_key_pair(KeyName=keyname)
    instances = driver.launch(name=name,
                              image_id=ami,
                              instance_type=instance_type,
                              count=count,
                              keyname=keyname,
                              security_group_name=DEFAULT_SG_GROUP_NAME,
                              volume_type=volume_type,
                              volume_size=volume_size,
                              keypair=keypair,
                              check_ami=False)

    instance = Cluster.from_boto3_instances(instances)
