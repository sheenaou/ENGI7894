from queue import Queue
from simpy import RealtimeEnvironment
from random import randint
from threading import Lock, Thread, active_count
import sys


class GroceryStore:
    def __init__(self):
        self.checkout_lock = Lock()
        self.checkout0 = CheckoutStation()
        self.checkout1 = CheckoutStation()
        self.checkout2 = CheckoutStation()


class CheckoutStation:
    def __init__(self):
        self.queue = Queue(maxsize=2)
        self.clock = RealtimeEnvironment(initial_time=0, factor=speed, strict=False)
        self.status = True

    def serve_queue(self):
        serve_time = 0
        while (self.status and not self.queue.empty()) or (not self.status and not self.queue.empty()):
            time = randint(300, 600)
            serve_time = serve_time + time
            self.checkout_lock.acquire()
            c = self.queue.get()
            self.checkout_lock.release()
            self.clock.run(until=serve_time)
            print("Customer {} has finished being served".format(c.id))
            c.finished(time)


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
            3 - Leaving the line
            4 - Rejoining the line
            5 - Leaving the line permanently
            (-1) - Put into checkout station
        """
        self.actions = self.actions + value
        # self.wait_time = self.wait_time + time

    def queue_action(self):
        self.actions = -1

    def in_checkout(self):
        if self.actions == -1:
            return True
        else:
            return False

    def finished(self, time):
        self.finish_time = self.arrival_time + time
        self.complete = True

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
        arrive_time = randint(50, 100)
        while arrive_time < self.duration:
            # Generate a person
            self.clock.run(until=arrive_time)
            c = Customer(id=len(self.history), time=arrive_time)
            self.history.append(c)

            # Try to put them in a checkout
            self.checkout_lock.acquire()

            # CASE: All checkouts are full --> customer must wait
            if self.checkout0.queue.full and self.checkout1.queue.full and self.checkout2.queue.full:
                def waiting(customer):
                    clock = RealtimeEnvironment(initial_time=0, factor=speed, strict=False)
                    customer.action()   # Waiting for checkout to open

                    for i in range(1, 20):
                        clock.run(until=i)
                        self.checkout_lock.acquire()
                        if not (self.checkout0.queue.full and self.checkout1.queue.full and self.checkout2.queue.full):
                            key = min(self.checkout0.queue.qsize(), self.checkout1.queue.qsize(),
                                      self.checkout2.queue.qsize())
                            c.queue_action()
                            c.add_time(i)
                            if self.checkout0.queue.qsize() == key:
                                self.checkout0.queue.put(c)
                            elif self.checkout1.queue.qsize() == key:
                                self.checkout1.queue.put(c)
                            else:  # self.checkout2.queue.qsize() == key:
                                self.checkout2.queue.put(c)
                        self.checkout_lock.release()


                    if not customer.in_checkout():
                        customer.action()   # Leave the area
                        customer.add_time(600)
                        clock.run(until=620)

                        self.checkout_lock.acquire()
                        if not (self.checkout0.queue.full and self.checkout1.queue.full and self.checkout2.queue.full):
                            key = min(self.checkout0.queue.qsize(), self.checkout1.queue.qsize(),
                                      self.checkout2.queue.qsize())
                            c.queue_action()
                            c.add_time(i)
                            if self.checkout0.queue.qsize() == key:
                                self.checkout0.queue.put(c)
                            elif self.checkout1.queue.qsize() == key:
                                self.checkout1.queue.put(c)
                            else:  # self.checkout2.queue.qsize() == key:
                                self.checkout2.queue.put(c)
                        self.checkout_lock.release()

                        if not customer.in_checkout():
                            for i in range(1, 40):
                                clock.run(until=620+i)
                                self.checkout_lock.acquire()
                                if not (self.checkout0.queue.full and self.checkout1.queue.full and self.checkout2.queue.full):
                                    key = min(self.checkout0.queue.qsize(), self.checkout1.queue.qsize(),
                                              self.checkout2.queue.qsize())
                                    c.queue_action()
                                    c.add_time(i)
                                    if self.checkout0.queue.qsize() == key:
                                        self.checkout0.queue.put(c)
                                    elif self.checkout1.queue.qsize() == key:
                                        self.checkout1.queue.put(c)
                                    else:  # self.checkout2.queue.qsize() == key:
                                        self.checkout2.queue.put(c)
                                self.checkout_lock.release()

                # Execute waiting sequence
                self.checkout_lock.release()
                waiting = Thread(target=waiting, args=(c,))
                waiting.start()
                clock = RealtimeEnvironment(initial_time=0, factor=speed, strict=False)
                clock.run(until=20)
                self.checkout_lock.release()

            # CASE: A checkout station is open --> place in the shortest queue
            else:
                key = min(self.checkout0.queue.qsize(), self.checkout1.queue.qsize(), self.checkout2.queue.qsize())
                c.queue_action()
                if self.checkout0.queue.qsize() == key:
                    self.checkout0.queue.put(c)
                elif self.checkout1.queue.qsize() == key:
                    self.checkout1.queue.put(c)
                else:   # self.checkout2.queue.qsize() == key:
                    self.checkout2.queue.put(c)
            self.checkout_lock.release()

            arrive_time = arrive_time + randint(50, 100)
        pass