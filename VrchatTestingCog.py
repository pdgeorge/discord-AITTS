from discord.ext import commands
import asyncio
import vrchat_ai

# For testing the main runner.

# TODO: Create self.TAI

async def actions_tester():
    await asyncio.sleep(5)
    response, actions = vrchat_ai.action_stripper("*happy* I am happy to see you")
    print(response)
    await asyncio.sleep(1)
    response, actions = vrchat_ai.action_stripper("*exasperated* I am exasperated!")
    print(response)
    await asyncio.sleep(1)
    response, actions = vrchat_ai.action_stripper("*blush* UwU do not lewd the mint.")
    print(response)
    await asyncio.sleep(1)
    response, actions = vrchat_ai.action_stripper("*derp* What did you say?")
    print(response)
    await asyncio.sleep(1)
    # Wink test does not work when coggified
    # response, actions = vrchat_ai.action_stripper("*wink* I think you are cute.")
    # print(response)
    await asyncio.sleep(1)
    response, actions = vrchat_ai.action_stripper("*embarrassed* I am a little shy.")
    print(response)
    await asyncio.sleep(1)
    response, actions = vrchat_ai.action_stripper("*scared* Ahhhhh")
    print(response)
    await asyncio.sleep(1)
    response, actions = vrchat_ai.action_stripper("*alert* I am watching you.")
    print(response)
    await asyncio.sleep(1)
    response, actions = vrchat_ai.action_stripper("*happy* I am happy to see you")
    print(response)

class VrchatTestingCog(commands.Cog):
    def __init__(self, discord_bot):
                print("VRCTC Loaded")
                self.discord_bot = discord_bot

    # Command to make the bot join a voice channel
    @commands.command(name="emotetest")
    async def emotetest(self, ctx):
        await actions_tester()

def setup(discord_bot):
        discord_bot.add_cog(VrchatTestingCog(discord_bot))