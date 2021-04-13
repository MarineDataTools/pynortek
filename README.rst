
Python toolbox to read and process data files recorded with acoustic current profilers from Nortek_, e.g. Vector ADV, Aquadopp

.. _Nortek: http://www.nortek-as.com/


Install
-------

The package was developed using python 3.5+, it might work with
earlier versions, but its not supported. 

User
____

Install as a user

.. code:: bash
	  
   python setup.py install --user

Uninstall as a user
   
.. code:: bash
	  
pip uninstall pynortek



Developer
_________

Install as a developer

.. code:: bash
	  
   python setup.py develop --user

Uninstall as a user
   
.. code:: bash
	  
pip uninstall pynortek


FEATURES
--------

Pynorteks main functionality are the binary reading of ADV Vector
(.vec) files and storing in the netCDF_ format, which is designed to
handle huge datasets. The original Nortek software converts the data
into text files, which become unhandy when the dataset increases in
size. The main feature during the conversion process is to add a
timestamp to all velocity measurements. The raw binary velocity data
does not include time stamps. To do so packages with timestamp (sys,
velocity header) in the vicinity of the velocity package have to be
found and, depending on the samplingrate, timestamp of the velocity
package are calculated.

.. _netCDF: https://www.unidata.ucar.edu/software/netcdf/

  
EXAMPLES 
--------

The main function is pynortek_vec2nc, arguments are the input file and the netcdf filename, i.e.:

.. code:: bash
	  
	  pynortek_vec2nc advfile.vec advfile.nc

Which results in a netcdf file called advfile.nc. One can also merge several split datafiles into one netcdf file,

.. code:: bash
	  
	  pynortek_vec2nc advfile1.vec advfile2.vec advfile3.vec advfile.nc
	  
The conversion can also be done within a python script.

.. code:: python
	  
	  import pynortek
	  pynortek.bin2nc(advfile.vec,advfile.nc)



Plotting netCDF4 files
----------------------

Assuming that pynortek_vec2nc created a netCDF file called
advfile.nc. The following small program plots the first velocity
component.

.. code:: python
	  
	  import pylab as pl
	  import netCDF4
	  import matplotlib.dates as mdates

	  nc = netCDF4.Dataset('advfile.nc')
	  tsys = nc.groups['sys'].variables['time'][:] # Unix time
	  tvel = nc.groups['vel'].variables['time'][:] # Unix time
	  v1 = nc.groups['vel'].variables['v1'][:] # The v1 velocity
	  burst = nc.groups['vel'].variables['burst'][:] # The burst sample

	  pl.figure(1)
	  pl.clf()
	  pl.subplot(2,1,1)
	  pl.plot(tvel,v1)
	  pl.xlabel('unix time [s]')
	  pl.ylabel('u [m/s]')

	  pl.subplot(2,1,2)
	  for i in range(max(burst)):
	  ind = burst == i
	  pl.plot_date(pl.epoch2num(tvel[ind]),v1[ind],'-')

	  pl.xlabel('Date')
	  pl.ylabel('u [m/s]')    
	  pl.draw()
	  pl.show()




	  



