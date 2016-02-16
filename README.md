# DEC2

Launch EC2 instances for `dask.distributed`


## Usage

**Credentials:** `dec2` uses [`boto3`](http://boto3.readthedocs.org/en/latest/index.html) so you can set your AWS credentials using [Environment
Variables](http://boto3.readthedocs.org/en/latest/guide/configuration.html#environment-variables)
or [Configuration Files](http://boto3.readthedocs.org/en/latest/guide/configuration.html#configuration-files).

There is some CLI arguments
```bash
$ dec2 up --help

Usage: dec2 up [OPTIONS]

Options:
  --keyname TEXT                Keyname on EC2 console  [required]
  --keypair PATH                Path to the keypair that matches the keyname
                                [required]
  --name TEXT                   Tag name on EC2
  --region-name TEXT            AWS region  [default: us-east-1]
  --ami TEXT                    EC2 AMI  [default: ami-d05e75b8]
  --username TEXT               User to SSH to the AMI  [default: ubuntu]
  --type TEXT                   EC2 Instance Type  [default: m3.2xlarge]
  --count INTEGER               Number of nodes  [default: 4]
  --security-group TEXT         Security Group Name  [default: dec2-default]
  --volume-type TEXT            Root volume type  [default: gp2]
  --volume-size INTEGER         Root volume size (GB)  [default: 500]
  --file PATH                   File to save the metadata  [default:
                                cluster.yaml]
  --ssh-check / --no-ssh-check  Whether to check or not for SSH connection
                                [default: True]
  --provision / --no-provision  Provision salt on the nodes  [default: True]
  --dask / --no-dask            Install Dask.Distributed in the cluster
                                [default: True]
  -h, --help                    Show this message and exit.
```

The minimal required are:

```
$ dec2 up --keyname myawskey --keypair ~/.ssh/myawskey.pem
```

This will create a `cluster.yaml` in the directory it was executed, this file is required for the other commands in the CLI.

To start a distributed cluster:

```
$ dec2 dask-distributed
```
