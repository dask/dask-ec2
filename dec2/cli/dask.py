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
    output = cluster.pepper.local("node-0", "state.sls", ["dask.distributed.scheduler"])
    response = print_state(output)

    click.echo("Installing workers")
    cluster.pepper.local("node-[1-9]*", "grains.append", ["roles", "dask.distributed.worker"])
    output = cluster.pepper.local("node-[1-9]*", "state.sls", ["dask.distributed.worker"])
    response = print_state(output)

    ctx.invoke(dask_open, filepath=filepath)


@dask.command("open", short_help="Start a dask.distributed cluster")
@click.pass_context
@click.option("--file", "filepath", type=click.Path(exists=True), default="cluster.yaml", show_default=True, required=False, help="Filepath to the instances metadata")
def dask_open(ctx, filepath):
    cluster = Cluster.from_filepath(filepath)
    click.echo("Scheduler URL: {}:{}".format(cluster.instances[0].ip, 8786))
