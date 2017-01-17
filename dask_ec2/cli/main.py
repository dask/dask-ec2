from __future__ import print_function, division, absolute_import

import sys
import click

from botocore.exceptions import ClientError

import dask_ec2
from ..salt import Response
from ..cluster import Cluster
from ..exceptions import DaskEc2Exception
from ..config import setup_logging
from .utils import Table


def start():
    import sys
    import logging
    import traceback

    try:
        setup_logging(logging.DEBUG)
        cli(obj={})
    except DaskEc2Exception as e:
        click.echo("ERROR: %s" % e, err=True)
        sys.exit(1)
    except ClientError as e:
        click.echo("Unexpected EC2 error: %s" % e, err=True)
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo(
            "Interrupted by Ctrl-C. One or more actions could be still running in the cluster")
        sys.exit(1)
    except Exception as e:
        click.echo(traceback.format_exc(), err=True)
        sys.exit(1)


CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(prog_name="dask-ec2", version=dask_ec2.__version__)
@click.pass_context
def cli(ctx):
    ctx.obj = {}


@cli.command(short_help="Launch instances")
@click.pass_context
@click.option("--keyname", required=True, help="Keyname on EC2 console")
@click.option("--keypair",
              required=True,
              type=click.Path(exists=True),
              help="Path to the keypair that matches the keyname")
@click.option("--name", required=False, default="dask-ec2-cluster", help="Tag name on EC2")
@click.option("--region-name",
              default="us-east-1",
              show_default=True,
              required=False,
              help="AWS region")
@click.option("--vpc-id", default=None, show_default=True, required=False, help="EC2 VPC ID")
@click.option("--subnet-id", default=None, show_default=True, required=False, help="EC2 Subnet ID on the VPC")
@click.option("--iaminstance-name", default=None, show_default=True, required=False, help="IAM Instance Name")
@click.option("--ami", default="ami-d05e75b8", show_default=True, required=False, help="EC2 AMI")
@click.option("--username",
              default="ubuntu",
              show_default=True,
              required=False,
              help="User to SSH to the AMI")
@click.option("--type",
              "instance_type",
              default="m3.2xlarge",
              show_default=True,
              required=False,
              help="EC2 Instance Type")
@click.option("--count", default=4, show_default=True, required=False, help="Number of nodes")
@click.option("--security-group",
              "security_group_name",
              default="dask-ec2-default",
              show_default=True,
              required=False,
              help="Security Group Name")
@click.option("--security-group-id",
              "security_group_id",
              default=None,
              show_default=True,
              required=False,
              help="Security Group ID (overwrites Security Group Name)")
@click.option("--volume-type",
              default="gp2",
              show_default=True,
              required=False,
              help="Root volume type")
@click.option("--volume-size",
              default=500,
              show_default=True,
              required=False,
              help="Root volume size (GB)")
@click.option("--file",
              "filepath",
              type=click.Path(),
              default="cluster.yaml",
              show_default=True,
              required=False,
              help="File to save the metadata")
@click.option("--provision/--no-provision",
              "_provision",
              default=True,
              show_default=True,
              required=False,
              help="Provision salt on the nodes")
@click.option("--anaconda/--no-anaconda", "anaconda_",
              is_flag=True,
              default=True,
              show_default=True,
              help="Bootstrap anaconda")
@click.option("--dask/--no-dask",
              "dask",
              default=True,
              show_default=True,
              required=False,
              help="Install Dask.Distributed in the cluster")
@click.option("--notebook/--no-notebook",
              "notebook",
              default=True,
              show_default=True,
              required=False,
              help="Start a Jupyter Notebook in the head node")
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
def up(ctx, name, keyname, keypair, region_name, vpc_id, subnet_id,
       iaminstance_name, ami, username, instance_type, count,
       security_group_name, security_group_id, volume_type, volume_size, filepath, _provision, anaconda_,
       dask, notebook, nprocs, source):
    import os
    import yaml
    from ..ec2 import EC2

    if os.path.exists(filepath):
        if not click.confirm("A file named {} already exists, proceding will overwrite this file. Continue?".format(filepath)):
            click.echo("Not doing anything")
            sys.exit(0)

    driver = EC2(region=region_name, vpc_id=vpc_id, subnet_id=subnet_id,
                 default_vpc=not(vpc_id), default_subnet=not(subnet_id),
                 iaminstance_name=iaminstance_name)
    click.echo("Launching nodes")
    instances = driver.launch(name=name,
                              image_id=ami,
                              instance_type=instance_type,
                              count=count,
                              keyname=keyname,
                              security_group_name=security_group_name,
                              security_group_id=security_group_id,
                              volume_type=volume_type,
                              volume_size=volume_size,
                              keypair=keypair)

    cluster = Cluster.from_boto3_instances(instances)
    cluster.set_username(username)
    cluster.set_keypair(keypair)
    with open(filepath, "w") as f:
        yaml.safe_dump(cluster.to_dict(), f, default_flow_style=False)

    if _provision:
        ctx.invoke(provision, filepath=filepath, anaconda_=anaconda_, dask=dask,
                   notebook=notebook, nprocs=nprocs, source=source)


@cli.command(short_help="Destroy cluster")
@click.pass_context
@click.option("--file",
              "filepath",
              type=click.Path(exists=True),
              envvar="CLUSTERFILE",
              default="cluster.yaml",
              show_default=True,
              required=False,
              help="Filepath to the instances metadata")
@click.option('--yes', '-y', is_flag=True, default=False, help='Answers yes to questions')
@click.option("--region-name",
              default="us-east-1",
              show_default=True,
              required=False,
              help="AWS region")
def destroy(ctx, filepath, yes, region_name):
    import os
    from ..ec2 import EC2
    cluster = Cluster.from_filepath(filepath)

    question = 'Are you sure you want to destroy the cluster?'
    if yes or click.confirm(question):
        driver = EC2(region=region_name, default_vpc=False, default_subnet=False)
        #needed if there is no default vpc or subnet
        ids = [i.uid for i in cluster.instances]
        click.echo("Terminating instances")
        driver.destroy(ids)

        question = "Do you want to remove the `{}` file?".format(filepath)
        if yes or click.confirm(question):
            os.remove(filepath)


@cli.command(short_help="SSH to one of the node. 0-index")
@click.pass_context
@click.argument('node', required=False, default=0)
@click.option("--file",
              "filepath",
              type=click.Path(exists=True),
              envvar="CLUSTERFILE",
              default="cluster.yaml",
              show_default=True,
              required=False,
              help="Filepath to the instances metadata")
def ssh(ctx, node, filepath):
    import os
    import subprocess
    cluster = Cluster.from_filepath(filepath)
    instance = cluster.instances[node]
    ip = instance.ip
    username = instance.username
    keypair = os.path.expanduser(instance.keypair)
    cmd = ['ssh', username + '@' + ip]
    cmd = cmd + ['-i', keypair]
    cmd = cmd + ['-oStrictHostKeyChecking=no']
    cmd = cmd + ['-p %i' % instance.port]
    click.echo(' '.join(cmd))
    subprocess.call(cmd)


@cli.command(short_help="Provision salt instances")
@click.pass_context
@click.option("--file",
              "filepath",
              type=click.Path(exists=True),
              envvar="CLUSTERFILE",
              default="cluster.yaml",
              show_default=True,
              required=False,
              help="Filepath to the instances metadata")
@click.option("--ssh-check/--no-ssh-check",
              default=True,
              show_default=True,
              required=False,
              help="Whether to check or not for SSH connection")
@click.option("--master/--no-master",
              is_flag=True,
              default=True,
              show_default=True,
              help="Bootstrap the salt master")
@click.option("--minions/--no-minions",
              is_flag=True,
              default=True,
              show_default=True,
              help="Bootstrap the salt minions")
@click.option("--upload/--no-upload",
              is_flag=True,
              default=True,
              show_default=True,
              help="Upload the salt formulas")
@click.option("--anaconda/--no-anaconda", "anaconda_",
              is_flag=True,
              default=True,
              show_default=True,
              help="Bootstrap anaconda")
@click.option("--dask/--no-dask",
              "dask",
              default=True,
              show_default=True,
              required=False,
              help="Install Dask.Distributed in the cluster")
@click.option("--notebook/--no-notebook",
              "notebook",
              default=True,
              show_default=True,
              required=False,
              help="Start a Jupyter Notebook in the head node")
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
def provision(ctx, filepath, ssh_check, master, minions, upload, anaconda_, dask, notebook, nprocs, source):
    import six
    from ..salt import install_salt_master, install_salt_minion, upload_formulas, upload_pillar

    cluster = Cluster.from_filepath(filepath)
    if ssh_check:
        click.echo("Checking SSH connection to nodes")
        cluster = Cluster.from_filepath(filepath)
        info = cluster.check_ssh()
        data = [["Node IP", "SSH check"]]
        for ip, status in info.items():
            data.append([ip, status])
        t = Table(data, 1)
        t.write()
    if master:
        click.echo("Bootstraping salt master")
        install_salt_master(cluster)
    if minions:
        click.echo("Bootstraping salt minions")
        install_salt_minion(cluster)
    if upload:
        click.echo("Uploading salt formulas")
        upload_formulas(cluster)
        click.echo("Uploading conda and cluster settings")
        upload_pillar(cluster, "conda.sls", {"conda": {"pyversion": 2 if six.PY2 else 3}})
        upload_pillar(cluster, "cluster.sls",
                      {"cluster": {
                          "username": cluster.instances[0].username
                        }
                      })
    if anaconda_:
        ctx.invoke(anaconda, filepath=filepath)
    if dask:
        from .daskd import dask_install
        ctx.invoke(dask_install, filepath=filepath, nprocs=nprocs, source=source)
    if notebook:
        ctx.invoke(notebook_install, filepath=filepath)


@cli.command(short_help="Provision anaconda")
@click.pass_context
@click.option("--file",
              "filepath",
              type=click.Path(exists=True),
              envvar="CLUSTERFILE",
              default="cluster.yaml",
              show_default=True,
              required=False,
              help="Filepath to the instances metadata")
def anaconda(ctx, filepath):
    cluster = Cluster.from_filepath(filepath)
    output = cluster.salt_call("*", "state.sls", ["conda"])
    response = print_state(output)
    if not response.aggregated_success():
        sys.exit(1)


def print_state(output):
    response = Response.from_dict(output)
    response = response.aggregate_by(field="result")
    data = [["Node ID", "# Successful actions", "# Failed action"]]
    data.extend(response.aggregated_to_table(agg=len))
    t = Table(data, 1)
    t.write()

    for node_id, data in response.items():
        failed = data["failed"]
        if len(failed):
            click.echo("Failed states for '{}'".format(node_id))
            for fail in failed:
                name = fail["name"].replace("_|-", " | ")
                click.echo("  {name}: {comment}".format(name=name, comment=fail["comment"]))
    return response


from .daskd import *
from .notebook import *
