#!/usr/bin/env python
# coding=utf8
# kombu_rpc.py
# Remote Process Call
 
 
import kombu
import kombu.entity
import kombu.messaging
import kombu.connection
import uuid
import itertools
 
class Connection(object):
    """连接类,具体参考nova中的代码,这里只提取出关键部分代码"""
    def __init__(self):
        self.connection = kombu.connection.BrokerConnection(transport='pyamqp', hostname='localhost',
                                             port=5672,
                                             userid='guest',
                                             password='guest',
                                             virtual_host='/')
        self.channel = self.connection.channel()
         
    def create_consumer(self, topic, callback, style='topic', msg_id=None):
        '''创建consumer方法
        nova中对Consumer基类进行了继承分为topic,direct,fouout三个子类
        这里为了方便说明提供了style参数进行区分
        '''
        self.consumer = Consumer(self.channel, topic, callback, style, msg_id)
     
    def iterconsume(self):
        '''创建迭代器,作用是为了方便在某些情况下跳出循环,这里主要体现在call方法调用时'''
        while True:
            self.consumer.consume()
            for iteration in itertools.count(0):
                print 1
                yield self.connection.drain_events()
     
    def consume(self):
        it = self.iterconsume()
        while True:
            try:
                it.next()
            except StopIteration:
                return
 
    def send(self, topic, msg, style='topic'):
        '''发布信息的方法,同样在nova中分为direct,topic,fanout send三种方式,这里进行简化'''
        publisher = Publisher(self.channel, topic, style)
        publisher.send(msg)
     
    def close(self):
        self.connection.release()
 
 
class Consumer(object):
 
    def __init__(self, channel, topic, callback, style='topic', msg_id=None):
        '''根据style类型来决定exchang以及queue的生成类型,nova中分为三个子类来实现'''
        self.channel = channel
        self.callback = callback
        if style == 'topic':
            self.exchange = kombu.entity.Exchange(name='test-1987',
                                                  type='topic',
                                                  durable=False,
                                                  auto_delete=False)
            self.queue = kombu.entity.Queue(name=topic,
                                        exchange=self.exchange,
                                        routing_key=topic,
                                        channel=channel,
                                        durable=False,
                                        auto_delete=False,
                                        exclusive=False)
        elif style == 'direct':
            self.exchange = kombu.entity.Exchange(name=msg_id,
                                                  type='direct',
                                                  durable=False,
                                                  auto_delete=True)
            self.queue = kombu.entity.Queue(name=msg_id,
                                        exchange=self.exchange,
                                        routing_key=msg_id,
                                        channel=channel,
                                        durable=False,
                                        auto_delete=True,
                                        exclusive=True)
        self.queue.declare()
         
    def consume(self):
        '''注册consumer,注意这里的callback函数'''
        def _callback(raw_message):
            message = self.channel.message_to_python(raw_message)
            self.callback(message.payload)
            message.ack()
        self.queue.consume(callback=_callback)
 
 
class Publisher(object):
 
    def __init__(self, channel, topic, style='topic', msg_id=None):
        self.channel = channel
        if style == 'topic':
            self.exchange = kombu.entity.Exchange(name='test-1987',
                                                  type='topic',
                                                  durable=False,
                                                  auto_delete=False)
            self.producer = kombu.messaging.Producer(exchange=self.exchange,
                                        routing_key=topic,
                                        channel=channel)
        elif style == 'direct':
            self.exchange = kombu.entity.Exchange(name=msg_id,
                                                  type='direct',
                                                  durable=False,
                                                  auto_delete=True)
            self.producer = kombu.messaging.Producer(exchange=self.exchange,
                                        routing_key=topic,
                                        channel=channel)
     
    def send(self, msg):
        '''发送消息'''
        self.producer.publish(msg)
 
     
class Waiter(object):
    """当使用call模式请求消息返回值信息的注册函数类
    当消息回传回来的时候,销毁创建的临时consumer
    """
    def __init__(self, conn):
        self._connection = conn
        self._iterator = conn.iterconsume()
        self._result = None
        self._done = False
        self._got_ending = False
     
    def done(self):
        if self._done:
            return
        self._done = True
        self._iterator.close()
        self._iterator = None
        self._connection.close()
         
         
    def __call__(self, data):
        '''消息回传接收到的时候,这里对nova代码进行了简化,nova中加了一层判断'''
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
             
 
def call(msg):
    '''发送消息同时等待远程返回值
    那我们考虑下这里面的整个流程：
    1.首先对面已有一个consumer在那里，它定义了自己的callback方法
    2.那我们要发出信息就要生成一个publisher将消息发出去
    3.同时需要在consumer处理完消息回发回来时接收到,这就需要生成一个临时的consumer(与msg_id密切相关)
    4.远程consumer,接受到消息发现是需要回发的(msg_id),需要生成一个publisher扔回消息
    5.接收到远程回复的消息后做一些清理工作
    '''
    msg_id = uuid.uuid4().hex
    msg = eval(msg)
    msg.update({'_msg_id':msg_id})
    msg = str(msg)
 
    conn = Connection()
    wait_msg = Waiter(conn)
    conn.create_consumer(msg_id, wait_msg, 'direct', msg_id)
    conn.send('network', msg)
     
    rv = list(wait_msg)
    if not rv:
        return
    return rv[-1]
 
def cast(msg):
    '''只发送消息不等待远程执行结果'''
    conn = Connection()
    conn.send('network', msg)
 
if __name__ == '__main__':
    conn = Connection()
    def echo(value):
        msg = eval(value)
        msg_id = msg.pop('_msg_id', None)
        if msg_id:
            conn = Connection()
            conn.send(msg_id, 'some message info here', style='direct')
        print 'message: %s' % value
 
    conn.create_consumer('network', echo)
    conn.consume()
