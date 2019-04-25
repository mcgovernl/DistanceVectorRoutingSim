#!/usr/bin/python3

from argparse import ArgumentParser #look at proj02 for help using this
import os
import sys
import time
import copy
import random
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot
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

    def vector_str(self):
        #take the vector and turn it into a nicely formated form for veiwing in plotly
        s = "Vector for Switch "+str(self._num)+"<br>| Sequence Number | Distance |<br>"
        for num in self._vector:
            s += "| "+ str(num) + " | " + str(self._vector[num]) + " |<br>"
        return s

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
        G.add_node(switch, pos=(num ,num % 2)) #need to set node pos to create traces, need some way to standardize node placement
        for snum in switch._links:
            G.add_edge(switch,state._switches[snum])
    return G

def create_edge_trace(G):
    edge_trace = go.Scatter(
        x=[],
        y=[],
        text = [],
        line=dict(width=3,color='#888'),
        hoverinfo='text',
        mode='lines')

    for edge in G.edges():
        #dont understand how this works
        x0, y0 = G.node[edge[0]]['pos']
        x1, y1 = G.node[edge[1]]['pos']
        edge_trace['x'] += tuple([x0, x1, None])
        edge_trace['y'] += tuple([y0, y1, None])

    return edge_trace

def create_node_trace(G):
    node_trace = go.Scatter(
    x=[],
    y=[],
    text=[],
    mode='markers',
    hoverinfo='text',
    marker=dict(
        showscale=False, #set true to see side scale based on colorbar
        # colorscale options
        #'Greys' | 'YlGnBu' | 'Greens' | 'YlOrRd' | 'Bluered' | 'RdBu' |
        #'Reds' | 'Blues' | 'Picnic' | 'Rainbow' | 'Portland' | 'Jet' |
        #'Hot' | 'Blackbody' | 'Earth' | 'Electric' | 'Viridis' |
        colorscale='YlGnBu',
        reversescale=True,
        color=[],
        size=100,
        colorbar=dict(
            thickness=15,
            title='Node Connections',
            xanchor='left',
            titleside='right'
        ),
        line=dict(width=2)))

    for node in G.nodes():
        x, y = G.node[node]['pos']
        node_trace['x'] += tuple([x])
        node_trace['y'] += tuple([y])
        node_trace['marker']['color']+=tuple([10]) #set node color
        node_trace['text']+=tuple([node.vector_str()]) #set vector str as info

    return node_trace

def create_frame(G,t):
    #here G is a networkx graph object
    edge_trace = create_edge_trace(G)
    node_trace = create_node_trace(G)
    edge_frame = go.Frame(data=[edge_trace],group='edges',name='edges at time '+str(t))
    node_frame = go.Frame(data=[node_trace],group='nodes',name='nodes at time '+str(t))
    return [node_frame,edge_frame]

def animate(f):
    #takes list of frames as arg creates layout and animation
    lay = go.Layout(
                title='<br>Distance Vector Routing Graph',
                titlefont=dict(size=16),
                showlegend=False,
                hovermode='closest',
                margin=dict(b=20,l=5,r=5,t=40),
                annotations=[],
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                updatemenus= [{'type': 'buttons',
                           'buttons': [{'label': 'Play',
                                        'method': 'animate',
                                        'args': ['nodes']}]}])
    fig = go.Figure(data=[{'x': [0, 1], 'y': [0, 1]}],frames=f, layout=lay) #can add layout = go.Layout()
    plot(fig,filename='dvr_graph.html')

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

    #create frame list for animation later
    frames = []

    # Run simulation for specified number of steps
    for t in range(settings.steps):
        state = simulation.step(t)
        #state.display()
        G = create_graph(settings,state) #create a graph of the netork each time step
        graph_frames = create_frame(G,t) #create a frame of the graph each time step
        frames.extend(graph_frames)

    animate(frames)


if __name__ == '__main__':
    main()
