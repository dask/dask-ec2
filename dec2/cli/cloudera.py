import sys

import click

from .main import cli, print_state
from ..cluster import Cluster


@cli.group("cloudera-manager", invoke_without_command=True, short_help="Cloudera manager options")
@click.pass_context
@click.option("--file",
              "filepath",
              type=click.Path(exists=True),
              default="cluster.yaml",
              show_default=True,
              required=False,
              help="Filepath to the instances metadata")
def cloudera(ctx, filepath):
    if ctx.invoked_subcommand is None:
        ctx.invoke(cloudera_install, filepath=filepath)


@cloudera.command("install", short_help="Start a cloudera manager cluster")
@click.pass_context
@click.option("--file",
              "filepath",
              type=click.Path(exists=True),
              default="cluster.yaml",
              show_default=True,
              required=False,
              help="Filepath to the instances metadata")
def cloudera_install(ctx, filepath):
    cluster = Cluster.from_filepath(filepath)
    click.echo("Installing Cloudera Manager")
    cluster.pepper.local("node-0", "grains.append", ["roles", "cloudera.manager.server"])
    cluster.pepper.local("node-*", "grains.append", ["roles", "cloudera.manager.agent"])
    output = cluster.pepper.local("node-*", "state.sls", ["cloudera.manager.cluster"])
    print_state(output)


@cloudera.command("open", short_help="Open the cloudera manager URL")
@click.pass_context
@click.option("--file",
              "filepath",
              type=click.Path(exists=True),
              default="cluster.yaml",
              show_default=True,
              required=False,
              help="Filepath to the instances metadata")
def cloudera_open(ctx, filepath):
    cluster = Cluster.from_filepath(filepath)
    import webbrowser
    url = 'http://%s:7180' % cluster.instances[0].ip
    webbrowser.open(url, new=2)
