# bot.py
import os
from random import *

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

bot = commands.Bot(command_prefix='!')

bot.guild = discord.utils.get(bot.guilds, name="games")

bot.players = []
bot.game_in_session = False
bot.joinable = False
bot.liberal_policies_left = 6
bot.liberal_policies_played = 0
bot.fascist_policies_left = 11
bot.fascist_policies_played = 0
bot.policies = []
bot.drawn_policies = []
bot.discarded_policies = []
bot.voting_open = False
bot.voted_yes = 0
bot.voted_no = 0
bot.has_voted = []


@bot.event
async def on_ready():
	print(f'{bot.user.name} has connected to Discord!')

@bot.event
async def on_command_error(ctx, error):
	if hasattr(ctx.command, 'on_error'):
		return
		
	ignored = (commands.CommandNotFound, commands.UserInputError)
	
	error = getattr(error, 'original', error)
	
	if isinstance(error, ignored):
		return
	
	if isinstance(error, commands.CommandNotFound):
		return
	elif isinstance(error, commands.MissingPermissions):
		missing = [perm.replace('_', ' ').replace('guild', 'server').title() for perm in error.missing_perms]
		if len(missing) > 2:
			fmt = '{}, and {}'.format("**, **".join(missing[:-1]), missing[-1])
		else:
			fmt = ' and '.join(missing)
		_message = 'You need the **{}** permission(s) to use this command.'.format(fmt)
		await ctx.send(_message)
		return
	elif isinstance(error, commands.CheckFailure):
		await ctx.send("You do not have permission to use this command.")
		return
	elif isinstance(error, commands.UserInputError):
		await ctx.send("Invalid input.")
		return
	elif isinstance(error, commands.DisabledCommand):
		await ctx.send('This command has been disabled.')
		return
	else:
		await ctx.send("The command has failed for an unlisted reason")
		return

@bot.command(pass_context = True, name = 'debug', help = 'Enables a number of flags to allow for proper debugging - requires \'Antagonist\' role')
@commands.has_role('Antagonist')
async def debug(ctx):
	bot.players.append(ctx.author)
	bot.game_in_session = True
	bot.joinable = True
	bot.liberal_policies_left = 6
	bot.liberal_policies_played = 0
	bot.fascist_policies_left = 11
	bot.fascist_policies_played = 0
	#bot.policies = []
	#bot.drawn_policies = []
	#bot.discarded_policies = []
	bot.chancellor_nominee = ctx.author
	bot.voting_open = True
	#bot.voted_yes = 0
	#bot.voted_no = 0
	await ctx.send("Debug Triggered")

# Commands for gameplay ----------------------------------------------------------------------------------------------------

@bot.event
async def on_message(message):
	channel = message.channel
	they_have_voted = False
	if bot.game_in_session:
		for member in bot.has_voted:
			if message.author == bot.has_voted[member]:
				they_have_voted = True
			else:
				they_have_voted = False
			
		if they_have_voted == False:
			if message.content.startswith('ja'):
				if bot.voting_open:
					bot.voted_yes += 1
					await channel.send("Yes registered, {}!".format(message.author.mention))
				else:
					await channel.send("Voting isn\'t open yet!")
					return
				
			elif message.content.startswith('nein'):
				if bot.voting_open:
					bot.voted_no += 1
					await channel.send("No registered, {}!".format(message.author.mention))
				else:
					await channel.send("Voting isn\'t open yet!")
					return
			else:
				return
			
			if bot.voted_yes + bot.voted_no >= len(bot.players):
				bot.voting_open = False
				bot.voted_yes = 0
				bot.voted_no = 0
				
				await channel.send("Everyone has cast their vote! Voting is now closed.")
				await channel.send("There were {} \'ja\' votes, and {} \'nein\' votes.".format(bot.voted_yes, bot.voted_no))
			
				if bot.voted_yes > bot.voted_no:
					role = discord.utils.get(message.guild.roles, name="Chancellor")
					await bot.chancellor_nominee.add_roles(role)
					await channel.send("The motion passed! {} is now the Chancellor!".format(bot.chancellor_nominee.mention))
				else:
					bot.chancellor_nominee = ""
					await channel.send("The motion failed! No Chancellor has been elected.")
		
		else:
			await ctx.send("You have already voted, {}!".formet(message.author.mention))

	await bot.process_commands(message)
		
#Allows a player to join a game that isn't underway	
@bot.command(pass_context = True, name = 'join_game', help = 'Join the game')
async def join_game(ctx):
	if ctx.guild:
		if not bot.game_in_session:
			if bot.joinable:
				role = discord.utils.get(ctx.guild.roles, name="Secret Hitler")
				if role in ctx.author.roles:
					await ctx.send(f'You\'re already part of the game!')
				else:
					await ctx.author.add_roles(role)
					await ctx.send(":white_check_mark: {} is now in the game!".format(ctx.message.author.mention))
					bot.players.append(ctx.author)
			else:
				await ctx.send("A game has yet to begin / is already in progress!")

# Allows a player to leave a game that isn't underway
@bot.command(pass_context = True, name = 'leave_game', help = 'Leave the game')		
async def leave_game(ctx):
	if ctx.guild:
		if not bot.game_in_session:
			game_role = discord.utils.get(ctx.guild.roles, name="Secret Hitler")
			chancellor_role = discord.utils.get(ctx.guild.roles, name="Chancellor")
			president_role = discord.utils.get(ctx.guild.roles, name="President")
			if game_role in ctx.author.roles:
				await ctx.author.remove_roles(game_role)
				await ctx.author.remove_roles(chancellor_role)
				await ctx.author.remove_roles(president_role)
				await ctx.send(":white_check_mark: {} has now left the game!".format(ctx.message.author.mention))
				bot.players.remove(ctx.author)
			else:
				await ctx.send(f'You aren\'t part of the game yet!')
		else:
			await ctx.send("A game is currently underway!")

# 'Force quits' the game, just in case it gets stuck (ADD CONFIRMATION PROMPT)
@bot.command(pass_context = True, name = 'end_game', help = 'Ends the game')
async def end_game(ctx):
	if ctx.guild:
		if bot.game_in_session:
			bot.game_in_session = False
			for member in bot.players:
				sh_role = discord.utils.get(ctx.guild.roles, name="Secret Hitler")
				president_role = discord.utils.get(ctx.guild.roles, name="President")
				chancellor_role = discord.utils.get(ctx.guild.roles, name="Chancellor")
				#if sh_role in member.roles:
				await member.remove_roles(sh_role)
				#if president_role in member.roles:	
				await member.remove_roles(president_role)
				#if chancellor_role in member.roles:	
				await member.remove_roles(chancellor_role)
				await ctx.send("{} has left the game".format(member.mention))
			await ctx.send("Game ended.")
		else:
			await ctx.send("Can't end game: one isn\'t running!")

@bot.command(pass_context = True, name = 'player_count', help = 'Reports players in game / lobby')
async def player_count(ctx):
	if len(bot.players) == 0:
		await ctx.send("There aren\'t any players!")
	else:
		await ctx.send("Players: " + str(len(bot.players)))
		for player in bot.players:
			await ctx.send(player.mention)
			
# Allows the President to select a new Chancellor
@bot.command(pass_context = True, name = 'appoint', help = 'Allows the President to appoint a Chancellor (@nickname)')
@commands.has_role('Secret Hitler')
@commands.has_role('President')
async def appoint(ctx, nominee):
	if ctx.guild:
		if bot.game_in_session:
			if bot.chancellor_nominee == "":
				for player in bot.players:
					if player.mention == nominee:
						role = discord.utils.get(ctx.guild.roles, name="President")
						if not role in player.roles:
							bot.chancellor_nominee = player
							bot.voting_open == True
							await ctx.send(":white_check_mark: {} has been nominated by {} as Chancellor!".format(player.mention, ctx.message.author.mention))
							await ctx.send("Voting has opened. Please type either \"ja\" or \"nein\" into this chat to place your vote")
							await ctx.send("The game will continue once all players have voted.")
						else:
							await ctx.send("You can't nominate yourself!")
					if nominee == "":
						await ctx.send("Can\'t do that: player isn\'t in this game!")
			else:
				await ctx.send("Can\'t do that: a player has already been nominated as Chancellor")
		else:
			await ctx.send("Can\'t do that: game not in session!")
		
		
# Allows the President to draw 3 policy cards, and DM's them the result		
@bot.command(pass_context = True, name = 'draw_policies', help = 'Allows the President to draw 3 new policies')
@commands.has_role('Secret Hitler')
@commands.has_role('President')
async def draw_policies(ctx):
	if ctx.guild:
		if bot.game_in_session:
			# Check if there is an elected Chancellor in the game
			role = discord.utils.get(ctx.message.guild.roles, name="Chancellor")
			for member in ctx.message.guild.members:
				if role in member.roles:
					chancellor_check = True
				else:
					chancellor_check = False
					
			if chancellor_check:
				member = ctx.message.author
				await member.create_dm()
				await member.dm_channel.send(f'Policies will go here!')
			else:
				await ctx.send("There isn't a Chancellor yet!")
			
		else:
			await ctx.send("Can\'t do that: game not in session!")

# Allows the Chancellor to play a policy card
@bot.command(pass_context = True, name = 'play_policy', help = 'Allows the Chancellor to play 1 policy, "liberal" or "fascist"')
@commands.has_role('Secret Hitler')
@commands.has_role('Chancellor')
async def play_policy(ctx, policy_type):
	if ctx.guild:
		if bot.game_in_session:
			await ctx.send("{} played a {} card!".format(ctx.message.author.mention, policy_type))
			if policy_type == "liberal":
				bot.liberal_policies_played += 1
			elif policy_type == "fascist":
				bot.fascist_policies_played += 1
			else:
				return
			lib_address, fasc_address = display_board()
			await ctx.send(file = discord.File(lib_address))
			await ctx.send(file = discord.File(fasc_address))
		else:
			await ctx.send("Can\'t do that: game not in session!")

# Displays the current game boards
def display_board():
	liberal_board = ['Liberal0.png', 'Liberal1.png', 'Liberal2.png', 'Liberal3.png', 'Liberal4.png', 'Liberal5.png']
	fascist_board_56 = ['Fascist(5,6)0.png', 'Fascist(5,6)1.png', 'Fascist(5,6)2.png', 'Fascist3.png', 'Fascist4.png', 'Fascist5.png', 'Fascist6.png']
	fascist_board_78 = ['Fascist(7,8)0.png', 'Fascist(7,8,9,10)1.png', 'Fascist(7,8,9,10)2.png', 'Fascist3.png', 'Fascist4.png', 'Fascist5.png', 'Fascist6.png']
	fascist_board_910 = ['Fascist(9,10)0.png', 'Fascist(7,8,9,10)1.png', 'Fascist(7,8,9,10)2.png', 'Fascist3.png', 'Fascist4.png', 'Fascist5.png', 'Fascist6.png']
	if len(bot.players) < 7:
		liberal_address = liberal_board[bot.liberal_policies_played]
		liberal_address = os.path.join(r"D:\Projects\Discord\Bots\Games_Bot\Secret-Hitler-Bot\Images", liberal_address)
		
		fascist_address = fascist_board_56[bot.fascist_policies_played]
		fascist_address = os.path.join(r"D:\Projects\Discord\Bots\Games_Bot\Secret-Hitler-Bot\Images", fascist_address)
		
	elif len(bot.players) < 9:
		liberal_address = liberal_board[bot.liberal_policies_played]
		liberal_address = os.path.join(r"D:\Projects\Discord\Bots\Games_Bot\Secret-Hitler-Bot\Images", liberal_address)
		
		fascist_address = fascist_board_78[bot.fascist_policies_played]
		fascist_address = os.path.join(r"D:\Projects\Discord\Bots\Games_Bot\Secret-Hitler-Bot\Images", fascist_address)
		
	else:
		liberal_address = liberal_board[bot.liberal_policies_played]
		liberal_address = os.path.join(r"D:\Projects\Discord\Bots\Games_Bot\Secret-Hitler-Bot\Images", liberal_address)
		
		fascist_address = fascist_board_910[bot.fascist_policies_played]
		fascist_address = os.path.join(r"D:\Projects\Discord\Bots\Games_Bot\Secret-Hitler-Bot\Images", fascist_address)

	return liberal_address, fascist_address
	
	
# Runs the game ----------------------------------------------------------------------------------------------------

def shuffle_deck():
	for card in range(0, (bot.liberal_policies + bot.fascist_policies)):
		random_bin = randint(0,2)
		if random_bin == 0:
			if bot.liberal_policies > 0:
				bot.liberal_policies -= 1
				bot.policies.append("liberal")
			else:
				if bot.fascist_policies > 0:
					bot.fascist_policies -= 1
					bot.policies.append("fascist")
		elif random_bin >= 1:
			if bot.fascist_policies > 0:
				bot.fascist_policies -= 1
				bot.policies.append("fascist")
			else:
				if bot.liberal_policies > 0:
					bot.liberal_policies -= 1
					bot.policies.append("liberal")
	
	print("Policy Deck: ")
	print(bot.policies)

@bot.command(pass_context = True, name = 'open_lobby', help = 'Allows players to join game / starts game sequence - DON\'T RUN THIS YET')
async def open_lobby(ctx):
	bot.players = []
	bot.game_in_session = False
	bot.joinable = True
	bot.liberal_policies = 6
	bot.fascist_policies = 11
	bot.liberal_policies_played = 0
	bot.fascist_policies_played = 0
	bot.policies = []
	bot.drawn_policies = []
	bot.discarded_policies = []
	bot.chancellor_nominee = ""
	bot.voting_open = False
	bot.voted_yes = 0
	bot.voted_no = 0
	bot.has_voted = []
	
	await ctx.send("Lobby open!")
	await ctx.send("Join the lobby with the \"!join_game\" command!")
	await ctx.send("Leave the lobby with the \"!leave_game\" command!")
	await ctx.send("Check which players are in the lobby with the \"!player_count\" command!")
	await ctx.send("When all players have joined the lobby, start the game with the \"!start_game\" command!")

# Starts the game (ADD CONFIRMATION PROMPT)			
@bot.command(pass_context = True, name = 'start_game', help = 'Starts the game')
async def start_game(ctx):
	if ctx.guild:
		if bot.game_in_session:
			await ctx.send("Can\'t start game: one\'s already running!")
			return
		else:
			bot.game_in_session = True
			bot.joinable = False
			
			# Rebuild player list now that changes have been finalized
			bot.players = []
			role = discord.utils.get(ctx.message.guild.roles, name="Secret Hitler")
			for member in ctx.message.guild.members:
				if role in member.roles: 
					bot.players.append(member)
			
			# Create temporory list for assigning roles
			unassigned_players = bot.players
			
			# Check for correct player count
			if len(unassigned_players) < 5 or len(unassigned_players) > 10:
				await ctx.send("Game start failed: there aren\'t between 5 and 10 players!")
				unassigned_players = []
				await end_game(ctx)
				return
			
			await ctx.send("Game starting! (Lobby has closed)")
			
			# Generates the deck
			shuffle_deck()
			
			# Displays the game board
			lib_address, fasc_address = display_board()
			await ctx.send(file = discord.File(lib_address))
			await ctx.send(file = discord.File(fasc_address))
			
			# Decides what distribution of Fascists, Liberals, and Hitler to use based on the player count, and assigns them to people randomly
			# For 5 or 6 players, assign one Fascist + Hitler
			if len(unassigned_players) == 5 or len(unassigned_players) == 6:
				selection = random.choice(range(0, len(unassigned_players) - 1))
				member = unassigned_players[selection]
				await member.create_dm()
				await member.dm_channel.send(f'You are Hitler!')
				unassigned_players.remove(member)
		
				selection = random.choice(range(0, len(unassigned_players) - 1))
				member = unassigned_players[selection]
				await member.create_dm()
				await member.dm_channel.send(f'You are a fascist!')
				unassigned_players.remove(member)
			
			# For 7 or 8 players, assign two Fascists + Hitler
			elif len(unassigned_players) == 7 or len(unassigned_players) == 8:
				selection = random.choice(range(0, len(unassigned_players) - 1))
				member = unassigned_players[selection]
				await member.create_dm()
				await member.dm_channel.send(f'You are Hitler!')
				unassigned_players.remove(member)
		
				for i in range (0, 2):
					selection = random.choice(range(0, len(unassigned_players) - 1))
					member = unassigned_players[selection]
					await member.create_dm()
					await member.dm_channel.send(f'You are a fascist!')
					unassigned_players.remove(member)
		
			# For 9 or 10 players, assign three Fascists + Hitler
			else:
				selection = random.choice(range(0, len(unassigned_players) - 1))
				member = unassigned_players[selection]
				await member.create_dm()
				await member.dm_channel.send(f'You are Hitler!')
				unassigned_players.remove(member)
	
				for i in range (0, 3):
					selection = random.choice(range(0, len(unassigned_players) - 1))
					member = unassigned_players[selection]
					await member.create_dm()
					await member.dm_channel.send(f'You are a fascist!')
					unassigned_players.remove(member)
			
			# For everyone that isn't a Fascist or Hitler, make them a Liberal
			for member in unassigned_players:
				await member.create_dm()
				await member.dm_channel.send(f'You are a liberal!')
				unassigned_players.remove(member)
		
			# Randomly select a President from the pool of players (MIGHT BE BETTER AS OWN FUNCTION?)
			selection = random.choice(range(0, len(bot.players) - 1))
			member = bot.players[selection]
			member.add_roles("President")
			await ctx.send("Our first president is... {}!".format(member.mention))
			await ctx.send("When you are ready, {}, please appoint a Chancellor with the \"!appoint @nickname\" command!".format(member.mention))
	
# Remind president to draw when ready
# Record drawn policies
# Remove drawn policies from "deck"
# Add played policies to "board"
# Add unplayed policies to discarded policies "deck"
	
# New round
# Reassign president role to next in list
# Take away Chancellor role


# Just for fun --------------------------------------------------

@bot.command(name = 'roll_dice', help = 'Simultes rolling dice')
async def roll(ctx, number_of_dice: int, number_of_sides: int):
	dice = [
		str(random.choice(range(1, number_of_sides + 1)))
		for _ in range(number_of_dice)
	]
	await ctx.send(','.join(dice))	

bot.run(TOKEN)