import json
from flask import Flask
from flask_sockets import Sockets
import boto3
import botocore
import numpy as np
import keras
from keras.models import load_model
import tensorflow as tf


app = Flask(__name__)
app.config.from_pyfile('aws_config.cfg')
sockets = Sockets(app)

graph = tf.get_default_graph()


def get_prediction(model, image):
    """Preprocess image, pass to model, and return prediction"""
    _, rows, cols, channels = model.layers[0].input_shape
    reshaped = np.array([np.reshape(image, (rows, cols, channels))])
    result = model.predict(reshaped, batch_size=1)

    return result[0]


def get_session():
    return boto3.session.Session(
        aws_access_key_id=app.config['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=app.config['AWS_SECRET_ACCESS_KEY'],
        region_name=app.config['REGION_NAME']
    )


def get_available_models():
    session = get_session()
    s3 = session.resource('s3')

    bucket = s3.Bucket(app.config['S3_BUCKET'])
    return bucket.objects.all()


@app.route('/dashboard')
def dashboard():
    """Webpage that displays status info and some management functionality"""
    model_file_names = ', '.join(key.key for key in get_available_models())

    return 'Available models: {}'.format(model_file_names)


@app.route('/models')
def models():
    """Get list of valid model names"""
    model_file_names = [key.key for key in get_available_models()]

    return json.dumps({'models': model_file_names})


@app.route('/models/<string:model_name>/input_shape')
def get_input_shape(model_name):
    """Get dimensions and number of channels of input image"""
    session = get_session()
    s3 = session.resource('s3')

    try:
        s3.Object(app.config['S3_BUCKET'], model_name).download_file(model_name)
    except botocore.exceptions.ClientError:
        return json.dumps({'error': 'failed to load model'})
    else:
        global graph

        with graph.as_default():
            model = load_model(model_name)
            data_format = model.layers[0].data_format
            if data_format == 'channels_last':
                _, height, width, channels = model.layers[0].input_shape
            elif data_format == 'channels_first':
                _, channels, height, width = model.layers[0].input_shape

        return json.dumps({
            'width': width,
            'height': height,
            'channels': channels
        })


@sockets.route('/models/<string:model_name>/get_predictions')
def label(ws, model_name):
    """Use model with given name to predict label for data in each message"""

    session = get_session()
    s3 = session.resource('s3')

    try:
        s3.Object(app.config['S3_BUCKET'], model_name).download_file(model_name)
    except botocore.exceptions.ClientError:
        ws.send('Error: model file not found')
        ws.close()
    else:
        global graph

        with graph.as_default():
            model = load_model(model_name)
            model._make_predict_function()

            while not ws.closed:
                message = ws.receive()
                js = json.loads(message)
                arr = np.asarray(js)

                pred = get_prediction(model, arr)

                ws.send(str(list(pred)))


if __name__ == '__main__':
    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler
    server = pywsgi.WSGIServer(('', 5000), app, handler_class=WebSocketHandler)
    server.serve_forever()
