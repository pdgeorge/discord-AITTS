# Beginnings of a base wrapper for main runner
import discord
import os
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.environ.get('CYRA_DISCORD')

intents = discord.Intents.all()
discord_bot = commands.Bot(command_prefix='!', intents=intents)
discord_bot.connections = {}

@discord_bot.event
async def on_ready():
    print(f"Logged in as {discord_bot.user.name}")

@discord_bot.command(name='ping')
async def ping(ctx):
    print(f"pong")
    print(f"Bot command prefix: {ctx.prefix}")
    await ctx.channel.send("pong")

discord_bot.load_extension("VrchatTestingCog")
discord_bot.load_extension("VrchatAI")

discord_bot.run(DISCORD_TOKEN)