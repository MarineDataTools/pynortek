import numpy as np
import logging
import sys
import pkg_resources
import pytz
import datetime
import os
import re
from numpy import cos,sin


whd_format = """1   Month                            (1-12)
 2   Day                              (1-31)
 3   Year
 4   Hour                             (0-23)
 5   Minute                           (0-59)
 6   Second                           (0-59)
 7   Burst counter
 8   No of wave data records
 9   Cell position                    (m)
10   Battery voltage                  (V)
11   Soundspeed                       (m/s)
12   Heading                          (degrees)
13   Pitch                            (degrees)
14   Roll                             (degrees)
15   Minimum pressure                 (dbar)
16   Maximum pressure                 (dbar)
17   Temperature                      (degrees C)
18   CellSize                         (m)
19   Noise amplitude beam 1           (counts)
20   Noise amplitude beam 2           (counts)
21   Noise amplitude beam 3           (counts)
22   Noise amplitude beam 4           (counts)
23   AST window start                 (m)
24   AST window size                  (m)
25   AST window offset                (m)"""

# Get the version
version_file = pkg_resources.resource_filename('pynortek','VERSION')

# Setup logging module
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
logger = logging.getLogger('pynortek')

def xyz2enu(u,v,w,head,pitch,roll,inverse=False):
    """
    Transforms velocities in XYZ coordinates to ENU, or vice versa if
    inverse=True. Transformation is done according to the Nortek
    convention

    """
    # convert to radians
    hh = np.pi*(head-90)/180
    pp = np.pi*pitch/180
    rr = np.pi*roll/180

    ut = np.zeros(np.shape(u))
    vt = np.zeros(np.shape(u))
    wt = np.zeros(np.shape(u))    

    for i in range(len(head)):
        # generate heading matrix
        H = np.matrix([[cos(hh[i]), sin(hh[i]), 0],[-sin(hh[i]), cos(hh[i]), 0],[0, 0, 1]])
        # generate combined pitch and roll matrix
        P = [[cos(pp[i]), -sin(pp[i])*sin(rr[i]), -cos(rr[i])*sin(pp[i])],
             [0,           cos(rr[i]),                       -sin(rr[i])],
             [sin(pp[i]),  sin(rr[i])*cos(pp[i]),  cos(pp[i])*cos(rr[i])]]

        R = H*P
        #print(R)
        if(inverse):
            R = np.inv(R)

        # do transformation
        ut[i]  = R[0,0]*u[i] + R[0,1]*v[i] + R[0,2]*w[i];
        vt[i]  = R[1,0]*u[i] + R[1,1]*v[i] + R[1,2]*w[i];
        wt[i]  = R[2,0]*u[i] + R[2,1]*v[i] + R[2,2]*w[i];

    
    return [ut,vt,wt]

raw_data_files = ['.prf','.vec','.wpa','.wpr'] # Names of raw binary data files
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
        self.data = {}
        print(self.deployment)
        print(self.fpath)        
        filename_hdr = filename + '.hdr'
        logger.debug('Trying to open header file: ' + filename_hdr)
        try:
            fhdr = open(filename_hdr)
        except Exception as e:
            raise ValueError('Could not open header file, exiting\n{}'.format(filename_hdr))
            #logger.warning('Could not open header file, exiting')
            #return

        header = self.parse_header(fhdr)
        self.header = header
        #print(header)
        logger.info('Loading files')
        flag_wave = False
        for fread in header['files']:
            logger.info('File:{}'.format(fread))
            IS_RAW = False
            for rawname in raw_data_files:
                if(rawname in fread.lower()):
                    IS_RAW=True

            if(IS_RAW == False):
                logger.info('Loading:{}'.format(fread))
                suffix = fread.split('.')[-1]
                fname_tmp = os.path.join(self.fpath,fread)
                #print(fname_tmp)
                # Read the rawdata
                if fname_tmp.lower().endswith('.whd'):  # Loading wave header data
                    logger.info('Reading wave header data')
                    #self.read_rawdata_wave_header(fname_tmp)
                    try:
                        data_tmp = np.loadtxt(fname_tmp)
                        self.rawdata[suffix] = data_tmp
                        flag_wave = True                        
                    except:
                        self.rawdata[suffix] = None
                elif fname_tmp.lower().endswith('.wad'):  # Loading wave data
                    logger.info('Reading wave data')
                    flag_wave = True
                    try:
                        data_tmp = np.loadtxt(fname_tmp)
                        self.rawdata[suffix] = data_tmp
                    except:
                        self.rawdata[suffix] = None
                else:  # Saving rawdata into dictionary
                    logger.info('Reading velocity data')                    
                    try:
                        data_tmp = np.loadtxt(fname_tmp)
                        self.rawdata[suffix] = data_tmp
                    except:
                        self.rawdata[suffix] = None

        if flag_wave:
            self.process_rawdata_wave()
        # Process the raw data just loaded
        self.process_rawdata()
        
    def parse_header(self,fhdr):
        """ Parses a nortek header file
        """
        header = {}
        header['Burst sampling'] = False
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
                    logger.debug('Found a sensor file (.sen), looking for key entries')
                    header_field = 'sensors'
                    header[header_field] = {}
                # If we have a wave header file, check position of fields
                if('.whd' in l[-7:]):
                    logger.debug('Found a wave header file (.whd), looking for key entries')
                    header_field = 'wave_header'
                    header[header_field] = {}
                # If we have a wave header file, check position of fields
                if('.wad' in l[-7:]):
                    logger.debug('Found a wave data file (.wad), looking for key entries')
                    header_field = 'wave_data'
                    header[header_field] = {}                                        

            # Transducer distance (beam coordinates)
            if(('Beam' in l) and ('Vertical' in l)):
                print('Transducer distance (beam coordinates)')
                header_field = 'distance'
                header[header_field] = {'cell':[],'beam':[],'vertical':[]}
                continue

            if 'Current profile cell center distance from head' in l:
                print('Transducer distance (XYZ or ENU coordinates)')
                header_field = 'distance'
                header[header_field] = {'cell': [], 'vertical': []}
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
                elif ('Burst sampling' in l):
                    logger.debug('Burst sampling entry found')
                    if 'ON' in l:
                        header['Burst sampling'] = True
                    else:
                        header['Burst sampling'] = False
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
                        T_tmp = np.asarray(tmp[i].split()[-3:]).astype(float)
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
                        T_tmp = np.asarray(tmp[i].split()[-3:]).astype(float)
                        header['Magnetometer calibration matrix'][i,:] = T_tmp

                    logger.debug(str(header['Magnetometer calibration matrix']))


                else:
                    pass

                # Check for the header field an look for the entries that are mapping the matrix structure to individual data/sensors
                if(header_field is not None):
                    if(header_field == 'sensors'):
                        l = l.replace('\n','').replace('\r','').strip() # remove return and trailing/leading blanks
                        lsp = re.sub("  +" , "\t", l).split('\t')
                        logger.debug('.sen sensors entry:{}'.format(lsp))
                        field = lsp[1]
                        value = lsp[0]
                        header[header_field][field] = int(value)
                    elif(header_field == 'wave_header'):
                        l = l.replace('\n','').replace('\r','').strip()
                        lsp = re.sub("  +" , "\t", l).split('\t')
                        logger.debug('.whd entry:{}'.format(lsp))
                        field = lsp[1]
                        value = lsp[0]
                        header[header_field][field] = int(value)
                    elif(header_field == 'wave_data'):
                        l = l.replace('\n','').replace('\r','').strip()
                        lsp = re.sub("  +" , "\t", l).split('\t')
                        logger.debug('.wad entry:{}'.format(lsp))
                        field = lsp[1]
                        value = lsp[0]
                        header[header_field][field] = int(value)                                                
                    elif(header_field == 'distance'):
                        l = l.replace('\n','').replace('\r','').strip()
                        lsp = re.sub("  +" , "\t", l).split('\t')
                        if len(lsp)>2:
                            cell = lsp[0]
                            beam = lsp[1]
                            vertical = lsp[2]
                            print('Distance beam',cell,beam,vertical)
                            header[header_field]['cell'].append(int(cell))
                            header[header_field]['beam'].append(float(beam))
                            header[header_field]['vertical'].append(float(vertical))
                        else:
                            cell = lsp[0]
                            vertical = lsp[1]
                            print('Distance xyz',cell, vertical)
                            header[header_field]['cell'].append(int(cell))
                            header[header_field]['vertical'].append(float(vertical))

                    else:
                        ind2 = l.rfind('  ')
                        data = l[ind2+2:].replace('\n','').replace('\r','')
                        field = l[:ind].replace('\n','').replace('\r','')
                        header[header_field][field] = data
                    
                
            #print(l.split())

        return header

    def read_rawdata_wave_header(self,fname):
        """ Processes rawdata from a wave measurement

        """
        try:
            self.data_wave
        except:
            self.data_wave = {}


        if fname.lower().endswith('.wad'):
            data1 = []
            f = open(fname)
            for i,l in enumerate(f.readlines()):
                # There is always a two line combination
                if i%2==0:
                    larray = np.fromstring(l, sep=' ')
                    #print('larray',larray,len(larray))
                    data1.append(larray)

            data1 = np.asarray(data1)
            self.data_wave['stg'] = data1            
        elif fname.lower().endswith('.stg'):  # Legacy, remove soon
            data1 = []
            f = open(fname)
            for i,l in enumerate(f.readlines()):
                # There is always a two line combination
                if i%2==0:
                    larray = np.fromstring(l, sep=' ')
                    #print('larray',larray,len(larray))
                    data1.append(larray)

            data1 = np.asarray(data1)
            self.data_wave['stg'] = data1
        elif fname.lower().endswith('.whd'): # Wave header file
            self.__data_wave_whd_entries = {}
            for lheader in whd_format.split('\n'):
                #lheader_parse = np.fromstring(lheader, sep=' ')
                lheader_parse = ' '.join(lheader.split('  '))
                lsp = lheader.split('  ')
                print('lheader',lheader,lsp)
                ind = int(lsp[0])
                datakey = str(lsp[1]).strip()
                if ind >= 7:
                    print('Datakey',datakey,ind)
                    self.__data_wave_whd_entries[datakey] = ind - 1

            t = []
            tu = []
            f = open(fname)
            self.data_wave['t'] = []
            self.data_wave['tu'] = []
            self.data_wave['Burst counter'] = []
            self.data_wave['No of wave data records'] =[]
            self.data_wave['Cell position'] = []
            self.data_wave['Battery voltage'] = []
            for i, l in enumerate(f.readlines()):
                larray = np.fromstring(l, sep=' ')
                month = int(larray[0])
                day = int(larray[1])
                year = int(larray[2])
                hour = int(larray[3])
                minute = int(larray[4])
                #millis = self.rawdata['sen'][i, 5] % 1
                second = int(larray[5])
                #micro = int(millis * 1000 * 1000)
                micro = 0
                ttmp = datetime.datetime(year, month, day, hour, minute, second, micro, tzinfo=self.timezone)
                t.append(ttmp)
                tu.append(ttmp.timestamp())
                self.data_wave['t'].append(ttmp)
                self.data_wave['tu'].append(ttmp.timestamp())
                for dataentry in self.__data_wave_whd_entries.keys():
                    print('Dataentry',dataentry)
                    i_dataentry = self.__data_wave_whd_entries[dataentry]
                    try:
                        self.data_wave[dataentry]
                    except:
                        self.data_wave[dataentry] = []
                    self.data_wave[dataentry].append(float(larray[i_dataentry]))
                #self.data_wave['No of wave data records'].append(int(larray[7]))
                #self.data_wave['Cell position'].append(float(larray[8]))
                #self.data_wave['Battery voltage'].append(float(larray[9]))

    def process_rawdata_wave(self):
        """ Processes .wad data stored in data['wad'] and the remaining rawdata, mainly adding a proper time stamp and similar tasks
        """
        logger.debug('Creating time axis for wave data')
        freqstr = self.header['Head configuration']['Head frequency']
        if freqstr.startswith('1000'):
            logger.debug('1000 kHz: Setting Delta t for burst to 0.5s (0.25 for AST)')
            dt = datetime.timedelta(seconds=0.5)
            dt_AST = datetime.timedelta(seconds=0.25)
        else:
            logger.debug('<1000 kHz: Setting Delta t for burst to 1s (0.5 for AST)')
            dt = datetime.timedelta(seconds=1.0)
            dt_AST = datetime.timedelta(seconds=0.5)

        try:
            self.data_wave
        except:
            self.data_wave = {}

        try:
            self.data_wave_burst
        except:
            self.data_wave_burst = {}                        

        t  = []
        tu = []
        burst_tmp = []
        for i in range(np.shape(self.rawdata['whd'][:,0])[0]):
            burst = int(self.rawdata['whd'][i,6])
            month  = int(self.rawdata['whd'][i,0])
            day    = int(self.rawdata['whd'][i,1])
            year   = int(self.rawdata['whd'][i,2])
            hour   = int(self.rawdata['whd'][i,3])
            minute = int(self.rawdata['whd'][i,4])
            millis = self.rawdata['whd'][i,5]%1
            second = int(self.rawdata['whd'][i,5] - millis)
            micro  = int(millis*1000*1000)
            ttmp = datetime.datetime(year,month,day,hour,minute,second,micro,tzinfo=self.timezone)
            t.append(ttmp)
            tu.append(ttmp.timestamp())
            burst_tmp.append(burst)

        # Map burst data
        logger.debug('Mapping burst data (.whd)')
        self.data_wave['t'] = t
        self.data_wave['tu'] = tu
        for k in self.header['wave_header'].keys():
            ind_key = self.header['wave_header'][k] - 1
            self.data_wave[k] = self.rawdata['whd'][:,ind_key]


        # Calculate time for ensemble members of burst
        logger.debug('Mapping ensemble members of burst data (.wad)')        
        for k in self.header['wave_data'].keys():
            ind_key = self.header['wave_data'][k] - 1
            self.data_wave_burst[k] = self.rawdata['wad'][:,ind_key]

        logger.debug('Creating time axis for burst members')
        t_burst  = []
        tu_burst = []
        t_AST  = []
        tu_AST  = []
        burst_AST  = []        
        AST  = []                
        for i in range(np.shape(self.rawdata['wad'][:,0])[0]):
            burst = int(self.rawdata['wad'][i,0])
            ensemble = int(self.rawdata['wad'][i,1])
            #print('burst',burst,'ensemble',ensemble)
            #print(burst_tmp)
            iburst = burst_tmp.index(burst)
            #print('iburst',iburst)
            #t_iburst = t[iburst]            
            t_ensemble = t[iburst] + (ensemble - 1 ) * dt
            t_burst.append(t_ensemble)
            tu_burst.append(t_ensemble.timestamp())            
            # AST is sampled with double frequency
            AST1 = float(self.rawdata['wad'][i,3])
            AST2 = float(self.rawdata['wad'][i,4])
            AST.append(AST1)
            AST.append(AST2)
            t_AST1 = t[iburst] + (ensemble - 1 ) * dt - dt_AST
            t_AST2 = t[iburst] + (ensemble - 1 ) * dt
            t_AST.append(t_AST1)
            t_AST.append(t_AST2)
            burst_AST.append(burst)
            burst_AST.append(burst)
            tu_AST.append(t_AST1.timestamp())
            tu_AST.append(t_AST2.timestamp())




        self.data_wave_burst['t'] = t_burst
        self.data_wave_burst['t_AST'] = t_AST
        self.data_wave_burst['tu'] = tu_burst
        self.data_wave_burst['tu_AST'] = tu_AST        
        self.data_wave_burst['AST'] = AST
        self.data_wave_burst['burst_AST'] = burst_AST        
            
        


    def process_rawdata(self):
        """ Processes .sen data stored in data['sen'] and the remaining rawdata
        """
        logger.debug('Creating time axis')
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

        for k in self.header['sensors'].keys():
            ind_key = self.header['sensors'][k] - 1
            self.data[k] = self.rawdata['sen'][:,ind_key]

        
        # Processing the remaining data
        try:
            burst_sampling = self.header['Burst sampling']
        except:
            burst_sampling = False

        logger.info('Burst sampling {}'.format(burst_sampling))
        # For a profiler (Aquadopp)
        aquadopp_keys = ['v1','v2','v3','a1','a2','a3','c1','c2','c3']
        for key in aquadopp_keys:
            if(key in self.rawdata.keys()):
               logger.info('Getting data from: ' + key + ' (profiler)')
               if burst_sampling:
                   self.data[key] = self.rawdata[key][:,2:]
               else:
                   self.data[key] = self.rawdata[key][:,:]

        if('distance' in self.header.keys()):
            try:
                self.data['dis_beam'] = np.asarray(self.header['distance']['beam'])
            except:
                pass
            self.data['dis_vertical'] = np.asarray(self.header['distance']['vertical'])

        vector_keys = ['dat']
        for key in vector_keys:
            if(key in self.rawdata.keys()):
               logger.info('Getting data from: ' + key + ' (Vector)')
               if burst_sampling:
                   self.data[key] = self.rawdata[key][:,2:]
               else:
                   self.data[key] = self.rawdata[key][:,:]


    def rot_vel(self,coord,updown=None,save=True):
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
            repaired = False
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

    def avg(self,burst=True,navg=10):
        if burst:
            self.burst_avg()
        else:
            self.navg(navg)

    def navg(self,navg=10):
        """
        Averages n samples to one value
        """
        funcname = __name__ + '.navg_avg():'
        try:
            self.rotvel
            flag_rotvel = True
        except:
            flag_rotvel = False
        nsamples = len(self.t)
        print('Nsamples',nsamples)
        burstavg = {}
        burstavg_rotvel = {}
        varavg = ['v1','v2','v3','a1','a2','a3','c1','c2','c3','Pressure']
        logger.info(funcname + ' Will average over {:d} samples'.format(navg))
        #burstavg['nburst'] = []
        burstavg['t'] = []
        for count,i in enumerate(range(0,nsamples,navg)):
            iup = min([i+navg,nsamples])
            ind = range(i,iup)
            t0 = self.t[ind[0]]
            t1 = self.t[ind[-1]]
            dt = t1 - t0
            tb = t0 + dt / 2
            #print(t0,dt)
            burstavg['t'].append(tb)
            #burstavg['nburst'].append(sum(ind))
            logger.debug('Averaging {:d} samples of burst {:d} between {:s} and {:s}'.format(sum(ind),i, str(t0), str(t1)))
            for ivar, v in enumerate(varavg):
                if v in self.data.keys():
                    if count == 0:
                        burstavg[v] = []

                    # This holds for vectors
                    if len(np.shape(self.data[v])) == 2:
                        dataavg = self.data[v][ind,:].mean(0)
                    elif len(np.shape(self.data[v])) == 1:
                        dataavg = self.data[v][ind].mean(0)

                    burstavg[v].append(dataavg)
                else:
                    logger.info('Variable {} not found'.format(v))

            if flag_rotvel:
                rotvel_vars = ['u', 'v', 'w']
                for ivar, v in enumerate(rotvel_vars):
                    if count == 0:
                        burstavg_rotvel[v] = []

                    dataavg = self.rotvel[v][ind, :].mean(0)
                    burstavg_rotvel[v].append(dataavg)


                #dataavg = self.data[v][ind, :].mean(0)

        # Make an array out of the lists
        burstavg['t'] = np.asarray(burstavg['t'])
        #burstavg['nburst'] = np.asarray(burstavg['nburst'])
        for ivar, v in enumerate(varavg):
            if v in self.data.keys():
                burstavg[v] = np.asarray(burstavg[v])

        self.data_navg = burstavg

        if flag_rotvel:
            for ivar, v in enumerate(rotvel_vars):
                burstavg_rotvel[v] = np.asarray(burstavg_rotvel[v])
                self.rotvel_burstavg = burstavg_rotvel            

    def burst_avg(self, c_threshold=0):
        """
        Averages the bursts
        """
        funcname = __name__ + '.burst_avg():'
        nbursts = int(self.data['Burst counter'].max())
        sburst = int(self.data['Burst counter'].min())
        burstavg = {}
        burstavg_rotvel = {}
        varavg = ['v1','v2','v3','a1','a2','a3','c1','c2','c3','Pressure']
        logger.info(funcname + ' Will average {:d} bursts'.format(nbursts))
        burstavg['nburst'] = []
        burstavg['t'] = []
        for count,i in enumerate(range(sburst,nbursts)):
            ind = self.data['Burst counter'] == i
            indi = np.where(ind)[0]
            t0 = self.t[indi[0]]
            t1 = self.t[indi[-1]]
            dt = t1 - t0
            tb = t0 + dt / 2
            #print(t0,dt)
            burstavg['t'].append(tb)
            burstavg['nburst'].append(sum(ind))
            logger.debug('Averaging {:d} samples of burst {:d} between {:s} and {:s}'.format(sum(ind),i, str(t0), str(t1)))
            for ivar, v in enumerate(varavg):
                if count == 0:
                    burstavg[v] = []

                # This holds for vectors
                if len(np.shape(self.data[v])) == 2:
                    datatmp = self.data[v][ind,:]
                    if c_threshold > 0:
                        c1tmp = self.data['c1'][ind,:]
                        c2tmp = self.data['c2'][ind,:]
                        c3tmp = self.data['c3'][ind,:]                        
                elif len(np.shape(self.data[v])) == 1:
                    datatmp = self.data[v][ind]
                    if c_threshold > 0:
                        c1tmp = self.data['c1'][ind]
                        c2tmp = self.data['c2'][ind]
                        c3tmp = self.data['c3'][ind]

                if c_threshold > 0 and (v != 'Pressure'):                
                    indbad = (c1tmp <= c_threshold) & (c2tmp <= c_threshold) & (c3tmp <= c_threshold)
                    #print(np.shape(indbad),np.shape(datatmp),np.shape(c1tmp),np.shape(c2tmp),np.shape(c3tmp))
                    datatmp[indbad] = np.NaN
                    dataavg = np.nanmean(datatmp,0)
                else:
                    dataavg = datatmp.mean(0)
                    
                burstavg[v].append(dataavg)


            if True:
                rotvel_vars = ['u', 'v', 'w']
                for ivar, v in enumerate(rotvel_vars):
                    if count == 0:
                        burstavg_rotvel[v] = []

                    datatmp = self.rotvel[v][ind, :]
                    if c_threshold > 0:
                        c1tmp = self.data['c1'][ind,:]
                        c2tmp = self.data['c2'][ind,:]
                        c3tmp = self.data['c3'][ind,:]
                        indbad = (c1tmp <= c_threshold) & (c2tmp <= c_threshold) & (c3tmp <= c_threshold)
                        #print(np.shape(indbad),np.shape(datatmp),np.shape(c1tmp),np.shape(c2tmp),np.shape(c3tmp))
                        datatmp[indbad] = np.NaN
                        dataavg = np.nanmean(datatmp,0)
                        #print('dataavg')
                    else:
                        dataavg = datatmp.mean(0)                        
                    
                    burstavg_rotvel[v].append(dataavg)


                #dataavg = self.data[v][ind, :].mean(0)

        # Make an array out of the lists
        burstavg['t'] = np.asarray(burstavg['t'])
        burstavg['nburst'] = np.asarray(burstavg['nburst'])
        for ivar, v in enumerate(varavg):
            burstavg[v] = np.asarray(burstavg[v])

        self.data_burstavg = burstavg

        if True:
            for ivar, v in enumerate(rotvel_vars):
                burstavg_rotvel[v] = np.asarray(burstavg_rotvel[v])
                self.rotvel_burstavg = burstavg_rotvel


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
