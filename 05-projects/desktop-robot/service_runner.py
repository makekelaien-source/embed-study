"""Headless service entry: identify USB audio by name, then load voice once."""
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parent


def resolve_devices(devices,input_name='USB PnP Sound Device',output_name='CD002-AUDIO'):
    def find(name,kind):
        matches=[(i,d) for i,d in enumerate(devices) if name in d['name'] and d[f'max_{kind}_channels']>0]
        if len(matches)!=1:
            raise ValueError(f'USB {kind} {name!r}: found {len(matches)}, need exactly one')
        index,device=matches[0]
        card=re.search(r'hw:(\d+),',device['name'])
        if not card:
            raise ValueError(f'无法确定ALSA声卡: {device["name"]}')
        return index,int(card.group(1))
    i,ic=find(input_name,'input')
    o,oc=find(output_name,'output')
    return i,o,ic,oc


def notify_ready(path=None):
    if path:
        path=Path(path)
        path.parent.mkdir(parents=True,exist_ok=True)
        temporary=path.with_suffix('.tmp')
        temporary.write_text(json.dumps({'state':'ready','pid':os.getpid(),
            'monotonic':time.monotonic()}),encoding='utf8')
        temporary.replace(path)
    address=os.environ.get('NOTIFY_SOCKET')
    if address:
        if address.startswith('@'):address='\0'+address[1:]
        with socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM) as sock:
            sock.sendto(b'READY=1\nSTATUS=Offline voice ready',address)
    print('READY: offline voice loaded; waiting for speech',flush=True)


def main():
    import sounddevice as sd
    ready=ROOT/'.local/service-ready.json'
    ready.unlink(missing_ok=True)
    language=os.environ.get('ROBOT_LANGUAGE','zh')
    if language not in ('zh','en'):raise ValueError('ROBOT_LANGUAGE must be zh or en')
    deadline=time.monotonic()+45
    while True:
        try:
            # Refresh PortAudio after USB enumeration; there is no open stream yet.
            sd._terminate();sd._initialize()
            i,o,ic,oc=resolve_devices(sd.query_devices(),
                os.environ.get('ROBOT_INPUT_NAME','USB PnP Sound Device'),
                os.environ.get('ROBOT_OUTPUT_NAME','CD002-AUDIO'))
            break
        except (ValueError,sd.PortAudioError) as error:
            if time.monotonic()>=deadline:raise RuntimeError('USB音频设备等待超时') from error
            print(f'Waiting for USB audio: {error}',flush=True)
            time.sleep(2)
    subprocess.run(['amixer','-c',str(ic),'sset','Mic','8','cap'],check=True)
    subprocess.run(['amixer','-c',str(oc),'sset','PCM','70%','unmute'],check=True)
    try:
        return subprocess.call([sys.executable,'-u',str(ROOT/'run_fast.py'),'--language',language,
            '--auto-listen','--ready-file',str(ready),'--input-device',str(i),
            '--output-device',str(o),'--metrics',str(ROOT/'.local/service-turns.jsonl')],cwd=ROOT)
    finally:
        ready.unlink(missing_ok=True)


if __name__=='__main__':raise SystemExit(main())
