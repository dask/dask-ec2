import pytest


@pytest.yield_fixture(scope="module")
def driver():
    from dec2.ec2 import EC2
    driver = EC2(region="us-east-1")
    yield driver
