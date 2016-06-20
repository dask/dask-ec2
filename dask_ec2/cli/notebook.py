import sys

import click

from .main import cli, print_state
from ..cluster import Cluster
from ..salt import upload_pillar

@cli.group('notebook', invoke_without_command=True, short_help='Provision the Jupyter notebook')
@click.pass_context
@click.option("--file",
              "filepath",
              type=click.Path(exists=True),
              envvar="CLUSTERFILE",
              default="cluster.yaml",
              show_default=True,
              required=False,
              help="Filepath to the instances metadata")
def notebook(ctx, filepath):
    if ctx.invoked_subcommand is None:
        ctx.invoke(notebook_install, filepath=filepath)


@notebook.command("install", short_help='Provision the Jupyter notebook')
@click.pass_context
def notebook_install(ctx, filepath):
    click.echo("Installing Jupyter notebook on the head node")
    cluster = Cluster.from_filepath(filepath)
    output = cluster.salt_call("*", "state.sls", ["jupyter.notebook"])
    response = print_state(output)
    if not response.aggregated_success():
        sys.exit(1)
    click.echo("Jupyter notebook available at http://%s:8888/" %
               cluster.instances[0].ip)


@notebook.command("open", short_help="Open a web browser pointing to the Notebook UI")
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
    address = "{}:{}".format(cluster.instances[0].ip, 8888)
    webbrowser.open(address, new=2)
