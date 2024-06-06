import numpy as np
import logging
import sys
import pkg_resources
import pytz
import datetime
import os
import re
import struct
import netCDF4
import argparse
import time

# Get the version
version_file = pkg_resources.resource_filename('pynortek','VERSION')
with open(version_file) as version_f:
   version = version_f.read().strip()

# Setup logging module
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
logger = logging.getLogger('pynortek')