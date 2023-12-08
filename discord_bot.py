# Discord Bot is purely for testing on the side. The TRUE Discord bot is vrchat_ai

import os
import discord
from discord.ext import commands, voice_recv
from discord.commands import ApplicationContext, option
import speech_recognition as sr
import time
import asyncio

from pydub import AudioSegment

# Get your bot token from the environment variable
DISCORD_TOKEN = os.environ.get('CYRA_DISCORD')

# Create an instance of the bot with a command prefix
intents = discord.Intents.all()
discord_bot = commands.Bot(command_prefix='!', intents=intents)
# discord_bot = discord.Bot(debug_guilds=[...])
discord_bot.connections = {}

@discord_bot.command()
async def start(
    ctx: ApplicationContext
):
    time_to_record = 5
    channel = ctx.channel
    voice = ctx.author.voice

    if not voice:
        return await channel.send("You're not in a vc right now")

    vc = await voice.channel.connect()
    discord_bot.connections.update({ctx.guild.id: vc})

    sink = discord.sinks.MP3Sink()
    vc.start_recording(
        sink,
        finished_callback,
        ctx.channel,
    )

    await channel.send("The recording has started!")

    await asyncio.sleep(time_to_record)

    vc.stop_recording()
    del discord_bot.connections[ctx.guild.id]
    # exit()

async def finished_callback(sink, channel: discord.TextChannel, *args):
    recorded_users = [f"<@{user_id}>" for user_id, audio in sink.audio_data.items()]
    await sink.vc.disconnect()
    # For saving to Discord Channel
    # files = [discord.File(audio.file, f"{user_id}.{sink.encoding}") for user_id, audio in sink.audio_data.items()]
    # For saving locally
    for user_id, audio in sink.audio_data.items():
        file_path = f"{user_id}.{sink.encoding}"
        with open(file_path, 'wb') as file:
            file.write(audio.file.read())
            print("A little bit of a wait")
            await asyncio.sleep(0.5)
        file_path = await mp3_to_wav(file_path)
        await transcribe_audio(file_path, channel, user_id)

    # await channel.send(f"Finished! Recorded audio for {', '.join(recorded_users)}.", files=files)
    await channel.send(f"Finished! Recorded audio for {', '.join(recorded_users)}.")

async def transcribe_audio(file_path, channel: discord.TextChannel, user_id):
    print(file_path)
    r = sr.Recognizer()
    samplerate = 48000
    sink_channels = 1

    with sr.AudioFile(file_path) as source:
        audio = r.record(source)
    try:
        print("bang 1")
        transcribed_text = r.recognize_google(audio)
        await channel.send(f"Transcription for <@{user_id}>: {transcribed_text}")
        print("bang 2")
    except sr.UnknownValueError:
        print("band f")
        await channel.send(f"Unable to transcribe audio for <@{user_id}>. Speech Recognition could not understand the audio.")
    except sr.RequestError as e:
        print("band f")
        await channel.send(f"Unable to transcribe audio for <@{user_id}>. Error with the Speech Recognition service: {e}")

async def mp3_to_wav(path):
    sound = AudioSegment.from_mp3(path)
    new_path = path+".wav"
    sound.export(new_path, format="wav")
    return new_path

@discord_bot.command()
async def transcribetest(ctx):
    channel = ctx.channel
    await channel.send("transcribetest called")
    transcribed_data = await transcribe_audio('Test.opus', channel, 123)

@discord_bot.command(name="testlisten")
async def testListen(ctx):
    def cb(user, text: str):
        asyncio.run_coroutine_threadsafe(ctx.send(f"{user} said: {text}"), loop=ctx.bot.loop)
    voice_channel = ctx.author.voice.channel
    vc = await voice_channel.connect(cls=voice_recv.VoiceRecvClient)
    vc.listen(voice_recv.extras.SpeechRecognitionSink(text_cb=cb))

# Event to print a message when the bot is ready
@discord_bot.event
async def on_ready():
    print(f'{discord_bot.user} has connected to Discord!')

# Simple "ping" command
@discord_bot.command(name='ping')
async def ping(ctx):
    await ctx.send('Pong!')

# Command to make the bot join a voice channel
@discord_bot.command(name='join')
async def join(ctx):
    voice_channel = ctx.author.voice.channel
    voice = await voice_channel.connect()
    await ctx.send(f'Joined {voice_channel.name}')
    source = discord.FFmpegPCMAudio("./outputs\\tester\\_Msg589158584504913860.opus")
    player = voice.play(source)

# Run the bot with the token
discord_bot.run(DISCORD_TOKEN)