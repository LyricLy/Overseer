description = """A bot to oversee games of Shack Mafia. """
# import dependencies
import discord
import os
import time
import traceback
import asyncio
import random
from discord.ext import commands
from datetime import datetime


# sets working directory to bot's folder
dir_path = os.path.dirname(os.path.realpath(__file__))
os.chdir(dir_path)

prefix = ['!', '.', 'please ']
bot = commands.Bot(command_prefix=prefix, description=description, pm_help=None)


chars = "\\`*_<>#@:~"
def escape_name(name):
    name = str(name)
    for c in chars:
        if c in name:
            name = name.replace(c, "\\" + c)
    return name.replace("@", "@\u200b")  # prevent mentions
bot.escape_name = escape_name


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, discord.ext.commands.errors.CommandNotFound):
        pass  # ...don't need to know if commands don't exist
    if isinstance(error, discord.ext.commands.errors.CheckFailure):
        await ctx.send("You don't have permission to use this command.")
    elif isinstance(error, discord.ext.commands.errors.MissingRequiredArgument):
        formatter = commands.formatter.HelpFormatter()
        await ctx.send("You are missing required arguments.\n{}".format(formatter.format_help_for(ctx, ctx.command)[0]))
    else:
        if ctx.command:
            await ctx.send("An error occurred while processing the `{}` command.".format(ctx.command.name))
        print('Ignoring exception in command {0.command} in {0.message.channel}'.format(ctx))
        tb = traceback.format_exception(type(error), error, error.__traceback__)
        error_trace = "".join(tb)
        print(error_trace)


@bot.event
async def on_ready():
    global Player
    global Role
    global RoleCategory

    # this bot should only ever be in one guild anyway
    for guild in bot.guilds:
        bot.guild = guild
        
        bot.mafia_channel = discord.utils.get(guild.channels, name="mafia")
        bot.day_channel = discord.utils.get(guild.channels, name="day")
        bot.nintendo_channel = discord.utils.get(guild.channels, name="nintendo")
        bot.pre_game_channel = discord.utils.get(guild.channels, name="pre-game")
        
        bot.players_role = discord.utils.get(guild.roles, name="Player")
        bot.dead_role = discord.utils.get(guild.roles, name="Dead/Spectator")
        bot.nintendo_role = discord.utils.get(guild.roles, name="Nintendo")
        bot.homebrew_role = discord.utils.get(guild.roles, name="Homebrew")
        
        print("Initialized on {}.".format(guild.name))

        break  
    
    
    
    # GAME LOGIC BEGINS HERE


    class Player:

        def __init__(self, member, role):
            self.member = member
            self.role = role
        
    class Role:

        def __init__(self, name, night_role, night_ability, wins_with, must_kill, category):
            self.name = name
            self.night_role = night_role
            self.night_ability = night_ability
            self.wins_with = wins_with
            self.category = category
            category.roles.append(self)
        
    class RoleCategory:

        def __init__(self, name):
            self.name = name
            self.roles = []
        
    bot.players_queued = []
    bot.starting = False
    bot.started = False

    bot.welcome_message = """
The sun rises in the wonderful server of Nintendo Homebrew.

Will the Nintendo staff members and informants successfully ban all of the hackers on the server?
Will the Shackers strike back and successfully drive Nintendo out? 

That remains to be seen...
"""

    homebrew_category = RoleCategory("Team Homebrew")
    nintendo_category = RoleCategory("Team Nintendo")

    bot.roles = [
        Role("Shacker", bot.homebrew_role, [homebrew_category], None, [nintendo_category], homebrew_category),
        Role("Nintendo Employee", bot.nintendo_role, [nintendo_category], None, [homebrew_category], nintendo_category)
    ]
        
@bot.command(pass_context=True)
async def queue(ctx):
    """Queue for a game of Shack Mafia. The game needs at least 6 players to start."""
    if bot.started:
        return await ctx.send("{} A Mafia game is currently active. Wait for it to be over before using this command.".format(ctx.author.mention))
    if ctx.author not in bot.players_queued:
        bot.players_queued.append(ctx.author)
        await ctx.send("{} You have been added to the queue for a Mafia game. {}/6 players are queued.".format(ctx.author.mention, len(bot.players_queued)))
        if len(bot.players_queued) >= 6 and not bot.starting:
            await prepare_for_game()
    else:
        await ctx.send("{} You are already queued for a Mafia game.".format(ctx.author.mention))
        
@bot.command(pass_context=True)
async def dequeue(ctx):
    """Dequeue from a game of Shack Mafia."""
    if bot.started:
        return await ctx.send("{} A Mafia game is currently active. Wait for it to be over before using this command.".format(ctx.author.mention))
    if ctx.author in bot.players_queued:
        bot.players_queued.remove(ctx.author)
        await ctx.send("{} You have been removed from the queue for a Mafia game. {}/6 players are queued.".format(ctx.author.mention, len(bot.players_queued)))
    else:
        await ctx.send("{} You are not queued for a Mafia game.".format(ctx.author.mention))
        

@bot.command(pass_context=True)
async def queued(ctx):
    """Show a list of currently queued members."""
    if bot.started:
        return await ctx.send("{} A Mafia game is currently active. Wait for it to be over before using this command.".format(ctx.author.mention))
    await ctx.send("{} Currently queued members: {}".format(ctx.author.mention, ", ".join([str(x) for x in bot.players_queued])))
    
@bot.command(pass_context=True)
@commands.has_permissions(manage_guild=True)
async def stop(ctx):
    """Stop any currently running or starting game and dequeue all queued members."""
    bot.started = False
    bot.starting = False
    bot.players = []
    bot.players_queued = []
    
@bot.command(pass_context=True)
@commands.has_permissions(manage_guild=True)
async def setqueue(ctx, number: int):
    """Set the number of queued members to a specified amount."""
    if len(bot.players_queued) > number:
        for _ in range(len(bot.players_queued) - number):
            bot.players_queued.pop()
    elif len(bot.players_queued) < number:
        for _ in range(number - len(bot.players_queued)):
            bot.players_queued.append(ctx.author)
    await ctx.send("{} Successfully set the number of currently queued players to {}.".format(ctx.author.mention, number))
        
async def prepare_for_game():
    bot.starting = True
    await bot.pre_game_channel.send("The 6th player has queued for a game. The game will start after, uh, five seconds with no new joins.")
    timer = 5
    current_queued = len(bot.players_queued)
    while timer:
        await asyncio.sleep(1)
        timer -= 1
        if not bot.starting:
            return
        if len(bot.players_queued) != current_queued:
            if len(bot.players_queued) < 6:
                await bot.pre_game_channel.send("There are no longer enough players to start a game of Mafia.")
                bot.starting = False
                return
            elif len(bot.players_queued) > current_queued:
                timer = 5
            current_queued = len(bot.players_queued)
    await begin_game()
    
async def begin_game():
    bot.starting = False
    bot.started = True
    bot.players = []
    bot.turn = 0
    bot.day = True
    
    await clear(0)
    await clear(1)
    
    await bot.pre_game_channel.send("A game of Mafia is about to begin!")
    await asyncio.sleep(5)
    
    for member in bot.guild.members:
        if member in bot.players_queued:
            await member.add_roles(bot.players_role)
            bot.players.append(Player(member, random.choice(bot.roles)))
        else:
            await member.add_roles(bot.dead_role)

    bot.players_queued = []
    
    await announce(bot.welcome_message, 0)
    await day()
    
async def announce(message, channel=0):
    target = await get_channel(channel)
    await target.send(message)
    
async def clear(channel):
    target = await get_channel(channel)
    await target.purge(limit=10000)
    
async def get_channel(channel):
    channels = [bot.day_channel, bot.nintendo_channel]
    return channels[channel]
    
    
async def day():
    if not bot.started:
        for player in bot.players:
            await player.member.remove_roles(player.role.night_role)

        return await announce(":anger: The game has been halted. Aborting...")

    bot.turn += 1
    bot.day = True
    
    for player in bot.players:
        await player.member.remove_roles(player.role.night_role)
        await player.member.add_roles(bot.players_role)

    await announce(":sunny: It is Day {}. Discussion will be open as long as there is an active conversation.".format(bot.turn))
    
    e = True
    f = time.time()
    while e:
        async for message in bot.day_channel.history(limit=1):
            if (datetime.utcnow() - message.created_at).total_seconds() > 15 or time.time() - f > 120:
                e = False
    
    await announce("Time to vote! Vote to ban players with the `!ban` command. Voting period will last for 25 seconds.")
    
    await asyncio.sleep(25)
    await clear(0)
    await night()
    
async def night():
    bot.day = False
    
    for player in bot.players:
        await player.member.remove_roles(bot.players_role)
        await player.member.add_roles(player.role.night_role)
    
    await announce(":full_moon: It is Night {}. You may perform abilities using the `!ability` command by either DMing the bot or using any role channels you might have. Night will last for 30 seconds.".format(bot.turn))
    
    await asyncio.sleep(30)
    await clear(0)
    await clear(1)
    await day()

@bot.command(pass_context=True)
async def ban(ctx):
     # ban logic
     await announce(ctx.message.author + ' has voted to ban.')

@bot.command(pass_context=True)
async def ability():
     # ability logic
     # DM person back
     pass
     

# GAME LOGIC ENDS HERE

with open("token") as f:
    token = f.read()
    
# Execute
print('Bot directory: ', dir_path)
bot.run(token)
