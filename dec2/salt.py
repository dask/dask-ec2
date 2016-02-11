"""
Utilies to manage salt bootstrap and other stuff
"""
import os
import logging
import threading

from dec2.exceptions import DEC2Exception

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
        # data = {u'return': [{u'node-0': {u'cmd_|-miniconda-pip_|-/opt/anaconda//bin/conda install pip -y -q_|-run': {u'comment': u'unless execution succeeded', u'name': u'/opt/anaconda//bin/conda install pip -y -q', u'start_time': u'22:49:49.810941', u'skip_watch': True, u'result': True, u'duration': 3.462, u'__run_num__': 4, u'changes': {}}, u'file_|-dscheduler.conf_|-/etc/supervisor/conf.d//dscheduler.conf_|-managed': {u'comment': u'File /etc/supervisor/conf.d//dscheduler.conf is in the correct state', u'name': u'/etc/supervisor/conf.d//dscheduler.conf', u'start_time': u'22:49:50.772314', u'result': True, u'duration': 18.327, u'__run_num__': 7, u'changes': {}}, u'pip_|-distributed-install_|-distributed_|-installed': {u'comment': u'Python package distributed was already installed\nAll packages were successfully installed', u'name': u'distributed', u'start_time': u'22:49:50.369348', u'result': True, u'duration': 400.64, u'__run_num__': 6, u'changes': {}}, u'pkg_|-miniconda-curl_|-curl_|-installed': {u'comment': u'Package curl is already installed', u'name': u'curl', u'start_time': u'22:49:49.796988', u'result': True, u'duration': 3.284, u'__run_num__': 1, u'changes': {}}, u'cmd_|-miniconda-install_|-bash /tmp/miniconda.sh -b -p /opt/anaconda/_|-run': {u'comment': u'unless execution succeeded', u'name': u'bash /tmp/miniconda.sh -b -p /opt/anaconda/', u'start_time': u'22:49:49.806676', u'skip_watch': True, u'result': True, u'duration': 3.655, u'__run_num__': 3, u'changes': {}}, u'pip_|-dask-install_|-dask_|-installed': {u'comment': u'Python package dask was already installed\nAll packages were successfully installed', u'name': u'dask', u'start_time': u'22:49:49.966047', u'result': True, u'duration': 402.984, u'__run_num__': 5, u'changes': {}}, u'pkg_|-supervisor-pkg_|-supervisor_|-installed': {u'comment': u'Package supervisor is already installed', u'name': u'supervisor', u'start_time': u'22:49:49.542661', u'result': True, u'duration': 254.154, u'__run_num__': 0, u'changes': {}}, u'cmd_|-miniconda-download_|-curl https://repo.continuum.io/miniconda/Miniconda-latest-Linux-x86_64.sh > /tmp/miniconda.sh_|-run': {u'comment': u'unless execution succeeded', u'name': u'curl https://repo.continuum.io/miniconda/Miniconda-latest-Linux-x86_64.sh > /tmp/miniconda.sh', u'start_time': u'22:49:49.801437', u'skip_watch': True, u'result': True, u'duration': 4.827, u'__run_num__': 2, u'changes': {}}, u'supervisord_|-dscheduler-running_|-dscheduler_|-running': {u'comment': u'Not starting already running service: dscheduler', u'name': u'dscheduler', u'start_time': u'22:49:50.791807', u'result': True, u'duration': 64.257, u'__run_num__': 9, u'changes': {}}, u'cmd_|-dscheduler-update-supervisor_|-/usr/bin/supervisorctl -c /etc/supervisor/supervisord.conf update && sleep 2_|-wait': {u'comment': u'', u'name': u'/usr/bin/supervisorctl -c /etc/supervisor/supervisord.conf update && sleep 2', u'start_time': u'22:49:50.791023', u'result': True, u'duration': 0.339, u'__run_num__': 8, u'changes': {}}}}]}
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

    cmd = "curl -L https://bootstrap.saltstack.com | sudo sh -s -- "
    cmd += "-M -N stable"
    ret = master.exec_command(cmd, sudo=True)
    if ret["exit_code"] != 0:
        raise DEC2Exception("Couldn't bootstrap salt-master: %s" % ret["stderr"])

    cmd = "curl -L https://bootstrap.saltstack.com | sudo sh -s -- "
    cmd += "-M -N -P -L -p salt-api stable"
    ret = master.exec_command(cmd, sudo=True)
    if ret["exit_code"] != 0:
        raise DEC2Exception("Couldn't bootstrap salt-api: %s" % ret["stderr"])

    cmd = """echo "auto_accept: True" > /etc/salt/master.d/auto_accept.conf"""
    ret = master.exec_command(cmd, sudo=True)
    if ret["exit_code"] != 0:
        raise DEC2Exception("Couldn't setup salt-master settings: %s" % ret["stderr"])

    # Setup salt rest server
    cmd = "pip install cherrypy"
    ret = master.exec_command(cmd, sudo=True)
    if ret["exit_code"] != 0:
        raise DEC2Exception("Couldn't install CherryPy: %s" % ret["stderr"])

    cmd = "salt-call --local tls.create_self_signed_cert"
    ret = master.exec_command(cmd, sudo=True)
    if ret["exit_code"] != 0:
        raise DEC2Exception("Couldn't generate ssl certificate: %s" % ret["stderr"])

    cmd = """cat >/etc/salt/master.d/cherrypy.conf <<EOL
rest_cherrypy:
  port: 8000
  ssl_crt: /etc/pki/tls/certs/localhost.crt
  ssl_key: /etc/pki/tls/certs/localhost.key
    """
    ret = master.exec_command(cmd, sudo=True)
    if ret["exit_code"] != 0:
        raise DEC2Exception("Couldn't setup salt-rest server: %s" % ret["stderr"])

    cmd = """cat >/etc/salt/master.d/access.conf <<EOL
external_auth:
  pam:
    saltdev:
      - .*
    """
    ret = master.exec_command(cmd, sudo=True)
    if ret["exit_code"] != 0:
        raise DEC2Exception("Couldn't setup salt access control system: %s" % ret["stderr"])

    cmd = """useradd -p $(openssl passwd -1 saltdev) saltdev"""
    ret = master.exec_command(cmd, sudo=True)
    if ret["exit_code"] != 0:
        if "already exists" in ret["stderr"]:
            pass
        else:
            raise DEC2Exception("Couldn't create 'saltdev' user: %s" % ret["stderr"])

    cmd = "service salt-master restart"
    ret = master.exec_command(cmd, sudo=True)
    if ret["exit_code"] != 0:
        raise DEC2Exception("Couldn't restart salt-master: %s" % ret["stderr"])

    cmd = "service salt-api restart"
    ret = master.exec_command(cmd, sudo=True)
    if ret["exit_code"] != 0:
        raise DEC2Exception("Couldn't restart salt-api: %s" % ret["stderr"])


def work(results, instance, command):
    client = instance.ssh_client
    results[instance.ip] = client.exec_command(command, sudo=True)


def install_salt_minion(cluster):
    results = {}
    threads = []
    master_ip= cluster.instances[0].ip
    for i, instance in enumerate(cluster.instances):
        minion_id = "node-{}".format(i)

        cmd = "curl -L https://bootstrap.saltstack.com | sudo sh -s -- "
        cmd += "-P -L -A {master_ip} -i {minion_id} stable".format(master_ip=master_ip, minion_id=minion_id)

        t = threading.Thread(target=work, args=(results, instance, cmd))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    return_codes = [m["exit_code"] for key, m in results.items()]
    all_ok = all([rc == 0 for rc in return_codes])
    if not all_ok:
        for minion_ip, minion_data in results.items():
            if m["exit_code"] != 0:
                raise DEC2Exception("Error bootstraping salt-minion at node %s: %s", minion_ip, minion_data["stderr"])

    # Setup salt-mine
    results = {}
    threads = []
    cmd = """cat >/etc/salt/minion.d/mine.conf <<EOL
mine_functions:
  network.get_hostname: []
  network.interfaces: []
  network.ip_addrs: []
mine_interval: 2
"""
    for i, instance in enumerate(cluster.instances):
        t = threading.Thread(target=work, args=(results, instance, cmd))
        t.start()
        threads.append(t)

    return_codes = [m["exit_code"] for key, m in results.items()]
    all_ok = all([rc == 0 for rc in return_codes])
    if not all_ok:
        for minion_ip, minion_data in results.items():
            if m["exit_code"] != 0:
                raise DEC2Exception("Error setup the salt-minion mine at node %s: %s", minion_ip, minion_data["stderr"])

    # Restart salt-minions
    results = {}
    threads = []
    cmd = "service salt-minion restart"
    for i, instance in enumerate(cluster.instances):
        t = threading.Thread(target=work, args=(results, instance, cmd))
        t.start()
        threads.append(t)

    return_codes = [m["exit_code"] for key, m in results.items()]
    all_ok = all([rc == 0 for rc in return_codes])
    if not all_ok:
        for minion_ip, minion_data in results.items():
            if m["exit_code"] != 0:
                raise DEC2Exception("Error restartng the salt-minion at node %s: %s", minion_ip, minion_data["stderr"])


def upload_formulas(cluster):
    import dec2

    dec2_src = src_dir = os.path.realpath(os.path.dirname(dec2.__file__))
    src_salt_root = os.path.join(dec2_src, "formulas", "salt")
    src_pillar_root = os.path.join(dec2_src, "formulas", "pillar")
    dst_salt_root = "/srv/salt"
    dst_pillar_root = "/srv/pillar"

    client = cluster.instances[0].ssh_client
    client.put(src_salt_root, dst_salt_root, sudo=True)
    client.put(src_pillar_root, dst_pillar_root, sudo=True)
