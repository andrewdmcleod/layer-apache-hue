#import jujuresources
from charms.reactive import when, when_not, when_file_changed
from charms.reactive import set_state, remove_state
from charmhelpers.core import hookenv
#from jujubigdata import utils
#from charmhelpers.fetch import apt_install
#from subprocess import check_call
from charms.hue import Hue
from charms.hadoop import get_dist_config

#DIST_KEYS = ['hadoop_version', 'groups', 'users', 'dirs', 'ports']

#def get_dist_config(keys):
#    from jujubigdata.utils import DistConfig
#
#    if not getattr(get_dist_config, 'value', None):
#        get_dist_config.value = DistConfig(filename='dist.yaml', required_keys=keys)
#    return get_dist_config.value


@when_not('hadoop.related')
def missing_hadoop():
    hookenv.status_set('blocked', 'Waiting for relation to Hadoop Plugin')


@when('hadoop.related')
@when_not('hadoop.ready')
def report_waiting(hadoop):
    hookenv.status_set('waiting', 'Waiting for Hadoop to become ready')


@when('hadoop.ready')
@when_not('hue.installed')
def install_hue(hadoop):
    dist = get_dist_config()
    hue = Hue(dist)
    #hue = Hue(get_dist_config(DIST_KEYS))
    if hue.verify_resources():
        hookenv.status_set('maintenance', 'Installing Hue')
        dist.add_users()
        dist.add_dirs()
        dist.add_packages()
        hue.install()
        set_state('hue.installed')


@when('hue.installed', 'hadoop.ready')
@when_not('hue.configured')
def configure_hue(hadoop):
    namenodes = hadoop.namenodes()
    resmngmrs = hadoop.resourcemanagers()
    hdfs_port = hadoop.hdfs_port()
    yarn_port = hadoop.yarn_port()
    yarn_http = hadoop.yarn_hs_http_port()
    yarn_ipcp = hadoop.yarn_hs_ipc_port()
    hookenv.log("hs http, hs ipc: " + yarn_http + ", " + yarn_ipcp)
    hookenv.status_set('maintenance', 'Setting up Hue')
    hue = Hue(get_dist_config())
    hue.setup_hue(namenodes, resmngmrs, hdfs_port, yarn_port, yarn_http, yarn_ipcp)
    set_state('hue.configured')
    hookenv.status_set('active', 'Ready')


@when('hue.installed', 'hadoop.ready', 'hue.configured')
@when_not('hue.started')
def start_hue(hadoop):
    hookenv.status_set('maintenance', 'Setting up Hue')
    hue = Hue(get_dist_config())
    hue.open_ports()
    # start it!
    set_state('hue.started')
    hookenv.status_set('active', 'Ready')


@when('hue.started')
@when_not('hive.joined')
def missing_hive():
    hookenv.status_set('waiting', 'Waiting for relation to Hive')
        

#@when('hue.started')
#@when_not('hive.joined')
#def waiting_hive(hive):
#    hookenv.status_set('waiting', 'Waiting for Hive to be available')


@when('hue.started', 'hive.joined')
def configure_hive(hive):
    dist = get_dist_config()
    hue = Hue(dist)
    hive_host = hive.get_hostname()
    hive_port = hive.get_port()
    hue.configure_hive(hive_host, hive_port)
    hookenv.log("HIVE Hostname and port: " + hive_host + ":" + str(hive_port))

@when('hue.started')
@when_file_changed('/etc/hue/conf/hue.ini')
def restart_hue():
    dist = get_dist_config()
    hue = Hue(dist)
    hue.stop()
    hue.start()


#@when('hue.started')
#@when_not('hadoop.ready')
#def stop_hue():
#    hue.stop()
#    remove_state('hue.started')
#    hookenv.status_set('blocked', 'Waiting for Hadoop connection')
