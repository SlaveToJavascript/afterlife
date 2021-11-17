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

    return jsonify({"package": [package.json() for package in Package.query.filter_by(packagecategory=packagecategory)]})



@app.route("/packagebuy/<string:packageid>", methods=['PUT'])
def packagebuy(packageid):
    package = Package.query.filter_by(packageid=packageid).first()

    if (package.packagequantity > 0):
        setattr(package, 'packagequantity', package.packagequantity - 1)
        db.session.commit()
        return {'package': [package.json()]}
    else: 
        message = packageid + " is out of stock"
        send_error(message)
        return message, 400

@app.route("/packageupdate/<string:packageid>", methods=['PUT'])
def packageupdate(packageid):
    package = Package.query.filter_by(packageid=packageid).first()

    setattr(package, 'packagequantity', package.packagequantity + 1)
    db.session.commit()
    return {'package': [package.json()]}

def send_error(package):
    """inform Error as needed"""

    hostname = "localhost" 
    port = 5672 
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=hostname, port=port))

    channel = connection.channel()

    exchangename="afterlife_topic"
    channel.exchange_declare(exchange=exchangename, exchange_type='topic')


    message = json.dumps(package, default=str) 

    channel.queue_declare(queue='errorhandler', durable=True) 
    channel.queue_bind(exchange=exchangename, queue='errorhandler', routing_key='*.error') 
    channel.basic_publish(exchange=exchangename, routing_key="package.error", body=message,
        properties=pika.BasicProperties(delivery_mode = 2) 
    )
    print("Package status (400) sent to error handler.")
    connection.close()


if __name__ == '__main__':
    app.run(port=5000, debug=True)
