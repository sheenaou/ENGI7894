from queue import Queue
from simpy import RealtimeEnvironment
from random import randint
from threading import Lock, Thread

class DriveThrough:
    def __init__(self):
        self.customers = Customer_Queue()
        self.payment = Payment()
        self.window0 = Window(id="Jane", payment=self.payment)
        self.window1 = Window(id="John", payment=self.payment)
        self.monitor = Monitor(window0=self.window0, window1=self.window1, people=self.customers)
        people = Thread(target=self.customers.generate_customers, name="people", daemon=True)
        crew0 = Thread(target=self.window0.serve_queue, name="John", daemon=True)
        crew1 = Thread(target=self.window1.serve_queue, name="Jane", daemon=True)
        monitor = Thread(target=self.monitor.move_people, name="Monitor", daemon=True)
        self.threads = [people, crew0, crew1, monitor]
        self.clock = RealtimeEnvironment(initial_time=0, factor=1/3600, strict=False)

    def start(self):
        for thread in self.threads:
            thread.start()
        self.clock.run(until=14400000)


class Customer:
    def __init__(self, id, time):
        self.id = id
        self.arrival_time = time
        self.finish_time = None
        self.attempted = False
        self.complete = False

    def action(self):
        self.attempted=True

    def finished(self, time):
        self.finish_time = self.arrival_time + time
        self.complete = True

class Customer_Queue:
    def __init__(self):
        self.history = []
        self.customer_queue = []
        self.customer_count = 0
        self.queue_lock = Lock()
        self.clock = RealtimeEnvironment(initial_time=0, factor=1/3600, strict=False)

    def generate_customers(self):
        arrive_time = randint(50, 100)
        while True:
            self.clock.run(until = arrive_time)
            C = Customer(id=self.customer_count, time=arrive_time)
            # print("Customer {} has been created".format(C.id))
            self.history.append(C)
            self.queue_lock.acquire()
            self.customer_queue.append(C)
            self.queue_lock.release()
            self.customer_count = self.customer_count + 1
            arrive_time = arrive_time + randint(50, 100)

class Monitor:
    def __init__(self, window0, window1, people):
        self.window0 = window0
        self.window1 = window1
        self.people = people

    def move_people(self):
        while True:
            customer = self.people.customer_queue.pop(0)
            if len(self.window0.queue)==3 and len(self.window1.queue)==3:
                print("Customer is waiting to be put in line")
                def waiting():
                    clock = RealtimeEnvironment(initial_time=0, factor=1/3600, strict=False)
                    # Try to get into a queue every second
                    for i in range(1, 21):
                        clock.run(until=i)
                        full = self.window0.queue.full and self.window1.queue.full
                        if not full:
                            if len(self.window0.queue) < len(self.window1.queue):
                                self.window0.put(customer)
                                customer.action()
                                print("Customer {} has been put into {}'s queue".format(customer.id, self.window0.id))
                            else:
                                self.window1.put(customer)
                                customer.action()
                                print("Customer {} has been put into {}'s queue".format(customer.id, self.window1.id))
                    if not customer.attempted:
                        clock.run(until=621)
                        self.people.customer_queue.append(customer)
                        clock.run(until=661)
                        self.people.queue_lock.acquire()
                        if not customer.attempted:
                            self.people.customer_queue.remove(customer)
                        self.people.queue_lock.release()
                waiting = Thread(target=waiting, daemon=True)
                waiting.start()
                clock = RealtimeEnvironment(initial_time=0, factor=1 / 3600, strict=False)
                clock.run(until=20)
            elif len(self.window0.queue) < len(self.window1.queue):
                self.window0.put(customer)
                print("Customer {} has been put into {}'s queue".format(customer.id, self.window0.id))
            else:
                self.window1.put(customer)
                print("Customer {} has been put into {}'s queue".format(customer.id, self.window1.id))

class Window:
    def __init__(self, id, payment):
        self.id = id
        self.queue = Queue(maxsize=3)
        self.clock = RealtimeEnvironment(initial_time=0, factor=1/3600, strict=False)
        self.payment_queue = payment

    def serve_queue(self):
        serve_time = 0
        while True:
            if not self.queue.empty():
                time = randint(300, 600)
                serve_time = serve_time + time
                self.clock.run(until=serve_time)
                C = self.queue.get()
                print("Customer {} has finished being served".format(C.id))
                C.finished(time)
                self.payment_queue.complete(C)

class Payment:
    def __init__(self):
        self.queue = []
        self.lock = Lock()

    def complete(self, C):
        self.lock.acquire()
        self.queue.append(C)
        self.lock.release()

d = DriveThrough()
d.start()
