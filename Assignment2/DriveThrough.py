##################################################
# ENGI 7894 - Concurrent Programming
# Assignment 2 - Question 1 (Drive Through)
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

speed = 1 / 3600    # hours to seconds

class DriveThrough:
    """This class will simulate a Drive Through scenario"""
    def __init__(self, time):
        """This class will create an instance of a Drive Through"""
        self.length = time
        self.clock = RealtimeEnvironment(initial_time=0, factor=speed, strict=False)
        self.customers = CustomerQueue(time)
        self.payment = Payment()
        self.window0 = Window(id="Jane", payment=self.payment)
        self.window1 = Window(id="John", payment=self.payment)
        self.monitor = Monitor(window0=self.window0, window1=self.window1, people=self.customers)
        people = Thread(target=self.customers.generate_customers, name="people")
        crew0 = Thread(target=self.window0.serve_queue, name="John")
        crew1 = Thread(target=self.window1.serve_queue, name="Jane")
        monitor = Thread(target=self.monitor.move_people, name="Monitor")
        self.threads = [people, crew0, crew1, monitor]
        self.objects = [self.window0, self.window1, self.monitor]

    def start(self):
        """This method will start the drive though simulation"""
        for thread in self.threads:
            thread.start()
        self.clock.run(until=self.length)

        for thread in self.objects:
            thread.change_status()

        while not self.customers.customer_queue:
            pass
        self.clock.run(until=self.length + 1000)    # let each thread finish before collecting stats
        time_sum = 0
        complete = 0
        for customer in self.customers.history:
            if customer.complete:
                time_sum = time_sum + customer.finish_time - customer.arrival_time
                complete = complete + 1

        print("\n************************************\n"
              "Total Customer Arrived: {}\n"
              "Total Customer Served: {}\n"
              "Average time to serve: {}\n".format(len(self.customers.history), complete, time_sum//complete))


class Customer:
    """This class represents a customer that appears"""
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
            1 - Attempting to put into a window queue
            2 - Waiting for a window queue to open
            3 - Leaving the line
            4 - Rejoining the line
            5 - Leaving the line permanently
            (-1) - Put into window queue after waiting
        """
        self.actions = self.actions + value

    def queue_action(self):
        """This method will put the customer into the 'Put into window queue' state"""
        self.actions = -1

    def in_window(self):
        """This method will return a boolean value indicating if the customer has been put into a window queue"""
        if self.actions == -1:
            return True
        else:
            return False

    def add_time(self, time):
        """This method will add time to the total amount of time a customer has been waiting to be put into a queue"""
        self.wait_time = self.wait_time + time

    def finished(self, time):
        """This method will set the status of the customer to complete and
        add the total time it took for the customer to get served"""
        self.finish_time = self.arrival_time + self.wait_time + time
        self.complete = True


class CustomerQueue:
    """This class represents the line up of customers waiting to be put into queues.
    It will generate an instance of a customer every 50 to 100 seconds.
        """
    def __init__(self, duration):
        """This method will create an instance of a CustomerQueue"""
        self.history = []
        self.customer_queue = []
        self.customer_count = 0
        self.queue_lock = Lock()
        self.clock = RealtimeEnvironment(initial_time=0, factor=speed, strict=False)
        self.duration = duration
        self.status = True

    def generate_customers(self):
        """This function will generate a Customer object every 50-100 seconds"""
        arrive_time = randint(50, 100)
        while self.status:
            self.clock.run(until=arrive_time)
            c = Customer(id=self.customer_count, time=arrive_time)
            self.history.append(c)
            self.queue_lock.acquire()
            self.customer_queue.append(c)
            self.queue_lock.release()
            self.customer_count = self.customer_count + 1
            arrive_time = arrive_time + randint(50, 100)

    def change_status(self):
        """This method will halt the thread from performing any more executions of the target function"""
        self.status = False


class Monitor:
    """This class is responsible for placing the customers into a Window Queue"""
    def __init__(self, window0, window1, people):
        """This method will create an instance of a monitor"""
        self.window0 = window0
        self.window1 = window1
        self.people = people
        self.status = True

    def move_people(self):
        """This function will place customers into a window queue if space is available"""
        people = self.people.customer_queue
        people_lock = self.people.queue_lock
        window0 = self.window0.queue
        window1 = self.window1.queue
        queue_message = "Customer {} has been put into {}'s queue"

        while self.status:
            if len(people) is not 0:
                queue_message = "Customer {} has been put into {}'s queue"
                # CASE: Both window queues are full
                if window0.full() and window1.full():
                    def waiting(customer):
                        """This is the waiting sequence for a customer who cannot be put into a queue right away"""
                        clock = RealtimeEnvironment(initial_time=0, factor=speed, strict=False)
                        customer.action()  # Waiting for queue to open
                        # Try to get into a queue every seconds
                        for i in range(1, 20):
                            clock.run(until=i)
                            if not (window0.full and window1.full):
                                customer.queue_action()
                                customer.add_time(i)
                                if window0.qsize() < window1.qsize():
                                    window0.put(customer)
                                    print(queue_message.format(customer.id, self.window0.id))
                                else:
                                    window1.put(customer)
                                    print(queue_message.format(customer.id, self.window1.id))
                        if not customer.in_window():
                            # leave and put them back into the queue
                            print("Customer {} has left and will try again later".format(customer.id))
                            customer.action()   # Leaving the line
                            customer.add_time(600)
                            clock.run(until=620)
                            people_lock.acquire()
                            people.append(customer)

                            customer.action() # Rejoining the line
                            people_lock.release()
                            print("Customer {} had rejoined the waiting list".format(customer.id))

                            # Leave permanently
                            clock.run(until=660)
                            people_lock.acquire()
                            if not customer.in_window():
                                customer.action() # Leaving Permanently
                                customer.add_time(40)
                                people.remove(customer)
                                print("Customer {} has left permanently".format(customer.id))
                            people_lock.release()

                    # Execute waiting sequence
                    people_lock.acquire()
                    if people:
                        if people[0].in_window() is False and people[0].actions == 0:
                            customer = people.pop(0)
                            customer.action()
                            people_lock.release()

                            # Execute waiting sequence
                            waiting = Thread(target=waiting, args=(customer,))
                            waiting.start()
                            clock = RealtimeEnvironment(initial_time=0, factor=speed, strict=False)
                            clock.run(until=20)
                        else:
                            people_lock.release()
                    else:
                        people_lock.release()

                # CASE: There is available space in a window queue
                else:
                    people_lock.acquire()
                    customer = people.pop(0)
                    customer.queue_action()
                    people_lock.release()
                    if window0.qsize() < window1.qsize():
                        window0.put(customer)
                        print(queue_message.format(customer.id, self.window0.id))
                    else:
                        window1.put(customer)
                        print(queue_message.format(customer.id, self.window1.id))

    def change_status(self):
        """This method will halt the thread from performing any more executions of the target function"""
        self.status = False


class Window:
    """This class represents the window where the customer is served"""
    def __init__(self, id, payment):
        """This method will create an instance of a Window"""
        self.id = id
        self.queue = Queue(maxsize=3)
        self.clock = RealtimeEnvironment(initial_time=0, factor=speed, strict=False)
        self.payment_queue = payment
        self.status = True

    def serve_queue(self):
        """This method will serve the customers in the queue. Serving a customer will take 300 to 600 seconds"""
        serve_time = 0
        while self.status:
            if not self.queue.empty():
                time = randint(300, 600)
                serve_time = serve_time + time
                self.clock.run(until=serve_time)
                c = self.queue.get()
                print("Customer {} has finished being served".format(c.id))
                c.finished(time)
                self.payment_queue.complete(c)

    def change_status(self):
        """This method will halt the thread from performing any more executions of the target function"""
        self.status = False


class Payment:
    """This class represents the payment window"""
    def __init__(self):
        """This class will create an instance of a Payment window"""
        self.queue = []
        self.lock = Lock()

    def complete(self, c):
        """This method will set the customer to complete"""
        self.lock.acquire()
        self.queue.append(c)
        self.lock.release()


def main():
    """The function will parse command line arguments and execute the simulation"""
    if len(sys.argv) == 1:
        print("INVALID FORMAT -- usage: DriveThrough.py <simulation_duration>")
    else:
        duration = int(sys.argv[1]) * 60  #convert to seconds
        d = DriveThrough(duration)
        d.start()


main()

