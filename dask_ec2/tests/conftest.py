from __future__ import absolute_import

import os
import pytest


@pytest.yield_fixture(scope="module")
def driver():
    from dask_ec2.ec2 import EC2
    driver = EC2(region="us-east-1", default_vpc=False, default_subnet=False, test=False)

    yield driver


@pytest.yield_fixture(scope='module')
def cluster():
    from dask_ec2 import Cluster
    clusterfile = os.environ['TEST_CLUSTERFILE']
    yield Cluster.from_filepath(clusterfile)
