#!/usr/bin/env python3
"""장면 배경(스톡 영상·움직이는 그래픽) + 화면 틀/자막 + 내레이션 → out_<h|v|f>.mp4
사용: assemble.py <프로젝트 폴더> h|v|f   (h=가로, v=세로 기본형, f=세로 쇼츠형: 위 제목·가운데 1080x1080 영상·아래 계정명)
스톡 영상 방향이 칸과 다르면 원본에서 칸 비율만큼 잘라 쓴다. scene에 "focus": 0~1(세로 위치)로 자를 위치 지정."""
import json, subprocess, sys
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve()
O = sys.argv[2] if len(sys.argv) > 2 else "h"
W, H = (1920, 1080) if O == "h" else (1080, 1920)
F = O == "f"
BW, BH = (1080, 1080) if F else (W, H)
TOPY = 440
FPS = 30
CLIPS = ROOT / "clips"; CLIPS.mkdir(exist_ok=True)
cfg = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
durs = json.loads((ROOT / "durs.json").read_text())
tl = json.loads((ROOT / "timeline.json").read_text())

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode: raise SystemExit(r.stderr[-2000:])

def size(f):
    w, h = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                           "-of", "csv=p=0", str(f)], capture_output=True, text=True).stdout.strip().split(",")[:2]
    return int(w), int(h)

def crop_filter(f, fy):
    w, h = size(f)
    if w / h > BW / BH: cw, ch = int(h * BW / BH) // 2 * 2, h
    else:               cw, ch = w, int(w * BH / BW) // 2 * 2
    return f"crop={cw}:{ch}:{int((w - cw) * .5)}:{int((h - ch) * fy)},scale={BW}:{BH}"

parts = []
for si, (sc, d) in enumerate(zip(cfg["scenes"], durs), 1):
    gmov = CLIPS / f"g{si}_{O}.mov"   # 투명 그래픽(실사 위 합성용)
    gmp4 = CLIPS / f"g{si}_{O}.mp4"   # 불투명 그래픽(종이 슬라이드 등)
    overlay_g = "graphic" in sc and gmov.exists()
    opaque_g = "graphic" in sc and not overlay_g
    # 스톡: "stock"(기본 원본, 영상 mp4 또는 사진 jpg), 세로용 원본을 따로 받았으면 "stock_v"
    bg = gmp4 if opaque_g else ROOT / (sc.get("stock_v") if O != "h" and sc.get("stock_v") else sc["stock"])
    still = bg.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")
    inp = (["-loop", "1", "-t", f"{d}", "-i", str(bg)] if still else ["-stream_loop", "-1", "-t", f"{d}", "-i", str(bg)])
    if opaque_g:
        v = "[0:v]fps=30,setsar=1"
    elif still:  # 픽사베이 사진: 칸 비율로 자른 뒤 천천히 확대(1.0→1.08)
        n = int(d * FPS) + 1
        v = (f"[0:v]{crop_filter(bg, sc.get('focus', .5))},scale={BW * 2}:{BH * 2},"
             f"zoompan=z='1+0.08*on/{n}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={n}:s={BW}x{BH}:fps={FPS},"
             f"eq=brightness=-0.04,vignette=PI/5,setsar=1")
    else:
        v = f"[0:v]{crop_filter(bg, sc.get('focus', .5))},fps=30,eq=brightness=-0.06,vignette=PI/5,setsar=1"
    nin = 1
    if overlay_g:  # 실사 위에 투명 그래픽을 얹는다
        inp += ["-t", f"{d}", "-i", str(gmov)]; nin = 2
        v += f"[s0];[1:v]fps=30,format=rgba[g0];[s0][g0]overlay=0:0:format=auto,format=yuv420p"
    v += f",pad={W}:{H}:0:{TOPY}:black[bg]" if F else "[bg]"
    chain, last = [v], "bg"
    ovs = [t for t in tl if t["scene"] == si]
    for k, o in enumerate(ovs, 1):
        inp += ["-i", str(ROOT / f"frames_{O}/o{si}_{o['idx']}.png")]
        t1 = o["start"] + o["dur"] if k < len(ovs) else d + 1
        chain.append(f"[{last}][{k + nin - 1}:v]overlay=0:0:enable='between(t,{o['start']:.3f},{t1:.3f})'[v{k}]")
        last = f"v{k}"
    out = CLIPS / f"c{si}_{O}.mp4"
    run(["ffmpeg", "-y", "-v", "error", *inp, "-filter_complex", ";".join(chain), "-map", f"[{last}]",
         "-t", f"{d}", "-r", str(FPS), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", str(out)])
    parts.append(out)

lst = CLIPS / f"v_{O}.txt"; lst.write_text("".join(f"file '{p}'\n" for p in parts))
# 내레이션은 prep.py가 만든 한 줄짜리 음성(틈 줄이고 배속)
run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-i", str(ROOT / "tts/narration.wav"),
     "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", str(ROOT / f"out_{O}.mp4")])
print(ROOT / f"out_{O}.mp4")
