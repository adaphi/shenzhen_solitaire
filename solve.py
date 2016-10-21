import copy
import itertools
import sys

# Generate valid cards
valid_nums = range(1,10) + ['D']
valid_suits = ['R', 'G', 'B']
valid_cards = [str(num) + suit for suit, num in itertools.product(valid_suits, valid_nums)] + ['A']

def main():
	solved = False
	states = [(apply(get_initstate()),[])]

	#solved, moves = solve_with( apply(get_initstate()) )
	for state in states:
		if is_solved(state[0]):
			solved = True
			break

		states.extend([(apply(newstate), state[1] + [move]) for newstate, move in valid_moves(state[0]) if newstate not in [state[0] for state in states]])

	if not solved:
		print 'No solution'
		sys.exit(1)

	print_moves(state[1])

def solve_with( state ):
	valid = valid_moves(state)
	for new_state, move in valid:
		new_state = apply(new_state)
		if is_solved(new_state):
			return True, [move]
		solved, moves = solve_with( new_state )
		if solved:
			moves.append( move )
			return True, moves
	return False, []

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

	initstate['rows'][0] = [ 'DR', '9G', 'DR', '5G', '9R' ]
	initstate['rows'][1] = [ 'DR', '3G', '3B', '4G', '4R' ]
	initstate['rows'][2] = [ 'DG', '8G', 'DB', '6G' ]
	initstate['rows'][3] = [ 'DB', '8B', '7G', '9B', 'DG' ]
	initstate['rows'][4] = [ '1R', 'DB', '5R', '6R', 'DG' ]
	initstate['rows'][5] = [ 'DG', '2B', 'DR', '7B', '2R' ]
	initstate['rows'][6] = [ '5B', '3R', '1B', '8R' ]
	initstate['rows'][7] = [ '7R', 'DB', '4B', 'A', '6B' ]

	initstate['stacks']['G'] = 2

	total = 0
	for row in initstate['rows']:
		total += len(row)
	for suit, stack in initstate['stacks'].items():
		total += stack

	if total != 40:
		print 'Bad number of cards given. Expected 40, but got %s' % total
		sys.exit(1)

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
	if any(get_num(card) != 9 for suit, stack in state['stacks'].items()):
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
		card = row[-1]
		# Can always move to an empty hold
		for hold_pos, hold in enumerate(state['holds']):
			if hold is None:
				new_states.append(move_card(('rows', row_pos), ('holds', hold_pos), state))
				break
		# Can move to other rows if the card allows
		new_states.extend(move_card(('rows', row_pos), ('rows', row_pos2), state) for row_pos2, otherrow in enumerate(state['rows']) if is_empty(otherrow) or can_be_placed_on(otherrow[-1], card))
		# Might be able to move to a stack, if it wasn't done automatically
		if can_be_placed_on(str(state['stacks'][get_suit(card)]) + 'S', card):
			new_states.append(move_card(('rows', row_pos), ('stacks',), state))

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
	card = None
	from_key = from_pos[0]
	if from_key == 'holds':
		card = state['holds'][from_pos[1]]
		newstate['holds'][from_pos[1]] = None
	elif from_key == 'rows':
		card = newstate['rows'][from_pos[1]].pop()

	to_key = to_pos[0]
	if to_key == 'holds':
		newstate['holds'][to_pos[1]] = card
	elif to_key == 'rows':
		newstate['rows'][to_pos[1]].append(card)
	elif to_key == 'ace':
		newstate['ace'] = True
	elif to_key == 'stacks':
		newstate['stacks'][get_suit(card)] = get_num(card)

	return newstate, [from_pos, to_pos]

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

	return newstate, ['collapse']


# Represents automatic moves
def apply(state):
	changed = False
	# Move the ace, if it is showing
	ace = [row_pos for row_pos, row in enumerate(state['rows']) if not is_empty(row) and is_ace(row[-1])]
	if ace:
		state, _ = move_card(('rows', ace[0]), ('ace',), state)
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
			state, _ = move_card(('rows', row_pos), ('stacks',), state)
			changed = True

	# If anything changed, keep going
	if changed:
		return apply(state)

	return state

def print_moves(moves):
	for move in moves:
		if move[0] == 'collapse':
			print 'Collapse dragons'
			continue

		instruction = 'Move card from %s #%s to %s'
		from_place = move[0][0][:-1]
		from_pos = move[0][1] + 1
		to_place = move[1][0][:-1]
		if to_place == 'hold' or to_place == 'row':
			to_place += ' #%s' % (move[1][1] + 1)

		print instruction % (from_place, from_pos, to_place)

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
