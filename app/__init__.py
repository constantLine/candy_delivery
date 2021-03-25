from flask import Flask, request, jsonify, abort, make_response
from werkzeug.wrappers import BaseResponse as Response
from __init__.config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
from models import *


from app import routes


