#!/usr/bin/env python3
#
# pysnapsync.py - LVM/btrfs snapshots + rsync backup utility
#
# Released under GPLv3, see LICENCE
#
# Copyright © 2016  David Taylor <davidt@yadt.uk>
#

import collections
from datetime import datetime
import os
import yaml
import subprocess
import sys

config=None
mntinfo={}
vginfo=collections.defaultdict(dict)

def read_config(config_file):
    global config

    with open(config_file, 'r') as config_stream:
        config = yaml.load(config_stream)

def find_mount(m):
    global mntinfo
    global vginfo

    mount_path = m['path']

    command = subprocess.run(["findmnt"] + config['findmnt']['options'] + [mount_path], stdout=subprocess.PIPE)
    filesystems = yaml.load(command.stdout)
    fs = filesystems['filesystems'][0]

    command = subprocess.run(["lsblk"] + config['lsblk']['options'] + [fs['source']], stdout=subprocess.PIPE)
    blks = yaml.load(command.stdout)
    blk = blks['blockdevices'][0]

    command = subprocess.run(["lvs"] + config['lvs']['options'] + [fs['source']], stdout=subprocess.PIPE)
    lvs = yaml.load(command.stdout)
    lv = lvs['report'][0]['lv'][0]

    vginfo[lv['vg_name']][lv['lv_name']] = mount_path

    snap_lv = lv['vg_name'] + "/" + config['rbaksnap_prefix'] + lv['lv_name']

    mntinfo[mount_path] = {}
    mntinfo[mount_path]['vg_name'] = lv['vg_name']
    mntinfo[mount_path]['lv_name'] = lv['lv_name']
    mntinfo[mount_path]['snap_lv'] = snap_lv

    while True:
        command = subprocess.run(["lvs"] + config['lvs']['options'] + [snap_lv], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        lvs = yaml.load(command.stdout)
        if len(lvs['report'][0]['lv']) == 0:
            return # no existing snap-LV

        lv = lvs['report'][0]['lv'][0]
        path = lv['lv_path']
        attr = lv['lv_attr']
        lv_type = attr[0]
        lv_perm = attr[1]
        lv_use = attr[5]
        lv_target = attr[6]

        if lv_type != "s" or lv_perm != "r" or lv_target != "s":
            raise RuntimeError("snapshot LV already exists, but not a RO snapshot: " + snap_lv)

        if lv_use == "-":
            break

        if lv_use == "o":
            command = subprocess.run(["umount", path])
        else:
            raise RuntimeError("snapshot LV already exists, and is in use: " + snap_lv)

    command = subprocess.run(["lvremove", "-f", snap_lv], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)


def process_vgs():
    sources = []
    vgcount = {}

    for vg in vginfo:
        vgcount[vg] = len(vginfo[vg])

    for mount in sorted(mntinfo):
        mnt = mntinfo[mount]

        print("Process mount", mount, mnt['lv_name'], mnt['vg_name'], mnt['snap_lv'])

        vg_pct = "%3.0f" % (100 / vgcount[mnt['vg_name']])
        vgcount[mnt['vg_name']] -= 1

        command = subprocess.run(["lvcreate", "-pr", "--snapshot", "--name", (config['rbaksnap_prefix'] + mnt['lv_name']), "-l" + vg_pct + "%FREE", (mnt['vg_name'] + "/" + mnt['lv_name'])], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        command = subprocess.run(["mount", "-r", "/dev/" + mnt['snap_lv'], config['tmp_mount'] + mount], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        sources += [config['tmp_mount'] + "/." + mount]

    snap = "{0:%Y%m%d}T{0:%H%M}Z".format(datetime.utcnow())

    infd, outfd = os.pipe()

    infile = os.fdopen(infd)
    outfile = os.fdopen(outfd)

    ssh_process = subprocess.Popen(
        ["ssh"]
            + [config['rsync']['remote']]
            + ["rbak-rsync-log"]
            + [snap],
        stdin=infile, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    infile.close()

    # do the rsync!
    command = subprocess.run(
        ["rsync"]
            + ["--rsync-path=rsync {0}".format(snap)]
            + config['rsync']['options']
            + sources
            + [config['rsync']['remote'] + ":" + config['rsync']['path']],
        stdout=outfile, stderr=subprocess.STDOUT)

    outfile.close()

    ssh_output = ssh_process.communicate()[0]

    if ssh_process.returncode:
        print("REMOTE", ssh_output.decode(), file=sys.stderr)
        raise subprocess.CalledProcessError(ssh_process.returncode, ssh_process.args)

    for mount in sorted(mntinfo, reverse=True):
        mnt = mntinfo[mount]
        command = subprocess.run(["umount", "/dev/" + mnt['snap_lv']], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        command = subprocess.run(["lvremove", "-f", mnt['snap_lv']], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

def main():
    read_config("pysnapsync.yaml")
    print(config)

    for m in config['mounts']:
        find_mount(m)

    process_vgs()
