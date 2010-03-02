#!/usr/bin/python
import logging
import os.path
import StringIO

from utils import run_command_or_raise


def write_hosts(basepath, hostname):
    alias = hostname.split('.')[0]
    hosts_path = os.path.join(basepath, 'etc', 'hosts')
    hosts_list = (
        ('127.0.0.1', 'localhost.localdomain\t\tlocalhost'),
        ('127.0.0.1', '%s\t\t%s' % (hostname, alias)),
        ('fe00::0', 'ip6-localnet'),
        ('ff00::0', 'ip6-mcastprefix'),
        ('ff02::1', 'ip6-allnodes'),
        ('ff02::2', 'ip6-allrouters'),
        ('ff02::3', 'ip6-allhosts'),
    )
    hosts = StringIO.StringIO()
    for ip, host in hosts_list:
        hosts.write('%s\t\t%s\n' % (ip, host))
    hosts = hosts.getvalue()
    logging.debug('write_hosts writing to %s content: %s' % (hosts_path, hosts))
    with open(hosts_path, 'w') as hosts_file:
        hosts_file.write(hosts)
    hostname_path = os.path.join(basepath, 'etc', 'hostname')
    with open(hostname_path, 'w') as hostname_file:
        hostname_file.write('%s\n' % hostname)
            
def write_interfaces(basepath, number=1):
    interfaces = StringIO.StringIO()
    interfaces.write('auto lo\niface lo inet loopback\n\n')
    for i in range(0, int(number)):
        interfaces.write('auto eth%s\niface eth%s inet dhcp\n\n' % (i, i))
    interfaces_path = os.path.join(basepath, 'etc', 'network', 'interfaces')
    interfaces = interfaces.getvalue()
    logging.debug('write_interfaces writing to %s: %s' % (interfaces_path,
        interfaces))
    with open(interfaces_path, 'w') as interfaces_file:
        interfaces_file.write(interfaces)

@run_command_or_raise
def hostname_fqdn():
    return 'hostname --fqdn', 'get_hostname'
    

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    write_hosts('/tmp', 'test1.seedboxcloud.com')
    write_interfaces('/tmp', number=10)
