from amqplib import client_0_8 as amqp

conn = amqp.Connection(host="xiaoxubeii:5672", userid="guest", password="guest", virtual_host="/", insist=False)
chan = conn.channel()

chan.queue_declare(queue="po_box", durable=True, exclusive=False, auto_delete=False)
chan.exchange_declare(exchange="sorting_room", type="direct", durable=True, auto_delete=False,)

chan.queue_bind(queue="po_box", exchange="sorting_room", routing_key="jason")

def recv_callback(msg):
    print 'Received: ' + msg.body + ' from channel #' + str(msg.channel.channel_id)

chan.basic_consume(queue='po_box', no_ack=True, callback=recv_callback, consumer_tag="testtag")
while True:
    chan.wait()
chan.basic_cancel("testtag")


chan.close()
conn.close()
