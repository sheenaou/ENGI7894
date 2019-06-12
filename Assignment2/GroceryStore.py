##################################################
# ENGI 7894 - Concurrent Programming
# Assignment 2 - Question 2 (Grocery Store)
#
# Sheena Ou
# so7122@mun.ca
# 201523958
##################################################

from queue import Queue
from simpy import RealtimeEnvironment
from random import randint
from threading import Lock, Thread
import sys

speed = 1/600

class GroceryStore:
    """This class will simulate a Grocery Store"""
    def __init__(self, duration):
        """This method will create an instance of a Grocery Store"""
        self.duration = duration
        self.checkout_lock = Lock()
        self.clock = RealtimeEnvironment(initial_time=0, factor=speed, strict=False)
        self.checkout0 = CheckoutStation(lock=self.checkout_lock)
        self.checkout1 = CheckoutStation(lock=self.checkout_lock)
        self.checkout2 = CheckoutStation(lock=self.checkout_lock)
        self.controller = Controller(duration=self.duration, lock=self.checkout_lock, checkout0=self.checkout0,
                                     checkout1=self.checkout1, checkout2=self.checkout2)
        thread_checkout0 = Thread(target=self.checkout0.serve_queue)
        thread_checkout1 = Thread(target=self.checkout1.serve_queue)
        thread_checkout2 = Thread(target=self.checkout2.serve_queue)
        thread_controller = Thread(target=self.controller.simulate)
        self.threads = [thread_checkout0, thread_checkout1, thread_checkout2, thread_controller]
        self.objects = [self.checkout0, self.checkout1, self.checkout2, self.controller]

    def start(self):
        """This method will perform the simulation of the Grocery Store and output statistics to the terminal"""
        print("Starting Threads...")
        for thread in self.threads:
            thread.start()
        self.clock.run(until=self.duration)

        for object in self.objects:
            object.change_status()
        self.clock.run(until=self.duration + 2000)
        print("All threads have stopped...")

        time_sum = 0
        complete = 0
        for customer in self.controller.history:
            if customer.complete:
                time_sum = time_sum + customer.finish_time - customer.arrival_time
                complete = complete + 1

        print("\n************************************\n"
              "Total Customer Arrived: {}\n"
              "Total Customer Served: {}\n"
              "Average time to serve: {}\n".format(len(self.controller.history), complete, time_sum // complete))

class CheckoutStation:
    """This class will represent a Checkout Station at the Grocery Store"""
    def __init__(self, lock):
        """This method will create an instance of a Checkout Station"""
        self.queue = Queue(maxsize=2)
        self.clock = RealtimeEnvironment(initial_time=0, factor=speed, strict=False)
        self.status = True
        self.checkout_lock = lock

    def serve_queue(self):
        """This method will execute the simulation of a Checkout Station. This is the target function for the thread"""
        serve_time = 0
        while self.status or not self.queue.empty() or (not self.status and not self.queue.empty()):
        # while True:
            time = randint(300, 600)
            serve_time = serve_time + time
            # self.checkout_lock.acquire()
            c = self.queue.get()
            # self.checkout_lock.release()
            self.clock.run(until=serve_time)
            c.finished(time)
            print("Customer {} has finished being served".format(c.id))

    def change_status(self):
        """This method will halt the thread from performing any more executions of the target function"""
        self.status = False

class Customer:
    """This class will represent a Customer"""
    def __init__(self, id, time):
        """This method will create an instance of a Customer"""
        self.id = id
        self.arrival_time = time
        self.wait_time = 0
        self.finish_time = None
        self.actions = 0
        self.complete = False

    def action(self, value=1):
        """ This function will increment for every action taken for a customer
            0 - No actions have happened
            1 - Waiting for a checkout to open
            2 - Leaving the line
            3 - Rejoining the line
            4 - Leaving the line permanently
            5 - Put into checkout station
            (-1) - Finished served
        """
        self.actions = self.actions + value

    def queue_action(self):
        """This method will set the customer into the 'put into checkout station' status """
        self.actions = 5

    def in_checkout(self):
        """This method will return a boolean value indicating if the customer has been put into a checkout queue"""
        if self.actions == 5:
            return True
        else:
            return False

    def add_time(self, time):
        """This method will keep track of the amount of time that a customer has waited to get servec"""
        self.wait_time = self.wait_time + time


    def finished(self, time):
        """This method will change the customer's status to 'Finished served' and sum the total sum that it took
         to complete the full transaction
         """
        self.finish_time = self.arrival_time + self.wait_time + time
        self.complete = True
        self.actions = -1


class Controller:
    """This class will control the flow between the customers and the checkout stations"""
    def __init__(self, duration, lock, checkout0, checkout1, checkout2):
        """This method will create an instance of the Controller

            args:
                duration -- The amount of time that the simulation will run in seconds
                lock -- The shared lock used for all checkout stations
                checkout<x> -- An instance of a checkout station
            """
        self.history = []
        self.status = False
        self.duration = duration
        self.clock = RealtimeEnvironment(initial_time=0, factor=speed, strict=False)
        self.checkout_lock = lock
        self.checkout0 = checkout0
        self.checkout1 = checkout1
        self.checkout2 = checkout2

    def simulate(self):
        """This method is the target function for the thread, it will do the following:
            - Generate customers every 50 to 100 seconds
            - Place the customers in a shortest checkout line
            - If no space is available, it will create a thread to perform the 'waiting' sequence
        """
        checkout0 = self.checkout0.queue
        checkout1 = self.checkout1.queue
        checkout2 = self.checkout2.queue
        lock = self.checkout_lock
        arrive_time = randint(50, 100)

        while arrive_time < self.duration:
            # Generate a person
            self.clock.run(until=arrive_time)
            c = Customer(id=len(self.history), time=arrive_time)
            # print("Customer {} has appeared".format(c.id))
            self.history.append(c)

            # Try to put them in a checkout
            lock.acquire()

            # CASE: All checkouts are full --> customer must wait
            if checkout0.full() and checkout1.full() and checkout2.full():
                def waiting(customer):
                    """This function is the waiting sequence for a customer. It wil perform the following:
                        - Attempt to put the customer in a queue every second for 20 seconds
                        - Wait 600 seconds
                        - Attempt to put the customer in a queue every second for 40 seconds
                        - Make the customer leave

                        *NOTE* The next step is only performed if the previous one is
                        unsuccessful in placing the customer in a queue
                        """
                    clock = RealtimeEnvironment(initial_time=0, factor=speed, strict=False)
                    customer.action()   # Waiting for checkout to open

                    print("Customer {} is waiting for a queue to open".format(customer.id))
                    for i in range(1, 20):
                        clock.run(until=i)
                        lock.acquire()
                        if (not customer.in_checkout()
                            and (not (checkout0.full() and checkout1.full() and checkout2.full()))):
                            key = min(checkout0.qsize(), checkout1.qsize(), checkout2.qsize())
                            customer.queue_action()
                            customer.add_time(i)
                            if checkout0.qsize() == key:
                                print("Customer {} has been put into Checkout 0".format(customer.id))
                                checkout0.put(customer)
                            elif checkout1.qsize() == key:
                                print("Customer {} has been put into Checkout 1".format(customer.id))
                                checkout1.put(customer)
                            else:  # self.checkout2.queue.qsize() == key:
                                print("Customer {} has been put into Checkout 2".format(customer.id))
                                checkout2.put(customer)
                        lock.release()

                    if not customer.in_checkout():
                        print("Customer {} had left and will try again later".format(customer.id))
                        customer.action()   # Leave the area
                        customer.add_time(600)
                        clock.run(until=620)

                        print("Customer {} had rejoined the checkout area".format(customer.id))
                        customer.action()
                        for i in range(1, 40):
                            clock.run(until=620+i)
                            lock.acquire()
                            if (not customer.in_checkout()
                                    and (not (checkout0.full() and checkout1.full() and checkout2.full()))):
                                key = min(checkout0.qsize(), checkout1.qsize(), checkout2.qsize())
                                customer.queue_action()
                                customer.add_time(i)
                                if checkout0.qsize() == key:
                                    print("Customer {} has been put into Checkout 0".format(customer.id))
                                    checkout0.put(customer)
                                elif checkout1.qsize() == key:
                                    print("Customer {} has been put into Checkout 1".format(customer.id))
                                    checkout1.put(customer)
                                else:  # self.checkout2.queue.qsize() == key:
                                    print("Customer {} has been put into Checkout 2".format(customer.id))
                                    checkout2.put(customer)
                            lock.release()

                        if not customer.in_checkout():
                            print("Customer {} has left permanently".format(customer.id))
                            customer.action()

                # Execute waiting sequence
                lock.release()
                print("Customer {} is waiting".format(c.id))
                waiting = Thread(target=waiting, args=(c,))
                waiting.start()
                clock = RealtimeEnvironment(initial_time=0, factor=speed, strict=False)
                clock.run(until=20)

            # CASE: A checkout station is open --> place in the shortest queue
            else:
                key = min(checkout0.qsize(), checkout1.qsize(), checkout2.qsize())
                c.queue_action()
                if checkout0.qsize() == key:
                    checkout0.put(c)
                    print("Customer {} has been put into Checkout 0".format(c.id))
                elif checkout1.qsize() == key:
                    checkout1.put(c)
                    print("Customer {} has been put into Checkout 1".format(c.id))
                else:   # checkout2.qsize() == key:
                    checkout2.put(c)
                    print("Customer {} has been put into Checkout 2".format(c.id))
                lock.release()

            arrive_time = arrive_time + randint(50, 100)

    def change_status(self):
        """This method will halt the thread from performing any more executions of the target function"""
        self.status = False

def main():
    """This function is the point of entry for the program.
    It will parse the command line arguments and execute the simualation"""
    if len(sys.argv) == 1:
        print("INVALID -- usage: GroceryStore.py <simulate_duration>")
    else:
        print("*****SIMULATION STARTED*****")
        duration = int(sys.argv[1]) * 60 # Convert to seconds
        g = GroceryStore(duration)
        g.start()


main()