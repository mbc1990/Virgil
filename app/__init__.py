
from flask import Flask, g
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object('config') 
db = SQLAlchemy(app)

from app import views, poem_queue
app.poem_queue = poem_queue.Poem_Queue()
