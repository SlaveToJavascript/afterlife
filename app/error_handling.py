import json
import sys
import os 
import random 
import datetime 
import pika 
import uuid 
import csv


def receiveOrderError():
    hostname = "localhost"
    port = 5672 
  
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=hostname, port=port))
    channel = connection.channel()


    exchangename="afterlife_topic"
    channel.exchange_declare(exchange=exchangename, exchange_type='topic')

   
    channelqueue = channel.queue_declare(queue="errorhandler", durable=True) 
    queue_name = channelqueue.method.queue
    channel.queue_bind(exchange=exchangename, queue=queue_name, routing_key='*.error') 
        

    
    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
    channel.start_consuming() 
def callback(channel, method, properties, body): 
    print("Received an error by " + __file__)
    processOrderError(json.loads(body))
    print()

def processOrderError(order):
    print("Processing an order error:")
    print(order)


if __name__ == "__main__":  
    print("This is " + os.path.basename(__file__) + ": processing an order error...")
    receiveOrderError()
