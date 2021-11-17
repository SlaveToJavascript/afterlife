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

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root@localhost:3306/supplier'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
CORS(app)


import pika

class Supplier(db.Model):
    __tablename__ = 'supplier'
 
    supplier_id = db.Column(db.String(255), primary_key=True)
    packageid = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
   
    def json(self):
        dto = {
            'supplier_id': self.supplier_id, 

            'packageid': self.packageid,
            'quantity': self.quantity
        }

        return dto

@app.route("/create_supplier", methods = ["POST"])
def create_order():

    status = 201
    result = {}


    rows = db.session.query(Supplier).count()
    supplier_id = 'S' + str(rows + 1)

    packageid = request.json.get('packageid', None)
    quantity = request.json.get('quantity', None)
    supplier = Supplier(supplier_id = supplier_id, packageid = packageid, quantity=quantity)


    if status==201:
        try:
            db.session.add(supplier)
            db.session.commit()
        except Exception as e:
            status = 500
            result = {"status": status, "message": "An error occurred when creating the order in DB.", "error": str(e)}

        if status==201:
            result = [supplier_id ,packageid, quantity]

    send_supplier(result)
    return Supplier.query.get(supplier_id).json()

def send_supplier(supplier):
    """inform Shipping/Monitoring/Error as needed"""
  
    hostname = "localhost" 
    port = 5672 
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=hostname, port=port))

    channel = connection.channel()

    
    exchangename="afterlife_topic"
    channel.exchange_declare(exchange=exchangename, exchange_type='topic')

    
    message = json.dumps(supplier, default=str) 



    if "status" in supplier: 
        
        channel.queue_declare(queue='errorhandler', durable=True) 
        channel.queue_bind(exchange=exchangename, queue='errorhandler', routing_key='supplier.error') 
        channel.basic_publish(exchange=exchangename, routing_key="supplier.error", body=message,
            properties=pika.BasicProperties(delivery_mode = 2)
        )
        print("Order status ({:d}) sent to error handler.".format(supplier["status"]))
    else:
        corrid = str(uuid.uuid4())
        row = {"supplier_id": supplier[0], "packageid": supplier[1], "quantity": supplier[2], "correlation_id": corrid}
        csvheaders = ["supplier_id", "packageid", "quantity", "correlation_id"]
        with open("suppliercorrids.csv", "a+", newline='') as corrid_file: 
            csvwriter = csv.DictWriter(corrid_file, csvheaders)
            csvwriter.writerow(row)
        replyqueuename = "packagesupplier.reply"

        channel.queue_declare(queue='packagesupplier', durable=True) 
        channel.queue_bind(exchange=exchangename, queue='packagesupplier', routing_key='supplier.package') 
        channel.basic_publish(exchange=exchangename, routing_key="supplier.package", body=message,
            properties=pika.BasicProperties(delivery_mode = 2,
                reply_to=replyqueuename, 
                correlation_id=corrid 
            )
        )
        print("Order sent to Package.")
    # close the connection to the broker
    connection.close()

# Execute this program if it is run as a main script (not by 'import')
if __name__ == '__main__': # if this flask programme is run directly, __name__ = "__main__"; else if via import, __name__ = file name of imported file
    app.run(host='0.0.0.0', port=5002, debug=True)
    