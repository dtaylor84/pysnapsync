# coding=utf-8
#
# snapsync.py - LVM/btrfs snapshots + rsync backup utility
#
# Released under GPLv3, see LICENCE
#
# Copyright © 2016  David Taylor <davidt@yadt.uk>
#
"""snapsync script.

This module implements the snapsync script.
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


class Config:
    """Store configuration."""

    config = {}

    def load(self, config_file):
        """Load configuration from config_file."""
        with resource_stream(__name__, 'config-schema.yaml') as schema_stream:
            schema = yaml.load(schema_stream)

        core = Core(source_file=config_file, schema_data=schema)
        self.config = core.validate(raise_exception=True)


CONFIG = Config()
MNTINFO = {}
VGINFO = collections.defaultdict(dict)


def find_mount(mount):
    """Find mount details."""
    mount_path = mount['path']

    output = subprocess.check_output(
        ["findmnt"] + CONFIG.config['findmnt']['options'] + [mount_path])
    filesystems = yaml.load(output)
    filesystem = filesystems['filesystems'][0]

    # output = subprocess.check_output(
    #     ["lsblk"] + CONFIG.config['lsblk']['options'] + [filesystem['source']])
    # blks = yaml.load(output)
    # blk = blks['blockdevices'][0]

    output = subprocess.check_output(
        ["lvs"] + CONFIG.config['lvs']['options'] + [filesystem['source']])
    logical_volumes = yaml.load(output)
    logical_volume = logical_volumes['report'][0]['lv'][0]

    VGINFO[logical_volume['vg_name']][logical_volume['lv_name']] = mount_path

    snap_logical_volume = (
        logical_volume['vg_name']
        + "/" + CONFIG.config['rbaksnap_prefix'] + logical_volume['lv_name'])

    MNTINFO[mount_path] = {}
    MNTINFO[mount_path]['vg_name'] = logical_volume['vg_name']
    MNTINFO[mount_path]['lv_name'] = logical_volume['lv_name']
    MNTINFO[mount_path]['snap_lv'] = snap_logical_volume

    while True:
        snap_subprocess = subprocess.run(
            ["lvs"]
            + CONFIG.config['lvs']['options']
            + [snap_logical_volume],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL)
        logical_volumes = yaml.load(snap_subprocess.stdout)
        if not logical_volumes['report'][0]['lv']:
            return  # no existing snap-LV

        logical_volume = logical_volumes['report'][0]['lv'][0]
        path = logical_volume['lv_path']
        attr = logical_volume['lv_attr']
        logical_volume_type = attr[0]
        logical_volume_perm = attr[1]
        logical_volume_use = attr[5]
        logical_volume_target = attr[6]

        if (logical_volume_type != "s"
                or logical_volume_perm != "r"
                or logical_volume_target != "s"):
            raise RuntimeError(
                "snapshot LV already exists, but not a RO snapshot: "
                + snap_logical_volume)

        if logical_volume_use == "-":
            break

        if logical_volume_use == "o":
            subprocess.check_call(["umount", path])
        else:
            raise RuntimeError("snapshot LV already exists, and is in use: " + snap_logical_volume)

    subprocess.call(
        ["lvremove", "-f", snap_logical_volume],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT)


def process_volume_groups():
    """Do backup."""
    sources = []
    volume_group_count = {}

    for volume_group in VGINFO:
        volume_group_count[volume_group] = len(VGINFO[volume_group])

    for mount in sorted(MNTINFO):
        mnt = MNTINFO[mount]

        print(
            "Process mount", mount, mnt['lv_name'],
            mnt['vg_name'], mnt['snap_lv'])

        volume_group_pct = "%03.0f" % (100 / volume_group_count[mnt['vg_name']])
        volume_group_count[mnt['vg_name']] -= 1

        subprocess.check_call(
            ["lvcreate", "-pr", "--snapshot", "--name",
             CONFIG.config['rbaksnap_prefix'] + mnt['lv_name'],
             "-l" + volume_group_pct + "%FREE",
             mnt['vg_name'] + "/" + mnt['lv_name']],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT)

        subprocess.check_call(
            ["mount", "-r", "/dev/" + mnt['snap_lv'],
             CONFIG.config['tmp_mount'] + mount],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT)

        sources += [CONFIG.config['tmp_mount'] + "/." + mount]

    snap = "{0:%Y%m%d}T{0:%H%M}Z".format(datetime.utcnow())

    infd, outfd = os.pipe()

    infile = os.fdopen(infd)
    outfile = os.fdopen(outfd)

    args = ["ssh"] + [CONFIG.config['rsync']['remote']] + ["rbak-rsync-log"] + [snap]
    ssh_process = subprocess.Popen(
        args,
        stdin=infile,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)

    infile.close()

    # do the rsync!
    subprocess.check_call(
        ["rsync"] + ["--rsync-path=rsync {0}".format(snap)] + CONFIG.config['rsync']['options']
        + sources + [CONFIG.config['rsync']['remote'] + ":" + CONFIG.config['rsync']['path']],
        stdout=outfile,
        stderr=subprocess.STDOUT)

    outfile.close()

    ssh_output = ssh_process.communicate()[0]

    if ssh_process.returncode:
        print("REMOTE", ssh_output.decode(), file=sys.stderr)
        raise subprocess.CalledProcessError(ssh_process.returncode, args)

    for mount in sorted(MNTINFO, reverse=True):
        mnt = MNTINFO[mount]
        subprocess.check_output(
            ["umount", "/dev/" + mnt['snap_lv']],
            stderr=subprocess.STDOUT)
        subprocess.check_output(
            ["lvremove", "-f", mnt['snap_lv']],
            stderr=subprocess.STDOUT)


def main():
    """Execute script."""
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

    # Do this in reverse order so we clean up failures correctly.
    for mount in sorted(CONFIG.config['mounts'], key=lambda k: k['path'], reverse=True):
        find_mount(mount)

    process_volume_groups()
