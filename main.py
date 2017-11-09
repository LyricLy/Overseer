description = """A bot to oversee games of Shack Mafia. """

# import dependencies
import discord
from discord.ext import commands
import os


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
        await bot.send_message(ctx.message.channel, "You don't have permission to use this command.")
    elif isinstance(error, discord.ext.commands.errors.MissingRequiredArgument):
        formatter = commands.formatter.HelpFormatter()
        await bot.send_message(ctx.message.channel, "You are missing required arguments.\n{}".format(formatter.format_help_for(ctx, ctx.command)[0]))
    else:
        if ctx.command:
            await bot.send_message(ctx.message.channel, "An error occurred while processing the `{}` command.".format(ctx.command.name))
        print('Ignoring exception in command {0.command} in {0.message.channel}'.format(ctx))
        tb = traceback.format_exception(type(error), error, error.__traceback__)
        error_trace = "".join(tb)
        print(error_trace)
        embed = discord.Embed(description=error_trace.translate(bot.escape_trans))
        await bot.send_message(bot.err_logs_channel, "An error occurred while processing the `{}` command in channel `{}`.".format(ctx.command.name, ctx.message.channel), embed=embed)
        
@bot.event
async def on_error(event_method, *args, **kwargs):
    if isinstance(args[0], commands.errors.CommandNotFound):
        return
    print("Ignoring exception in {}".format(event_method))
    tb = traceback.format_exc()
    error_trace = "".join(tb)
    print(error_trace)
    embed = discord.Embed(description=error_trace.translate(bot.escape_trans))
    await bot.send_message(bot.err_logs_channel, "An error occurred while processing `{}`.".format(event_method), embed=embed)

@bot.event
async def on_ready():
    # this bot should only ever be in one server anyway
    for server in bot.servers:
        bot.server = server
        if bot.all_ready:
            break
        bot.idiots_channel = discord.utils.get(server.channels, name="idiots")
        bot.private_messages_channel = discord.utils.get(server.channels, name="private-messages")
        bot.rules_channel = discord.utils.get(server.channels, name="rules")
        bot.logs_channel = discord.utils.get(server.channels, name="server-logs")
        bot.cmd_logs_channel = discord.utils.get(server.channels, name="cmd-logs")
        bot.containment_channel = discord.utils.get(server.channels, name="containment")
        bot.err_logs_channel = discord.utils.get(server.channels, name="err-logs")
        bot.msg_logs_channel = discord.utils.get(server.channels, name="msg-logs")
        bot.hidden_channel = discord.utils.get(server.channels, name="hiddenplace")
        
        bot.dead_role = discord.utils.get(server.roles, name="Dead")
        bot.nintendo_role = discord.utils.get(server.roles, name="Nintendo")
        bot.nintendo_role
        
        print("Initialized on {}.".format(server.name))
        
        bot.all_ready = True
        bot._is_all_ready.set()

        break
    

with open("token") as f:
    token = f.read()
    
# Execute
print('Bot directory: ', dir_path)
bot.run(token)
