#!/usr/bin/python
import logging
import os.path

from utils import run_command_or_raise


@run_command_or_raise
def gnt_instance_list(output=['name',]):
    output = ','.join(output)
    return ('gnt-instance list --no-headers --output=%s' % output,
        'gnt_instance_list')

@run_command_or_raise
def gnt_node_list(output=['name',]):
    output = ','.join(output)
    return ('gnt-node list --no-headers --output=%s' % output,
        'gnt_node_list')

@run_command_or_raise
def gnt_cluster_command(command, nodes=[]):
    nodestr = ''
    for node in nodes:
        nodestr += ' --node=' + node
    return ('gnt-cluster command %s %s' % (nodestr, command),
        'gnt_cluster_command')

@run_command_or_raise
def gnt_cluster_copyfile(filename, nodes=[]):
    if not os.path.exists(filename):
        raise Exception('file not found: %s' % filename)
    nodestr = ''
    for node in nodes:
        nodestr += ' --node=' + node
    return ('gnt-cluster copyfile %s %s' % (nodestr, filename),
        'gnt_cluster_copyfile')

@run_command_or_raise
def gnt_cluster_getmaster():
    return 'gnt-cluster getmaster', 'gnt_cluster_getmaster'


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    instances = gnt_instance_list().splitlines()
    nodes = gnt_node_list().splitlines()
    print 'instances: ', instances
    print 'nodes: ', nodes
    print gnt_cluster_command('ls -la /', nodes=nodes)
    filename = '/tmp/testthis.txt'
    with open(filename, 'w') as testfile:
        testfile.write('this is a test!\n')
    print gnt_cluster_copyfile(filename, nodes=nodes)
    print gnt_cluster_command('cat %s' % filename, nodes=nodes)
    print gnt_cluster_command('rm %s' % filename, nodes=nodes)

    
