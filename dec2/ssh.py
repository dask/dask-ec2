"""
Small wrapper around paramiko.SSHClient
"""
import os
import time
import logging
import posixpath
from socket import gaierror as sock_gaierror, error as sock_error

import paramiko


logger = logging.getLogger(__name__)


class SSHClient(object):

    def __init__(self, host, username=None, password=None, pkey=None, port=22,
                 timeout=15):
        self.host = host
        self.username = username
        self.password = password
        pkey = os.path.expanduser(pkey)
        if os.path.isfile(pkey):
            self.pkey = paramiko.RSAKey.from_private_key_file(pkey)
        else:
            self.pkey = pkey
        self.port = port
        self.timeout = timeout

        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.MissingHostKeyPolicy())
        self._sftp = None

        self.connect()

    def connect(self):
        """Connect to host
        """
        try:
            self.client.connect(self.host, username=self.username,
                           password=self.password, port=self.port,
                           pkey=self.pkey, timeout=self.timeout)
        except sock_gaierror as e:
            raise Exception("Unknown host '%s'" % self.host)
        except sock_error as e:
            raise Exception("Error connecting to host '%s:%s'\n%s" % (self.host, self.port, e))
        except paramiko.AuthenticationException as e:
            msg = "Host is '%s:%s'"
            raise Exception("Authentication Error to host '%s'" % self.host)
        except paramiko.SSHException as e:
            msg = "General SSH error - %s" % e
            raise Exception(msg)

    def close(self):
        self.client.close()

    def exec_command(self, command, sudo=False, **kwargs):
        """Wrapper to paramiko.SSHClient.exec_command
        """
        channel = self.client.get_transport().open_session()
        # stdin = channel.makefile('wb')
        stdout = channel.makefile('rb')
        stderr = channel.makefile_stderr('rb')

        if sudo:
            command = 'sudo -S bash -c \'%s\'' % command
        else:
            command = 'bash -c \'%s\'' % command

        logger.debug("Running command %s on '%s'", command, self.host)
        channel.exec_command(command, **kwargs)

        while not (channel.recv_ready() or channel.closed or
                   channel.exit_status_ready()):
            time.sleep(.2)

        ret = {'stdout': stdout.read().strip(), 'stderr': stderr.read().strip(),
               'exit_code': channel.recv_exit_status()}
        return ret

    def get_sftp(self):
        if self._sftp is None:
            self._sftp = self.make_sftp()
        return self._sftp

    def make_sftp(self):
        """Make SFTP client from open transport"""
        transport = self.client.get_transport()
        transport.open_session()
        return paramiko.SFTPClient.from_transport(transport)

    sftp = property(get_sftp, None, None)

    def mkdir(self, path, mode=511):
        if self.check_dir(path):
            return True
        else:
            dirname, basename = posixpath.split(path)
            if self.check_dir(dirname):
                logger.debug("Creating directory %s mode=%s", path, mode)
                self.sftp.mkdir(basename, mode=mode) # sub-directory missing, so created it
                self.sftp.chdir(basename)
            else:
                # Make parent directories:
                self.mkdir(dirname)
        return True

    def check_dir(self, path):
        try:
            self.sftp.chdir(path)
            return True
        except IOError as error:
            return False

    def put(self, local, remote, sudo=False):
        """Copy local file to host via SFTP/SCP

        Copy is done natively using SFTP/SCP version 2 protocol, no scp command
        is used or required.
        """
        if(os.path.isdir(local)):
            self.put_dir(local, remote, sudo=sudo)
        else:
            self.put_single(local, remote, sudo=sudo)

    def put_single(self, local, remote, sudo=False):
        if sudo:
            real_remote = remote
            remote = '/tmp/.__tmp_copy'

        logger.debug('Uploading file %s to %s', local, remote)
        self.sftp.put(local, remote)

        if sudo:
            cmd = 'cp -rf {} {}'.format(remote, real_remote)
            output = self.exec_command(cmd, sudo=True)
            cmd = 'rm -rf {}'.format(remote)
            output = self.exec_command(cmd, sudo=True)

    def put_dir(self, local, remote, sudo=False):
        logger.debug("Uploading directory %s to %s", local, remote)

        self.exec_command("mkdir -p {}".format(remote), sudo=True)

        if sudo:
            real_remote = remote
            remote = '/tmp/.__tmp_copy'

        self.mkdir(remote)
        for item in os.listdir(local):
            if os.path.isfile(os.path.join(local, item)):
                self.put(os.path.join(local, item), '%s/%s' % (remote, item))
            else:
                self.mkdir('%s/%s' % (remote, item))
                self.put_dir(os.path.join(local, item), '%s/%s' % (remote, item))

        if sudo:
            cmd = 'cp -rf {}/* {}'.format(remote, real_remote)
            output = self.exec_command(cmd, sudo=True)
            cmd = 'rm -rf {}'.format(remote)
            output = self.exec_command(cmd, sudo=True)
