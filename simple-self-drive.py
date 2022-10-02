
import time
import math
from random import randrange
import picar_4wd as fc

DIST = 25
LONGDIST = 55
SPEED = 30

route = []
INITIAL_ROUTE = ['FW', 200] # a simple route: 2m ahead
LEFT_TURN = ['LF', 90]
RIGHT_TURN = ['RT', 90]
RANDOM_TURN = ['RD', 0]
SHORT_FW = ['FW', 30]

def avoid_left():
    route.insert(0, RIGHT_TURN)
    route.insert(0, SHORT_FW)
    route.insert(0, LEFT_TURN)
def avoid_right():
    route.insert(0, LEFT_TURN)
    route.insert(0, SHORT_FW)
    route.insert(0, RIGHT_TURN)

def detect_close_object():
    while True:
        readings = fc.scan_step(DIST)
        if not readings:
            continue
        print(readings)
        return 1 in readings


def long_range_scan():
    long_read = []
    while len(long_read) < 5:
        readings = fc.scan_step(LONGDIST)
        if not readings:
            continue
        print(readings)
        long_read.append(readings)
    return long_read

def clean_readings(readings):
    return [0 if x == 2 else 1 for x in readings]

def average_readings(long_readings):
    cleaned = [clean_readings(x) for x in long_readings]
    results = [sum(i) for i in zip(*cleaned)]
    return results

def avoid(long_read):
    results = average_readings(long_read)
    l = int(len(results)/3)
    print(results)
    left = results[:l]
    right = results[-l:]
    leftsum = sum(left)
    rightsum = sum(right)
    if leftsum > 8 and rightsum > 8:
        route.insert(0, RANDOM_TURN)
    else:
        if leftsum<rightsum:
            avoid_left()
        elif rightsum<leftsum:
            avoid_right()
        else: # choses random direction
            if randrange(2) == 0:
                avoid_left()
            else:
                avoid_right()


ANGULAR_CALIBRATION = 1.55
TRACTION_RADIUS = 13.5
def angular_speed():
    return (fc.right_rear_speed() - fc.left_rear_speed()) / math.pi / TRACTION_RADIUS * ANGULAR_CALIBRATION

LEFT_TURN_CALIBRATION = 1.35 # turning right and left has different traction for some reason
def turn(rads, speed):
    # print(f"RADs: {rads}")
    if rads > 0:
        rads = rads * LEFT_TURN_CALIBRATION
        fc.turn_left(speed)
    elif rads < 0:
        fc.turn_right(speed)
    else: return
    curr = 0
    start_time = time.time()
    while abs(curr) < abs(rads):
        time.sleep(0.001)
        current_time = time.time()
        time_diff = current_time-start_time
        start_time = current_time
        dist = time_diff*angular_speed()
        curr += dist
    print(curr)
    fc.stop()
    time.sleep(0.5)


def turn_right_90deg(speed):
    angle = -math.pi/2
    turn(angle,speed)

def turn_left_90deg(speed):
    angle = math.pi/2
    turn(angle,speed)

def go_back(tgt):
    start_time = time.time()
    fc.backward(SPEED)
    curr = 0
    while curr < tgt:
        time.sleep(0.01)
        current_time = time.time()
        time_diff = current_time-start_time
        start_time = current_time
        dist = time_diff*fc.speed_val()
        curr += dist
    fc.stop()

def random_turn():
    current_time = time.time()*1000
    milis = randrange(3000)
    expected = current_time+milis
    dir = randrange(2) == 0
    while current_time<expected:
        if dir == 1:
            fc.turn_right(SPEED)
        else:
            fc.turn_left(SPEED)
        current_time = time.time()*1000
    fc.stop()


def main():
    route.append(INITIAL_ROUTE)
    fc.start_speed_thread()
    start_time = time.time()
    fc.forward(SPEED)
    while len(route) > 0:
        print(route)
        current_route = route[0]
        current_command, current_dist = current_route
        if current_command == 'FW':
            
            print(f'FORWARD {current_dist}')

            if detect_close_object():
                print("Close Object")
                fc.stop()
                go_back(10)
                print('-'*10)
                long_results = long_range_scan()
                avoid(long_results)
            else:
                fc.forward(SPEED)
                time.sleep(0.01)
                current_time = time.time()
                time_diff = current_time-start_time
                dist = time_diff*fc.speed_val()
                current_dist -= dist
                start_time = time.time()
                if current_dist <= 0:
                    route.pop(0)
                else:
                    route[0] = [current_command, current_dist]
        elif current_command == 'RT':
            turn_right_90deg(SPEED)
            route.pop(0)
        elif current_command == 'LF':
            turn_left_90deg(SPEED)
            route.pop(0)
        elif current_command == 'RD':
            random_turn()
            route.pop(0)
    print('DONE!')
    fc.stop()
    fc.turn_right(SPEED)

        

if __name__ == "__main__":
    try:
        main()
    finally:
        fc.stop()
