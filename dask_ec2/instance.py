from __future__ import print_function, division, absolute_import

import os
import socket
import logging

import paramiko
from paramiko.ssh_exception import BadHostKeyException, AuthenticationException, SSHException

from .ssh import SSHClient
from .utils import retry
from .exceptions import DaskEc2Exception

logger = logging.getLogger(__name__)


class Instance(object):

    def __init__(self, ip, uid=None, port=22, username=None, keypair=None):
        self.ip = ip
        self.uid = uid
        self.port = port
        self.username = username
        self.keypair = keypair

    @classmethod
    def from_boto3_instance(cls, instance):
        self = cls(ip=instance.public_ip_address, uid=instance.id)
        return self

    @retry(catch=(BadHostKeyException, AuthenticationException, SSHException, socket.error, TypeError, DaskEc2Exception))
    def check_ssh(self):
        logger.debug('Checking ssh connection for %s', self.ip)
        self.ssh_client.exec_command("ls")
        return True

    def get_ssh_client(self):
        host = self.ip
        username = self.username
        pkey = self.keypair
        port = self.port
        client = SSHClient(host, username=username, pkey=pkey, port=port)
        return client

    ssh_client = property(get_ssh_client, None, None)

    @classmethod
    def from_dict(cls, data):
        self = cls(ip=data["ip"])
        self.uid = data["uid"]
        self.port = data["port"]
        self.username = data["username"]
        self.keypair = data["keypair"]
        return self

    def to_dict(self):
        ret = {}
        ret['uid'] = self.uid
        ret['ip'] = self.ip
        ret['port'] = self.port
        ret['username'] = self.username
        ret['keypair'] = self.keypair
        return ret
