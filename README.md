# Dask EC2 [![Build Status](https://travis-ci.org/dask/dask-ec2.svg?branch=master)](https://travis-ci.org/dask/dask-ec2) [![Coverage Status](https://coveralls.io/repos/github/dask/dask-ec2/badge.svg?branch=master)](https://coveralls.io/github/dask/dask-ec2?branch=master)

Easily launch a cluster on Amazon EC2 configured with `dask.distributed`,
Jupyter Notebooks, and Anaconda.


## DEPRECATED

This project is not actively maintained.  Instead, to deploy Dask on EC2
we recommend the use of Kubernetes.
See [dask.pydata.org/en/latest/setup/cloud.html](http://dask.pydata.org/en/latest/setup/cloud.html)
for up-to-date information.


## Installation

You also install `dask-ec2` using pip:

```bash
$ pip install dask-ec2
```

You can also install `dask-ec2` and its dependencies from the
[conda-forge](https://conda-forge.github.io/) repository using
[conda](https://www.continuum.io/downloads):

```bash
$ conda install dask-ec2 -c conda-forge
```

## Usage

**Note:** `dask-ec2` uses
[`boto3`](http://boto3.readthedocs.io/en/latest/index.html) to interact with
Amazon EC2. You can configure your AWS credentials using
[Environment Variables](http://boto3.readthedocs.io/en/latest/guide/configuration.html#environment-variables)
or [Configuration Files](http://boto3.readthedocs.io/en/latest/guide/configuration.html#configuration-files).

The `dask-ec2 up` command can be used to create and provision a cluster on Amazon EC2:

```bash
$ dask-ec2 up --help
Usage: dask-ec2 up [OPTIONS]

Options:
  --keyname TEXT                Keyname on EC2 console  [required]
  --keypair PATH                Path to the keypair that matches the keyname
                                [required]
  --name TEXT                   Tag name on EC2
  --tags TEXT                   Additional EC2 tags.  Comma separated K:V
                                pairs: K1:V1,K2:V2
  --region-name TEXT            AWS region  [default: us-east-1]
  --vpc-id TEXT                 EC2 VPC ID
  --subnet-id TEXT              EC2 Subnet ID on the VPC
  --iaminstance-name TEXT       IAM Instance Name
  --ami TEXT                    EC2 AMI  [default: ami-d05e75b8]
  --username TEXT               User to SSH to the AMI  [default: ubuntu]
  --type TEXT                   EC2 Instance Type  [default: m3.2xlarge]
  --count INTEGER               Number of nodes  [default: 4]
  --security-group TEXT         Security Group Name  [default: dask-ec2-default]
  --security-group-id TEXT      Security Group ID (overwrites Security Group
                                Name)
  --volume-type TEXT            Root volume type  [default: gp2]
  --volume-size INTEGER         Root volume size (GB)  [default: 500]
  --file PATH                   File to save the metadata  [default:
                                cluster.yaml]
  --provision / --no-provision  Provision salt on the nodes  [default: True]
  --anaconda / --no-anaconda    Bootstrap anaconda  [default: True]
  --dask / --no-dask            Install Dask.Distributed in the cluster
                                [default: True]
  --notebook / --no-notebook    Start a Jupyter Notebook in the head node
                                [default: True]
  --nprocs INTEGER              Number of processes per worker  [default: 1]
  --source / --no-source        Install Dask/Distributed from git master
                                [default: False]
  -h, --help                    Show this message and exit.
```

The minimal required arguments for the `dask-ec2 up` command are:

```
$ dask-ec2 up --keyname my_aws_key --keypair ~/.ssh/my_aws_key.pem
```

This will create a `cluster.yaml` in the directory that it was executed, and
this file is required to use the other commands in the CLI.

Once a cluster is running, the `dask-ec2` command can be used to create or destroy
a cluster, ssh into nodes, or other functions:

```bash
$ dask-ec2
Usage: dask-ec2 [OPTIONS] COMMAND [ARGS]...

Options:
  --version   Show the version and exit.
  -h, --help  Show this message and exit.

Commands:
  anaconda          Provision anaconda
  dask-distributed  dask.distributed option
  destroy           Destroy cluster
  notebook          Provision the Jupyter notebook
  provision         Provision salt instances
  ssh               SSH to one of the node. 0-index
  up                Launch instances
```
