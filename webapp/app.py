from flask import Flask
from flask_sockets import Sockets

app = Flask(__name__)
sockets = Sockets(app)


@app.route('/dashboard')
def dashboard():
    """Webpage that displays status info and some management functionality"""

    return 'dashboard 1', 501

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
