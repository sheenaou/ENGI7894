from mpi4py import MPI
from random import randint, uniform
from math import ceil
from time import time

comm = MPI.COMM_WORLD
node = comm.Get_rank()

if node == 0:
    # Generate data used for simulation
    data = [randint(0,100) for i in range(4096)]  # Simulation for integers
    # data = [uniform(0,100) for i in range(8192)]    # Simulation for real numbers
    print("NODE DATA:\n", data)
    start_time = time()

    # Send data to right child
    index = ceil(len(data)/2) # Get midpoint of list
    data_set = data[:index]
    comm.send(data[index:], 4)

    # Send data to right child
    index2 = ceil(len(data_set) / 2)
    data_set2 = data_set[:index2]
    comm.send(data_set[index2:], 2)

    # Send data to right child
    index3 = ceil(len(data_set2)/2)
    data_set3 = data_set2[:index3]
    comm.send(data_set2[index3:], 1)

    # Sort own data
    data_set3.sort()

    # Get right child data and sort
    sorted_rec = comm.recv(source = 1)
    sorted01 = data_set3 + sorted_rec
    sorted01.sort()

    # Get right child data and sort
    sorted_rec = comm.recv(source = 2)
    sorted0123 = sorted01 + sorted_rec
    sorted0123.sort()

    # Get right child data and sort
    sorted_rec = comm.recv(source = 4)
    final = sorted0123 + sorted_rec
    final.sort()

    # End metrics
    end_time = time()
    total_time = end_time - start_time
    print("Started time: {} \nFinished time: {} \nTime Elapsed: {}".format(start_time, end_time, total_time))

elif node == 1:
    info = comm.recv(source=0)  # Get data from parent
    info.sort()                 # Sort data
    comm.send(info, 0)          # Send data to parent node

elif node == 2:
    # Get data from parent node
    info = comm.recv(source=0)

    # Send data to right child
    index = ceil(len(info)/2) # Get midpoint of list
    data_set = info[:index]
    comm.send(info[index:], 3)

    # Get sorted data from right child
    sorted_rec = comm.recv(source = 3)
    sorted23 = data_set + sorted_rec

    # Send data to parent node
    comm.send(sorted23, 0)

elif node == 3:
    info = comm.recv(source=2)  # Get data from parent node
    info.sort()                 # Sort data
    comm.send(info, 2)          # Send data to parent node

elif node == 4:
    # Get data from parent
    info = comm.recv(source=0)

    # Send data to right child
    index = ceil(len(info)/2) # Get midpoint of list
    data_set = info[:index]
    comm.send(info[index:], 6)

    # Send data to right child
    index2 = ceil(len(data_set)/2) # Get midpoint of list
    data_set2 = data_set[:index2]
    comm.send(data_set[index2:], 5)

    # Sort own data
    data_set2.sort()

    # Get right child data and sort
    sorted_rec = comm.recv(source = 5)
    sorted45 = data_set2 + sorted_rec
    sorted45.sort()

    # Get right child data and sort
    sorted_rec = comm.recv(source = 6)
    sorted4567 = sorted45 + sorted_rec
    sorted4567.sort()

    # Send sorted data to parent node
    comm.send(sorted4567, 0)

elif node == 5:
    info = comm.recv(source=4)  # Get data from parent node
    info.sort()                 # Sort data
    comm.send(info, 4)          # Send sorted data to parent

elif node == 6:
    # Get data from parent
    info = comm.recv(source=4)
    index = ceil(len(info)/2) # Get midpoint of list
    data_set = info[:index]

    # Send right side to right child
    comm.send(info[index:], 7)

    # Sort own data
    data_set.sort()

    # Get sorted data from right child node
    sorted_rec = comm.recv(source = 7)
    sorted67 = (data_set + sorted_rec)

    # Sort combined data
    sorted67.sort()

    # Send to parent node
    comm.send(sorted67, 4)

elif node == 7:
    info = comm.recv(source=6)  # Get data from parent node
    info.sort()                 # Sort data
    comm.send(info, 6)          # Send sorted data to parent




