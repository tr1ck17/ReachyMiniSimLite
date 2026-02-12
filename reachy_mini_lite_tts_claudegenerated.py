
"""
Reachy Mini Lite Text-to-Speech Script (USB Connection)
This script enables the Reachy Mini Lite robot to speak aloud using text-to-speech.
Designed for USB serial connection.
"""

import time
import pyttsx3  # Text-to-speech library

class ReachyMiniLiteTalker:
    def __init__(self):
        """
        Initialize the TTS engine for Reachy Mini Lite.
        No SDK connection needed - just audio output from your computer.
        """
        print("Initializing Reachy Mini Lite TTS...")
        
        # Initialize text-to-speech engine
        self.tts_engine = pyttsx3.init()
        
        # Configure TTS properties
        self.configure_voice()
        print("TTS engine ready!")
        
    def configure_voice(self, rate=150, volume=1.0, voice_index=None):
        """
        Configure the voice properties for TTS.
        
        Args:
            rate (int): Speech rate (words per minute)
            volume (float): Volume level (0.0 to 1.0)
            voice_index (int): Voice selection index (None for default)
        """
        # Set speech rate
        self.tts_engine.setProperty('rate', rate)
        
        # Set volume
        self.tts_engine.setProperty('volume', volume)
        
        # Set voice if specified
        if voice_index is not None:
            voices = self.tts_engine.getProperty('voices')
            if 0 <= voice_index < len(voices):
                self.tts_engine.setProperty('voice', voices[voice_index].id)
                print(f"Voice set to: {voices[voice_index].name}")
        
    def list_available_voices(self):
        """List all available voices on the system."""
        voices = self.tts_engine.getProperty('voices')
        print("\nAvailable voices:")
        for i, voice in enumerate(voices):
            print(f"{i}: {voice.name} ({voice.id})")
        return voices
        
    def speak(self, text):
        """
        Make Reachy speak the given text.
        
        Args:
            text (str): Text to be spoken
        """
        print(f"🤖 Reachy says: {text}")
        self.tts_engine.say(text)
        self.tts_engine.runAndWait()
        
    def speak_with_delay(self, text, delay=0.5):
        """
        Speak text with a delay before speaking.
        
        Args:
            text (str): Text to be spoken
            delay (float): Delay in seconds before speaking
        """
        time.sleep(delay)
        self.speak(text)
        
    def stop_speaking(self):
        """Stop any ongoing speech."""
        self.tts_engine.stop()


def demo_mode(talker):
    """Run a demonstration of Reachy's speech capabilities."""
    print("\n" + "="*50)
    print("REACHY MINI LITE TTS DEMO")
    print("="*50)
    
    # Greeting
    talker.speak("Hello! I am Reachy Mini Lite.")
    time.sleep(0.5)
    
    # Introduction
    talker.speak("I am connected via USB and ready to talk!")
    time.sleep(0.5)
    
    # Capabilities
    phrases = [
        "I can speak at different speeds.",
        "I can help you with various tasks.",
        "My compact design makes me very portable."
    ]
    
    for phrase in phrases:
        talker.speak(phrase)
        time.sleep(0.3)
    
    print("\nDemo complete!")


def interactive_mode(talker):
    """Interactive mode where user can type what Reachy should say."""
    print("\n" + "="*50)
    print("INTERACTIVE MODE")
    print("="*50)
    print("Commands:")
    print("  'quit' or 'exit' - Exit the program")
    print("  'demo' - Run demonstration")
    print("  'voices' - List available voices")
    print("  'speed [number]' - Change speech speed (e.g., 'speed 180')")
    print("  'voice [number]' - Change voice (e.g., 'voice 1')")
    print("  Anything else - Reachy will say it!")
    print("="*50)
    
    while True:
        try:
            user_input = input("\n💬 What should Reachy say? ").strip()
            
            if not user_input:
                continue
                
            # Handle commands
            if user_input.lower() in ['quit', 'exit', 'q']:
                talker.speak("Goodbye! See you next time!")
                break
                
            elif user_input.lower() == 'demo':
                demo_mode(talker)
                
            elif user_input.lower() == 'voices':
                talker.list_available_voices()
                
            elif user_input.lower().startswith('speed '):
                try:
                    speed = int(user_input.split()[1])
                    talker.configure_voice(rate=speed)
                    print(f"✓ Speech rate set to {speed} words per minute")
                except (ValueError, IndexError):
                    print("❌ Usage: speed [number] (e.g., speed 180)")
                    
            elif user_input.lower().startswith('voice '):
                try:
                    voice_idx = int(user_input.split()[1])
                    talker.configure_voice(voice_index=voice_idx)
                except (ValueError, IndexError):
                    print("❌ Usage: voice [number] (e.g., voice 1)")
                    
            else:
                # Speak the user's input
                talker.speak(user_input)
                
        except KeyboardInterrupt:
            print("\n\nInterrupted by user.")
            talker.speak("Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


def main():
    """Main function for Reachy Mini Lite TTS."""
    
    print("""
    ╔══════════════════════════════════════════╗
    ║   Reachy Mini Lite Text-to-Speech       ║
    ║   USB Connection Version                 ║
    ╚══════════════════════════════════════════╝
    """)
    
    try:
        # Initialize TTS
        talker = ReachyMiniLiteTalker()
        
        # Ask user what mode to use
        print("\nSelect mode:")
        print("1. Interactive mode (type what Reachy should say)")
        print("2. Demo mode (predefined demonstration)")
        print("3. Custom script (edit this file to add your own)")
        
        choice = input("\nEnter choice (1-3, or press Enter for interactive): ").strip()
        
        if choice == "2":
            demo_mode(talker)
        elif choice == "3":
            # Custom script area - add your own code here
            print("\nRunning custom script...")
            talker.speak("This is the custom script area.")
            talker.speak("You can edit the code to add your own sequence here.")
        else:
            # Default to interactive mode
            interactive_mode(talker)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting tips:")
        print("- Ensure pyttsx3 is installed: pip install pyttsx3")
        print("- On Linux, install espeak: sudo apt-get install espeak")
        print("- Check that your audio output is working")
        
    print("\n✓ Program ended.")


if __name__ == "__main__":
    main()
