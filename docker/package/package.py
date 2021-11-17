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
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
CORS(app)


# class Inventory(db.Model):
#     __tablename__ = 'inventory'

#     itemid = db.Column(db.String(13), primary_key=True)
#     itemname = db.Column(db.String(64), nullable=False)
#     itemtype = db.Column(db.String(64), nullable=False)
#     quantity = db.Column(db.Integer, nullable=False)

#     def __init__(self, itemid, itemName, itemType, quantity):
#         self.itemid = itemid
#         self.itemName = itemname
#         self.itemType = itemtype
#         self.quantity = quantity

#     def json(self):
#         return {"itemid": self.itemid, "itemname": self.itemname, "itemtype": self.itemtype, "quantity": self.quantity}

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

@app.route("/package")
def getAllPackage():
    return jsonify({"package": [package.json() for package in Package.query.all()]})

@app.route("/package/<string:packageid>")
def find_by_package_id(packageid):
    package = Package.query.filter_by(packageid=packageid).first()
    if package:
        return package.json()
    return {'message': 'Package not found for id ' + str(packageid)}, 404

@app.route("/packagecat/<string:packagecategory>")
def find_by_package_category(packagecategory):
    # packages = Package.query.filter_by(packagecategory=packagecategory)
    # if packages:
    return jsonify({"package": [package.json() for package in Package.query.filter_by(packagecategory=packagecategory)]})
    # return {'message': 'Packages not found for category ' + str(packagecategory)}, 404

# @app.route("/inventory")
# def getAllInventory():
#     return jsonify({"inventory": [inventory.json() for inventory in Inventory.query.all()]})


# @app.route("/inventory/<string:itemid>")
# def getInventorybyitemid(itemid):
#     item = Inventory.query.filter_by(itemid=itemid).first()
#     if item:
#         return item.json()
#     return {'message': 'Item not found for id ' + str(itemid)}, 404
    


# @app.route("/inventory/<string:itemid>", methods=['PUT'])
# def updateinventory(itemid, quantity=1):
#     inventory = Inventory.query.filter_by(itemid=itemid).first()
#     # result: UPDATE user SET no_of_logins = no_of_logins + 1 WHERE user.id = 6
#     setattr(inventory, 'quantity', inventory.quantity + 1)
#     db.session.commit()
#     return {'inventory': [inventory.json()]}
    # # verify
    # v = Order.query.filter_by(order_id="order_id")
    # # return v.package_id == "O5"

@app.route("/packagebuy/<string:packageid>", methods=['PUT'])
def packagebuy(packageid):
    package = Package.query.filter_by(packageid=packageid).first()
    # result: UPDATE user SET no_of_logins = no_of_logins + 1 WHERE user.id = 6
    if (package.packagequantity > 0):
        setattr(package, 'packagequantity', package.packagequantity - 1)
        db.session.commit()
        return {'package': [package.json()]}
    else: 
        message = packageid + " is out of stock"
        send_error(message)
        return message, 400
    
def send_error(package):
    """inform Error as needed"""
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
    message = json.dumps(package, default=str) # convert a JSON object to a string

    # send the message
    # always inform Monitoring for logging no matter if successful or not
    # FIXME: Do you think if this line of code is needed according to the binding key used in Monitoring?
    # channel.basic_publish(exchange=exchangename, routing_key="shipping.info", body=message)
        # By default, the message is "transient" within the broker;
        #  i.e., if the monitoring is offline or the broker cannot match the routing key for the message, the message is lost.
        # If need durability of a message, need to declare the queue in the sender (see sample code below).

    # if "status" in package: # if some error happened in order creation
        # inform Error handler
    channel.queue_declare(queue='errorhandler', durable=True) # make sure the queue used by the error handler exist and durable
    channel.queue_bind(exchange=exchangename, queue='errorhandler', routing_key='*.error') # make sure the queue is bound to the exchange
    channel.basic_publish(exchange=exchangename, routing_key="package.error", body=message,
        properties=pika.BasicProperties(delivery_mode = 2) # make message persistent within the matching queues until it is received by some receiver (the matching queues have to exist and be durable and bound to the exchange)
    )
    print("Inventory status (400) sent to error handler.")
    connection.close()
    # else: # inform Shipping and exit
    #     # prepare the channel and send a message to Shipping
    #     channel.queue_declare(queue='order', durable=True) # make sure the queue used by Shipping exist and durable
    #     channel.queue_bind(exchange=exchangename, queue='order', routing_key='*.order') # make sure the queue is bound to the exchange
    #     channel.basic_publish(exchange=exchangename, routing_key="pricing.order", body=message,
    #         properties=pika.BasicProperties(delivery_mode = 2, # make message persistent within the matching queues until it is received by some receiver (the matching queues have to exist and be durable and bound to the exchange, which are ensured by the previous two api calls)
    #         )
    #     )
    #     print("Price changes sent to Order.")
    # # close the connection to the broker
    
    
# hostname = "localhost" # default broker hostname. Web management interface default at http://localhost:15672
# port = 5672 # default messaging port.
# # connect to the broker and set up a communication channel in the connection
# connection = pika.BlockingConnection(pika.ConnectionParameters(host=hostname, port=port))
# # Note: various network firewalls, filters, gateways (e.g., SMU VPN on wifi), may hinder the connections;
# # If "pika.exceptions.AMQPConnectionError" happens, may try again after disconnecting the wifi and/or disabling firewalls
# channel = connection.channel()
# # set up the exchange if the exchange doesn't exist
# exchangename="afterlife_topic"
# channel.exchange_declare(exchange=exchangename, exchange_type='direct')

# def receiveOrder():

#     replyqueuename="inventory.reply"
#     channelqueue = channel.queue_declare(queue='inventory', durable=True) # make sure the queue used for "reply_to" is durable for reply messages
#     queue_name = channelqueue.method.queue
#     channel.queue_bind(exchange=exchangename, queue=queue_name, routing_key='inventory.order') # bind the queue to the exchange via the key

#     #channel.queue_bind(exchange=exchangename, queue=replyqueuename, routing_key=replyqueuename) # make sure the reply_to queue is bound to the exchange
#     # set up a consumer and start to wait for coming messages
#     channel.basic_qos(prefetch_count=1) # The "Quality of Service" setting makes the broker distribute only one message to a consumer if the consumer is available (i.e., having finished processing and acknowledged all previous messages that it receives)
#     channel.basic_consume(queue=queue_name, on_message_callback=callback)
#     channel.start_consuming() # an implicit loop waiting to receive messages; it doesn't exit by default. Use Ctrl+C in the command window to terminate it.

# def updateDatabase(result):
#     packages = Package.query.all()
    
#     for package in packages:
#         if result['package_id'] == package.packageid:
#             package.packagequantity = package.packagequantity - 1
#             commitMsg= True
#             try:
#                 db.session.commit()
#             except Exception as e:
#                 commitMsg= False

#             if commitMsg == False:
#                 return False

#     return True
            

# def callback(channel, method, properties, body): # required signature for the callback; no return
#     print("Received an order by " + __file__)

#     result = json.loads(body)
    
#     message = updateDatabase(result)
#     # print processing result; not really needed
#     # my_message = json.dump(result, sys.stdout, default=str) # convert the JSON object to a string and print out on screen
#     # duration = json.dump(result['duration'], sys.stdout, default=str) # convert the JSON object to a string and print out on screen
#     print() # print a new line feed to the previous json dump
#     print() # print another new line as a separator

#     # if (Package.query.filter_by(packageid=package_id).first()):
#     #     records = db.session.query(Package).filter(Package.package_id == package_id).all()
#     #     print(records)
#         # stmt = session.query(Package).filter(Package.Package(sub_stmt))
#         # Package.query.update({Package.packagequantity: db.session.query(Order)}) 
#         # Session.commit()    
#         # for package in records:

    

#     # if fail: 
#     #     do this
#     # else:
#     #     do this
#     # prepare the reply message and send it out

#     replymessage = str(message)
#     # replymessage = json.dumps(result, default=str) # convert the JSON object to a string
#     replyqueuename="inventory.reply"
#     # A general note about AMQP queues: If a queue or an exchange doesn't exist before a message is sent,
#     # - the broker by default silently drops the message;
#     # - So, if really need a 'durable' message that can survive broker restarts, need to
#     #  + declare the exchange before sending a message, and
#     #  + declare the 'durable' queue and bind it to the exchange before sending a message, and
#     #  + send the message with a persistent mode (delivery_mode=2).
#     channel.queue_declare(queue=replyqueuename, durable=True) # make sure the queue used for "reply_to" is durable for reply messages
#     channel.queue_bind(exchange=exchangename, queue=replyqueuename, routing_key=replyqueuename) # make sure the reply_to queue is bound to the exchange
#     channel.basic_publish(exchange=exchangename,
#             routing_key=properties.reply_to, # use the reply queue set in the request message as the routing key for reply messages
#             body=replymessage, 
#             properties=pika.BasicProperties(delivery_mode = 2, # make message persistent (stored to disk, not just memory) within the matching queues; default is 1 (only store in memory)
#                 correlation_id = properties.correlation_id, # use the correlation id set in the request message
#             )
#     )
#     channel.basic_ack(delivery_tag=method.delivery_tag) # acknowledge to the broker that the processing of the request message is completed



# def reply_callback(channel, method, properties, body): # required signature for a callback; no return
#     """processing function called by the broker when a message is received"""
#     # Load correlations for existing created orders from a file.
#     # - In practice, using DB (as part of the order DB) is a better choice than using a file.
#     rows = []
#     with open("corrids.csv", 'r', newline='') as corrid_file: # 'with' statement in python auto-closes the file when the block of code finishes, even if some exception happens in the middle
#         csvreader = csv.DictReader(corrid_file)
#         for row in csvreader:
#             rows.append(row)
#     # Check if the reply message contains a valid correlation id recorded in the file.
#     # - Assume each line in the file is in this CSV format: <order_id>, <correlation_id>, <status>, ...
#     matched = False
#     for row in rows:
#         if not 'correlation_id' in row:
#             print('Warning for corrids.csv: no "correlation_id" for an order:', row)
#             continue
#         corrid = row['correlation_id']
#         if corrid == properties.correlation_id: # check if the reply message matches one request message based on the correlation id
#             print("--Matched reply message with a correlation ID: " + corrid)
#             # Can do anything needed for the scenario here, e.g., may update the 'status', or inform UI or other applications/services.
#             print(body) # Here, simply print the reply message directly
#             print()
#             matched = True
#             break
#     if not matched:
#         print("--Wrong reply correlation ID: No match of " + properties.correlation_id)
#         print()

#     # acknowledge to the broker that the processing of the message is completed
#     channel.basic_ack(delivery_tag=method.delivery_tag)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
    # print("This is " + os.path.basename(__file__) + ": inventory for an order...")
    # receiveOrder()

