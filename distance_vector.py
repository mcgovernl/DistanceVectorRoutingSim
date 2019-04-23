#!/usr/bin/python3

from argparse import ArgumentParser #look at proj02 for help using this
import os
import sys
import time
import copy
import random
import plotly.offline as pyoffline
import plotly.plotly as py
import plotly.graph_objs as go
import networkx as nx

#py = plotly.plotly("SammyButts", "xWKnYKgB6AiZiZ7U9Ql1") used for plotting online

class Simulation:
    def __init__(self,settings):
        self._settings = settings
        self._switches = self.create_switches(settings.switches,settings.links,settings.delay)
        self._links = settings.links
        self._sentvectors = {} #key is where vector should be going and delay, value is list of vectors, !!!might need to add tird entry in tuple with where it came from
        self._recvectors = {} #key is where vector should be going, value is list of vectors

    def create_switches(self,n,links,delay):
        switches = {}
        for i in range(n):
            switches[i] = Switch(i,links[i],delay[i])
        return switches

    def send_vectors(self):
        for snum,switch in self._switches.items():
            if switch._updated:
                for num in switch._links:
                    if (num,switch._delay) in self._sentvectors:
                        self._sentvectors[(num,switch._delay)].append(copy.deepcopy(switch._vector)) #need to deepcopy to avoid passing a reference to switch classes vector
                    else:
                        self._sentvectors[(num,switch._delay)] = [copy.deepcopy(switch._vector)] #need to deepcopy to avoid passing a reference to switch classes vector
            switch._updated = False

    def recv_vectors(self):
        for num in self._recvectors:
            for vector in self._recvectors[num]:
                    self._switches[num].update_vector(vector)
        self._recvectors.clear()

    def transport_vectors(self):
        vectors = {}
        for num,delay in self._sentvectors:
            if delay == 0:
                self._recvectors[num] = self._sentvectors[(num,delay)]
            else:
                vectors[(num,delay-1)] = self._sentvectors[(num,delay)]
        self._sentvectors.clear()
        self._sentvectors = vectors

    def step(self,t):
        #execute simulation steps
        self.recv_vectors()
        self.transport_vectors()
        self.send_vectors()
        return NetworkState(t,self._switches,self._sentvectors,self._recvectors)

class Switch:
    def __init__(self,num,links,delay):
        self._num = num
        self._links = links
        self._updated = True
        self._delay = delay
        self._vector = {num:0}

    def update_vector(self, vector):
        #should process and update vector, should set updated if there was an update
        for num in vector:
            if num not in self._vector:
                self._vector[num] = vector[num]+1
                self._updated = True
            elif self._vector[num] > vector[num]+1:
                self._vector[num] = vector[num]+1
                self._updated = True
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

def create_graph(settings,state):
    #creates a graph from a network state object
    G = nx.Graph()
    for num,switch in state._switches.items():
        G.add_node(switch, pos=(num ,num % 2)) #need to set node pos to create traces, setting randomly for time being
        for snum in switch._links:
            G.add_edge(switch,state._switches[snum]) #adds nodes improperly
    return G

def create_edge_trace(G):
    edge_trace = go.Scatter(
        x=[],
        y=[],
        line=dict(width=1,color='#888'),
        hoverinfo='none',
        mode='lines')
    for edge in G.edges():
        #dont understand how this works
        x0, y0 = G.node[edge[0]]['pos']
        x1, y1 = G.node[edge[1]]['pos']
        edge_trace['x'] += tuple([x0, x1, None])
        edge_trace['y'] += tuple([y0, y1, None])

    return edge_trace

def create_node_trace(G):
    node_trace = go.Scatter()

def draw_graph(G):
    #here G is a networkx graph object
    edge_trace = create_edge_trace(G)
    node_trace = create_node_trace(G)
    fig = go.Figure(data=[edge_trace,node_trace]) #can add layout = go.Layout()
    pyoffline.plot(fig,filename='dvr_graph')

def main():
    # Parse arguments
    arg_parser = ArgumentParser(description='Distance Vector routing simulator')
    arg_parser.add_argument('--switches', dest='switches', action='store',
            type=int, default=7, help='Number of switches in network')
    arg_parser.add_argument('--links', dest='links', action='store',
            type=list, default=[[1,2],[0,2,4],[0,1,3],[2,4,6],[1,3,5],[4,6],[3,5]], help='2D list of switch connections') #defaults
    arg_parser.add_argument('--steps', dest='steps', action='store',
            type=int, default=10, help="How many time steps to simulate")
    arg_parser.add_argument('--delay', dest='delay', action='store',
            type=list, default=[0,0,0,0,0,0,0], help="List of delay in sending for each switch")
    settings = arg_parser.parse_args()

    # Create simulation
    simulation = Simulation(settings)

    # Run simulation for specified number of steps
    for t in range(settings.steps):
        state = simulation.step(t)
        #state.display()
        G = create_graph(settings,state)
        draw_graph(G)



if __name__ == '__main__':
    main()
