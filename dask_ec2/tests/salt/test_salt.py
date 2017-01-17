from __future__ import absolute_import, print_function, division

import pytest

from ..utils import remotetest, cluster, invoke


@remotetest
def test_ssh(cluster):
    response = cluster.check_ssh()
    assert len(response) == len(cluster.instances)
    for address, status in response.items():
        assert status is True


@remotetest
def test_provision_salt(cluster):
    result = invoke("provision")
    if result.exit_code != 0:
        print(result.output_bytes)
    assert result.exit_code == 0

@remotetest
def test_salt_ping(cluster):
    response = cluster.salt_call("*", "test.ping")
    print(response)
    response = response["return"][0]
    assert len(response) == 2
    for address, status in response.items():
        assert status is True
