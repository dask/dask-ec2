from __future__ import absolute_import, print_function, division

import pytest

from dask_ec2.utils import retry
from dask_ec2.exceptions import RetriesExceededException


@retry(wait=0)
def ok():
    return 35


@retry(wait=0)
def ok_with_args(*args, **kwargs):
    return args, kwargs


ATTEMPT = 0


@retry(wait=0, retries=10)
def fail_10():
    global ATTEMPT
    ATTEMPT += 1
    raise Exception
    return True


@retry(wait=0, catch=(NotImplementedError,))
def catch_NotImplementedException_raises_TypeError():
    raise TypeError
    return True


@retry(wait=0, catch=(NotImplementedError,))
def catch_NotImplementedException_raises_Exception():
    raise Exception
    return True


def test_ok():
    assert ok() == 35
    assert ok_with_args('pew', 123, kw='args') == (('pew', 123), {'kw': 'args'})


def test_fails_after_retries():
    with pytest.raises(RetriesExceededException):
        fail_10()
    assert ATTEMPT == 10


def test_raises_catch_correct_type():
    with pytest.raises(TypeError):
        catch_NotImplementedException_raises_TypeError()


def test_retry_raises_catch_fail():
    with pytest.raises(Exception):
        catch_NotImplementedException_raises_Exception()
