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


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root@localhost:3306/package'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
CORS(app)


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

hostname = "localhost" 
port = 5672 
connection = pika.BlockingConnection(pika.ConnectionParameters(host=hostname, port=port))

channel = connection.channel()

exchangename= "supplier_direct"
channel.exchange_declare(exchange=exchangename, exchange_type='topic')


def receiveSupply():

    replyqueuename="packagesupplier.reply"
    channelqueue = channel.queue_declare(queue='packagesupplier', durable=True)
    queue_name = channelqueue.method.queue
    channel.queue_bind(exchange=exchangename, queue=queue_name, routing_key='supplier.package')

  
    channel.basic_qos(prefetch_count=1)
    channel.start_consuming()


def callback(channel, method, properties, body): 
    print("Received an order by " + __file__)

    result = json.loads(body)

    message = updateSupply(result)
    
    print() 
    print()



    replymessage = str(message)
   
    replyqueuename="packagesupplier.reply"
   
    channel.queue_declare(queue=replyqueuename, durable=True) 
    channel.queue_bind(exchange=exchangename, queue=replyqueuename, routing_key=replyqueuename) 
    channel.basic_publish(exchange=exchangename,
            routing_key=properties.reply_to, 
            body=replymessage, 
            properties=pika.BasicProperties(delivery_mode = 2, 
                correlation_id = properties.correlation_id, 
            )
    )
    channel.basic_ack(delivery_tag=method.delivery_tag) 
    

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



