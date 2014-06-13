from amqplib import client_0_8 as amqp
import sys

conn = amqp.Connection(host="xiaoxubeii:5672", userid="guest", password="guest", virtual_host="/", insist=False)
chan = conn.channel()

msg = amqp.Message(sys.argv[1])
msg.properties["delivery_mode"] = 2
chan.basic_publish(msg,exchange="sorting_room",routing_key="jason")

chan.close()
conn.close()