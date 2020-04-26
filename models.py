from flask_login import UserMixin
from . import db

from sqlalchemy import Table, Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))

class Player(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	email = db.Column(db.String(100), unique=True)
	bid = db.Column(db.Boolean, default=False)

class Game(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	rounds = db.relationship('Round', backref='game', lazy=True)
	hands = db.relationship('Hand', backref='game', lazy=True)
	bidder = db.Column(db.Integer)
	partners = db.relationship('Partner', backref='game', lazy=True)
	bid = db.Column(db.Integer)
	trump = db.Column(db.String(100))

class Partner(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	player_id = db.Column(db.Integer)
	game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=False)	
	suit = db.Column(db.String(100))
	value = db.Column(db.String(100))
	turn_number = db.Column(db.Integer)

class Round(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=False)
	cards = db.relationship('Round_Card', backref='round', lazy=True)
	winner = db.Column(db.Integer)
	points = db.Column(db.Integer)
	starting_player = db.Column(db.Integer, nullable=False)

class Hand(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	player_id = db.Column(db.Integer, nullable=False)
	game_id = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=False)
	cards = db.relationship('Hand_Card', backref='hand', lazy=True, cascade="all, delete-orphan")

class Round_Card(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	card = db.Column(db.Integer)
	round_id = db.Column(db.Integer, db.ForeignKey('round.id'))

class Hand_Card(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	card = db.Column(db.Integer)
	hand_id = db.Column(db.Integer, db.ForeignKey('hand.id'))

class Card(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	suit = db.Column(db.String(100))
	value = db.Column(db.String(100))
	points = db.Column(db.Integer)