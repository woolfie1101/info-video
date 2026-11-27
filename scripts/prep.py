#!/usr/bin/env python3
"""1단계: 내레이션 음성 + 장면 길이(durs.json) + 자막 타이밍(timeline.json).
사용: uv run --with elevenlabs python prep.py <프로젝트 폴더> [--say]
- 대본 전체를 '한 번에' 읽혀서(문단 경계가 끊기거나 겹치지 않게) 글자별 시간표로 장면을 나눈다.
- 문장 사이 쉬는 틈은 MAX_GAP 초로 줄이고, 전체를 config의 speed(기본 1.2배)로 빠르게(음높이 유지).
- 기본은 ElevenLabs(config voice.voice_id, 모델 eleven_v4). 키(ELEVENLABS_API_KEY)가 없거나 --say 면 맥 기본 음성(무료 초안).
- 키는 환경변수나 .env에서 읽는다(common.py). 키를 출력하지 말 것. 대본이 같으면 다시 만들지 않는다.
"""
import base64, hashlib, json, re, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from kor_num import normalize  # 7건 → 일곱 건
from common import load_env
import os, platform

ROOT = Path(sys.argv[1]).resolve()
load_env(ROOT)
USE_SAY = "--say" in sys.argv or not os.environ.get("ELEVENLABS_API_KEY")
if USE_SAY and platform.system() != "Darwin":
    raise SystemExit("ELEVENLABS_API_KEY 가 없습니다. https://elevenlabs.io 에서 키를 받아 .env 에 넣거나, "
                     "`npx -y @elevenlabs/cli@latest onboard init` 으로 로그인하세요. (맥에서는 키 없이 기본 음성으로 초안 가능)")
if USE_SAY and "--say" not in sys.argv:
    print("ELEVENLABS_API_KEY 없음 → 맥 기본 음성으로 만듭니다(초안).")
cfg = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
T = ROOT / "tts"; T.mkdir(exist_ok=True)
voice = cfg.get("voice", {})
SPEED = float(cfg.get("speed", 1.2))
MAX_GAP = float(cfg.get("max_gap", 0.12))   # 문장 사이 최대 쉼(초, 배속 전)
DEFAULT_VOICE = "Xb7hH8MSUJpSbSDYk0k2"  # 일레븐랩스 기본 목소리 Alice(교육 설명형)
lines = [normalize(s["line"]) for s in cfg["scenes"]]

def run(cmd): subprocess.run(cmd, check=True, capture_output=True)
def dur(f): return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)],
                                        capture_output=True, text=True).stdout)

raw, align = T / "raw.mp3", T / "align.json"
key = hashlib.md5(json.dumps([USE_SAY, voice, lines], ensure_ascii=False).encode()).hexdigest()[:12]
stamp = T / "raw.key"
if not (raw.exists() and stamp.exists() and stamp.read_text() == key):
    if USE_SAY:  # 맥 음성: 장면별로 만들어 이어 붙이고, 장면 경계 시간을 기록
        segs, bounds, t = [], [], 0.0
        for i, l in enumerate(lines):
            f = T / f"say{i}.aiff"; run(["say", "-v", "Yuna", "-r", "200", "-o", str(f), l]); segs.append(f)
            bounds.append([t, t + dur(f)]); t += dur(f)
        (T / "say.txt").write_text("".join(f"file '{f}'\n" for f in segs))
        run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(T / "say.txt"), "-c:a", "libmp3lame", str(raw)])
        json.dump({"scenes": bounds}, open(align, "w"))
    else:
        from elevenlabs import ElevenLabs, VoiceSettings
        r = ElevenLabs().text_to_speech.convert_with_timestamps(
            voice_id=voice.get("voice_id", DEFAULT_VOICE), text=" ".join(lines),
            model_id=voice.get("model_id", "eleven_v4"), language_code="ko", output_format="mp3_44100_128",
            voice_settings=VoiceSettings(stability=voice.get("stability", 0.4), similarity_boost=voice.get("similarity_boost", 0.9)))
        raw.write_bytes(base64.b64decode(r.audio_base_64))
        a = r.alignment
        json.dump({"chars": a.characters, "start": a.character_start_times_seconds, "end": a.character_end_times_seconds}, open(align, "w"))
    stamp.write_text(key)

A = json.load(open(align))
# 장면별 [말 시작, 말 끝] (원본 시간)
if "scenes" in A:
    spans = A["scenes"]
else:
    text = "".join(A["chars"]); spans = []; pos = 0
    for l in lines:
        i = text.find(l[:6], pos); i = pos if i < 0 else i
        j = i + len(l) - 1
        spans.append([A["start"][i], A["end"][min(j, len(A["end"]) - 1)]]); pos = j + 1

# 문장 사이 쉼을 MAX_GAP으로 줄인 오디오 조각을 이어 붙이고 배속
total = dur(raw); pieces = []; new_bounds = []; t = 0.0
for k, (s, e) in enumerate(spans):
    s = max(0.0, s - 0.03); e = min(total, e + 0.06)
    nxt = spans[k + 1][0] if k + 1 < len(spans) else total
    e2 = min(nxt, e + MAX_GAP) if k + 1 < len(spans) else min(total, e + 0.3)
    f = T / f"p{k}.wav"
    run(["ffmpeg", "-y", "-v", "error", "-i", str(raw), "-ss", f"{s:.3f}", "-to", f"{e2:.3f}", "-ar", "48000", "-ac", "2", str(f)])
    pieces.append(f); d = dur(f); new_bounds.append(d / SPEED); t += d
(T / "p.txt").write_text("".join(f"file '{f}'\n" for f in pieces))
run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(T / "p.txt"),
     "-af", f"atempo={SPEED}", "-ar", "48000", "-ac", "2", str(T / "narration.wav")])

durs, tl = new_bounds, []
for i, (sc, d) in enumerate(zip(cfg["scenes"], durs), 1):
    tot = sum(len(c) for c in sc["subs"]); t = 0.0
    for ci, c in enumerate(sc["subs"]):
        dd = d * len(c) / tot
        tl.append({"scene": i, "idx": ci, "start": round(t, 3), "dur": round(dd, 3)}); t += dd
(ROOT / "durs.json").write_text(json.dumps(durs))
(ROOT / "timeline.json").write_text(json.dumps(tl, ensure_ascii=False, indent=1))
print("총", round(sum(durs), 1), "초 /", [round(x, 1) for x in durs], f"/ {SPEED}배속")
