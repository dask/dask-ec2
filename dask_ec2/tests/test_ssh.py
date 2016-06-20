from __future__ import absolute_import, print_function, division

import pytest

from dask_ec2.ssh import SSHClient
from dask_ec2.exceptions import DaskEc2Exception
from .utils import remotetest, cluster


@remotetest
def test_ssh_ok_pkey_obj(cluster):
    import os
    import paramiko
    instance = cluster.head
    pkey = paramiko.RSAKey.from_private_key_file(os.path.expanduser(instance.keypair))
    client = SSHClient(host=instance.ip, username=instance.username, port=instance.port, password=None, pkey=pkey)


@remotetest
def test_wrong_pkey_type(cluster):
    instance = cluster.head
    pkey = {"wrong": "obj"}
    with pytest.raises(DaskEc2Exception) as excinfo:
        client = SSHClient(host=instance.ip, username=instance.username, port=instance.port, password=None, pkey=pkey)


@remotetest
def test_ssh_ok_password(cluster):
    instance = cluster.head
    password = "root"    # NOTE: this is a little bit hardcoded to docker setup
    client = SSHClient(host=instance.ip, username=instance.username, port=instance.port, password=password, pkey=None)
    reponse = client.exec_command("ls")
    client.close()


@remotetest
def test_ssh_fail_password(cluster):
    instance = cluster.head
    password = "root_not"    # NOTE: this is a little bit hardcoded to docker setup
    with pytest.raises(DaskEc2Exception) as excinfo:
        client = SSHClient(host=instance.ip, username=instance.username, port=instance.port, password=password, pkey=None)
    assert "Authentication Error" in str(excinfo.value)


@remotetest
def test_ssh_fail_user(cluster):
    client = cluster.head.ssh_client
    client.username = "FAKEUSER"
    with pytest.raises(DaskEc2Exception) as excinfo:
        client.connect()
    assert "Authentication Error" in str(excinfo.value)
    client.close()


@remotetest
def test_ssh_fail_host(cluster):
    client = cluster.head.ssh_client
    client.host = "1.1.1.1"
    client.timeout = 3    # so test runs faster
    with pytest.raises(DaskEc2Exception) as excinfo:
        client.connect()
    assert "Error connecting to host" in str(excinfo.value)
    assert "timed out" in str(excinfo.value)
    client.close()


@remotetest
def test_wrong_host(cluster):
    client = cluster.head.ssh_client
    client.host = "'WRONGHOST''"
    with pytest.raises(DaskEc2Exception) as excinfo:
        client.connect()
    assert "Unknown host" in str(excinfo.value)
    client.close()


@remotetest
def test_exec_command(cluster):
    client = cluster.head.ssh_client
    response = client.exec_command("whoami")
    assert response["exit_code"] == 0
    assert response["stdout"] == cluster.head.username
    client.close()


@remotetest
def test_exec_command_sudo(cluster, request):
    testname = request.node.name

    client = cluster.head.ssh_client
    response = client.exec_command("mkdir /{}".format(testname), sudo=True)
    assert response["exit_code"] == 0
    response = client.exec_command("test -d /{}".format(testname), sudo=True)
    assert response["exit_code"] == 0

    def fin():
        response = client.exec_command("rm -rf /{}".format(testname), sudo=True)
        assert response["exit_code"] == 0
        client.close()
    request.addfinalizer(fin)


@remotetest
def test_mkdir(cluster, request):
    import posixpath
    testname = request.node.name
    client = cluster.head.ssh_client

    dir1 = posixpath.join("/tmp", testname, "dir1")
    dir2 = posixpath.join(dir1, "dir2")
    dir3 = posixpath.join(dir2, "dir3")
    client.mkdir(dir3)
    assert client.dir_exists(dir1) == True
    assert client.dir_exists(dir2) == True
    assert client.dir_exists(dir3) == True

    assert client.dir_exists("test -d /FAKEFAKE") == False
    assert client.exec_command("test -d /FAKEFAKE")["exit_code"] == 1
    assert client.exec_command("test -d {}".format(dir1))["exit_code"] == 0
    assert client.exec_command("test -d {}".format(dir2))["exit_code"] == 0
    assert client.exec_command("test -d {}".format(dir3))["exit_code"] == 0

    # Calling mkdir multiple times is ok
    client.mkdir(dir3)
    client.mkdir(dir3)
    client.mkdir(dir3)

    def fin():
        response = client.exec_command("rm -rf /tmp/{}".format(testname), sudo=True)
        assert response["exit_code"] == 0
        client.close()
    request.addfinalizer(fin)


@remotetest
def test_put_file(cluster, tmpdir):
    client = cluster.head.ssh_client

    content = "content"
    f = tmpdir.join("upload1.txt")
    f.write(content)

    local = f.strpath
    remote = "/tmp/upload1.txt"

    client.put(local, remote, sudo=True)
    assert client.exec_command("test -e {}".format(remote))["exit_code"] == 0
    assert client.exec_command("cat {}".format(remote))["stdout"] == content


@remotetest
def test_put_dir(cluster, tmpdir, request):
    import posixpath
    testname = request.node.name
    client = cluster.head.ssh_client

    d1 = tmpdir.mkdir("rootdir")
    f1 = d1.join("upload1.txt")
    f1.write("content1")

    d2 = d1.mkdir("subdir")
    f2 = d2.join("upload2.txt")
    f2.write("content2")

    d3 = d2.mkdir("subsubdir")
    f3 = d3.join("upload3.txt")
    f3.write("content3")

    local = d1.strpath
    remote = "/tmp/{}".format(testname)
    client.put(local, remote, sudo=True)
    assert client.dir_exists(posixpath.join(remote)) == True
    assert client.dir_exists(posixpath.join(remote, "subdir")) == True
    assert client.dir_exists(posixpath.join(remote, "subdir", "subsubdir")) == True
    assert client.exec_command("test -e {}".format(posixpath.join(remote)))["exit_code"] == 0
    assert client.exec_command("cat {}".format(posixpath.join(remote, "upload1.txt")))["stdout"] == "content1"
    assert client.exec_command("cat {}".format(posixpath.join(remote, "subdir", "upload2.txt")))["stdout"] == "content2"
    assert client.exec_command("cat {}".format(posixpath.join(remote, "subdir", "subsubdir", "upload3.txt")))["stdout"] == "content3"

    def fin():
        response = client.exec_command("rm -rf /tmp/{}".format(testname), sudo=True)
        assert response["exit_code"] == 0
        client.close()
    request.addfinalizer(fin)
