'''
Created on May 19, 2014

@author: xiaoxubeii
'''
from kombu import Connection
from kombu.messaging import Producer
from entity1 import exchange
#from kombu.transport.base import Message

connection = Connection("amqp://guest:guest@xiaoxubeii")
channel = connection.channel()
#message = Message(channel, body='hi, i am a test')
producer = Producer(channel, exchange=exchange)
producer.publish('hi, i am a test', route_key='test')
