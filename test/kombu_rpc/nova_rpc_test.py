'''
Created on May 27, 2014

@author: xiaoxubeii
'''
import kombu
import kombu.entity
import kombu.messaging
import uuid
import itertools

class Connection(object):
    def __init__(self):
        self.connection = kombu.BrokerConnection(hostname='xiaoxubeii', userid='guest',
                                           password='guest', virtual_host='/',
                                           port='5672', transport='pyamqp')
        self.channel = self.connection.channel()

    def create_consumer(self, topic, callback, style='topic', msg_id=None):
        self.consumer = Consumer(self.channel, topic, callback, style, msg_id) 
        
    def iterconsume(self):
        while True:
            self.consumer.consume()
            for iteration in itertools.count(0):
                yield self.connection.drain_events()

    def consume(self):
        it = self.iterconsume()
        while True:
            try:
                it.next()
            except StopIteration:
                return
        
    def send(self, topic, msg, style='topic'):
        publisher = Publisher(self.channel, topic, style)
        publisher.send(msg)
        
    def close(self):
        self.connection.release()
        
class Consumer(object):
    def __init__(self, channel, topic, callback, style='topic', msg_id=None):
        self.channel = channel
        self.callback = callback
        if style == "topic":
            self.exchange = kombu.entity.Exchange("testxxxx", type="topic",
                                                  durable=False, auto_delete=False)
            self.queue = kombu.entity.Queue(name=topic, exchange=self.exchange, routing_key=topic,
                                            channel=self.channel, durable=False,
                                            auto_delete=False, exclusive=False)
        if style == 'direct':
            self.exchange = kombu.entity.Exchange(name=msg_id, type="direct",
                                                  durable=False, auto_delete=True)
            self.queue = kombu.entity.Queue(name=msg_id, exchange=self.exchange, routing_key=topic,
                                            channel=self.channel, durable=False,
                                            auto_delete=True, exclusive=True)
        
        self.queue.declare()
    
    def consume(self):
        def _callback(raw_message):
            message = self.channel.message_to_python(raw_message)
            self.callback(message.payload)
            message.ack()
        self.queue.consume(callback=_callback)

class Publisher(object):
    def __init__(self, channel, topic, style="topic", msg_id=None):
        self.channel = channel
        if style == 'topic':
            self.exchange = kombu.entity.Exchange(name="testxxxx", type="topic", durable=False, auto_delete=False)
            self.producer = kombu.messaging.Producer(channel=self.channel, exchange=self.exchange,
                                                     routing_key=topic)
        if style == 'direct':
            self.exchange = kombu.entity.Exchange(name=msg_id, type="direct", durable=False, auto_delete=True)
            self.producer = kombu.messaging.Producer(channel=self.channel, exchange=self.exchange,
                                                     routing_key=topic)
        
    def send(self, msg):
        self.producer.publish(msg)
        
class Waiter(object):
    def __init__(self, connection):
        self._connection = connection
        self._iterator = self._connection.iterconsume()
        self._result = None
        self._done = False
        self._got_ending = False
        
    def done(self):
        self._done = True
        self._iterator.close()
        self._iterator = None
        self._connection.close()
    
    def __call__(self, data):
        if data:
            self._result = data
            self._got_ending = True
            
    def __iter__(self):
        if self._done:
            raise StopIteration
        while True:
            self._iterator.next()
            if self._got_ending:
                result = self._result
                yield result
                self.done()
                raise StopIteration
        
def cast(msg):
    connection = Connection()
    connection.send('test', msg)
    
def call(msg):
    msg_id = uuid.uuid4().hex
    msg = eval(msg)
    msg.update({'_msg_id':msg_id})
    msg = str(msg)
    
    connection = Connection()
    wait_msg = Waiter(connection)
    
    connection.create_consumer(msg_id, wait_msg, 'direct', msg_id)
    connection.send('test', msg)
    
    rv = list(wait_msg)
    
    if not rv:
        return
    return rv[-1]

if __name__ == '__main__':
    connection = Connection()
    def echo(value):
        msg = eval(value)
        msg_id = msg.pop("_msg_id", None)
        if msg_id:
            conn = Connection()
            conn.send(msg_id, 'some message info here', style='direct')
        print 'message:%s' % value
        
    connection.create_consumer('test', echo, 'topic')
    connection.consume()
