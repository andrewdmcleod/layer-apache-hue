import jujuresources
from charms.reactive import when, when_not
from charms.reactive import set_state, remove_state, is_state
from charmhelpers.core import hookenv
from jujubigdata import utils

def dist_config():
    from jujubigdata.utils import DistConfig  # no available until after bootstrap

    if not getattr(dist_config, 'value', None):
        hue_reqs = ['hadoop_version', 'groups', 'users', 'dirs']
        dist_config.value = DistConfig(filename='dist.yaml', required_keys=hue_reqs)
    return dist_config.value

#  http_host=0.0.0.0
#    http_port=8888
#
#      # Time zone name
#        time_zone=America/Los_Angeles

@when('bootstrapped')
@when_not('hue.installed')
def install_hue(*args):

    from charms.hue import Hue  # in lib/charms; not available until after bootstrap

    hue = Hue(dist_config())
    if hue.verify_resources():
        hookenv.status_set('maintenance', 'Installing Hue')
        hue.install()
        set_state('hue.installed')


@when('namenode.available')
def update_etc_hosts(namenode):
    utils.update_kv_hosts(namenode.hosts_map())
    utils.manage_etc_hosts()
    barry = hookenv.relation_get('hostname') + "Blah blah blH BLALH BLAKFLAS DHALKSJD"
    hookenv.log(barry)

@when('bootstrapped')
@when_not('hadoop.connected')
def missing_hadoop():
    hookenv.status_set('blocked', 'Waiting for relation to Hadoop')


@when('bootstrapped', 'hadoop.connected')
@when_not('hadoop.ready')
def waiting_hadoop(hadoop):
    hookenv.status_set('waiting', 'Waiting for Hadoop to become ready')


@when('hue.installed', 'hadoop.ready')
@when_not('hue.started')
def configure_hue(*args):
    from charms.hue import Hue # in lib/charms; not available until after bootstrap

    hookenv.status_set('maintenance', 'Setting up Hue')
    hue = Hue(dist_config())
    hookenv.open_port('8888')
    set_state('hue.started')
    hookenv.status_set('active', 'Ready')


@when('hue.started')
@when_not('hadoop.ready')
def stop_hue():
    self.dist_config.port('hue_web')
    remove_state('hue.started')
    hookenv.status_set('blocked', 'Waiting for Haddop connection')
