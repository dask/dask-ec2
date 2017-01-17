"""
Utilies to manage salt bootstrap and other stuff
"""
import os
import logging
import itertools
import threading

import dask_ec2
from dask_ec2.utils import retry
from dask_ec2.exceptions import DaskEc2Exception, RetriesExceededException

logger = logging.getLogger(__name__)


class Response(dict):
    """Response from a Salt Command
    Format is based on salt output but is flattened by compute_id, example:
    ```
    {'compute1': [state_1_output, state_2_output], 'compute2': [state_1_output]}
    ```
    Where `state_x_output` is: `{'name': 'my_state', 'result': True}`
    """

    def __init__(self, *args, **kwargs):
        super(Response, self).__init__(*args, **kwargs)

    @classmethod
    def from_dict(cls, data):
        self = cls()
        data = data["return"]
        for item in data:
            for minion_id, states in item.items():
                self[minion_id] = states
        return self

    def aggregate_by(self, field='result', validation=True):
        """
        Usefull when the Command module return a dictionary, for example state.sls
        Default values are for salt module `state.sls`
        """
        try:
            ret = Response()
            for minion_id, values in self.items():
                inner_values = []
                if type(values) == dict:
                    # Assumes: depth=1 going to flat
                    for key, value in values.items():
                        value['name'] = key
                        inner_values.append(value)
                elif type(self[minion_id]) == list:
                    inner_values = self[minion_id]

                successful = [action for action in inner_values if action[field] == validation]
                failed = [action for action in inner_values if action[field] != validation]
                summary = {'successful': successful, 'failed': failed}
                ret[minion_id] = summary
                return ret
        except TypeError:
            logger.debug("Error with salt state.  Printing full returned output")
            logger.debug(self)

    def aggregated_to_table(self, agg=None):
        """
        From an aggregated response it retuns a list of 3 columns:
        1. node id
        2. successful states
        3. failed states
        """
        ret = []
        for node_id, data in self.items():
            if agg:
                ret.append([node_id, agg(data["successful"]), agg(data["failed"])])
            else:
                ret.append([node_id, data["successful"], data["failed"]])
        return ret

    def aggregated_success(self):
        """
        From an aggregated return True if all the states where successful
        """
        ret = True
        for node_id, data in self.items():
            failed = data["failed"]
            ret = ret & (len(failed) == 0)
        return ret

    def group_by_id(self, ignore_fields=None, sort=True):
        if ignore_fields:
            copy = copy_(self)
            for id_ in copy:
                for field in ignore_fields:
                    del copy[id_][field]
        else:
            copy = self

        items = sorted(copy.items(), key=lambda x: x[1])
        groups = []
        for key, group in itertools.groupby(items, key=lambda x: x[1]):
            groups.append((key, [item[0] for item in group]))

        if sort:
            groups = sorted(groups, key=lambda x: len(x[1]), reverse=True)
        return groups


def install_salt_master(cluster):
    master = cluster.instances[0].ssh_client
    dask_ec2_src = os.path.realpath(os.path.dirname(dask_ec2.__file__))
    templates_src = os.path.join(dask_ec2_src, "templates")

    @retry(retries=3, wait=0)
    def __install_salt_master():
        cmd = "curl -sS -L https://bootstrap.saltstack.com | sh -s -- -d -X -M -N stable"
        ret = master.exec_command(cmd, sudo=True)
        if ret["exit_code"] != 0:
            raise Exception(ret["stderr"].decode('utf-8'))
        return True

    try:
        __install_salt_master()
    except RetriesExceededException as e:
        raise DaskEc2Exception("%s\nCouldn't bootstrap salt-master. Error is above (maybe try again)" %
                               e.last_exception)

    @retry(retries=3, wait=0)
    def __install_salt_api():
        cmd = "curl -L https://bootstrap.saltstack.com | sh -s -- -d -X -M -N -P -L -p salt-api stable"
        ret = master.exec_command(cmd, sudo=True)
        if ret["exit_code"] != 0:
            raise Exception(ret["stderr"].decode('utf-8'))

    try:
        __install_salt_api()
    except RetriesExceededException as e:
        raise DaskEc2Exception("%s\nCouldn't bootstrap salt-api. Error is above (maybe try again)" %
                               e.last_exception)

    @retry(retries=3, wait=0)
    def __setup_salt_master():
        local = os.path.join(templates_src, "auto_accept.conf")
        remote = "/etc/salt/master.d/auto_accept.conf"
        master.put(local, remote, sudo=True)

    try:
        __setup_salt_master()
    except RetriesExceededException as e:
        raise DaskEc2Exception(
            "%s\nCouldn't setup salt-master settings. Error is above (maybe try again)" %
            e.last_exception)

    @retry(retries=3, wait=0)
    def __install_python_pip():
        cmd = "apt-get install -y python-pip"
        ret = master.exec_command(cmd, sudo=True)
        if ret["exit_code"] != 0:
            raise Exception(ret["stderr"].decode('utf-8'))

    try:
        __install_python_pip()
    except RetriesExceededException as e:
        raise DaskEc2Exception("%s\nCouldn't install python-pip. Error is above (maybe try again)" %
                               e.last_exception)

    @retry(retries=3, wait=0)
    def __install_salt_rest_api():
        cmd = "pip install cherrypy"
        ret = master.exec_command(cmd, sudo=True)
        if ret["exit_code"] != 0:
            raise Exception(ret["stderr"].decode('utf-8'))

    try:
        __install_salt_rest_api()
    except RetriesExceededException as e:
        raise DaskEc2Exception("%s\nCouldn't install CherryPy. Error is above (maybe try again)" %
                               e.last_exception)

    @retry(retries=3, wait=0)
    def __install_pyopensll():
        cmd = "pip install PyOpenSSL"
        ret = master.exec_command(cmd, sudo=True)
        if ret["exit_code"] != 0:
            raise Exception(ret["stderr"].decode('utf-8'))

    try:
        __install_pyopensll()
    except RetriesExceededException as e:
        raise DaskEc2Exception("%s\nCouldn't install PyOpenSSL. Error is above (maybe try again)" %
                               e.last_exception)

    @retry(retries=3, wait=0)
    def __create_ssl_cert():
        cmd = "salt-call --local tls.create_self_signed_cert"
        ret = master.exec_command(cmd, sudo=True)
        if ret["exit_code"] != 0:
            raise Exception(ret["stderr"].decode('utf-8'))

    try:
        __create_ssl_cert()
    except RetriesExceededException as e:
        raise DaskEc2Exception(
            "%s\nCouldn't generate SSL certificate. Error is above (maybe try again)" %
            e.last_exception)

    @retry(retries=3, wait=0)
    def __setup_rest_cherrypy():
        local = os.path.join(templates_src, "rest_cherrypy.conf")
        remote = "/etc/salt/master.d/rest_cherrypy.conf"
        master.put(local, remote, sudo=True)

    try:
        __setup_rest_cherrypy()
    except RetriesExceededException as e:
        raise DaskEc2Exception("%s\nCouldn't setup salt-rest server. Error is above (maybe try again)" %
                               e.last_exception)

    @retry(retries=3, wait=0)
    def __setup_salt_external_auth():
        local = os.path.join(templates_src, "external_auth.conf")
        remote = "/etc/salt/master.d/external_auth.conf"
        master.put(local, remote, sudo=True)

    try:
        __setup_salt_external_auth()
    except RetriesExceededException as e:
        raise DaskEc2Exception(
            "%s\nCouldn't setup salt external auth system. Error is above (maybe try again)" %
            e.last_exception)

    @retry(retries=3, wait=0)
    def __create_saltdev_user():
        cmd = "id -u saltdev &>/dev/null || useradd -p $(openssl passwd -1 saltdev) saltdev"
        ret = master.exec_command(cmd, sudo=True)
        if ret["exit_code"] != 0:
            raise Exception(ret["stderr"].decode('utf-8'))

    try:
        __create_saltdev_user()
    except RetriesExceededException as e:
        raise DaskEc2Exception("%s\nCouldn't create 'saltdev' user. Error is above (maybe try again)" %
                               e.last_exception)

    @retry(retries=3, wait=0)
    def __restart_salt_master():
        cmd = "service salt-master restart"
        ret = master.exec_command(cmd, sudo=True)
        if ret["exit_code"] != 0:
            raise Exception(ret["stderr"].decode('utf-8'))

    try:
        __restart_salt_master()
    except RetriesExceededException as e:
        raise DaskEc2Exception(
            "%s\nCouldn't restart salt-master service. Error is above (maybe try again)" %
            e.last_exception)

    @retry(retries=3, wait=0)
    def __restart_salt_api():
        cmd = "service salt-api restart"
        ret = master.exec_command(cmd, sudo=True)
        if ret["exit_code"] != 0:
            raise Exception(ret["stderr"].decode('utf-8'))

    try:
        __restart_salt_api()
    except RetriesExceededException as e:
        raise DaskEc2Exception(
            "%s\nCouldn't restart salt-api service. Error is above (maybe try again)" %
            e.last_exception)


def async_cmd(results, instance, command):
    client = instance.ssh_client

    @retry(retries=3, wait=0)
    def __remote_cmd():
        ret = client.exec_command(command, sudo=True)
        if ret["exit_code"] != 0:
            raise Exception(ret["stderr"].decode('utf-8'))
        return ret

    try:
        results[instance.ip] = __remote_cmd()
    except RetriesExceededException as e:
        results[instance.ip] = False


def async_upload(results, instance, local, remote):
    client = instance.ssh_client

    @retry(retries=3, wait=0)
    def __remote_upload():
        client.put(local, remote, sudo=True)
        return True

    try:
        results[instance.ip] = __remote_upload()
    except RetriesExceededException as e:
        results[instance.ip] = False


def install_salt_minion(cluster):
    dask_ec2_src = os.path.realpath(os.path.dirname(dask_ec2.__file__))
    templates_src = os.path.join(dask_ec2_src, "templates")

    logger.debug("Installing salt-minion on all the nodes")
    results, threads = {}, []
    master_ip = cluster.instances[0].ip
    for i, instance in enumerate(cluster.instances):
        minion_id = "node-{}".format(i)
        cmd = "curl -L https://bootstrap.saltstack.com | sh -s -- "
        cmd += "-d -X -P -L -A {master_ip} -i {minion_id} stable".format(master_ip=master_ip,
                                                                         minion_id=minion_id)
        t = threading.Thread(target=async_cmd, args=(results, instance, cmd))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()

    all_ok = all([r == False for r in results])
    if not all_ok:
        failed_nodes = []
        for minion_ip, minion_data in results.items():
            if minion_data is False:
                failed_nodes.append(minion_ip)
        if failed_nodes:
            raise DaskEc2Exception("Error bootstraping salt-minion at nodes: %s (maybe try again)" %
                                   failed_nodes)

    logger.debug("Configuring salt-mine on the salt minions")
    results, threads = {}, []
    for i, instance in enumerate(cluster.instances):
        local = os.path.join(templates_src, "mine_functions.conf")
        remote = "/etc/salt/minion.d/mine.conf"
        t = threading.Thread(target=async_upload, args=(results, instance, local, remote))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()

    all_ok = all([r is False for r in results])
    if not all_ok:
        failed_nodes = []
        for minion_ip, minion_data in results.items():
            if minion_data is False:
                failed_nodes.append(minion_ip)
        if failed_nodes:
            raise DaskEc2Exception(
                "Error configuring the salt-mine in the salt-minion at nodes: %s (maybe try again)"
                % failed_nodes)

    logger.debug("Restarting the salt-minion service")
    results, threads = {}, []
    for i, instance in enumerate(cluster.instances):
        cmd = "service salt-minion restart"
        t = threading.Thread(target=async_cmd, args=(results, instance, cmd))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()

    all_ok = all([r is False for r in results])
    if not all_ok:
        failed_nodes = []
        for minion_ip, minion_data in results.items():
            if minion_data is False:
                failed_nodes.append(minion_ip)
        if failed_nodes:
            raise DaskEc2Exception("Error restarting the salt-minion at nodes: %s (maybe try again)" %
                                   failed_nodes)


def upload_formulas(cluster):
    dask_ec2_src = os.path.realpath(os.path.dirname(dask_ec2.__file__))
    src_salt_root = os.path.join(dask_ec2_src, "formulas", "salt")
    src_pillar_root = os.path.join(dask_ec2_src, "formulas", "pillar")
    dst_salt_root = "/srv/salt"
    dst_pillar_root = "/srv/pillar"

    client = cluster.instances[0].ssh_client
    client.put(src_salt_root, dst_salt_root, sudo=True)
    client.put(src_pillar_root, dst_pillar_root, sudo=True)


def upload_pillar(cluster, name, data):
    import os
    import yaml
    import tempfile

    master = cluster.instances[0].ssh_client
    f = tempfile.NamedTemporaryFile("w", delete=False)
    try:
        yaml.safe_dump(data, f, default_flow_style=False)
        f.close()
        local = f.name
        remote = "/srv/pillar/{}".format(name)
        master.put(local, remote, sudo=True)
    finally:
        os.remove(f.name)
