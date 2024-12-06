import os
from flask import Flask,jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager

app = Flask(__name__)
app.config['SECRET_KEY'] = 'aps$1232'
app.config['JWT_SECRET_KEY'] = 'qw@r4'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 300  
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = 86400 
basedir = os.path.abspath(os.path.dirname(__file__))

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'+os.path.join(basedir,'Library.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
Migrate(app,db)
jwt = JWTManager(app)


from app import views

