"""공통: API 키 읽기, 픽사베이, 글꼴, 브라우저.
키는 코드·설정 파일에 넣지 않는다. 아래 순서로 찾는다:
  1) 환경변수  2) 프로젝트 폴더의 .env  3) 지금 폴더의 .env  4) ~/.config/info-video/.env
필요한 키: PIXABAY_API_KEY (필수, 무료: https://pixabay.com/api/docs/ 로그인 후 키 확인)
          ELEVENLABS_API_KEY (선택, 없으면 맥 기본 음성으로 대체)
"""
import json, os, subprocess, urllib.parse
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
CACHE = Path.home() / ".cache/info-video"; CACHE.mkdir(parents=True, exist_ok=True)

def load_env(project=None):
    files = [Path(project) / ".env" if project else None, Path.cwd() / ".env", Path.home() / ".config/info-video/.env"]
    for f in files:
        if f and f.is_file():
            for line in f.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line: continue
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip().removeprefix("export ").strip(), v.strip().strip('"').strip("'"))

def need(name, how):
    v = os.environ.get(name)
    if not v:
        raise SystemExit(f"{name} 가 없습니다. {how}")
    return v

def pixabay_key():
    return need("PIXABAY_API_KEY", "https://pixabay.com/api/docs/ 에서 무료 키를 받아 .env 에 PIXABAY_API_KEY=... 로 넣어 주세요.")

def _get(url):
    r = subprocess.run(["curl", "-s", "-A", "info-video-skill", url], capture_output=True, text=True)
    return json.loads(r.stdout)

def pixabay_videos(q=None, vid=None, per_page=50):
    p = {"key": pixabay_key(), "per_page": per_page, "safesearch": "true"}
    if vid: p["id"] = vid
    else: p["q"] = q
    return _get("https://pixabay.com/api/videos/?" + urllib.parse.urlencode(p))["hits"]

def pixabay_images(q=None, iid=None, orientation="all", per_page=50):
    p = {"key": pixabay_key(), "per_page": per_page, "safesearch": "true", "image_type": "photo", "orientation": orientation}
    if iid: p = {"key": pixabay_key(), "id": iid}
    else: p["q"] = q
    return _get("https://pixabay.com/api/?" + urllib.parse.urlencode(p))["hits"]

def download(url, out):
    subprocess.run(["curl", "-sL", "-A", "info-video-skill", "-o", str(out), url], check=True)

PAPER_ID = 626781  # 픽사베이 '구겨진 흰 종이' 사진 — 그래프 배경

def paper():
    """그래프 배경 종이 질감. 첫 실행 때 픽사베이에서 받아 캐시에 둔다."""
    f = CACHE / "paper.jpg"
    if not f.exists():
        try:
            download(pixabay_images(iid=PAPER_ID)[0]["largeImageURL"], f)
        except Exception:
            return None
    return f

# 글꼴: 구글 폰트(어느 컴퓨터든 같은 모양). 본문 Noto Sans KR, 인용 Nanum Myeongjo
FONT_CSS = ("@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700;800;900"
            "&family=Nanum+Myeongjo:wght@400;700;800&family=Nanum+Pen+Script&family=Gaegu:wght@700"
            "&family=Black+Han+Sans&display=block');")
HAND = "'Nanum Pen Script','Gaegu',cursive"      # 손글씨(이름표·메모)
BUBBLE = "'Gaegu','Noto Sans KR',sans-serif"      # 말풍선
POSTER = "'Black Han Sans','Noto Sans KR',sans-serif"  # 키네틱 큰 글자
SANS = "'Noto Sans KR','Apple SD Gothic Neo','Malgun Gothic',sans-serif"
SERIF = "'Nanum Myeongjo','AppleMyungjo',serif"

def launch(p):
    """설치된 Chrome이 있으면 쓰고, 없으면 Playwright 크로미움(최초 1회: uv run --with playwright playwright install chromium)."""
    try:
        return p.chromium.launch(channel="chrome")
    except Exception:
        return p.chromium.launch()

def wait_fonts(page):
    page.evaluate("document.fonts.ready.then(()=>true)")
    page.evaluate("Promise.all([...document.fonts].map(f=>f.load().catch(()=>0)))")
    page.wait_for_timeout(300)
