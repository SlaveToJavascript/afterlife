import stripe
import pika
import json
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

stripe.api_key = 'sk_test_ScxsPnmGvJobZDnpKrUIP5zD00HCvJFDBs'

@app.route('/')
def index():
    return render_template('index.html', key='pk_test_7Vq9qmZYBNUnRYWjKVe11GLN00ofUZcDC0') #this page brings the user to the homepage whenever it is run.

@app.route('/charge', methods=['POST']) #calls the form action /charge on index.html
def charge():
    try:
        customer = stripe.Customer.create(
            email= request.json['email'],
            source= request.json['token']
        )

        stripe.Charge.create(
            customer=customer.id,
            amount=request.json['amount'] * 100,
            currency='sgd',
            description=request.json['description']
        )
        return jsonify({'status': 'success!'}) #if success, redirect to the success page.
    except stripe.error.StripeError as e:
        send_error(e)
        return jsonify({'status': 'error'}), 500 #redirect to an error page, for our case, put in the error microservice and redirect user.

def send_error(e):
    hostname = "localhost"
    port = 5672
    connection = pika.BlockingConnection(pika.ConnectionParameters('172.17.0.2'))
    channel = connection.channel()

    exchangename="afterlife_topic"
    channel.exchange_declare(exchange=exchangename, exchange_type='topic')

    message = json.dumps(e, default=str)

    channel.queue_declare(queue='errorhandler', durable=True)
    channel.queue_bind(exchange=exchangename, queue='errorhandler', routing_key='*.error')
    channel.basic_publish(exchange=exchangename, routing_key="payment.error", body=message,
        properties=pika.BasicProperties(delivery_mode = 2) 
    )
    print("Payment status error sent to error handler.")

    connection.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4242, debug=True)


