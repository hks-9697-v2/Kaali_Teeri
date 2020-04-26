from flask import Blueprint, render_template, redirect, url_for, request
from . import db
from flask_login import login_required, current_user
from .models import Game, Round, Hand, Card, Partner, Player, Hand_Card, Round_Card
from .players import game_started
import random

game = Blueprint('game', __name__)
bidding_completed = False
partner_chosen = False
player_order = []
player_shift = 0
rank = {}
for i in range(2,11):
	rank[str(i)] = i-1
rank['J'] = 11
rank['Q'] = 12
rank['K'] = 13
rank['A'] = 14

def get_hand():
	player = Player.query.filter_by(email=current_user.email).first()
	game = db.session.query(Game).order_by(Game.id.desc()).first()
	hand_card_ids = Hand.query.filter_by(player_id=player.id).filter_by(game_id=game.id).first().cards
	cards = []
	for hand_card_id in hand_card_ids:
		card = Card.query.filter_by(id=hand_card_id.card).first()
		cards.append((card.suit,card.value))
	cards = sorted(cards)
	return cards

def get_round():
	game = db.session.query(Game).order_by(Game.id.desc()).first()
	round_card_ids = db.session.query(Round).order_by(Round.id.desc()).first().cards
	cards = []
	for round_card_id in round_card_ids:
		card = Card.query.filter_by(id=round_card_id.card).first()
		cards.append((card.suit,card.value, card.points))
	return cards

@game.route('/bid')
@login_required
def bid():
	player = Player.query.filter_by(email=current_user.email).first()
	game = db.session.query(Game).order_by(Game.id.desc()).first()
	cards = get_hand()
	return render_template('bid.html', already_bid=player.bid, cards=cards, activityClass="inactiveLink")

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
		return render_template('bid.html', already_bid=True, cards=cards, activityClass="inactiveLink")
	else:
		return render_template('bid.html', already_bid=True, activityClass="inactiveLink")

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
	number_of_partners = int(number_of_players/2)-1
	suits = ['spades', 'diams', 'clubs', 'hearts']
	values = ['A', '2', '3','4','5','6','7','8','9','10', 'J', 'Q', 'K']
	turn = [1] if number_of_players <= 4 else [1,2]
	to_choose = False
	if bidder_id == player.id:
		to_choose = True
	cards = get_hand()
	return render_template('/choose.html', to_choose=to_choose, suits=suits, values=values, turn=turn, number_of_partners=number_of_partners, cards=cards, activityClass="inactiveLink")

@game.route('/trump_and_partner', methods=['POST'])
@login_required
def post_choose_trump_and_partner():
	global partner_chosen, player_order
	game = db.session.query(Game).order_by(Game.id.desc()).first()
	trump = request.form.get('trump')
	game.trump = trump
	db.session.commit()
	number_of_players = len(Player.query.all())
	number_of_partners = int(number_of_players/2) - 1
	print(request.form.get('trump'))
	for i in range(1,number_of_partners):
		new_partner = Partner(game_id=game.id, suit=request.form.get('partner_suit'+str(i)), value=request.form.get('partner_value'+str(i)), turn_number=int(request.form.get('partner_turn'+str(i))))
		db.session.add(new_partner)
		db.session.commit()
	partner_chosen = True
	players = Player.query.all()
	player_order1 = []
	for player in players:
		player_order1.append(player.id)
	bidder_id = game.bidder
	bidder_index = player_order1.index(bidder_id)
	print(player_order1)
	temp1 = player_order1[bidder_index:]
	temp1.extend(player_order1[:bidder_index])
	player_order = temp1
	new_round = Round(game_id=game.id, starting_player=bidder_id)
	db.session.add(new_round)
	db.session.commit()
	print(bidder_id)
	print(bidder_index)
	print(player_order)
	print(player_order.index(bidder_id))
	return redirect(url_for('game.play_round', round_id=1))

@game.route('/check_selection')
@login_required
def check_selection():
	global partner_chosen
	return str(partner_chosen)

@game.route('/round/<int:round_id>')
@login_required
def play_round(round_id):
	global player_order, player_shift
	game = db.session.query(Game).order_by(Game.id.desc()).first()
	round_model = db.session.query(Round).order_by(Round.id.desc()).first()
	partners = game.partners
	partner_cards = []
	for partner in partners:
		partner_cards.append((partner.suit, partner.value, partner.turn_number))
	cards = get_hand()

	table_cards = get_round()

	current_player = Player.query.filter_by(email=current_user.email).first()

	print(rank)

	get_order()

	if len(player_order) <= player_shift:
		winner = 0
		start_suit = table_cards[0][0]
		for i,j in enumerate(table_cards):
			if j[0]==start_suit and rank[j[1]]>rank[table_cards[winner][1]]:
				winner = i
		flag = 0
		for i,j in enumerate(table_cards):
			if j[0]==game.trump:
				if flag==0 or rank[j[1]]>rank[table_cards[winner][1]]:
					winner = i
					flag=1
		round_model.winner = player_order[winner]
		round_model.points = sum(i[2] for i in table_cards)
		db.session.commit()
		new_round = Round(game_id = game.id, starting_player=round_model.winner)
		db.session.add(new_round)
		db.session.commit()
		player_shift = 0
		get_order()
		round_id += 1

	activityClass = "" if current_player.id == player_order[player_shift] else "inactiveLink"

	return render_template('round.html', round_number=round_id, cards=cards, trump=game.trump, partner_cards=partner_cards, table_cards=table_cards, activityClass=activityClass, turn_id=player_shift)

def get_order():
	global player_order
	round_model = db.session.query(Round).order_by(Round.id.desc()).first()
	print(player_order)
	start_index = player_order.index(round_model.starting_player)
	temp1 = player_order[start_index:]
	temp1.extend(player_order[:start_index])
	player_order = temp1

@game.route('/make_move/<string:suit>/<string:value>/<int:round_id>')
@login_required
def post_play_round(suit, value, round_id):
	global player_shift
	game = db.session.query(Game).order_by(Game.id.desc()).first()
	round_model = db.session.query(Round).order_by(Round.id.desc()).first()
	card = Card.query.filter_by(suit=suit).filter_by(value=value).first()
	new_round_card = Round_Card(card = card.id, round_id = round_model.id)
	db.session.add(new_round_card)
	db.session.commit()
	table_cards = get_round()
	player_shift += 1
	used_card = Hand_Card.query.filter_by(card = card.id).first()
	db.session.commit()
	db.session.delete(used_card)
	db.session.commit()
	return redirect(url_for('game.play_round', round_id=round_id))

@game.route('/next_turn/<int:previos_player>')
@login_required
def check_next_turn(previos_player):
	global player_shift
	return str(player_shift != previos_player)

@game.route('/endgame')
@login_required
def endgame():
	global bidding_completed, partner_chosen, player_order, player_shift
	bidding_completed = False
	partner_chosen = False
	player_order = []
	player_shift = 0
	return redirect(url_for('players.end_game'))
