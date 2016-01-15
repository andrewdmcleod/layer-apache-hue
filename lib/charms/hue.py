import jujuresources
from jujubigdata import utils
from charmhelpers.core import unitdata
from charmhelpers import fetch

from shutil import copy, copyfile
import os

# Main Hue class for callbacks
class Hue(object):

    def __init__(self, dist_config):
        self.dist_config = dist_config
        self.cpu_arch = utils.cpu_arch()
        self.resources = {
            'hue': 'hue-%s' % self.cpu_arch,
        }
        self.verify_resources = utils.verify_resources(*self.resources.values())

    def is_installed(self):
        return unitdata.kv().get('hue.installed')

    def pre_install(self):
        hue_version = jujuresources.config_get("hue-version")
        packages = [
            "ant",
            "g++",
            "libsasl2-modules-gssapi-mit",
            "libtidy-0.99-0",
            "python2.7-dev",
            "maven",
            "python-dev",
            "python-simplejson",
            "python-setuptools",
            "make",
            "libsasl2-dev",
            "libmysqlclient-dev",
            "libkrb5-dev",
            "libxml2-dev",
            "libxslt-dev",
            "libxslt1-dev",
            "libsqlite3-dev",
            "libssl-dev",
            "libldap2-dev",
            "python-pip"
        ]
        fetch.apt_install(packages)

    def install(self, force=False):
        if not force and self.is_installed():
            return
        self.pre_install()
        jujuresources.install(self.resources['hue'],
                              destination=self.dist_config.path('hue'),
                              skip_top_level=True)
        self.dist_config.add_users()
        self.dist_config.add_dirs()

        unitdata.kv().set('hue.installed', True)
        unitdata.kv().flush(True)

    def setup_hue(self):
        hue_bin = self.dist_config.path('hue') / 'bin'
        with utils.environment_edit_in_place('/etc/environment') as env:
            if hue_bin not in env['PATH']:
                env['PATH'] = ':'.join([env['PATH'], hue_bin])
            env['HADOOP_BIN_DIR'] = env['HADOOP_HOME'] + '/bin'
            env['GOBBLIN_WORK_DIR'] = self.dist_config.path('outputdir')
            hadoop_conf = env['HADOOP_CONF_DIR'] + '/core-site.xml'
        
        with utils.xmlpropmap_edit_in_place(hadoop_conf) as props:
            hdfs_endpoint = props['fs.defaultFS']

        default_conf = self.dist_config.path('hue') / 'desktop/conf'
        hue_conf = self.dist_config.path('hue_conf')
        hue_conf.rmtree_p()
        default_conf.copytree(hue_conf)
        # Now remove the conf included in the tarball and symlink our real conf
        default_conf.rmtree_p()
        hue_conf.symlink(default_conf)

        hue_config = ''.join((self.dist_config.path('hue'), '/desktop/conf/hue.ini'))
        hue_port = self.dist_config.port('hue_web')

        utils.re_edit_in_place(hue_config, {
            r'http_port=8888': 'http_port=%s' % hue_port,
            r'fs.uri=hdfs://localhost:8020': 'fs.uri=%s' % hdfs_endpoint,                
            })
