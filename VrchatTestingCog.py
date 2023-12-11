import discord
from discord.ext import commands
from discord import FFmpegPCMAudio
from discord.commands import ApplicationContext
import asyncio
import VrchatAI
from bot_openai import OpenAI_Bot
from pydub import AudioSegment
import speech_recognition as sr

# For testing the main runner.

# TODO: Create self.TAI

LISTEN_FOR = 10
BOT_NAME = "TAI"
WAKE_UP_MESSAGE = f"Hello {BOT_NAME}."
SYSTEM_MESSAGE = "You are a test AI that helps test programs. You will resond sometimes with the following actions at the start of your message: *happy*, *exasperated*, *blush*, *derp*, *embarrassed*, *scared*, *alert*, *wink*"

async def actions_tester(bot):
    await asyncio.sleep(5)
    response, actions = VrchatAI.action_stripper("*happy* I am happy to see you", bot)
    print(response)
    await asyncio.sleep(1)
    response, actions = VrchatAI.action_stripper("*exasperated* I am exasperated!", bot)
    print(response)
    await asyncio.sleep(1)
    response, actions = VrchatAI.action_stripper("*blush* UwU do not lewd the mint.", bot)
    print(response)
    await asyncio.sleep(1)
    response, actions = VrchatAI.action_stripper("*derp* What did you say?", bot)
    print(response)
    await asyncio.sleep(1)
    # Wink test does not work when coggified
    # response, actions = VrchatAI.action_stripper("*wink* I think you are cute.")
    # print(response)
    await asyncio.sleep(1)
    response, actions = VrchatAI.action_stripper("*embarrassed* I am a little shy.", bot)
    print(response)
    await asyncio.sleep(1)
    response, actions = VrchatAI.action_stripper("*scared* Ahhhhh", bot)
    print(response)
    await asyncio.sleep(1)
    response, actions = VrchatAI.action_stripper("*alert* I am watching you.", bot)
    print(response)
    await asyncio.sleep(1)
    response, actions = VrchatAI.action_stripper("*happy* I am happy to see you", bot)
    print(response)

class VrchatTestingCog(commands.Cog):
    def __init__(self, discord_bot):
                print("VRCTC Loaded")
                self.discord_bot = discord_bot
                self.tai_bot = OpenAI_Bot(BOT_NAME, SYSTEM_MESSAGE)

    # Command to make the bot join a voice channel
    @commands.command(name="emotetest")
    async def emotetest(self, ctx):
        await actions_tester(self.tai_bot)

    @commands.command(name="teststart")
    async def teststart(
        self, ctx: ApplicationContext
    ):
        global transcribed_text_from_cb
        channel = ctx.channel
        voice = ctx.author.voice

        if not voice:
            return await channel.send("You're not in a vc right now")
        vc = await voice.channel.connect()
        self.discord_bot.connections.update({ctx.guild.id: vc})

        to_send = WAKE_UP_MESSAGE
        
        # Generates the text from bot
        response = await self.tai_bot.send_msg(to_send)

        # Strips any actions to do from the reponse and sets them as separate lambdas
        response, actions = VrchatAI.action_stripper(msg=response, bot=self.tai_bot)
        print("response: " + response)

        # Generates audio file, then speaks the audio file through Discord channel
        path, file_length = self.tai_bot.create_voice(response)
        # Use this for testing to not waste money:
        # path, file_length = "./outputs\\tester\\_Msg589158584504913860.opus", 9
        source = FFmpegPCMAudio(path)
        player = vc.play(source)
        await asyncio.sleep(file_length)
        ################################### INTRO FINISHED BEGIN RECORDING
        while True:

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
            response = await self.tai_bot.send_msg(to_send)
            response, actions = VrchatAI.action_stripper(msg=response, bot=self.tai_bot)
            print("response: " + response)

            path_to_voice, file_length = self.tai_bot.create_voice(response)
            print(path_to_voice)
            VrchatAI.action_looper(actions)
            source = FFmpegPCMAudio(path_to_voice)
            player = vc.play(source)
            await asyncio.sleep(file_length)
            source.cleanup()

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
        discord_bot.add_cog(VrchatTestingCog(discord_bot))