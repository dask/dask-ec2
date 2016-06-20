from __future__ import print_function, division, absolute_import

import logging

import six
import yaml
from . import libpepper

from .compatibility import URLError
from .exceptions import DaskEc2Exception
from .instance import Instance

logger = logging.getLogger(__name__)


class Cluster(object):

    def __init__(self, instances=None):
        self._pepper = None
        self.instances = instances or []

    @classmethod
    def from_boto3_instances(cls, instances):
        self = cls()
        for boto3_instance in instances:
            instance = Instance.from_boto3_instance(boto3_instance)
            self.append(instance)
        return self

    @classmethod
    def from_filepath(cls, filepath):
        with open(filepath, 'r') as f:
            data = yaml.load(f.read())
            return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data):
        self = cls()
        instances = data["instances"]
        for instance in instances:
            self.instances.append(Instance.from_dict(instance))
        return self

    def get_head(self):
        return self.instances[0]

    head = property(get_head, None, None)

    def get_pepper_client(self):
        if not self._pepper:
            url = 'https://{}:8000'.format(self.instances[0].ip)
            try:
                self._pepper = libpepper.Pepper(url, ignore_ssl_errors=True)
                self._pepper.login('saltdev', 'saltdev', 'pam')
            except URLError as e:
                raise DaskEc2Exception(
                    "Could not connect to salt server. Try `dask-ec2 provision` and try again")
        return self._pepper

    pepper = property(get_pepper_client, None, None)

    def salt_call(self, target, module, args=None):
        args = [] or args
        try:
            return self.pepper.local(target, module, args)
        except URLError as e:
            raise DaskEc2Exception(
                "Could not connect to salt server. Try `dask-ec2 provision` and try again")

    def append(self, instance):
        if isinstance(instance, Instance):
            self.instances.append(instance)
        else:
            raise DaskEc2Exception("Can only append dask_ec2.Instance types to the cluster nodes")

    def set_username(self, username):
        for instance in self.instances:
            instance.username = username

    def set_keypair(self, keypair_path):
        for instance in self.instances:
            instance.keypair = keypair_path

    def check_ssh(self):
        ret = {}
        for instance in self.instances:
            address = "{}:{}".format(instance.ip, instance.port)
            ret[address] = instance.check_ssh()
        return ret

    def to_dict(self):
        ret = {}
        ret["instances"] = []
        for instance in self.instances:
            ret["instances"].append(instance.to_dict())
        return ret

    def to_file(self, filepath):
        with open(filepath, "w") as f:
            yaml.safe_dump(self.to_dict(), f, default_flow_style=False)

    def __repr__(self):
        return str(self.to_dict())
