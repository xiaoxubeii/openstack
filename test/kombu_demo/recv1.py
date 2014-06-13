'''
Created on May 19, 2014

@author: xiaoxubeii
'''
from kombu import Connection
from kombu.messaging import Consumer
from entity1 import queue

connection = Connection("amqp://guest:guest@xiaoxubeii:5672//")
channel = connection.channel()

def test(body, message):
    print body
    message.ack()
    
consumer = Consumer(channel, queue)
consumer.register_callback(test)
consumer.consume()

while True:
    connection.drain_events()
