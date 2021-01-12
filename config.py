import os
import json

with open('key.json') as f:
    firebase_config = json.load(f)
f.close()


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'thisisasecretekey'
    FIREBASE_CONFIG = firebase_config
