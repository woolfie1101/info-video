#!/usr/bin/env python3
"""3단계: 움직이는 그래픽 장면을 config의 데이터로 그려 mp4로 만든다.
사용: uv run --with playwright graphics.py <프로젝트 폴더> h|v|f
- 그래픽은 1000x800 '무대' 좌표로 그리고, 방향별 안전 영역(채널명·자막과 겹치지 않는 칸)에 맞춰 배치한다.
- 애니메이션은 CSS로 쓰고 프레임마다 시간을 고정해 찍는다. 등장 시점은 자막 번호(at)로 내레이션에 맞춘다.
장면 graphic 종류(references/graphics.md): bar, cards, quote, compare, line, donut, table, timeline, ranking, bignum, headline, steps, versus, photo
"""
import json, os, subprocess, sys
from pathlib import Path
from playwright.sync_api import sync_playwright
sys.path.insert(0, str(Path(__file__).resolve().parent))
from graphics_more import MORE, EXTRA_CSS
from templates_jh import JH, JH_CSS, COUNT_JS, DIM_CSS
from common import FONT_CSS, SANS, SERIF, launch, wait_fonts, paper, load_env

ROOT = Path(sys.argv[1]).resolve()
O = sys.argv[2] if len(sys.argv) > 2 else "h"
CANVAS = {"h": (1920, 1080), "v": (1080, 1920), "f": (1080, 1080)}[O]
SAFE = {"h": (60, 130, 1800, 785), "v": (20, 320, 1040, 880), "f": (20, 20, 1040, 850)}[O]
FPS = 30
CLIPS = ROOT / "clips"; CLIPS.mkdir(exist_ok=True)
HTML = ROOT / "html"; HTML.mkdir(exist_ok=True)
load_env(ROOT)
PAPER = paper()  # 픽사베이 종이 질감(캐시). 없으면 밝은 단색
cfg = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
durs = json.loads((ROOT / "durs.json").read_text())
tl = json.loads((ROOT / "timeline.json").read_text())

def at(si, idx):
    """자막 idx번째가 시작하는 시각(초)."""
    ss = [t["start"] for t in tl if t["scene"] == si]
    return ss[min(idx, len(ss) - 1)] if ss else 0

K = min(SAFE[2] / 1000, SAFE[3] / 800)
FLUID_W = min(SAFE[2] / K, 1400)  # 템플릿(JH)용 무대 폭: 가로 화면에선 더 넓게

def stage_css(sw=1000):
    x, y, w, h = SAFE
    pw, ph = sw * K, 800 * K
    return (f".stage{{position:absolute;left:{x + (w - pw) / 2:.1f}px;top:{y + (h - ph) / 2:.1f}px;width:{sw:.0f}px;height:800px;"
            f"transform:scale({K:.4f});transform-origin:0 0}}")

BASE = FONT_CSS + """*{margin:0;padding:0;box-sizing:border-box}
html,body{width:%dpx;height:%dpx;overflow:hidden;font-family:%s}
.paper{position:absolute;inset:0;background:#f3f3f1 %s center/cover}
.dark{position:absolute;inset:0;background:#050505;overflow:hidden}
.rays{position:absolute;left:50%%;top:45%%;width:3200px;height:3200px;margin:-1600px 0 0 -1600px;
      background:repeating-conic-gradient(from 0deg at 50%% 50%%,rgba(70,110,95,.30) 0deg 2deg,transparent 2deg 7deg);
      -webkit-mask:radial-gradient(circle at 50%% 50%%,#000 0,#000 6%%,transparent 34%%);animation:spin 12s linear both}
.glow{position:absolute;inset:0;background:radial-gradient(ellipse at 50%% 45%%,rgba(40,80,65,.55),transparent 60%%)}
.title{position:absolute;top:10px;width:100%%;text-align:center;font-size:44px;font-weight:800;color:#222}
.src{position:absolute;right:0;bottom:0;font-size:20px;color:#777}
@keyframes grow{from{transform:scaleY(0)}to{transform:scaleY(1)}}
@keyframes wipeUp{from{clip-path:inset(100%% 0 0 0);transform:translateY(24px)}to{clip-path:inset(0 0 0 0);transform:none}}
@keyframes pop{0%%{transform:scale(0);opacity:0}70%%{transform:scale(1.08);opacity:1}100%%{transform:scale(1);opacity:1}}
@keyframes fadeIn{from{opacity:0}to{opacity:1}}
@keyframes spin{from{transform:rotate(0)}to{transform:rotate(25deg)}}
@keyframes ch{from{opacity:0}to{opacity:1}}
""" % (CANVAS[0], CANVAS[1], SANS, f"url('file://{PAPER}')" if PAPER else "")

def head(g):
    t = f"<div class=title style='animation:fadeIn .3s .05s both'>{g['title']}</div>" if g.get("title") else ""
    s = f"<div class=src style='animation:fadeIn .3s .2s both'>출처 : {g['source']}</div>" if g.get("source") else ""
    return t, s

# ---------- bar: 막대가 아래에서 자라고, 수치 태그가 아래에서 닦이듯 등장 ----------
def bar(si, g):
    data = g["data"]; n = len(data); hi = set(g.get("highlight", []))
    vmax = g.get("max") or max(v for _, v in data) * 1.03
    suffix = g.get("suffix", "")
    base, top, left, right = 640, 150, 60, 970
    slot = (right - left) / n; bw = min(130, slot * .72)
    start = at(si, g.get("at", 0)); extra = {int(k): v for k, v in g.get("at_bar", {}).items()}
    bars = []
    for i, (lab, v) in enumerate(data):
        h = (base - top) * v / vmax; x = left + i * slot + (slot - bw) / 2
        t = at(si, extra[i]) if i in extra else start + i * 0.16
        col = "#c62828" if i in hi else g.get("color", "#0f2a5c")
        bars.append(f"""<div class=bar style="left:{x:.0f}px;width:{bw:.0f}px;height:{h:.0f}px;background:{col};animation:grow .45s {t:.2f}s both cubic-bezier(.2,.8,.2,1)"></div>
        <div class=tag style="left:{x + bw / 2 - 65:.0f}px;top:{base - h - 58:.0f}px;background:{col};--c:{col};animation:wipeUp .35s {t + .3:.2f}s both">{v:,}{suffix}</div>
        <div class=lab style="left:{x + bw / 2 - 80:.0f}px">{str(lab).replace(chr(10), '<br>')}</div>""")
    css = """.unit{position:absolute;left:30px;top:96px;font-size:22px;color:#555}
    .axis{position:absolute;left:40px;right:20px;top:640px;border-top:3px solid #333}
    .bar{position:absolute;bottom:160px;border-radius:5px 5px 0 0;transform-origin:bottom}
    .tag{position:absolute;width:130px;height:46px;line-height:46px;text-align:center;color:#fff;font-size:26px;font-weight:800;border-radius:8px;white-space:nowrap}
    .tag:after{content:'';position:absolute;left:55px;bottom:-10px;border:10px solid transparent;border-bottom:0;border-top-color:var(--c)}
    .lab{position:absolute;top:654px;width:160px;text-align:center;font-size:24px;font-weight:700;color:#333;line-height:1.15}"""
    t, s = head(g); unit = f"<div class=unit>({g['unit']})</div>" if g.get("unit") else ""
    return css, f"<div class=paper></div><div class=stage>{t}{unit}<div class=axis></div>{''.join(bars)}{s}</div>"

# ---------- cards: 아이콘 카드가 하나씩 튀어나옴 ----------
ICONS = {
    "phone": """<svg viewBox="0 0 120 120" width="150" height="150"><rect x="30" y="8" width="60" height="104" rx="12" fill="#fff" stroke="#111" stroke-width="7"/><rect x="48" y="16" width="24" height="6" rx="3" fill="#111"/><circle cx="60" cy="62" r="16" fill="#2557d6"/><circle cx="60" cy="62" r="7" fill="#fff"/></svg>""",
    "glasses": """<svg viewBox="0 0 160 120" width="200" height="150"><path d="M10 50 h140" stroke="#111" stroke-width="7"/><rect x="14" y="40" width="56" height="42" rx="14" fill="#2557d6" stroke="#111" stroke-width="7"/><rect x="90" y="40" width="56" height="42" rx="14" fill="#2557d6" stroke="#111" stroke-width="7"/><circle cx="118" cy="30" r="8" fill="#ff4d4d" stroke="#111" stroke-width="4"/></svg>""",
    "paper": """<svg viewBox="0 0 120 120" width="150" height="150"><path d="M28 8 h46 l20 20 v84 h-66z" fill="#fff" stroke="#111" stroke-width="7"/><path d="M40 50 h40 M40 66 h40 M40 82 h28" stroke="#2557d6" stroke-width="7" stroke-linecap="round"/></svg>""",
    "warning": """<svg viewBox="0 0 120 120" width="150" height="150"><path d="M60 10 L112 104 H8 Z" fill="#ffd21f" stroke="#111" stroke-width="7" stroke-linejoin="round"/><path d="M60 42 v32" stroke="#111" stroke-width="9" stroke-linecap="round"/><circle cx="60" cy="88" r="6" fill="#111"/></svg>""",
    "money": """<svg viewBox="0 0 140 120" width="175" height="150"><rect x="10" y="28" width="120" height="68" rx="10" fill="#7bd389" stroke="#111" stroke-width="7"/><circle cx="70" cy="62" r="18" fill="#fff" stroke="#111" stroke-width="6"/></svg>""",
    "clock": """<svg viewBox="0 0 120 120" width="150" height="150"><circle cx="60" cy="60" r="48" fill="#fff" stroke="#111" stroke-width="7"/><path d="M60 30 v32 l20 12" stroke="#2557d6" stroke-width="8" stroke-linecap="round" fill="none"/></svg>""",
    "person": """<svg viewBox="0 0 120 120" width="150" height="150"><circle cx="60" cy="38" r="22" fill="#2557d6" stroke="#111" stroke-width="7"/><path d="M18 112 c0-30 20-44 42-44 s42 14 42 44z" fill="#fff" stroke="#111" stroke-width="7"/></svg>""",
}
def cards(si, g):
    cs = g["cards"]; n = len(cs); gap = 40; w = (1000 - gap * (n - 1)) / n
    out = []
    for i, c in enumerate(cs):
        t = at(si, c.get("at", i + 1))
        tag = f"<span class=ai>{c['tag']}</span>" if c.get("tag") else ""
        out.append(f"""<div class=card style="left:{i * (w + gap):.0f}px;width:{w:.0f}px;animation:pop .45s {t:.2f}s both">
          <div class=num>{i + 1}</div>{ICONS.get(c.get('icon', 'warning'), '')}<p>{c['text']}</p>{tag}</div>""")
    fs = 40 if n <= 2 else 32
    css = f""".card{{position:absolute;top:130px;height:560px;border:6px solid #111;border-radius:40px;background:#fff;text-align:center;
          box-shadow:10px 10px 0 rgba(0,0,0,.08);padding-top:60px}}
    .num{{position:absolute;left:-20px;top:-26px;width:72px;height:72px;border-radius:50%;background:#ffe27a;border:5px solid #111;font-size:38px;font-weight:900;line-height:62px}}
    .card p{{margin-top:36px;font-size:{fs}px;font-weight:800;line-height:1.35;color:#111;word-break:keep-all;padding:0 14px}}
    .card .ai{{display:inline-block;margin-top:24px;padding:8px 26px;border-radius:30px;background:#2557d6;color:#fff;font-size:28px;font-weight:800}}"""
    t, s = head(g)
    return css, f"<div class=paper></div><div class=stage>{t}{''.join(out)}{s}</div>"

# ---------- quote: 어두운 배경 + 빛줄기, 명조체 글자가 타자 치듯 ----------
def quote(si, g):
    lines = g["lines"]; hl = g.get("highlight", [])
    total = sum(map(len, lines)); dt = g.get("type_seconds", 2.4) / total; k = 0; out = []
    for l in lines:
        mark = set()
        for p in hl:
            i = l.find(p)
            if i >= 0: mark |= set(range(i, i + len(p)))
        sp = []
        for ci, c in enumerate(l):
            col = "#ffe14d" if ci in mark else "#f2f2f2"
            sp.append(f"<span class=c style='color:{col};animation-delay:{.3 + k * dt:.3f}s'>{c}</span>"); k += 1
        out.append("".join(sp))
    top = max(60, 330 - len(lines) * 40)
    css = f""".q{{position:absolute;top:{top}px;width:100%;text-align:center;font-family:{SERIF};font-weight:800;font-size:50px;line-height:1.65}}
    .c{{opacity:0;animation:ch .05s both}}.src{{color:#888}}"""
    s = f"<div class=src>출처 : {g['source']}</div>" if g.get("source") else ""
    return css, f"<div class=dark><div class=rays></div><div class=glow></div></div><div class=stage><div class=q>{'<br>'.join(out)}</div>{s}</div>"

# ---------- compare: 두 숫자 카드, 숫자가 0부터 올라감 ----------
def compare(si, g):
    L, R = g["left"], g["right"]; a = g.get("at", [0, 1, 2])
    css = f"""@property --n{{syntax:'<integer>';inherits:false;initial-value:0}}
    @keyframes cL{{from{{--n:0}}to{{--n:{int(L['value'])}}}}}@keyframes cR{{from{{--n:0}}to{{--n:{int(R['value'])}}}}}
    .sub{{position:absolute;top:72px;width:100%;text-align:center;font-size:28px;color:#555}}
    .box{{position:absolute;top:170px;width:420px;height:470px;border-radius:36px;border:6px solid #111;background:#fff;text-align:center;box-shadow:10px 10px 0 rgba(0,0,0,.08)}}
    .box h3{{margin-top:50px;font-size:40px;font-weight:800;word-break:keep-all}}
    .n{{margin-top:60px;font-size:150px;font-weight:900;line-height:1;counter-reset:n var(--n)}}
    .n:before{{content:counter(n)}}.n small{{font-size:56px}}
    .arrow{{position:absolute;left:470px;top:370px;font-size:80px;font-weight:900;color:#c62828}}"""
    t, s = head(g); sub = f"<div class=sub style='animation:fadeIn .3s .2s both'>{g['subtitle']}</div>" if g.get("subtitle") else ""
    body = f"""<div class=paper></div><div class=stage>{t}{sub}
      <div class=box style="left:20px;animation:pop .45s {at(si, a[0]):.2f}s both"><h3>{L['label']}</h3>
        <div class=n style="color:#2557d6;animation:cL .9s {at(si, a[0]) + .2:.2f}s both ease-out"><small>{L.get('suffix', '')}</small></div></div>
      <div class=arrow style="animation:fadeIn .3s {at(si, a[1]):.2f}s both">→</div>
      <div class=box style="left:560px;animation:pop .45s {at(si, a[1]):.2f}s both"><h3>{R['label']}</h3>
        <div class=n style="color:#c62828;animation:cR .9s {at(si, a[2]):.2f}s both ease-out"><small>{R.get('suffix', '')}</small></div></div>{s}</div>"""
    return css, body

GRAPHICS = {"bar": bar, "cards": cards, "quote": quote, "compare": compare,
            **{k: (lambda f: lambda si, g: f(si, g, at))(f) for k, f in MORE.items()}}
# 한국 지식 설명 유튜브 스타일 템플릿(templates_jh.py): 겹치는 이름(table, line)은 이쪽이 기본
JH_NAMES = set(JH)

def render(page, name, css, body, dur, mode="paper", sw=1000):
    """mode overlay → 투명 배경 .mov(알파, 실사 위 합성), 그 외 → .mp4"""
    f = HTML / f"{name}_{O}.html"
    f.write_text(f"<!doctype html><meta charset=utf-8><style>{BASE}{EXTRA_CSS}{JH_CSS}{DIM_CSS}{stage_css(sw)}{css}</style>"
                 f"<body>{body}{COUNT_JS}</body>", encoding="utf-8")
    page.goto(f"file://{f}"); wait_fonts(page)
    page.evaluate("document.getAnimations().forEach(a=>a.pause())")
    alpha = mode == "overlay"
    out = CLIPS / f"{name}_{O}.{'mov' if alpha else 'mp4'}"
    other = CLIPS / f"{name}_{O}.{'mp4' if alpha else 'mov'}"
    if other.exists(): other.unlink()
    enc = (["-c:v", "qtrle", "-pix_fmt", "argb"] if alpha else ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18"])
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "image2pipe", "-framerate", str(FPS), "-i", "-", *enc, str(out)],
                          stdin=subprocess.PIPE)
    for i in range(int(dur * FPS) + 1):
        t = i / FPS
        page.evaluate(f"(()=>{{document.getAnimations().forEach(a=>a.currentTime={t * 1000});window.__tick&&window.__tick({t})}})()")
        ff.stdin.write(page.screenshot(type="png", omit_background=alpha))
    ff.stdin.close(); ff.wait(); print("✓", out.name, flush=True)

def has_stock(sc):
    return bool(sc.get("stock") or sc.get("pixabay_video") or sc.get("pixabay_image"))

if __name__ == "__main__":
    only = os.environ.get("ONLY", "")  # 예: ONLY=2,5 (장면 번호)
    with sync_playwright() as p:
        b = launch(p)
        pg = b.new_page(viewport={"width": CANVAS[0], "height": CANVAS[1]})
        for si, sc in enumerate(cfg["scenes"], 1):
            g = sc.get("graphic")
            if not g or (only and str(si) not in only.split(",")): continue
            if g.get("src"): g = {**g, "src": str((ROOT / g["src"]).resolve())}
            if g["type"] in JH_NAMES:
                ctx = {"sw": FLUID_W, "dur": durs[si - 1], "over": has_stock(sc)}
                css, body, mode = JH[g["type"]](si, g, at, ctx)
                if mode == "overlay" and not has_stock(sc):
                    print(f"  ! 장면 {si}: '{g['type']}'는 실사 위에 얹는 템플릿 — pixabay_video/pixabay_image 를 같이 적으세요", flush=True)
                render(pg, f"g{si}", css, body, durs[si - 1], mode, FLUID_W)
            else:
                css, body = GRAPHICS[g["type"]](si, g)
                render(pg, f"g{si}", css, body, durs[si - 1])
        b.close()
