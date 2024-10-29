# import sounddevice as sd
# from scipy.io.wavfile import write
# from pynput import keyboard
# from openai import OpenAI
# import threading
# import time
# import os
# from dotenv import load_dotenv

# load_dotenv()

# os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "default_api_key")
# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# import numpy as np
# import sounddevice as sd

# def record_audio_on_key(key_combination=('cmd', 'r'), duration=10, sample_rate=44100, file_name='output.wav'):
#     """
#     Starts recording audio when the specified key combination is pressed and stops 
#     when it is pressed again, with a bouncing bar animation indicating recording status.
#     Returns the filename once the recording is done.
#     """
#     sd.default.device = 'MacBook Pro Microphone, Core Audio'
#     recording = False
#     audio_data = None
#     stop_event = threading.Event()
#     lock = threading.Lock()
#     current_keys = set()

#     def animation():
#         spinner = ['|', '/', '-', '\\']
#         idx = 0
#         while not stop_event.is_set():
#             if recording:
#                 print(f"\r{spinner[idx % len(spinner)]}", end='', flush=True)
#                 idx += 1
#                 time.sleep(0.2)
#             else:
#                 print("\r", end='', flush=True)
#                 time.sleep(0.2)

#     def toggle_recording():
#         nonlocal recording, audio_data
#         with lock:
#             if not recording:
#                 audio_data = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
#                 recording = True
#                 stop_event.clear()  # Clear the stop event for animation
#             else:
#                 sd.stop()
#                 recording = False
#                 stop_event.set()  # Stop the animation

#                 # Save the audio file
#                 write(file_name, sample_rate, audio_data)
#                 exit()

#     def on_press(key_input):
        
#         try:
#             if key_input == keyboard.Key.cmd:
#                 current_keys.add('cmd')
#             elif hasattr(key_input, 'char') and key_input.char == 'r':
#                 current_keys.add('r')

#             if all(k in current_keys for k in ['cmd', 'r']):
#                 toggle_recording()

#         except AttributeError:
#             pass

#     def on_release(key_input):
#         try:
#             if key_input == keyboard.Key.cmd:
#                 current_keys.discard('cmd')
#             elif hasattr(key_input, 'char') and key_input.char == 'r':
#                 current_keys.discard('r')
#         except AttributeError:
#             pass

#     print("Press 'Cmd + R' to start/stop recording.")

#     # Start the bouncing bar animation thread
#     anim_thread = threading.Thread(target=animation, daemon=True)
#     anim_thread.start()

#     # Set up the keyboard listener
#     listener = keyboard.Listener(on_press=on_press, on_release=on_release)
#     listener.start()

#     # Wait for the user to finish recording
#     listener.join()

#     # Stop the animation thread
#     anim_thread.join()

#     # Return the filename once the recording is complete
#     return file_name

# # Run the function


# def speech_to_text(file_name):
#         result = ""
#         try:
#             audio_file= open(file_name, "rb")
#             transcription = client.audio.transcriptions.create(
#             model="whisper-1", 
#             language="en",
#             file=audio_file
#             )
#             result = transcription.text 
#         except Exception as e:
#             print(f"Error transcribing audio: {e}")

#         return result

# def get_user_input():
#     file_name = record_audio_on_key()
#     text = speech_to_text(file_name)
#     return text


import sounddevice as sd
from scipy.io.wavfile import write
from openai import OpenAI
import threading
import time
import os
from dotenv import load_dotenv

load_dotenv()

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "default_api_key")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

import numpy as np

def record_audio(duration=10, sample_rate=44100, file_name='output.wav'):
    """
    Starts and stops recording audio when 'Enter' is pressed.
    Displays an animation to indicate recording status.
    Returns the filename once the recording is done.
    """
    sd.default.device = 'MacBook Pro Microphone, Core Audio'
    recording = False
    audio_data = None
    stop_event = threading.Event()

    def animation():
        spinner = ['|', '/', '-', '\\']
        idx = 0
        while not stop_event.is_set():
            if recording:
                print(f"\rRecording... {spinner[idx % len(spinner)]}", end='', flush=True)
                idx += 1
                time.sleep(0.2)
            else:
                print("\r", end='', flush=True)
                time.sleep(0.2)

    print("Press 'Enter' to start recording...")
    input()  # Wait for first 'Enter' to start recording

    # Start recording
    recording = True
    audio_data = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
    
    # Start the animation in a separate thread
    anim_thread = threading.Thread(target=animation, daemon=True)
    anim_thread.start()

    print("Recording started. Press 'Enter' to stop...")
    input()  # Wait for second 'Enter' to stop recording

    # Stop recording
    sd.stop()
    recording = False
    stop_event.set()  # Stop the animation thread

    # Save the audio file
    write(file_name, sample_rate, audio_data)
    anim_thread.join()

    print(f"\nRecording saved as {file_name}")
    return file_name

def speech_to_text(file_name):
    result = ""
    try:
        with open(file_name, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                language="en",
                file=audio_file
            )
            result = transcription.text 
    except Exception as e:
        print(f"Error transcribing audio: {e}")

    return result

def get_user_input():
    file_name = record_audio()
    text = speech_to_text(file_name)
    return text

# Run the function
if __name__ == "__main__":
    result = get_user_input()
    print(f"Transcription: {result}")
