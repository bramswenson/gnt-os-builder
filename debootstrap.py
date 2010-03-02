#!/usr/bin/python
'''
Usage: debootstrap [OPTION]... <suite> <target> [<mirror> [<script>]]
Bootstrap Debian base system.

      --help                 display this help and exit
      --version              display version information and exit
      --verbose              don't turn off the output of wget

      --download-only        download packages, but don't perform installation
      --print-debs           print the packages to be installed, and exit

      --arch=A               set the target architecture (use if no dpkg)
                               [ --arch=powerpc ]

      --include=A,B,C        adds specified names to the list of base packages
      --exclude=A,B,C        removes specified packages from the list
      --components=A,B,C     use packages from the listed components of the
                             archive
      --variant=X            use variant X of the bootstrap scripts
                             (currently supported variants: buildd, fakechroot,
                              scratchbox)
      --keyring=K            check Release files against keyring K
      --no-resolve-deps      don't try to resolve dependencies automatically

      --unpack-tarball=T     acquire .debs from a tarball instead of http
      --make-tarball=T       download .debs and create a tarball (tgz format)
      --second-stage-target=DIR
                             Run second stage in a subdirectory instead of root
                               (can be used to create a foreign chroot)
                               (requires --second-stage)
      --boot-floppies        used for internal purposes by boot-floppies
      --debian-installer     used for internal purposes by debian-installer
'''
import logging
import sys
import os

from utils import run_command_or_raise


@run_command_or_raise
def debootstrap(suite, target, arch='', mirror='', script='', include=[]):
    if include != []:
        include = '--include=%s' % ','.join(include)
    else:
        include = ''
    if arch != '':
        arch = '--arch=%s' % arch
    else:
        arch = ''
    components = '--components=main,restricted,universe,multiverse'
    command = 'debootstrap --verbose %s %s %s %s %s %s %s' % (components, arch, 
        include, suite, target, mirror, script)
    return command, 'debootstrap'

@run_command_or_raise
def debootstrap_mktarball(suite, target, tarball_path, arch='', mirror='',
                          script='', include=[]):
    if include != []:
        include = '--include=%s' % ','.join(include)
    else:
        include = ''
    if arch != '':
        arch = '--arch=%s' % arch
    else:
        arch = ''
    components = '--components=main,restricted,universe,multiverse'
    command = 'debootstrap --verbose --make-tarball=%s %s %s %s %s %s %s %s' % (
        tarball_path, components, arch, include, suite, target, mirror, script)
    return command, 'debootstrap_mktarball'

@run_command_or_raise
def debootstrap_unpacktarball(suite, target, tarball_path, arch='', mirror='',
                              script='', include=[]):
    if include != []:
        include = '--include=%s' % ','.join(include)
    else:
        include = ''
    if arch != '':
        arch = '--arch=%s' % arch
    else:
        arch = ''
    components = '--components=main,restricted,universe,multiverse'
    command = 'debootstrap --verbose --unpack-tarball=%s %s %s %s %s %s %s %s' % (
        tarball_path, components, arch, include, suite, target, mirror, script)
    return command, 'debootstrap_unpacktarball'
#Usage: debootstrap [OPTION]... <suite> <target> [<mirror> [<script>]]

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
