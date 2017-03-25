from __future__ import absolute_import, print_function, division

import os
import pytest

from click.testing import CliRunner

from dask_ec2.cli.main import cli

remotetest = pytest.mark.skipif(
    'TEST_CLUSTERFILE' not in os.environ, reason="Environment variable 'TEST_CLUSTERFILE' is required")


def invoke(*args):
    clusterfile = os.environ['TEST_CLUSTERFILE']
    args = list(args)
    args.extend(['--file', clusterfile])
    runner = CliRunner()
    return runner.invoke(cli, args, catch_exceptions=False, input=os.devnull)


def assert_all_true(salt_output, none_is_ok=False):
    for minion_id, minion_states in salt_output.items():
        for state_id, value in minion_states.items():
            if none_is_ok:
                assert value['result'] is not False, (state_id, value)
            else:
                assert value['result'] is True, (state_id, value)
