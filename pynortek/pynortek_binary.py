import numpy as np
import logging
import sys
import pkg_resources
import pytz
import datetime
import os
import re

# Get the version
version_file = pkg_resources.resource_filename('pynortek','VERSION')

# Setup logging module
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
logger = logging.getLogger('pynortek')

raw_data_files = ['.prf','.vec'] # Names of raw binary data files

def calc_checksum(data):
    """Calculates the checksum of a package as described in the Nortek
    integrators Section 10.2 verson Mar2016
    """
    pass
    

def convert_bin(fname):
    """ Converts a binary data stream into a list of packages (dictionaries)
    """
    pass

    
