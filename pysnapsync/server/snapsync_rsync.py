# coding=utf-8
"""snapsync_rsync wrapper script.

This module implements the snapsync_rsync wrapper script.
"""


from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import os
import re
import shlex
import subprocess
import sys


class Fail(Exception):
    """General exception for all script failures."""

    pass


def background():
    """Fork into background."""
    pid = os.fork()

    if pid == 0:
        os.setsid()
        pid = os.fork()

    if pid != 0:
        os._exit(0)  # pylint: disable=locally-disabled,protected-access

    os.closerange(0, 2)


def main_log(host, args):
    """Write stdin to logfile."""
    if args[0] != "rbak-rsync-log":
        raise Fail("Invalid command")

    snap = args[1]

    with open("/backup/btrfs/{0}/logs/{1}.client.log".format(host, snap), 'w') as log:
        for line in sys.stdin:
            print(line, file=log, end="")

    exit(0)


def main():
    """Validate parameters and execute rsync."""
    match = re.match(r"^rsync([a-z0-9-]+)$", os.environ['USER'])
    if not match:
        raise Fail("Invalid username")
    host = match.group(1)

    args = shlex.split(os.environ['SSH_ORIGINAL_COMMAND'])

    if len(args) == 0:
        raise Fail("No arguments")

    if len(args) == 2:
        main_log(host, args)

    if len(args) < 4:
        raise Fail("Insufficient arguments")
    if args[0] != 'rsync':
        raise Fail("First argument not 'rsync'")

    if not re.match(r"^[0-9]{8}T[0-9]{4}Z$", args[1]):
        raise Fail("Invalid snapshot id")

    if args[2] != '--server':
        raise Fail("Second argument not '--server'")

    snap = args.pop(1)

    log = "/backup/btrfs/{0}/logs/{1}".format(host, snap)

    args.insert(2, "--log-file={0}.rsync.log".format(log))
    args.insert(3, "--log-file-format=")

    with open("{0}.rsync.err".format(log), 'w') as err:
        subprocess.check_call(
            args,
            executable="/usr/bin/rsync",
            stderr=err)

    background()

    with open("{0}.btrfs.out".format(log), 'w') as out, \
            open("{0}.btrfs.err".format(log), 'w') as err:

        subprocess.check_call(
            ['btrfs', 'subvolume', 'snapshot', '-r',
             '/backup/btrfs/{0}/sync'.format(host),
             '/backup/btrfs/{0}/{1}'.format(host, snap)],
            stdout=out, stderr=err)
