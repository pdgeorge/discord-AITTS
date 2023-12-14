import json
import keyboard
import asyncio
from bot_openai import OpenAI_Bot
import os
import discord
from discord import FFmpegPCMAudio
from discord.commands import ApplicationContext
from discord.ext import commands
import time
from pydub import AudioSegment
import speech_recognition as sr

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
# ^^ !DONE! ^^
# TODO: Add protections to only allow certain people to use commands
# ^^ !DONE! ^^ "Orange-People" role
# TODO: Place system_message and wake_up_message into external file
# QUESTION: Does the play.ht manifest path need to be an init param?
# Answer: Yes !DONE!

LISTEN_FOR = 10 # How long the bot should listen for

transcribed_text_from_cb = ""

def wink(bot):
    keyboard.press("left shift")
    keyboard.press("f5")
    time.sleep(0.1)
    keyboard.release("left shift")
    keyboard.release("f5")
    time.sleep(1)
    keyboard.press("left shift")
    keyboard.press(bot.last_emote)
    time.sleep(0.1)
    keyboard.release("left shift")
    keyboard.release(bot.last_emote)
    time.sleep(0.1)
    
def mood(fun_key, bot):
    print(fun_key)
    time.sleep(0.1)
    bot.last_emote = fun_key
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

def action_stripper(msg, bot):
    functions_to_call = []
    print("message received: " + msg)
    words_to_check = {"*happy*": "f1", "*exasperated*": "f2", "*blush*": "f3", "*derp*": "f4", "*wink*": "", "*embarrassed*": "f6", "*scared*": "f7", "*alert*": "f8"}
    msg_lower = msg.lower()
    for word, fun_key in words_to_check.items():
        if word == "*wink*":
            bot.wink_flag = True
            pass
        elif word.lower() in msg_lower:
            msg_lower = msg_lower.replace(word.lower(), "")
            mood_lambda = lambda key=fun_key: mood(fun_key=key, bot=bot)
            functions_to_call.append(mood_lambda)
        msg_lower = msg_lower.replace(word.lower(), "")
    return msg_lower, functions_to_call

class VrchatAI(commands.Cog):
    def __init__(self, discord_bot):
        bot_name = None
        system_message = None
        self.wake_up_message = None
        voice = None

        load_from = "vrchat_ai.txt"
        with open(load_from, 'r') as f:
            data = json.load(f)
        if data:
            bot_name = data["bot_name"]
            system_message = data["system_message"]
            self.wake_up_message = data["wake_up_message"]
            voice = data["voice"]
        self.discord_bot = discord_bot
        self.vrchat_bot = OpenAI_Bot(bot_name, system_message, voice=voice)
        self.looping = False

    # Command to load the bots "last" chat history in the event of a crash.
    @commands.command(name='load')
    @commands.has_role('Orange-People')
    async def load(self, ctx):
        self.vrchat_bot.load_from_file(self.vrchat_bot.bot_file)

    @commands.command()
    @commands.has_role('Orange-People')
    async def stop(self, ctx: ApplicationContext):
        self.looping = False
        await ctx.channel.send("Stopping looping")

    @commands.command()
    @commands.has_role('Orange-People')
    async def start(
        self, ctx: ApplicationContext
    ):
        self.looping = True
        global transcribed_text_from_cb
        channel = ctx.channel
        voice = ctx.author.voice

        if not voice:
            return await channel.send("You're not in a vc right now")
        vc = await voice.channel.connect()
        self.discord_bot.connections.update({ctx.guild.id: vc})

        to_send = self.wake_up_message
        
        # Generates the text from bot
        response = await self.vrchat_bot.send_msg(to_send)

        # Strips any actions to do from the reponse and sets them as separate lambdas
        response, actions = action_stripper(msg=response, bot=self.vrchat_bot)
        print("response: " + response)

        # Generates audio file, then speaks the audio file through Discord channel
        path, file_length = await self.vrchat_bot.playHT_wav_generator(response)
        # Use this for testing to not waste money:
        # path, file_length = "./outputs\\tester\\_Msg589158584504913860.opus", 9
        action_looper(actions) # Perform actions after audio generation, but before 'speaking'
        source = FFmpegPCMAudio(path)
        player = vc.play(source)
        if self.vrchat_bot.wink_flag == True:
            wink(self.vrchat_bot)
            self.vrchat_bot.wink_flag = False
        await asyncio.sleep(file_length)
        ################################### INTRO FINISHED BEGIN RECORDING
        while self.looping == True:
            print("Begining rec")
            sink = discord.sinks.MP3Sink()
            vc.start_recording(
                sink,
                finished_callback,
                ctx.channel,
            )
            await asyncio.sleep(LISTEN_FOR)

            vc.stop_recording()
            await asyncio.sleep(1)

            to_send = transcribed_text_from_cb
            print("ttfcb: "+transcribed_text_from_cb)
            print("t_s: "+to_send)
            response = await self.vrchat_bot.send_msg(to_send)
            response, actions = action_stripper(msg=response, bot=self.vrchat_bot)

            # Generates audio file, then speaks the audio file through Discord channel
            path_to_voice, file_length = await self.vrchat_bot.playHT_wav_generator(response)
            # Use this for testing to not waste money:
            # path_to_voice, file_length = "./outputs\\tester\\_Msg589158584504913860.opus", 9
            print(path_to_voice)
            action_looper(actions)
            source = FFmpegPCMAudio(path_to_voice)
            player = vc.play(source)
            await asyncio.sleep(file_length)
            source.cleanup()
            if self.vrchat_bot.wink_flag == True:
                wink(self.vrchat_bot)
                self.vrchat_bot.wink_flag = False

async def finished_callback(sink, channel: discord.TextChannel, *args):
    global transcribed_text_from_cb
    recorded_users = [f"<@{user_id}>" for user_id, audio in sink.audio_data.items()]
    # await sink.vc.disconnect()
    # For saving to Discord Channel
    # files = [discord.File(audio.file, f"{user_id}.{sink.encoding}") for user_id, audio in sink.audio_data.items()]
    # For saving locally
    for user_id, audio in sink.audio_data.items():
        file_path = f"{user_id}.{sink.encoding}"
        with open(file_path, 'wb') as file:
            file.write(audio.file.read())
            await asyncio.sleep(0.5)
        file_path = await mp3_to_wav(file_path)
        transcribed_text_from_cb = await transcribe_audio(file_path, channel, user_id)
        print("ttfcb in f_c: "+transcribed_text_from_cb)

    # await channel.send(f"Finished! Recorded audio for {', '.join(recorded_users)}.", files=files)
    await channel.send(f"Finished! Recorded audio for {', '.join(recorded_users)}.")

async def transcribe_audio(file_path, channel: discord.TextChannel, user_id):
    print("t_a: "+file_path)
    r = sr.Recognizer()
    with sr.AudioFile(file_path) as source:
        audio = r.record(source)
    try:
        transcribed_text = r.recognize_google(audio)
        # await channel.send(f"Transcription for <@{user_id}>: {transcribed_text}")
        print(f"Transcription for <@{user_id}>: {transcribed_text}")
        return transcribed_text
    except sr.UnknownValueError:
        await channel.send(f"Unable to transcribe audio for <@{user_id}>. Speech Recognition could not understand the audio.")
    except sr.RequestError as e:
        await channel.send(f"Unable to transcribe audio for <@{user_id}>. Error with the Speech Recognition service: {e}")

async def mp3_to_wav(path):
    sound = AudioSegment.from_mp3(path)
    new_path = path+".wav"
    sound.export(new_path, format="wav")
    return new_path


def setup(discord_bot):
    discord_bot.add_cog(VrchatAI(discord_bot))