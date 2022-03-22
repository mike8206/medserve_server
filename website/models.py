from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    account = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    userName = db.Column(db.String(150))
    email = db.Column(db.String(150))
    group = db.Column(db.String(150))
    token = db.Column(db.String(150))
    notes = db.relationship('Note')
    cases = db.relationship('MyCaseList')

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(10000))
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Case(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    redcap_id = db.Column(db.String(150), unique=True)
    name = db.Column(db.String(150))
    sex = db.Column(db.String(150))
    birthday = db.Column(db.Date, index=True)
    age = db.Column(db.String(150))
    location = db.Column(db.String(150))

class MyCaseList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    list = db.Column(db.PickleType)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

# class Chart(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     chartS = db.Column(db.String(10000))
#     chartO = db.Column(db.String(10000))
#     chartA = db.Column(db.String(10000))
#     chartP = db.Column(db.String(10000))
#     date = db.Column(db.DateTime(timezone=True), default=func.now())
#     case_id = db.Column(db.Integer, db.ForeignKey('case.id'))

# class Photo(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     filename = db.Column(db.String(150))
#     fileobject = db.Column(db.LargeBinary)
#     date = db.Column(db.DateTime(timezone=True), default=func.now())
#     case_id = db.Column(db.Integer, db.ForeignKey('case.id'))