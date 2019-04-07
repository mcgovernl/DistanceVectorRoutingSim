#!/usr/bin/python3

from argparse import ArgumentParser #look at proj02 for help using this
import os
import sys
import time
import bisect #not sure we need this one

class Simulation:
    def __init__(self,settings):
        self._settings = settings
        self._switches = self.create_switches(settings.switches,settings.links)
        self._links = settings.links
        self._sentvectors = {} #key is where vector should be going, value is list of vectors
        self._recvectors = {} #key is where vector should be going, value is list of vectors

    def create_switches(self,n,links):
        switches = {}
        for i in range(n):
            switches[i] = Switch(i,links[i])
        return switches

    def send_vectors(self):
        for switch in self._switches:
            if self._switches[switch]._updated:
                for num in self._switches[switch]._links:
                    if num in self._sentvectors:
                        self._sentvectors[num].append(self._switches[switch]._vector)
                    else:
                        self._sentvectors[num] = [self._switches[switch]._vector]
            self._switches[switch]._updated = False

    def recv_vectors(self):
        for num in self._recvectors:
            for vector in self._recvectors[num]:
                    print("Self._recvectors = " +str(self._recvectors))
                    self._switches[num].update_vector(vector)
        self._recvectors.clear()

    def transport_vectors(self):
        for num in self._sentvectors:
            self._recvectors[num] = self._sentvectors[num]
        self._sentvectors.clear()

    def step(self,t):
        #execute simulation steps
        self.recv_vectors()
        self.transport_vectors()
        self.send_vectors()
        return NetworkState(t,self._switches,self._sentvectors,self._recvectors)

class Switch:
    def __init__(self,num,links):
        self._num = num
        self._links = links
        self._updated = True
        self._vector = {num:0}

    def update_vector(self, vector):
        #should process and update vector, should set updated if there was an update
        print("Before update for Switch "+str(self._num)+": "+str(self._vector))
        print("Vector handed to switch: "+str(vector))
        for switch in vector:
            if switch not in self._vector:
                self._vector[switch] = vector[switch]+1
                self._updated = True
            elif self._vector[switch] > vector[switch]+1:
                self._vector[switch] = vector[switch]+1
                self._updated = True
        print("After update " +str(self._vector))
        return

class NetworkState:
    def __init__(self,t,switches,sentvectors,recvectors):
        self._switches = switches
        self._sentvectors = sentvectors
        self._recvectors = recvectors
        self._t = t

    def display(self):
        output = "Time: "+str(self._t)+"\n"
        for switch in self._switches:
            switch = self._switches[switch]
            output += "Switch " + str(switch._num) + "'s vectors: \n"
            for num in switch._vector:
                output += "Switch " + str(num) + " has a cost of " + str(switch._vector[num]) + "\n"
        output += "Sent vectors:\n"
        for num in self._sentvectors:
            output += "En route to " + str(num) + "\n"
            for vector in self._sentvectors[num]:
                for num in vector:
                    output += "Switch " + str(num) + " has a cost of " + str(vector[num]) + "\n"
        output += "About to be received vectors:\n"
        for num in self._recvectors:
            output += "En route to " + str(num) + "\n"
            for vector in self._recvectors[num]:
                for num in vector:
                    output += "Switch " + str(num) + " has a cost of " + str(vector[num]) + "\n"
        print(output)


def main():
    # Parse arguments
    arg_parser = ArgumentParser(description='Distance Vector routing simulator')
    arg_parser.add_argument('--switches', dest='switches', action='store',
            type=int, default=7, help='Number of switches in network')
    arg_parser.add_argument('--links', dest='links', action='store',
            type=list, default=[[1,2],[0,2,4],[0,1,3],[2,4,5],[1,4,6],[4,5],[4,6]], help='2D list of switch connections') #defaults
    arg_parser.add_argument('--steps', dest='steps', action='store',
            type=int, default=10, help="How many time steps to simulate")
    settings = arg_parser.parse_args()

    # Create simulation
    simulation = Simulation(settings)

    # Run simulation for specified number of steps
    for t in range(settings.steps):
        state = simulation.step(t)
        state.display()

if __name__ == '__main__':
    main()
