#!/usr/bin/env python
# coding: utf-8
# Copyright (c) 2019 Abram Hindle, Shu-Jun Pierre Lin
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import flask
from flask import Flask, request
from flask_sockets import Sockets
import gevent
from gevent import queue
import time
import json
import os

app = Flask(__name__)
sockets = Sockets(app)
app.debug = True

class World:
    def __init__(self):
        self.clear()
        # we've got listeners now!
        self.listeners = list()
        
    def add_set_listener(self, listener):
        self.listeners.append( listener )

    def update(self, entity, key, value):
        entry = self.space.get(entity,dict())
        entry[key] = value
        self.space[entity] = entry
        self.update_listeners( entity )

    def set(self, entity, data):
        self.space[entity] = data
        self.update_listeners( entity )

    def update_listeners(self, entity):
        '''update the set listeners'''
        for listener in self.listeners:
            listener(entity, self.get(entity))

    def clear(self):
        self.space = dict()

    def get(self, entity):
        return self.space.get(entity,dict())
    
    def world(self):
        return self.space

# https://github.com/abramhindle/WebSocketsExamples/blob/master/broadcaster.py
# Credit: Abram Hindle (https://github.com/abramhindle)
gevents = list()
clients = list()

# https://github.com/abramhindle/WebSocketsExamples/blob/master/broadcaster.py
# Credit: Abram Hindle (https://github.com/abramhindle)
def send_all(msg):
    for client in clients:
        client.put( msg )

# https://github.com/abramhindle/WebSocketsExamples/blob/master/broadcaster.py
# Credit: Abram Hindle (https://github.com/abramhindle)
def send_all_json(obj):
    send_all( json.dumps(obj) )

# https://github.com/abramhindle/WebSocketsExamples/blob/master/broadcaster.py
# Credit: Abram Hindle (https://github.com/abramhindle)
class Client:
    def __init__(self):
        self.queue = queue.Queue()

    def put(self, v):
        self.queue.put_nowait(v)

    def get(self):
        return self.queue.get()

myWorld = World()        

def set_listener( entity, data ):
    ''' do something with the update ! '''

myWorld.add_set_listener( set_listener )
        
@app.route('/')
def hello():
    '''Return something coherent here.. perhaps redirect to /static/index.html '''
    # https://github.com/abramhindle/WebSocketsExamples/blob/master/broadcaster.py
    # Credit: Abram Hindle (https://github.com/abramhindle)
    return flask.redirect("/static/index.html")

def read_ws(ws,client):
    '''A greenlet function that reads from the websocket and updates the world'''
    # XXX: TODO IMPLEMENT ME
    # https://github.com/abramhindle/WebSocketsExamples/blob/master/broadcaster.py
    # Credit: Abram Hindle (https://github.com/abramhindle)
    try:
        while True:
            msg = ws.receive()
            print("WS RECV: %s" % msg)
            #msg is {"X0": {"x": 0, "y": 0}}

            #packet is {'X0': {'x': 0, 'y': 0}}

            if (msg is not None):
                packet = json.loads(msg)
                #Note that packet is a dict
                send_all_json(packet)
                # https://stackoverflow.com/questions/2733813/iterating-through-a-json-object
                # Credit: tzot (https://stackoverflow.com/users/6899/tzot)
                for entity, data in packet.items():
                    myWorld.set(entity, data)
            else:
                break
    except:
        '''Done'''

@sockets.route('/subscribe')
def subscribe_socket(ws):
    '''Fufill the websocket URL of /subscribe, every update notify the
       websocket and read updates from the websocket '''
    # XXX: TODO IMPLEMENT ME
    # https://github.com/abramhindle/WebSocketsExamples/blob/master/broadcaster.py
    # Credit: Abram Hindle (https://github.com/abramhindle)
    client = Client()
    clients.append(client)
    g = gevent.spawn( read_ws, ws, client)
    #print("Subscribing")
    try:
        while True:
            msg = client.get()
            #print("Got a message!")
            ws.send(msg)
    except Exception as e:
        print("WS Error %s" % e)
    finally:
        clients.remove(client)
        gevent.kill(g)



# I give this to you, this is how you get the raw body/data portion of a post in flask
# this should come with flask but whatever, it's not my project.
def flask_post_json():
    '''Ah the joys of frameworks! They do so much work for you
       that they get in the way of sane operation!'''
    if (request.json != None):
        return request.json
    elif (request.data != None and request.data.decode("utf8") != u''):
        return json.loads(request.data.decode("utf8"))
    else:
        return json.loads(request.form.keys()[0])

@app.route("/entity/<entity>", methods=['POST','PUT'])
def update(entity):
    '''update the entities via this interface'''
    # https://github.com/pslin1/CMPUT404-assignment-ajax/blob/master/server.py
    # Credit: pslin1 (https://github.com/pslin1)
    data = flask_post_json()
    for key, value in data.items():
        myWorld.update(entity, key, value)
    #How do we return the updated entity?**
    #https://stackoverflow.com/questions/34057851/python-flask-typeerror-dict-object-is-not-callable/34057946
    #Credit: davidism (https://stackoverflow.com/users/400617/davidism)
    return jsonify(myWorld.get(entity))

@app.route("/world", methods=['POST','GET'])    
def world():
    '''you should probably return the world here'''
    # https://github.com/pslin1/CMPUT404-assignment-ajax/blob/master/server.py
    # Credit: pslin1 (https://github.com/pslin1)
    return jsonify(myWorld.world())

@app.route("/entity/<entity>")    
def get_entity(entity):
    '''This is the GET version of the entity interface, return a representation of the entity'''
    # https://github.com/pslin1/CMPUT404-assignment-ajax/blob/master/server.py
    # Credit: pslin1 (https://github.com/pslin1)
    #https://stackoverflow.com/questions/34057851/python-flask-typeerror-dict-object-is-not-callable/34057946
    #Credit: davidism (https://stackoverflow.com/users/400617/davidism)
    return jsonify(myWorld.get(entity))


@app.route("/clear", methods=['POST','GET'])
def clear():
    '''Clear the world out!'''
    # https://github.com/pslin1/CMPUT404-assignment-ajax/blob/master/server.py
    # Credit: pslin1 (https://github.com/pslin1)
    myWorld.clear()
    #https://stackoverflow.com/questions/34057851/python-flask-typeerror-dict-object-is-not-callable/34057946
    #Credit: davidism (https://stackoverflow.com/users/400617/davidism)
    return jsonify(myWorld.world())



if __name__ == "__main__":
    ''' This doesn't work well anymore:
        pip install gunicorn
        and run
        gunicorn -k flask_sockets.worker sockets:app
    '''
    app.run()
