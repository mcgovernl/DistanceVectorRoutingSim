#!/usr/bin/python3

from argparse import ArgumentParser
import os
import sys
import time
import copy
import math
import random
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot
import plotly.graph_objs as go
import networkx as nx


class Simulation:
    def __init__(self,settings):
        self._settings = settings
        self._switches = self.create_switches(settings.switches,settings.links,settings.delay)
        self._links = settings.links
        self._sentvectors = {} #key is where vector should be going and delay, value is list of vectors, !!!might need to add entry in tuple with where it came from
        self._recvectors = {} #key is where vector should be going, value is list of vectors !!!might need to add entry in tuple with where it came from

    def create_switches(self,n,links,delay):
        switches = {}
        for i in range(n):
            switches[i] = Switch(i,links[i],delay[i])
        return switches

    #need to fix the logic so i can animate the edges
    def send_vectors(self):
        for snum,switch in self._switches.items():
            if switch._updated:
                for num in switch._links:
                    if (num,snum,switch._delay) in self._sentvectors:
                        self._sentvectors[(num,snum,switch._delay)].append(copy.deepcopy(switch._vector)) #need to deepcopy to avoid passing a reference to switch classes vector
                    else:
                        self._sentvectors[(num,snum,switch._delay)] = [copy.deepcopy(switch._vector)] #need to deepcopy to avoid passing a reference to switch classes vector
            switch._updated = False

    def recv_vectors(self):
        for num,snum in self._recvectors:
            for vectors in self._recvectors[(num,snum)]:
                for vector in vectors:
                    self._switches[num].update_vector(snum,vector)
        self._recvectors.clear()

    def transport_vectors(self):
        vectors = {}
        for num,snum,delay in self._sentvectors:
            if delay == 0:
                if num in self._recvectors:
                    self._recvectors[(num,snum)].append(copy.deepcopy(self._sentvectors[(num,snum,delay)]))
                else:
                    self._recvectors[(num,snum)] = [copy.deepcopy(self._sentvectors[(num,snum,delay)])]
            else:
                vectors[(num,snum,delay-1)] = self._sentvectors[(num,snum,delay)]
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
        self._vector = {num:(0,num)} #dict dest : dict distance:next hop

    def update_vector(self,rnum,vector):
        #should process and update vector, should set updated if there was an update
        for num in vector:
            dst = vector[num][0] #distance to vector
            nxt = rnum #next hop
            if num not in self._vector:
                self._vector[num] = (dst+1,nxt)
                self._updated = True
            elif self._vector[num][0] > dst+1:
                self._vector[num] = (dst+1,nxt)
                self._updated = True
        return

    def vector_str(self):
        #take the vector and turn it into a nicely formated form for veiwing in plotly
        s = "Vector for Switch "+str(self._num)+"<br>| Sequence Number | Distance | Next Hop |<br>"
        for num in self._vector:
            s += "| "+ str(num) + " | " + str(self._vector[num][0]) +" | "+ str(self._vector[num][1]) + " |<br>"
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
                output += "Switch " + str(num) + " has a cost of " + str(switch._vector[num][0]) + " with next hop " +str(switch._vector[num][1])+"\n"
        output += "Sent vectors:\n"
        for num in self._sentvectors:
            output += "En route to " + str(num) + "\n"
            for vector in self._sentvectors[num]:
                for num in vector:
                    output += "Switch " + str(num) + " has a cost of " + str(vector[num][0]) + " with next hop " +str(vector[num][1])+"\n"
        output += "About to be received vectors:\n"
        for num in self._recvectors:
            output += "To be received by " + str(num) + "\n"
            for vectors in self._recvectors[num]:
                for vector in vectors:
                    for num in vector:
                        output += "Switch " + str(num) + " has a cost of " + str(vector[num][0]) + " with next hop " +str(vector[num][1])+ "\n"
        print(output)

#below is all graphing related functions
def create_graph(settings,state):
    #creates a graph from a network state object
    r = settings.switches #circle radius
    theta = ((2*math.pi)/r) #degree seperation between nodes
    G = nx.Graph()
    for num,switch in state._switches.items():
        x= r*math.cos(num*theta)
        y= r*math.sin(num*theta)
        G.add_node(switch, pos=(x ,y))
        for snum in switch._links:
            G.add_edge(switch,state._switches[snum])
    return G

def create_edge_trace(G,inflight_vectors):
    edge_trace = go.Scatter(
        x=[],
        y=[],
        text = [],
        line=dict(width=3,color='#888'),
        hoverinfo='text',
        mode='lines')

    middle_node_trace = go.Scatter(
    x=[],
    y=[],
    text=[],
    mode='markers',
    hoverinfo='text',
    marker=go.scatter.Marker(
        opacity=0
        )
    )

    for edge in G.edges():
        #need to somehow update text to show sent vector info
        #edge[0] is switch where edge starts
        #edge[1] is switch where edge ends
        x0, y0 = G.node[edge[0]]['pos']
        x1, y1 = G.node[edge[1]]['pos']
        edge_trace['x'] += tuple([x0, x1, None])
        edge_trace['y'] += tuple([y0, y1, None])

        middle_node_trace['x'] += tuple([(x0+x1)/2])
        middle_node_trace['y'] += tuple([(y0+y1)/2])

        text = ""
        key = (edge[0]._num,edge[1]._num,edge[0]._delay)
        key2 = (edge[1]._num,edge[0]._num,edge[1]._delay)
        if key in inflight_vectors:
            vectors = inflight_vectors[key] #vector going from where edge starts to where it ends
            text += sentvector_text(key,vectors)
        if key2 in inflight_vectors:
            vectors2 = inflight_vectors[key2] #vector going from where edge starts to where it ends
            text += sentvector_text(key2,vectors2)
        middle_node_trace['text'] += tuple([text])

    return [edge_trace,middle_node_trace]

def sentvector_text(key,vectors):
        s = ""
        for vector in vectors:
            s += "Vector traveling from Switch "+str(key[1])+" to Switch "+str(key[0])+"<br>| Sequence Number | Distance | Next Hop |<br>"
            for num in vector:
                s += "| "+ str(num) + " | " + str(vector[num][0]) + " | "+str(vector[num][1])+" |<br>"
        return s

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

def create_frame(G,inflight_vectors,t):
    #here G is a networkx graph object
    [edge_trace,middle_node_trace] = create_edge_trace(G,inflight_vectors)
    node_trace = create_node_trace(G)
    frame = go.Frame(data=[node_trace,middle_node_trace,edge_trace],group='nodes',name='nodes at time '+str(t)) #should change code from here, just naming is wrong
    return [frame,node_trace,edge_trace]

def animate(f,edges,nodes):
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
                updatemenus= [{
                                'buttons': [
                                    {
                                        'args': ['nodes', {'frame': {'duration': 1500, 'redraw': False},
                                                 'fromcurrent': True, 'transition': {'duration': 300, 'easing': 'quadratic-in-out'}}],
                                        'label': 'Play',
                                        'method': 'animate'
                                    },
                                    {
                                        'args': [[None], {'frame': {'duration': 0, 'redraw': False}, 'mode': 'immediate',
                                        'transition': {'duration': 0}}],
                                        'label': 'Pause',
                                        'method': 'animate'
                                    }
                                ],
                                'direction': 'left',
                                'pad': {'r': 10, 't': 87},
                                'showactive': False,
                                'type': 'buttons',
                                'x': 0,
                                'xanchor': 'right',
                                'y': -0.1,
                                'yanchor': 'top'
                            }])
    slider_dict = { #create slider dict
    'active': 0,
    'yanchor': 'bottom',
    'xanchor': 'left',
    'currentvalue': {
        'font': {'size': 20},
        'prefix': 'Time Step: ',
        'visible': True,
        'xanchor': 'left'
    },
    'transition': {'duration': 300, 'easing': 'cubic-in-out'},
    'pad': {'b': 10, 't': 20},
    'len': 0.9,
    'x': 0,
    'y': -0.25,
    'steps': []
    }
    for frame in f:
        slider_dict['steps'].append( {
                        'method': 'animate',
                        'label': frame['name'][-1],
                        'args': [[frame['name']],{'frame': {'duration': 1500, 'redraw': False},
                             'mode': 'immediate'}
                        ]
                    })
    lay['sliders'] = [slider_dict]
    fig = go.Figure(data=[edges,edges,nodes,nodes],frames=f, layout=lay)
    plot(fig,filename='dvr_graph.html')

def arg_checks(settings):
    #run tests to make sure arguements match up
    #returns True if passed or returns a error string if failed
    num_switches = settings.switches
    links = settings.links
    delay = settings.delay
    err = ""
    if len(links) != num_switches:
        err += "ERROR:\nNumber of switches and number of link specifications do not match\n"
    if len(delay) != num_switches:
        err += "ERROR:\nNumber of switches and number of delay specifications do not match\n"
    if len(links) != len(delay):
        err+= "ERROR:\nNumber of links and number of delay specifications do not match\n"

    for i in range(len(links)):
        link = links[i]
        if i in link:
            err+="ERROR:\nSwitch cannot have a link to itself\n"
            err+= "Error found in link specification "+str(i)+"\n"

    for num in delay:
        if num < 0:
            err+="ERROR:\nDelay cannot be negative\n"

    if err != "":
        return err
    else:
        return True

def main():
    # Parse arguments
    arg_parser = ArgumentParser(description='Distance Vector routing simulator')
    arg_parser.add_argument('--switches', dest='switches', action='store',
            type=int, default=7, help='Number of switches in network')
    arg_parser.add_argument('--links', dest='links', action='store',
            type=str, default="[1,2],[0,2,4],[0,1,3],[2,4,6],[1,3,5],[4,6],[3,5]" , help='2D list of switch connections') #defaults
    arg_parser.add_argument('--steps', dest='steps', action='store',
            type=int, default=10, help="How many time steps to simulate")
    arg_parser.add_argument('--delay', dest='delay', action='store',
            type=str, default="[0,0,0,0,0,0,0]", help="List of delay in sending for each switch")
    settings = arg_parser.parse_args()
    settings.links = eval(settings.links)
    settings.delay = eval(settings.delay)


    if arg_checks(settings) == True:
        # Create simulation
        simulation = Simulation(settings)

        #create frame list for animation later
        frames = []

        # Run simulation for specified number of steps
        for t in range(settings.steps):
            state = simulation.step(t)
            #state.display()
            G = create_graph(settings,state) #create a graph of the netork each time step
            graph_frames = create_frame(G,state._sentvectors,t) #create a frame of the graph each time step
            frames.append(graph_frames[0])
            if t == 0: #set intial data so we dont have to redraw it
                nodes = graph_frames[1]
                nodes['hoverinfo'] = 'skip'
                edges = graph_frames[2]
                edges['hoverinfo'] = 'skip'


        animate(frames,edges,nodes)
    else:
        print(arg_checks(settings))


if __name__ == '__main__':
    main()
