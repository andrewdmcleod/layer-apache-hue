from charms.reactive import when, when_not, when_file_changed
from charms.reactive import set_state, remove_state
from charms.reactive.bus import get_states
from charmhelpers.core import hookenv
from charms.hue import Hue
from charms.hadoop import get_dist_config


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


@when('hue.installed', 'hadoop.ready', 'hue.configured')
@when_not('hue.started')
def start_hue(hadoop):
    hookenv.status_set('maintenance', 'Setting up Hue')
    hue = Hue(get_dist_config())
    hue.open_ports()
    hue.start()
    set_state('hue.started')

if 'hue.started' in get_states():
    @when_file_changed('/etc/hue/conf/hue.ini')
    def restart_hue():
        # Can't seem to mix @when_file_changed and @when('hue.started')
        hue.restart()


@when('hue.started', 'hadoop.ready')
def check_relations(*args):
    hue.check_relations()


@when('hue.started', 'hive.ready')
def configure_hive(hive):
    hive_host = hive.get_private_ip()
    hive_port = hive.get_port()
    hue.configure_hive(hive_host, hive_port)
    set_state('hive.configured')


@when('hue.started', 'spark.ready')
def configure_spark(spark):
    spark_host = spark.get_private_ip()
    spark_rest_port = spark.get_rest_port()
    hue.configure_spark(spark_host, spark_rest_port)
    set_state('spark.configured')


@when('hue.started', 'oozie.ready')
def configure_oozie(oozie):
    oozie_host = oozie.get_private_ip()
    oozie_port = oozie.get_port()
    hue.configure_oozie(oozie_host, oozie_port)
    set_state('oozie.configured')


@when('hue.started', 'hive.configured')
@when_not('hive.joined')
def depart_hive():
    remove_state('hive.configured')


@when('hue.started', 'oozie.configured')
@when_not('oozie.joined')
def depart_oozie():
    remove_state('oozie.configured')


@when('hue.started', 'spark.configured')
@when_not('spark.joined')
def depart_spark():
    remove_state('spark.configured')


@when('hue.started')
@when_not('hadoop.ready')
def stop_hue():
    hue.stop()
    remove_state('hue.started')
    hookenv.status_set('blocked', 'Waiting for Hadoop connection')
