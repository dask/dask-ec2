import sys

import click

from .main import cli, print_state
from ..cluster import Cluster
from ..salt import upload_pillar


@cli.group('dask-distributed', invoke_without_command=True, short_help='dask.distributed option')
@click.option("--file",
              "filepath",
              type=click.Path(exists=True),
              default="cluster.yaml",
              show_default=True,
              required=False,
              help="Filepath to the instances metadata")
@click.option("--nprocs",
              default=1,
              show_default=True,
              required=False,
              help="Number of processes per worker")
@click.option("--source/--no-source",
              is_flag=True,
              default=False,
              show_default=True,
              help="Install Dask/Distributed from git master")
@click.pass_context
def dask(ctx, filepath, nprocs, source):
    if ctx.invoked_subcommand is None:
        ctx.invoke(dask_install, filepath=filepath, nprocs=nprocs, source=source)


@dask.command("install", short_help="Start a dask.distributed cluster")
@click.pass_context
@click.option("--file",
              "filepath",
              type=click.Path(exists=True),
              default="cluster.yaml",
              show_default=True,
              required=False,
              help="Filepath to the instances metadata")
@click.option("--shell/--no-shell",
              is_flag=True,
              default=False,
              show_default=True,
              help="Start or not a python shell when installation is finished")
@click.option("--nprocs",
              default=1,
              show_default=True,
              required=False,
              help="Number of processes per worker")
@click.option("--source/--no-source",
              is_flag=True,
              default=False,
              show_default=True,
              help="Install Dask/Distributed from git master")
def dask_install(ctx, filepath, shell, nprocs, source):
    cluster = Cluster.from_filepath(filepath)
    scheduler_public_ip = cluster.instances[0].ip
    upload_pillar(cluster, "dask.sls", {"dask": {
                                            "scheduler_public_ip": scheduler_public_ip,
                                            "source_install": source,
                                            "dask-worker": {
                                                "nprocs": nprocs
                                            }
                                        }})

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
    click.echo("")
    ctx.invoke(dask_address, filepath=filepath)

    if shell:
        click.echo("Starting python shell")
        ctx.invoke(dask_shell, filepath=filepath)


@dask.command("address", short_help="Print the address to the dask.distributed cluster")
@click.pass_context
@click.option("--file",
              "filepath",
              type=click.Path(exists=True),
              default="cluster.yaml",
              show_default=True,
              required=False,
              help="Filepath to the instances metadata")
def dask_address(ctx, filepath):
    cluster = Cluster.from_filepath(filepath)
    address = cluster.instances[0].ip
    click.echo("""

Addresses
---------
Web Interface:    http://{0}:8787/status
TCP Interface:           {0}:8786

To connect from the cluster
---------------------------

dask-ec2 ssh  # ssh into head node
ipython  # start ipython shell

from dask.distributed import Client, progress
c = Client(127.0.0.1:8786')  # Connect to scheduler running on the head node

To connect locally
------------------

Note: this requires you to have identical environments on your local machine and cluster.

ipython  # start ipython shell

from dask.distributed import Client, progress
e = Client('{0}:8786')  # Connect to scheduler running on the head node

To destroy
----------

dask-ec2 destroy""".format(address).lstrip())


@dask.command(
    "shell",
    short_help=
    "Open a python (ipython if available) shell connected to the dask.distributed cluster")
@click.pass_context
@click.option("--file",
              "filepath",
              type=click.Path(exists=True),
              default="cluster.yaml",
              show_default=True,
              required=False,
              help="Filepath to the instances metadata")
def dask_shell(ctx, filepath):
    try:
        import distributed
    except:
        click.echo("ERROR: `distributed` package not found, not starting the python shell",
                   err=True)
        sys.exit(1)
    try:
        import IPython
        shell = "ipython"
    except:
        shell = "python"
    import os
    import subprocess
    import dask_ec2
    cluster = Cluster.from_filepath(filepath)
    address = "{}:{}".format(cluster.instances[0].ip, 8786)
    os.environ["DISTRIBUTED_ADDRESS"] = address
    dask_ec2_src = os.path.realpath(os.path.dirname(dask_ec2.__file__))
    dask_shell_py = os.path.join(dask_ec2_src, "cli", "dask_shell.py")
    cmd = [shell, "-i", dask_shell_py]
    subprocess.call(cmd)


@dask.command(
    "ui",
    short_help=
    "Open a web browser pointing to the Dask UI")
@click.pass_context
@click.option("--file",
              "filepath",
              type=click.Path(exists=True),
              default="cluster.yaml",
              show_default=True,
              required=False,
              help="Filepath to the instances metadata")
def open_ui(ctx, filepath):
    import webbrowser
    cluster = Cluster.from_filepath(filepath)
    address = "{}:{}/status".format(cluster.instances[0].ip, 8787)
    webbrowser.open(address, new=2)
