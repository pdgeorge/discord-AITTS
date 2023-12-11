# Beginnings of a base wrapper for main runner
import os
from discord.ext import commands
from VrchatTestingCog import VrchatTestingCog

DISCORD_TOKEN = os.environ.get('CYRA_DISCORD')

discord_bot = commands.Bot(commands_prefix="!")

async  def on_ready():
    print(f"Logged in as {discord_bot.user.name}")

@discord_bot.command(name='ping')
async def ping(ctx):
    print(f"pong")
    print(f"Bot command prefix: {ctx.prefix}")

discord_bot.load_extension("VrchatTestingCog")
discord_bot.load_extension("VrchatAI")

discord_bot.run(DISCORD_TOKEN)