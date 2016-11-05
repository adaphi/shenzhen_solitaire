import copy
import itertools
import sys

from heapq import *

# Generate valid cards
# Three suits, numbered 1-9, plus 4 "dragons" of each suit, plus one ace.
valid_nums = range(1,10) + ['D']*4
valid_suits = ['R', 'G', 'B']
valid_cards = [str(num) + suit for suit, num in itertools.product(valid_suits, valid_nums)] + ['A']

max_iter = 5000

def main():
	solved = False
	seen_states = []
	initstate = get_initstate()
	states = [(score(initstate), initstate, [])]
	count=0

	print 'Thinking...'
	while states:
		count+= 1
		_, state, moves = heappop(states)
		if is_solved(state):
			solved = True
			break

		for newstate, newmove in valid_moves(state):
			newstate = apply(newstate)
			if is_solved(newstate):
				heappush(states, (-999, newstate, moves + [newmove]))
				break
			if not any(states_equal(newstate, seen_state) for seen_state in seen_states):
				seen_states.append(newstate)
				heappush(states, (score(newstate), newstate, moves + [newmove]))

		if count == max_iter:
			print 'Couldn\'t solve after %s iterations' % max_iter
			print 'Best go so far:'
			_, state, moves = heappop(states)
			print state
			print_moves(moves)
			sys.exit(1)

	if not solved:
		print 'No solution'
		sys.exit(1)

	print 'Solved!'
	print_moves(moves)

def get_initstate():
	# 3 holds, 8 rows, 1 ace, 3 "finished" stacks
	initstate = {
		'holds': [None]*3,
		'rows': [[]]*8,
		'ace': False,
		'stacks': {suit: 0 for suit in valid_suits}
	}

	print 'Enter initial state:'
	#for i in range(0,8):
	#	row = [x.strip().upper() for x in raw_input('Row %s: ' % (i+1)).split(',')]
	#	if any(card not in valid_cards for card in row):
	#		print 'Invalid card given, must be Num + Suit'
	#		sys.exit(1)
	#	initstate['rows'][i] = row

	#prompt = raw_input('Any in stacks? (Y/N): ').strip().upper()
	#if prompt:
	#	stack_r = raw_input('Enter highest number in stack for RED (0 for nothing): ').strip().upper()
	#		if not stack_r.isdigit() or int(stack_r) > 9:
	#			print 'Bad stack number'
	#			sys.exit(1)
	#		if int(stack_r) > 0:
	#			initstate['stacks']['R'] = int(stack_r)
	#	stack_g = raw_input('Enter highest number in stack for GREEN (0 for nothing): ').strip().upper()
	#		if not stack_g.isdigit() or int(stack_g) > 9:
	#			print 'Bad stack number'
	#			sys.exit(1)
	#		if int(stack_g) > 0:
	#			initstate['stacks']['G'] = int(stack_g)
	#	stack_b = raw_input('Enter highest number in stack for BLACK (0 for nothing): ').strip().upper()
	#		if not stack_b.isdigit() or int(stack_b) > 9:
	#			print 'Bad stack number'
	#			sys.exit(1)
	#		if int(stack_b) > 0:
	#			initstate['stacks']['B'] = int(stack_b)

	# Test puzzle
	initstate['rows'][0] = [ 'DR', '1R', '7G', 'DB', '5R' ]
	initstate['rows'][1] = [ '4G', '4B', 'DG', '3R', '5G' ]
	initstate['rows'][2] = [ '3G', 'DR', 'DB', '6G', 'DB' ]
	initstate['rows'][3] = [ 'DG', '6R', 'DG', 'A', '9R' ]
	initstate['rows'][4] = [ '4R', 'DB', '9G', '1G', '8R' ]
	initstate['rows'][5] = [ '3B', 'DR', '8B', '7B', '9B' ]
	initstate['rows'][6] = [ '8G', '2R', '2G', 'DR', '7R' ]
	initstate['rows'][7] = [ '5B', 'DG', '1B', '6B', '2B' ]

	total = 0
	for row in initstate['rows']:
		total += len(row)
	for suit, stack in initstate['stacks'].items():
		total += stack

	if total != 40:
		print 'Bad number of cards given. Expected 40, but got %s' % total
		sys.exit(1)

	# We expect every card to appear exactly once
	expected_cards = valid_cards[:]
	for suit, stack in initstate['stacks'].items():
			if stack > 0:
				for card in [str(num+1) + suit for num in range(0,stack)]:
					expected_cards.remove(card)

	for row_pos, row in enumerate(initstate['rows']):
		for card_pos, card in enumerate(row):
			if card not in expected_cards:
				print 'Bad inital state: duplicate card found at row %s, card %s' % ((row_pos+1), (card_pos+1))
				sys.exit(1)
			expected_cards.remove(card)

	if len(expected_cards) > 0:
		print 'Bad initial state: Missing cards ' + expected_cards

	return initstate

def is_solved(state):
	# Are all holds closed?
	if any(not is_closed(hold) for hold in state['holds']):
		return False

	# Any cards left in the rows?
	if any(not is_empty(row) for row in state['rows']):
		return False

	# Is the ace in?
	if not state['ace']:
		return False

	# Are all stacks showing 9?
	if any(stack != 9 for suit, stack in state['stacks'].items()):
		return False

	return True

def valid_moves(state):
	new_states = []
	# Check hold cards - these might be moveable
	for hold_pos, card in enumerate(state['holds']):
		if card is None or is_closed(card):
			continue
		# Can always move to an empty row, might be able to move to some non-empty rows
		new_states.extend(move_card(('holds', hold_pos), ('rows', row_pos), state) for row_pos, row in enumerate(state['rows']) if is_empty(row) or can_be_placed_on(row[-1], card))
		# Might be able to move to a stack, if it wasn't done automatically
		if can_be_placed_on(str(state['stacks'][get_suit(card)]) + 'S', card):
			new_states.append(move_card(('holds', hold_pos), ('stacks',), state))

	# Check row cards, we might be able to move them about
	for row_pos, row in enumerate(state['rows']):
		if is_empty(row):
			continue
		end_pos = len(row)-1
		end_card = row[-1]
		# Can always move the current last card to an empty hold
		for hold_pos, hold in enumerate(state['holds']):
			if hold is None:
				new_states.append(move_card(('rows', row_pos, end_pos), ('holds', hold_pos), state))
				break
		# Can move to other rows if the card allows
		# We can move several at once if it's valid to do so
		moveable_cards = []
		for card_pos, card in reversed(list(enumerate(row))):
			moveable_cards.append((card_pos, card))
			if card_pos > 0 and not can_be_placed_on(row[card_pos-1], card):
				break
		for card_pos, card in moveable_cards:
			new_states.extend(move_card(('rows', row_pos, card_pos), ('rows', row_pos2), state) for row_pos2, otherrow in enumerate(state['rows']) if is_empty(otherrow) or can_be_placed_on(otherrow[-1], card))
		# Might be able to move the end card to a stack, if it wasn't done automatically
		if can_be_placed_on(str(state['stacks'][get_suit(end_card)]) + 'S', end_card):
			new_states.append(move_card(('rows', row_pos, end_pos), ('stacks',), state))

	# Check to see if we can collapse any dragon cards
	hold_dragons = [('holds', hold_pos, card) for hold_pos, card in enumerate(state['holds']) if card is not None and is_dragon(card)]
	row_dragons = [('rows', row_pos, row[-1]) for row_pos, row in enumerate(state['rows']) if not is_empty(row) and is_dragon(row[-1])]
	dragons = { suit: [dragon for dragon in hold_dragons + row_dragons if get_suit(dragon[2]) == suit] for suit in valid_suits }
	for suit, cards in dragons.items():
		if len(cards) == 4:
			# We need an empty hold, or one of the dragons needs to be in a hold already
			if any(card[0] == 'holds' for card in cards) or any(hold is None for hold in state['holds']):
				new_states.append(collapse_dragons(cards, state))

	return new_states

def move_card(from_pos, to_pos, state):
	newstate = copy.deepcopy(state)
	cards = []
	from_key = from_pos[0]
	if from_key == 'holds':
		cards = [state['holds'][from_pos[1]]]
		newstate['holds'][from_pos[1]] = None
	elif from_key == 'rows':
		cards = newstate['rows'][from_pos[1]][from_pos[2]:]
		newstate['rows'][from_pos[1]] = newstate['rows'][from_pos[1]][:from_pos[2]]

	to_key = to_pos[0]
	if to_key == 'holds':
		newstate['holds'][to_pos[1]] = cards[0]
	elif to_key == 'rows':
		newstate['rows'][to_pos[1]].extend(cards)
	elif to_key == 'ace':
		newstate['ace'] = True
	elif to_key == 'stacks':
		newstate['stacks'][get_suit(cards[0])] = get_num(cards[0])

	return newstate, (from_pos, to_pos)

def collapse_dragons(dragons, state):
	newstate = copy.deepcopy(state)
	# Find somewhere to put them
	holds = [pos for key, pos, card in dragons if key == 'holds']
	target_hold = holds[0] if len(holds) > 0 else [hold_pos for hold_pos, hold in enumerate(state['holds']) if hold is None][0]

	# Remove all the dragons
	for key, pos, card in dragons:
		if key == 'holds':
			newstate['holds'][pos] = None
		elif key == 'rows':
			newstate['rows'][pos].pop()

	# Close the hold they went to
	newstate['holds'][target_hold] = 'X'

	return newstate, ('collapse')


# Represents automatic moves
def apply(state):
	changed = False
	# Move the ace, if it is showing
	ace = [row_pos for row_pos, row in enumerate(state['rows']) if not is_empty(row) and is_ace(row[-1])]
	if ace:
		state, _ = move_card(('rows', ace[0], -1), ('ace',), state)
		changed = True

	# Move any number cards to their home in the stacks, if appropriate
	for row_pos, row in enumerate(state['rows']):
		if is_empty(row):
			continue
		card = row[-1]
		if is_dragon(card):
			continue
		# Can only be moved if all other stacks have the previous number or better
		if all(stack >= get_num(card)-1 for suit, stack in state['stacks'].items()):
			state, _ = move_card(('rows', row_pos, -1), ('stacks',), state)
			changed = True

	# If anything changed, keep going
	if changed:
		return apply(state)

	return state

# Score a state - used for ordering the heap
def score(state):
	score = 0
	# Non-dragon cards in the hold are worth 2
	score += sum(2 for pos, hold in enumerate(state['holds']) if hold is not None and not is_closed(hold) and not is_dragon(hold))
	# Dragons in the hold are worth 1
	score += sum(1 for pos, hold in enumerate(state['holds']) if hold is not None and not is_closed(hold) and is_dragon(hold))
	# From the end of a row, cards sitting on a valid other are (i.e. different suit, one number higher) are worth 0. Every other card in that row is worth 1
	for row in state['rows']:
		row_score = 0
		for card_pos, card in reversed(list(enumerate(row))):
			if (is_dragon(card) or is_ace(card) or (card_pos > 0 and not can_be_placed_on(row[card_pos-1], card))):
				row_score = card_pos + 1
				break
		score += row_score
	return score

# Equality check for states
def states_equal(state1, state2):
	if state1['stacks'] != state2['stacks']:
		return False
	if state1['ace'] != state2['ace']:
		return False
	if sorted(state1['holds']) != sorted(state2['holds']):
		return False
	if sorted(state1['rows']) != sorted(state2['rows']):
		return False
	return True

def print_moves(moves):
	for move in moves:
		if move == 'collapse':
			print 'Collapse dragons'
			continue

		instruction = 'Move card%s from %s #%s to %s'
		card_pos = ''
		from_place = move[0][0][:-1]
		from_pos = move[0][1] + 1
		if from_place == 'row':
			card_pos = ' #%s' % (move[0][2] + 1)
		to_place = move[1][0][:-1]
		if to_place == 'hold' or to_place == 'row':
			to_place += ' #%s' % (move[1][1] + 1)

		print instruction % (card_pos, from_place, from_pos, to_place)

def get_num(card):
	return int(card[0])

def get_suit(card):
	return card[1]

def is_dragon(card):
	return card[0] == 'D'

def is_ace(card):
	return card == 'A'

def is_closed(hold):
	return hold == 'X'

def is_empty(row):
	return len(row) == 0

def can_be_placed_on(undercard, overcard):
	# False if either is a dragon
	if is_dragon(undercard) or is_dragon(overcard):
		return False

	# False if either is the ace
	if is_ace(undercard) or is_ace(overcard):
		return False

	# False if same suit
	if get_suit(undercard) == get_suit(overcard):
		return False

	# True if undercard is 1 higher number than overcard
	if get_num(undercard) == get_num(overcard) + 1:
		return True

	# Otherwise false
	return False

if __name__ == '__main__':
	main()
