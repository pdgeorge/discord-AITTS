# VRChat-AI-Assistant
AI Assistant to chat with and to engage (in a limited capacity) in VRChat

Integrations with play.ht for 'realistic' voice. Currently based on a small streamer known as DetsyVR. 

# Workflow:

Microphone listens -> STT transcribe -> chatGPT -> play.ht TTS response -> loop

## Still in development. Can do everything that is needed, can connect to a Discord server, listen to the user who uses the !start command and has a "human like" conversation with them.
## Testing cog has been added.
## Currently in progress: Tidying everything up, making it more modular to allow things to read from file. To improve the ability to have different people in the future.
### Thoughts for extentions:

With the inclusion of the ability to load different personas based on vrchat_ai.txt, potentially extend VrchatAI cog to have a !personalist option which lists available personas with a brief description of each from a file (array of dictionary). Then !load <persona> to load the chosen one in to vrchat_ai.txt. After that, reload the cog or reload self.vrchat_ai.