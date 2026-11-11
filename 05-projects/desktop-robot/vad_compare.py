"""Replay known pauses to compare endpoint settings; no live recording."""
import json
from pathlib import Path
import numpy as np
from robot import Endpoint, RATE, ROOT, Speech, resample_audio
from acceleration import SileroDetector
from speed_probe import load_recording


def detect(samples, backend, silence):
    detector = SileroDetector(ROOT/".local/silero_vad.onnx") if backend == "silero" else None
    ep = Endpoint(silence)
    voiced_blocks = 0
    for end in range(320, len(samples)+1, 320):
        block = samples[end-320:end]
        voiced = detector.feed(block) if detector else np.sqrt(np.mean(block**2)) >= .004
        voiced_blocks = voiced_blocks+1 if voiced else 0
        if ep.first_voice is None:
            voiced = voiced_blocks >= 3
        state = ep.feed(voiced, end/RATE)
        if state != "listen":
            return {"state":state,"end_s":end/RATE,"first_s":ep.first_voice,"last_s":ep.last_voice}
    return {"state":"listen","end_s":len(samples)/RATE,"first_s":ep.first_voice,"last_s":ep.last_voice}


def main():
    speech = Speech(ROOT/".local",2,"zh","theresa",8,.9)
    def synth(text):
        x = np.concatenate([resample_audio(a.samples,a.sample_rate,RATE) for a in speech.synthesize(text)])
        # Remove TTS boundary silence so the inserted pause has a known duration.
        active = np.flatnonzero(np.abs(x)>.006)
        return x[max(0,active[0]-160):min(len(x),active[-1]+160)]
    a,b = synth("我今天打印了一个蓝色外壳"),synth("请问应该放在什么位置？")
    tests = {"human": (load_recording(ROOT/".local/human-mic-check-10s.wav"),None),
             "silence":(np.zeros(16*RATE,dtype="float32"),None)}
    for pause in [.3,.5]:
        x=np.concatenate([np.zeros(8000),a,np.zeros(int(pause*RATE)),b,np.zeros(2*RATE)]).astype("float32")
        tests[f"pause-{pause}"]=(x,(8000+len(a)+int(pause*RATE)+len(b))/RATE)
    rows=[]
    for backend in ["rms","silero"]:
        for silence in [.45,.55,.7]:
            for name,(samples,expected_end) in tests.items():
                row={"backend":backend,"silence":silence,"case":name,**detect(samples,backend,silence)}
                row["expected_end_s"]=expected_end
                row["truncated"]=None if expected_end is None else row["end_s"] < expected_end-.1
                print(json.dumps(row),flush=True);rows.append(row)
    (ROOT/".local/vad-comparison.json").write_text(json.dumps(rows,indent=2),encoding="utf8")


if __name__ == "__main__":
    main()
