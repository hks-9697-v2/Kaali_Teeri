from flask import Blueprint, render_template, redirect, url_for, request
from . import db
from flask_login import login_required, current_user
from .models import Game, Round, Hand, Card, Partner, Player
from .players import game_started
import random

game = Blueprint('game', __name__)
bidding_completed = False

@game.route('/bid')
@login_required
def bid():
	player = Player.query.filter_by(email=current_user.email).first()
	game = db.session.query(Game).order_by(Game.id.desc()).first()
	hand_card_ids = Hand.query.filter_by(player_id=player.id).filter_by(game_id=game.id).first().cards
	cards = []
	for hand_card_id in hand_card_ids:
		card = Card.query.filter_by(id=hand_card_id.card).first()
		cards.append(card.suit + " + " + card.value)
	return render_template('bid.html', already_bid=player.bid, cards=cards)

@game.route('/bid', methods=['POST'])
@login_required
def bid_post():
	global bidding_completed
	if bidding_completed == False:
		player = Player.query.filter_by(email=current_user.email).first()
		game = db.session.query(Game).order_by(Game.id.desc()).first()
		hand_card_ids = Hand.query.filter_by(player_id=player.id).filter_by(game_id=game.id).first().cards
		cards = []
		for hand_card_id in hand_card_ids:
			card = Card.query.filter_by(id=hand_card_id.card).first()
			cards.append(card.suit + " + " + card.value)
		if player.bid == True:
			return render_template('bid.html', already_bid=player.bid, cards=cards)
		bid_points = int(request.form.get('bid'))
		if bid_points == -1:
			number_of_players = len(Player.query.all())
			bid_points = 150 if number_of_players <= 4 else 270
		if game.bidder is None:
			game.bid = bid_points
			game.bidder = player.id
			db.session.commit()
		elif game.bid < bid_points:
			game.bid = bid_points
			game.bidder = player.id
			db.session.commit()
		player.bid = True
		db.session.commit()
		return render_template('bid.html', already_bid=True, cards=cards)
	else:
		return render_template('bid.html', already_bid=True)

@game.route('/bidding_completed')
@login_required
def check_bidding_completed():
	global bidding_completed
	if bidding_completed==True:
		return str(True)
	else:
		players = Player.query.all()
		bidding_bool = [i.bid for i in players]
		print(bidding_bool)
		if all(bidding_bool):
			bidding_completed = True
			return str(True)
		else:
			return str(False)


@game.route('/round/<int:round_id>')
@login_required
def round(round_id):
	return render_template('profile.html', name=round_id)
# 	TODO: Remove mod number of 2s

# Bidding => Round robin default winner

# Partner and Sur Choose => Bid winner, display to all

# Round Start in recursive fashion (Decide starting point of next round)

# Declase winner and return to lobby (See who was partner)
