import numpy as np
import logging
import sys
import pkg_resources
import pytz
import datetime
import os
import re
from numpy import cos,sin

# Get the version
version_file = pkg_resources.resource_filename('pynortek','VERSION')

# Setup logging module
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
logger = logging.getLogger('pynortek')

def xyz2enu(u,v,w,head,pitch,roll,inverse=False):
    """Transforms volcities in XYZ coordinates to ENU, or vice versa if
    inverse=True. Transformation is done according to the Nortek
    convention
    """
    # convert to radians
    hh = np.pi*(head-90)/180
    pp = np.pi*pitch/180
    rr = np.pi*roll/180

    ut = np.NaN(shape(u))
    vt = np.NaN(shape(u))
    wt = np.NaN(shape(u))    

    for i in range(len(head)):
        # generate heading matrix
        H = np.matrix([[cos(hh[i]), sin(hh[i]), 0],[-sin(hh[i]), cos(hh[i]), 0],[0, 0, 1]])
        # generate combined pitch and roll matrix
        P = [[cos(pp[i]), -sin(pp[i])*sin(rr[i]), -cos(rr[i])*sin(pp[i])],
             [0,           cos(rr[i]),                       -sin(rr[i])],
             [sin(pp[i]),  sin(rr[i])*cos(pp[i]),  cos(pp[i])*cos(rr[i])]]

        R = H*P
        print(R)
        if(inverse):
            R = np.inv(R)

        # do transformation
        ut[i]  = R[0,0]*u[i] + R[0,1]*v[i] + R[0,2]*w[i];
        vt[i]  = R[1,0]*u[i] + R[1,1]*v[i] + R[1,2]*w[i];
        wt[i]  = R[2,0]*u[i] + R[2,1]*v[i] + R[2,2]*w[i];

        

raw_data_files = ['.prf','.vec'] # Names of raw binary data files 
class pynortek():
    """A Nortek parsing object

    Author: Peter Holtermann (peter.holtermann@io-warnemuende.de)

    Usage:
       >>>filename='test'
       >>>aquadopp = pynortek(filename)

    """
    def __init__(self,filename, verbosity=logging.DEBUG, timezone=pytz.UTC):
        """
        """
        logger.setLevel(verbosity)
        self.timezone = timezone
        self.deployment = os.path.split(filename)[-1]
        self.fpath = os.path.split(filename)[0]
        self.rawdata = {}
        print(self.deployment)
        print(self.fpath)        
        filename_hdr = filename + '.hdr'
        logger.debug('Trying to open header file: ' + filename_hdr)
        try:
            fhdr = open(filename_hdr)
        except Exception as e:
            logger.warning('Could not open header file, exiting')
            return

        header = self.parse_header(fhdr)
        self.header = header
        print(header)
        print('Loading files')
        for fread in header['files']:
            print(fread)
            IS_RAW = False
            for rawname in raw_data_files:
                if(rawname in fread.lower()):
                    IS_RAW=True

            if(IS_RAW == False):
                print('Loading ' + fread)
                suffix = fread.split('.')[-1]
                fname_tmp = os.path.join(self.fpath,fread)
                print(fname_tmp)
                data_tmp = np.loadtxt(fname_tmp)
                self.rawdata[suffix] = data_tmp


        # Process the raw data just loaded
        self.process_rawdata()
        
    def parse_header(self,fhdr):
        """ Parses a nortek header file
        """
        header = {}
        datefmt = '%d.%m.%Y %H:%M:%S'
        header_field = None
        header['files'] = []
        while True:
            l = fhdr.readline()
            if(len(l) == 0):
                break

            # Find all files to be read
            if((l[0] == '[')):
                ftmp = l.split("\\")[-1].replace(']','').replace('\n','')
                header['files'].append(ftmp)
                # If we have a sensor file, check position of fields
                if('.sen' in l[-7:]):
                    print('Sensor file')
                    header_field = 'sensors'
                    header[header_field] = {}

            # Transducer distance 
            if(('Beam' in l) and ('Vertical' in l)):
                print('Transducer distance')
                header_field = 'distance'
                header[header_field] = {'cell':[],'beam':[],'vertical':[]}
                continue

            
            # Check for the header field        
            if('User setup' in l):
                print('User setup')
                header_field = 'User setup'
                header[header_field] = {}                
            elif('Hardware configuration' in l):
                print('Hardware configuration')                    
                header_field = 'Hardware configuration'
                header[header_field] = {}                   
            elif('Head configuration' in l):
                header_field = 'Head configuration'
                header[header_field] = {}

            #print(l)
            if(header_field is not None): # Check if field is over (one empty line)
                if(len(l) <= 2):
                    print('Header ' + header_field + ' over')
                    header_field = None

            # Check for a one line list        
            ind = l.find('  ')
            if(ind >= 0):
                if('Number of measurements' in l):
                    header['Number of measurements'] = int(l.split()[-1])
                elif('Coordinate system' in l):
                    header['Coordinate system'] = l.split()[-1]
                    logger.debug('Coordinate system found: ' + header['Coordinate system'])
                elif('Horizontal velocity range' in l):
                    header['Horizontal velocity range'] = float(l.split()[-2])
                    logger.debug('Horizontal velocity range: ' + str(header['Horizontal velocity range']))
                elif('Vertical velocity range' in l):
                    header['Vertical velocity range'] = float(l.split()[-2])
                    logger.debug('Vertical velocity range: ' + str(header['Vertical velocity range']))
                elif('Orientation' in l):
                    header['Orientation'] = l.split()[-1]
                    if('DOWN' in header['Orientation']):
                        header['updown'] = True
                    else:
                        header['updown'] = False

                    logger.debug('Orientation ' + header['Orientation'] + ' updown:' + str(header['updown']))
                    
                    
                elif('Number of checksum errors' in l):
                    header['Number of checksum errors'] = int(l.split()[-1])
                elif('Time of first measurement' in l):
                    ind2 = l.rfind('  ')
                    tstr = l[ind2+2:].replace('\n','')
                    ttmp = datetime.datetime.strptime(tstr,datefmt)
                    ttmp = ttmp.replace(tzinfo=self.timezone)
                    header['Time of first measurement'] = ttmp
                elif('Time of last measurement' in l):
                    ind2 = l.rfind('  ')
                    tstr = l[ind2+2:].replace('\n','')
                    ttmp = datetime.datetime.strptime(tstr,datefmt)
                    ttmp = ttmp.replace(tzinfo=self.timezone)                    
                    header['Time of last measurement'] = ttmp
                elif('Transformation matrix' in l):
                    logger.debug('Transformation matrix found')
                    header['Transformation matrix'] = np.zeros((3,3))
                    # Get all three lines
                    tmp = []
                    tmp.append(l)
                    tmp.append(fhdr.readline())
                    tmp.append(fhdr.readline())                    
                    for i in range(3):
                        T_tmp = np.asarray(tmp[i].split()[-3:]).astype(np.float)
                        header['Transformation matrix'][i,:] = T_tmp

                    logger.debug(str(header['Transformation matrix']))

                elif('Magnetometer calibration matrix' in l):
                    logger.debug('Magnetometer calibration matrix found')
                    header['Magnetometer calibration matrix'] = np.zeros((3,3))
                    # Get all three lines
                    tmp = []
                    tmp.append(l)
                    tmp.append(fhdr.readline())
                    tmp.append(fhdr.readline())                    
                    for i in range(3):
                        T_tmp = np.asarray(tmp[i].split()[-3:]).astype(np.float)
                        header['Magnetometer calibration matrix'][i,:] = T_tmp

                    logger.debug(str(header['Magnetometer calibration matrix']))


                else:
                    pass

                if(header_field is not None):
                    if(header_field is 'sensors'):
                        l = l.replace('\n','').replace('\r','').strip() # remove return and trailing/leading blanks
                        lsp = re.sub("  +" , "\t", l).split('\t')
                        print('sensors',lsp)
                        field = lsp[1]
                        value = lsp[0]
                        header[header_field][field] = int(value)
                    elif(header_field is 'distance'):
                        l = l.replace('\n','').replace('\r','').strip() # remove return and trailing/leading blanks
                        lsp = re.sub("  +" , "\t", l).split('\t')
                        cell = lsp[0]                        
                        beam = lsp[1]
                        vertical = lsp[2]
                        print(cell,beam,vertical)
                        header[header_field]['cell'].append(int(cell))
                        header[header_field]['beam'].append(float(beam))
                        header[header_field]['vertical'].append(float(vertical))
                    else:
                        ind2 = l.rfind('  ')
                        data = l[ind2+2:].replace('\n','').replace('\r','')
                        field = l[:ind].replace('\n','').replace('\r','')
                        header[header_field][field] = data
                    
                
            #print(l.split())

        return header

    
    def process_rawdata(self):
        """ Processes .sen data stored in data['sen'] and the remaining rawdata
        """
        print('Creating time axis')
        t  = []
        tu = []        
        for i in range(np.shape(self.rawdata['sen'][:,0])[0]):
            month  = int(self.rawdata['sen'][i,0])
            day    = int(self.rawdata['sen'][i,1])
            year   = int(self.rawdata['sen'][i,2])
            hour   = int(self.rawdata['sen'][i,3])
            minute = int(self.rawdata['sen'][i,4])
            millis = self.rawdata['sen'][i,5]%1
            second = int(self.rawdata['sen'][i,5] - millis)
            micro  = int(millis*1000*1000)
            ttmp = datetime.datetime(year,month,day,hour,minute,second,micro,tzinfo=self.timezone)
            t.append(ttmp)
            tu.append(ttmp.timestamp())
            
        
        self.t = t # datetime time
        self.tu = tu # unix time
        self.data = {}
        for k in self.header['sensors'].keys():
            ind_key = self.header['sensors'][k] - 1
            self.data[k] = self.rawdata['sen'][:,ind_key]

        
        # Processing the remaining data
        # For a profiler (Aquadopp)
        aquadopp_keys = ['v1','v2','v3','a1','a2','a3','c1','c2','c3']
        for key in aquadopp_keys:
            if(key in self.rawdata.keys()):
               print('Getting data from: ' + key + ' (profiler)')
               self.data[key] = self.rawdata[key][:,2:]

        if('distance' in self.header.keys()):
            self.data['dis_beam'] = np.asarray(self.header['distance']['beam'])
            self.data['dis_vertical'] = np.asarray(self.header['distance']['vertical'])

        vector_keys = ['dat']
        for key in vector_keys:
            if(key in self.rawdata.keys()):
               print('Getting data from: ' + key + ' (Vector)')
               self.data[key] = self.rawdata[key][:,2:]


    def rot_vel(self,coord,updown=None,save=False):
        """ Rotates the velocities to different coordinate system
        Args:
            coord:
            updown:
            save:
        """
        logger.debug('trans_coord():')
        T = self.header['Transformation matrix'][:]
        if(updown == None):
            updown = self.header['updown']

        # flip axes if instrument is pointing downward
        # (so from here on, XYZ refers to a right-handed coordinate system
        # with z pointing upward)

        if updown:
            logger.debug('Downlooking, changing matrix')
            T[1,:] = -T[1,:];
            T[2,:] = -T[2,:];

        v1_rot = np.zeros(np.shape(self.data['v1']))
        v2_rot = np.zeros(np.shape(self.data['v2']))
        v3_rot = np.zeros(np.shape(self.data['v3']))
        try:
            v1_rep_rot = np.zeros(np.shape(self.data['v1_rep']))
            v2_rep_rot = np.zeros(np.shape(self.data['v2_rep']))
            v3_rep_rot = np.zeros(np.shape(self.data['v3_rep']))
            repaired = True
        except:
            repaired_false = True            
            pass
        
        print(np.shape(self.data['v1']))
        if(coord == 'XYZ'):
            if(self.header['Coordinate system'] == 'BEAM'):
                logger.debug('BEAM to XYZ')
                for i in range(np.shape(v1_rot)[0]):
                    for j in range(np.shape(v1_rot)[1]):
                        v1_rot[i,j] = T[0,0] * self.data['v1'][i,j] + T[0,1] * self.data['v2'][i,j] + T[0,2] * self.data['v3'][i,j]
                        v2_rot[i,j] = T[1,0] * self.data['v1'][i,j] + T[1,1] * self.data['v2'][i,j] + T[1,2] * self.data['v3'][i,j]
                        v3_rot[i,j] = T[2,0] * self.data['v1'][i,j] + T[2,1] * self.data['v2'][i,j] + T[2,2] * self.data['v3'][i,j]
                        if repaired:
                            v1_rep_rot[i,j] = T[0,0] * self.data['v1_rep'][i,j] + T[0,1] * self.data['v2_rep'][i,j] + T[0,2] * self.data['v3_rep'][i,j]
                            v2_rep_rot[i,j] = T[1,0] * self.data['v1_rep'][i,j] + T[1,1] * self.data['v2_rep'][i,j] + T[1,2] * self.data['v3_rep'][i,j]
                            v3_rep_rot[i,j] = T[2,0] * self.data['v1_rep'][i,j] + T[2,1] * self.data['v2_rep'][i,j] + T[2,2] * self.data['v3_rep'][i,j]                        


        if save:
            logger.debug('saving data in trans')
            try: # Check if self.trans is existing
                self.trans
            except:
                self.rotvel = {}
            if(coord == 'XYZ'):
                self.rotvel['u'] = v1_rot[:]
                self.rotvel['v'] = v2_rot[:]
                self.rotvel['w'] = v3_rot[:]
                if repaired:                
                    # Save the repaired data as well
                    self.rotvel['u_rep'] = v1_rep_rot[:]
                    self.rotvel['v_rep'] = v2_rep_rot[:]
                    self.rotvel['w_rep'] = v3_rep_rot[:]                                


        return [v1_rot,v2_rot,v3_rot]


        
    def repair_phase_shift(self,vel=None,threshold=None, save = False):
        """Tries to repair a phase shift in pulse coherent measurements. It
        assumes that the first measured value is correct.

        """
        
        if(vel == None):
            vel = self.data
            logger.debug('repairing native velocity')
            coordinate_system = self.header['Coordinate system']
            vel_all = [self.data['v1'],self.data['v2'],self.data['v3']]
        else:
            vel_all = [vel]
            
        vel_rep_all = []
        for vel_tmp in vel_all:
        # Compute threshold from header data
            if( coordinate_system == 'BEAM'):
                logger.debug('Using thresholds for beam coordinates')
                # Get the factor for the beam from the vertical velocity
                fac = np.linalg.inv(self.header['Transformation matrix'])[0,2]
                threshold_tmp = self.header['Vertical velocity range']# * fac
            else:
                logger.debug('Unknown threshold, returning')
                return

            vel_rep = np.zeros(np.shape(vel_tmp))
            for i in range(np.shape(vel_rep)[1]):
                vel_rep[:,i] = self.repair_phase_shift_vector(vel_tmp[:,i],threshold_tmp)
                
            vel_rep_all.append(vel_rep)


        print('hallo',vel is self.data)
        if((vel is self.data) and save):
            logger.debug("Saving data as data['v1_rep'] etc")
            self.data['v1_rep'] = vel_rep_all[0]
            self.data['v2_rep'] = vel_rep_all[1]
            self.data['v3_rep'] = vel_rep_all[2]


    def repair_phase_shift_vector(self,vel,threshold):
        """Tries to repair a phase shift in pulse coherent measurements. It
        assumes that the first measured value is correct.

        """

        vel_rep = vel.copy()

        vthresh = threshold - 0.3 * threshold
        for i in range(1,len(vel)):
            if((np.sign(vel_rep[i-1]) != np.sign(vel_rep[i])) and (abs(vel_rep[i-1]) > vthresh) and (abs(vel_rep[i]) > vthresh)):
               #print('Phase shift!')
               dv = threshold - abs(vel_rep[i])
               vel_rep[i] =  np.sign(vel_rep[i-1]) * (threshold + dv)

        return vel_rep    
