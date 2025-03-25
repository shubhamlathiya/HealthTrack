from flask_pymongo import PyMongo

mongo: PyMongo = PyMongo()


def init_app(app):
    app.config['MONGO_URI'] = 'mongodb://localhost:27017/HealthTrack'
    mongo.init_app(app)
