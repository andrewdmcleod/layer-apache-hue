import jujuresources
from jujubigdata import utils
from charmhelpers.core import unitdata, hookenv
from charmhelpers.core.host import chownr
from charms.reactive.bus import get_states
from charmhelpers import fetch
import os
import yaml

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
        #utils.run_as('root', 'chown', '-R', 'hue:hadoop', self.dist_config.path('hue'))
        chownr(self.dist_config.path('hue'), 'hue', 'hadoop')
        unitdata.kv().set('hue.installed', True)
        
    def check_relations(self):
        '''
        This function checks the 'additional_relations' list against the joined 
        relation states so we don't have to explicitly set_status in each reactive
        function
        '''
        additional_relations = []
        metadata_stream = open('metadata.yaml', 'r')
        data = yaml.load(metadata_stream)
        for key in data['requires']:
            additional_relations.append(key)
        current_relations = additional_relations
        all_states = get_states()
        for k, v in all_states.items():
            if "joined" in k:
                relname = k.split('.')[0]
                if relname in additional_relations:
                    current_relations.remove(relname)

        wait_rels = ', '.join(current_relations)
        if len(current_relations) > 0:
            hookenv.status_set('waiting', 'Waiting for relations: ' + wait_rels)
        else:
            hookenv.status_set('active', 'Ready')

    def setup_hue(self, namenodes, resourcemanagers, hdfs_port, yarn_port, yarn_http, yarn_ipc):
        hookenv.status_set('maintenance', 'Setting up Hue')
        hue_bin = self.dist_config.path('hue') / 'bin'
        with utils.environment_edit_in_place('/etc/environment') as env:
            if hue_bin not in env['PATH']:
                env['PATH'] = ':'.join([env['PATH'], hue_bin])
            env['HADOOP_BIN_DIR'] = env['HADOOP_HOME'] + '/bin'
            env['GOBBLIN_WORK_DIR'] = self.dist_config.path('outputdir')
            hadoop_conf = env['HADOOP_CONF_DIR'] + '/core-site.xml'
            yarn_conf = env['HADOOP_CONF_DIR'] + '/yarn-site.xml'
            mapred_conf = env['HADOOP_CONF_DIR'] + '/mapred-site.xml'

        with utils.xmlpropmap_edit_in_place(hadoop_conf) as props:
            hdfs_endpoint = props['fs.defaultFS']

        with utils.xmlpropmap_edit_in_place(yarn_conf) as props:
            yarn_log_url = props['yarn.log.server.url'] # 19888
            yarn_resmgr = props['yarn.resourcemanager.address'] # 8032

        with utils.xmlpropmap_edit_in_place(mapred_conf) as props:
            mapred_jobhistory = props['mapreduce.jobhistory.address'] # 10020

        default_conf = self.dist_config.path('hue') / 'desktop/conf'
        hue_conf = self.dist_config.path('hue_conf')

        if os.path.islink('/usr/lib/hue/desktop/conf'):
                return
        else:
                hue_conf.rmtree_p()
                default_conf.copytree(hue_conf)
                # Now remove the conf included in the tarball and symlink our real conf
                default_conf.rmtree_p()
                hue_conf.symlink(default_conf)
        
        hdfs_fulluri = hdfs_endpoint.split('/')[2]
        hdfs_hostname = hdfs_fulluri.split(':')[0]

        hue_config = ''.join((self.dist_config.path('hue'), '/desktop/conf/hue.ini'))
        hue_port = self.dist_config.port('hue_web')

        # Fix following for HA: http://docs.hortonworks.com/HDPDocuments/HDP2/HDP-2.3.0/bk_hadoop-ha/content/ha-nn-deploy-hue.html
        hookenv.log("Not currently supporting HA, FIX: namenodes are: " + str(namenodes) + " resmanagers: " + str(resourcemanagers))
        utils.re_edit_in_place(hue_config, {
            r'http_port=8888': 'http_port=%s' % hue_port,
            #r'fs_defaultfs=hdfs://localhost:8020': 'fs_defaultfs=%s' % hdfs_endpoint,
            r'fs_defaultfs=hdfs://localhost:8020': 'fs_defaultfs=%s:%s' % (namenodes[0], hdfs_port),
            #r'## resourcemanager_host=localhost': 'resourcemanager_host=%s' % yarn_resmgr.split(':')[0],
            r'.*resourcemanager_host=localhost': 'resourcemanager_host=%s' % resourcemanagers[0],
            #r'## resourcemanager_port=8032': 'resourcemanager_port=%s' % yarn_resmgr.split(':')[1],
            r'.*resourcemanager_port=8032': 'resourcemanager_port=%s' % yarn_port,
            r'.*webhdfs_url=http://localhost:50070/webhdfs/v1': 'webhdfs_url=http://%s:50070/webhdfs/v1' % namenodes[0],
            r'.*history_server_api_url=http://localhost:19888': 'history_server_api_url=%s' % yarn_log_url.split('/')[0],
            r'.*resourcemanager_api_url=http://localhost:8088': 'resourcemanager_api_url=http://%s:8088' % yarn_resmgr.split(':')[0]
            })

    def open_ports(self):
        for port in self.dist_config.exposed_ports('hue'):
            hookenv.open_port(port)

    def close_ports(self):
        for port in self.dist_config.exposed_ports('hue'):
            hookenv.close_port(port)

    def start(self):
        self.stop()
        hookenv.log("Starting HUE with Supervisor process")
        hue_log = self.dist_config.path('hue_log')
        utils.run_as('hue', '/usr/lib/hue/build/env/bin/supervisor', '-l', hue_log, '-d')

    def stop(self):
        hookenv.log("Stopping HUE and Supervisor process")
        try:
            utils.run_as('hue', 'pkill', '-9', 'supervisor')
            utils.run_as('hue', 'pkill', '-9', 'hue')
        except:
            return

    def restart(self):
        hookenv.log("Restarting HUE with Supervisor process")
        try:
            utils.run_as('hue', 'pkill', '-9', 'hue')
        except:
            hookenv.log("Problem with Supervisor process, doing hard HUE restart")
            self.stop()
            self.start()

    def configure_hive(self, hostname, port):
        hookenv.log("Configuring hive connection")
        hue_config = ''.join((self.dist_config.path('hue'), '/desktop/conf/hue.ini'))
        utils.re_edit_in_place(hue_config, {
            r'.*hive_server_host *=.*': 'hive_server_host=%s' % hostname,
            r'.*hive_server_port *=.*': 'hive_server_port=%s' % port
            })
          
    def configure_oozie(self):
        hookenv.log("configuring oozie connection")

    def configure_spark(self, hostname, port):
        hookenv.log("configuring spark connection via livy")
        hue_config = ''.join((self.dist_config.path('hue'), '/desktop/conf/hue.ini'))
        utils.re_edit_in_place(hue_config, {
            r'.*livy_server_host *=.*': 'hive_server_host=%s' % hostname,
            r'.*livy_server_port *=.*': 'hive_server_port=%s' % port
            })  

    def configure_impala(self):
        hookenv.log("configuring impala connection")

    def configure_sqoop(self):
        hookenv.log("configuring sqoop connection")

    def configure_hbase(self):
        hookenv.log("configuring hbase connection")

    def configure_solr(self):
        hookenv.log("configuring solr connection")

    def configure_zookeeper(self):
        hookenv.log("configuring zookeeper connection")

    def configure_aws(self):
        hookenv.log("configuring AWS connection")

    def configure_sentry(self):
        hookenv.log("configuring sentry connection")
