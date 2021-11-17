import json
import sys
import os
import random
import csv
import uuid

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from flask_cors import CORS
from datetime import datetime
from os import environ


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('dbURL')
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root@localhost:3306/supplier'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
CORS(app)


# Communication patterns:
# Use a message-broker with 'direct' exchange to enable interaction
import pika
# If see errors like "ModuleNotFoundError: No module named 'pika'", need to
# make sure the 'pip' version used to install 'pika' matches the python version used.
class Correlation_id(db.Model):
    __tablename__ = 'correlation_id'
    supplier_id = db.Column(db.String(64), primary_key=True)
    package_id = db.Column(db.String(64), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    corr_id = db.Column(db.String(255), nullable=False)

    def json(self):

        dto1 = {
            'supplier_id': self.supplier_id,  
            'package_id': self.package_id,
            'quantity': self.quantity,
            'corr_id': self.corr_id
        }

        return dto1

class Supplier(db.Model):
    __tablename__ = 'supplier'
 
    supplier_id = db.Column(db.String(255), primary_key=True)
    # supplier_name = db.Column(db.String(255), nullable=False)
    packageid = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    # undertaker_name = db.Column(db.String(255), nullable=True)

    # def __init__(self, order_id, customer_id, date, package_id, price):
    #     self.order_id = order_id
    #     self.customer_id = customer_id
    #     self.date = date
    #     self.package_id = package_id
    #     self.price = price

    # def json(self):
    #     return {"order_id": self.order_id, "customer_id": self.customer_id, "date":self.date, "package_id": self.package_id, "price": self.price}
    def json(self):
        dto = {
            'supplier_id': self.supplier_id, 
            # 'supplier_name': self.supplier_name, 
            'packageid': self.packageid,
            'quantity': self.quantity
        }

        return dto

@app.route("/create_supplier", methods = ["POST"])
def create_order():
    # status in 2xx indicates success
    status = 201
    result = {}

    # retrieve information about order and order items from the request
    rows = db.session.query(Supplier).count()
    supplier_id = 'S' + str(rows + 1)
    # supplier_name = request.json.get('supplier_name', None)
    packageid = request.json.get('packageid', None)
    quantity = request.json.get('quantity', None)
    supplier = Supplier(supplier_id = supplier_id, packageid = packageid, quantity=quantity)
    # cart_item = request.json.get('cart_item')
    # for index, ci in enumerate(cart_item):
    #     if 'book_id' in cart_item[index] and 'quantity' in cart_item[index]:
    #         order.order_item.append(Order_Item(book_id = cart_item[index]['book_id'], quantity = cart_item[index]['quantity']))
    #     else:
    #         status = 400
    #         result = {"status": status, "message": "Invalid 'book_id' or 'quantity'."}
    #         break

    # if status==201 and len(order)<1:
    #     status = 404
    #     result = {"status": status, "message": "Empty order."}

    if status==201:
        try:
            db.session.add(supplier)
            db.session.commit()
        except Exception as e:
            status = 500
            result = {"status": status, "message": "An error occurred when creating the order in DB.", "error": str(e)}

        if status==201:
            result = [supplier_id ,packageid, quantity]

    # FIXME: add a call to "send_order" copied from another appropriate file
    send_supplier(result)
    return Supplier.query.get(supplier_id).json()

def send_supplier(supplier):
    """inform Shipping/Monitoring/Error as needed"""
    # default username / password to the borker are both 'guest'
    hostname = "localhost" # default broker hostname. Web management interface default at http://localhost:15672
    port = 5672 # default messaging port.
    # connect to the broker and set up a communication channel in the connection
    connection = pika.BlockingConnection(pika.ConnectionParameters('172.17.0.2'))
    # connection = pika.BlockingConnection(pika.ConnectionParameters(host=hostname, port=port))
        # Note: various network firewalls, filters, gateways (e.g., SMU VPN on wifi), may hinder the connections;
        # If "pika.exceptions.AMQPConnectionError" happens, may try again after disconnecting the wifi and/or disabling firewalls
    channel = connection.channel()

    # set up the exchange if the exchange doesn't exist
    exchangename="afterlife_topic"
    channel.exchange_declare(exchange=exchangename, exchange_type='topic')

    # prepare the message body content
    message = json.dumps(supplier, default=str) # convert a JSON object to a string

    # send the message
    # always inform Monitoring for logging no matter if successful or not
    # FIXME: is this line of code needed according to the binding key used in Monitoring?
    #channel.basic_publish(exchange=exchangename, routing_key="shipping.info", body=message)
        # By default, the message is "transient" within the broker;
        #  i.e., if the monitoring is offline or the broker cannot match the routing key for the message, the message is lost.
        # If need durability of a message, need to declare the queue in the sender (see sample code below).

    if "status" in supplier: # if some error happened in order creation
        # inform Error handler
        channel.queue_declare(queue='errorhandler', durable=True) # make sure the queue used by the error handler exist and durable
        channel.queue_bind(exchange=exchangename, queue='errorhandler', routing_key='supplier.error') # make sure the queue is bound to the exchange
        channel.basic_publish(exchange=exchangename, routing_key="supplier.error", body=message,
            properties=pika.BasicProperties(delivery_mode = 2) # make message persistent within the matching queues until it is received by some receiver (the matching queues have to exist and be durable and bound to the exchange)
        )
        print("Order status ({:d}) sent to error handler.".format(supplier["status"]))
    else:
        corrid = str(uuid.uuid4())
        #add inside
        correlation_id = Correlation_id(supplier_id = supplier[0], package_id = supplier[1], quantity=supplier[2], corr_id=corrid)
        db.session.add(correlation_id)
        db.session.commit()
        # row = {"supplier_id": supplier[0], "packageid": supplier[1], "quantity": supplier[2], "correlation_id": corrid}
        # csvheaders = ["supplier_id", "packageid", "quantity", "correlation_id"]
        # with open("suppliercorrids.csv", "a+", newline='') as corrid_file: # 'with' statement in python auto-closes the file when the block of code finishes, even if some exception happens in the middle
        #     csvwriter = csv.DictWriter(corrid_file, csvheaders)
        #     csvwriter.writerow(row)
        replyqueuename = "inventorysupplier.reply"
        # prepare the channel and send a message to Shipping
        channel.queue_declare(queue='inventorysupplier', durable=True) # make sure the queue used by Shipping exist and durable
        channel.queue_bind(exchange=exchangename, queue='inventorysupplier', routing_key='supplier.inventory') # make sure the queue is bound to the exchange
        channel.basic_publish(exchange=exchangename, routing_key="supplier.inventory", body=message,
            properties=pika.BasicProperties(delivery_mode = 2, # make message persistent within the matching queues until it is received by some receiver (the matching queues have to exist and be durable and bound to the exchange, which are ensured by the previous two api calls)
                reply_to=replyqueuename, # set the reply queue which will be used as the routing key for reply messages
                correlation_id=corrid # set the correlation id for easier matching of replies
            )
        )
        print("Order sent to Inventory.")
    # close the connection to the broker
    connection.close()

# Execute this program if it is run as a main script (not by 'import')
if __name__ == '__main__': # if this flask programme is run directly, __name__ = "__main__"; else if via import, __name__ = file name of imported file
    app.run(host='0.0.0.0', port=5002, debug=True)
    