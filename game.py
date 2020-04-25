from flask import Blueprint, render_template, redirect, url_for, request
from . import db
from flask_login import login_required, current_user
from .models import Game, Round, Hand, Card, Partner, Player
from .players import game_started
import random

game = Blueprint('game', __name__)
bidding_completed = False
partner_chosen = False

def get_hand():
	player = Player.query.filter_by(email=current_user.email).first()
	game = db.session.query(Game).order_by(Game.id.desc()).first()
	hand_card_ids = Hand.query.filter_by(player_id=player.id).filter_by(game_id=game.id).first().cards
	cards = []
	for hand_card_id in hand_card_ids:
		card = Card.query.filter_by(id=hand_card_id.card).first()
		cards.append(card.suit + " + " + card.value)
	return cards

@game.route('/bid')
@login_required
def bid():
	player = Player.query.filter_by(email=current_user.email).first()
	game = db.session.query(Game).order_by(Game.id.desc()).first()
	cards = get_hand()
	return render_template('bid.html', already_bid=player.bid, cards=cards)

@game.route('/bid', methods=['POST'])
@login_required
def bid_post():
	global bidding_completed
	if bidding_completed == False:
		player = Player.query.filter_by(email=current_user.email).first()
		game = db.session.query(Game).order_by(Game.id.desc()).first()
		cards = get_hand()
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


@game.route('/trump_and_partner')
@login_required
def choose_trump_and_partner():
	game = db.session.query(Game).order_by(Game.id.desc()).first()
	bidder_id = game.bidder
	player = Player.query.filter_by(email=current_user.email).first()
	number_of_players = len(Player.query.all())
	number_of_partners = int(number_of_players/2)
	suits = ['spades', 'diamonds', 'clubs', 'hearts']
	values = ['A', '2', '3','4','5','6','7','8','9','10', 'J', 'Q', 'K']
	turn = [1] if number_of_players <= 4 else [1,2]
	to_choose = False
	if bidder_id == player.id:
		to_choose = True
	cards = get_hand()
	return render_template('/choose.html', to_choose=to_choose, suits=suits, values=values, turn=turn, number_of_partners=number_of_partners, cards=cards)

@game.route('/trump_and_partner', methods=['POST'])
@login_required
def post_choose_trump_and_partner():
	global partner_chosen
	game = db.session.query(Game).order_by(Game.id.desc()).first()
	trump = request.form.get('trump')
	game.trump = trump
	db.session.commit()
	number_of_players = len(Player.query.all())
	number_of_partners = int(number_of_players/2)
	for i in range(1,number_of_partners):
		new_partner = Partner(game_id=game.id, suit=request.form.get('partner_suit'+str(i)), value=request.form.get('partner_value'+str(i)), turn=int(request.form.get('partner_turn'+str(i))))
		db.session.add(new_partner)
		db.session.commit()
	partner_chosen = True
	return redirect(url_for('game.round', round_id=1))

@game.route('/check_selection')
@login_required
def check_selection():
	global partner_chosen
	return str(partner_chosen)

@game.route('/round/<int:round_id>')
@login_required
def round(round_id):
	return render_template('profile.html', name=round_id)

# Partner and Sur Choose => Bid winner, display to all

# Round Start in recursive fashion (Decide starting point of next round)

# Declase winner and return to lobby (See who was partner)
