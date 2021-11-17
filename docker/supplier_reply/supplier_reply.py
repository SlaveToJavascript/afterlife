import json
import sys
import os 
import random 
import datetime 
import pika 
import uuid 
import csv

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from sqlalchemy import update
from os import environ


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('dbURL')
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root@localhost:3306/supplier'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
CORS(app)


class Correlation_id(db.Model):
    __tablename__ = 'correlation_id'
    supplier_id = db.Column(db.String(64), primary_key=True)
    package_id = db.Column(db.String(64), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    corr_id = db.Column(db.String(255), nullable=False)

    def json(self):
        return {'supplier_id': self.supplier_id, 'package_id': self.package_id, 
        'quantity': self.quantity, 'corr_id': self.corr_id}


hostname = "localhost" # default broker hostname. Web management interface default at http://localhost:15672
port = 5672 # default messaging port.
    # connect to the broker and set up a communication channel in the connection
connection = pika.BlockingConnection(pika.ConnectionParameters('172.17.0.2'))
        # Note: various network firewalls, filters, gateways (e.g., SMU VPN on wifi), may hinder the connections;
        # If "pika.exceptions.AMQPConnectionError" happens, may try again after disconnecting the wifi and/or disabling firewalls
channel = connection.channel()

    # set up the exchange if the exchange doesn't exist
exchangename="supplier_direct"
channel.exchange_declare(exchange=exchangename, exchange_type='topic')

def receiveSupply():

    replyqueuename="inventorysupplier.reply"
    channel.queue_declare(queue=replyqueuename, durable=True) # make sure the queue used for "reply_to" is durable for reply messages
    channel.queue_bind(exchange=exchangename, queue=replyqueuename, routing_key=replyqueuename) # make sure the reply_to queue is bound to the exchange
    # set up a consumer and start to wait for coming messages
    channel.basic_qos(prefetch_count=1) # The "Quality of Service" setting makes the broker distribute only one message to a consumer if the consumer is available (i.e., having finished processing and acknowledged all previous messages that it receives)
    channel.basic_consume(queue=replyqueuename,
            on_message_callback=reply_callback, # set up the function called by the broker to process a received message
    ) # prepare the reply_to receiver
    channel.start_consuming() # an implicit loop waiting to receive messages; it doesn't exit by default. Use Ctrl+C in the command window to terminate it.

def reply_callback(channel, method, properties, body): # required signature for a callback; no return
    """processing function called by the broker when a message is received"""
    # Load correlations for existing created orders from a file.
    # - In practice, using DB (as part of the order DB) is a better choice than using a file.
    rows = []
    
    # with open("suppliercorrids.csv", 'r', newline='') as corrid_file: # 'with' statement in python auto-closes the file when the block of code finishes, even if some exception happens in the middle
    #     csvreader = csv.DictReader(corrid_file)
    #     for row in csvreader:
    #         rows.append(row)
    # Check if the reply message contains a valid correlation id recorded in the file.
    # - Assume each line in the file is in this CSV format: <order_id>, <correlation_id>, <status>, ...
    # matched = False
    
    # for row in rows:
    #     if not 'correlation_id' in row:
    #         print('Warning for corrids.csv: no "correlation_id" for an order:', row)
    #         continue
    #     corrid = row['correlation_id']
    #     if corrid == properties.correlation_id: # check if the reply message matches one request message based on the correlation id
    result = Correlation_id.query.filter_by(corr_id=properties.correlation_id)
    if result:    
        print("--Matched reply message with a correlation ID: ")
        # Can do anything needed for the scenario here, e.g., may update the 'status', or inform UI or other applications/services.
        #now i do something here
        body = body.decode("utf-8")

        if (body == "True"):
            print('Supplier has delivered the order. Thank you')
        else:
            print('An Error has occured')
            #send to error microservice
            #send error message
        
        print()
        matched = True
    print("--Wrong reply correlation ID: No match of " + properties.correlation_id)
    #send to errormicroservice
    print()

    # acknowledge to the broker that the processing of the message is completed
    channel.basic_ack(delivery_tag=method.delivery_tag)


# Execute this program if it is run as a main script (not by 'import')
if __name__ == "__main__":
    print("This is " + os.path.basename(__file__) + ": supplier for an order...")
    receiveSupply()
