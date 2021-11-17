# Download the helper library from https://www.twilio.com/docs/python/install
import twilio
import twilio.rest
import json
from twilio.rest import Client
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

account_sid = 'AC751f2965fc7bbf4922e1d46b79bfa631'
auth_token = 'ed6180541cd11cd507dfee3d08e3bf21'

@app.route('/editnotif/<string:orderid>', methods=['POST'])
def editnotif(orderid):
    client = Client(account_sid, auth_token)
    previousUT = request.json.get('previousUT', None)
    newUT = request.json.get('newUT', None)
    details = "Undertaker for Order " + orderid + " changed from " + previousUT + " to " + newUT

    message = client.messages \
                    .create(
                        body=details,
                        from_='+12056563594',
                        to='+6583662434'
                    )
    # return message.sid
    # return message.status
    return {'sid': message.sid, 'status': message.status}

@app.route('/delnotif/<string:orderid>', methods=['POST'])
def delnotif(orderid):
    client = Client(account_sid, auth_token)
    details = "Order " + orderid + " deleted"

    message = client.messages \
                    .create(
                        body=details,
                        from_='+12056563594',
                        to='+6583662434'
                    )
    # return message.sid
    # return message.status
    return {'sid': message.sid, 'status': message.status}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3333, debug=True)