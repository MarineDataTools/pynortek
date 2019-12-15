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

# Get the version
version_file = pkg_resources.resource_filename('pynortek','VERSION')
with open(version_file) as version_f:
   version = version_f.read().strip()

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

def timefrombin(data):
    """ Converts binary time into python readable time
    """
    conv_data = {}
    conv_data['minute']  = (data[0] & 0x0F) + 10 * ((data[0] >> 4) & 0x0F)
    conv_data['second']  = (data[1] & 0x0F) + 10 * ((data[1] >> 4) & 0x0F)
    conv_data['day']     = (data[2] & 0x0F) + 10 * ((data[2] >> 4) & 0x0F)
    conv_data['hour']    = (data[3] & 0x0F) + 10 * ((data[3] >> 4) & 0x0F)
    conv_data['year']    = (data[4] & 0x0F) + 10 * ((data[4] >> 4) & 0x0F) + 2000
    conv_data['month']   = (data[5] & 0x0F) + 10 * ((data[5] >> 4) & 0x0F)
    conv_data['date']    = datetime.datetime(conv_data['year'],conv_data['month'],conv_data['day'],conv_data['hour'],conv_data['minute'],conv_data['second'])
    return conv_data


def convert_vector_system_data(data,apply_unit_factor = False):
    #print('Vector system data')
    #print('System data',data)
    if(apply_unit_factor):
        pass

    conv_data = {}
    conv_data['units'] = {}
    conv_data['minute']       = (data[4] & 0x0F) + 10 * ((data[4] >> 4) & 0x0F)
    conv_data['second']       = (data[5] & 0x0F) + 10 * ((data[5] >> 4) & 0x0F)
    conv_data['day']          = (data[6] & 0x0F) + 10 * ((data[6] >> 4) & 0x0F)
    conv_data['hour']         = (data[7] & 0x0F) + 10 * ((data[7] >> 4) & 0x0F)
    conv_data['year']         = (data[8] & 0x0F) + 10 * ((data[8] >> 4) & 0x0F) + 2000
    conv_data['month']        = (data[9] & 0x0F) + 10 * ((data[9] >> 4) & 0x0F)
    conv_data['bat']          = struct.unpack('<H', data[10:12])[0] # Little endian
    conv_data['units']['bat'] = 'battery voltage (0.1 V)'
    conv_data['SndVel']       = struct.unpack('<H', data[12:14])[0] # Little endian
    conv_data['units']['SndVel'] = 'speed of sound (0.1 m/s)'
    conv_data['Hdg']             = struct.unpack('<h', data[14:16])[0] # Little endian
    conv_data['units']['Hdg']    = 'compass heading (0.1 deg)'
    conv_data['Pitch']            = struct.unpack('<h', data[16:18])[0] # Little endian
    conv_data['units']['Pitch']   = 'compass pitch (0.1 deg)'    
    conv_data['Roll']            = struct.unpack('<h', data[18:20])[0] # Little endian
    conv_data['units']['Roll']   = 'compass roll (0.1 deg)'
    conv_data['T']            = struct.unpack('<h', data[20:22])[0] # Little endian
    conv_data['units']['T']   = 'temperature (0.01 deg C)'
    conv_data['err']            = int(data[23])
    conv_data['units']['err']   = 'Error code'
    conv_data['stat']            = int(data[23])
    conv_data['units']['stat']   = 'Status code'
    conv_data['AnaIn']            = float(struct.unpack('<H', data[20:22])[0]) # Little endian
    conv_data['units']['AnaIn']   = 'counts (V = 5/65536)'

    
    #print((data[5] & 0x0F),((data[5]>>4) & 0x0F))
    #print(conv_data)
    #print('day',data[6])
    conv_data['date']    = datetime.datetime(conv_data['year'],conv_data['month'],conv_data['day'],conv_data['hour'],conv_data['minute'],conv_data['second'])

    #print(conv_data)
    #print('Vector system data')
    #print('Vector system data')
    #print('End Vector system data')
    return conv_data


def convert_vector_velocity_header(data,apply_unit_factor = False):
    """ Converts binary data in a vector velocity data structure
    """
    pass
    #print('Vector velocity header')
    #print(data)
    #print('End Vectir velocity header')


def convert_vector_IMU(data,apply_unit_factor = False):
    """ Converts binary data in a vector velocity data structure
    """
    conv_data = {}
    conv_data['units']  = {}
    conv_data['EnsCnt'] = data[4]
    conv_data['AHRSId'] = data[5]
    conv_data['DeltaAngleX'] = struct.unpack('<f', data[6:10])[0] # Little endian
    conv_data['units']['DeltaAngleX'] = 'Delta Angle x (radians)'
    conv_data['DeltaAngleY'] = struct.unpack('<f', data[10:14])[0] # Little endian
    conv_data['units']['DeltaAngleY'] = 'Delta Angle y (radians)'    
    conv_data['DeltaAngleZ'] = struct.unpack('<f', data[14:18])[0] # Little endian
    conv_data['units']['DeltaAngleZ'] = 'Delta Angle z (radians)'        
    conv_data['DeltaVelX'] = struct.unpack('<f', data[18:22])[0] # Little endian
    conv_data['units']['DeltaVelX'] = 'Delta Velocity Rate x (g*seconds)'
    conv_data['DeltaVelY'] = struct.unpack('<f', data[22:26])[0] # Little endian
    conv_data['units']['DeltaVelY'] = 'Delta Velocity Rate y (g*seconds)'    
    conv_data['DeltaVelZ'] = struct.unpack('<f', data[26:30])[0] # Little endian
    conv_data['units']['DeltaVelZ'] = 'Delta Velocity Rate z (g*seconds)'
    conv_data['M11']   = struct.unpack('<f', data[30:34])[0] # Little endian
    conv_data['units']['M11'] = 'Orientation Matrix X (M11). Describes the orientation of the IMU'
    conv_data['M12']   = struct.unpack('<f', data[34:38])[0] # Little endian
    conv_data['units']['M12'] = 'Orientation Matrix X (M12). Describes the orientation of the IMU'    
    conv_data['M13']   = struct.unpack('<f', data[38:42])[0] # Little endian
    conv_data['units']['M13'] = 'Orientation Matrix X (M13). Describes the orientation of the IMU'    
    conv_data['M21']   = struct.unpack('<f', data[42:46])[0] # Little endian
    conv_data['units']['M21'] = 'Orientation Matrix X (M21). Describes the orientation of the IMU'    
    conv_data['M22']   = struct.unpack('<f', data[46:50])[0] # Little endian
    conv_data['units']['M22'] = 'Orientation Matrix X (M22). Describes the orientation of the IMU'    
    conv_data['M23']   = struct.unpack('<f', data[50:54])[0] # Little endian
    conv_data['units']['M23'] = 'Orientation Matrix X (M23). Describes the orientation of the IMU'    
    conv_data['M31']   = struct.unpack('<f', data[54:58])[0] # Little endian
    conv_data['units']['M31'] = 'Orientation Matrix X (M31). Describes the orientation of the IMU'    
    conv_data['M32']   = struct.unpack('<f', data[58:62])[0] # Little endian
    conv_data['units']['M32'] = 'Orientation Matrix X (M32). Describes the orientation of the IMU'    
    conv_data['M33']   = struct.unpack('<f', data[62:66])[0] # Little endian
    conv_data['units']['M33'] = 'Orientation Matrix X (M33). Describes the orientation of the IMU'    
    conv_data['timer'] = struct.unpack('<i', data[66:70])[0] # Little endian
    conv_data['units']['timer'] = 'Timer value, measures the time since start of each burst. To convert the timer value to time in seconds, divide by 62,500.'
    return conv_data

def convert_vector_velocity(data,apply_unit_factor = False):
    """ Converts binary data in a vector velocity data structure
    """
    #print('Vector velocity data')
    #print(data)
    fac_analog = 1.0
    fac_press  = 1.0
    fac_vel    = 1.0
    if(apply_unit_factor):
        fac_analog = 5/65536
        pac_press = 1000.
        fac_vel   = 1/1000. # mm/s to m/s

    conv_data = {}
    conv_data['Count']  = data[3]
    conv_data['AnaIn2'] = float(data[2] + 256 * data[5]) * fac_analog
    conv_data['AnaIn1'] = float(data[8] + 256 * data[9]) * fac_analog
    conv_data['p']  = float(data[4] * 65536 + data[7] * 256 + data[6]) * fac_press # [0.001 dbar]
    #print([data[10:11],data[11:12]])
    #ba = bytearray([data[10],data[11]])
    #print(struct.unpack('<h', ba))
    #print(int.frombytes(ba))
    conv_data['v1']   = float(struct.unpack('<h', data[10:12])[0]) * fac_vel
    conv_data['v2']   = float(struct.unpack('<h', data[12:14])[0]) * fac_vel
    conv_data['v3']   = float(struct.unpack('<h', data[14:16])[0]) * fac_vel
    conv_data['a1']   = float(data[16]) # amplitude beam1 (counts)
    conv_data['a2']   = float(data[17]) # amplitude beam2 (counts)
    conv_data['a3']   = float(data[18]) # amplitude beam3 (counts)
    conv_data['c1']   = float(data[19]) # correlation beam1 (%)
    conv_data['c2']   = float(data[20]) # correlation beam2 (%)
    conv_data['c3']   = float(data[21]) # correlation beam3 (%)

    return conv_data

def convert_hw_conf(data,apply_unit_factor = False):
    conv_data = {}
    conv_data['SerialNo'] = data[4:18].decode('utf-8')
    conv_data['Config'] = struct.unpack('<H', data[18:20])[0]
    conv_data['Frequency'] = struct.unpack('<H', data[20:22])[0]
    conv_data['PICVersion'] = struct.unpack('<H', data[22:24])[0]
    conv_data['HWRevision'] = struct.unpack('<H', data[24:26])[0]
    conv_data['RECSize'] = struct.unpack('<H', data[26:28])[0]
    conv_data['Status'] = struct.unpack('<H', data[28:30])[0]
    conv_data['Spare'] = data[30:42]
    conv_data['FWVersion'] = data[42:46].decode('utf-8')
    #print('Hardware',conv_data)
    return conv_data

def convert_head_conf(data,apply_unit_factor = False):
    #print('Head conf')
    conv_data = {}
    conv_data['Config'] = struct.unpack('<H', data[4:6])[0]
    conv_data['Frequency'] = struct.unpack('<H', data[6:8])[0]
    conv_data['Type'] = struct.unpack('<H', data[8:10])[0]        # Head Type
    tmpstr = data[10:22]
    tmpstr = tmpstr[:tmpstr.find(b'\x00')]
    conv_data['SerialNo'] = tmpstr.decode('utf-8')
    conv_data['System'] = data[22:198]
    conv_data['Spare'] = data[198:220]
    conv_data['Nbeams'] = struct.unpack('<H', data[220:222])[0]
    #print('Head',conv_data)    
    return conv_data

def convert_usr_conf(data,apply_unit_factor = False):
    conv_data = {}
    conv_data['units'] = {} # The units/description as in the system integrators manual
    conv_data['T1'] = struct.unpack('<H', data[4:6])[0] 
    conv_data['units']['T1'] = 'Transmit pulse length (counts)'
    conv_data['T2'] = struct.unpack('<H', data[6:8])[0] 
    conv_data['units']['T2'] = 'Blanking distance (counts)'
    conv_data['T3'] = struct.unpack('<H', data[8:10])[0] 
    conv_data['units']['T3'] = 'Receive length (counts)'
    conv_data['T4'] = struct.unpack('<H', data[10:12])[0] 
    conv_data['units']['T4'] = 'time between pings (counts)'    
    conv_data['T5'] = struct.unpack('<H', data[12:14])[0] 
    conv_data['units']['T5'] = 'time between burst sequences (counts)'
    conv_data['NPings'] = struct.unpack('<H', data[14:16])[0] 
    conv_data['units']['NPings'] = 'number of beam sequences per burst (counts)'    
    conv_data['AvgInterval'] = struct.unpack('<H', data[16:18])[0] 
    conv_data['units']['AvgInterval'] = 'average interval in seconds For Vector AvgInterval = 512/Sampling Rate'
    conv_data['nbeams'] = struct.unpack('<H', data[18:20])[0] 
    conv_data['units']['nbeams'] = 'number of beams'
    conv_data['TimCtrlReg'] = struct.unpack('<H', data[20:22])[0]
    conv_data['units']['TimCtrlReg'] = 'timing controller mode. bit 1: profile (0=single, 1=continuous) bit 2: mode (0=burst, 1=continuous) bit 5: power level (0=1, 1=2, 0=3, 1=4) bit 6: power level (0 0 1 1 ) bit 7: synchout position (0=middle of sample, 1=end of sample (Vector)) bit 8: sample on synch (0=disabled,1=enabled, rising edge) bit 9: start on synch (0=disabled,1=enabled, rising edge)'    
    conv_data['PwrCtrlReg'] = struct.unpack('<H', data[22:24])[0]
    conv_data['units']['PwrCtrlReg'] = 'power control register bit 5: power level (0=1, 1=2, 0=3, 1=4) bit 6: power level (0 0 1 1 )'
    conv_data['A1'] = struct.unpack('<H', data[24:26])[0]
    conv_data['units']['A1'] = 'not used'
    conv_data['B0'] = struct.unpack('<H', data[26:28])[0]
    conv_data['units']['B0'] = 'not used'    
    conv_data['B1'] = struct.unpack('<H', data[28:30])[0]
    conv_data['units']['B1'] = 'not used'    
    conv_data['CompassUpdRate'] = struct.unpack('<H', data[30:32])[0]
    conv_data['units']['CompassUpdRate']= 'compass update rate'
    conv_data['CoordSystem'] = struct.unpack('<H', data[32:34])[0]
    conv_data['units']['CoordSystem']= 'coordinate system (0=ENU, 1=XYZ, 2=BEAM)'
    conv_data['NBins'] = struct.unpack('<H', data[34:36])[0]
    conv_data['units']['NBins'] = 'number of cells'
    conv_data['BinLength'] = struct.unpack('<H', data[36:38])[0]
    conv_data['units']['BinLength'] = 'cell size'
    conv_data['MeasInterval'] = struct.unpack('<H', data[38:40])[0]
    conv_data['units']['MeasInterval'] = 'measurement interval'
    tmpstr = data[40:46]
    tmpstr = tmpstr[:tmpstr.find(b'\x00')]    
    conv_data['DeployName'] = tmpstr.decode('utf-8').replace('\x00','')
    conv_data['units']['DeployName'] = 'recorder deployment name'    
    conv_data['WrapMode'] = struct.unpack('<H', data[46:48])[0]
    conv_data['units']['WrapMode'] = 'recorder wrap mode (0=NO WRAP, 1=WRAP WHEN FULL)'
    conv_data['clockDeploy'] = timefrombin(data[48:54])['date']
    conv_data['units']['clockDeploy'] = 'deployment start time'
    conv_data['DiagInterval'] = struct.unpack('<I', data[54:58])[0]
    conv_data['units']['DiagInterval'] = 'number of seconds between diagnostics measurements'
    conv_data['Mode'] = struct.unpack('<H', data[58:60])[0]
    conv_data['units']['Mode'] = 'mode: bit 0: use user specified sound speed (0=no, 1=yes) bit 1: diagnostics/wave mode 0=disable, 1=enable) bit 2: analog output mode (0=disable, 1=enable) bit 3: output format (0=Vector, 1=ADV) bit 4: scaling (0=1 mm, 1=0.1 mm) bit 5: serial output (0=disable, 1=enable) bit 6: reserved EasyQ bit 7: stage (0=disable, 1=enable) bit 8: output power for analog input (0=disable, 1=enable)'
    conv_data['AdjSoundSpeed'] = struct.unpack('<H', data[58:60])[0]
    conv_data['units']['AdjSoundSpeed'] = 'user input sound speed adjustment factor'
    conv_data['NSampDiag'] = struct.unpack('<H', data[62:64])[0]
    conv_data['units']['NSampDiag'] = '# samples (AI if EasyQ) in diagnostics mode'
    conv_data['NBeamsCellDiag'] = struct.unpack('<H', data[64:66])[0]
    conv_data['units']['NBeamsCellDiag'] = '# beams / cell number to measure in diagnostics mode'
    conv_data['ModeTest'] = struct.unpack('<H', data[68:70])[0]
    conv_data['units']['ModeTest'] = 'mode test: bit 0: correct using DSP filter (0=no filter, 1=filter) bit 1: filter data output (0=total corrected velocity,1=only correction part)'
    conv_data['AnaInAddr'] = struct.unpack('<H', data[70:72])[0]
    conv_data['units']['AnaInAddr'] = 'analog input address'
    conv_data['SWVersion'] = struct.unpack('<H', data[72:74])[0]
    conv_data['units']['SWVersion'] = 'software version'
    conv_data['spare'] = struct.unpack('<H', data[74:76])[0]
    conv_data['units']['spare'] = 'spare'
    conv_data['VelAdjTable'] = data[76:256]
    conv_data['units']['VelAdjTable'] = 'velocity adjustment table'
    tmpstr = data[256:436]
    tmpstr = tmpstr[:tmpstr.find(b'\x00')]
    conv_data['Comments'] = tmpstr.decode('utf-8')
    conv_data['units']['Comments'] = 'file comments'
    conv_data['WaveMode'] = struct.unpack('<H', data[436:438])[0]
    conv_data['units']['WaveMode'] = 'wave measurement mode bit 0: data rate (0=1 Hz, 1=2 Hz) bit 1: wave cell position (0=fixed, 1=dynamic) bit 2: type of dynamic position (0=pct of mean pressure, 1=pct of min re)'
    conv_data['DynPercPos'] = struct.unpack('<H', data[438:440])[0]
    conv_data['units']['DynPercPos'] = 'percentage for wave cell positioning (=32767×#%/100) (# means number of)'
    conv_data['T1Wave'] = struct.unpack('<H', data[440:442])[0]
    conv_data['units']['T1Wave'] = 'wave transmit pulse'
    conv_data['T2Wave'] = struct.unpack('<H', data[442:444])[0]
    conv_data['units']['T2Wave'] = 'fixed wave blanking distance (counts)'
    conv_data['T3Wave'] = struct.unpack('<H', data[444:446])[0]
    conv_data['units']['T3Wave'] = 'wave measurement cell size'
    conv_data['NSampWave'] = struct.unpack('<H', data[446:448])[0]
    conv_data['units']['NSampWave'] = 'number of diagnostics/wave samples'
    conv_data['A1_1'] = struct.unpack('<H', data[448:450])[0]
    conv_data['units']['A1_1'] = 'not used'
    conv_data['B0_1'] = struct.unpack('<H', data[450:452])[0]
    conv_data['units']['B0_1'] = 'not used'    
    conv_data['B1_1'] = struct.unpack('<H', data[452:454])[0]
    conv_data['units']['B1_1'] = 'not used for most instruments For Vector it holds Number of Samples Per Burst'
    conv_data['spare2'] = struct.unpack('<H', data[454:456])[0]
    conv_data['units']['spare2'] = 'spare 2'
    conv_data['AnaOutScale'] = struct.unpack('<H', data[456:458])[0]
    conv_data['units']['AnaOutScale'] = 'analog output scale factor (16384=1.0, max=4.0)'
    conv_data['CorrThresh'] = struct.unpack('<H', data[460:462])[0]
    conv_data['units']['CorrThresh'] = 'correlation threshold for resolving ambiguities'
    conv_data['spare3'] = data[462:462+30]
    conv_data['units']['spare3'] = 'spare 3'
    conv_data['QualConst'] = data[494:494+16]
    conv_data['units']['QualConst'] = 'stage match filter constants (EZQ)'        

    return conv_data

# The packages
package_user_configuration = {'name':'user config','sync':b'\xa5','id':b'\x00','size':512,'function':convert_usr_conf} #
package_hardware_configuration = {'name':'hardware config','sync':b'\xa5','id':b'\x05','size':48,'function':convert_hw_conf} #
package_head_configuration = {'name':'head config','sync':b'\xa5','id':b'\x04','size':224,'function':convert_head_conf} #
package_aquadopp_velocity = {'name':'Aquadopp velocity','sync':b'\xa5','id':b'\x01','size':42,'function':None}
package_aquadopp_diagnostics_header = {'name':'Aquadopp diagnostics header','sync':b'\xa5','id':b'\x06','size':36,'function':None}
package_vector_velocity_header = {'name':'Vector velocity header','sync':b'\xa5','id':b'\x12','size':42,'function':convert_vector_velocity_header} #
package_vector_velocity = {'name':'Vec vel','sync':b'\xa5','id':b'\x10','size':24,'function':convert_vector_velocity} #
package_vector_sytem = {'name':'Vec sys','sync':b'\xa5','id':b'\x11','size':28,'function':convert_vector_system_data} #
package_vector_probe_check = {'name':'Vector/Vectrino probe check','sync':b'\xa5','id':b'\x07','size':None,'sizeoff':2,'function':None}
package_imu_data = {'name':'IMU','sync':b'\xa5','id':b'\x71','size':72,'function':convert_vector_IMU} #
package_aquadopp_profiler = {'name':'Aquadopp Profiler velocity','sync':b'\xa5','id':b'\x21','size':None,'sizeoff':2,'function':None}
package_aquadopp_HRprofiler = {'name':'High resolution Aquadopp Profiler velocity','sync':b'\xa5','id':b'\x2a','size':None,'function':None}
package_awac_profile = {'name':'Awac velocity profile','sync':b'\xa5','id':b'\x20','size':None,'sizeoff':2,'function':None}
package_awac_wave_header = {'name':'Awac wave header','sync':b'\xa5','id':b'\x31','size':60,'function':None}
package_awac_stage = {'name':'Awac stage data','sync':b'\xa5','id':b'\x42','size':None,'sizeoff':2,'function':None}
package_awac_wave = {'name':'Awac wave data','sync':b'\xa5','id':b'\x30','size':24,'function':None}
package_awac_wave_suv = {'name':'Awac wave data for suv','sync':b'\xa5','id':b'\x36','size':24,'function':None}

packages = [package_aquadopp_velocity,
            package_user_configuration,            
            package_hardware_configuration,
            package_head_configuration,            
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



def convert_bin(data, apply_unit_factor = False, statistics = False):
    """ Converts a binary data stream into a list of packages (dictionaries)
    """
    conv_data_all = []
    #for i in range(len(data)-1):
    i = 0
    ilast = 0 # Index after of the last found package
    if(statistics):
        statistic_dict = {}
        statistic_dict['packages'] = []
        statistic_dict['package_names'] = []        
        for np,package in enumerate(packages):
            statistic_dict['package_names'].append(package['name'])
            
    while i < (len(data)-1):
        d1 = data[i:i+1]
        d2 = data[i+1:i+2]        
        #print(i,d1,d2)
        FOUND_PACKAGE = False
        for np,package in enumerate(packages):
            if((d1 == package['sync']) and (d2 == package['id']) and (FOUND_PACKAGE == False)):
                if package['size'] is not None:
                    psize = package['size']
                else:
                    offset = i+package['sizeoff']
                    if((i+offset) < len(data)): # Do we have enough data for the package?                    
                        psize = int.from_bytes(data[offset:offset+2], byteorder='little')
                        print('Size read:',psize)
                    else:
                        break

                if((i+psize) < len(data)): # Do we have enough data for the package?
                    data_package = data[i:i+psize]
                    #print(i,i+psize,package['sync'],package['id'],package['name'])
                    if(statistics):                    
                        statistic_dict['packages'].append([i,i+psize,np])
                    checksum = int.from_bytes(data[i+psize-2:i+psize], byteorder='little')
                    checksum_calc = calc_checksum(data[i:i+psize-2])
                    #print(checksum,checksum_calc)
                    #print(len(data_package))
                    FLAG_CHECKSUM=False
                    if(checksum == checksum_calc):
                        FLAG_CHECKSUM=True

                    # Convert the data

                    if package['function'] is not None:
                        conv_data = package['function'](data_package, apply_unit_factor = apply_unit_factor)
                    else:
                        print('No function available for package:' + package['name'])
                        #conv_data = None

                    # Add name and sync/id
                    if(conv_data == None):
                        conv_data = {}
                        
                    conv_data['name'] = package['name']
                    conv_data['sync'] = package['sync']
                    conv_data['id'] = package['id']                                            

                    conv_data_all.append(conv_data)

                    i = i+psize
                    ilast = i
                    FOUND_PACKAGE = True
                    break
                
        if(FOUND_PACKAGE == False): # Try next byte
            i += 1

    ret_dict = {'packages':conv_data_all, 'ilast':ilast,'data_rest':data[ilast:]}
    if(statistics):
        ret_dict['statistics'] = statistic_dict
        
    return ret_dict


def add_timestamp(packages,num_dates = 2):
    """Adds a timestamp to the data in between the timestamps given by
    the device
    num_dates: The number of date packages used to calculate the dt (2 good for IMU vector)

    """
    idate0 = -1
    idate1 = -1
    date0 = datetime.datetime(1,1,1)
    date1 = datetime.datetime(1,1,1)
    ivel = []
    iimu = []    
    num_system = -1
    HAVE_DATE = False
    for i,p in enumerate(packages):
        if(p['name'] == 'Vec sys'): # A time stamp package
            num_system += 1
            if(np.mod(num_system,num_dates) == 0):
                if(idate1 == -1): # Not yet a second date
                    idate0 = i
                    idate1 = i                    
                else:
                    idate0 = idate1
                    idate1 = i
                    
                date0  = date1
                date1  = p['date']
                if ((idate0 >= 0) & (idate1 > idate0)):
                    HAVE_DATE = True
                else:
                    HAVE_DATE = False                
                dt = (date1 - date0).total_seconds()
                print('Date',i,idate0,idate1,p['date'],dt,len(ivel))
                # Add timestamps to velocity package
                if(HAVE_DATE & (len(ivel)>0)): # We found more than one package
                    dt_vel = dt/len(ivel)                 
                    #print('dt_vel',dt_vel)
                    if True:
                        for itmp,iv in enumerate(ivel):
                            date_vel = date0 + itmp * datetime.timedelta(seconds=dt_vel)
                            packages[iv]['date'] = date_vel
                            #print('ivel',iv,itmp,len(ivel),date0,date_vel)
                    ivel = []
                    
                # Add timestamps to IMU package
                if(HAVE_DATE & (len(iimu)>0)): # We found more than one package
                    dt_imu = dt/len(iimu)
                    #print('dt_imu',dt_imu)
                    if True:
                        for itmp,iv in enumerate(iimu):
                            date_imu = date0 + itmp * datetime.timedelta(seconds=dt_imu)
                            packages[iv]['date'] = date_imu
                            #print('iimu',iv,itmp,len(iimu),date0,date_imu)                            
                            
                            
                    iimu = []
        #if(HAVE_DATE):
        if(idate0 > -1):
            if(p['name'] == 'IMU'):
                iimu.append(i)
            if(p['name'] == 'Vec vel'):
                ivel.append(i)                
                #print('H',ivel)

    return packages



def calc_dates(packages,plot=False):
    nd = 0
    for p in packages:
        try:
            p['date']
            nd += 1
            if plot:
                print(p['name'].upper())
        except:
            if plot:
                print(p['name'].lower())

    return nd


def create_netcdf(fname, vel=True, imu=True):
    zlib = True # compression
    dataset = netCDF4.Dataset(fname, 'w')
    dataset.history = str(datetime.datetime.now()) + ': Pynortek version ' + version
    if vel:
        velgrp = dataset.createGroup('vel')
        velgrp.createDimension('count', 0)
        velgrp.createVariable('count', 'd', ('count'),zlib=zlib)
        velgrp.createVariable('time', 'd', ('count'),zlib=zlib)
        velgrp.createVariable('v1', 'd', ('count'),zlib=zlib)
        velgrp.createVariable('v2', 'd', ('count'),zlib=zlib)
        velgrp.createVariable('v3', 'd', ('count'),zlib=zlib)
        velgrp.createVariable('a1', 'd', ('count'),zlib=zlib)
        velgrp.createVariable('a2', 'd', ('count'),zlib=zlib)
        velgrp.createVariable('a3', 'd', ('count'),zlib=zlib)
        velgrp.createVariable('c1', 'd', ('count'),zlib=zlib)
        velgrp.createVariable('c2', 'd', ('count'),zlib=zlib)
        velgrp.createVariable('c3', 'd', ('count'),zlib=zlib)
        velgrp.createVariable('p', 'd', ('count'),zlib=zlib)
        velgrp.createVariable('AnaIn1', 'd', ('count'),zlib=zlib)
        velgrp.createVariable('AnaIn2', 'd', ('count'),zlib=zlib)
        # Units
        velgrp.variables['time'].units = 'seconds since 1970-01-01 00:00:00'        
        velgrp.variables['AnaIn1'].units = 'counts (V = 5/65536)'
        velgrp.variables['AnaIn2'].units = 'counts (V = 5/65536)'                
        velgrp.variables['v1'].units = 'mm/s'
        velgrp.variables['v2'].units = 'mm/s'
        velgrp.variables['v3'].units = 'mm/s'
        velgrp.variables['a1'].units = 'counts'
        velgrp.variables['a2'].units = 'counts'
        velgrp.variables['a3'].units = 'counts'
        velgrp.variables['c1'].units = '%'
        velgrp.variables['c2'].units = '%'
        velgrp.variables['c3'].units = '%'                
        velgrp.variables['p'].units = '0.001 dbar'        
    if imu:
        imugrp = dataset.createGroup('imu')
        imugrp.createDimension('count', 0)
        #velgrp.createVariable('time', 'd', ('count'))        

    for grp in dataset.groups:
        print(grp)
        print(dataset.groups[grp])
        
    return dataset

def create_group(dataset,package,group_name,zlib = True,time=True):
    """Creates a group for a specific datatype into the dataset
    """
    grp = dataset.createGroup(group_name)
    grp.createDimension('count', 0)
    grp.createVariable('count', 'd', ('count'),zlib=zlib)    
    if time:
        grp.createVariable('time', 'd', ('count'),zlib=zlib)    
        grp.variables['time'].units = 'seconds since 1970-01-01 00:00:00'
        
    for key in package.keys():
        print(key)
        if(key == 'units'):
            pass
        elif(key == 'id'):
            pass
        elif(key == 'sync'):
            pass
        else:
            print('type',type(package[key]))
            if( type(package[key]) == int):
                dtype = 'i'
            elif( type(package[key]) == float):
                dtype = 'f'
            else:
                dtype = None

            if(dtype is not None):
                print('Creating variable with type',key,dtype)
                varnc = grp.createVariable(key, dtype, ('count'),zlib=zlib)
                try:
                    unit = package['units'][key]
                except:
                    unit = ''

                print('Unit',unit)
                varnc.units = unit

    return grp        

def add_packages_to_netcdf(dataset,packages):
    #for grp in rootgrp.groups:
    velgrp = dataset.groups['vel']
    tvel_tmp = []    
    v1_tmp = []
    v2_tmp = []
    v3_tmp = []
    a1_tmp = []
    a2_tmp = []
    a3_tmp = []
    c1_tmp = []
    c2_tmp = []
    c3_tmp = []
    ana1_tmp = []
    ana2_tmp = []
    p_tmp = []
    for i,p in enumerate(packages):
        if(p['name'] == 'Vec sys'): # Vector system data
            print('Vector system')
            try:
                  sysgrp = dataset.groups['sys']
            except:
                  print('No system group found, will create it')
                  sysgrp = create_group(dataset,p,'sys')

            n = len(sysgrp.variables['count'])
            print('Length sysgrp',n)
            ttmp = netCDF4.date2num(p['date'],sysgrp.variables['time'].units)
            sysgrp.variables['time'][n] = ttmp            
            for key in p.keys():
                if( (type(p[key]) == int) or (type(p[key]) == float) ):
                    var = sysgrp.variables[key]
                    var[n] = p[key]
                
                  
        if(p['name'] == 'Vec vel'): # Velocity
            #print(i)
            try:
                p['date']
                HAS_DATE = True                
            except:
                HAS_DATE = False

            if HAS_DATE:
                ttmp = netCDF4.date2num(p['date'],velgrp.variables['time'].units)
            else:
                #print('No Date')                
                ttmp = -9999

            #print(ttmp,p['v1'])
            tvel_tmp.append(ttmp)
            v1_tmp.append(p['v1'])
            v2_tmp.append(p['v2'])
            v3_tmp.append(p['v3'])
            a1_tmp.append(p['a1'])
            a2_tmp.append(p['a2'])
            a3_tmp.append(p['a3'])
            c1_tmp.append(p['c1'])
            c2_tmp.append(p['c2'])
            c3_tmp.append(p['c3'])
            ana1_tmp.append(p['AnaIn1'])
            ana2_tmp.append(p['AnaIn2'])
            p_tmp.append(p['p'])                        

    n = len(velgrp.variables['count'])
    nn = len(v1_tmp) + n
    velgrp.variables['time'][n:nn] = tvel_tmp    
    velgrp.variables['v1'][n:nn] = v1_tmp
    velgrp.variables['v2'][n:nn] = v2_tmp
    velgrp.variables['v3'][n:nn] = v3_tmp
    velgrp.variables['a1'][n:nn] = a1_tmp
    velgrp.variables['a2'][n:nn] = a2_tmp
    velgrp.variables['a3'][n:nn] = a3_tmp
    velgrp.variables['c1'][n:nn] = c1_tmp
    velgrp.variables['c2'][n:nn] = c2_tmp
    velgrp.variables['c3'][n:nn] = c3_tmp
    velgrp.variables['AnaIn1'][n:nn] = ana1_tmp
    velgrp.variables['AnaIn2'][n:nn] = ana2_tmp
    velgrp.variables['p'][n:nn] = p_tmp


def find_time_range(fname):
    fsize = os.path.getsize(fname)    
    print(fname,'size',fsize)

    f = open(fname,'rb')    
    chunk = 4096*10
    package_tmp  = [] 
    #for i in range(n):
    i = 0
    if True:
        datastart = f.read(chunk)
        f.seek(fsize - chunk)
        dataend = f.read(chunk)        
        # Convert the data
        package_data_start     = convert_bin(datastart)
        package_data_end       = convert_bin(dataend)        

    f.close()
    dates = []

    for p in package_data_start['packages']:
        if(p['name'] == 'Vec sys'):
            dates.append(p['date'])

    for p in package_data_end['packages']:
        if(p['name'] == 'Vec sys'):
            dates.append(p['date'])

    ret_data = {'fname':fname,'first':min(dates),'last':max(dates)}
    print(ret_data)
    return ret_data


def bin2nc(fnames_in,fname_nc):
    """ Converts binary files to a netCDF
    """
    date_ranges = []
    date_first = []
    print('Checking times in input file(s)')
    if(type(fnames_in) == str):
        fnames_in = [fnames_in]
    for fname in fnames_in:
        drange = find_time_range(fname)
        date_ranges.append(drange)
        date_first.append(drange['first'])
        print(drange['fname'] + ':' + str(drange['first']) + ' - ' + str(drange['last']))

    HAS_DATA = True # TODO: Here we can check if we have valid data (i.e. datasets and the same headers/heads/sensors
    if(HAS_DATA):
        # Create netCDF file
        print('Creating netcdf file: ' + fname_nc)
        dataset = create_netcdf(fname_nc)
    else:
        return
    
    # Sort the datasets and read them in in the correct order
    ind_sorted = np.argsort(date_first)
    for ind_sort in ind_sorted:
        fname = date_ranges[ind_sort]['fname']
        print('Opening:' + fname)        
        f = open(fname,'rb')
        chunk = 4096*1000
        statistics_all = np.zeros((0,3))
        package_all  = []
        package_tmp  = [] 
        i = 0
        while True:
            offset = i * chunk
            data = f.read(chunk)
            #if i > 10:
            #    break
            if(offset/1000/1000 > 20): # In MB
                print('Reading only a part')
                break
            print(str(offset/1000/1000) + ' MB')
            if(len(data) < chunk):
                break
            if(i > 0):
                data = package_data['data_rest'] + data

            print('len data',len(data))
            # Convert the data
            package_data     = convert_bin(data,statistics = True)
            ilast            = package_data['ilast']
            statistics       = package_data['statistics']['packages']
            statistics       = np.asarray(statistics)
            statistics[:,0] += offset
            statistics[:,1] += offset
            print(np.shape(statistics),np.shape(statistics_all))
            statistics_all   = np.vstack((statistics_all,statistics))
            package_tmp.extend(package_data['packages'])
            HAVETIME = False
            if(len(package_tmp)>0):
                for itmp in range(len(package_tmp)-1,-1,-1):
                    p = package_tmp[itmp]
                    if(p['name'] == 'Vec vel'): # A time stamp package            
                        try:
                            p['date']
                            HAVETIME = True
                        except:
                            HAVETIME = False
                    
                    if(HAVETIME or (itmp == 0)):
                        print('len',len(package_tmp[itmp:]),'len0',len(package_tmp))
                        package_tmp[itmp:] = add_timestamp(package_tmp[itmp:],num_dates = 2)
                        print('Found a time package and a velocity package with time',itmp)
                        print(p)
                        break
                    
                # Adding the packages to netcdf
                for isave in range(len(package_tmp)-1,-1,-1): # Put only datasets with time stamp
                    p = package_tmp[isave]
                    if(p['name'] == 'Vec vel'): # A time stamp package            
                        try:
                            p['date']
                            break
                        except:
                            pass
                        
                if(isave > 0):
                    package_save = package_tmp[:isave]
                    package_tmp  = package_tmp[isave:]
                    print('0',package_tmp[0])
                    print('1',package_tmp[1])
                    #package_all.extend(package_save)
                    print('Saving data to nc file',len(package_save))
                    add_packages_to_netcdf(dataset,package_save)


            i += 1

        print('Closing file')
        f.close()
        
    dataset.close()
