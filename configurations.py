#!/usr/bin/python
""" configurations """
import logging
import ConfigParser


from disk import FSTYPES
from disk import parse_disk_configuration

SUITES  = ('karmic',)
ARCHS   = ('amd64', 'x86')


class ValidatingConfigParser(ConfigParser.SafeConfigParser):
    required = {}
    def __init__(self, path, read=False, *args, **kwargs):
        self.path = path
        ConfigParser.SafeConfigParser.__init__(self, *args, **kwargs)
        #if read is not False:
        #    self.read()

    def validate_config(self):
        """ validates the current state of the configuration then asks
        validate_config custom to do the same
        """
        # validate that all required sections and keys exist
        for section in self.required:
            for config_key in self.required[section]:
                if not self.has_option(section, config_key):
                    raise KeyError('%s required config item not found: %s' % (
                        self.__class__.__name__, config_key))

    def read(self, *args, **kwargs):
        logging.debug('%s loading configuration file: %s' % (
            self.__class__.__name__, self.path))
        ConfigParser.SafeConfigParser.read(self, self.path, *args, **kwargs)
        self.validate_config()

    def write(self):
        self.validate_config()
        with open(self.path, 'w') as configfile:
            ConfigParser.SafeConfigParser.write(self, configfile)
        logging.info('%s configuration file written to disk: %s' % (
            self.__class__.__name__, self.path))


class OsConfiguration(ValidatingConfigParser):
    required = {
        'os': ('name', 'arch', 'suite', 'packages', 'disks',),
        'cache': ('tarball_path',),
    }
    def __init__(self, path, name='', arch='', suite='', chroot_script='',
                 tarball_path='', disks=[], packages=[], *args, **kwargs):
        ValidatingConfigParser.__init__(self, path, *args, **kwargs)
        self.add_section('os')
        self.add_section('cache')
        self.set('os', 'name', name)
        self.set('os', 'arch', arch)
        self.set('os', 'suite', suite)
        self.set('os', 'chroot_script', chroot_script)
        self.set('cache', 'tarball_path', tarball_path)
        self.set('os', 'packages', ','.join(packages))
        self.set('os', 'disks', ','.join(disks))
    
    def validate_config(self):
        ValidatingConfigParser.validate_config(self)
        for disk in self.get('os', 'disks').split(','):
            parsed_disk = parse_disk_configuration(disk)
        if not self.get('os', 'disks'): #and update is not True:
            raise ValueError('%s no disks have been defined' %
                self.__class__.__name__)


class CoreConfiguration(ValidatingConfigParser):
    required = { 
        'core': ('os_configs_dir', 'core_dir',),
        'os': ('ganeti_os_dir', 'default_suite', 'default_arch'),
        'cache': ('tarball_dir',),
    }
    def __init__(self, *args, **kwargs):
        ValidatingConfigParser.__init__(self, *args, **kwargs)
        self.read()


