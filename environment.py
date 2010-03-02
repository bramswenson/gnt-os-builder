#!/usr/bin/python
""" environment.py """
import logging
import os
import sys


GANETI_ENVIRON_VARS = ( 'OS_API_VERSION', 'INSTANCE_NAME', 'INSTANCE_OS', 
                        'HYPERVISOR', 'DISK_COUNT', 'NIC_COUNT',
                        'DEBUG_LEVEL' )

def count_is_valid(count):
    try:
        int(count)
        return True
    except ValueError:
        return False

def get_ganeti_disk_env_vars(disk_count):
    disk_var_name_templates = ( 'DISK_%s_PATH', 'DISK_%s_ACCESS', 'DISK_%s_FRONTEND_TYPE' )
    disk_var_names = []
    for dc in range(0, int(disk_count)):
        disk_var_names += [ dvnt % str(dc) for dvnt in disk_var_name_templates ]
    return ((dck, os.environ.get(dck, None)) for dck in disk_var_names)


def get_ganeti_nic_env_vars(nic_count):
    nic_var_name_templates = ( 'NIC_%s_MAC', 'NIC_%s_IP', 'NIC_%s_BRIDGE',
                               'NIC_%s_FRONTEND_TYPE' )
    nic_var_names = []
    for nc in range(0, int(nic_count)):
        nic_var_names += [ nvnt % str(nc) for nvnt in nic_var_name_templates ]
    return ((nck, os.environ.get(nck, None)) for nck in nic_var_names)

def get_ganeti_environment():
    # get all the env variables into a dict
    ganeti_env = dict(((k, os.environ.get(k, None)) for k \
                        in GANETI_ENVIRON_VARS))

    # test that we have and env
    if ganeti_env['INSTANCE_NAME'] is None:
        logging.critical('cannot get environment variables')
        sys.exit(1)
        
    # get the disk and net vars
    if not count_is_valid(ganeti_env['DISK_COUNT']) or \
       not count_is_valid(ganeti_env['NIC_COUNT']):
        logging.critical('disk or nic count is invalid')
        sys.exit(1)
    ganeti_env.update(get_ganeti_disk_env_vars(ganeti_env['DISK_COUNT']))
    ganeti_env.update(get_ganeti_nic_env_vars(ganeti_env['NIC_COUNT']))
    return ganeti_env


