from random import randint
from threading import Lock, Thread
from simpy import RealtimeEnvironment
import sys

speed = 0.25
action_time = 2
active_light = None
error = None
directions = {0:"left", 1:"straight", 2:"right"}

class Car:
    def __init__(self, road, id, direction):
        self.road = road
        self.id = str(road) +"." + str(id)
        self.direction = direction


class Road:
    def __init__(self, id, cars):
        """Method to create an instance of a road
            args:
                id = Unique identifier (0, 1, 2, 3)
                cars = The number of initial cars at an intersection"""
        self.cars = []
        self.id = id
        self.incoming = Lock()
        self.status = True
        for i in range(0, cars):
            car = Car(road=self.id, id=i, direction=randint(0, 2))
            self.cars.append(car)
        self.set_directions()
        print("Road {} has been created with the following cars:".format(id, ))
        for car in self.cars:
            print("\t> {} and wants to go {}".format(car.id, directions[car.direction]))

    def set_directions(self):
        """Method to determine which road corresponds to the left, straight, and right directions"""
        self.left = (self.id + 3) % 4
        self.straight = (self.id + 2) % 4
        self.right = (self.id + 1) % 4

    def set_lock(self, locks):
        self.locks = locks

    def green_actions(self, direction):
        global error
        clock = RealtimeEnvironment(initial_time=0, factor=speed, strict=False)
        print("Car {} is trying to go {}".format(self.cars[0].id, directions[self.cars[0].direction]))
        if not error:
            # CASE: Left turn
            if int(direction) == 0:
                print("Car {} is checking if it is clear".format(self.cars[0].id))
                if self.locks[str(self.left)].acquire():
                    if self.locks[str(self.id)].acquire(timeout=action_time):
                        print("It is clear for Car {} to go".format(self.cars[0].id))
                        clock.run(until=action_time) # Two seconds to perform actions -- arbitrary
                        car = self.cars.pop(0)
                        print("Car {} has made a left turn".format(car.id))
                        self.locks[str(self.id)].release()
                    else:
                        print("Car {} was unable to go...trying again")
                    self.locks[str(self.left)].release()

            # CASE: Straight
            elif int(direction) == 1:
                print("Car {} is checking if it is clear".format(self.cars[0].id))
                if self.locks[str(self.right)].acquire():
                    if self.locks[str(self.straight)].acquire(timeout=action_time):
                        print("It is clear for Car {} to go".format(self.cars[0].id))
                        clock.run(until=action_time)
                        car = self.cars.pop(0)
                        print("Car {} has driven straight".format(car.id))
                        self.locks[str(self.straight)].release()
                    else:
                        print("Car {} was unable to go...trying again")
                    self.locks[str(self.right)].release()

            # CASE: Right turn
            elif int(direction) == 2:
                print("Car {} is checking if it is clear".format(self.cars[0].id))
                self.locks[str(self.right)].acquire()
                print("It is clear for Car {} to go".format(self.cars[0].id))
                clock.run(until=2)
                car = self.cars.pop(0)
                print("Car {} has made a right turn".format(car.id))
                self.locks[str(self.right)].release()

            # CASE: Unknown action
            else:
                pass

    def red_actions(self, direction):
        complete = False
        global active_light
        global human
        global error
        if int(direction) == 2:
            while self.id != (active_light.direction % 2) and not complete and not error:
                print("Car {} wants to turn right on a red light".format(self.cars[0].id))
                clock = RealtimeEnvironment(initial_time=0, factor=speed, strict=False)
                clock.run(until=3)
                if self.locks[str(self.right)].acquire(False):
                    car = self.cars.pop(0)
                    print("It is clear for Car {}".format(car.id))
                    clock.run(until=5)
                    print("Car {} has made a right turn".format(car.id))
                    self.locks[str(self.right)].release()
                    complete = True
                else:
                    if human:
                        print("WARNING:Car {} has caused a crash...\n SIMULATION OVER".format(self.cars[0].id))

                        error = True
                    else:
                        print("Car {} was unable turn right on a red light, trying again".format(self.cars[0].id))

    def run(self):
        global active_light
        while self.status:
            if active_light is not None and len(self.cars) > 0:
                if (self.id % 2) == active_light.direction:   # The light is green for this road
                    self.green_actions(direction=self.cars[0].direction)
                else:
                    self.red_actions(direction=self.cars[0].direction)
            elif len(self.cars) == 0:
                print("All the cars in road {} has been cleared".format(self.id))
                self.status = False


class TrafficLight:
    def __init__(self, direction):
        """Method to create an instance of a traffic light
            args:
                direction -- the direction of the traffic light
                    available values -- 0/2 or 1/4 """

        self.direction = direction
        self.status = "red"

    def set_colour(self, colour):
        self.status = colour


class TrafficLightController:
    def __init__(self):
        self.light0 = TrafficLight(direction=0)
        self.light1 = TrafficLight(direction=1)
        self.active = True

    def run(self):
        while self.active:
            for light in [self.light0, self.light1]:
                clock = RealtimeEnvironment(initial_time=0, factor=speed, strict=False)
                other_light = self.light1 if light == self.light0 else self.light0
                global active_light
                active_light = light
                print("*************************\n"
                      "Active Light: {} and {}\n"
                      "Inactive Light : {} and {}\n"
                      "*************************\n".format(active_light.direction,
                                                           int(active_light.direction) + 2,
                                                           other_light.direction,
                                                           other_light.direction + 2))
                other_light.set_colour("red")
                light.set_colour("green")
                clock.run(until=18)
                light.set_colour("yellow")
                clock.run(until=20)


class Intersection:
    def __init__(self):
        global human
        self.lights = TrafficLightController()
        self.road0 = Road(id=0, cars=1 if not human else 10)
        self.road1 = Road(id=1, cars=1 if not human else 10)
        self.road2 = Road(id=2, cars=2 if not human else 10)
        self.road3 = Road(id=3, cars=3 if not human else 10)
        self.roads = [self.road0, self.road1, self.road2, self.road3]
        locks = {
            "0": self.road0.incoming,
            "1": self.road1.incoming,
            "2": self.road2.incoming,
            "3": self.road3.incoming,
        }
        for road in self.roads:
            road.set_lock(locks)
        self.thread_lights = Thread(target=self.lights.run, daemon = True)
        self.thread_roads = [
            Thread(target=self.road0.run, daemon = True),
            Thread(target=self.road1.run, daemon = True),
            Thread(target=self.road2.run, daemon = True),
            Thread(target=self.road3.run, daemon = True)
        ]

    def run(self):
        self.thread_lights.start()
        for road in self.thread_roads:
            road.start()
        status = True
        while status:
            if error:
                sys.exit()
            else:
                count = 0
                for road in self.roads:
                    if not road.status:
                        count = count + 1
                if count == 4:
                    status = False
                    self.lights.active = False
        print("Simulation is COMPLETE")

simulation = input("Would you like to simulate with human error? Y/N\n")
human = True if simulation == "Y" else False
t = Intersection()
t.run()