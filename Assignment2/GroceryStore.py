from queue import Queue
from simpy import RealtimeEnvironment
from random import randint
from threading import Lock, Thread
import sys

speed = 1/600

class GroceryStore:
    def __init__(self, duration):
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
    def __init__(self, lock):
        self.queue = Queue(maxsize=2)
        self.clock = RealtimeEnvironment(initial_time=0, factor=speed, strict=False)
        self.status = True
        self.checkout_lock = lock

    def serve_queue(self):
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
        self.status = False

class Customer:
    def __init__(self, id, time):
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
        # self.wait_time = self.wait_time + time

    def queue_action(self):
        self.actions = 5

    def in_checkout(self):
        if self.actions == 5:
            return True
        else:
            return False

    def add_time(self, time):
        self.wait_time = self.wait_time + time


    def finished(self, time):
        self.finish_time = self.arrival_time + time
        self.complete = True
        self.actions = -1


class Controller:
    def __init__(self, duration, lock, checkout0, checkout1, checkout2):
        self.history = []
        self.status = False
        self.duration = duration
        self.clock = RealtimeEnvironment(initial_time=0, factor=speed, strict=False)
        self.checkout_lock = lock
        self.checkout0 = checkout0
        self.checkout1 = checkout1
        self.checkout2 = checkout2

    def simulate(self):
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
        self.status = False

def main():
    if len(sys.argv) == 1:
        print("INVALID -- usage: GroceryStore.py <simulate_duration>")
    else:
        print("*****SIMULATION STARTED*****")
        duration = int(sys.argv[1]) * 60 # Convert to seconds
        g = GroceryStore(duration)
        g.start()


main()