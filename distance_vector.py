#!/bash/bin/python3

from argparse import ArgumentParser #look at proj02 for help using this
import os
import sys
import time
import bisect #not sure we need this one

class Simulation:
    def __init__(self,settings):
        self._settings = settings
        self._switches = create_switches(settings.switches,settings.links,settings.hosts)
        self._links = settings.links
        self._hosts = settings.hosts

    def create_switches(n,links,hosts):
        switches = {}
        for i in range(n):
            switches[i+1] = Switch(i+1,links,hosts)
        return switches

    def step(self,t):
        #plan order of simulation steps here



class NetworkState:
    def __init__(self,switches):

class Switch:
    def __init__(self,num,links,hosts):
        self._num = num
        self._links = links[num-1]
        self._hosts = hosts[num-1]
        self._fwdtable = []

def main():
    # Parse arguments
    arg_parser = ArgumentParser(description='Distance Vector routing simulator')
    arg_parser.add_argument('--switches', dest='switches', action='store',
            type=int, default=3, help='Number of switches in network')
    arg_parser.add_argument('--links', dest='links', action='store',
            type=list, default=[[2,3],[3],[1,2]], help='2D list of switch connections')
    arg_parser.add_argument('--hosts', dest='hosts', action='store',
            type=list, default=[[1],[2],[3]], help='2D list of host connections')
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
