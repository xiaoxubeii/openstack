'''
Created on May 13, 2014

@author: xiaoxubeii
'''
from kombu import Connection  
from kombu.messaging import Producer  
from entity import task_exchange  
from kombu.transport.base import Message  
  
connection = Connection('amqp://guest:guest@localhost:5672//')  
channel = connection.channel()  
  
message = Message(channel, body='Hello Kombu')  
  
# produce  
producer = Producer(channel, exchange=task_exchange)  
producer.publish(message.body, routing_key='suo_piao')
