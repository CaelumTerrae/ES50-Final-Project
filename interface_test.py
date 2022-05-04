import pyaudio
import numpy as np
import time
import wave
import os

settings_file = open('Config/settings.prt', 'r')
parameters = settings_file.readlines()
settings_file.close()
RECORD_SECONDS = 5
WAVE_OUTPUT_FILENAME = "recordedFile.wav"

RATE = int(parameters[0])  # sample rate
CHUNK = int(parameters[1])  # buffer size
FORMAT = pyaudio.paInt16  # specifies bit depth (16-bit)
CHANNELS = 2  # mono audio
latency_in_milliseconds = int(parameters[2])
LATENCY = round((latency_in_milliseconds/1000) *
                (RATE/CHUNK))  # latency in buffers
INDEVICE = int(parameters[3])  # index (per pyaudio) of input device
OUTDEVICE = int(parameters[4])  # index of output device
print('looking for devices ' + str(INDEVICE) + ' and ' + str(OUTDEVICE))
# allowance in milliseconds for pressing 'stop recording' late
overshoot_in_milliseconds = int(parameters[5])
OVERSHOOT = round((overshoot_in_milliseconds/1000) *
                  (RATE/CHUNK))  # allowance in buffers
MAXLENGTH = int(12582912 / CHUNK)  # 96mb of audio in total
# maximum possible value for an audio sample (little bit of margin)
SAMPLEMAX = 0.9 * (2**15)
# length of the first recording on track 1, all subsequent recordings quantized to a multiple of this.
LENGTH = 0

debounce_length = 0.1  # length in seconds of button debounce period

silence = np.zeros([CHUNK], dtype=np.int16)  # a buffer containing silence

# mixed output (sum of audio from tracks) is multiplied by output_volume before being played.
# This is updated dynamically as max peak in resultant audio changes
output_volume = np.float16(1.0)

# multiplying by upramp and downramp gives fade-in and fade-out
downramp = np.linspace(1, 0, CHUNK)
upramp = np.linspace(0, 1, CHUNK)
# fadein() applies fade-in to a buffer


def fadein(buffer):
    np.multiply(buffer, upramp, out=buffer, casting='unsafe')
# fadeout() applies fade-out to a buffer


def fadeout(buffer):
    np.multiply(buffer, downramp, out=buffer, casting='unsafe')


pa = pyaudio.PyAudio()


def looping_callback(in_data, frame_count, time_info, status):
    global LENGTH
    LENGTH = LENGTH + 1
    print(LENGTH)
    return (silence, pyaudio.paContinue)


stream = pa.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    input=True,
    output=True,
    input_device_index=INDEVICE,
    output_device_index=OUTDEVICE,
    frames_per_buffer=CHUNK,
    start=True,
    stream_callback=looping_callback
)
print("recording started")
Recordframes = []

for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
    data = stream.read(CHUNK, exception_on_overflow=False)
    Recordframes.append(data)
print("recording stopped")

stream.stop_stream()
stream.close()
pa.terminate()
waveFile = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
waveFile.setnchannels(CHANNELS)
waveFile.setsampwidth(pa.get_sample_size(FORMAT))
waveFile.setframerate(RATE)
waveFile.writeframes(b''.join(Recordframes))
waveFile.close()
