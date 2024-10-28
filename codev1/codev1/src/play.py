import threading
import sounddevice as sd
import soundfile as sf

from codev1.src.utils import cprint

def play_audio(tone, device="MacBook Pro Speakers, Core Audio"):
    """
    Load an audio file into memory and play its contents.
    
    Args:
        file_path (str): The path to the audio file to be played back.
        device (int or str, optional): The output device (numeric ID or substring).
    """
    event = threading.Event()

    try:
        data, fs = sf.read(f"/Users/saravanan/base/code-assist/codev1/codev1/src/assets/sound/{tone}.mp3", always_2d=True)

        current_frame = 0

        def callback(outdata, frames, time, status):
            nonlocal current_frame
            chunksize = min(len(data) - current_frame, frames)
            outdata[:chunksize] = data[current_frame:current_frame + chunksize]
            if chunksize < frames:
                outdata[chunksize:] = 0
                raise sd.CallbackStop()
            current_frame += chunksize

        stream = sd.OutputStream(
            samplerate=fs, device=device, channels=data.shape[1],
            callback=callback, finished_callback=event.set)
        with stream:
            event.wait()  # Wait until playback is finished
    except KeyboardInterrupt:
        cprint('\nPlayback interrupted by user.', 'error')
    except Exception as e:
        cprint(f'Error: {type(e).__name__}: {e}', 'error')

