"""Replay immutable PCM through capture without stopping on an empty ASR result.

This diagnostic never receives expected prompts. Times index original PCM, not
verified human speech. Transcript acceptance only means nonempty linguistic text.
"""
import io
import json
from pathlib import Path
import wave
import zipfile
import numpy as np
from audio_capture import UtteranceGate


def meaningful_transcript(text):
    return any(c.isalnum() for c in text)


def read_pcm(source):
    with wave.open(source, 'rb') as w:
        if w.getsampwidth()!=2: raise ValueError('requires PCM16')
        rate=w.getframerate(); channels=w.getnchannels()
        pcm=np.frombuffer(w.readframes(w.getnframes()),'<i2').astype('float32')/32768
    return pcm.reshape(-1,channels).mean(axis=1),rate


def replay(samples,rate,recognize,*,threshold=10**(-46/20),silence=.55,detector=None):
    """Yield every complete segment, continuing after punctuation-only/noise ASR.

    Fixed 20ms replay. No expected questions, substitutions, or labels enter ASR.
    Replay does not append synthetic silence or claim trailing partials complete.
    """
    gate=UtteranceGate(threshold,200,500,silence,idle_seconds=len(samples)/rate+1,sample_rate=rate)
    block=round(rate*.02)
    for start in range(0,len(samples),block):
        part=samples[start:start+block]
        voiced=True if detector is None else detector(part,rate)
        result=gate.feed(part,speech_detected=voiced)
        if result is not None and result.state=='done':
            text=recognize(result.samples,rate)
            yield {'start_s':result.start_sample/rate,'end_s':result.end_sample/rate,
                   'last_energy_frame_s':result.last_voice_sample/rate,
                   'text':text,'nonempty_text':meaningful_transcript(text)}


def main():
    import argparse,time
    from scipy.signal import resample_poly
    from math import gcd
    import sherpa_onnx
    parser=argparse.ArgumentParser();parser.add_argument('--archive',type=Path,required=True)
    parser.add_argument('--assets',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(); rows=[]
    model=args.assets/'sherpa-onnx-sense-voice-zh-en-ja-ko-yue-int8-2024-07-17'
    with zipfile.ZipFile(args.archive) as z:
        for lang in ('zh','auto'):
            r=sherpa_onnx.OfflineRecognizer.from_sense_voice(model=str(model/'model.int8.onnx'),tokens=str(model/'tokens.txt'),language=lang,use_itn=True,num_threads=4)
            def recognize(pcm,rate):
                d=gcd(rate,16000);pcm=resample_poly(pcm,16000//d,rate//d) if rate!=16000 else pcm
                s=r.create_stream();s.accept_waveform(16000,pcm);r.decode_stream(s);return s.result.text.strip()
            for name in z.namelist():
                if not any(t in name for t in ('zh-04-','zh-12-')) or not name.endswith(('-input.wav','-microphone.wav')):continue
                pcm,rate=read_pcm(io.BytesIO(z.read(name)));began=time.perf_counter()
                row={'file':name,'language':lang,'duration_s':len(pcm)/rate,'rms':float(np.sqrt(np.mean(pcm**2))),
                     'direct_full_transcript':recognize(pcm,rate),'segments':list(replay(pcm,rate,recognize))}
                row['processing_s']=time.perf_counter()-began;rows.append(row);print(json.dumps(row,ensure_ascii=False),flush=True)
    args.output.write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')

if __name__=='__main__':main()
