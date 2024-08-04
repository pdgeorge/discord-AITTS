# VRChat-AI-Assistant
AI Assistant to chat with and to engage (in a limited capacity) in VRChat

Integrations with play.ht for 'realistic' voice. Currently based on a small streamer known as DetsyVR. 

# Installation:

## First:

pip install -r requirements.txt

## Secondly

As the voice module of the py-cord library is specialised it must be installed by itself.

python3 -m pip install -U "py-cord[voice]"

# create a .env file with your API keys for the following:

CYRA_DISCORD=

OPENAI_API_KEY=

PLAY_HT_USER_ID=

PLAY_HT_API_KEY=

TIKTOK_TOKEN=

CYRA_DISCORD is your Discord bot's API Token
OPENAI_API_KEY is your key from OPENAI
PLAY_HY_USER_ID and PLAY_HT_API_KEY are received from play.ht 

# Get TikTok Token

Install Cookie Editor extension for your browser.
Log in to TikTok Web.
While on TikTok web, open the extension and look for sessionid.
Copy the sessionid value. (It should be an alphanumeric value)
The sessionid is the Token you need.

# Usage Instructions

Join a Discord voice channel.
Ensure that someone has a role named "Cyra-chatter" to execute commands.
Within that channel, you can type !help to view all of the available commands.

The following commands will cause Cyra to join the voice channel you are in, assuming you send the message in the text channel associated with the voice channel.
Once Cyra is in the voice channel, she will begin to 'speak' each of the messages sent within the channel out loud in the voice selected when joining. This voice can be changed once in using a new command if desired.

## !join 
Will use the gTTS voice.

## !ttttsjoin 
Will give access to the suite of TikTokTextToSpeech voices. The default voice is that of a Stormtrooper.
Use the command !voices to see the list of voices available.
Use the command !voice <num> to choose from the previous list a new voice.

## !aijoin
Will speak using the playht aitts functionality, using the voice connected to whichever AI personality is loaded.

# AI Personalities
Multiple AI personalities are available and can be found in vrchat_ais.json, with the currently loaded one found in vrchat_ai.json.

# !ask
It is possible to ask the AI single questions and it will answer with a message history.

# !start
It will begin talking with you in a conversational stt -> ttt -> tts manner using the loaded personality and voice.

# !checkPersona
Will return available personalities.

# !loadPersona
Will load a selected personality, or will give an error if the selected personality wasn't in checkPersona.
