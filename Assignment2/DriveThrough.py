from queue import Queue
from simpy import RealtimeEnvironment
from random import randint
from threading import Lock, Thread

speed = 1 / 60


class DriveThrough:
    def __init__(self):
        self.customers = CustomerQueue()
        self.payment = Payment()
        self.window0 = Window(id="Jane", payment=self.payment)
        self.window1 = Window(id="John", payment=self.payment)
        self.monitor = Monitor(window0=self.window0, window1=self.window1, people=self.customers)
        people = Thread(target=self.customers.generate_customers, name="people", daemon=True)
        crew0 = Thread(target=self.window0.serve_queue, name="John", daemon=True)
        crew1 = Thread(target=self.window1.serve_queue, name="Jane", daemon=True)
        monitor = Thread(target=self.monitor.move_people, name="Monitor", daemon=True)
        self.threads = [people, crew0, crew1, monitor]
        self.clock = RealtimeEnvironment(initial_time=0, factor=speed, strict=False)

    def start(self):
        for thread in self.threads:
            thread.start()
        self.clock.run(until=14400)


class Customer:
    def __init__(self, id, time):
        self.id = id
        self.arrival_time = time
        self.wait_time = 0
        self.finish_time = None
        self.actions = 0
        self.complete = False

    def actions(self):
        """ This function will increment for every action taken for a customer
            1 - Attempting to put into a queue
            2 - Waiting for a queue to open
            3 - Leaving the queue
            4 - Rejoining the queue
            5 - Leaving the queue permanently
        """
        self.actions = self.attempted + 1
        # self.wait_time = self.wait_time + time


    def finished(self, time):
        self.finish_time = self.arrival_time + time
        self.complete = True


class CustomerQueue:
    def __init__(self):
        self.history = []
        self.customer_queue = []
        self.customer_count = 0
        self.queue_lock = Lock()
        self.clock = RealtimeEnvironment(initial_time=0, factor=speed, strict=False)

    def generate_customers(self):
        """This function will generate a Customer object every 50-100 seconds"""
        arrive_time = randint(50, 100)
        while True:
            self.clock.run(until=arrive_time)
            c = Customer(id=self.customer_count, time=arrive_time)
            # print("Customer {} has been created".format(c.id))
            self.history.append(c)

            self.queue_lock.acquire()
            self.customer_queue.append(c)
            self.queue_lock.release()

            self.customer_count = self.customer_count + 1
            arrive_time = arrive_time + randint(50, 100)


class Monitor:
    def __init__(self, window0, window1, people):
        self.window0 = window0
        self.window1 = window1
        self.people = people

    def move_people(self):
        """This function will place customers into a window queue if space is available"""
        people = self.people.customer_queue
        people_lock = self.people.queue_lock
        window0 = self.window0.queue
        window1 = self.window0.queue
        queue_message = "Customer {} has been put into {}'s queue"

        while True:
            if len(people) is not 0:
                queue_message = "Customer {} has been put into {}'s queue"
                # CASE: Both window queues are full
                if window0.full() and window1.full():
                    # Waiting function for thread to execute
                    def waiting():
                        pass

                    # Get a Customer
                    people_lock.aquire()
                    customer = people.pop(0)
                    customer.actions()
                    # print(queue_message.format(customer.id, self.window0.id))
                    people_lock.release()

                    #

                else:
                    people_lock.aquire()
                    customer = people.pop(0)
                    customer.actions()
                    people_lock.release()
                    if window0.qsize() < window1.qsize():
                        window0.put(customer)
                        print(queue_message.format(customer.id, self.window0.id))
                    else:
                        window1.put(customer)
                        print(queue_message.format(customer.id, self.window1.id))





class Window:
    def __init__(self, id, payment):
        self.id = id
        self.queue = Queue(maxsize=3)
        self.clock = RealtimeEnvironment(initial_time=0, factor=speed, strict=False)
        self.payment_queue = payment

    def serve_queue(self):
        serve_time = 0
        while True:
            if not self.queue.empty():
                time = randint(300, 600)
                serve_time = serve_time + time
                self.clock.run(until=serve_time)
                c = self.queue.get()
                print("Customer {} has finished being served".format(c.id))
                c.finished(time)
                self.payment_queue.complete(c)


class Payment:
    def __init__(self):
        self.queue = []
        self.lock = Lock()

    def complete(self, c):
        self.lock.acquire()
        self.queue.append(c)
        self.lock.release()


def main():
    d = DriveThrough()
    d.start()


main()

queue_message = "Customer {} has been put into {}'s queue"
# CASE: Both window queues are full
if self.window0.queue.full() and self.window1.queue.full():
    # Waiting function for thread to execute
    def waiting():
        clock = RealtimeEnvironment(initial_time=0, factor=speed, strict=False)
        # Try to get into a queue every second
        for i in range(1, 21):
            clock.run(until=i)
            full = self.window0.queue.full and self.window1.queue.full
            if not full:
                if len(self.window0.queue) < len(self.window1.queue):
                    self.window0.queue.put(customer)
                    customer.action()
                    print(queue_message.format(customer.id, self.window0.id))
                else:
                    self.window1.queue.put(customer)
                    customer.action()
                    print(queue_message.format(customer.id, self.window1.id))
        if not customer.attempted:
            print("Customer {} has left and will try again".format(customer.id))
            clock.run(until=621)
            self.people.queue_lock.acquire()
            self.people.customer_queue.append(customer)
            self.people.queue_lock.release()
            print("Customer {} has rejoined the waiting list".format(customer.id))

            clock.run(until=661)
            self.people.queue_lock.acquire()
            if not customer.attempted:
                customer.action()
                self.people.customer_queue.remove(customer)
            self.people.queue_lock.release()
            print("Customer {} has left".format(customer.id))


    # Get a Customer
    self.people.queue_lock.acquire()
    customer = self.people.customer_queue.pop(0)
    self.people.queue_lock.release()
    print("Customer {} arrived at: {}".format(customer.id, customer.arrival_time))

    # Execute waiting sequence
    waiting = Thread(target=waiting, daemon=True)
    waiting.start()
    clock = RealtimeEnvironment(initial_time=0, factor=speed, strict=False)
    clock.run(until=20)

elif self.window0.queue.qsize() < self.window1.queue.qsize():
    # Get a Customer
    self.people.queue_lock.acquire()
    customer = self.people.customer_queue.pop(0)
    customer.action()
    self.people.queue_lock.release()
    self.window0.queue.put(customer)

    print(queue_message.format(customer.id, self.window0.id))
else:
    # Get a Customer
    self.people.queue_lock.acquire()
    customer = self.people.customer_queue.pop(0)
    customer.action()
    self.people.queue_lock.release()
    self.window1.queue.put(customer)
    print(queue_message.format(customer.id, self.window1.id))