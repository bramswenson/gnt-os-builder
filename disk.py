#!/usr/bin/python
import logging
import string
import os
from StringIO import StringIO

import parted

from utils import run_command_or_raise


FSTYPES = {
    'swap': 0x82,
    'ext3': 0x83,
    'ext4': 0x83,
}    

SIZE_MULTIS = {
    'm': 1048576,
    'g': 1073741824,
    't': 1099511627776,
}

DISK_LETTER_MAP = dict(zip(range(0,26), string.letters[:26]))

def parse_disk_configuration(diskdef):
    ''' parses the disk string input provided to the gnt-os-builder command 
    --disk argument'''
    values = diskdef.split(':')

    if len(values) < 4:
        raise ValueError('disk definitions require at least 4 arguments')
    elif len(values) > 5:
        raise ValueError('disk definitions require at most 5 arguments')
    elif len(values) == 4:
        values.append(None)
    
    if values[3] not in FSTYPES:
        raise ValueError('disk definitions require one types %r' % FSTYPES)

    if values[4] is None and values[3] != 'swap':
        raise ValueError('disk definitions require a path argument')

    return {
        'disk': values[0],
        'part': values[1],
        'size': values[2],
        'fstype': values[3],
        'path': values[4],
    }

def size_to_bytes(size):
    # if last char is + save it
    size = str(size)
    grow = ''
    if size[-1] == '+':
        grow = '+'
        size = size[:-1]
    # get the size multiplyer
    if size[-1].lower() in SIZE_MULTIS:
        multiplyer = SIZE_MULTIS[size[-1].lower()]
        size = size[:-1]
    else:
        multiplyer = 1
    # make sure we have an int left
    size = str(int(size) * multiplyer)
    return size + grow

def size_bytes_to_int(size_bytes):
    if str(size_bytes)[-1] == '+':
        return int(size_bytes[:-1])
    else:
        return int(size_bytes)

def is_valid_fstype(fstype):
    return bool(fstype in FSTYPES)

def is_valid_path(path):
    if not path: return False
    path = path.strip()
    return bool(path[0] == '/')

def get_disk_size(path):
    device = parted.getDevice(path)
    return int(device.getSize(unit='b'))

def bytes_to_sectors(bytes, sector_size):
    return int(bytes) / sector_size

@run_command_or_raise
def mkfs_ext3(path, cmd_args=''):
    return 'mkfs.ext3 %s %s' % (path, cmd_args), 'mkfs_ext4'

@run_command_or_raise
def fsck_ext3(path, cmd_args='-y'):
    return 'fsck.ext3 %s %s' % (path, cmd_args), 'fsck_ext3'

@run_command_or_raise
def mkfs_ext4(path, cmd_args=''):
    return 'mkfs.ext4 %s %s' % (path, cmd_args), 'mkfs_ext4'

@run_command_or_raise
def fsck_ext4(path, cmd_args='-y'):
    return 'fsck.ext4 %s %s' % (path, cmd_args), 'fsck_ext4'

@run_command_or_raise
def mkfs_swap(path, cmd_args=''):
    return 'mkswap %s %s' % (path, cmd_args), 'mkfs_swap'

def fsck_swap(path, cmd_args=''):
   return

@run_command_or_raise
def mount(device, path, cmd_args=''):
    return 'mount %s %s %s' % (device, path, cmd_args), 'mount'

@run_command_or_raise
def umount(path, cmd_args=''):
    return 'umount %s %s' % (path, cmd_args), 'umount'

@run_command_or_raise
def rm_dev(path, cmd_args=''):
    return 'kpartx -d -v %s %s' % (path, cmd_args), 'rm_dev'

def write_fstab(basepath, disks):
    fsline = "%s\t\t%s\t\t%s\t%s\t%s\t%s\n"
    logging.debug('write_fstab line template: %s' % fsline)
    path = os.path.join(basepath, 'etc', 'fstab')
    fstab = StringIO()
    fstab.write('# created by gnt-os-builder\n')
    fstab.write("proc\t\t/proc\t\tproc\tdefaults\t0\t0\n")
    fstab.write("sys\t\t/sys\t\tsysfs\tdefaults\t0\t0\n")
    for disk in disks:
        for part in disk.partitions:
            if part.path == '/':
                fpass = 1
            elif part.path and part.path.startswith('/'):
                fpass = 2
            else:
                fpass = 0
            disk_letter = DISK_LETTER_MAP[int(disk.number)]
            disk_type = 'vd'
            devicepath = '/dev/%s%s%s' % (disk_type, disk_letter, 
                                          part.number)
            line = fsline % (devicepath, part.path, part.fstype, 'defaults',
                             '0', fpass)
            logging.debug('write_fstab formatted fsline: %s' % line)
            fstab.write(line)
    fstab = fstab.getvalue()
    logging.info('writing fstab to %s with contents %s' % (path, fstab))
    with open(path, 'w') as fstab_file:
        fstab_file.write(fstab)


class Partition(object):
    def __init__(self, disk, number, size, fstype, path=None):
        self.ppartition = None
        self.disk = disk
        self.number = int(number)
        self._size_bytes = size_to_bytes(size)
        if self.size_bytes[-1] == '+':
            self.grow = True
        else:
            self.grow = False
        self.fstype = fstype
        self.path = path

    def __str__(self):
        return '%s path=%s disk=%s number=%s size_bytes=%s \
                size_sectors=%s fstype=%s' % (
            self.__class__.__name__, self.path, self.disk, self.number,
            self.size_bytes, self.size_sectors, self.fstype)

    @property
    def size_sectors(self):
        return bytes_to_sectors(size_bytes_to_int(self.size_bytes),
                                self.disk.pdev.sectorSize)

    @property
    def size_bytes(self):
        return self._size_bytes

    @size_bytes.setter
    def size_bytes(self, size):
        self._size_bytes = size_to_bytes(size)

    def create_filesystem(self):
        logging.info('%s creating filesystem %s for partition %s at %s' % (
            self.__class__.__name__, self.fstype, self.number, 
            self.ppartition.path))
        mkfs = eval('mkfs_%s' % self.fstype)
        mkfs_out = mkfs(self.ppartition.path)
        logging.info('%s filesystem creation success: %s' % (
            self.__class__.__name__, mkfs_out))

    def check_filesystem(self, passes=4):
        for i in range(1, passes+1):
            logging.info('%s checking filesystem pass %s: %s' % (
                self.__class__.__name__, i, self.ppartition.path))
            fsck = eval('fsck_%s' % self.fstype)
            fsck_out = fsck(self.ppartition.path)
            logging.info('%s filesystem check success pass %s: %s' % (
                self.__class__.__name__, i, fsck_out))
            

class Disk(object):
    def __init__(self, number, path):
        self.number = number
        self.path = path
        self.pdev = parted.getDevice(path)
        self.pdisk = parted.freshDisk(self.pdev, 'msdos')
        if self.pdisk.deleteAllPartitions():
            self.pdisk.commit()
            logging.info('%s cleared all prexisting partitions from disk' % (
                self.__class__.__name__))
        self.size_bytes = get_disk_size(path)
        self.size_sectors = bytes_to_sectors(size_bytes_to_int(self.size_bytes),
                                             self.pdev.sectorSize)
        self.grow_part = False
        self._partitions = []

    def __str__(self):
        return '%s path=%s number=%s size_bytes=%s size_sectors=%s' % (
            self.__class__.__name__, self.path, self.number, self.size_bytes,
            self.size_sectors)

    @property
    def used_bytes(self):
        used_bytes = 0 # does this need to change for an mbr sector
        for part in self._partitions:
            s = part.size_bytes
            if s[-1] == '+':
                s = s[:-1]
            used_bytes += int(s)
        return used_bytes
    
    @property
    def free_bytes(self):
        return size_bytes_to_int(self.size_bytes) - self.used_bytes

    @property
    def used_sectors(self):
        used_sectors = 0
        for part in self._partitions:
            s = part.size_sectors
            used_sectors += int(s)
        return used_sectors
    
    @property
    def free_sectors(self):
        return self.size_sectors - self.used_sectors

    @property
    def partitions(self):
        return sorted(self._partitions, key=lambda part: part.number)

    def path_is_available(self, path):
        return bool([] == [ part for part in self._partitions if \
                            part.path == path ])

    def get_partition(self, number):
        part = [ p for p in self.partitions if int(p.number) == int(number) ]
        if not part:
            return None
        else:
            return part[0]

    def _grow_partition(self):
        if self.grow_part is not False and self.free_bytes >= 512:
            grow_part = self.get_partition(self.grow_part)
            new_size = size_bytes_to_int(grow_part.size_bytes) + self.free_bytes
            logging.info('%s growing partition %s from %s bytes to %s bytes' % (
                self.__class__.__name__, self.grow_part, grow_part.size_bytes,
                new_size))
            grow_part.size_bytes = new_size
            grow_part.size_sector = bytes_to_sectors(
                size_bytes_to_int(new_size),
                self.pdev.sectorSize)

    def commit(self):
        # make sure we grow the grow_part first
        self._grow_partition()
        logging.info('%s preparing to partition disk: %s' % (
            self.__class__.__name__, self.number))
        # get the free space part to find the start sector
        free_part = self.pdisk.getFreeSpacePartitions()[0]
        logging.debug('%s free space partition: %s' % (
            self.__class__.__name__, str(free_part)))
        logging.debug('%s free space geometry: %s' % (
            self.__class__.__name__, str(free_part.geometry)))
        start_sector = free_part.geometry.start
        for part in self.partitions:
            logging.info('%s preparing to create partition %s on disk %s' % (
                self.__class__.__name__, part.number, self.number))
            part_geom = parted.Geometry(device=self.pdev, start=start_sector,
                                        length=part.size_sectors)
            logging.info('%s partition expected geometry %s' % (
                self.__class__.__name__, part_geom))
            partition = parted.Partition(disk=self.pdisk, geometry=part_geom, 
                                         type=parted.PARTITION_NORMAL)
            logging.info('%s partition object %s' % (
                self.__class__.__name__, partition))
            part.ppartition = partition
            constraint = parted.Constraint(device=self.pdev)
            self.pdisk.addPartition(partition=part.ppartition,
                constraint=constraint)
            start_sector = part.ppartition.geometry.end + 1
        check = self.pdisk.check()
        if check is not True:
            raise Exception('%s sanity check run on disk %s failed' % (
                self.__class__.__name__, self.number))
        logging.info('%s sanity check run on disk %s returned %s' % (
            self.__class__.__name__, self.number, str(check)))
        self.pdisk.commit()
        logging.info('%s disk changes commited successfully:' % (
            self.__class__.__name__))
        logging.info('%s             %s' % (self.__class__.__name__,
            self.pdisk))
        # now create the filesystems
        self._create_filesystems()

    def _create_filesystems(self):
        for part in self.partitions:
            part.create_filesystem()

    def add_partition(self, number, size, fstype, path=None):
        # see if we have the free space
        size_bytes = size_to_bytes(size)
        size_bytes_int = size_bytes_to_int(size_bytes)
        if self.free_bytes < size_bytes_int:
            raise ValueError('%s not enough freespace for partition' % (
                self.__class__.__name__))
        else:
            logging.info('%s free space found %s of %s' % (
                self.__class__.__name__, size_bytes_int, self.free_bytes))
        # see if we are adding a growing part and even can
        if size_bytes[-1] == '+':
            if self.grow_part is not False:
                raise ValueError(
                    '%s disk cannont have multiple growing partitions' % (
                    self.__class__.__name__))
            else:
                self.grow_part = str(number)
                logging.debug(
                    '%s partition is set to grow to max possible size %s' % (
                    self.__class__.__name__, self.grow_part))
        # see if we supprt the fstype
        if not is_valid_fstype(fstype):
            raise ValueError('%s fstype not supported %s' % (
                self.__class__.__name__, fstype))
        # see if we have a path that is valid and available
        if path is None and fstype != 'swap':
            raise ValueError('%s non-swap partitions must have a mount path' % (
                self.__class__.__name__))
        if not is_valid_path(path) and fstype != 'swap':
            raise ValueError('%s path is invalid %s' % (
                self.__class__.__name__, path))
        if not self.path_is_available(path):
            raise ValueError('%s path is already in use %s' % (
                self.__class__.__name__, path))
        # see if we have an unused number
        if int(number) > 4:
            raise ValueError('%s partition number is greater than 4 %s' % (
                self.__class__.__name__, number))
        if number in [ int(part.number) for part in self.partitions ]:
            raise ValueError('%s partition number is already in use %s' % (
                self.__class__.__name__, number))
        # add the part object to self.partitions
        self._partitions.append(Partition(self, number, size, fstype, path))


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

