FROM heroku/miniconda
RUN conda install scikit-image
RUN conda install keras

# Grab requirements.txt.
ADD ./webapp/requirements.txt /tmp/requirements.txt

# Install dependencies
RUN pip install -qr /tmp/requirements.txt

# Add our code
ADD ./webapp /opt/webapp/
WORKDIR /opt/webapp

CMD gunicorn -k flask_sockets.worker --bind 0.0.0.0:$PORT wsgi
