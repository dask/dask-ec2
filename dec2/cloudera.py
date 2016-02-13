"""
Utilies to manage a cloudera managed cluster
"""
import time


from cm_api.endpoints.services import ApiServiceSetupInfo


CDH_VERSION = "CDH5"


def init_cluster(cluster):
    CM_HOST_IP = cluster.salt_call('node-0', 'network.ip_addrs')['return'][0]['node-0'][0]
    api = cluster.cmanager

    cm_cluster = api.create_cluster("CM", CDH_VERSION)

    # Add all hosts to the cluster
    cm_hosts = api.get_all_hosts()
    cm_hosts_ids = [host.hostId for host in cm_hosts]
    cm_cluster.add_hosts(cm_hosts_ids)

    # Deploy Management
    manager = api.get_cloudera_manager()
    mgmt = manager.create_mgmt_service(ApiServiceSetupInfo())

    cm_host = [host for host in cm_hosts if host.ipAddress == CM_HOST_IP][0]
    cm_host_id = cm_host.hostId

    ret = cluster.instances[0].ssh_client.exec_command('grep com.cloudera.cmf.ACTIVITYMONITOR.db.password /etc/cloudera-scm-server/db.mgmt.properties | cut -f2 -d"="', sudo=True)
    FIREHOSE_DATABASE_PASSWORD = ret["stdout"]
    AMON_ROLENAME = "ACTIVITYMONITOR"
    AMON_ROLE_CONFIG = {
        'firehose_database_host': CM_HOST_IP + ":7432",
        'firehose_database_user': 'amon',
        'firehose_database_password': FIREHOSE_DATABASE_PASSWORD,
        'firehose_database_type': 'postgresql',
        'firehose_database_name': 'amon',
        'firehose_heapsize': '215964392',
    }
    mgmt.create_role(AMON_ROLENAME + "-1", "ACTIVITYMONITOR", cm_host_id)

    APUB_ROLENAME = "ALERTPUBLISHER"
    APUB_ROLE_CONFIG = { }
    mgmt.create_role(APUB_ROLENAME + "-1", "ALERTPUBLISHER", cm_host_id)

    ESERV_ROLENAME = "EVENTSERVER"
    ESERV_ROLE_CONFIG = {
        'event_server_heapsize': '268435456'
    }
    mgmt.create_role(ESERV_ROLENAME + "-1", "EVENTSERVER", cm_host_id)

    HMON_ROLENAME = "HOSTMONITOR"
    HMON_ROLE_CONFIG = { }
    mgmt.create_role(HMON_ROLENAME + "-1", "HOSTMONITOR", cm_host_id)

    SMON_ROLENAME = "SERVICEMONITOR"
    SMON_ROLE_CONFIG = { }
    mgmt.create_role(SMON_ROLENAME + "-1", "SERVICEMONITOR", cm_host_id)


    mgmt.create_role(rman_role_name + "-1", "REPORTSMANAGER", CM_HOST)

    for group in mgmt.get_all_role_config_groups():
        if group.roleType == "ACTIVITYMONITOR":
            group.update_config(AMON_ROLE_CONFIG)
        elif group.roleType == "ALERTPUBLISHER":
            group.update_config(APUB_ROLE_CONFIG)
        elif group.roleType == "EVENTSERVER":
            group.update_config(ESERV_ROLE_CONFIG)
        elif group.roleType == "HOSTMONITOR":
            group.update_config(HMON_ROLE_CONFIG)
        elif group.roleType == "SERVICEMONITOR":
            group.update_config(SMON_ROLE_CONFIG)

    mgmt.start().wait()

    # Deploy parcel
    target_version = '5.5.1'
    parcel_version = [i.version for i in cm_cluster.get_all_parcels() if i.version.startswith(target_version)][0]
    parcel = {'name' : "CDH", 'version' : parcel_version }
    p = cm_cluster.get_parcel(parcel['name'], parcel['version'])
    p.start_download()
    while True:
        p = cm_cluster.get_parcel(parcel['name'], parcel['version'])
        if p.stage == "DOWNLOADED":
            break
        if p.state.errors:
            raise Exception(str(p.state.errors))
        print "Downloading %s: %s / %s" % (parcel['name'], p.state.progress, p.state.totalProgress)
        time.sleep(15)
    print "Downloaded %s" % (parcel['name'])
    p.start_distribution()
    while True:
        p = cm_cluster.get_parcel(parcel['name'], parcel['version'])
        if p.stage == "DISTRIBUTED":
            break
        if p.state.errors:
            raise Exception(str(p.state.errors))
        print "Distributing %s: %s / %s" % (parcel['name'], p.state.progress, p.state.totalProgress)
        time.sleep(15)
    print "Distributed %s" % (parcel['name'])
    p.activate()

        # Deploy zookeeper
    ZOOKEEPER_HOSTS = list(cm_hosts_ids[:3])
    ZOOKEEPER_SERVICE_NAME = "ZOOKEEPER"
    ZOOKEEPER_SERVICE_CONFIG = {
       'zookeeper_datadir_autocreate': 'true',
    }
    ZOOKEEPER_ROLE_CONFIG = {
        'quorumPort': 2888,
        'electionPort': 3888,
        'dataLogDir': '/var/lib/zookeeper',
        'dataDir': '/var/lib/zookeeper',
        'maxClientCnxns': '1024',
    }

    zk = cm_cluster.create_service(ZOOKEEPER_SERVICE_NAME, "ZOOKEEPER")
    zk.update_config(ZOOKEEPER_SERVICE_CONFIG)

    zk_id = 0
    for zk_host in ZOOKEEPER_HOSTS:
        zk_id += 1
        ZOOKEEPER_ROLE_CONFIG['serverId'] = zk_id
        role = zk.create_role(ZOOKEEPER_SERVICE_NAME + "-" + str(zk_id), "SERVER", zk_host)
        role.update_config(ZOOKEEPER_ROLE_CONFIG)
    zk.init_zookeeper()
