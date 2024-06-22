import asyncio
import os
from gtts import gTTS
import vlc
from openai import AsyncOpenAI
import json
import speech_recognition as sr
import datetime
from pyht import Client
from pyht.client import TTSOptions
import wave
from scipy.io import wavfile
import sounddevice as sd
from pydub import AudioSegment
import time
import math
import requests
import base64

TEXT_DIR = "./"
TTS_DIR = "./outputs/"
COLAB_PARTNER = "pdgeorge" # For when there is a colab partner, enter the name here.
DEFAULT_NAME = "TAI" # Which personality is being loaded
MESSAGE_CHANCE = 5 # Chance for user name to be included in the message, 1 in MESSAGE_CHANGE
SYSTEM_MESSAGE = "You are 'BasedMod', moderator of a Twitch community you really do not like. This community is a community of people who watch v-tubers. In fact you greatly enjoy roasting them. Every time that you receive a message, you give a brief, one sentence vitriolic rant about the individual and what they said before declaring that they are banned followed by an inventive way that they are banished from the internet."
WAKE_UP_MESSAGE = "It's time to wake up."
APIKEY = os.getenv("OPENAI_API_KEY")
USER_ID = os.getenv("PLAY_HT_USER_ID")
API_KEY = os.getenv("PLAY_HT_API_KEY")
TIKTOK_TOKEN = os.getenv("TIKTOK_TOKEN")

client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

ERROR_MSG = {
    "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello! How can I assist you today?"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 27,
    "completion_tokens": 9,
    "total_tokens": 36
  }}

def normalise_dir(dir):
    current_dir = os.getcwd()
    normalised_dir = os.path.normpath(os.path.join(current_dir, dir))
    return normalised_dir

async def speech_listener_async(listen_for):
    r = sr.Recognizer()
    transcription = "Not yet"
    with sr.Microphone() as source:
        print("Recording started")
        try:
            audio = r.listen(source, timeout=listen_for, phrase_time_limit=listen_for)  # Capture the audio input
        except sr.WaitTimeoutError:
            print(f"No speech detected before {listen_for} seconds.")
            return "" # No audio recorded, no string to transcribe, no string to return
    try:
        transcription = r.recognize_whisper(audio, language="english", model="base.en")  # Perform the speech-to-text transcription
    except sr.UnknownValueError:
        print("Speech recognition could not understand audio")
        transcription = "Error"
    except sr.RequestError as e:
        print("Could not request speech recognition results; {0}".format(e))
        transcription = "Error"
    return transcription

def speech_listener(listen_for):
    r = sr.Recognizer()
    transcription = "Not yet"
    with sr.Microphone() as source:
        print("Recording started")
        try:
            audio = r.listen(source, timeout=listen_for, phrase_time_limit=listen_for)  # Capture the audio input
        except sr.WaitTimeoutError:
            print(f"No speech detected before {listen_for} seconds.")
            return "" # No audio recorded, no string to transcribe, no string to return
    try:
        transcription = r.recognize_google(audio)  # Perform the speech-to-text transcription
    except sr.UnknownValueError:
        print("Speech recognition could not understand audio")
        transcription = "Error"
    except sr.RequestError as e:
        print("Could not request speech recognition results; {0}".format(e))
        transcription = "Error"
    return transcription

class OpenAI_Bot():
    def __init__(self, bot_name, system_message, voice=None):
        self.chat_history = []
        self.bot_name = bot_name
        self.voice = voice
        self.wink_flag = False
        self.last_emote = "f1"

        self.start_datetime = datetime.datetime.now()
        path = normalise_dir(TEXT_DIR)
        temp_bot_file = f"{self.bot_name}.txt"
        self.bot_file = os.path.join(path,temp_bot_file)

        self.last_pulled = "youtube" # Useful only if doing GamingAssistant project
        self.mode = "colab" # Useful only if doing GamingAssistant project

        temp_system_message = {}
        temp_system_message["role"] = "system"
        temp_system_message["content"] = system_message

        self.chat_history.append(temp_system_message)
        self.total_tokens = 0

        # "I am alive!"
        print("Bot initialised, name: " + self.bot_name)

    # Load message history from file
    def load_from_file(self, load_from):
        with open(load_from, 'r') as f:
            data = json.load(f)
        if data:
            self.chat_history = data
            print(self.chat_history)

    def save_json_to_file(self, contents, dir):
        with open(dir, 'w+') as json_file:
            json.dump(contents, json_file)

    # Send message to LLM, returns response
    async def send_msg(self, data_to_give):
        response = {}
        to_send = {}
        to_send['role'] = 'user'
        to_send['content'] = data_to_give
        self.chat_message = to_send

        print("chat message is: ")
        print(to_send)

        self.chat_history.append(self.chat_message)
        try:
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=self.chat_history,
                temperature=0.6,
            )
        except Exception as e:
            print("An exception occurred:", str(e))
            response = ERROR_MSG
            response["choices"][0]["message"] = {'role': 'assistant', 'content': 'Sorry, there was an exception. '+str(e)}
        
        bot_response = {}
        bot_response["role"] = response.choices[0].message.role
        bot_response["content"] = response.choices[0].message.content
        self.chat_history.append(bot_response)

        if response.usage.total_tokens > 3500:
            del self.chat_history[1]
            del self.chat_history[1]
            del self.chat_history[1]

        self.save_json_to_file(self.chat_history, self.bot_file)

        return response.choices[0].message.content
    
    # Create a generic TTS using gTTS
    # This is a robotic female voice saved in opus format
    def create_voice(self, msg):
        msgAudio = gTTS(text=msg, lang="en", slow=False)
        filename = "_Msg" + str(hash(msg)) + ".mp3"
        normalised_dir = normalise_dir(TTS_DIR)
        # Where is the file?
        msg_file_path = os.path.join(normalised_dir, filename)
        msgAudio.save(msg_file_path)

        opus_file_path, duration = self.mp3_to_opus(msg_file_path)
        rounded_duration = math.ceil(duration)

        return opus_file_path, rounded_duration
    
    # Starts playing through default audio channel using VLC
    def read_message(self, msg_file_path):
        # Start playing!
        p = vlc.MediaPlayer(msg_file_path)

        p.audio_output_device_get()
        p.play()

        time.sleep(0.1)
        
        duration = p.get_length() / 1000
        time.sleep(duration)

    # Allows you to choose which audio channel to output to using device_id
    def read_message_choose_device(self, msg_file_path, device_id):
        sample_rate, data = wavfile.read(msg_file_path)

        sd.play(data, sample_rate, device=device_id)
        sd.wait()

    # Listens to the audio input when connected in Discord
    def discord_colab(self, listen_for):
        heard_msg = speech_listener(listen_for)
        print("heard_msg is: "+heard_msg)
        return heard_msg

    def turn_to_wav(self, wavify, name):
        sample_width = 2
        channels = 1
        sample_rate=24000 

        output_directory = TTS_DIR

        os.makedirs(output_directory, exist_ok=True)

        file_name = os.path.join(output_directory, name)
        with wave.open(file_name, 'wb') as wave_file:
            wave_file.setnchannels(channels)
            wave_file.setsampwidth(sample_width)
            wave_file.setframerate(sample_rate)
            wave_file.writeframes(wavify)

        print("ttw file_name: "+file_name)
        return file_name

    def mp3_to_opus(self, path_to_start):
        mp3_file = AudioSegment.from_file(path_to_start, format="mp3")

        # Generate new filename based on old name
        output_dir = os.path.dirname(path_to_start)
        output_name = os.path.splitext(os.path.basename(path_to_start))[0]
        opus_file_path = os.path.join(output_dir, f"{output_name}.opus")
        opus_file = opus_file_path

        mp3_file.export(opus_file, format="opus", parameters=["-ar", str(mp3_file.frame_rate)])
        
        opus_duration = mp3_file.duration_seconds
        
        if os.path.exists(path_to_start):
            os.remove(path_to_start)
            print(f"{path_to_start} removed!")
        else:
            print(f"Something went wrong.")

        return opus_file_path, opus_duration

    def turn_to_opus(self, path_to_mp3ify):
        wav_file = AudioSegment.from_file(path_to_mp3ify, format="wav")

        # Generate new filename based on old name
        output_dir = os.path.dirname(path_to_mp3ify)
        output_name = os.path.splitext(os.path.basename(path_to_mp3ify))[0]
        opus_file_path = os.path.join(output_dir, f"{output_name}.opus")
        opus_file = opus_file_path

        wav_file.export(opus_file, format="opus", parameters=["-ar", str(wav_file.frame_rate)])
        
        opus_duration = wav_file.duration_seconds
        
        return opus_file_path, opus_duration

    async def playHT_wav_generator(self, to_generate):
        client = Client(
            user_id=USER_ID,
            api_key=API_KEY,
        )
        filename = None
        try:
            options = TTSOptions(voice=self.voice)
            omega_chunk = b''
            for i, chunk in enumerate(client.tts(to_generate, options)):
                if i == 0:
                    continue
                omega_chunk += chunk
            filename = "_Msg" + str(hash(omega_chunk)) + ".wav"
            wav_filepath = self.turn_to_wav(wavify=omega_chunk, name=filename)
            print("Received from wav, turning to opus: " + wav_filepath)
            filepath, file_length = self.turn_to_opus(wav_filepath)
            
            if os.path.exists(wav_filepath):
                os.remove(wav_filepath)
                print(f"{wav_filepath} removed!")
            else:
                print("Something went wrong.")
            
            print("Received from opus: " + filepath)
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            client.close()
        client.close()
        print(filepath)
        return filepath, file_length

    async def tttts(self, session_id: str, text_speaker: str = "en_us_002", req_text: str = "TikTok Text To Speech", filename: str = 'voice.mp3', play: bool = False):
        req_text = req_text.replace("+", "plus")
        req_text = req_text.replace(" ", "+")
        req_text = req_text.replace("&", "and")

        headers = {
            'User-Agent': 'com.zhiliaoapp.musically/2022600030 (Linux; U; Android 7.1.2; es_ES; SM-G988N; Build/NRD90M;tt-ok/3.12.13.1)',
            'Cookie': f'sessionid={session_id}'
        }
        url = f"https://api16-normal-v6.tiktokv.com/media/api/text/speech/invoke/?text_speaker={text_speaker}&req_text={req_text}&speaker_map_type=0&aid=1233"
        r = requests.post(url, headers = headers)

        if r.json()["message"] == "Couldn't load speech. Try again.":
            output_data = {"status": "Session ID is invalid", "status_code": 5}
            print(output_data)
            return output_data

        vstr = [r.json()["data"]["v_str"]][0]
        msg = [r.json()["message"]][0]
        scode = [r.json()["status_code"]][0]
        log = [r.json()["extra"]["log_id"]][0]
        
        dur = [r.json()["data"]["duration"]][0]
        spkr = [r.json()["data"]["speaker"]][0]

        b64d = base64.b64decode(vstr)

        with open(filename, "wb") as out:
            out.write(b64d)

        output_data = {
            "status": msg.capitalize(),
            "status_code": scode,
            "duration": dur,
            "speaker": spkr,
            "log": log
        }

        opus_file_path, duration = self.mp3_to_opus(filename)
        rounded_duration = math.ceil(duration)

        return opus_file_path, rounded_duration

def scan_audio_devices():
    devices = sd.query_devices()
    for i, device in enumerate(devices):
        print(f"{i}: {device}")

async def testing_main():
    test_bot = OpenAI_Bot(DEFAULT_NAME, SYSTEM_MESSAGE)

    ### Testing the TikTokTextToSpeech Section ###
    # filename = "implementation_test.mp3"
    # current_dir = os.getcwd()
    # print(current_dir)
    # newpath = os.path.normpath(os.path.join(current_dir, "./TikToks"))
    # print(newpath)
    # normalised_filename = os.path.normpath(os.path.join(newpath, filename))
    # print(normalised_filename)
    # sample_text = "I am a stormtrooper talking through TikTok Text To Speech."
    # opus_filename, duration = await test_bot.tttts(TIKTOK_TOKEN, 'en_us_stormtrooper', sample_text, normalised_filename)
    # print(opus_filename)
    # test_bot.read_message(opus_filename)
    # await asyncio.sleep(duration)
    # print("Done")

    ### Test STT -> TTT -> basic TTS ###
    # results = await test_bot.discord_colab(10)
    # print(results)
    # path = await test_bot.playHT_wav_generator("I am Detsy!")
    # path = "./outputs\\tester\\_Msg589158584504913860.wav"
    # test_bot.read_message(path)
    # print("Done playing")
    # scan_audio_devices()
    # test_bot.load_from_file(test_bot.bot_file)
    # response = await test_bot.send_msg("Hello, this is a first message")
    # response = speech_listener(10)
    # print(response)
    # response = await test_bot.send_msg("Is this a second message?")
    # response = speech_listener(10)
    # print(response)
    # response = await test_bot.send_msg("Is this a THIRD message?")
    # response = speech_listener(10)
    # print(response)

    ### Single message TTT version
    msg_to_test = "Do you like beatsaber?"
    response = await test_bot.send_msg(msg_to_test)
    print(response)
    test_bot.chat_history.pop()
    test_bot.chat_history.pop()
    print("==============================================================")
    response = await test_bot.send_msg(msg_to_test)
    print(response)
    test_bot.chat_history.pop()
    test_bot.chat_history.pop()
    print("==============================================================")
    response = await test_bot.send_msg(msg_to_test)
    print(response)
    test_bot.chat_history.pop()
    test_bot.chat_history.pop()
    print("==============================================================")
    response = await test_bot.send_msg(msg_to_test)
    print(response)
    test_bot.chat_history.pop()
    test_bot.chat_history.pop()
    print("==============================================================")

if __name__ == "__main__":
    asyncio.run(testing_main())
