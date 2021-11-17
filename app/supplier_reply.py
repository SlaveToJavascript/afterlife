

import sys
import os
import csv


import pika


def receiveSupply():
    hostname = "localhost"
    port = 5672 
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=hostname, port=port))
        
    channel = connection.channel()

    
    exchangename="supplier_direct"
    channel.exchange_declare(exchange=exchangename, exchange_type='topic')

    replyqueuename="packagesupplier.reply"
    channel.queue_declare(queue=replyqueuename, durable=True) 
    channel.queue_bind(exchange=exchangename, queue=replyqueuename, routing_key=replyqueuename) 
   
    channel.basic_qos(prefetch_count=1) 
    channel.basic_consume(queue=replyqueuename,
            on_message_callback=reply_callback, 
    ) 
    channel.start_consuming() 

def reply_callback(channel, method, properties, body): 
    """processing function called by the broker when a message is received"""
   
   
    rows = []
    with open("suppliercorrids.csv", 'r', newline='') as corrid_file: 
        csvreader = csv.DictReader(corrid_file)
        for row in csvreader:
            rows.append(row)

    matched = False
    for row in rows:
        if not 'correlation_id' in row:
            print('Warning for corrids.csv: no "correlation_id" for an order:', row)
            continue
        corrid = row['correlation_id']
        if corrid == properties.correlation_id: 
            print("--Matched reply message with a correlation ID: " + corrid)


            body = body.decode("utf-8")

            if (body == "True"):
                print('Supplier has delivered the order. Thank you')
                #send Payment and Twillo
                #if payment fail
                    #send error message
                #else
                    #send Twillo SMS and success msg.
            else:
                print('An Error has occured')
                #send to error microservice
                #send error message
            
            print()
            matched = True
            break
    if not matched:
        print("--Wrong reply correlation ID: No match of " + properties.correlation_id)
        #send to errormicroservice
        print()


    channel.basic_ack(delivery_tag=method.delivery_tag)


if __name__ == "__main__":
    print("This is " + os.path.basename(__file__) + ": listening for a reply from package for an order from supplier...")
    receiveSupply()
