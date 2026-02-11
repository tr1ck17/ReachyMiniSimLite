# Reachy Mini Lite Text-to-Speech (USB Connection)

Make your Reachy Mini Lite robot speak aloud via USB connection!

## About

This script provides text-to-speech capabilities for the Reachy Mini Lite when connected via USB. Since the Reachy Mini Lite doesn't have built-in speakers, the audio will play through your computer's speakers/headphones.

## Prerequisites

- Reachy Mini Lite robot
- USB connection to your computer
- Python 3.7 or higher
- Computer speakers or headphones for audio output

## Installation

### 1. Install Python Dependencies

```bash
pip install -r requirements_mini_lite.txt
```

Or install directly:

```bash
pip install pyttsx3
```

### 2. Platform-Specific Setup

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install espeak espeak-data
```

**macOS:**
- No additional setup needed (uses built-in `say` command)

**Windows:**
- No additional setup needed (uses SAPI5)

## Usage

### Quick Start

Simply run the script:

```bash
python reachy_mini_lite_tts.py
```

### Available Modes

1. **Interactive Mode** (default)
   - Type what you want Reachy to say
   - Use commands to change voice settings
   - Type 'quit' to exit

2. **Demo Mode**
   - Pre-programmed demonstration
   - Shows various capabilities

3. **Custom Script Mode**
   - Edit the script to add your own sequence

### Interactive Mode Commands

When in interactive mode, you can use these commands:

- **Text input** - Reachy will speak whatever you type
- `quit` or `exit` - Exit the program
- `demo` - Run the demonstration
- `voices` - List all available voices
- `speed [number]` - Change speech rate (e.g., `speed 180`)
- `voice [number]` - Change voice (e.g., `voice 1`)

### Example Code Usage

```python
from reachy_mini_lite_tts import ReachyMiniLiteTalker

# Initialize
talker = ReachyMiniLiteTalker()

# Make Reachy speak
talker.speak("Hello, I am Reachy Mini Lite!")

# Change voice settings
talker.configure_voice(rate=180, volume=0.8)

# Speak with custom delay
talker.speak_with_delay("This comes after a delay", delay=1.0)

# List available voices
talker.list_available_voices()
```

## Customization

### Speech Rate
- Default: 150 words per minute
- Recommended range: 100-250
- Lower = slower, Higher = faster

```python
talker.configure_voice(rate=180)
```

### Volume
- Range: 0.0 (mute) to 1.0 (maximum)

```python
talker.configure_voice(volume=0.8)
```

### Voice Selection

First, list available voices:
```python
talker.list_available_voices()
```

Then select by index:
```python
talker.configure_voice(voice_index=1)  # Usually female voice
```

## USB Connection Notes

Since you're connected via USB:
- The Reachy Mini Lite receives commands via USB serial
- Audio plays through your computer's speakers/headphones
- No network connection required for TTS
- You can control Reachy's movements while it "speaks"

## Combining with Movement

If you want to make Reachy move while speaking, you can integrate with the Reachy SDK:

```python
from reachy_sdk_api import ReachySDK
from reachy_mini_lite_tts import ReachyMiniLiteTalker

# Initialize both
reachy = ReachySDK(host='localhost')  # or your USB serial connection
talker = ReachyMiniLiteTalker()

# Speak and move
talker.speak("I'm moving my arm now!")
# Add movement commands here
```

## Troubleshooting

### No audio output
- Check system volume settings
- Verify speakers/headphones are connected
- Test with: `talker.speak("test")`

### "pyttsx3 not found"
```bash
pip install --upgrade pyttsx3
```

### "espeak not found" (Linux)
```bash
sudo apt-get install espeak espeak-data libespeak-dev
```

### Robotic or choppy voice
- Try adjusting the speech rate: `talker.configure_voice(rate=140)`
- Try different voices: `talker.list_available_voices()`

### Voice is too fast/slow
- Adjust rate: `talker.configure_voice(rate=180)` for faster
- Or: `talker.configure_voice(rate=120)` for slower

## Advanced: Creating Custom Scripts

Edit the `main()` function to create your own sequences:

```python
def custom_sequence(talker):
    """Your custom speech sequence."""
    talker.speak("Starting my custom routine")
    time.sleep(1)
    
    # Your sequence here
    phrases = [
        "First action complete",
        "Now doing second action",
        "All done!"
    ]
    
    for phrase in phrases:
        talker.speak(phrase)
        time.sleep(0.5)  # Pause between phrases
```

## Alternative TTS Options

If pyttsx3 doesn't work well, try these alternatives:

### Google TTS (requires internet)
```bash
pip install gtts playsound
```

```python
from gtts import gTTS
import os

text = "Hello from Reachy"
tts = gTTS(text=text, lang='en')
tts.save("speech.mp3")
os.system("mpg321 speech.mp3")  # Linux
# or os.system("afplay speech.mp3")  # macOS
```

## Examples

Check the script for built-in examples:
- Greeting sequence
- Multi-phrase demonstration
- Interactive conversation mode

## Resources

- [Reachy Mini Lite Documentation](https://docs.pollen-robotics.com/)
- [pyttsx3 Documentation](https://pyttsx3.readthedocs.io/)
- [Python Speech Recognition](https://pypi.org/project/SpeechRecognition/) - Add voice input!

## License

Example code for educational purposes.

## Support

For issues specific to:
- **Reachy hardware**: Contact Pollen Robotics support
- **TTS library**: Check pyttsx3 documentation
- **This script**: Review troubleshooting section above
