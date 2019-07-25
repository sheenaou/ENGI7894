from pycuda import driver, autoinit
from pycuda.compiler import SourceModule
import numpy
import sys

kernel = SourceModule("""
  __global__ void distance(float *trajectories, float *stops, float *src, float *dest)
  {

    int i = threadIdx.x + threadIdx.y;
    
    int numStops = stops[i];
    int numTraj = trajectories[i];
    double lengths[20];
    int index = 0 ;
    
    for (int j = i; j<numTraj*numStops*2; j += numStops*2){ 
        int x = 0;
        int y = 0;
        double length = 0;
        
        for (int k = j; k < j + numStops*2; k += 2){
            length += sqrt( ( (x-src[k]) * (x-src[k]) ) + ( (y-src[k+1]) * (y-src[k+1]) ) );
            x = src[k];
            y = src[k+1];
        }
        lengths[index] = length;
        index ++;
    }
    
    for (int m = 0; m < numTraj; m ++){
        int min = m;
        for (int n = m + 1; n < numTraj; n++){
            if (lengths[n] < lengths[min]){
                min = n;
            }
        }
        
        double temp = lengths[m];
        lengths[m] = lengths[min];
        lengths[min] = temp;
        
        for (int p = 0; p < numStops*2; p ++){
            dest[m * numStops*2 + p] = src[m * numStops*2 + p];
        }
    }
    
  }
  """)

def main():
    if len(sys.argv) < 3:
        print "INVALID USAGE: Missing arguments"
    elif len(sys.argv) == 3:
        # Gather information for GPU
        file = open(sys.argv[1]).readlines()
        for i in range(0, len(file)):
            file[i] = file[i].replace("\n", "").split(" ")
        trajectories = numpy.array([int(file[0][0])]).astype(numpy.float32)
        num_stops = numpy.array([int(file[0][1])]).astype(numpy.float32)
        stops = numpy.array(file[1:]).astype(numpy.float32)
        dest = numpy.zeros_like(stops)

        # Create callable python function
        distance = kernel.get_function("distance")
        distance(driver.In(trajectories), driver.In(num_stops), driver.In(stops),  driver.Out(dest), block=(1, 1, 1))

        with open(sys.argv[2], "w") as output_file:
            for line in dest.tolist():
                for element in line:
                    output_file.write(str(int(element)) + " ")
                output_file.write("\n")

main()
