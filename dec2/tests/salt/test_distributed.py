from __future__ import absolute_import, print_function, division

import pytest

requests = pytest.importorskip("distributed")

from utils import remotetest, cluster, invoke, assert_all_true


# def setup_module(module):
#     utils.invoke('dask-distributed', 'install')


@remotetest
def test_dask(cluster):
    response = cluster.salt_call("*", "state.sls", ["dask.distributed"])["return"][0]
    assert_all_true(response)
