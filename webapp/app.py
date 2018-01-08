from flask import Flask
from flask_sockets import Sockets
import boto3

app = Flask(__name__)
app.config.from_pyfile('aws_config.cfg')
sockets = Sockets(app)


def get_available_models():
    session = boto3.session.Session(
        aws_access_key_id=app.config['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=app.config['AWS_SECRET_ACCESS_KEY'],
        region_name=app.config['REGION_NAME']
    )
    s3 = session.resource('s3')

    bucket = s3.Bucket(app.config['S3_BUCKET'])
    return bucket.objects.all()


@app.route('/dashboard')
def dashboard():
    """Webpage that displays status info and some management functionality"""
    model_file_names = ', '.join(key.key for key in get_available_models())

    return 'Available models: {}'.format(model_file_names)


@app.route('/update_models')
def update_models():
    """Reload list of models from S3"""

    return 'update models', 501

@sockets.route('/label/<string:model_name>')
def label(ws, model_name):
    """Use model with given name to predict label for data in each message"""
    while not ws.closed:
        message = ws.receive()

        ws.send(model_name)

if __name__ == '__main__':
    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler
    server = pywsgi.WSGIServer(('', 5000), app, handler_class=WebSocketHandler)
    server.serve_forever()
