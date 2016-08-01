# coding=utf-8
#
# client.py - LVM/btrfs snapshots + rsync backup utility
#
# Released under GPLv3, see LICENCE
#
# Copyright © 2016  David Taylor <davidt@yadt.uk>
#

from __future__ import print_function, division
import collections
from datetime import datetime
import os
import subprocess
import sys
import yaml


class Config(object):
    config = {}

    def load(self, config_file):
        with open(config_file, 'r') as config_stream:
            self.config = yaml.load(config_stream)


CONFIG = Config()
MNTINFO = {}
VGINFO = collections.defaultdict(dict)


def find_mount(mount):
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
        ["logical_volumes"] + CONFIG.config['logical_volumes']['options'] + [filesystem['source']])
    logical_volumes = yaml.load(output)
    logical_volume = logical_volumes['report'][0]['logical_volume'][0]

    VGINFO[logical_volume['volume_group_name']][logical_volume['logical_volume_name']] = mount_path

    snap_logical_volume = (
        logical_volume['volume_group_name']
        + "/" + CONFIG.config['rbaksnap_prefix'] + logical_volume['logical_volume_name'])

    MNTINFO[mount_path] = {}
    MNTINFO[mount_path]['volume_group_name'] = logical_volume['volume_group_name']
    MNTINFO[mount_path]['logical_volume_name'] = logical_volume['logical_volume_name']
    MNTINFO[mount_path]['snap_logical_volume'] = snap_logical_volume

    while True:
        output = subprocess.check_output(
            ["logical_volumes"]
            + CONFIG.config['logical_volumes']['options']
            + [snap_logical_volume],
            stderr=os.devnull)
        logical_volumes = yaml.load(output)
        if len(logical_volumes['report'][0]['logical_volume']) == 0:
            return  # no existing snap-LV

        logical_volume = logical_volumes['report'][0]['logical_volume'][0]
        path = logical_volume['logical_volume_path']
        attr = logical_volume['logical_volume_attr']
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
        stdout=os.devnull,
        stderr=subprocess.STDOUT)


def process_volume_groups():
    sources = []
    volume_groupcount = {}

    for volume_group in VGINFO:
        volume_groupcount[volume_group] = len(VGINFO[volume_group])

    for mount in sorted(MNTINFO):
        mnt = MNTINFO[mount]

        print(
            "Process mount", mount, mnt['logical_volume_name'],
            mnt['volume_group_name'], mnt['snap_logical_volume'])

        volume_group_pct = "%3.0f" % (100 / volume_groupcount[mnt['volume_group_name']])
        volume_groupcount[mnt['volume_group_name']] -= 1

        subprocess.check_call(
            ["lvcreate", "-pr", "--snapshot", "--name",
             CONFIG.config['rbaksnap_prefix'] + mnt['logical_volume_name'],
             "-l" + volume_group_pct + "%FREE",
             mnt['volume_group_name'] + "/" + mnt['logical_volume_name']],
            stdout=os.devnull,
            stderr=subprocess.STDOUT)
        subprocess.check_call(
            ["mount", "-r", "/dev/" + mnt['snap_logical_volume'],
             CONFIG.config['tmp_mount'] + mount],
            stdout=os.devnull,
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
            ["umount", "/dev/" + mnt['snap_logical_volume']],
            stderr=subprocess.STDOUT)
        subprocess.check_output(
            ["logical_volumeremove", "-f", mnt['snap_logical_volume']],
            stderr=subprocess.STDOUT)


def main():
    CONFIG.load("pysnapsync.yaml")
    print(CONFIG.config)

    for mount in CONFIG.config['mounts']:
        find_mount(mount)

    process_volume_groups()
