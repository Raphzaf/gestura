# Gestura launch film (50 s, 4K / 24 fps)

Programmatic motion design: every frame is drawn with Qt (`QPainter`) at
3840×2160 from the scripts in `scripts/`; nothing is filmed or AI-generated.

* Hand tracking overlays use the same 21-landmark articulated hand model as
  Gestura's tests, so every pose shown is one the real recogniser classifies as
  that gesture. The face uses MediaPipe's canonical 468-vertex face mesh.
* Voice-over: Kokoro-82M (Apache-2.0) neural TTS, voice `af_heart`; "Gestura" is
  forced to the pronunciation *jes-TOO-ra*. Each phrase is a separate clip so
  animation beats are timed from `work/cues.json`.
* Music and sound effects are synthesised in `scripts/audio.py`, timed from the
  same event list as the animation (`film_scenes.events()`).
* `Gestura_Launch_Film_EN.srt`: English captions.

## Regenerate

Requires the project's virtual environment (PySide6, NumPy, OpenCV) and ffmpeg.
Run from `promo/launch_film/`.

1. Face mesh:

```bash
mkdir -p dl_face && curl -L -o dl_face/canonical_face_model.obj https://raw.githubusercontent.com/google-ai-edge/mediapipe/master/mediapipe/modules/face_geometry/data/canonical_face_model.obj
```

2. Voice-over (optional: `work/cues.json` is committed, but the audio is not).
   Install `kokoro-onnx` in a separate venv, download `kokoro-v1.0.onnx` and
   `voices-v1.0.bin` from the kokoro-onnx GitHub release into `dl_tts/`, then:

```bash
tts_env/bin/python scripts/cues.py "$PWD"
```

3. Music + effects, then the mix:

```bash
python scripts/audio.py
```

```bash
ffmpeg -i work/vo_track.wav -i work/bed.wav -i work/sfx.wav -filter_complex "[0:a]aresample=48000,pan=stereo|c0=c0|c1=c0,volume=1.6,asplit=2[vo][key];[1:a][key]sidechaincompress=threshold=0.03:ratio=6:attack=25:release=350[duck];[2:a]volume=0.9[fx];[vo][duck][fx]amix=inputs=3:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[out]" -map "[out]" -c:a pcm_s24le -t 50 work/mix.wav
```

4. Preview stills (1080p) or render a segment of frames (4K):

```bash
cd scripts && python render.py preview 3.0 16.3 30.9
```

```bash
cd scripts && FILM_SCALE=2 python render.py segment 0 1200 ../out/video.mp4
```

Render in four parallel segments of 300 frames for speed (about 2 minutes on 4
cores), concatenate with ffmpeg's concat demuxer and mux `work/mix.wav`.
