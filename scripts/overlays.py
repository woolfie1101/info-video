#!/usr/bin/env python3
"""2단계: 고정 화면 틀(채널명·소주제)과 자막을 투명 PNG로 렌더.
사용: uv run --with playwright python overlays.py <프로젝트 폴더> h|v|f
h=가로, v=세로 기본형, f=세로 쇼츠형(위 검은 띠에 제목, 가운데 영상, 아래 계정명)
색은 config의 "theme"으로 바꿀 수 있다: {"accent": 자막 바 선, "label": 소주제 선, "title_accent": 쇼츠 제목 2줄}"""
import json, sys
from pathlib import Path
from playwright.sync_api import sync_playwright
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import FONT_CSS, SANS, launch, wait_fonts
from templates_jh import is_light

ROOT = Path(sys.argv[1]).resolve()
O = sys.argv[2] if len(sys.argv) > 2 else "h"
W, H = (1920, 1080) if O == "h" else (1080, 1920)
OUT = ROOT / f"frames_{O}"; OUT.mkdir(exist_ok=True)
CFG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
TH = {"accent": "#7a1f2b", "label": "#f5c400", "title_accent": "#ffe45c", **CFG.get("theme", {})}
TITLE = CFG.get("title", ["", ""]); ACCOUNT = CFG.get("account", ""); CHANNEL = CFG.get("channel", "")

COMMON = f"""{FONT_CSS}*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{W}px;height:{H}px;overflow:hidden;background:transparent;font-family:{SANS}}}
.logo{{position:absolute;font-weight:900;color:#fff;letter-spacing:-1px;
      text-shadow:0 2px 0 #000,2px 0 0 #000,-2px 0 0 #000,0 -2px 0 #000,0 4px 10px rgba(0,0,0,.4)}}
.sec{{position:absolute;padding:0 26px 0 22px;font-weight:700;color:#fff;background:rgba(40,40,40,.85);border-left:6px solid {TH['label']}}}
.sub{{position:absolute;left:50%;transform:translateX(-50%);background:rgba(20,20,20,.72);border-radius:10px;color:#fff;font-weight:800;text-align:center}}
.sub:before{{content:'';position:absolute;left:0;top:10px;bottom:10px;width:7px;background:{TH['accent']};border-radius:3px}}
/* 밝은 종이 슬라이드 위: 자막 바·이름표를 회색으로, 채널명은 은은한 양각 */
.light .sub{{background:rgba(110,110,110,.93)}}
.light .sec{{background:rgba(110,110,110,.93)}}
.light .logo{{color:#fff;text-shadow:0 1px 2px rgba(0,0,0,.5),0 0 1px rgba(0,0,0,.6)}}
.title{{position:absolute;left:0;right:0;top:170px;text-align:center;font-weight:900;font-size:96px;line-height:1.18;letter-spacing:-3px;color:#fff}}
.title b{{color:{TH['title_accent']}}}
.acc{{position:absolute;left:0;right:0;top:1700px;text-align:center;font-size:54px;font-weight:700;color:#8c8c8c;letter-spacing:1px}}
.osub{{position:absolute;left:40px;right:40px;bottom:440px;text-align:center;font-weight:900;font-size:58px;color:#fff;line-height:1.3;
      word-break:keep-all;text-wrap:balance;-webkit-text-stroke:10px #000;paint-order:stroke fill}}
"""
LAYOUT = {
    "h": """.head{position:absolute;left:66px;top:52px;display:flex;align-items:center;gap:22px}
.head .logo,.head .sec{position:static}.logo{font-size:46px}.sec{height:44px;line-height:44px;font-size:24px}
.sub{bottom:62px;min-width:1000px;max-width:1500px;padding:16px 60px;font-size:44px;white-space:nowrap}""",
    # 세로 기본형: 위쪽에 틀, 자막은 쇼츠·릴스 하단 버튼을 피해 화면 2/3 지점
    "v": """.head{position:absolute;left:60px;top:150px;display:flex;flex-direction:column;align-items:flex-start;gap:16px}
.head .logo,.head .sec{position:static}.logo{font-size:54px}.sec{height:50px;line-height:50px;font-size:28px}
.sub{bottom:520px;width:940px;padding:22px 40px;font-size:52px;line-height:1.35;word-break:keep-all;text-wrap:balance}""",
    "f": "",
}

def body(si, c):
    if O == "f":
        return f"<div class=title>{TITLE[0]}<br><b>{TITLE[1]}</b></div><div class=acc>{ACCOUNT}</div><div class=osub>{c}</div>"
    sec = CFG["scenes"][si - 1].get("section", "")
    sec_html = f"<div class=sec>{sec}</div>" if sec else ""
    return f"<div class=head><div class=logo>{CHANNEL}</div>{sec_html}</div><div class=sub>{c}</div>"

with sync_playwright() as p:
    b = launch(p); pg = b.new_page(viewport={"width": W, "height": H})
    for si, sc in enumerate(CFG["scenes"], 1):
        for ci, c in enumerate(sc["subs"]):
            cls = "light" if is_light(sc) else ""
            pg.set_content(f"<!doctype html><meta charset=utf-8><style>{COMMON}{LAYOUT[O]}</style><body class='{cls}'>{body(si, c)}</body>")
            wait_fonts(pg)
            pg.screenshot(path=str(OUT / f"o{si}_{ci}.png"), omit_background=True)
    b.close()
print("overlays", O, "done")
