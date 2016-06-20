from __future__ import absolute_import, print_function, division

import pytest

from ..utils import remotetest, cluster, invoke, assert_all_true


@remotetest
def test_ssh(cluster):
    response = cluster.check_ssh()
    assert len(response) == len(cluster.instances)
    for address, status in response.items():
        assert status == True


@remotetest
@pytest.mark.skip(reason="test is broken")
def test_provision_salt(cluster):
    invoke("provision")
    response = cluster.salt_call("*", "test.ping")["return"][0]
    assert len(response) == 2
    for address, status in response.items():
        assert status == True
