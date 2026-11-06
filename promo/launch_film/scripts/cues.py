"""Synthesize each VO phrase and lay out a timeline -> work/cues.json + work/vo_track.wav"""
import sys, json
import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro
V = sys.argv[1]
k = Kokoro(f"{V}/dl_tts/kokoro-v1.0.onnx", f"{V}/dl_tts/voices-v1.0.bin")
FIX = ("dʒˈɛstʃɚɹə", "dʒɛstˈʊɹə")
SR = 24000
# scene: (start of first phrase in seconds, [(cue_id, text, gap_after)])
PLAN = [
 (1.3, [("s1", "What if you could control your computer, without touching it?", 0)]),
 (6.3, [("s2a", "Meet Gestura.", 0.35), ("s2b", "A hands-free desktop control system, powered by real-time computer vision.", 0)]),
 (12.9, [("s3a", "Move your index finger to control the cursor.", 0.45), ("s3b", "Pinch your fingers to click.", 0.45),
         ("s3c", "Move your hand to scroll.", 0.45), ("s3d", "Simple, intuitive gestures replace traditional mouse interactions.", 0)]),
 (24.2, [("s4a", "Head tracking adds another layer of control.", 0.35),
         ("s4b", "Turn your head to navigate between pages, and use simple movements to trigger actions.", 0)]),
 (33.0, [("s5", "And when you need to type, Gestura brings up a virtual keyboard that you can control entirely through gestures.", 0)]),
 (40.8, [("s6a", "One webcam.", 0.3), ("s6b", "Real-time tracking.", 0.3), ("s6c", "Complete hands-free interaction.", 0)]),
 (45.9, [("s7a", "Gestura.", 0.3), ("s7b", "Control your computer, without touching it.", 0)]),
]
total = 50.0
track = np.zeros(int(total * SR), np.float32)
cues = {}
for start, phrases in PLAN:
    t = start
    for cid, text, gap in phrases:
        ph = k.tokenizer.phonemize(text, "en-us").replace(*FIX)
        s, sr = k.create(ph, voice="af_heart", speed=1.0, is_phonemes=True)
        a = np.abs(s); idx = np.where(a > 0.01)[0]
        s = s[max(0, idx[0] - int(0.02 * sr)): idx[-1] + int(0.1 * sr)].astype(np.float32)
        i = int(t * SR)
        if i + len(s) > len(track):
            raise SystemExit(f"{cid} overruns the timeline ({t + len(s)/SR:.2f}s)")
        track[i:i + len(s)] += s
        cues[cid] = {"start": round(t, 3), "end": round(t + len(s) / SR, 3), "text": text}
        t += len(s) / SR + gap
for a, b in zip(list(cues.values()), list(cues.values())[1:]):
    assert a["end"] <= b["start"] + 1e-6, (a, b)
sf.write(f"{V}/work/vo_track.wav", track, SR)
json.dump(cues, open(f"{V}/work/cues.json", "w"), indent=1)
for cid, c in cues.items():
    print(f"{cid:4s} {c['start']:6.2f} -> {c['end']:6.2f}  {c['text'][:60]}")
