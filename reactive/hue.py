#import jujuresources
from charms.reactive import when, when_not, when_file_changed
from charms.reactive import set_state, remove_state
from charms.reactive.bus import get_state
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


dist = get_dist_config()
hue = Hue(dist)

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
    hookenv.status_set('maintenance', 'Setting up Hue')
    hue = Hue(get_dist_config())
    hue.setup_hue(namenodes, resmngmrs, hdfs_port,
                  yarn_port, yarn_http, yarn_ipcp)
    set_state('hue.configured')
    hookenv.status_set('active', 'Ready')


@when('hue.installed', 'hadoop.ready', 'hue.configured')
@when_not('hue.started')
def start_hue(hadoop):
    hookenv.status_set('maintenance', 'Setting up Hue')
    hue = Hue(get_dist_config())
    hue.open_ports()
    hue.start()
    set_state('hue.started')
    hookenv.status_set('active', 'Ready')


@when_file_changed('/etc/hue/conf/hue.ini')
def restart_hue():
    # Can't seem to mix @when_file_changed and @when...
    if get_state('hue.started'):
        hue.restart()
    else:
        return

@when('hue.started', 'hive.joined')
@when_not('hive.configured')
def configure_hive(hive):
    hive_host = hive.get_hostname()
    hive_port = hive.get_port()
    hue.relations(joined='Hive')
    if hive_port:
        hue.configure_hive(hive_host, hive_port)
    set_state('hive.configured')


@when('hue.started', 'spark.joined')
@when_not('spark.configured')
def configure_spark(spark):
    spark_host = spark.get_hostname()
    spark_port = spark.get_port()
    hue.relations(joined='Spark')
    if spark_port:
        hue.configure_spark(spark_host, spark_port)
    set_state('spark.configured')


@when('hue.started', 'oozie.joined')
@when_not('oozie.configured')
def configure_oozie(oozie):
    oozie_host = oozie.get_hostname()
    oozie_port = oozie.get_port()
    hue.relations(joined='Oozie')
    if oozie_port:
        hue.configure_oozie(oozie_host, oozie_port)
    set_state('oozie.configured')


@when('hue.started')
@when_not('hive.joined')
def depart_hive():
    hue.relations(departed='Hive')
    remove_state('hive.configured')


@when('hue.started')
@when_not('oozie.joined')
def depart_oozie():
    hue.relations(departed='Oozie')
    remove_state('oozie.configured')


@when('hue.started')
@when_not('spark.joined')
def depart_spark():
    hue.relations(departed='Spark')
    remove_state('spark.configured')


@when('hue.started')
@when_not('hadoop.ready')
def stop_hue():
    hue.stop()
    remove_state('hue.started')
    hookenv.status_set('blocked', 'Waiting for Hadoop connection')
