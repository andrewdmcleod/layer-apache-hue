# This charm is under construction and requires further work in these areas:

        oozie interface and configuration
        spark-livy interface and configuration

## Overview

Hue is an open-source Web interface that supports Apache Hadoop and its ecosystem

Hue aggregates the most common Apache Hadoop components into a single interface
and targets the user experience. Its main goal is to have the users "just use"
Hadoop without worrying about the underlying complexity or using a command line.

Features: File Browser for accessing HDFS, Beeswax application for executing
Hive queries, Impala App for executing Impala queries, Spark Editor and
Dashboard, Pig Editor for submitting Pig scripts, Oozie App for submitting and
monitoring workflows, coordinators and bundles, HBase Browser for exploring and
modifying HBase tables and data, Table Browser for accessing Hive metadata and
HCatalog, Search App for querying Solr and Solr Cloud, Job Browser for accessing
MapReduce jobs (MR1/MR2-YARN), Job Designer for creating
MapReduce/Streaming/Java jobs, A Sqoop 2 Editor and Dashboard, A ZooKeeper
Browser and Editor, A DB Query Editor for MySql, PostGres, Sqlite and Oracle, On
top of that, a SDK is available for creating new apps integrated with Hadoop.

## Usage

This charm leverages our pluggable Hadoop model with the `hadoop-plugin`
interface. This means that you will need to deploy a base Apache Hadoop cluster
to run Hue. The suggested deployment method is to use the
[BUNDLE WITH HUE](https://jujucharms.com/u/LINK LINK LINK/)
bundle. This will deploy the Apache Hadoop platform with a single Hue
unit that communicates with the cluster by relating to the
`apache-hadoop-plugin` subordinate charm:

    juju quickstart ????????????????????????????????????

Alternatively, you may manually deploy the recommended environment as follows:

    juju deploy apache-hadoop-namenode namenode
    juju deploy apache-hadoop-resourcemanager resourcemanager
    juju deploy apache-hadoop-slave slave
    juju deploy apache-hadoop-plugin plugin
    juju deploy hue hue
    juju deploy apache-hive hive
    juju deploy apache-oozie oozie
    juju deploy apache-spark spark
    juju deploy apache-spark-livy spark-livy
    ?? pig is a principal charm ??

    juju add-relation resourcemanager namenode
    juju add-relation slave resourcemanager
    juju add-relation slave namenode
    juju add-relation plugin resourcemanager
    juju add-relation plugin namenode
    juju add-relation plugin hue
    juju add-relation plugin hive
    juju add-relation plugin oozie
    juju add-relation plugin spark
    juju add-relation spark spark-livy
    juju add-relation hue hive
    juju add-relation hue oozie
    juju add-relation hue hive
    juju add-relation hue spark-livy

You will then need to manually expose hue:

    juju expose hue

And then browse to the HUE_IP:HUE_PORT shown in 'juju status --format tabular'

The reason for this is that the first login to hue via the web interface creates
the default admin user so we need to make sure you are the first person to 
log in.

## Contact Information

- <bigdata-dev@lists.launchpad.net>


## Help

- [HUE home page](http://gethue.com)
- [HUE bug tracker](https://issues.cloudera.org/projects/HUE)
- `#juju` on `irc.freenode.net`
