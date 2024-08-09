import json
import keyboard
import asyncio
from bot_openai import OpenAI_Bot
import os
import discord
from discord import FFmpegPCMAudio
from discord.ext import commands
import time
from pydub import AudioSegment
import speech_recognition as sr
import random
import re
from dotenv import load_dotenv

load_dotenv()

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

# TODO: Improve listener functionality to be able to listen accurately to multiple users in one call

LISTEN_FOR = 30 # How long the bot should listen for

transcribed_text_from_cb = ""

CHEWBACCA_CHANCE = 100
TIKTOK_TOKEN = os.getenv("TIKTOK_TOKEN")
TIKTOK_VOICE = "en_us_stormtrooper"
TIKTOK_VOICES = ["en_us_ghostface", "en_us_chewbacca", "en_us_c3po", "en_us_stitch", "en_us_stormtrooper", "en_us_rocket", "en_au_001", "en_au_002", "en_uk_001", "en_uk_003", "en_us_001", "en_us_002", "en_us_006", "en_us_007", "en_us_009", "en_us_010", "fr_001", "fr_002", "de_001", "de_002", "es_002", "es_mx_002", "br_001", "br_003", "br_004", "br_005", "id_001", "jp_001", "jp_003", "jp_005", "jp_006", "kr_002", "kr_003", "kr_004"]

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

def filter(message):
    filtered_msg = message
    
    message = re.sub('(\<.?\:)|(\:\d+\>)', "", message)
    message = re.sub('https?\:\/\/(\w+\.)?\w+\.\w+\/.+', "A link!", message)
    filtered_msg = message
    
    return filtered_msg

class VrchatAI(commands.Cog):
    def __init__(self, discord_bot):
        bot_name = None
        system_message = None
        self.wake_up_message = None
        voice = None

        load_from = "vrchat_ai.json"
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
        self.aitts = False
        self.gtts = False
        self.tttts = False
        self.chewbacca_chance = CHEWBACCA_CHANCE
        self.tttts_voice = TIKTOK_VOICE

    @commands.Cog.listener()
    async def on_message(self, message):
        # Check if the message was sent by the bot itself to avoid reacting to its own messages
        if message.author == self.discord_bot.user:
            return
        
        ctx = await self.discord_bot.get_context(message)

        vc = discord.utils.get(self.discord_bot.voice_clients, guild=message.guild)
        if vc:
            print(f"currently in: {vc.channel.name}") ## THIS
        print(message.channel.name) ## MUST MATCH THIS

        if (vc.channel.name == message.channel.name) and not (message.content[0] == "!"):
            if self.aitts:
                await self.aispeak(ctx, to_speak = message.content)
            elif self.tttts:
                await self.speak(ctx, to_speak = message.content)
            elif self.gtts:
                await self.gttsspeak(ctx, to_speak = message.content)

        # # React to the message by adding a reaction
        # await message.add_reaction("👍")  # You can replace "👍" with any emoji you like
        # print(message.channel.name)

    # Command to make the bot join a voice channel
    @commands.command(name="join")
    @commands.has_role("Cyra-chatter")
    async def join(self, ctx):
        self.aitts = False
        self.gtts = True
        self.tttts = False
        vc = None
        if not ctx.author.voice:
            return await ctx.channel.send("You are not in a vc right now")
        if not ctx.voice_client:
            vc = await ctx.author.voice.channel.connect()
        else:
            vc = ctx.voice_client
        self.discord_bot.connections.update({ctx.guild.id: vc})

    # Command to make the bot leave a voice channel
    @commands.command(name="leave")
    @commands.has_role("Cyra-chatter")
    async def leave(self, ctx):
        self.aitts = False
        vc = None
        if not ctx.author.voice:
            return await ctx.channel.send("You are not in a vc right now")
        if not ctx.voice_client:
            return await ctx.channel.send("I am not in a vc right now")
        else:
            for x in self.discord_bot.voice_clients:
                print("====================")
                print(self.discord_bot.voice_clients)
                print("====================")
                print(f"x:{x.guild.id}")
                print(f"ctx.guild.id:{ctx.guild.id}")
                if int(x.guild.id) == int(ctx.guild.id):
                    await x.disconnect()
        self.discord_bot.connections.update({ctx.guild.id: vc})

    # Command to make the bot join a voice channel
    @commands.command(name="aijoin")
    @commands.has_role("Cyra-chatter")
    async def aijoin(self, ctx):
        self.aitts = True
        self.gtts = False
        self.tttts = False
        vc = None

        if not ctx.author.voice:
            return await ctx.channel.send("You're not in a vc right now")
        if not ctx.voice_client:
            vc = await ctx.author.voice.channel.connect()
        else:
            vc = ctx.voice_client
        self.discord_bot.connections.update({ctx.guild.id: vc})

    # Command to make the bot join a voice channel
    @commands.command(name="ttttsjoin")
    @commands.has_role("Cyra-chatter")
    async def ttttsjoin(self, ctx):
        self.aitts = False
        self.gtts = False
        self.tttts = True
        vc = None

        if not ctx.author.voice:
            return await ctx.channel.send("You're not in a vc right now")
        if not ctx.voice_client:
            vc = await ctx.author.voice.channel.connect()
        else:
            vc = ctx.voice_client
        self.discord_bot.connections.update({ctx.guild.id: vc})

    # Command to load the bots "last" chat history in the event of a crash.
    @commands.command(name="load")
    @commands.has_role("Cyra-chatter")
    async def load(self, ctx):
        self.vrchat_bot.load_from_file(self.vrchat_bot.bot_file)

    # Stops the AI looping and communicating.
    @commands.command()
    @commands.has_role("Cyra-chatter")
    async def stop(self, ctx):
        self.looping = False
        await ctx.channel.send("Stopping looping")

    # Ask the AI a single question and have it respond with AI-TTS
    @commands.command()
    @commands.has_role("Cyra-chatter")
    async def ask(self, ctx, *, to_ask):
        response = await self.vrchat_bot.send_msg(to_ask)
        await ctx.channel.send(f"Response was: {response}")
        if self.aitts:
            await self.aispeak(ctx, to_speak = response)
        elif self.aitts == False:
            await self.speak(ctx, to_speak = response)

    # Starts the AI talking and speaking loop
    @commands.command()
    @commands.has_role("Cyra-chatter")
    async def start(self, ctx):
        self.looping = True
        global transcribed_text_from_cb
        
        vc = None
        if not ctx.author.voice:
            return await ctx.channel.send("You're not in a vc right now")
        if not ctx.voice_client:
            vc = await ctx.author.voice.channel.connect()
        else:
            vc = ctx.voice_client
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

    # Loads the chosen persona in to file and memory
    @commands.command()
    @commands.has_role("Cyra-chatter")
    async def loadPersona(self, ctx, persona):
        load_from = "vrchat_ais.json"
        with open(load_from, 'r') as f:
            data = json.load(f)
        if data:
            persona_data = next(item for item in data if item["bot_name"] == persona)
            if persona_data:
                with open('vrchat_ai.json', 'w+') as json_file:
                    json.dump(persona_data, json_file, indent=2)
                    await ctx.channel.send(f"Successfully loaded {persona}")
                    self.vrchat_bot = None
                    print(persona_data)
                    print(type(persona_data))
                    bot_name = persona_data["bot_name"]
                    system_message = persona_data["system_message"]
                    voice = persona_data["voice"]
                    self.vrchat_bot = OpenAI_Bot(bot_name, system_message, voice)
                    await ctx.channel.send(f"Successfully reloaded {self.vrchat_bot.bot_name}")
            else:
                await ctx.channel.send(f"Unable to load {persona} please use !checkPersona to check Personas")

    # Prints out available personalities
    @commands.command()
    @commands.has_role("Cyra-chatter")
    async def checkPersona(self, ctx):
        load_from = "vrchat_ais.json"
        with open(load_from, 'r') as f:
            data = json.load(f)
        if data:
            for item in data:
                await ctx.channel.send(f'This persona is available: {item["bot_name"]}')

    # List TikTokTTSVoices that can be used
    @commands.command()
    @commands.has_role("Cyra-chatter")
    async def voices(self, ctx):
        await ctx.channel.send("0: en_us_ghostface\n1: en_us_chewbacca\n2: en_us_c3po\n3: en_us_stitch\n4: en_us_stormtrooper\n5: en_us_rocket\n\nEnglish Voices\n6: en_au_001\n7: en_au_002\n8: en_uk_001\n9: en_uk_003\n10: en_us_001\n11: en_us_002\n12: en_us_006\n13: en_us_007\n14: en_us_009\n15: en_us_010\n\nEuropean Voices\n16: fr_001\n17: fr_002\n18: de_001\n19: de_002\n20: es_002\n\nAmerican Voices\n21: es_mx_002\n22: br_001\n23: br_003\n24: br_004\n25: br_005\n\nAsia Voices\n26: id_001\n27: jp_001\n28: jp_003\n29: jp_005\n30: jp_006\n31: kr_002\n32: kr_003\n33: kr_004")

    # Change the chance to use the chewbacca voice
    @commands.command()
    @commands.has_role("Cyra-chatter")
    async def voice(self, ctx, new_voice=None):
        print(new_voice)
        if new_voice == None:
            await ctx.channel.send(f"The current voice is {self.tttts_voice}")
        elif new_voice.isdigit():
            if int(new_voice) > 33:
                await ctx.channel.send("The number you entered is larger than the potential voices. Please look at !voices again to see what options are available")
            else:
                self.tttts_voice = TIKTOK_VOICES[int(new_voice)]
                await ctx.channel.send(f"Your new voice is {self.tttts_voice}")
        elif new_voice in TIKTOK_VOICES:
            self.tttts_voice = new_voice
            await ctx.channel.send(f"The new voice is {self.tttts_voice}")
        else:
            await ctx.channel.send(f"{new_voice} is not in the list of voices. Please look at !voices again to see what options are available")

    # Change the chance to use the chewbacca voice
    @commands.command()
    @commands.has_role("Cyra-chatter")
    async def chance(self, ctx, chance):
        if chance.isdigit():
            self.chewbacca_chance = int(chance)
            await ctx.channel.send(f"The new chance is 1 in {self.chewbacca_chance}")
        else:
            await ctx.channel.send(f"{chance} is not a number. Please use a number.")

    # Send a message to Cyra to have her speak using TikTokTextToSpeach
    @commands.command(name="speak")
    @commands.has_role("Cyra-chatter")
    async def speak(self, ctx, *, to_speak):
        self.looping = True
        global transcribed_text_from_cb
        channel = ctx.channel
        voice = ctx.author.voice
        vc = None

        if not voice:
            return await channel.send("You're not in a vc right now")
        if not ctx.voice_client:
            vc = await voice.channel.connect()
        else:
            vc = ctx.voice_client
            
        print("ctx.voice_client:")
        print(ctx.voice_client)
        
        self.discord_bot.connections.update({ctx.guild.id: vc})
        
        to_speak = filter(to_speak)
        
        response = to_speak

        # Generates audio file, then speaks the audio file through Discord channel
        tttts_filename = f"{self.vrchat_bot.bot_name}_{int(time.time())}"
        tttts_path = await path_for_tttts(tttts_filename)

        tiktok_voice_to_use = self.tttts_voice
        if random.randint(1, self.chewbacca_chance) == 1:
            tiktok_voice_to_use = "en_us_chewbacca"

        print("response: " + response)

        path_to_voice, file_length = await self.vrchat_bot.tttts(TIKTOK_TOKEN, tiktok_voice_to_use, response, tttts_path)
        # Use this for testing to not waste money:
        # path, file_length = "./outputs\\tester\\_Msg589158584504913860.opus", 9
        print("path_to_voice: " + path_to_voice)
        print("file_length: " + str(file_length))
        source = FFmpegPCMAudio(path_to_voice)
        player = vc.play(source)
        await asyncio.sleep(file_length)
        if os.path.exists(path_to_voice):
            os.remove(path_to_voice)
            await asyncio.sleep(1)
            print(f"{path_to_voice} removed!")
        else:
            print(f"Something went wrong.")

    @commands.command(name="gttsspeak")
    @commands.has_role("Cyra-chatter")
    async def gttsspeak(self, ctx, *, to_speak):
        channel = ctx.channel
        voice = ctx.author.voice
        vc = None
        
        if not voice:
            return await channel.send("You're not in a vc right now")
        if not ctx.voice_client:
            vc = await voice.channel.connect()
        else:
            vc = ctx.voice_client
            
        print("ctx.voice_client:")
        print(ctx.voice_client)
        
        self.discord_bot.connections.update({ctx.guild.id: vc})

        to_speak = filter(to_speak)
        
        response = to_speak
        
        gtts_path, gtts_duration = self.vrchat_bot.create_voice(response)
        
        source = FFmpegPCMAudio(gtts_path)
        player = vc.play(source)
        await asyncio.sleep(gtts_duration)
        if os.path.exists(gtts_path):
            os.remove(gtts_path)
            print(f"{gtts_path} removed!")
        else: print(f"Something went wrong.")

    # Send a message to Cyra to have her speak using TikTokTextToSpeach
    @commands.command(name="aispeak")
    @commands.has_role("Cyra-chatter")
    async def aispeak(self, ctx, *, to_speak):
        global transcribed_text_from_cb
        channel = ctx.channel
        voice = ctx.author.voice
        vc = None

        if not voice:
            return await channel.send("You're not in a vc right now")
        if not ctx.voice_client:
            vc = await voice.channel.connect()
        else:
            vc = ctx.voice_client
        self.discord_bot.connections.update({ctx.guild.id: vc})
        
        to_speak = filter(to_speak)
        
        response = to_speak

        # Generates audio file, then speaks the audio file through Discord channel
        aitts_path, aitts_length = await self.vrchat_bot.playHT_wav_generator(response)

        source = FFmpegPCMAudio(aitts_path)
        player = vc.play(source)
        await asyncio.sleep(aitts_length)
        if os.path.exists(aitts_path):
            os.remove(aitts_path)
            print(f"{aitts_path} removed!")
        else:
            print(f"Something went wrong.")

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

        # This is only good for ONE USER AT A TIME. Would need to be updated to include multiple users at a time.
        transcribed_text_from_cb = await transcribe_audio(file_path, channel, user_id)
        print("ttfcb in f_c: "+transcribed_text_from_cb)

    # await channel.send(f"Finished! Recorded audio for {', '.join(recorded_users)}.", files=files)
    # await channel.send(f"Finished! Recorded audio for {', '.join(recorded_users)}.")

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
        transcribed_text = "Sorry I have nothing to say"
        return transcribed_text
    except sr.RequestError as e:
        await channel.send(f"Unable to transcribe audio for <@{user_id}>. Error with the Speech Recognition service: {e}")
        transcribed_text = "Sorry I have nothing to say"
        return transcribed_text

async def mp3_to_wav(path):
    sound = AudioSegment.from_mp3(path)
    new_path = path+".wav"
    sound.export(new_path, format="wav")
    return new_path

async def path_for_tttts(path_to_ttttsify):
    filename = path_to_ttttsify
    current_dir = os.getcwd()
    newpath = os.path.normpath(os.path.join(current_dir, "./outputs"))
    normalised_filename = os.path.normpath(os.path.join(newpath, filename))
    return normalised_filename

async def setup(discord_bot):
    await discord_bot.add_cog(VrchatAI(discord_bot))
    
if __name__ == "__main__":
    print("Ok it loaded")