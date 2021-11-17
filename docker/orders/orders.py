import json
import sys
import os 
import random 
import datetime 
import pika 
import uuid 
import csv
import random

import uuid
import csv

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from flask_cors import CORS
from datetime import datetime
from os import environ

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = environ.get('dbURL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
CORS(app)


# Communication patterns:
# Use a message-broker with 'direct' exchange to enable interaction
import pika
# If see errors like "ModuleNotFoundError: No module named 'pika'", need to
# make sure the 'pip' version used to install 'pika' matches the python version used.

class Order(db.Model):
    __tablename__ = 'order_table'
 
    order_id = db.Column(db.String(255), primary_key=True)
    customer_name = db.Column(db.String(255), nullable=False)
    customer_id = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.now)
    package_id = db.Column(db.String(255), nullable=False)
    undertaker_name = db.Column(db.String(255), nullable=False)
    order_status = db.Column(db.String(255), nullable=False)

    # def __init__(self, order_id, customer_id, date, package_id, undertaker_name, duration):
    #     self.order_id = order_id
    #     self.customer_id = customer_id
    #     self.date = date
    #     self.package_id = package_id
    #     self.undertaker_name = undertaker_name

    # def json(self):
    #     return {"order_id": self.order_id, "customer_id": self.customer_id, "date":self.date, "package_id": self.package_id, "undertaker_name": self.undertaker_name}
    
    def json(self):
        dto = {
            'order_id': self.order_id, 
            'customer_name': self.customer_name,
            'customer_id': self.customer_id, 
            'email': self.email,
            'date': self.date,
            'package_id': self.package_id,
            'undertaker_name' : self.undertaker_name,
            'order_status': self.order_status
        }

        return dto

@app.route("/get_all")
def get_all():
    return {'orders': [order.json() for order in Order.query.all()]}

@app.route("/get_success")
def get_success():
    return {'orders': [order.json() for order in Order.query.filter_by(order_status="Success")]}
    
@app.route("/order/<string:order_id>")
def find_by_order_id(order_id):
    order = Order.query.filter_by(order_id=order_id).first()
    if order:
        return order.json()
    return {'message': 'Order not found for id ' + str(order_id)}, 404

@app.route("/create_order", methods=['POST'])
def create_order():
    # status in 2xx indicates success
    status = 201
    result = {}

    rows = db.session.query(Order).count()
    order_id = 'O' + str(rows + 1)
    customer_name = request.json.get('customer_name', None)
    customer_id = request.json.get('customer_id', None)
    email = request.json.get('email', None)
    package_id = request.json.get('package_id', None)
    # retrieve information about order and order items from the request
    undertakers = ['Lukas Tham', 'Zhi Poh', 'Wei Bin', 'Kevin Sia', 'Emmanuel Tan', 'Cindy Zheng']
    day_of_week = datetime.today().weekday()
    if day_of_week == 6:
        day_of_week = random.randint(0,5)
    undertaker_name = undertakers[day_of_week]

    order = Order(order_id = order_id, customer_name = customer_name, customer_id = customer_id, email = email, package_id = package_id, undertaker_name = undertaker_name, order_status = "Pending")
    # if status==201 and len(order)<1:
    #     status = 404
    #     result = {"status": status, "message": "Empty order."}

    if status==201:
        try:
            db.session.add(order)
            db.session.commit()
        except Exception as e:
            status = 500
            result = {"status": status, "message": "An error occurred when creating the order in DB.", "error": str(e)}
            send_error(result)
        if status==201:
            result = order.json()
            # result = [Order.query.get(order_id).json(), package_id]
    return jsonify(result)


# @app.route("/create_order", methods = ["POST"])
# def create_order():
#     # status in 2xx indicates success
#     status = 201
#     result = {}
#     my_order = json.loads(order)

#     # retrieve information about order and order items from the request
#     rows = db.session.query(Order).count()
#     order_id = 'O' + str(rows + 1)
#     customer_id = my_order['customer_id']
#     package_id = my_order['package_id']
#     duration = my_order['duration']
#     order = Order(order_id = order_id, customer_id = customer_id, package_id = package_id, duration = duration)
#     # cart_item = request.json.get('cart_item')
#     # for index, ci in enumerate(cart_item):
#     #     if 'book_id' in cart_item[index] and 'quantity' in cart_item[index]:
#     #         order.order_item.append(Order_Item(book_id = cart_item[index]['book_id'], quantity = cart_item[index]['quantity']))
#     #     else:
#     #         status = 400
#     #         result = {"status": status, "message": "Invalid 'book_id' or 'quantity'."}
#     #         break

#     # if status==201 and len(order)<1:
#     #     status = 404
#     #     result = {"status": status, "message": "Empty order."}

#     if status==201:
#         try:
#             db.session.add(order)
#             db.session.commit()
#         except Exception as e:
#             status = 500
#             result = {"status": status, "message": "An error occurred when creating the order in DB.", "error": str(e)}
        
#         if status==201:
#             result = [Order.query.get(order_id).json(), package_id]
#     # FIXME: add a call to "send_error" copied from another appropriate file
#     # send_error(result)

#     return my_order, order_id

@app.route("/confirm/<string:order_id>", methods=["PUT"])
def confirm_orderid(order_id):
    order = Order.query.filter_by(order_id=order_id).first()
    # undertaker_name = request.json.get('undertaker_name', None)
    order.order_status = "Success"
    db.session.commit()
    return {'orders': [order.json() for order in Order.query.all()]}


@app.route("/update/<string:order_id>", methods=["PUT"])
def update_UT(order_id):
    status = 201
    result = {}
    order = Order.query.filter_by(order_id=order_id).first()
    undertaker_name = request.json.get('undertaker_name', None)
    setattr(order, 'undertaker_name', undertaker_name)
    try:
        db.session.commit()
    except:
        message = "Unable to update Undertaker " + undertaker_name
        send_error(message)
        return message,400
    return {'orders': [order.json() for order in Order.query.all()]}
    # # verify
    # v = Order.query.filter_by(order_id="order_id")
    # # return v.package_id == "O5"
    
@app.route("/delete/<string:order_id>", methods=["DELETE"])
def delete_order(order_id):
    status = 201
    result = {}
    order = Order.query.get(order_id)

    if status==201:
        try:
            db.session.delete(order)
            db.session.commit()
        except Exception as e:
            status = 500
            result = {"status": status, "message": "An error occurred when deleting the order in DB.", "error": str(e)}
            send_error(result)
            return result,status
    return {'orders': [order.json() for order in Order.query.all()]}

def send_error(order):
    """inform Shipping/Monitoring/Error as needed"""
    # default username / password to the borker are both 'guest'
    hostname = "localhost" # default broker hostname. Web management interface default at http://localhost:15672
    port = 5672 # default messaging port.
    # connect to the broker and set up a communication channel in the connection
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=hostname, port=port))
        # Note: various network firewalls, filters, gateways (e.g., SMU VPN on wifi), may hinder the connections;
        # If "pika.exceptions.AMQPConnectionError" happens, may try again after disconnecting the wifi and/or disabling firewalls
    channel = connection.channel()

    # set up the exchange if the exchange doesn't exist
    exchangename="afterlife_topic"
    channel.exchange_declare(exchange=exchangename, exchange_type='topic')

    # prepare the message body content
    message = json.dumps(order, default=str) # convert a JSON object to a string

    # send the message
    # always inform Monitoring for logging no matter if successful or not
    # FIXME: is this line of code needed according to the binding key used in Monitoring?
    #channel.basic_publish(exchange=exchangename, routing_key="shipping.info", body=message)
        # By default, the message is "transient" within the broker;
        #  i.e., if the monitoring is offline or the broker cannot match the routing key for the message, the message is lost.
        # If need durability of a message, need to declare the queue in the sender (see sample code below).

    # if "status" in order: # if some error happened in order creation
        # inform Error handler
    channel.queue_declare(queue='errorhandler', durable=True) # make sure the queue used by the error handler exist and durable
    channel.queue_bind(exchange=exchangename, queue='errorhandler', routing_key='order.error') # make sure the queue is bound to the exchange
    channel.basic_publish(exchange=exchangename, routing_key="order.error", body=message,
        properties=pika.BasicProperties(delivery_mode = 2) # make message persistent within the matching queues until it is received by some receiver (the matching queues have to exist and be durable and bound to the exchange)
    )
    print("Order status ({:d}) sent to error handler.".format(order["status"]))
    # else:
    #     corrid = str(uuid.uuid4())
    #     row = {"order_id": order['order_id'], "package_id": order['package_id'], "correlation_id": corrid}
    #     csvheaders = ["order_id", "package_id", "correlation_id"]
    #     with open("ordercorrids.csv", "a+", newline='') as corrid_file: # 'with' statement in python auto-closes the file when the block of code finishes, even if some exception happens in the middle
    #         csvwriter = csv.DictWriter(corrid_file, csvheaders)
    #         csvwriter.writerow(row)
    #     replyqueuename = "inventory.reply"
    #     # prepare the channel and send a message to Shipping
    #     channel.queue_declare(queue='inventory', durable=True) # make sure the queue used by Shipping exist and durable
    #     channel.queue_bind(exchange=exchangename, queue='inventory', routing_key='inventory.order') # make sure the queue is bound to the exchange
    #     channel.basic_publish(exchange=exchangename, routing_key="inventory.order", body=message,
    #         properties=pika.BasicProperties(delivery_mode = 2, # make message persistent within the matching queues until it is received by some receiver (the matching queues have to exist and be durable and bound to the exchange, which are ensured by the previous two api calls)
    #             reply_to=replyqueuename, # set the reply queue which will be used as the routing key for reply messages
    #             correlation_id=corrid # set the correlation id for easier matching of replies
    #         )
    #     )
    #     print("Order sent to Inventory.")
    # close the connection to the broker
    connection.close()
    
    
# Execute this program if it is run as a main script (not by 'import')
if __name__ == '__main__': # if this flask programme is run directly, __name__ = "__main__"; else if via import, __name__ = file name of imported file
    app.run(host='0.0.0.0', port=5001, debug=True)
    # # order = '{"customer_id": "C1", "package_id" : "001", "duration" : 3 }'
    # order = create_order()

