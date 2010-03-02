#!/usr/bin/python
import logging
import os
import sys
import shutil
import subprocess
import urllib2
import urllib

import simplejson


_NAME = os.path.splitext(sys.argv[0])[0]
_CONFIG_SERVER = "https://accounts.seedboxhosting.com/hosts"
# https://accounts.seedboxhosting.com/hosts/pear.s33db0x.com


# general use funcs

def log(msg, level='info'):
    log = eval('logging.%s' % str(level))
    log('%s: %s' % (_NAME, msg))

def run_command(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, *args,
                **kwargs):
    if not isinstance(command, (list, tuple)):
        command = tuple(command.split())
    log('run_command: creating runner with command: %s' % str(command))
    runner = subprocess.Popen(command, stdout=stdout, stderr=stderr, *args, 
        **kwargs)
    stdoutdata, stderrdata = runner.communicate()
    log('run_command: returncode: %s' % str(runner.returncode))
    log('run_command: stdout:\n%s' % stdoutdata)
    log('run_command: stderr:\n%s' % stderrdata)
    return (stdoutdata, stderrdata, runner)


# json functions

def get_server_config(hostname):
    config_url = '%s/%s' % (_CONFIG_SERVER, hostname)
    log('get_server_config: %s' % config_url)
    try:
        config_url_f = urllib2.urlopen(config_url, timeout=30)
        config = simplejson.load(config_url_f)
    except:
        config = { 
            'fqdn': hostname,
            'netmask': '255.255.255.0',
            'password': 'password',
            'gateway': '192.168.1.1',
            'ip': '192.168.1.100',
            'hostname': hostname,
            'suite': 'karmic',
            'ns1': '8.8.8.8',
            'ns2': '8.8.4.4',
        }
    if 'suite' not in config:
        config['suite'] = 'karmic'
    if 'ns1' not in config:
        config['ns1'] = '8.8.8.8'
        config['ns2'] = '8.8.4.4'
    return config
    #{"fqdn":"pear.s33db0x.com","netmask":"255.255.255.192","password":"Q3K5friNu45cre","gateway":"208.73.224.65","ip":"208.73.224.88","hostname":"pear"}
    #config = '{"hostname": "%s", "ipaddress": "204.9.240.100", "netmask": \
    #          "255.255.255.0", "gateway": "204.9.240.1", "ns1": "8.8.8.8", \
    #          "ns2": "8.8.4.4", "suite": "karmic" }' % str(hostname)


# package configuration functions

def update_apt_sources_list(config):
    sources = '''
# Packages
deb http://mirror01.noservr.com/ubuntu/ %(suite)s main restricted universe multiverse
deb-src http://mirror01.noservr.com/ubuntu/ %(suite)s main restricted universe multiverse

# Updates
deb http://mirror01.noservr.com/ubuntu/ %(suite)s-updates main restricted universe multiverse
deb-src http://mirror01.noservr.com/ubuntu/ %(suite)s-updates main restricted universe multiverse

# Security Updates
deb http://security.ubuntu.com/ubuntu %(suite)s-security main restricted universe multiverse
deb-src http://security.ubuntu.com/ubuntu %(suite)s-security main restricted universe multiverse

# Backports
# deb http://mirror01.noservr.com/ubuntu/ %(suite)s-backports main restricted universe multiverse
# deb-src http://mirror01.noservr.com/ubuntu/ %(suite)s-backports main restricted universe multiverse

# Partners
# deb http://archive.canonical.com/ubuntu %(suite)s partner
# deb-src http://archive.canonical.com/ubuntu %(suite)s partner
    ''' % config
    log('update_apt_sources_list:\n%s' % sources)
    with open('/etc/apt/sources.list', 'w') as sources_f:
        sources_f.write(sources)

def apt_upgrade(config):
    update_apt_sources_list(config)
    log('apt_upgrade: updating')
    stdout, stderr, apt_update = run_command('aptitude -y update')
    log('apt_upgrade: safe-upgrading')
    stdout, stderr, apt_update = run_command('aptitude -y safe-upgrade')
    
def apt_install(packages):
    if not isinstance(packages, (list, tuple)):
        packages = tuple(packages.split(','))
    stdout, stderr, runner = run_command('aptitude -y install %s' % (
        ' '.join(packages)))
    if runner.returncode != 0:
        log('apt_install: failed to install or configure packages %s\n%s' % (
            ','.join(packages), stderr))
    else:
        log('apt_install: success for packages %s\n%s' % ( 
            ','.join(packages), stdout))


# network config funcs

def setup_interfaces(config):
    interfaces = 'auto lo\niface lo inet loopback\n\n'
    interfaces += '''auto eth0
iface eth0 inet static
    address %(ip)s
    netmask %(netmask)s
    gateway %(gateway)s
''' % config
    log('setup_interfaces:\n%s' % interfaces)
    with open('/etc/network/interfaces', 'w') as interfaces_f:
        interfaces_f.write(interfaces)
    
def setup_resolv(config):
    domainname = '.'.join(config['fqdn'].split('.')[1:])
    resolv = 'domain %s\nsearch %s\nnameserver %s\nnameserver %s'
    resolv = resolv % (domainname, domainname, config['ns1'], config['ns2'])
    log('setup_resolv:\n%s' % resolv)
    with open('/etc/resolv.conf', 'w') as resolv_f:
        resolv_f.write(resolv)
    
def setup_hosts(config):
    config['alias'] = config['fqdn'].split('.')[0]
    hosts = '''
127.0.0.1 localhost.localdomain localhost
%(ip)s %(fqdn)s %(alias)s

fe00::0 ip6-localnet
ff00::0 ip6-mcastprefix
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters
ff02::3 ip6-allhosts
::1     localhost-ipv6  ip6-localhost   ip6-loopback
''' % config
    log('setup_hosts:\n%s' % hosts)
    with open('/etc/hosts', 'w') as hosts_f:
        hosts_f.write(hosts)

def setup_network_files(config):
    setup_interfaces(config)
    setup_resolv(config)
    setup_hosts(config)


# kernel and bootloader funcs

def install_kernel(config):
    apt_install('linux-image-server')

def install_grub2(config):
    apt_install('grub-pc')
    with open('/boot/grub/device.map', 'w') as devmap_f:
        devmap_f.write('(hd0) /dev/vda\n')
    stdout, stderr, update_grub = run_command('update-grub')
    #stdout, stderr, update_grub = run_command('grub-install /dev/vda')
    #stdout, stderr, update_grub = run_command('grub-install --recheck /dev/vda')


# serial port setup funcs

def setup_serial(config):
    try:
        serial_setup = eval('setup_serial_%s' % config['suite'])
        log('setup_serial: suite found %s' % config['suite'])
    except:
        serial_setup = setup_serial_inittab
        log('setup_serial: suite not found %s, reverting to inittab' % (
            config['suite']))
    serial_setup(config)

def setup_serial_inittab(config):
    serial = 'T0:23:respawn:/sbin/getty -L ttyS0 115200 vt100\n'
    with open('/etc/inittab', 'a') as serial_f:
        serial.f.write(serial)

def setup_serial_intrepid(config):
    serial = '''
# ttyS0 - getty
#
# This service maintains a getty on ttyS0 from the point the system is
# started until it is shut down again.

start on runlevel 2
start on runlevel 3
start on runlevel 4
start on runlevel 5

stop on runlevel 0
stop on runlevel 1
stop on runlevel 6

respawn
exec /sbin/getty 115200 ttyS0
'''
    with open('/etc/event.d/ttyS0', 'w') as serial_f:
        serial_f.write(serial)

def setup_serial_karmic(config):
    serial = '''
# ttyS0 - getty
#
# This service maintains a getty on ttyS0 from the point the system is
# started until it is shut down again.

start on stopped rc RUNLEVEL=[2345]
stop on runlevel [!2345]

respawn
exec /sbin/getty -L 115200 ttyS0 vt102
'''
    with open('/etc/init/ttyS0.conf', 'w') as serial_f:
        serial_f.write(serial)


# user and auth funcs

def delete_root_passwd(config):
    stdout, stderr, runner = run_command('passwd -d root')
    log('delete_root_passwd: root passwd deleted')

# main funcs

def read_hostname():
    return open('/etc/hostname', 'r').read().strip()

def main():
    config = get_server_config(read_hostname())
    apt_upgrade(config)
    setup_network_files(config)
    install_kernel(config)
    install_grub2(config)
    setup_serial(config)
    delete_root_passwd(config)


if __name__ == '__main__':
    logfile = os.path.join('/', '%s.log' % _NAME)
    logging.basicConfig(level=logging.DEBUG,filename=logfile)
    main()
    #logging.basicConfig(level=logging.DEBUG)
    #print get_server_config('pear.s33db0x.com')

