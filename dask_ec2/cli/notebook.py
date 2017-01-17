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
@click.option("--file",
              "filepath",
              type=click.Path(exists=True),
              envvar="CLUSTERFILE",
              default="cluster.yaml",
              show_default=True,
              required=False,
              help="Filepath to the instances metadata")
@click.option("--password",
              default="jupyter",
              show_default=True,
              required=False,
              help="Password for Jupyter Notebook")
@click.pass_context
def notebook_install(ctx, filepath, password):
    click.echo("Installing Jupyter notebook on the head node")
    cluster = Cluster.from_filepath(filepath)

    upload_pillar(cluster, "jupyter.sls",
                  {"jupyter": {
                      "password": password
                    }
                  })

    # only install on head node
    output = cluster.salt_call("node-0", "state.sls", ["jupyter.notebook"])

    response = print_state(output)
    if not response.aggregated_success():
        print(output)
        click.echo(output)
        sys.exit(1)
    click.echo("Jupyter notebook available at http://%s:8888/ \nLogin with "
               "password: %s" %
               (cluster.head.ip, password))



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
    address = "{}:{}".format(cluster.head.ip, 8888)
    webbrowser.open(address, new=2)
