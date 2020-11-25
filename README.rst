
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
size. 

.. _netCDF: https://www.unidata.ucar.edu/software/netcdf/

  
EXAMPLES 
--------

The main function is pynortek_vec2nc, arguments are the input file and the netcdf filename, i.e.:

.. code:: bash
	  
	  pynortek_vec2nc advfile.vec advfile.nc

Which results in a netcdf file called advfile.nc. One can also merge several split datafiles into one netcdf file,

.. code:: bash
	  
	  pynortek_vec2nc advfile1.vec advfile2.vec advfile3.vec advfile.nc




	  



