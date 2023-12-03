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

TEXT_DIR = ""
TTS_DIR = "./outputs/"
COLAB_PARTNER = "pdgeorge" # For when there is a colab partner, enter the name here.
DEFAULT_NAME = "TAI" # Which personality is being loaded
MESSAGE_CHANCE = 5 # Chance for user name to be included in the message, 1 in MESSAGE_CHANGE
SYSTEM_MESSAGE = "You are an AI designed to play Roleplaying games with other AI."
WAKE_UP_MESSAGE = "It's time to wake up."
APIKEY = os.getenv("OPENAI_API_KEY")
USER_ID = os.getenv("PLAY_HT_USER_ID")
API_KEY = os.getenv("PLAY_HT_API_KEY")

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

async def speech_listener(listen_for):
    r = sr.Recognizer()
    transcription = "Not yet"
    error_checker = True
    while error_checker:
        with sr.Microphone() as source:
            print("Recording started")
            audio = r.listen(source, timeout=listen_for)  # Capture the audio input
        try:
            transcription = r.recognize_whisper(audio, language="english", model="base.en")  # Perform the speech-to-text transcription
            error_checker = False
        except sr.UnknownValueError:
            print("Speech recognition could not understand audio")
            transcription = "Error"
        except sr.RequestError as e:
            print("Could not request speech recognition results; {0}".format(e))
            transcription = "Error"
        while transcription == "Not yet":
            await asyncio.sleep(0.1)
    return transcription

class OpenAI_Bot():
    def __init__(self, bot_name, system_message):
        self.chat_history = []
        self.bot_name = bot_name
        self.voice = """s3://voice-cloning-zero-shot/900b9c8f-d12e-46b5-acc2-3d60b56351d9/detsyvr/manifest.json"""
        self.wink_flag = False
        self.last_emote = "f1"

        self.start_datetime = datetime.datetime.now()
        formatted_datetime = self.start_datetime.strftime("%Y-%m-%d_%H-%M-%S")
        path = normalise_dir(TEXT_DIR)
        path = os.path.join(path, bot_name)
        temp_bot_file = f"{self.bot_name}_{formatted_datetime}.txt"
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
    async def load_from_file(self, load_from):
        with open(load_from, 'r') as f:
            data = json.load(f)
        if data:
            self.chat_history = data
            print(self.chat_history)

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

        return response.choices[0].message.content
    
    # Create a generic TTS using gTTS
    # This is a robotic female voice
    async def create_message(self, msg):
        msgAudio = gTTS(text=msg, lang="en", slow=False)
        filename = "_Msg" + str(hash(msg)) + ".wav"
        normalised_dir = normalise_dir(TTS_DIR)
        
        # Where is the file?
        msg_file_path = os.path.join(normalised_dir, filename)
        msgAudio.save(msg_file_path)

        return msg_file_path
    
    # Starts playing through default audio channel using VLC
    async def read_message(self, msg_file_path):
        # Start playing!
        p = vlc.MediaPlayer(msg_file_path)

        p.audio_output_device_get()
        p.play()

        await asyncio.sleep(0.1)
        
        duration = p.get_length() / 1000
        await asyncio.sleep(duration)

    # Allows you to choose which audio channel to output to using device_id
    async def read_message_choose_device(self, msg_file_path, device_id):
        sample_rate, data = wavfile.read(msg_file_path)

        sd.play(data, sample_rate, device=device_id)
        sd.wait()

    # Listens to the audio input when connected in Discord
    async def discord_colab(self, listen_for):
        heard_msg = await speech_listener(listen_for)
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
            filepath = self.turn_to_wav(wavify=omega_chunk, name=filename)
            print("Received from wav, turning to opus: " + filepath)
            filepath, file_length = self.turn_to_opus(filepath)
            print("Received from opus: " + filepath)
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            client.close()
        client.close()
        print(filepath)
        return filepath, file_length

def scan_audio_devices():
    devices = sd.query_devices()
    for i, device in enumerate(devices):
        print(f"{i}: {device}")

async def testing_main():
    test_bot = OpenAI_Bot(DEFAULT_NAME, SYSTEM_MESSAGE)

    # results = await test_bot.discord_colab(10)
    # print(results)

    path = await test_bot.playHT_wav_generator("I am Detsy!")
    # path = "C:\development\VRChatAI\_Msg-1823043863420221505.wav"
    await test_bot.read_message(path)
    print("Done playing")
    # scan_audio_devices()
    # await test_bot.load_from_file("TAI_Test.txt")
    #response = await test_bot.send_msg("Hello, who are you?")
    # response = speech_listener(10)
    # await test_bot.read_message_two(response)
    # response = await test_bot.send_msg("Is this a second message?")
    # response = speech_listener(10)
    # await test_bot.read_message_two(response)
    # response = await test_bot.send_msg("Is this a THIRD message?")
    # response = speech_listener(10)
    # await test_bot.read_message_two(response)
    # voice_tester()

if __name__ == "__main__":
    asyncio.run(testing_main())
