# Beginnings of a base wrapper for main runner
import os
from discord.ext import commands
from VrchatTestingCog import VrchatTestingCog

DISCORD_TOKEN = os.environ.get('CYRA_DISCORD')

discord_bot = commands.Bot(commands_prefix="!")

async  def on_ready():
    print(f"Logged in as {discord_bot.user.name}")

discord_bot.add_cog(VrchatTestingCog(discord_bot))

discord_bot.run(DISCORD_TOKEN)