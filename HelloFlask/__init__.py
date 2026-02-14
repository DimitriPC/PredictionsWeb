from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

db = SQLAlchemy()   # create db object (no app yet)

app = Flask(__name__)


app.config["SQLALCHEMY_DATABASE_URI"] = (
    os.environ.get("DATABASE_URL") or
    "postgresql://dimitri:4939@localhost:5432/mydb"
)


app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)    # attach db to app

# Import models so Flask-Migrate sees them
from HelloFlask import tables

# Import routes last
import HelloFlask.routes
