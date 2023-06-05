#!/usr/bin/env python
# coding=utf-8
#
# test.py - LVM/btrfs snapshots + rsync backup utility [win32 test]
#
# Released under GPLv3, see LICENCE
#
# Copyright © 2016  David Taylor <davidt@yadt.uk>
#
"""snapsync script.

This module implements the snapsync script. TEST VERSION FOR W32
"""


from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import argparse
import collections
from datetime import datetime
import os
import subprocess
import sys
import yaml
from pykwalify.core import Core
from pkg_resources import resource_stream


class Config(object):
    """Store configuration."""

    config = {}

    def load(self, config_file):
        """Load configuration from config_file."""
        with resource_stream(__name__, 'config-schema.yaml') as schema_stream:
            schema = yaml.safe_load(schema_stream)

        core = Core(source_file=config_file, schema_data=schema)
        self.config = core.validate(raise_exception=True)


CONFIG = Config()
MNTINFO = {}
VGINFO = collections.defaultdict(dict)


def process_volume_groups():
    """Do backup."""
    sources = ["/cygdrive/c/x/logs/"]

    snap = "{0:%Y%m%d}T{0:%H%M}Z".format(datetime.utcnow())

    infd, outfd = os.pipe()

    infile = os.fdopen(infd)
    outfile = os.fdopen(outfd)

    args = ["C:\\cygwin64\\bin\\ssh.exe"] + ["-i", "C:\\x\\.ssh\\id_ed25519"] + [CONFIG.config['rsync']['remote']] + ["rbak-rsync-log"] + [snap]
    ssh_process = subprocess.Popen(
        args,
        stdin=infile,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)

    infile.close()

    # do the rsync!
    subprocess.check_call(
        ["C:\\cygwin64\\bin\\rsync.exe"] + ["--rsync-path=rsync {0}".format(snap)] + ["--rsh=C:\\cygwin64\\bin\\ssh.exe -i /cygdrive/c/x/.ssh/id_ed25519"] + CONFIG.config['rsync']['options']
        + sources + [CONFIG.config['rsync']['remote'] + ":" + CONFIG.config['rsync']['path']],
        stdout=outfile,
        stderr=subprocess.STDOUT)

    outfile.close()

    ssh_output = ssh_process.communicate()[0]

    if ssh_process.returncode:
        print("REMOTE", ssh_output.decode(), file=sys.stderr)
        raise subprocess.CalledProcessError(ssh_process.returncode, args)


def main():
    """Execute script."""
    print("HI!")
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c", "--config", default="/etc/snapsync.yml",
        help="set config file path")
    parser.add_argument(
        "--generate-config", action="store_true",
        help="output config file template and exit")
    parser.add_argument("-V", "--version", action="version", version="%(prog)s 0.0")
    args = parser.parse_args()

    try:
        CONFIG.load(args.config)
    except Exception as ex:  # pylint: disable=locally-disabled,broad-except
        print("Failed to load config:", ex, file=sys.stderr)
        sys.exit(2)

    print(CONFIG.config)

    process_volume_groups()

    
if __name__ == '__main__':
    main()
