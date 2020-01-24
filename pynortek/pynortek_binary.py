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

# Get the version
version_file = pkg_resources.resource_filename('pynortek','VERSION')
with open(version_file) as version_f:
   version = version_f.read().strip()

# Setup logging module
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
logger = logging.getLogger('pynortek')

raw_data_files = ['.prf','.vec'] # Names of raw binary data files

# 
def no_dates_index(packackes):
    for npi,p in enumerate(packages):
        try:
            p['date']
        except:
            print('no dates in index',npi,len(packages))
            
# Get the dates
def calc_dates(packages,plot=False):
    nd = 0
    nn = 0    
    for p in packages:
        try:
            p['date']
            nd += 1
            if plot:
                print(p['name'].upper())
        except:
            nn += 1
            if plot:
                print(p['name'].lower())

    print('with dates',nd,'no dates',nn)
    return nd

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


def convert_vector_system_data(data,apply_unit_factor = False,units = False,scaling = 1.0):
    #print('Vector system data')
    #print('System data',data)
    if(apply_unit_factor):
        pass

    conv_data = {}
    if units:
        conv_data['units'] = {}
        conv_data['dtype'] = {}
        conv_data['units']['minute'] = 'minute'
        conv_data['units']['second'] = 'second'
        conv_data['units']['day']    = 'day'
        conv_data['units']['hour']   = 'hour'
        conv_data['units']['year']   = 'year'
        conv_data['units']['month']  = 'month'
        conv_data['units']['bat']    = 'battery voltage (0.1 V)'
        conv_data['units']['SndVel'] = 'speed of sound (0.1 m/s)'
        conv_data['units']['Hdg']    = 'compass heading (0.1 deg)'
        conv_data['units']['Pitch']  = 'compass pitch (0.1 deg)'
        conv_data['units']['Roll']   = 'compass roll (0.1 deg)'
        conv_data['units']['T']      = 'temperature (0.01 deg C)'
        conv_data['units']['err']    = 'Error code'
        conv_data['units']['stat']   = 'Status code'
        conv_data['units']['AnaIn']  = 'counts (V = 5/65536)'
        conv_data['dtype']['minute'] = 'i'
        conv_data['dtype']['second'] = 'i'
        conv_data['dtype']['day']    = 'i'
        conv_data['dtype']['hour']   = 'i'
        conv_data['dtype']['year']   = 'i'
        conv_data['dtype']['month']  = 'i'
        conv_data['dtype']['bat']    = 'i'
        conv_data['dtype']['SndVel'] = 'i'
        conv_data['dtype']['Hdg']    = 'i'
        conv_data['dtype']['Pitch']  = 'i'
        conv_data['dtype']['Roll']   = 'i'
        conv_data['dtype']['T']      = 'i'
        conv_data['dtype']['err']    = 'i'
        conv_data['dtype']['stat']   = 'i'
        conv_data['dtype']['AnaIn']  = 'i'
        # Decoded status byte
        conv_data['dtype']['stat_power_level']    = 'u1' # unsigned byte
        conv_data['units']['stat_power_level']    = '00=0 (high), 10=2(low)'
        conv_data['dtype']['stat_wakeup_state']   = 'u1' # unsigned byte
        conv_data['units']['stat_wakeup_state']   = '00(0)=bad power,01 (1)=power applied,10(2)=break,11(3)=RTC alarmu'
        conv_data['dtype']['stat_Roll']           = 'u1' # unsigned byte
        conv_data['units']['stat_Roll']           = '0=ok, 1=out of range'
        conv_data['dtype']['stat_Pitch']          = 'u1' # unsigned byte
        conv_data['units']['stat_Pitch']          = '0=ok, 1=out of range'
        conv_data['dtype']['stat_Scaling']        = 'u1' # unsigned byte
        conv_data['units']['stat_Scaling']        = '0=mm/s, 1=0.1mm/s'
        conv_data['dtype']['stat_Orientation']    = 'u1' # unsigned byte
        conv_data['units']['stat_Orientation']    = '0=up, 1=down'
        return conv_data
    
    conv_data['minute']       = (data[4] & 0x0F) + 10 * ((data[4] >> 4) & 0x0F)
    conv_data['second']       = (data[5] & 0x0F) + 10 * ((data[5] >> 4) & 0x0F)
    conv_data['day']          = (data[6] & 0x0F) + 10 * ((data[6] >> 4) & 0x0F)
    conv_data['hour']         = (data[7] & 0x0F) + 10 * ((data[7] >> 4) & 0x0F)
    conv_data['year']         = (data[8] & 0x0F) + 10 * ((data[8] >> 4) & 0x0F) + 2000
    conv_data['month']        = (data[9] & 0x0F) + 10 * ((data[9] >> 4) & 0x0F)
    conv_data['bat']          = struct.unpack('<H', data[10:12])[0] # Little endian
    conv_data['SndVel']       = struct.unpack('<H', data[12:14])[0] # Little endian
    conv_data['Hdg']          = struct.unpack('<h', data[14:16])[0] # Little endian
    conv_data['Pitch']        = struct.unpack('<h', data[16:18])[0] # Little endian
    conv_data['Roll']         = struct.unpack('<h', data[18:20])[0] # Little endian
    conv_data['T']            = struct.unpack('<h', data[20:22])[0] # Little endian
    conv_data['err']          = int(data[22])
    conv_data['stat']         = int(data[23])
    conv_data['AnaIn']        = float(struct.unpack('<H', data[20:22])[0]) # Little endian
    conv_data['date']         = datetime.datetime(conv_data['year'],conv_data['month'],conv_data['day'],conv_data['hour'],conv_data['minute'],conv_data['second'])
    # Status
    conv_data['stat_power_level']    = int((data[23] & 0b11000000) >>6 )
    conv_data['stat_wakeup_state']   = int((data[23] & 0b00110000) >>4 )
    conv_data['stat_Roll']           = int((data[23] & 0b00001000) >>3 )
    conv_data['stat_Pitch']          = int((data[23] & 0b00000100) >>2 )
    conv_data['stat_Scaling']        = int((data[23] & 0b00000010) >>1 )
    conv_data['stat_Orientation']    = int((data[23] & 0b00000001))
    #print('Scaling',conv_data['stat_Scaling'])
    #print('Orientation',conv_data['stat_Orientation'])
    #print('power level',conv_data['stat_power_level'])        
    return conv_data


def convert_vector_velocity_header(data,apply_unit_factor = False, scaling = 1.0):
    """ Converts binary data in a vector velocity data structure
    """
    pass
    #print('Vector velocity header')
    #print(data)
    #print('End Vectir velocity header')


def convert_vector_IMU(data,apply_unit_factor = False,units = False, scaling = 1.0):
    """ Converts binary data in a vector velocity data structure
    """
    conv_data = {}
    if units:
        conv_data['units']  = {}
        conv_data['dtype']  = {}
        conv_data['units']['EnsCnt'] = 'Ensemble Counter'
        conv_data['units']['AHRSId'] = 'AHRS ID, 0xc3'
        conv_data['units']['DeltaAngleX'] = 'Delta Angle x (radians)'
        conv_data['units']['DeltaAngleY'] = 'Delta Angle y (radians)'
        conv_data['units']['DeltaAngleZ'] = 'Delta Angle z (radians)'
        conv_data['units']['DeltaVelX'] = 'Delta Velocity Rate x (g*seconds)'
        conv_data['units']['DeltaVelY'] = 'Delta Velocity Rate y (g*seconds)'
        conv_data['units']['DeltaVelZ'] = 'Delta Velocity Rate z (g*seconds)'
        conv_data['units']['M11'] = 'Orientation Matrix X (M11). Describes the orientation of the IMU'
        conv_data['units']['M12'] = 'Orientation Matrix X (M12). Describes the orientation of the IMU'
        conv_data['units']['M13'] = 'Orientation Matrix X (M13). Describes the orientation of the IMU'
        conv_data['units']['M21'] = 'Orientation Matrix X (M21). Describes the orientation of the IMU'
        conv_data['units']['M22'] = 'Orientation Matrix X (M22). Describes the orientation of the IMU'
        conv_data['units']['M23'] = 'Orientation Matrix X (M23). Describes the orientation of the IMU'
        conv_data['units']['M31'] = 'Orientation Matrix X (M31). Describes the orientation of the IMU'
        conv_data['units']['M32'] = 'Orientation Matrix X (M32). Describes the orientation of the IMU'
        conv_data['units']['M33'] = 'Orientation Matrix X (M33). Describes the orientation of the IMU'
        conv_data['units']['pitch']       = 'Pitch [deg]'
        conv_data['units']['roll']        = 'Roll [deg]'
        conv_data['units']['yaw']         = 'Yaw [deg]'
        conv_data['units']['timer'] = 'Timer value, measures the time since start of each burst. To convert the timer value to time in seconds, divide by 62,500.'
        conv_data['dtype']['EnsCnt']      = 'i'
        conv_data['dtype']['AHRSId']      = 'i'
        conv_data['dtype']['DeltaAngleX'] = 'f'
        conv_data['dtype']['DeltaAngleY'] = 'f'
        conv_data['dtype']['DeltaAngleZ'] = 'f'
        conv_data['dtype']['DeltaVelX']   = 'f'
        conv_data['dtype']['DeltaVelY']   = 'f'
        conv_data['dtype']['DeltaVelZ']   = 'f'
        conv_data['dtype']['M11']         = 'f'
        conv_data['dtype']['M12']         = 'f'
        conv_data['dtype']['M13']         = 'f'
        conv_data['dtype']['M21']         = 'f'
        conv_data['dtype']['M22']         = 'f'
        conv_data['dtype']['M23']         = 'f'
        conv_data['dtype']['M31']         = 'f'
        conv_data['dtype']['M32']         = 'f'
        conv_data['dtype']['M33']         = 'f'
        conv_data['dtype']['timer']       = 'i'
        conv_data['dtype']['pitch']       = 'f'
        conv_data['dtype']['roll']        = 'f'
        conv_data['dtype']['yaw']         = 'f'                        
        return conv_data
    
    conv_data['EnsCnt'] = data[4]
    conv_data['AHRSId'] = data[5]
    conv_data['DeltaAngleX'] = struct.unpack('<f', data[6:10])[0] # Little endian
    conv_data['DeltaAngleY'] = struct.unpack('<f', data[10:14])[0] # Little endian
    conv_data['DeltaAngleZ'] = struct.unpack('<f', data[14:18])[0] # Little endian
    conv_data['DeltaVelX'] = struct.unpack('<f', data[18:22])[0] # Little endian
    conv_data['DeltaVelY'] = struct.unpack('<f', data[22:26])[0] # Little endian
    conv_data['DeltaVelZ'] = struct.unpack('<f', data[26:30])[0] # Little endian
    conv_data['M11']   = struct.unpack('<f', data[30:34])[0] # Little endian
    conv_data['M12']   = struct.unpack('<f', data[34:38])[0] # Little endian
    conv_data['M13']   = struct.unpack('<f', data[38:42])[0] # Little endian
    conv_data['M21']   = struct.unpack('<f', data[42:46])[0] # Little endian
    conv_data['M22']   = struct.unpack('<f', data[46:50])[0] # Little endian
    conv_data['M23']   = struct.unpack('<f', data[50:54])[0] # Little endian
    conv_data['M31']   = struct.unpack('<f', data[54:58])[0] # Little endian
    conv_data['M32']   = struct.unpack('<f', data[58:62])[0] # Little endian
    conv_data['M33']   = struct.unpack('<f', data[62:66])[0] # Little endian
    conv_data['pitch'] = np.arcsin(conv_data['M13'])/2/np.pi*360
    conv_data['roll']  = np.arctan2(conv_data['M23'],conv_data['M33'])/2/np.pi*360
    conv_data['yaw']   = np.arctan2(conv_data['M12'],conv_data['M11'])/2/np.pi*360
    conv_data['timer'] = struct.unpack('<i', data[66:70])[0] # Little endian
    return conv_data

def convert_vector_velocity(data,apply_unit_factor = False,units = False, scaling = 1.0):
    """ Converts binary data in a vector velocity data structure
    """
    #print('Vector velocity data')
    #print(data)
    conv_data = {}    
    if units:
        conv_data['units']  = {}
        conv_data['dtype']  = {}
        conv_data['units']['Count']  = 'ensemble counter'
        conv_data['units']['AnaIn2'] = 'counts (V = 5/65536)'
        conv_data['units']['AnaIn1'] = 'counts (V = 5/65536)'
        conv_data['units']['p']      = 'pressure (0.001 dbar)'
        conv_data['units']['v1']     = 'velocity beam1 or X or East (m/s)'
        conv_data['units']['v2']     = 'velocity beam2 or Y or North (m/s)'
        conv_data['units']['v3']     = 'velocity beam3 or Z or Up (m/s)'
        conv_data['units']['a1']     = 'amplitude beam1 (counts)'
        conv_data['units']['a2']     = 'amplitude beam2 (counts)'
        conv_data['units']['a3']     = 'amplitude beam3 (counts)'
        conv_data['units']['c1']     = 'correlation beam1 (%)'
        conv_data['units']['c2']     = 'correlation beam2 (%)'
        conv_data['units']['c3']     = 'correlation beam3 (%)'
        conv_data['dtype']['Count']  = 'i'
        conv_data['dtype']['AnaIn2'] = 'i'
        conv_data['dtype']['AnaIn1'] = 'i'
        conv_data['dtype']['p']      = 'i'
        conv_data['dtype']['v1']     = 'f'
        conv_data['dtype']['v2']     = 'f'
        conv_data['dtype']['v3']     = 'f'
        conv_data['dtype']['a1']     = 'i'
        conv_data['dtype']['a2']     = 'i'
        conv_data['dtype']['a3']     = 'i'
        conv_data['dtype']['c1']     = 'i'
        conv_data['dtype']['c2']     = 'i'
        conv_data['dtype']['c3']     = 'i'
        return conv_data
        

    conv_data['Count']  = data[3]
    conv_data['AnaIn2'] = data[2] + 256 * data[5]
    conv_data['AnaIn1'] = data[8] + 256 * data[9]
    conv_data['p']      = data[4] * 65536 + data[7] * 256 + data[6] # [0.001 dbar]
    conv_data['v1']     = struct.unpack('<h', data[10:12])[0] * scaling
    conv_data['v2']     = struct.unpack('<h', data[12:14])[0] * scaling
    conv_data['v3']     = struct.unpack('<h', data[14:16])[0] * scaling
    conv_data['a1']     = data[16] # amplitude beam1 (counts)
    conv_data['a2']     = data[17] # amplitude beam2 (counts)
    conv_data['a3']     = data[18] # amplitude beam3 (counts)
    conv_data['c1']     = data[19] # correlation beam1 (%)
    conv_data['c2']     = data[20] # correlation beam2 (%)
    conv_data['c3']     = data[21] # correlation beam3 (%)

    return conv_data

def convert_hw_conf(data,apply_unit_factor = False, scaling = 1.0):
    conv_data = {}
    #conv_data['SerialNo'] = data[4:18].decode('utf-8')
    #'VEC13244\xd7\x054.22' works only with latin-1
    conv_data['SerialNo'] = data[4:18].decode('latin-1')
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

def convert_head_conf(data,apply_unit_factor = False, scaling = 1.0):
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

def convert_usr_conf(data,apply_unit_factor = False, scaling = 1.0):
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
#package_aquadopp_HRprofiler = {'name':'High resolution Aquadopp Profiler velocity','sync':b'\xa5','id':b'\x2a','size':None,'function':None}
package_awac_profile = {'name':'Awac velocity profile','sync':b'\xa5','id':b'\x20','size':None,'sizeoff':2,'function':None}
package_awac_wave_header = {'name':'Awac wave header','sync':b'\xa5','id':b'\x31','size':60,'function':None}
package_awac_stage = {'name':'Awac stage data','sync':b'\xa5','id':b'\x42','size':None,'sizeoff':2,'function':None}
package_awac_wave = {'name':'Awac wave data','sync':b'\xa5','id':b'\x30','size':24,'function':None}
package_awac_wave_suv = {'name':'Awac wave data for suv','sync':b'\xa5','id':b'\x36','size':24,'function':None}

nortek_packages = [package_aquadopp_velocity,
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
            #package_aquadopp_HRprofiler,
            package_awac_profile,
            package_awac_wave_header,
            package_awac_stage,
            package_awac_wave,
            package_awac_wave_suv]



def convert_bin(data, apply_unit_factor = False, statistics = False):
    """ Converts a binary data stream into a list of packages (dictionaries)
    """
    scaling = np.NaN # The scaling of the data (depends on the status bit in the system package
    conv_data_all = []
    #for i in range(len(data)-1):
    i = 0
    ilast = 0 # Index after of the last found package
    if(statistics):
        statistic_dict = {}
        statistic_dict['packages'] = []
        statistic_dict['package_names'] = []
        statistic_dict['package_num'] = []                
        for npi,package in enumerate(nortek_packages):
            statistic_dict['package_names'].append(package['name'])
            statistic_dict['package_num'].append(0)            
            
    while i < (len(data)-1):
        d1 = data[i:i+1]
        d2 = data[i+1:i+2]        
        #print(i,d1,d2)
        FOUND_PACKAGE = False
        for npi,package in enumerate(nortek_packages):
            if((d1 == package['sync']) and (d2 == package['id']) and (FOUND_PACKAGE == False)):
                if package['size'] is not None:
                    psize = package['size']
                else:
                    print('Package:',package)
                    offset = i+package['sizeoff']
                    if((i+offset) < len(data)): # Do we have enough data for the package?                    
                        psize = int.from_bytes(data[offset:offset+2], byteorder='little')
                        print('Size read:',psize)
                    else:
                        break

                if((i+psize) < len(data)): # Do we have enough data for the package?
                    data_package = data[i:i+psize]
                    if(statistics):                    
                        statistic_dict['packages'].append([i,i+psize,npi])
                        statistic_dict['package_num'][npi] += 1
                        
                    checksum = int.from_bytes(data[i+psize-2:i+psize], byteorder='little')
                    checksum_calc = calc_checksum(data[i:i+psize-2])
                    FLAG_CHECKSUM=False
                    if(checksum == checksum_calc):
                        FLAG_CHECKSUM=True

                    # Convert the data
                    if package['function'] is not None:
                        conv_data = package['function'](data_package, apply_unit_factor = apply_unit_factor, scaling = scaling)
                    else:
                        print('No function available for package:' + package['name'])
                        #conv_data = None

                    # Add name and sync/id
                    if(conv_data == None):
                        conv_data = {}
                        
                    conv_data['name'] = package['name']
                    conv_data['sync'] = package['sync']
                    conv_data['id'] = package['id']
                    # Check if we have a scaling
                    if(np.isnan(scaling)):
                        if(conv_data['name'] == 'Vec sys'): # A system package
                            if(conv_data['stat_Scaling'] >0): # 0.1 mm/s to m/s
                                scaling = 1/10000.0
                            else: # 1.0 mm/s to m/s
                                scaling = 1/1000.0

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
    Arguments:
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
    idate_sys = []
    idate_vel = []
    idate_imu = []        
    #for i,p in enumerate(packages):
    # Scanning packages for system, imu and velocity content
    for i,p in enumerate(packages):
        p = packages[i]
        if(p['name'] == 'IMU'): # An IMU package
            idate_imu.append(i)
        if(p['name'] == 'Vec vel'): # A velocity package
            idate_vel.append(i)                        
        if(p['name'] == 'Vec sys'): # A time stamp package
            num_system += 1
            idate_sys.append(i)


    idate_imu = np.asarray(idate_imu)
    idate_vel = np.asarray(idate_vel)
    for i in range(len(idate_sys)):
        if(len(idate_sys) > (i+num_dates)): # Do we have enough dates?
            idate0 = idate_sys[i]
            idate1 = idate_sys[i+num_dates]
            date0 = packages[idate0]['date']
            date1 = packages[idate1]['date']                
            ind_vel = idate_vel[(idate_vel >= idate0) & (idate_vel <= (idate1))]
            ind_imu = idate_imu[(idate_imu >= idate0) & (idate_imu <= (idate1))]            
            #print('ind',idate0,idate1,min(ind_vel),max(ind_vel))
            dt = (date1 - date0).total_seconds()
            # A time package should be there every second
            # We found more than one package, add timestamp and
            # after done that roll loop back to next timestamp
            # after idate0
            if(len(ind_vel)>0): 
                dt_vel = dt/len(ind_vel)
                #print('dt',dt,len(ind_vel),dt_vel)                
                for itmp,iv in enumerate(ind_vel):
                    date_vel = date0 + itmp * datetime.timedelta(seconds=dt_vel)
                    packages[iv]['date'] = date_vel


                    
            # Add timestamps to IMU package
            if(len(ind_imu)>0): # We found more than one package
                dt_imu = dt/len(ind_imu)
                #print('dt_imu',dt_imu)
                for itmp,iv in enumerate(ind_imu):
                    date_imu = date0 + itmp * datetime.timedelta(seconds=dt_imu)
                    packages[iv]['date'] = date_imu
        else:
            pass
            #print('Stopping at package',i,len(idate_sys),idate_sys[i-1],len(packages))

    return packages





def create_netcdf(fname, vel=True, imu=True):
    print('Creating netcdf with IMU:' + str(imu))
    zlib = True # compression
    dataset = netCDF4.Dataset(fname, 'w')
    dataset.history = str(datetime.datetime.now()) + ': Pynortek version ' + version
    conv_data = convert_vector_system_data(None,units = True)    
    sysgrp = create_group(dataset,conv_data,'sys')
    if vel:    
        conv_data = convert_vector_velocity(None,units = True)
        create_group(dataset,conv_data,'vel')
    if imu:
        conv_data = convert_vector_IMU(None,units = True)    
        imugrp = create_group(dataset,conv_data,'imu',time=True)        

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
        
    for key in package['units'].keys():
        if False:
            pass
        else:
            dtype = package['dtype'][key]
            if(dtype is not None):
                print('Creating variable with type',key,dtype)
                varnc = grp.createVariable(key, dtype, ('count'),zlib=zlib)
                unit = package['units'][key]
                varnc.units = unit

    return grp        

def add_packages_to_netcdf(dataset,packages):
    #for grp in rootgrp.groups:
    velgrp = dataset.groups['vel']
    # Velocity veriables
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
    Count_tmp = []    
    ana1_tmp = []
    ana2_tmp = []
    p_tmp = []
    # IMU
    timu_tmp = []        
    EnsCnt_tmp  = []
    AHRSId_tmp  = []
    DeltaAngleX_tmp  = []
    DeltaAngleY_tmp = []
    DeltaAngleZ_tmp = []
    DeltaVelX_tmp = []
    DeltaVelY_tmp = []
    DeltaVelZ_tmp = []
    M11_tmp = []
    M12_tmp = []
    M13_tmp = []
    M21_tmp = []
    M22_tmp = []
    M23_tmp = []
    M31_tmp = []
    M32_tmp = []
    M33_tmp = []
    pitch_tmp = []
    yaw_tmp = []
    roll_tmp = []
    imutimer_tmp = []
    
    for i,p in enumerate(packages):
        if(p['name'] == 'Vec sys'): # Vector system data
            #print('Vector system')
            sysgrp = dataset.groups['sys']
            n = len(sysgrp.variables['count'])
            #print('Length sysgrp',n)
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
            Count_tmp.append(p['Count'])            
            ana1_tmp.append(p['AnaIn1'])
            ana2_tmp.append(p['AnaIn2'])
            p_tmp.append(p['p'])
        if(p['name'] == 'IMU'): # IMU
            #print(i)
            imugrp = dataset.groups['imu']            
            try:
                p['date']
                HAS_DATE = True                
            except:
                HAS_DATE = False

            if HAS_DATE:
                ttmp = netCDF4.date2num(p['date'],imugrp.variables['time'].units)
            else:
                #print('No Date')                
                ttmp = -9999            

            timu_tmp.append(ttmp)        
            EnsCnt_tmp.append(p['EnsCnt'])
            AHRSId_tmp.append(p['AHRSId'])
            DeltaAngleX_tmp.append(p['DeltaAngleX'])
            DeltaAngleY_tmp.append(p['DeltaAngleY'])
            DeltaAngleZ_tmp.append(p['DeltaAngleZ'])
            DeltaVelX_tmp.append(p['DeltaVelX'])
            DeltaVelY_tmp.append(p['DeltaVelY'])
            DeltaVelZ_tmp.append(p['DeltaVelZ'])
            M11_tmp.append(p['M11'])
            M12_tmp.append(p['M12'])
            M13_tmp.append(p['M13'])
            M21_tmp.append(p['M21'])
            M22_tmp.append(p['M22'])
            M23_tmp.append(p['M23'])
            M31_tmp.append(p['M31'])
            M32_tmp.append(p['M32'])
            M33_tmp.append(p['M33'])
            pitch_tmp.append(p['pitch'])
            yaw_tmp.append(p['yaw'])
            roll_tmp.append(p['roll'])
            imutimer_tmp.append(p['timer'])

    # Fill the velocities
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
    velgrp.variables['Count'][n:nn] = Count_tmp    
    velgrp.variables['AnaIn1'][n:nn] = ana1_tmp
    velgrp.variables['AnaIn2'][n:nn] = ana2_tmp
    velgrp.variables['p'][n:nn] = p_tmp
    # If we have IMU data
    if(len(AHRSId_tmp)>0):
        n = len(imugrp.variables['count'])        
        nn = len(DeltaAngleX_tmp) + n
        imugrp.variables['time'][n:nn] = timu_tmp    
        imugrp.variables['EnsCnt'][n:nn] = EnsCnt_tmp
        imugrp.variables['AHRSId'][n:nn] = AHRSId_tmp
        imugrp.variables['DeltaAngleX'][n:nn] = DeltaAngleX_tmp
        imugrp.variables['DeltaAngleY'][n:nn] = DeltaAngleY_tmp
        imugrp.variables['DeltaAngleZ'][n:nn] = DeltaAngleZ_tmp
        imugrp.variables['DeltaVelX'][n:nn] = DeltaVelX_tmp
        imugrp.variables['DeltaVelY'][n:nn] = DeltaVelY_tmp
        imugrp.variables['DeltaVelZ'][n:nn] = DeltaVelZ_tmp
        imugrp.variables['timer'][n:nn] = imutimer_tmp
        imugrp.variables['M11'][n:nn]   = M11_tmp
        imugrp.variables['M12'][n:nn]   = M12_tmp
        imugrp.variables['M13'][n:nn]   = M13_tmp
        imugrp.variables['M21'][n:nn]   = M21_tmp
        imugrp.variables['M22'][n:nn]   = M22_tmp
        imugrp.variables['M23'][n:nn]   = M23_tmp
        imugrp.variables['M31'][n:nn]   = M31_tmp
        imugrp.variables['M32'][n:nn]   = M32_tmp
        imugrp.variables['M33'][n:nn]   = M33_tmp
        imugrp.variables['pitch'][n:nn] = pitch_tmp 
        imugrp.variables['roll'][n:nn]  = roll_tmp 
        imugrp.variables['yaw'][n:nn]   = yaw_tmp 


def find_time_range(fname):
    """Looks for time and IMU packages in dataset and returns if IMU has
    been found as well as the first and last time package
    """
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

    HAS_IMU = False
    for p in package_data_start['packages']:
        if(p['name'] == 'IMU'):
            HAS_IMU = True

    usr_cfg = None
    hw_cfg = None
    head_cfg = None
    for p in package_data_start['packages']:
        if(p['name'] == 'Vec sys'):
            dates.append(p['date'])

        if(p['name'] == 'user config'):
            usr_cfg = p
        if(p['name'] == 'hardware config'):
            hw_cfg   = p
        if(p['name'] == 'head config'):
            head_cfg = p
        
    for p in package_data_end['packages']:
        if(p['name'] == 'Vec sys'):
            dates.append(p['date'])


    ret_data = {'fname':fname,'first':min(dates),'last':max(dates),'IMU':HAS_IMU,'fsize':fsize,'usr_cfg':usr_cfg,'hw_cfg':hw_cfg,'head_cfg':head_cfg}
    return ret_data


#def bin2nc(fnames_in,fname_nc,chunksize = 4096*2000, nbytes=None):
def bin2nc(fnames_in,fname_nc,chunksize = 4096*500, nbytes=None):
    """ Converts binary files to a netCDF
    Arguments:
       chunksize: The number of bytes read at once
       nbytes: The number of bytes read from file
    """
    date_ranges = []
    date_first = []
    print('Checking times in input file(s)')
    HAS_IMU = False
    if(type(fnames_in) == str):
        fnames_in = [fnames_in]
        
    for fname in fnames_in:
        drange = find_time_range(fname)
        date_ranges.append(drange)
        date_first.append(drange['first'])
        print(drange['fname'] + ':' + str(drange['first']) + ' - ' + str(drange['last']))
        HAS_IMU = drange['IMU']

    HAS_DATA = True # TODO: Here we can check if we have valid data (i.e. datasets and the same headers/heads/sensors
    if(HAS_DATA):
        # Create netCDF file
        print('Creating netcdf file: ' + fname_nc)
        dataset = create_netcdf(fname_nc,imu=HAS_IMU)
    else:
        return

    # Calculate the total file size to be read on
    fsize_total = 0
    for d in date_ranges:
        fsize_total += d['fsize']
        
    # Sort the datasets and read them in in the correct order
    ind_sorted = np.argsort(date_first)
    bytes_read_total = 0
    for ind_sort in ind_sorted:
        fname = date_ranges[ind_sort]['fname']
        fsize = date_ranges[ind_sort]['fsize'] # file size
        print('Opening:' + fname)        
        f = open(fname,'rb')
        chunk = chunksize
        statistics_all = np.zeros((0,3))
        statistics_num_packages = np.zeros((len(nortek_packages)))
        package_all  = []
        package_tmp  = []
        bytes_read = 0        
        i = 0
        while True:
            offset = i * chunk
            data = f.read(chunk)
            bytes_read += len(data)            
            bytes_read_total += len(data)
            #if i > 10:
            #    break
            #if(offset/1000/1000 > 20): # In MB
            #    print('Reading only a part')
            #    break
            print(str(bytes_read/1000/1000) + ' MB of file with size ' + '{:5.9f}'.format(fsize/1000/1000) + ' MB')
            print(str(bytes_read_total/1000/1000) + ' MB of all files with total size ' + '{:5.9f}'.format(fsize_total/1000/1000) + ' MB')
            # Only read part of the dataset
            if(nbytes is not None):
                if(bytes_read_total >= nbytes):
                    print('Number of bytes read threshold reached')
                    break
            if(len(data) < chunk):
                break
            if(i > 0):
                data = package_data['data_rest'] + data

            # Convert the data
            package_data     = convert_bin(data,statistics = True)
            ilast            = package_data['ilast']
            statistics       = package_data['statistics']['packages']
            statistics       = np.asarray(statistics)
            statistics[:,0] += offset
            statistics[:,1] += offset
            num_packages       = package_data['statistics']['package_num']
            num_packages       = np.asarray(num_packages)            
            #print(np.shape(statistics),np.shape(statistics_all))
            statistics_all           = np.vstack((statistics_all,statistics))
            statistics_num_packages += num_packages
            package_tmp.extend(package_data['packages'])
            HAVETIME = False
            if(len(package_tmp)>0):
                # Go backwards thorugh the new packages and search
                # for the first one with a timestamp, if found
                # take the packages from that package onwards                
                for itmp in range(len(package_tmp)-1,-1,-1):
                    p = package_tmp[itmp]
                    if(p['name'] == 'Vec vel'): 
                        try:
                            p['date']
                            HAVETIME = True
                        except:
                            HAVETIME = False
                    
                    if(HAVETIME or (itmp == 0)):
                        package_tmp[itmp:] = add_timestamp(package_tmp[itmp:],num_dates = 2)
                        break
                    
                # Adding the packages to netcdf
                for isave in range(len(package_tmp)-1,-1,-1): # Put only datasets with timestamp
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
                    #package_all.extend(package_save)
                    #print('Saving data to nc file',len(package_save))
                    #print('Statistics',statistics_num_packages)
                    # Print statistics of packages
                    print('Packages read:')
                    for npi,pack in enumerate(nortek_packages):
                        if statistics_num_packages[npi] > 0:
                            print(pack['name'] + ': ' + str(int(statistics_num_packages[npi])))
                            
                    add_packages_to_netcdf(dataset,package_save)


            i += 1

        print('Closing file')
        f.close()
        
    dataset.close()


def vecinfo(fnames_in):
    """ Prints useful information of a Nortek .vec binary file
    """
    if(type(fnames_in) == str):
        fnames_in = [fnames_in]
        
    for fname in fnames_in:
        drange = find_time_range(fname)
        print('First',drange['first'])
        print('Last',drange['last'])        
        print('User config')
        print(drange['usr_cfg'])
        print('Head config')
        print(drange['head_cfg'])
        print('Hardware config')
        print(drange['hw_cfg'])                

def vec2nc():
    """ A function call for a command line based conversion of a .vec file to a netCDF file. Basically a wrapper for bin2nc
    """
    in_help         = 'One or more Nortek Vector binary file(s) (filename.VEC)'
    nc_help         = 'Name of the netCDF output file (typically filename.nc)'
    nbytes_help     = 'Read only number of bytes of the total length of all datasets'
    info_help       = 'Prints useful information about files'
    parser = argparse.ArgumentParser(description='Convert a Nortek .VEC file binary Vector file into netCDF file')
    parser.add_argument('--version', action='version', version='%(prog)s ' + version)
    parser.add_argument('--nbytes', help=nbytes_help)
    parser.add_argument('--info', action='store_true', help=info_help)    
    parser.add_argument('filename_bin',nargs='+',help=in_help)
    parser.add_argument('filename_nc',help=nc_help)        
    args = parser.parse_args()

    filename_bin = args.filename_bin
    filename_nc = args.filename_nc
    print('Hallo!')
    print(filename_bin)
    print(filename_nc)
    print(args.nbytes)
    # Number of bytes to read
    if(args.nbytes is not None):
        nbytes = int(float(args.nbytes))
    else:
        nbytes = None

    # Just print information
    if(args.info):
        vecinfo(filename_bin)
        return

    if(filename_nc is not None):
        if(os.path.isfile(filename_nc) ):
            print('Target nc file is existing, will quit now')
            return

        print('Start converting file(s)')
        bin2nc(filename_bin,filename_nc,nbytes = nbytes)
