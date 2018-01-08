# HTTP/Websocket server for running Keras models on Heroku

This repository contains two things:

- A `Dockerfile`, which installs [scikit-image](http://scikit-image.org/) and [Keras](https://keras.io) with [miniconda](http://conda.pydata.org/miniconda.html), and a few [pip](https://pip.pypa.io/en/stable/) dependencies.
- A [Flask](http://flask.pocoo.org) `webapp`, which:
  - Downloads trained keras model files from S3
  - Takes input data from websocket connections and returns predictions

I have multiple projects that use roughly the same structure:
- webapp captures images and sends them over a websocket connection to a server that feeds each image through a Keras model (that has been trained locally) and returns predictions over a websocket.

```
                        -------------------------
                       | Flask app                |
 ------     images     |    -------------------   |
|      | -----------------> | project specific |  |
| web  |               |    | Keras model      |  |
| page |               |     -------+----------   |
|      |               |            |             |
|      | <--------------------------+             |
 ------   image labels |                          |
                        -------------------------
```

I'm serving a very low volume of requests and the backend for each app is essentially the same, so I'd like to use one Heroku dyno to serve everything for now for simplicity.

Trained models will be stored in [S3](https://aws.amazon.com/s3/) and retrieved by the Flask app as needed, so I can let Amazon worry about authentication and persistence.

This project's structure is based on Heroku's [Miniconda example](https://github.com/heroku-examples/python-miniconda), and some parts of this particular file are copied verbatim.

## Deploy this Application:

Deploy with the [Container Registry and Runtime](https://devcenter.heroku.com/articles/container-registry-and-runtime):

     $ heroku plugins:install heroku-container-registry
     $ heroku container:login
     
     $ cd model-server
     
     $ heroku create
     $ heroku container:push 

