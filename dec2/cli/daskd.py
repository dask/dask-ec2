import sys

import click

from .main import cli, print_state
from ..cluster import Cluster


@cli.group('dask-distributed', invoke_without_command=True, short_help='dask.distributed option')
@click.option("--file", "filepath", type=click.Path(exists=True), default="cluster.yaml", show_default=True, required=False, help="Filepath to the instances metadata")
@click.pass_context
def dask(ctx, filepath):
    if ctx.invoked_subcommand is None:
        ctx.invoke(dask_install, filepath=filepath)


@dask.command("install", short_help="Start a dask.distributed cluster")
@click.pass_context
@click.option("--file", "filepath", type=click.Path(exists=True), default="cluster.yaml", show_default=True, required=False, help="Filepath to the instances metadata")
def dask_install(ctx, filepath):
    cluster = Cluster.from_filepath(filepath)

    click.echo("Installing scheduler")
    cluster.pepper.local("node-0", "grains.append", ["roles", "dask.distributed.scheduler"])
    output = cluster.salt_call("node-0", "state.sls", ["dask.distributed.scheduler"])
    response = print_state(output)
    if not response.aggregated_success():
        sys.exit(1)

    click.echo("Installing workers")
    cluster.pepper.local("node-[1-9]*", "grains.append", ["roles", "dask.distributed.worker"])
    output = cluster.salt_call("node-[1-9]*", "state.sls", ["dask.distributed.worker"])
    response = print_state(output)
    if not response.aggregated_success():
        sys.exit(1)

    click.echo("Dask.Distributed Installation succeeded")
    ctx.invoke(dask_address, filepath=filepath)


@dask.command("address", short_help="Print the address to the dask.distributed cluster")
@click.pass_context
@click.option("--file", "filepath", type=click.Path(exists=True), default="cluster.yaml", show_default=True, required=False, help="Filepath to the instances metadata")
def dask_address(ctx, filepath):
    cluster = Cluster.from_filepath(filepath)
    address = "{}:{}".format(cluster.instances[0].ip, 8786)
    click.echo("Scheduler Address: {}".format(address))


@dask.command("shell", short_help="Open a python (ipython if available) shell connected to the dask.distributed cluster")
@click.pass_context
@click.option("--file", "filepath", type=click.Path(exists=True), default="cluster.yaml", show_default=True, required=False, help="Filepath to the instances metadata")
def dask_shell(ctx, filepath):
    try:
        import distributed
    except:
        click.echo("ERROR: `distributed` package not found, not starting the python shell", err=True)
        sys.exit(1)
    try:
        import IPython
        shell = "ipython"
    except:
        print('HSI')
        shell = "python"
    import os
    import subprocess
    import dec2
    cluster = Cluster.from_filepath(filepath)
    address = "{}:{}".format(cluster.instances[0].ip, 8786)
    os.environ["DISTRIBUTED_ADDRESS"] = address
    dec2_src = src_dir = os.path.realpath(os.path.dirname(dec2.__file__))
    dask_shell_py = os.path.join(dec2_src, "cli", "dask_shell.py")
    cmd = [shell, "-i", dask_shell_py]
    subprocess.call(cmd)
