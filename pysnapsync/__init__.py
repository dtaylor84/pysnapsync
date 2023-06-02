# coding=utf-8
"""PySnapSync application.

This package contains the PySnapSync application.

The package contains two sub-packages, `client` and `server`.  The client
package implements the pysnapsync script.  The server package implements the
pysnapsync_rsync wrapper script.

See the module doc strings for more information.
"""


from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

from pysnapsync import client
from pysnapsync import server

__all__ = [x.__name__.rsplit(".", maxsplit=1)[-1] for x in [client, server]]
