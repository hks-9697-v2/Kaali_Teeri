from flask import Blueprint, render_template, redirect, url_for, request
from . import db
from .models import Player, Card, Hand, Game, Hand_Card
from flask_login import login_required, current_user
import random

game_started = False

players = Blueprint('players', __name__)

@players.route('/players')
@login_required
def list_players():

	players = Player.query.all()

	present = False if Player.query.filter_by(email=current_user.email).first() is None else True

	return render_template('players.html', players=players, present=present)

@players.route('/add_me')
@login_required
def add_player():
	global game_started
	if game_started == True:
		flash('Game Started wait for game to finish')
		return redirect(url_for('players.list_players'))

	player = Player(email=current_user.email)

	db.session.add(player)

	db.session.commit()

	return redirect(url_for('players.list_players'))

@players.route('/game_query')
@login_required
def game_query():
	global game_started
	return str(game_started)	

@players.route('/start_game')
@login_required
def start_game():
	global game_started
	if game_started == False:
		game_started = True
		distribute_cards()
	return redirect(url_for('game.bid'))

@players.route('/end_game')
@login_required
def end_game():
	global game_started
	game_started = False
	db.session.query(Player).delete()
	db.session.commit()
	print(len(Player.query.all()))

	return redirect(url_for('players.list_players'))

def create_deck(number_of_decks, number_of_players):

	db.session.query(Card).delete()

	number_of_removed_cards = (number_of_decks*52)%(number_of_players)

	suits = ['spades', 'diams', 'clubs', 'hearts']

	values = ['A', '2', '3','4','5','6','7','8','9','10', 'J', 'Q', 'K']

	points = [10, 0, 0, 0, 5, 0, 0, 0, 0, 10, 10, 10, 10]

	for suit in suits:
		for point_index,value in enumerate(values):
			if values == '3' and suits == 'spades':
				card = Card(suit = suit, valur = value, points = 30)
				db.session.add(card)
				db.session.commit()
			elif values == '2' and number_of_removed_cards > 0:
				continue
			else:
				card = Card(suit = suit, value = value, points = points[point_index])
				db.session.add(card)
				db.session.commit()        	

def distribute_cards():
	
	players = Player.query.all()

	number_of_players = len(players)
	
	if number_of_players > 4:
		create_deck(2, number_of_players)
	else:
		create_deck(1, number_of_players)

	cards = Card.query.all()
	
	random.shuffle(cards)

	number_of_cards = len(cards)

	number_of_cards_in_hand = int(number_of_cards / number_of_players)
	new_game = Game()
	db.session.add(new_game)
	db.session.commit()
	for i in range(number_of_players):
		new_hand = Hand(player_id=players[i].id, game_id=new_game.id)
		db.session.add(new_hand)
		db.session.commit()
		for j in range(number_of_cards_in_hand):
			hand_card = Hand_Card(card=cards[i*number_of_cards_in_hand+j].id, hand_id=new_hand.id)
			db.session.add(hand_card)
			db.session.commit()
	