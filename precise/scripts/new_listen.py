#!/usr/bin/env python3
# Copyright 2018 Mycroft AI Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from select import select
from sys import stdin
from termios import tcsetattr, tcgetattr, TCSADRAIN

import pyaudio
import tty
import wave
from os.path import isfile
from prettyparse import create_parser
import numpy as np

from precise.network_runner import Listener

usage = '''
    Record audio samples for use with precise
    
    :-w --width int 2
        Sample width of audio
    
    :-r --rate int 16000
        Sample rate of audio
    
    :-c --channels int 1
        Number of audio channels
'''

RECORD_KEY = ' '

def key_pressed():
    return select([stdin], [], [], 0) == ([stdin], [], [])

def should_return():
    return key_pressed() and stdin.read(1) == RECORD_KEY


def record_until(p, stream, listener, chunk_size, args):
    frames = []
    while not should_return():
        chunk = stream.read(chunk_size, exception_on_overflow = False)
        #print('read chunk len: ', len(chunk))
        frames.append(chunk)
        #print('read frames len: ', np.shape(frames))
        prob = listener.update(chunk)
        print('prob: ', prob)

    stream.stop_stream()
    stream.close()

    return b''.join(frames)

def _main():
    parser = create_parser(usage)
    args = parser.parse_args()

    chunk_size = 1024
    listener = Listener('HirogoAll.net', chunk_size)
    p = pyaudio.PyAudio()
    
    print("================================================")
    x = 0
    info = p.get_host_api_info_by_index(x)
    numdevices = info.get('deviceCount')
    print('numdevices: ', numdevices)
    for i in range(0, numdevices):
        if (p.get_device_info_by_host_api_device_index(x, i).get('maxInputChannels')) > 0:
            print ("Input Device id ", i, " - ",
                   p.get_device_info_by_host_api_device_index(x, i).get('name'),
                   p.get_device_info_by_index(i).get('defaultSampleRate'))
    
    print("================================================")

    stream = p.open(format=p.get_format_from_width(args.width), channels=args.channels,
                    rate=args.rate, input=True, frames_per_buffer=chunk_size, input_device_index=2)

    while True:
        d = record_until(p, stream, listener, chunk_size, args)

    p.terminate()

if __name__ == '__main__':
    _main()