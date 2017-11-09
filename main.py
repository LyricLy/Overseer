description = """A bot to oversee games of Shack Mafia. """

# import dependencies
import discord
from discord.ext import commands
import os
import time


# sets working directory to bot's folder
dir_path = os.path.dirname(os.path.realpath(__file__))
os.chdir(dir_path)

prefix = ['!', '.']
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
async def on_command_error(error, ctx):
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
async def on_error(event_method, *args, **kwargs):
    if isinstance(args[0], commands.errors.CommandNotFound):
        return
    print("Ignoring exception in {}".format(event_method))
    tb = traceback.format_exc()
    error_trace = "".join(tb)
    print(error_trace)

@bot.event
async def on_ready():
    # this bot should only ever be in one server anyway
    for server in bot.servers:
        bot.server = server
        if bot.all_ready:
            break
        bot.mafia_channel = discord.utils.get(server.channels, name="mafia")
        bot.day_channel = discord.utils.get(server.channels, name="day")
        bot.pre_game_channel = discord.utils.get(server.channels, name="pre-game")
        
        bot.dead_role = discord.utils.get(server.roles, name="Dead")
        bot.nintendo_role = discord.utils.get(server.roles, name="Nintendo")
        
        print("Initialized on {}.".format(server.name))
        
        bot.all_ready = True
        bot._is_all_ready.set()

        break
    
bot.players_queued = []
bot.starting = False
bot.started = False
        
@bot.command(pass_context=True)
async def queue(ctx):
    """Queue for a game of Shack Mafia. The game needs at least 6 players to start."""
    bot.players_queued.append(ctx.author)
    await ctx.send("{} You have been added to the queue for a Mafia game. {}/6 players are queued.".format(ctx.author.mention, len(bot.players_queued)))
    if len(bot.players_queued) >= 6 and not bot.starting:
        await prepare_for_game()
        
@bot.command(pass_context=True)
async def dequeue(ctx):
    """Queue for a game of Shack Mafia. The game needs at least 6 players to start."""
    if ctx.author in bot.players_queued:
        bot.players_queued.remove(ctx.author)
        await ctx.send("{} You have been removed from the queue for a Mafia game. {}/6 players are queued.".format(ctx.author.mention, len(bot.players_queued)))
    else:
        await ctx.send("{} You are not queued for a Mafia game.".format(ctx.author.mention))
        
        
async def prepare_for_game():
    bot.starting = True
    await bot.pre_game_channel.send("The 6th player has queued for a game. The game will start after one minute with no new joins.")
    timer = 60
    current_queued = len(bot.players_queued)
    while timer:
        time.sleep(1)
        timer -= 1
        if len(bot.players_queued) != current_queued:
            if len(bot.players_queued) < 6:
                await bot.pre_game_channel.send("There are no longer enough players to start a game of Mafia.")
                bot.starting = False
                return
            elif len(bot.players_queued) > current_queued:
                timer = 60
            current_queued = len(bot.players_queued)
    await begin_game()
    
async def begin_game():
    pass
    
    
# GAME LOGIC BEGINS HERE

class Player:
    pass
    
class Role:
    pass
    
class RoleCategory:
    pass
    

# GAME LOGIC ENDS HERE

with open("token") as f:
    token = f.read()
    
# Execute
print('Bot directory: ', dir_path)
bot.run(token)
