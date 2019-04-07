#!/bash/bin/python3

from argparse import ArgumentParser #look at proj02 for help using this
import os
import sys
import time
import bisect #not sure we need this one

class Simulation:
    def __init__(self,settings):
        self._settings = settings
        self._switches = create_switches(settings.switches,settings.links)
        self._links = settings.links
        self._inflightvectors = {} #key is where vector should be going, value is list of vectors

    def create_switches(n,links):
        switches = {}
        for i in range(n):
            switches[i] = Switch(i,links[i])
        return switches

    def send_vectors():
        for switch in switches:
            if switch._updated:
                for num in switch._links:
                    if self._inflightvectors.has_key(num):
                        self._inflightvectors[num].append(switch._vector)
                    else:
                        self._inflightvectors[num] = [switch._vector]
            switch._updated = False

    def recv_vectors():
        for num in self._inflightvectors:
            for vector in self._inflightvectors[num]:
                self._switches[num].update_vector(vector)



    def step(self,t):
        #plan order of simulation steps here
        recv_vectors()
        send_vectors()



class Switch:
    def __init__(self,num,links):
        self._num = num
        self._links = links
        self._updated = True
        self._vector = [[num,0]]

    def update_vector(vector):
        #should process and update vector, should set updated if there was an update
        return None

class NetworkState:
    def __init__(self,switches,inflightvectors):

def main():
    # Parse arguments
    arg_parser = ArgumentParser(description='Distance Vector routing simulator')
    arg_parser.add_argument('--switches', dest='switches', action='store',
            type=int, default=3, help='Number of switches in network')
    arg_parser.add_argument('--links', dest='links', action='store',
            type=list, default=[[2,3],[3],[1,2]], help='2D list of switch connections')
    arg_parser.add_argument('--steps', dest='steps', action='store',
            type=int, default=10, help="How many time steps to simulate")
    arg_parser.add_argument('--speed', dest='speed', action='store',
            type=float, default=-1, help="Speed at which to display")
    settings = arg_parser.parse_args()

    # Create simulation
    simulation = Simulation(settings)

    # Run simulation for specified number of steps
    for t in range(settings.steps):
        state = simulation.step(t)

if __name__ == '__main__':
    main()
