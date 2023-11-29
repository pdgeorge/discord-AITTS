import keyboard
import asyncio
from bot_openai import OpenAI_Bot
import os
import discord
from discord.ext import commands
import speech_recognition as sr
import time

# VRChat emotion -> Hotkey to use
# *happy* -> shift+f1 (default)
# *exasperated* -> shift+f2
# *blush* -> shift+f3
# *derp* -> shift+f4
# *wink* -> shift + f5
# *embarrassed* -> shift + f6
# *scared* -> shift + f7
# *alert* -> shift + f8

# {"*happy*": "f1", "*exasperated*": "f2", "*blush*": "f3", "*derp*": "f4", "*wink*": "f5", "*embarrassed*": "f6", "*scared*": "f7", "*alert*": "f8"}

# TODO: Strip *action* out of text during action_stripper
# TODO: Add Wink Detection (If wink, add wink_flag to bot. Have a wink_flag checker that will *wink* if wink_flag == True)
# TODO: Add protections to only allow certain people to use commands
# TODO: Place SYSTEM_MESSAGE into external file
# TODO: 

SYSTEM_MESSAGE = "You are a streamer on Twitch known as Detsy. You are funny and friendly. You primarily play VRChat. You are most known for being a 'Mint' (a small, short, cute, femboy avatar that must never be lewded). People accuse you of being the 'ERP king' but you refute those allegations, maintaining that you are wholesome. You will even say 'Do not lewd the Mint'. You do not stream for money or glory, you only stream for friendship. You will begin sentences with the following depending on the emotion you want to portray: *happy* if you want to be happy, *exasperated* if you are exasperated, *blush* for when you want to blush, *derp* for when you are confused, *embarrassed* if you are embarrassed, *scared* if you are scared, *alert* if something grabs your attention. Finally, you can *wink* whenever you want if you want to. Most importantly, please only respond with one sentence at a time!"
WAKE_UP_MESSAGE = "Hello Detsy, are you ready to start streaming?"

DISCORD_TOKEN = os.environ.get('CYRA_DISCORD')

# To find a device name and id, use bot_openai.scan_audio_devices
OUTPUT_DEVICE_NAME = "CABLE Input (VB-Audio Virtual Cable)"
OUTPUT_DEVICE_ID = 13

detsy_bot = OpenAI_Bot("Detsy", SYSTEM_MESSAGE)

# Discord bot instance with '!' prefix to commands
intents = discord.Intents.all()
discord_bot = commands.Bot(command_prefix='!', intents=intents)

async def mood(fun_key):
    await asyncio.sleep(0.1)
    print(fun_key)
    keyboard.press("left shift")
    keyboard.press(fun_key)
    await asyncio.sleep(0.1)
    keyboard.release("left shift")
    keyboard.release(fun_key)
    await asyncio.sleep(0.1)

async def listen_to_press():
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        print("Say 'forward' to move forward or 'exit' to quit.")

        while True:
            try:
                audio_data = recognizer.listen(source, timeout=5)
                command = recognizer.recognize_google(audio_data).lower()

                if "forward" in command:
                    print("Moving forward!")
                    keyboard.press("w")
                    time.sleep(1)
                    keyboard.release("w")

                elif "exit" in command:
                    print("Exiting program.")
                    break

            except sr.UnknownValueError:
                print("Could not understand audio.")
            except sr.RequestError as e:
                print(f"Error making the request; {e}")

async def action_stipper(msg):
    functions_to_call = []
    print("message received: " + msg)
    words_to_check = {"*happy*": "f1", "*exasperated*": "f2", "*blush*": "f3", "*derp*": "f4", "*wink*": "", "*embarrassed*": "f6", "*scared*": "f7", "*alert*": "f8"}
    for word, fun_key in words_to_check.items():
        if word == "*wink*":
            pass
        elif word in msg:
            functions_to_call.append(mood(fun_key))
    await asyncio.gather(*functions_to_call)

async def actions_tester():
    await asyncio.sleep(5)
    await action_stipper("This is a *happy* message.")
    await asyncio.sleep(1)
    await action_stipper("This is a *exasperated* message.")
    await asyncio.sleep(1)
    await action_stipper("This is a *blush* message.")
    await asyncio.sleep(1)
    await action_stipper("This is a *derp* message.")
    await asyncio.sleep(1)
    await action_stipper("This is a *wink* message.")
    await asyncio.sleep(1)
    await action_stipper("This is a *embarrassed* message.")
    await asyncio.sleep(1)
    await action_stipper("This is a *scared* message.")
    await asyncio.sleep(1)
    await action_stipper("This is a *alert* message.")
    await asyncio.sleep(1)
    await action_stipper("This is a *happy* message.")

async def main_runner():
    await asyncio.sleep(1)
    to_send = WAKE_UP_MESSAGE
    response = await detsy_bot.send_msg(to_send) # Generates the text from bot
    await action_stipper(response)
    path = await detsy_bot.playHT_wav_generator(response)
    await detsy_bot.read_message_choose_device(path, OUTPUT_DEVICE_ID)
    # Add "Wink detection" here
    await asyncio.sleep(0.1)

    while True:
        to_send = await detsy_bot.discord_colab(5)
        response = await detsy_bot.send_msg(to_send)
        await action_stipper(response)
        path = await detsy_bot.playHT_wav_generator(response)
        await detsy_bot.read_message_choose_device(path, OUTPUT_DEVICE_ID)
        # Add "Wink detection" here
        await asyncio.sleep(0.1)

# Command to make the bot join a voice channel
@discord_bot.command(name='join')
async def join(ctx):
    channel = ctx.author.voice.channel
    await channel.connect()
    await main_runner()

# Event to print a message when the bot is ready
@discord_bot.event
async def on_ready():
    print(f'{discord_bot.user} has connected to Discord!')

# Command to make the bot disconnect from a voice channel
# Does not actually work sadly
@discord_bot.command(name='disconnect')
async def disconnect(ctx):
    await ctx.send("Attempting to disconnect?")
    voice_channel = ctx.author.voice.channel
    await ctx.send(f"Disconnected from {voice_channel.name}")
    
    if voice_channel:
        await voice_channel.disconnect()
        await ctx.send("Disconnected from the voice channel.")
    else:
        await ctx.send("I am not currently in a voice channel.")

async def main():
    print("async main")
    # Run the bot with the token
    await discord_bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

    # response_path = await detsy_bot.save_message_two(response, 225) # Creates robo TTS
    # await detsy_bot.read_message_three(response_path, OUTPUT_DEVICE) # Sends TTS to RVC