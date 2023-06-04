# coding=utf-8
#
# snapsync_w32.py - LVM/btrfs snapshots + rsync backup utility [win32]
#
# Released under GPLv3, see LICENCE
#
# Copyright © 2016  David Taylor <davidt@yadt.uk>
#
"""snapsync_w32 script.

This module implements the snapsync script for win32 clients.
"""


from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

import argparse
import collections
from datetime import datetime
import os
from shutil import rmtree
import subprocess
import sys
from tempfile import mkdtemp
import yaml
from pykwalify.core import Core
from pkg_resources import resource_stream
import win32com.client


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


def process_mounts():
    """Do backup."""
    sources = []
    shadow_ids = []

    temp_w32 = mkdtemp()

    drive, destination = temp_w32.replace('\\','/').split(':')
    temp = '/cygdrive/' + drive.lower() + destination

    wmi_shadow_copy = win32com.client.GetObject("winmgmts:\\\\.\\root\\cimv2:Win32_ShadowCopy")
    wmi_locator = win32com.client.Dispatch("WbemScripting.SWbemLocator")
    wmi_service = wmi_locator.ConnectServer(".", "root\cimv2")

    for mount in sorted(CONFIG.config['mounts'], key=lambda k: k['path'], reverse=True):
        mount = mount['path']
        print("Process mount", mount)

        create_method = wmi_shadow_copy.Methods_("Create")
        create_params = create_method.InParameters
        create_params.Properties_['Context'].value = "NASRollback"
        create_params.Properties_['Volume'].value = "{0}:\\".format(mount)
        result = wmi_shadow_copy.ExecMethod_("Create", create_params)
        print(str([(x.name, x.value) for x in result.Properties_]))

        return_value = int(result.Properties_['ReturnValue'])
        if return_value != 0:
            raise Exception()

        id = str(result.Properties_['ShadowID'])
        
        assert id is not None

        shadow_ids.append(id)

        wmi_items = wmi_service.ExecQuery('SELECT * FROM Win32_ShadowCopy WHERE ID="{0}"'.format(id))

        if len(wmi_items) != 1:
            raise Exception()

        shadow = wmi_items[0]
        device = str(shadow.Properties_['DeviceObject']).split('\\')[-1]

        subprocess.check_output(
            ["C:\\cygwin64\\bin\\ln.exe", "-s", "/proc/sys/Device/{0}/".format(device), "{0}/{1}".format(temp, mount)],
            stderr=subprocess.STDOUT)

        sources.append("{0}/./{1}/".format(temp, mount))

    snap = "{0:%Y%m%d}T{0:%H%M}Z".format(datetime.utcnow())

    infd, outfd = os.pipe()

    infile = os.fdopen(infd)
    outfile = os.fdopen(outfd)

    args = ["C:\\cygwin64\\bin\\ssh.exe"] + [CONFIG.config['rsync']['remote']] + ["rbak-rsync-log"] + [snap]
    ssh_process = subprocess.Popen(
        args,
        stdin=infile,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)

    infile.close()

    # do the rsync!
    subprocess.check_call(
        ["C:\\cygwin64\\bin\\rsync"] + ["--rsync-path=rsync {0}".format(snap)] + ["--rsh=C:\\cygwin64\\bin\\ssh.exe"] + CONFIG.config['rsync']['options']
        + sources + [CONFIG.config['rsync']['remote'] + ":" + CONFIG.config['rsync']['path']],
        stdout=outfile,
        stderr=subprocess.STDOUT)

    outfile.close()

    ssh_output = ssh_process.communicate()[0]

    if ssh_process.returncode:
        print("REMOTE", ssh_output.decode(), file=sys.stderr)
        raise subprocess.CalledProcessError(ssh_process.returncode, args)

    rmtree(temp_w32)
    for shadow_id in shadow_ids:
        wmi_items = wmi_service.ExecQuery("SELECT * FROM Win32_ShadowCopy WHERE ID=\"{0}\"".format(shadow_id))

        for wmi_item in wmi_items:
            wmi_item.Delete_()


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

    if args.generate_config:
        print("# Default config TBC")
        sys.exit(0)

    try:
        CONFIG.load(args.config)
    except Exception as ex:  # pylint: disable=locally-disabled,broad-except
        print("Failed to load config:", ex, file=sys.stderr)
        sys.exit(2)

    print(CONFIG.config)

    process_mounts()
