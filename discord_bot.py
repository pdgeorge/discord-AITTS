# Beginnings of a base wrapper for main runner
import discord
import os
import asyncio
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

async def main():
    async with discord_bot:
        await discord_bot.load_extension("VrchatTestingCog")
        await discord_bot.load_extension("VrchatAI")
        await discord_bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
