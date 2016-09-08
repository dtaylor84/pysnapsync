# coding=utf-8
"""PySnapSync server.

This package implements the pysnapsync server.

The package exports the following modules:

o `pysnapsync_rsync` rsync wrapper script.

See the module doc strings for more information.
"""


from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

from pysnapsync.server import snapsync_rsync

__all__ = [x.__name__.split(".")[-1] for x in [snapsync_rsync]]
