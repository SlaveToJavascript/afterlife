from mailjet_rest import Client
import os
import pika
import json
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

api_key = 'd33bf20543dd27cfb253fadba4ad4b93'
api_secret = 'f1be66c0ef1332824e309915fb097b90'

@app.route('/sendemail', methods=['POST'])
def sendemail(): 
  mailjet = Client(auth=(api_key, api_secret), version='v3.1')
  customername = request.json.get('customername', None)
  email = request.json.get('email', None)
  packagename = request.json.get('packagename', None)
  data = {
    'Messages': [
      {
        "From": {
          "Email": "emmanueltan.2018@sis.smu.edu.sg",
          "Name": "AfterLife"
        },
        "To": [
          {
            "Email": email,
            "Name": customername
          }
        ],
        "Subject": "Your order is confirmed",
        "HTMLPart": "Dear " + customername + ",<br><br>We would like to inform you that the payment \
            for \"" + packagename + "\" has been received and your order is being processed.\
            <br><br>Sincerely, <br>AfterLIFE",
        "CustomID": "AppGettingStartedTest"
      }
    ]
  }
  result = mailjet.send.create(data=data)
  if (result.status_code != 200):
    error = {'status':result.status_code, 'message': result.json()["Messages"][0]["Errors"][0]["ErrorMessage"]}
    send_error(error)
    return (error),result.status_code
  else:
    return (result.json())
  # print (result.status_code)
  # print(result.json())
  

def send_error(e):
    hostname = "localhost"
    port = 5672
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=hostname, port=port))
    channel = connection.channel()

    exchangename="afterlife_topic"
    channel.exchange_declare(exchange=exchangename, exchange_type='topic')

    message = json.dumps(e["message"], default=str)

    channel.queue_declare(queue='errorhandler', durable=True)
    channel.queue_bind(exchange=exchangename, queue='errorhandler', routing_key='*.error')
    channel.basic_publish(exchange=exchangename, routing_key="mailjet.error", body=message,
        properties=pika.BasicProperties(delivery_mode = 2) 
    )
    print("Mailjet status ({:d}) sent to error handler.".format(e["status"]))

    connection.close()


if __name__ == '__main__':
    app.run(port=5555, debug=True)
