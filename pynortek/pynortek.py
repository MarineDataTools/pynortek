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
logging.basicConfig(stream=sys.stderr, level=logging.WARNING)
logger = logging.getLogger('pynortek')

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

            if(('Beam' in l) and ('Vertical' in l)):
                print('Transducer distance')
                header_field = 'distance'
                header[header_field] = {'cell':[],'beam':[],'vertical':[]}
                continue
                    
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

                    
            ind = l.find('  ')
            if(ind >= 0):
                if('Number of measurements' in l):
                    header['Number of measurements'] = int(l.split()[-1])
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
            micro  = int(millis*1000)
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


        
        
        
        
