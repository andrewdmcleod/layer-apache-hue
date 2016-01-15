import jujuresources
from charms.reactive import when, when_not
from charms.reactive import set_state, remove_state, is_state
from charmhelpers.core import hookenv
from charms.hadoop import get_hadoop_base
from jujubigdata import utils
from charmhelpers.fetch import apt_install
from subprocess import check_call
from charms.hue import Hue

DIST_KEYS = ['hadoop_version', 'groups', 'users', 'dirs', 'ports']

def get_dist_config(keys):
    from jujubigdata.utils import DistConfig

    if not getattr(get_dist_config, 'value', None):
        get_dist_config.value = DistConfig(filename='dist.yaml', required_keys=keys)
    return get_dist_config.value


#@when('hadoop.installed')
@when_not('hue.installed')
def install_hue():
    hue = Hue(get_dist_config(DIST_KEYS))
    if hue.verify_resources():
        hookenv.status_set('maintenance', 'Installing Hue')
        hue.install()
        set_state('hue.installed')


@when('hue.installed')
@when_not('hadoop.related')
def missing_hadoop():
    hookenv.status_set('blocked', 'Waiting for relation to Hadoop')


@when('hue.installed', 'hadoop.ready')
@when_not('hue.configured')
def configure_hue(*args):
    hookenv.status_set('maintenance', 'Setting up Hue')
    hue = Hue(get_dist_config(DIST_KEYS))
    hue.setup_hue()
    set_state('hue.configured')
    hookenv.status_set('active', 'Ready')


#@when('namenode.available')
#def update_etc_hosts(namenode):
#    utils.update_kv_hosts(namenode.hosts_map())
#    utils.manage_etc_hosts()
#    barry = hookenv.relation_get('hostname') + "Blah blah blH BLALH BLAKFLAS DHALKSJD"
#    hookenv.log(barry)
#
#@when('bootstrapped')
#@when_not('hadoop.connected')
#def missing_hadoop():
#    hookenv.status_set('blocked', 'Waiting for relation to Hadoop')
#
#
#@when('bootstrapped', 'hadoop.connected')
#@when_not('hadoop.ready')
#def waiting_hadoop(hadoop):
#    hookenv.status_set('waiting', 'Waiting for Hadoop to become ready')
#
#
@when('hue.installed', 'hadoop.ready')
@when_not('hue.started')
def start_hue(*args):
    hookenv.status_set('maintenance', 'Setting up Hue')
    hue = Hue(get_dist_config(DIST_KEYS))
    # start it!
    set_state('hue.started')
    hookenv.status_set('active', 'Ready')


#@when('hue.started')
#@when_not('hadoop.ready')
#def stop_hue():
#    self.dist_config.port('hue_web')
#    remove_state('hue.started')
#    hookenv.status_set('blocked', 'Waiting for Haddop connection')
