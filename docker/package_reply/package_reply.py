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
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root@localhost:3306/package'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
CORS(app)


class Inventory(db.Model):
    __tablename__ = 'inventory'

    package_id = db.Column(db.String(13), primary_key=True)
    itemname = db.Column(db.String(64), nullable=False)
    itemtype = db.Column(db.String(64), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    def __init__(self, itemid, itemName, itemType, quantity):
        self.itemid = itemid
        self.itemName = itemname
        self.itemType = itemtype
        self.quantity = quantity

    def json(self):
        return {"itemid": self.itemid, "itemname": self.itemname, "itemtype": self.itemtype, "quantity": self.quantity}

class Package(db.Model):
    __tablename__ = 'package'

    packageid = db.Column(db.String(13), primary_key=True)
    packagename = db.Column(db.String(13), nullable=False)
    packageprice = db.Column(db.Float(10), nullable=False)
    packagequantity = db.Column(db.Integer, nullable=False)
    packagecategory = db.Column(db.String(13), nullable=False)

    def __init__(self, packagename, packageid, packageprice, packagequantity, packagecategory):
        self.packagename = packagename
        self.packageid = packageid
        self.packageprice = packageprice
        self.packagequantity = packagequantity
        self.packagecategory = packagecategory

    def json(self):
        return {'packagename': self.packagename, 'packageid': self.packageid, 
        'packageprice': self.packageprice, 'packagequantity': self.packagequantity, 
        'packagecategory': self.packagecategory}

hostname = "localhost" # default broker hostname. Web management interface default at http://localhost:15672
port = 5672 # default messaging port.
# connect to the broker and set up a communication channel in the connection
connection = pika.BlockingConnection(pika.ConnectionParameters('172.17.0.2'))
# Note: various network firewalls, filters, gateways (e.g., SMU VPN on wifi), may hinder the connections;
# If "pika.exceptions.AMQPConnectionError" happens, may try again after disconnecting the wifi and/or disabling firewalls
channel = connection.channel()

exchangename= "supplier_direct"
channel.exchange_declare(exchange=exchangename, exchange_type='topic')


def receiveSupply():

    replyqueuename="inventorysupplier.reply"
    channelqueue = channel.queue_declare(queue='inventorysupplier', durable=True) # make sure the queue used for "reply_to" is durable for reply messages
    queue_name = channelqueue.method.queue
    channel.queue_bind(exchange=exchangename, queue=queue_name, routing_key='supplier.inventory') # bind the queue to the exchange via the key

    #channel.queue_bind(exchange=exchangename, queue=replyqueuename, routing_key=replyqueuename) # make sure the reply_to queue is bound to the exchange
    # set up a consumer and start to wait for coming messages
    channel.basic_qos(prefetch_count=1) # The "Quality of Service" setting makes the broker distribute only one message to a consumer if the consumer is available (i.e., having finished processing and acknowledged all previous messages that it receives)
    channel.basic_consume(queue=queue_name, on_message_callback=callback)
    channel.start_consuming() # an implicit loop waiting to receive mes


def callback(channel, method, properties, body): # required signature for the callback; no return
    print("Received an order by " + __file__)

    result = json.loads(body)

    message = updateSupply(result)
    # print processing result; not really needed
    # my_message = json.dump(result, sys.stdout, default=str) # convert the JSON object to a string and print out on screen
    # duration = json.dump(result['duration'], sys.stdout, default=str) # convert the JSON object to a string and print out on screen
    print() # print a new line feed to the previous json dump
    print() # print another new line as a separator
    
    # if (Package.query.filter_by(packageid=package_id).first()):
    #     records = db.session.query(Package).filter(Package.package_id == package_id).all()
    #     print(records)
        # stmt = session.query(Package).filter(Package.Package(sub_stmt))
        # Package.query.update({Package.packagequantity: db.session.query(Order)}) 
        # Session.commit()    
        # for package in records:


    # if fail: 
    #     do this
    # else:
    #     do this
    # prepare the reply message and send it out

    replymessage = str(message)
    # replymessage = json.dumps(result, default=str) # convert the JSON object to a string
    replyqueuename="inventorysupplier.reply"
    # A general note about AMQP queues: If a queue or an exchange doesn't exist before a message is sent,
    # - the broker by default silently drops the message;
    # - So, if really need a 'durable' message that can survive broker restarts, need to
    #  + declare the exchange before sending a message, and
    #  + declare the 'durable' queue and bind it to the exchange before sending a message, and
    #  + send the message with a persistent mode (delivery_mode=2).
    channel.queue_declare(queue=replyqueuename, durable=True) # make sure the queue used for "reply_to" is durable for reply messages
    channel.queue_bind(exchange=exchangename, queue=replyqueuename, routing_key=replyqueuename) # make sure the reply_to queue is bound to the exchange
    channel.basic_publish(exchange=exchangename,
            routing_key=properties.reply_to, # use the reply queue set in the request message as the routing key for reply messages
            body=replymessage, 
            properties=pika.BasicProperties(delivery_mode = 2, # make message persistent (stored to disk, not just memory) within the matching queues; default is 1 (only store in memory)
                correlation_id = properties.correlation_id, # use the correlation id set in the request message
            )
    )
    channel.basic_ack(delivery_tag=method.delivery_tag) # acknowledge to the broker that the processing of the request message is completed
    

def updateSupply(result):
    packages = Package.query.all()
    commitMsg = None
    for package in packages:
        if result[1] == package.packageid:
            package.packagequantity = int(result[2]) + package.packagequantity
            try:
                db.session.commit()
                
            except Exception as e:
                commitMsg = False

        if commitMsg == False:
            return commitMsg
            
    return True


if __name__ == '__main__':
    print("This is " + os.path.basename(__file__) + ": supplier for an order...")
    receiveSupply()



