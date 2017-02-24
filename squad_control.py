# Conan Veitch, 2017
#
# Lowest MAC address in the squad is nominated as squad leader.
# Squad leader moves towards destination, squad follows.
#
# Step by step process below:
#
# 1) Leader checks if squad members are within n cm.
# 2) If yes, leader moves forward.
# 3) Squad members stay within x cm, outside of y cm of one another.
# 4) If a squad member is outside of x cm from the leader, stop.
# 5) If a squad leader is outside of x cm from another member, stop.
# 6) When within range of all squad members, begin moving again.
#
#
#

from mobility import drive
from mobility import turn
from mobility import Direction
from mobility import Bearing
from wireless_control import broadcast
from wireless_control import receive_rssi
from wireless_control import get_mac
from threading import Thread
from threading import RLock
from kalman_filter import KalmanFilter
import time

# Enum variables
forw = Direction.FORWARD
back = Direction.BACKWARD
right = Direction.RIGHT
left = Direction.LEFT
stop = Direction.STOP
fortyfive = Bearing.FORTY_FIVE
ninety = Bearing.NINETY

lock = RLock()

# Rupert specific variables
is_leader = False
in_formation = None
mac = None
d = None
d_error = None


def main():
    # Run Squad Behaviour functions.
    time.sleep(1)
    initialize_rupert(50, 10, 0, 900, 5, 10)
    # This sleep allows some rssi data to build up in the Kalman filter.
    time.sleep(3)
    while 1:
        check_distance()
        if in_formation:
            # NOTE: THIS IS TEMPORARY.  WHEN IR SENSORS WORK, REMOVE THIS.
            if not dist_b < d - d_error:
                if mac == 1:
                    turn(left, fortyfive)
                if mac == 2:
                    turn(right, fortyfive)
            drive(forw, 0.25)
        elif not in_formation:
            while not in_formation:
                form_up()
            get_bearing()


def initialize_rupert(dist, dist_err, init_rssi, init_var, sens_var, rssi_var):
    global is_leader, in_formation, mac, d, d_error, k_filter_a, k_filter_b
    # Ruperts may assume they begin in formation
    in_formation = True
    # Get our mac address, and check if we are the leader.
    mac = get_mac()
    if mac == 0:
        is_leader = True
    # Distance in cm we require between Ruperts for the formation.
    d = dist
    # error margin for distance
    d_error = dist_err
    # Initialize our Kalman Filters
    k_filter_a = KalmanFilter(init_rssi, init_var, sens_var, rssi_var)
    k_filter_b = KalmanFilter(init_rssi, init_var, sens_var, rssi_var)

    # Begin broadcasting data and receiving distances
    Thread(target=broadcast, args=5)
    Thread(target=receive_rssi, args=())
    # _thread.start_new_thread(broadcast(1))

    # THESE VALUES ARE DUMMY VALUES FOR TESTING WITHOUT ACTUAL RSSI VALUES
    global dist_a, dist_b
    dist_a = 5
    dist_b = 5


k_filter_a = None   # Filter for distance a
k_filter_b = None   # filter for distance b
leader_mac = 0
dist_a = None       # distance from squad member 1/squad leader
dist_b = None       # distance from squad member 2
rssi_values = {}


def receive_distances():
    global dist_a, dist_b, k_filter_a, k_filter_b
    # get a (mac address, rssi value) tuple from another feather.
    rssi_tuple = receive_rssi()
    lock.acquire()
    # matches node a with mac 0, if this Rupert isn't squad leader.
    # if rssi_tuple[0] not in rssi_values:
    #     if rssi_tuple[0] == 0:
    #         leader
    rssi_values[rssi_tuple[0]] = rssi_tuple[1]
    


def check_distance():
    global in_formation
    # Leader checks if it is out of range of both Ruperts.
    if is_leader and (dist_a > d + d_error or dist_b > d + d_error):
        drive(stop, 0)
        in_formation = False
    # Other ruperts check to see if they are out of range of leader.
    elif not is_leader and (dist_a > d + d_error or dist_a < d - d_error):
        drive(stop, 0)
        in_formation = False


def form_up():
    # If out of formation, this is how we get back.
    # Actions depend on mac address of the Rupert.
    global dist_a,dist_b, in_formation
    # Leader doesn't move, it's at the top of the triangle.
    if is_leader:
        drive(stop, 0)
    # Otherwise, other Ruperts get in range of the leader
    else:
        if dist_a > d + d_error or dist_a < d - d_error \
                or dist_b < d - d_error - d_error:
            turn(right, fortyfive)
            drive(forw, 0.25)


def get_bearing():
    global dist_a
    correct_bearing = False
    while not correct_bearing:
        last_d = dist_a
        drive(forw, 0.75)
        if last_d < dist_a:
            correct_bearing = True
        else:
            turn(right, ninety)


main()


