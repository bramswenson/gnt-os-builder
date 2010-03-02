#!/usr/bin/python
""" system commands """
import logging
import os
import sys
import subprocess

def run_command_or_raise(func, *args, **kwargs):
    def _inner(*args, **kwargs):
        command, msg = func(*args, **kwargs)
        stdoutdata, stderrdata, runner = run_command(command)
        if runner.returncode != 0:
            raise Exception(
                '%s command failure: %s' % (msg, stderrdata.strip()))
        else:
            return stdoutdata.strip()
    return _inner

def run_command_chrooted_or_raise(func, *args, **kwargs):
    def _inner(*args, **kwargs):
        if 'path' not in kwargs:
            raise Exception('chroot commands need a path')
        path = kwargs['path']
        del kwargs['path']
        command, msg = func(*args, **kwargs)
        command = 'chroot %s %s' % (path, command)
        stdoutdata, stderrdata, runner = run_command(command)
        if runner.returncode != 0:
            raise Exception(
                '%s command failure: %s' % (msg, stderrdata.strip()))
        else:
            return stdoutdata.strip()
    return _inner


def run_command(command=('ls', '/'), *args, **kwargs):
    if not isinstance(command, (list, tuple)):
        command = (command.split())
    logging.info("run_command called for command: %s" % str(command))
    for o in ['stdout', 'stderr']:
        if o not in kwargs:
            kwargs[o] = subprocess.PIPE
    logging.info("run_command called with kwargs: %r" % kwargs)
    runner = subprocess.Popen(command, *args, **kwargs)
    stdoutdata, stderrdata = runner.communicate()
    logging.debug('run_command return pid: %s' % runner.pid)
    logging.info('run_command return code: %s' % runner.returncode)
    logging.debug('run_command returned stdout: %s' % stdoutdata.strip())
    logging.debug('run_command returned stderr: %s' % stderrdata.strip())
    return (stdoutdata.strip(), stderrdata.strip(), runner)


def run_command_chrooted(chrootdir, command=('ls', '/'), *args, **kwargs):
    if not isinstance(command, (list, tuple)):
        command = (command.split())
    logging.info("run_command_chrooted called for command: %s" % str(command))
    command = ['chroot', chrootdir, ] + list(command)
    logging.info("run_command_chrooted real command: %s" % str(command))
    for o in ['stdout', 'stderr']:
        if o not in kwargs:
            kwargs[o] = subprocess.PIPE
    logging.info("run_command_chrooted called with kwargs: %r" % kwargs)
    runner = subprocess.Popen(command, *args, **kwargs)
    stdoutdata, stderrdata = runner.communicate()
    logging.debug('run_command_chrooted return pid: %s' % runner.pid)
    logging.info('run_command_chrooted return code: %s' % runner.returncode)
    logging.debug('run_command_chrooted returned stdout: %s' % stdoutdata.strip())
    logging.debug('run_command_chrooted returned stderr: %s' % stderrdata.strip())
    return (stdoutdata.strip(), stderrdata.strip(), runner)


class CleanupRunner(object):
    ''' allows running a series of commands that may need to be
    cleanupne in order if any command in the series fails. '''
    def __init__(self, *args, **kwargs):
        self.cleanup_queue = [ ]
        self.clean = False
        self.args = args
        self.kwargs = kwargs

    def add_cleanup_command(self, cleanup_command, *args, **kwargs):
        if self.clean:
            raise RuntimeError('cannot add cleanup commands to an already \
                                cleanupne instance')
        else:
            self.cleanup_queue.append((cleanup_command, args, kwargs))

    def run_cleanup_command(self, command, *args, **kwargs):
        # see if we are working with a local namespace command
        localname = False
        try:
            if callable(command):
                c = command
            else:
                c = eval(command)
            localname = True
        except:
            c = command

        if not localname:
            # run with run command
            logging.debug('%s running cleanup command: %s' % (
                self.__class__.__name__, command))
            stdoutdata, stderrdata, runner = run_command(command)
            if runner.returncode != 0:
                logging.warning('%s cleanup command returned non-zero: %s' % (
                    self.__class__.__name__, stderrdata))
            else:
                logging.debug('%s cleanup command success: %s' % (
                    self.__class__.__name__, stdoutdata))
        else:
            logging.debug('%s running cleanup command in local namespace: %s' % (
                self.__class__.__name__, command))
            try:
                results = c(*args, **kwargs)
            except:
                logging.warning(
                    '%s cleanup command in local namespace failed %s' % (
                    self.__class__.__name__, command))
            logging.debug('%s cleanup command success: %s' % (
                self.__class__.__name__, str(results)))

    def cleanup(self):
        if self.clean is not True:
            logging.info('%s run cleanup' % self.__class__.__name__)
            self.cleanup_queue.reverse() # run from last to first
            for command in self.cleanup_queue:
                self.run_cleanup_command(command[0], *command[1], **command[2])
            self.clean = True

    def __del__(self, *args, **kwargs):
        if self.clean is not True:
            self.cleanup()

    def run(self):
        return


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    run_command()
    run_command('ls -la /')
    run_command('ls /this/place/doesnt/exist')
    
    @run_command_or_raise
    def test_decorator_good():
        return 'ls -la /', 'ls root'

    @run_command_or_raise
    def test_decorator_bad():
        return 'ls /this/place/doesnt/exist', 'ls no good'

    test_decorator_good()
    test_decorator_bad()


