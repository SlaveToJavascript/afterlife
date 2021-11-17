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

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root@localhost:3306/order'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
CORS(app)


import pika

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

    status = 201
    result = {}

    rows = db.session.query(Order).count()
    order_id = 'O' + str(rows + 1)
    customer_name = request.json.get('customer_name', None)
    customer_id = request.json.get('customer_id', None)
    email = request.json.get('email', None)
    package_id = request.json.get('package_id', None)

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

    return jsonify(result)


@app.route("/confirm/<string:order_id>", methods=["PUT"])
def confirm_orderid(order_id):
    order = Order.query.filter_by(order_id=order_id).first()

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
    
    hostname = "localhost" 
    port = 5672 
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=hostname, port=port))
       
    channel = connection.channel()

    exchangename="afterlife_topic"
    channel.exchange_declare(exchange=exchangename, exchange_type='topic')

    message = json.dumps(order, default=str) 

    channel.queue_declare(queue='errorhandler', durable=True) 
    channel.queue_bind(exchange=exchangename, queue='errorhandler', routing_key='order.error') 
    channel.basic_publish(exchange=exchangename, routing_key="order.error", body=message,
        properties=pika.BasicProperties(delivery_mode = 2) 
    )
    print("Order status ({:d}) sent to error handler.".format(order["status"]))

    connection.close()
    
    

if __name__ == '__main__': 
    app.run(port=5001, debug=True)


