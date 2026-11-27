#!/usr/bin/env python3
"""픽사베이 스톡 영상·사진 검색과 다운로드 (PIXABAY_API_KEY 필요, 무료).
검색(영상):  fetch_stock.py list  "exam students" landscape|portrait [프로젝트 폴더]
검색(사진):  fetch_stock.py ilist "exam students" landscape|portrait [프로젝트 폴더]
받기(영상):  fetch_stock.py get   <영상 id> <저장 경로.mp4>
받기(사진):  fetch_stock.py iget  <사진 id> <저장 경로.jpg>
설정대로 받기: fetch_stock.py sync <프로젝트 폴더>   (장면의 "pixabay_video"/"pixabay_image" id를 stock/ 에 받아 둠)
미리보기:    fetch_stock.py sheet <id,id,...> <저장 경로.jpg>   (영상 썸네일을 한 장으로 — 고를 때 눈으로 확인)
- 만들 영상 방향(가로/세로)에 맞는 것만 먼저 보여준다. 없으면 반대 방향을 보여주고, 합성 때 확대 없이 잘라 쓴다.
- AI 생성물(태그 "ai generated")과 애니메이션(type=animation)은 뺀다 — 실사만.
"""
import json, subprocess, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import load_env, pixabay_videos, pixabay_images, download

def real(h):
    t = h.get("tags", "").lower()
    return "ai generated" not in t and "ai-generated" not in t and h.get("type", "film") != "animation"

def best(h):
    vs = sorted([v for v in h["videos"].values() if v.get("url")], key=lambda v: v["width"] * v["height"], reverse=True)
    return next((v for v in vs if max(v["width"], v["height"]) <= 1920), vs[-1])

def want(orient, w, h):
    return w > h if orient == "landscape" else h > w

def main():
    cmd = sys.argv[1]
    if cmd in ("list", "ilist"):
        q, orient = sys.argv[2], sys.argv[3]
        load_env(sys.argv[4] if len(sys.argv) > 4 else None)
        if cmd == "list":
            hits = [h for h in pixabay_videos(q) if real(h)]
            fit = [h for h in hits if want(orient, best(h)["width"], best(h)["height"])]
            show = fit or hits
            for h in show[:15]:
                v = best(h); print(h["id"], f'{v["width"]}x{v["height"]}', f'{h["duration"]}s', h["tags"][:60])
        else:
            hits = [h for h in pixabay_images(q, orientation="horizontal" if orient == "landscape" else "vertical") if real(h)]
            fit = hits; show = hits
            for h in show[:15]:
                print(h["id"], f'{h["imageWidth"]}x{h["imageHeight"]}', h["tags"][:60])
        print(f"(방향 맞는 것 {len(fit)}개" + ("" if fit else " — 없어서 반대 방향을 보여줌, 잘라서 사용") + ")")
    elif cmd == "get":
        load_env(); h = pixabay_videos(vid=sys.argv[2])[0]; v = best(h)
        download(v["url"], sys.argv[3]); print(sys.argv[3], f'{v["width"]}x{v["height"]}')
    elif cmd == "iget":
        load_env(); h = pixabay_images(iid=sys.argv[2])[0]
        download(h.get("largeImageURL") or h["webformatURL"], sys.argv[3]); print(sys.argv[3], f'{h["imageWidth"]}x{h["imageHeight"]}')
    elif cmd == "sync":
        root = Path(sys.argv[2]).resolve(); load_env(root)
        cfg = json.loads((root / "config.json").read_text(encoding="utf-8")); (root / "stock").mkdir(exist_ok=True)
        for i, sc in enumerate(cfg["scenes"], 1):
            for key, ext, fn in (("pixabay_video", "mp4", "v"), ("pixabay_video_v", "mp4", "vv"), ("pixabay_image", "jpg", "i")):
                if not sc.get(key): continue
                rel = f"stock/s{i}{'_v' if key.endswith('_v') else ''}.{ext}"; out = root / rel
                if not out.exists():
                    if fn == "i":
                        h = pixabay_images(iid=sc[key])[0]; download(h.get("largeImageURL") or h["webformatURL"], out)
                    else:
                        download(best(pixabay_videos(vid=sc[key])[0])["url"], out)
                    print("받음", rel)
                sc["stock_v" if key.endswith("_v") else "stock"] = rel
        (root / "config.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    elif cmd == "sheet":
        load_env(); ids = sys.argv[2].split(","); tmp = Path(tempfile.mkdtemp()); ins = []
        for i in ids:
            h = pixabay_videos(vid=i)[0]; f = tmp / f"{i}.jpg"
            download(h["videos"]["medium"]["thumbnail"], f); ins += ["-i", str(f)]
        n = len(ids); cols = min(4, n)
        lay = "|".join(f"{(k % cols) * 480}_{(k // cols) * 270}" for k in range(n))
        fl = ";".join(f"[{k}]scale=480:270,drawtext=text='{ids[k]}':x=10:y=10:fontsize=28:fontcolor=white:box=1:boxcolor=black@0.6[s{k}]" for k in range(n))
        fl += ";" + "".join(f"[s{k}]" for k in range(n)) + (f"xstack=inputs={n}:layout={lay}" if n > 1 else "null")
        subprocess.run(["ffmpeg", "-y", "-v", "error", *ins, "-filter_complex", fl, sys.argv[3]], check=True); print(sys.argv[3])
    else:
        print(__doc__)

if __name__ == "__main__":
    main()
