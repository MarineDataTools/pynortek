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
    hChecksum = np.ushort(0xb58c)
    for i in range(0,len(data),2):
        tmp = int.from_bytes(data[i:i+2], byteorder='little')
        hChecksum += tmp
        
    return np.ushort(hChecksum)


def convert_vector_velocity(data):
    """ Converts binary data in a vector velocity data structure
    """
    print('Vector velocity data')
    print(data)
    conv_data = {}
    conv_data['Count']  = data[3]
    conv_data['AnaIn2'] = float(data[2] + 256 * data[5])
    conv_data['AnaIn1'] = float(data[8] + 256 * data[9])
    conv_data['Press']  = float(data[4] * 65536 + data[7] * 256 + data[6]) # [0.001 dbar]
    conv_data['Vel1']   = float(data[10] + 256 * data[11])
    conv_data['Vel2']   = float(data[12] + 256 * data[13])
    conv_data['Vel3']   = float(data[14] + 256 * data[15])
    conv_data['Amp1']   = float(data[16])
    conv_data['Amp2']   = float(data[17])
    conv_data['Amp3']   = float(data[18])
    conv_data['Amp1']   = float(data[19])
    conv_data['Amp2']   = float(data[20])
    conv_data['Amp3']   = float(data[21])
    print(conv_data)
    return conv_data


package_aquadopp_velocity = {'name':'Aquadopp velocity','sync':b'\xa5','id':b'\x01','size':42}
package_aquadopp_diagnostics_header = {'name':'Aquadopp diagnostics header','sync':b'\xa5','id':b'\x06','size':36} #
package_vector_velocity_header = {'name':'Vector velocity header','sync':b'\xa5','id':b'\x12','size':42} #
package_vector_velocity = {'name':'Vector velocity','sync':b'\xa5','id':b'\x10','size':24,'function':convert_vector_velocity} #
package_vector_sytem = {'name':'Vector system','sync':b'\xa5','id':b'\x11','size':28} #
package_vector_probe_check = {'name':'Vector/Vectrino probe check','sync':b'\xa5','id':b'\x07','size':None,'sizeoff':2} #
package_imu_data = {'name':'IMU data','sync':b'\xa5','id':b'\x71','size':72} #
package_aquadopp_profiler = {'name':'Aquadopp Profiler velocity','sync':b'\xa5','id':b'\x21','size':None,'sizeoff':2} #
package_aquadopp_HRprofiler = {'name':'High resolution Aquadopp Profiler velocity','sync':b'\xa5','id':b'\x2a','size':None} #
package_awac_profile = {'name':'Awac velocity profile','sync':b'\xa5','id':b'\x20','size':None,'sizeoff':2} #
package_awac_wave_header = {'name':'Awac wave header','sync':b'\xa5','id':b'\x31','size':60} #
package_awac_stage = {'name':'Awac stage data','sync':b'\xa5','id':b'\x42','size':None,'sizeoff':2} #
package_awac_wave = {'name':'Awac wave data','sync':b'\xa5','id':b'\x30','size':24} #
package_awac_wave_suv = {'name':'Awac wave data for suv','sync':b'\xa5','id':b'\x36','size':24} #

packages = [package_aquadopp_velocity,
            package_aquadopp_diagnostics_header,
            package_vector_velocity_header,
            package_vector_velocity,
            package_vector_sytem,
            package_vector_probe_check,
            package_imu_data,
            package_aquadopp_profiler,
            package_aquadopp_HRprofiler,
            package_awac_profile,
            package_awac_wave_header,
            package_awac_stage,
            package_awac_wave,
            package_awac_wave_suv]


    

def convert_bin(data):
    """ Converts a binary data stream into a list of packages (dictionaries)
    """
    for i in range(len(data)-1):
        d1 = data[i:i+1]
        d2 = data[i+1:i+2]        
        #print(i,d1,d2)
        for package in packages:
            if((d1 == package['sync']) and (d2 == package['id'])):
                print(package['name'])
                if package['size'] is not None:
                    psize = package['size']
                else:
                    offset = i+package['sizeoff']
                    psize = int.from_bytes(data[offset:offset+2], byteorder='little')
                    print('Size read:',psize)

                data_package = data[i:i+psize]
                checksum = int.from_bytes(data[i+psize-2:i+psize], byteorder='little')
                checksum_calc = calc_checksum(data[i:i+psize-2])
                print(checksum,checksum_calc)
                print(len(data_package))
                FLAG_CHECKSUM=False
                if(checksum == checksum_calc):
                    FLAG_CHECKSUM=True
                    
                # Convert the data
                try:
                    conv_data = package['function'](data_package)
                except:
                    print('No function available')

                input('fsdfs')
