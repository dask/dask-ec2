from __future__ import absolute_import, print_function, division

import pytest

from ..utils import remotetest, assert_all_true

requests = pytest.importorskip("distributed")

# def setup_module(module):
#     utils.invoke('dask-distributed', 'install')


@remotetest
def test_dask(cluster):
    output = cluster.salt_call("*", "state.sls", ["dask.distributed"])
    response = output["return"][0]
    assert_all_true(response)
