# isort: skip_file
__version__ = "0.0.1"
__doc__ = """
Welcome to FileAttributes's API documentation!
=======================================

The API documentation is built automatically using sphinx and a couple
of different extensions. Please read carefully the settings in docs
Each module is described at all stages.

See Also
--------
The package uses lazy loading to speed up the loading process and only
load the needed information. See info : https://peps.python.org/pep-0562/
"""

__all__ = ["FileAttributes"]

import sys
from ._core import _FileAttributesCore
from ._mac import FileAttributesMacOS
from ._linux import FileAttributesLinux
from ._windows import FileAttributesWindows

if sys.platform == "win32":
    FileAttributes = FileAttributesWindows
elif sys.platform == "darwin":
    FileAttributes = FileAttributesMacOS
elif sys.platform == "linux":
    FileAttributes = FileAttributesLinux
else:
    raise NotImplementedError(f"Nothing implemented for {sys.platform}")
