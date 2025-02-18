import pyttsx3

def text_to_speech(text: str, rate: int = 170, volume: float = 1.0, voice_index: int = 1, save_to_file: str = None):
    engine = pyttsx3.init()
    
    # Adjust speaking rate
    engine.setProperty('rate', rate)
    
    # Adjust volume
    engine.setProperty('volume', volume)
    
    # Change voice if available
    voices = engine.getProperty('voices')
    if len(voices) > voice_index:
        engine.setProperty('voice', voices[voice_index].id)
    
    # Speak text
    engine.say(text)
    engine.runAndWait()
    
    # Save to file if specified
    if save_to_file:
        engine.save_to_file(text, save_to_file)
        engine.runAndWait()
    
    # Stop engine
    engine.stop()

# Example usage
text_to_speech("Hello, this is a text-to-speech test.")