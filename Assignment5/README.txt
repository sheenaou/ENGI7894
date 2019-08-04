##################################################
#	README for mergeSort.py
##################################################

Step 1:
	- Install Python3.x
	- The latest version can be found here https://www.python.org/downloads/release/python-374/
	- Ensure your path environment variable is updated, a system restart may be necessary
	
Step 2:
	- Install Microsoft MPI
	- The latest version can be found here https://www.microsoft.com/en-us/download/details.aspx?id=57467
	- Ensure your path environment variable is updated, a system restart may be necessary
	
Step 3:
	- Install mpi4py via python's package manager pip
	- pip install mpi4py
	
Step 4:
	- Navigate to the directory containing mergeSort.py
	- Execute the following command
		- mpiexec -n 8 python mergeSort.py
