import serial
import time
import sys
import os
import datetime
import argparse
import logging
import glob

# Serial baud rates
baud = [300,600,1200,2400,4800,9600,19200,38400,57600,115200,460800,576000,921600]


logging.basicConfig(stream=sys.stderr, level=logging.INFO)
logger = logging.getLogger('nortek_time')
logger.setLevel(logging.DEBUG)

# Try to import Qt5
try:
    from PyQt5 import QtWidgets
    from PyQt5 import QtCore
    from PyQt5 import QtGui
except:
    print('Did not find qt5, only commnand line modes works...')
    pass



def serial_ports():
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system

        found here: http://stackoverflow.com/questions/12090503/listing-available-com-ports-with-python
    """
    FLAG_UNIXOID=True
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
        FLAG_UNIXOID=False
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            logger.debug("serial_ports(): Testing serial port " + str(port))
            if(FLAG_UNIXOID): # test if serial port has been locked
                logger.debug('Testing serial port ' + str(port))
                ret = test_serial_lock_file(port,brutal=True)
            else:
                ret = False
                
            if(ret == False):
                logger.debug("serial_ports(): Opening serial port " + str(port))
                s = serial.Serial(port)
                s.close()
                result.append(port)
        #except (OSError, serial.SerialException):
        except Exception as e:
            logger.debug('serial_ports(): Exception:' + str(e))
            pass

    return result


def test_serial_lock_file(port, brutal = False):
    """
    Creates or removes a lock file for a serial port in linux
    Args:
       port: Device string
       brutal: Remove lock file if a nonexisting PID was found or no PID at all within the file
    Return:
       True if port is already in use, False otherwise
    """
    devicename = port.split('/')[-1]
    filename = '/var/lock/LCK..'+devicename
    logger.debug('serial_lock_file(): filename:' + str(filename))
    try:
        flock = open(filename,'r')
        pid_str = flock.readline()
        flock.close()
        logger.debug('test_serial_lock_file(): PID:' + pid_str)
        PID_EXIST=None
        try:
            pid = int(pid_str)
            PID_EXIST = psutil.pid_exists(pid)
            pid_ex = ' does not exist.'
            if(PID_EXIST):
                pid_ex = ' exists.'
            logger.debug('Process with PID:' + pid_str[:-1] + pid_ex)
        except Exception as e:
            logger.debug('No valid PID value' + str(e))

            
        if(PID_EXIST == True):
            return True
        elif(PID_EXIST == False):
            if(brutal == False):
                return True
            else: # Lock file with "old" PID
                logger.debug('Removing lock file, as it has a not existing PID')
                os.remove(filename)
                return False
        elif(PID_EXIST == None): # No valid PID value
            if(brutal):
                logger.debug('Removing lock file, as it no valid PID')
                os.remove(filename)
                return False
            else:
                return True
    except Exception as e:
        print('serial_lock_file():' + str(e))
        return False

    
def serial_lock_file(port,remove=False):
    """
    Creates or removes a lock file for a serial port in linux
    """
    devicename = port.split('/')[-1]
    filename = '/var/lock/LCK..'+devicename
    logger.debug('serial_lock_file(): filename:' + str(filename))
        
    if(remove == False):
        try:
            flock = open(filename,'w')
            lockstr = str(os.getpid()) + '\n'
            logger.debug('Lockstr:' + lockstr)
            flock.write(lockstr)
            flock.close()
        except Exception as e:
            logger.debug('serial_lock_file():' + str(e))
    else:
        try:
            logger.debug('serial_lock_file(): removing filename:' + str(filename))
            flock = open(filename,'r')
            line = flock.readline()
            logger.debug('data:' + str(line))
            flock.close()
            os.remove(filename)
        except Exception as e:
            logger.debug('serial_lock_file():' + str(e))



def int2bcd(data):
    ints = []
    for decimal in data:
        ints.append( int(str(decimal), 16) )

    return bytes(ints)

def bcdDigits(chars):
    """ 
    bcd to ints
    """
    vals_all = []
    for char in chars:
        char = ord(char)
        vals = []
        for val in (char >> 4, char & 0xF):
            vals.append(val)
            if val == 0xF:
                return None

        vals_all.append(vals[1] + vals[0] * 10)
        
    return vals_all

def check_nortek(data):
    """ Checks in a binary data string if a Nortek like pattern is found
    """
    if(b'Confirm:' in data):
        print('Found Nortek device in sampling mode, doing nothing')
        return [False,None]
    if(b'Command mode' in data):
        print('Found Nortek device in command mode')
        # Lets get the device string
        ind1 = data.find(b'\n\r')
        ind2 = data.rfind(b'\x06\x06')
        #print(data,ind1,ind2)
        if( (ind1 > -1) and (ind2 > 0) ):
            dev_str = data[ind1:ind2-2].decode('utf-8')
        else:
            dev_str = 'unknown'
            
        return [True,dev_str]
    else:
        print('Found no Nortek device, doing nothing')
        return [False,None]


def nortek_set_time(ser,time_set):
    """ Send a get time command and returns the current time
    """
    print('Setting time')
    ser.reset_input_buffer()
    t2 = time_set + datetime.timedelta(0,2)
    
    tdata = [t2.minute,t2.second,t2.day,t2.hour,t2.year-2000,t2.month]
    bdata = int2bcd(tdata)
    com = b'SC' + bdata
    print(com)
    ser.write(com)
    time.sleep(2.0)
    data = ser.read(ser.in_waiting)
    ind1 = data.find(b'\x06\x06')
    if(ind1 > -1):
        print('Time set ...')
    else:
        print('Time not set ...')        
        

def nortek_get_time(ser):
    """ Send a get time command and returns the current time
    """
    ser.reset_input_buffer()
    t2 = datetime.datetime.utcnow()    
    ser.write(b'RC')
    t1 = datetime.datetime.utcnow()
    while( (ser.in_waiting <= 9) and ((t2 - t1) < datetime.timedelta(0,1)) ):
        t2 = datetime.datetime.utcnow()    

    data = ser.read(ser.in_waiting)
    ind1 = data.rfind(b'\x06\x06')
    #print(ind1)
    #print('data_all',data)
    #print('data:',data[:ind1])    
    if(ind1 > -1):
        #print(data[ind1-1:ind1])
        month  = bcdDigits([data[ind1-1:ind1]])[0]
        year   = bcdDigits([data[ind1-2:ind1-1]])[0] + 2000
        hour   = bcdDigits([data[ind1-3:ind1-2]])[0]
        day    = bcdDigits([data[ind1-4:ind1-3]])[0]
        second = bcdDigits([data[ind1-5:ind1-4]])[0]
        minute = bcdDigits([data[ind1-6:ind1-5]])[0]
        t = datetime.datetime(year,month,day,hour,minute,second)
        print(t2,t,(t2-t).total_seconds())
        return({'sys': t2, 'nortek':t,'sys_sent': t1})


    return None


def main():    
    desc = 'A simple tool to set the time of a Nortek device (Aquadopp, Vector), Peter Holtermann, typical baud rates: Aquadopp 9600, Vector 19200'

    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('com_port', help='Serial port for connection to device')
    parser.add_argument('baud',default=9600, help='baudrate')
    parser.add_argument('--set_time', '-s', action='store_true')

    parser.add_argument('--num_compare', '-n',default=3)
    args = parser.parse_args()

    PORT = args.com_port
    BAUD = args.baud
    FLAG_SET_TIME = args.set_time


    # Check if we have a Nortek device here
    print('Looking for device on port: ' + PORT)
    if True:
        #ser = serial.Serial(PORT,9600)  # open serial port (Aquadopp)
        ser = serial.Serial(PORT,BAUD)  # open serial port (Vector)
        print(ser.name)         # check which port was really used
        ser.reset_input_buffer()
        ser.write(b'@@@@@@')     # send a break
        time.sleep(.200) # wait at least 100 ms
        ser.write(b'K1W%!Q')     # write a break, second part
        time.sleep(2.0)
        data = ser.read(ser.in_waiting)
        print('data',data)
        nortek = check_nortek(data)
        if nortek[0]:
            print('Found a Nortek device: ' + nortek[1])
        else:
            print('Did not find a Nortek device in command mode, exiting ...')
            ser.close()
            sys.exit()




    # Setting time like this
    #set time yyyy-mm-dd HH:MM:SS
    if FLAG_SET_TIME:
        tset = datetime.datetime.utcnow()
        ts = tset.strftime('%Y-%m-%d %H:%M:%S') 
        print('Setting time to:' + ts)    
        nortek_set_time(ser,tset)


    t = datetime.datetime.utcnow()
    second_done = t.second
    n_compare = 3
    dt_sleep = 0.01
    n_test = int(1.0/dt_sleep)
    dt_all = []
    while True:
        if(n_compare == 0):
            break

        t = datetime.datetime.utcnow()
        sec = t.second

        if(t.microsecond > 970000): # A bit of time for progamming needed roughly 0.03 seconds
            n_compare -= 1
            nortek_get_time(ser)        


    ser.close()             # close port


# A qt gui for conveniently setting Nortek time
class guiMain(QtWidgets.QMainWindow):
    """ The main gui widget

    """
    def __init__(self):
        funcname = self.__class__.__name__ + '.___init__()'
        #self.__version__ = pymqdatastream.__version__
        # Add a logger object
        QtWidgets.QWidget.__init__(self)
        # Create the menu
        self.file_menu = QtWidgets.QMenu('&File',self)
        self.device_widgets = []
        #self.file_menu.addAction('&Settings',self.fileSettings,Qt.CTRL + Qt.Key_S)
        self.file_menu.addAction('&Quit',self._quit,QtCore.Qt.CTRL + QtCore.Qt.Key_Q)
        self.about_menu = QtWidgets.QMenu('&About',self)
        self.about_menu.addAction('&About',self._about)
        self.menuBar().addMenu(self.file_menu)
        self.menuBar().addMenu(self.about_menu)
        mainwidget = QtWidgets.QWidget(self)
        self.layout = QtWidgets.QGridLayout(mainwidget)        
        # Serial interface stuff
        self.combo_serial = QtWidgets.QComboBox(self)
        self.combo_baud   = QtWidgets.QComboBox(self)
        for b in baud:
            self.combo_baud.addItem(str(b))

        self.combo_baud.setCurrentIndex(5)
        
        self.close_bu = QtWidgets.QPushButton('Close')
        #self.close_bu.clicked.connect(w.close)
        self.open_bu = QtWidgets.QPushButton('Open')
        self.open_bu.clicked.connect(self.serial_open_bu)
        self.get_time_bu = QtWidgets.QPushButton('Get time')
        self.get_time_bu.clicked.connect(self.get_time)
        self.set_time_bu = QtWidgets.QPushButton('Set time')
        self.text = QtWidgets.QPlainTextEdit()
        self.text.setReadOnly(True)
        self.text.textChanged.connect(self.text_changed)
        self.input_name = QtWidgets.QLineEdit(self)
        self.file_bu = QtWidgets.QPushButton('File')
        self.file_bu.clicked.connect(self.get_file)
        self.log_check = QtWidgets.QCheckBox("Logging")
        self.log_check.stateChanged.connect(self.log_file)
        self.test_ports()


        self.layout.addWidget(self.combo_serial,0,0)
        self.layout.addWidget(self.combo_baud,0,1)
        self.layout.addWidget(self.open_bu,0,2)
        self.layout.addWidget(self.get_time_bu,1,2)
        self.layout.addWidget(self.set_time_bu,2,2)
        self.layout.addWidget(self.text,3,0,1,3)
        self.layout.addWidget(self.log_check,4,0)
        self.layout.addWidget(self.input_name,4,1)
        self.layout.addWidget(self.file_bu,4,2)

        # Focus 
        mainwidget.setFocus()
        self.setCentralWidget(mainwidget)

    def text_changed(self):
        print('Changed')

    def log_file(self):
        fname = self.input_name.text()        
        if self.log_check.isChecked() == True:
            try:
                print('Opening')
                self.logfile = open(fname,'w')
            except Exception as e:
                self.text.appendPlainText('Could not open: ' + str(fname) + ' ' + str(e))
                self.log_check.setChecked(False)
        else:
            self.text.appendPlainText('Closing : ' + str(fname))
            self.logfile.close()

    def get_file(self):
        fname = QtWidgets.QFileDialog.getSaveFileName(self)
        if(len(fname[0]) > 0):
            print(fname)
            self.input_name.setText(fname[0])

            
    def get_time(self):
        t = nortek_get_time(self.ser)
        print(t)
        if(t is not None):
            dt = (t['sys'] - t['nortek'])
            dts = (t['sys_sent'] - t['nortek'])
            time_str = 'PC: ' + str(t['sys']) + ' Nortek: '  + str(t['nortek'])
            time_str += ', difference PC-Nortek ' + str( dt.total_seconds()) + ' s'
            time_str += ', difference PC-Nortek ' + str( dts.total_seconds()) + ' s'
            self.text.appendPlainText(time_str)
            if self.log_check.isChecked():
                self.logfile.write(time_str + '\n')
                self.logfile.flush()
            

    def serial_open_bu(self):
        PORT = self.combo_serial.currentText()
        BAUD = int(self.combo_baud.currentText())
        ser = serial.Serial(PORT,BAUD)  # open serial port
        self.ser = ser
        print('Opened port: ' + ser.name)         # check which port was really used
        ser.reset_input_buffer()
        ser.write(b'@@@@@@')     # send a break
        time.sleep(.200) # wait at least 100 ms
        ser.write(b'K1W%!Q')     # write a break, second part
        time.sleep(2.0)
        data = ser.read(ser.in_waiting)
        print('data',data)
        nortek = check_nortek(data)
        if nortek[0]:
            dstr = 'Found a Nortek device: ' + nortek[1]
            self.text.appendPlainText(dstr)
            if self.log_check.isChecked():
                self.logfile.write(dstr + '\n')
                self.logfile.flush()                
        else:
            dstr = 'Did not find a Nortek device in command mode ...'
            self.text.appendPlainText(dstr)
            if self.log_check.isChecked():
                self.logfile.write(dstr + '\n')
                self.logfile.flush()                
            ser.close()
        

    def test_ports(self):
        """ Searching for serial ports
        """
        ports = serial_ports()
        ports_good = ports
        self.combo_serial.clear()
        for port in ports_good:
            self.combo_serial.addItem(str(port))        


    def _quit(self):
        funcname = '_quit()'        
        logger.debug(funcname)
        self.close()

        
    def _about(self):
        about_str = '\n'        
        about_str += '\n This is pynortek_time_gui: '
        about_str += '\n Written by Peter Holtermann \n'
        about_str += '\n peter.holtermann@io-warnemuende.de \n'
        about_str += '\n under the GPL v3 license \n'                
        self._about_label = QtWidgets.QLabel(about_str)
        self._about_label.show()            



def gui():
    app = QtWidgets.QApplication(sys.argv)
    myapp = guiMain()
    myapp.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
