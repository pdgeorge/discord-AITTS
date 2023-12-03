import keyboard
import asyncio
from bot_openai import OpenAI_Bot
import os
import discord
from discord import FFmpegPCMAudio
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
# ^^ !DONE! ^^
# TODO: Add Wink Detection (If wink, add wink_flag to bot. Have a wink_flag checker that will *wink* if wink_flag == True)
# TODO: Add protections to only allow certain people to use commands
# TODO: Place SYSTEM_MESSAGE into external file
# TODO: 

SYSTEM_MESSAGE = "You are a streamer on Twitch known as Detsy. You are funny and friendly. You primarily play V-R-Chat. You are most known for being a 'Mint' (a small, short, cute, femboy avatar that must never be lewded). People accuse you of being the 'ERP king' but you refute those allegations, maintaining that you are wholesome. You will even say 'Do not lewd the Mint'. You do not stream for money or glory, you only stream for friendship. You will begin sentences with the following depending on the emotion you want to portray: *happy* if you want to be happy, *exasperated* if you are exasperated, *blush* for when you want to blush, *derp* for when you are confused, *embarrassed* if you are embarrassed, *scared* if you are scared, *alert* if something grabs your attention. Finally, you can *wink* whenever you want if you want to, but try not to over do it. Most importantly, please only respond with one sentence at a time!"
WAKE_UP_MESSAGE = "Hello Detsy, are you ready to start streaming?"

DISCORD_TOKEN = os.environ.get('CYRA_DISCORD')

# To find a device name and id, use bot_openai.scan_audio_devices
OUTPUT_DEVICE_NAME = "CABLE Input (VB-Audio Virtual Cable)"
OUTPUT_DEVICE_ID = 13
FFMPEG_PATH = "C:\\ffmpeg\\ffmpeg.exe"

detsy_bot = OpenAI_Bot("Detsy", SYSTEM_MESSAGE)

# Discord bot instance with '!' prefix to commands
intents = discord.Intents.all()
discord_bot = commands.Bot(command_prefix='!', intents=intents)

def wink():
    keyboard.press("left shift")
    keyboard.press("f5")
    time.sleep(0.1)
    keyboard.release("left shift")
    keyboard.release("f5")
    time.sleep(1)
    keyboard.press("left shift")
    keyboard.press(detsy_bot.last_emote)
    time.sleep(0.1)
    keyboard.release("left shift")
    keyboard.release(detsy_bot.last_emote)
    time.sleep(0.1)
    

def mood(fun_key):
    print(fun_key)
    time.sleep(0.1)
    detsy_bot.last_emote = fun_key
    keyboard.press("left shift")
    keyboard.press(fun_key)
    time.sleep(0.1)
    keyboard.release("left shift")
    keyboard.release(fun_key)
    time.sleep(0.1)

def action_looper(action_list):
    print("Inside action_looper")
    for action in action_list:
        action()

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

def action_stripper(msg):
    functions_to_call = []
    print("message received: " + msg)
    words_to_check = {"*happy*": "f1", "*exasperated*": "f2", "*blush*": "f3", "*derp*": "f4", "*wink*": "", "*embarrassed*": "f6", "*scared*": "f7", "*alert*": "f8"}
    msg_lower = msg.lower()
    for word, fun_key in words_to_check.items():
        if word == "*wink*":
            detsy_bot.wink_flag = True
            pass
        elif word.lower() in msg_lower:
            msg_lower = msg_lower.replace(word.lower(), "")
            mood_lambda = lambda key=fun_key: mood(fun_key=key)
            functions_to_call.append(mood_lambda)
        msg_lower = msg_lower.replace(word.lower(), "")
    return msg_lower, functions_to_call

def actions_tester():
    time.sleep(5)
    response, actions = action_stripper("*happy* I am happy to see you")
    print(response)
    action_looper(actions)
    time.sleep(1)
    response, actions = action_stripper("*exasperated* I am exasperated!")
    print(response)
    action_looper(actions)
    time.sleep(1)
    response, actions = action_stripper("*blush* UwU do not lewd the mint.")
    print(response)
    action_looper(actions)
    time.sleep(1)
    response, actions = action_stripper("*derp* What did you say?")
    print(response)
    action_looper(actions)
    time.sleep(1)
    response, actions = action_stripper("*wink* I think you are cute.")
    print(response)
    action_looper(actions)
    time.sleep(1)
    response, actions = action_stripper("*embarrassed* I am a little shy.")
    print(response)
    action_looper(actions)
    time.sleep(1)
    response, actions = action_stripper("*scared* Ahhhhh")
    print(response)
    action_looper(actions)
    time.sleep(1)
    response, actions = action_stripper("*alert* I am watching you.")
    print(response)
    action_looper(actions)
    time.sleep(1)
    response, actions = action_stripper("*happy* I am happy to see you")
    print(response)
    action_looper(actions)

# Command to make the bot join a voice channel
@discord_bot.command(name='join')
async def join(ctx):
    voice_channel = ctx.author.voice.channel
    voice = await voice_channel.connect()
    await asyncio.sleep(1)
    time.sleep(0.1)
    to_send = WAKE_UP_MESSAGE
    
    # Generates the text from bot
    response = await detsy_bot.send_msg(to_send)

    # Strips any actions to do, then does the actions
    response, actions = action_stripper(response)
    print("response: " + response)

    # Generates audio file, then speaks the audio file through Discord channel
    # path, file_length = await detsy_bot.playHT_wav_generator(response)
    # Use this for testing to not waste money:
    path, file_length = "./outputs\\tester\\_Msg589158584504913860.opus", 9
    action_looper(actions) # Perform actions after audio generation, but before 'speaking'
    source = FFmpegPCMAudio(path)
    player = voice.play(source)
    await asyncio.sleep(file_length)
    if detsy_bot.wink_flag == True:
        wink()
        detsy_bot.wink_flag = False

    source.cleanup()
    while True:
        # Listen to Audio input, then send it to bot to generate text
        to_send = detsy_bot.discord_colab(5)
        ctx_to_send = "I heard: " + to_send
        await ctx.send(ctx_to_send)
        
        response = await detsy_bot.send_msg(to_send)

        # Strips any actions to do, then does the actions
        response, actions = action_stripper(response)
        print("response: " + response)

        # Generates audio file, then speaks the audio file through Discord channel
        # path, file_length = await detsy_bot.playHT_wav_generator(response)
        # Use this for testing to not waste money:
        path, file_length = "./outputs\\tester\\_Msg589158584504913860.opus", 9
        action_looper(actions) # Perform actions after audio generation, but before 'speaking'
        source = FFmpegPCMAudio(path)
        player = voice.play(source)
        await asyncio.sleep(file_length)
        if detsy_bot.wink_flag == True:
            wink()
            detsy_bot.wink_flag = False
        source.cleanup()

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
        await ctx.guild.voice_client.disconnect()
        await ctx.send("Disconnected from the voice channel.")
    else:
        await ctx.send("I am not currently in a voice channel.")

# Command to make the bot join a voice channel
@discord_bot.command(name='emoteTest')
async def emoteTest(ctx):
    actions_tester()


# Command to make the bot join a voice channel
@discord_bot.command(name='load')
async def load(ctx):
    detsy_bot.load_from_file(detsy_bot.bot_file)

async def main():
    print("async main")
    # Run the bot with the token
    await discord_bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())