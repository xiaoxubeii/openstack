'''
Created on May 19, 2014

@author: xiaoxubeii
'''
from kombu import Exchange, Queue

exchange = Exchange('test', type='direct')
queue = Queue('q_test', exchange, route_key='test')
