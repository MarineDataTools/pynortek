from .pynortek import *
from .pynortek_binary import *

with open(version_file) as version_f:
   version = version_f.read().strip()

__version__ = version
