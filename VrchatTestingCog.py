from discord.ext import commands
import vrchat_ai
import time

# For testing the main runner.

def actions_tester():
    time.sleep(5)
    response, actions = vrchat_ai.action_stripper("*happy* I am happy to see you")
    print(response)
    vrchat_ai.action_looper(actions)
    time.sleep(1)
    response, actions = vrchat_ai.action_stripper("*exasperated* I am exasperated!")
    print(response)
    vrchat_ai.action_looper(actions)
    time.sleep(1)
    response, actions = vrchat_ai.action_stripper("*blush* UwU do not lewd the mint.")
    print(response)
    vrchat_ai.action_looper(actions)
    time.sleep(1)
    response, actions = vrchat_ai.action_stripper("*derp* What did you say?")
    print(response)
    vrchat_ai.action_looper(actions)
    time.sleep(1)
    response, actions = vrchat_ai.action_stripper("*wink* I think you are cute.")
    print(response)
    vrchat_ai.action_looper(actions)
    time.sleep(1)
    response, actions = vrchat_ai.action_stripper("*embarrassed* I am a little shy.")
    print(response)
    vrchat_ai.action_looper(actions)
    time.sleep(1)
    response, actions = vrchat_ai.action_stripper("*scared* Ahhhhh")
    print(response)
    vrchat_ai.action_looper(actions)
    time.sleep(1)
    response, actions = vrchat_ai.action_stripper("*alert* I am watching you.")
    print(response)
    vrchat_ai.action_looper(actions)
    time.sleep(1)
    response, actions = vrchat_ai.action_stripper("*happy* I am happy to see you")
    print(response)
    vrchat_ai.action_looper(actions)

class VrchatTestingCog(commands.Cog):
    def __init__(self, bot):
                 self.bot = bot

    # Command to make the bot join a voice channel
    @commands.command()
    async def emoteTest(self, ctx):
        actions_tester()    