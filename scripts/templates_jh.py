"""한국 지식 설명 유튜브 스타일 템플릿 모음 (실제 채널 영상 프레임 분석 기반).
각 템플릿: fn(si, g, at, ctx) -> (css, body, mode)
  mode "paper"   : 구겨진 흰 종이 슬라이드(불투명). 내용이 블러+페이드로 들어오고 장면 내내 아주 느리게 확대
  mode "dark"    : 자체 어두운 배경(불투명)
  mode "overlay" : 투명 배경 — 장면의 실사 스톡(pixabay_video/pixabay_image) 위에 합성
ctx: {"sw": 무대 폭(무대 좌표), "dur": 장면 길이(초), "over": 장면에 스톡이 있는지}
무대 높이는 800. 무대는 자막·채널명과 겹치지 않는 안전 영역 안에 놓인다.
글 안의 **굵게** 는 강조색(밝은 배경: 빨강, 어두운 배경: 노랑)으로 칠해진다.
SVG 속성은 반드시 따옴표로 감쌀 것(따옴표 없이 '="3"/>'가 붙으면 요소가 안 닫혀 뒤 요소가 사라짐).
"""
import html, re
from common import SERIF, HAND, BUBBLE, POSTER

BLUE, LBLUE, RED, YEL, NAVY = "#2f6fd6", "#dce8f8", "#e03a3a", "#f0e040", "#1f4aa8"
OVERLAY_TYPES = {"darkcard", "tanbox", "number", "faded", "bubble", "headbar", "callout", "pin", "kinetic", "stamp", "vsnum"}
DARK_TYPES = {"glitch", "portrait"}

JH_CSS = """
@keyframes blurIn{from{opacity:0;filter:blur(12px)}to{opacity:1;filter:none}}
@keyframes kb{from{transform:scale(1)}to{transform:scale(1.04)}}
@keyframes tiltIn{from{opacity:0;filter:blur(8px);transform:perspective(1600px) rotateX(24deg) rotateY(-12deg) scale(.88)}
                  to{opacity:1;filter:none;transform:none}}
@keyframes growX{from{transform:scaleX(0)}to{transform:scaleX(1)}}
@keyframes growY{from{transform:scaleY(0)}to{transform:scaleY(1)}}
@keyframes upIn{from{opacity:0;filter:blur(6px);transform:translateY(50px)}to{opacity:1;filter:none;transform:none}}
@keyframes fadeIn2{from{opacity:0}to{opacity:1}}
@keyframes popO{0%{transform:scale(0);opacity:0}65%{transform:scale(1.1);opacity:1}100%{transform:scale(1);opacity:1}}
@keyframes bubbleIn{0%{transform:scaleX(.1) scaleY(.6);opacity:0}70%{transform:scaleX(1.08) scaleY(1.04);opacity:1}100%{transform:none;opacity:1}}
@keyframes drawL{to{stroke-dashoffset:0}}
@keyframes stampIn{0%{transform:scale(2.4) rotate(var(--r));opacity:0}60%{transform:scale(.94) rotate(var(--r));opacity:1}100%{transform:scale(1) rotate(var(--r));opacity:1}}
@keyframes kinIn{0%{transform:scale(3.2);opacity:0;filter:blur(10px)}55%{transform:scale(.93);opacity:1;filter:none}100%{transform:scale(1);opacity:1}}
@keyframes chIn{from{opacity:0}to{opacity:1}}
@keyframes mark{from{background-size:0% 100%}to{background-size:100% 100%}}
@keyframes scan{from{background-position:0 0}to{background-position:0 240px}}
@keyframes jitter{0%,100%{transform:translateX(0)}20%{transform:translateX(-14px)}40%{transform:translateX(10px)}60%{transform:translateX(-6px)}80%{transform:translateX(16px)}}
.c{opacity:0;animation:chIn .04s both}
.mk{background:linear-gradient(rgba(255,228,64,.75),rgba(255,228,64,.75)) no-repeat 0 85%/0% 45%}
.jt{position:absolute;left:0;top:10px;width:100%;text-align:center;font-size:46px;font-weight:500;color:#1b1b1b;letter-spacing:-1px}
.jsub{position:absolute;left:0;top:72px;width:100%;text-align:center;font-size:24px;color:#666}
.jsrc{position:absolute;right:0;bottom:0;font-size:20px;color:#666}
.jsrc.w{color:rgba(255,255,255,.75)}
"""

COUNT_JS = """<script>
window.__tick=function(t){document.querySelectorAll('[data-count]').forEach(function(e){
 var s=+e.dataset.start,d=+e.dataset.dur,a=+e.dataset.from,b=+e.dataset.to,dec=+e.dataset.dec;
 var p=Math.min(1,Math.max(0,(t-s)/d));p=1-Math.pow(1-p,3);var v=a+(b-a)*p;
 e.textContent=(e.dataset.sign&&v>0?'+':'')+v.toLocaleString('en-US',{minimumFractionDigits:dec,maximumFractionDigits:dec});});};
</script>"""

def esc(s): return html.escape(str(s), quote=False)

def rich(text, color):
    """**강조** → 색, 줄바꿈 \\n → <br>. HTML 태그(<br>)는 그대로 둔다."""
    t = str(text).replace("\n", "<br>")
    return re.sub(r"\*\*(.+?)\*\*", lambda m: f"<b style='color:{color}'>{m.group(1)}</b>", t)

def count(value, start, dur=.8, dec=None, frm=0, sign=False):
    v = float(value); d = dec if dec is not None else (len(str(value).split(".")[1]) if "." in str(value) else 0)
    shown = f"{v:,.{d}f}"
    return (f"<span data-count data-start='{start:.2f}' data-dur='{dur}' data-from='{frm}' data-to='{v}' data-dec='{d}'"
            f"{' data-sign=1' if sign else ''}>{shown}</span>")

def typed(lines, t0, seconds, base, hi):
    """한 글자씩 타자. lines 안의 **강조**는 hi 색."""
    out, k = [], 0
    plain = [re.sub(r"\*\*", "", l) for l in lines]; total = max(1, sum(map(len, plain))); dt = seconds / total
    for l in lines:
        sp, on = [], False
        for part in re.split(r"(\*\*)", l):
            if part == "**": on = not on; continue
            for ch in part:
                sp.append(f"<span class=c style='color:{hi if on else base};animation-delay:{t0 + k * dt:.3f}s'>{esc(ch)}</span>"); k += 1
        out.append("".join(sp))
    return "<br>".join(out)

def head(g, t, white=False):
    ti = f"<div class=jt style='{'color:#fff;' if white else ''}'>{esc(g['title'])}</div>" if g.get("title") else ""
    su = f"<div class=jsub>{esc(g['subtitle'])}</div>" if g.get("subtitle") else ""
    sr = f"<div class='jsrc{' w' if white else ''}'>출처 : {esc(g['source'])}</div>" if g.get("source") else ""
    return ti + su, sr

def paper_wrap(inner, src, ctx, t0):
    return (f"<div class=paper style='animation:kb {ctx['dur']:.2f}s linear both'></div><div class=stage>"
            f"<div style='position:absolute;inset:0;animation:kb {ctx['dur']:.2f}s linear both'>"
            f"<div style='position:absolute;inset:0;animation:blurIn .35s {t0:.2f}s both'>{inner}</div>{src}</div></div>")

def stamp_html(g, at, si):
    s = g.get("stamp")
    if not s: return ""
    t = at(si, s.get("at", 1)); x = s.get("x", .5); y = s.get("y", .45)
    return (f"<div class=stp style='left:{x * 100}%;top:{y * 100}%;--r:{s.get('rotate', -4)}deg;"
            f"animation:stampIn .25s {t:.2f}s both cubic-bezier(.2,.8,.2,1)'>{esc(s['text'])}</div>")

STAMP_CSS = """.stp{position:absolute;padding:14px 36px;border:7px solid #c8202a;border-radius:10px;
 background:rgba(250,236,200,.92);color:#c8202a;font-size:76px;font-weight:900;white-space:nowrap;box-shadow:0 6px 18px rgba(0,0,0,.25);
 translate:-50% -50%}"""

# ---------------------------------------------------------------- 1 흰 표
def table(si, g, at, ctx):
    t0 = at(si, g.get("at", 0)); cols = g["columns"]; rows = g["rows"]
    w = g.get("widths") or [2] + [1] * (len(cols) - 1); tw = sum(w)
    grid = " ".join(f"{x / tw * 100:.2f}%" for x in w)
    hc = g.get("highlight_col"); align = g.get("align") or ["left"] + ["center"] * (len(cols) - 1)
    width = min(ctx["sw"] - 40, g.get("width", 1100 if len(cols) <= 3 else 1250))
    def cell(c, j, hdr=False):
        bg = f"background:{LBLUE};" if (hc is not None and j == hc and not hdr) else ""
        return f"<div style='{bg}text-align:{align[j]}'>{rich(esc(c) if '<' not in str(c) else c, RED)}</div>"
    head_row = "<div class='jr hdr'>" + "".join(cell(c, j, True) for j, c in enumerate(cols)) + "</div>"
    body_rows = "".join(f"<div class='jr{' alt' if i % 2 else ''}'>" + "".join(cell(c, j) for j, c in enumerate(r)) + "</div>"
                        for i, r in enumerate(rows))
    rh = min(84, 560 / max(1, len(rows) + 1))
    # 형광펜/동그라미 표시
    marks = ""
    for m in g.get("marks", []):
        t = at(si, m.get("at", 1)); r, c = m["row"], m["col"]
        x = sum(w[:c]) / tw * width; cw = w[c] / tw * width; y = rh * (r + 1)
        if m.get("kind", "marker") == "circle":
            marks += (f"<svg class=jm style='left:{x - 14:.0f}px;top:{y - 10:.0f}px' width='{cw + 28:.0f}' height='{rh + 20:.0f}'>"
                      f"<ellipse cx='{(cw + 28) / 2:.0f}' cy='{(rh + 20) / 2:.0f}' rx='{cw / 2 + 8:.0f}' ry='{rh / 2 + 4:.0f}' fill='none' stroke='{RED}' stroke-width='5'"
                      f" style='stroke-dasharray:900;stroke-dashoffset:900;animation:drawL .5s {t:.2f}s both'/></svg>")
        else:
            marks += (f"<div class=jm style='left:{x + 8:.0f}px;top:{y + rh * .55:.0f}px;width:{cw - 16:.0f}px;height:{rh * .32:.0f}px;"
                      f"background:rgba(255,228,64,.7);transform-origin:left;animation:growX .4s {t:.2f}s both'></div>")
    css = f""".jtb{{position:absolute;left:50%;top:{110 if g.get('title') else 40}px;width:{width}px;margin-left:-{width / 2}px;border-radius:6px;overflow:visible;
       box-shadow:0 4px 18px rgba(0,0,0,.10);animation:tiltIn .45s {t0:.2f}s both cubic-bezier(.2,.8,.2,1)}}
    .jr{{display:grid;grid-template-columns:{grid};height:{rh:.0f}px;align-items:center;background:#fff;font-size:{min(34, rh * .44):.0f}px;color:#222}}
    .jr.alt{{background:#f5f6f8}}
    .jr div{{padding:0 22px;height:100%;display:flex;align-items:center;justify-content:center;font-weight:500;word-break:keep-all;line-height:1.2}}
    .jr div[style*='left']{{justify-content:flex-start}}
    .jr div:last-child{{font-weight:800}}
    .jr.hdr{{background:{NAVY};color:#fff;height:{rh:.0f}px;border-radius:6px 6px 0 0;font-weight:700}}
    .jr.hdr div{{font-weight:700}}
    .jm{{position:absolute;mix-blend-mode:multiply}}"""
    ti, sr = head(g, t0)
    inner = f"{ti}<div class=jtb>{head_row}{body_rows}{marks}</div>"
    return css, paper_wrap(inner, sr, ctx, t0), "paper"

# ---------------------------------------------------------------- 2 가로 막대
def hbar(si, g, at, ctx):
    t0 = at(si, g.get("at", 0)); it = g["items"]; n = len(it); vmax = g.get("max") or max(v for _, v in it)
    suf = g.get("suffix", ""); top = 150 if g.get("title") else 80; rowh = min(120, (720 - top) / n)
    W = min(ctx["sw"], 1250); x0 = 300; bw = W - x0 - 190
    rows = []
    for i, (lab, v) in enumerate(it):
        y = top + i * rowh; first = i == g.get("highlight", 0)
        rows.append(f"""<div class=hl style='top:{y:.0f}px'>{esc(lab)}</div>
        <div class=ht style='top:{y + 6:.0f}px;left:{x0}px;width:{bw}px'></div>
        <div class=hb style='top:{y + 6:.0f}px;left:{x0}px;width:{bw * v / vmax:.0f}px;animation:growX .5s {t0 + .25:.2f}s both cubic-bezier(.2,.8,.2,1)'></div>
        <div class=hv style='top:{y:.0f}px;left:{x0 + bw + 20}px;color:{BLUE if first else '#222'}'>{count(v, t0 + .25, .5)}{suf}</div>""")
    css = f""".hwrap{{position:absolute;left:50%;width:{W}px;margin-left:-{W / 2}px;top:0;bottom:0}}
    .hl{{position:absolute;left:0;width:{x0 - 20}px;height:64px;line-height:64px;font-size:36px;color:#333;font-weight:500;white-space:nowrap}}
    .ht,.hb{{position:absolute;height:52px}}.ht{{background:#e3e6eb}}.hb{{background:{BLUE};transform-origin:left}}
    .hv{{position:absolute;height:64px;line-height:64px;font-size:40px;font-weight:800;white-space:nowrap}}"""
    ti, sr = head(g, t0)
    return css, paper_wrap(f"{ti}<div class=hwrap>{''.join(rows)}</div>", sr, ctx, t0), "paper"

# ---------------------------------------------------------------- 3 선 그래프
def line(si, g, at, ctx):
    t0 = at(si, g.get("at", 0)); data = g["data"]; n = len(data); vals = [v for _, v in data]
    lo = g.get("min", 0); hi = g.get("max") or max(vals) * 1.15
    W = min(ctx["sw"], 1150); L, R, T, B = 90, W - 40, 150 if g.get("title") else 70, 640
    X = lambda i: L + (R - L) * i / max(1, n - 1); Y = lambda v: B - (B - T) * (v - lo) / (hi - lo)
    pts = [(X(i), Y(v)) for i, v in enumerate(vals)]
    fc = g.get("forecast_from")  # 이 인덱스부터 점선
    solid = pts if fc is None else pts[:fc + 1]; dash = [] if fc is None else pts[fc:]
    P = lambda ps: " ".join(f"{x:.1f},{y:.1f}" for x, y in ps)
    seg = lambda ps: sum(((ps[i + 1][0] - ps[i][0]) ** 2 + (ps[i + 1][1] - ps[i][1]) ** 2) ** .5 for i in range(len(ps) - 1)) + 1
    dl = .9; ls = seg(solid); ticks = g.get("ticks", 5)
    grid = "".join(f"<line x1='{L}' x2='{R}' y1='{Y(lo + (hi - lo) * k / ticks):.0f}' y2='{Y(lo + (hi - lo) * k / ticks):.0f}' stroke='#cfd3d8' stroke-width='1.5' stroke-dasharray='4 6'/>"
                   f"<text x='{L - 14}' y='{Y(lo + (hi - lo) * k / ticks) + 8:.0f}' text-anchor='end' font-size='22' fill='#555'>{round(lo + (hi - lo) * k / ticks):,}</text>"
                   for k in range(ticks + 1))
    step = max(1, n // 9)
    xl = "".join(f"<text x='{X(i):.0f}' y='{B + 36}' text-anchor='middle' font-size='22' fill='#444'>{esc(lab)}</text>"
                 for i, (lab, _) in enumerate(data) if i % step == 0 or i == n - 1)
    show = g.get("labels") or sorted({0, n - 1, vals.index(max(vals))})
    dots = ""
    for i in show:
        x, y = pts[i]; t = t0 + .35 + dl * i / max(1, n - 1)
        dots += (f"<circle cx='{x:.0f}' cy='{y:.0f}' r='9' fill='#fff' stroke='#444' stroke-width='3' style='animation:fadeIn2 .2s {t:.2f}s both'/>"
                 f"<text x='{x:.0f}' y='{y - 22:.0f}' text-anchor='middle' font-size='28' font-weight='800' fill='#222' style='animation:fadeIn2 .2s {t:.2f}s both'>{vals[i]:,}{esc(g.get('suffix', ''))}</text>")
    boxes = ""
    for bx in g.get("boxes", []):
        t = at(si, bx.get("at", 1)); c = RED if bx.get("color", "red") == "red" else BLUE
        x1, x2 = X(bx["from"]) - 24, X(bx["to"]) + 24
        boxes += (f"<rect x='{x1:.0f}' y='{T - 10}' width='{x2 - x1:.0f}' height='{B - T + 10}' fill='{c}' fill-opacity='.07' stroke='{c}' stroke-width='4' rx='8'"
                  f" style='animation:fadeIn2 .3s {t:.2f}s both'/>"
                  + (f"<text x='{(x1 + x2) / 2:.0f}' y='{T - 20}' text-anchor='middle' font-size='26' font-weight='800' fill='{c}' style='animation:fadeIn2 .3s {t:.2f}s both'>{esc(bx['label'])}</text>" if bx.get("label") else ""))
    area = f"{L},{B} {P(pts)} {R},{B}"
    svg = f"""<svg class=lsvg width='{W}' height='800'><defs><linearGradient id='ga{si}' x1='0' y1='0' x2='0' y2='1'>
      <stop offset='0' stop-color='#9aa0a8' stop-opacity='.45'/><stop offset='1' stop-color='#9aa0a8' stop-opacity='.03'/></linearGradient></defs>
      {grid}<line x1='{L}' x2='{R}' y1='{B}' y2='{B}' stroke='#333' stroke-width='2'/>{xl}
      <polygon points='{area}' fill='url(#ga{si})' style='animation:fadeIn2 .5s {t0 + .35 + dl:.2f}s both'/>
      <polyline points='{P(solid)}' fill='none' stroke='#4a4f57' stroke-width='5' stroke-linejoin='round'
        style='stroke-dasharray:{ls:.0f};stroke-dashoffset:{ls:.0f};animation:drawL {dl}s {t0 + .35:.2f}s both linear'/>
      {f"<polyline points='{P(dash)}' fill='none' stroke='#4a4f57' stroke-width='4' stroke-dasharray='3 9' stroke-linecap='round' style='animation:fadeIn2 .3s {t0 + .35 + dl:.2f}s both'/>" if dash else ""}
      {boxes}{dots}</svg>"""
    unit = f"<div style='position:absolute;left:{20}px;top:{T - 50}px;font-size:22px;color:#555'>({esc(g['unit'])})</div>" if g.get("unit") else ""
    css = f".lwrap{{position:absolute;left:50%;width:{W}px;margin-left:-{W / 2}px;top:0;bottom:0}}.lsvg{{position:absolute;left:0;top:0;overflow:visible}}"
    ti, sr = head(g, t0)
    return css, paper_wrap(f"{ti}<div class=lwrap>{unit}{svg}</div>", sr, ctx, t0), "paper"

# ---------------------------------------------------------------- 4 세로 막대 (실사 위면 17 다크 오버레이 차트)
def vbar(si, g, at, ctx):
    t0 = at(si, g.get("at", 0)); data = g["data"]; n = len(data); over = ctx["over"]
    vmax = g.get("max") or max(v for _, v in data) * 1.12; suf = g.get("suffix", "")
    hi = set(g.get("highlight", [n - 1])); W = min(ctx["sw"], 160 * n + 200)
    T, B = (170 if g.get("title") else 90), (560 if g.get("caption") else 640)
    slot = (W - 40) / n; bw = min(140, slot * .62); out = []
    at_bar = {int(k): v for k, v in g.get("at_bar", {}).items()}
    for i, (lab, v) in enumerate(data):
        h = (B - T) * v / vmax; x = 20 + i * slot + (slot - bw) / 2
        t = at(si, at_bar[i]) if i in at_bar else t0 + .3 + i * .08
        col = (BLUE if over else NAVY) if i in hi else ("#c9ccd2" if over else "#8b919b")
        vc = ("#fff" if over else (NAVY if i in hi else "#333"))
        out.append(f"""<div class=vb style='left:{x:.0f}px;width:{bw:.0f}px;height:{h:.0f}px;top:{B - h:.0f}px;background:{col};animation:growY .5s {t:.2f}s both cubic-bezier(.2,.8,.2,1)'></div>
        <div class=vv style='left:{x + bw / 2 - 110:.0f}px;top:{B - h - 52:.0f}px;color:{vc};font-weight:{900 if i in hi else 600};font-size:{34 if i in hi else 28}px;animation:fadeIn2 .25s {t + .35:.2f}s both'>{count(v, t + .2, .5)}{esc(suf)}</div>
        <div class=vx style='left:{x + bw / 2 - 110:.0f}px;top:{B + 12}px;{'color:#fff;' if over else ''}'>{esc(lab)}</div>""")
    cap = (f"<div class=vcap style='top:{B + 70}px;{'color:#fff;' if over else ''}animation:fadeIn2 .3s {at(si, g.get('caption_at', 1)):.2f}s both'>"
           f"{rich(esc(g['caption']), YEL if over else '#b51f24')}</div>") if g.get("caption") else ""
    css = f""".vwrap{{position:absolute;left:50%;width:{W}px;margin-left:-{W / 2}px;top:0;bottom:0}}
    .vb{{position:absolute;transform-origin:bottom}}
    .vv,.vx{{position:absolute;width:220px;text-align:center;white-space:nowrap}}.vx{{font-size:26px;color:#333;font-weight:500}}
    .vbase{{position:absolute;left:0;right:0;top:{B}px;border-top:2px solid {'rgba(255,255,255,.6)' if over else '#444'}}}
    .vcap{{position:absolute;left:0;right:0;text-align:center;font-family:{SERIF};font-size:32px;color:#222}}"""
    ti, sr = head(g, t0, white=over)
    inner = f"{ti}<div class=vwrap><div class=vbase></div>{''.join(out)}{cap}</div>"
    if over:
        return css, f"<div class=dim style='animation:fadeIn2 .3s {t0:.2f}s both'></div><div class=stage><div style='position:absolute;inset:0;animation:blurIn .35s {t0:.2f}s both'>{inner}</div>{sr}</div>", "overlay"
    return css, paper_wrap(inner, sr, ctx, t0), "paper"

# ---------------------------------------------------------------- 5 다크 내레이션 카드 (실사 위)
def darkcard(si, g, at, ctx):
    t0 = at(si, g.get("at", 0)); lines = g["lines"]
    txt = typed(lines, t0 + .2, g.get("type_seconds", 2.5), "#f4f4f4", g.get("color", YEL))
    css = f""".dk{{position:absolute;left:0;right:0;top:50%;transform:translateY(-50%);text-align:center;font-family:{SERIF};font-weight:700;
       font-size:{g.get('size', 44)}px;line-height:1.55;text-shadow:0 2px 6px rgba(0,0,0,.6)}}"""
    sr = f"<div class='jsrc w'>출처 : {esc(g['source'])}</div>" if g.get("source") else ""
    return css, (f"<div class=dim style='background:rgba(0,0,0,.66);animation:fadeIn2 .3s {t0:.2f}s both'></div>"
                 f"<div class=stage><div class=dk>{txt}</div>{sr}</div>"), "overlay"

# ---------------------------------------------------------------- 6 황갈색 인용 박스 (실사 위)
def tanbox(si, g, at, ctx):
    t0 = at(si, g.get("at", 0)); W = min(ctx["sw"] - 40, g.get("width", 1150))
    txt = typed(g["lines"], t0 + .15, g.get("type_seconds", 1.4), "#1d1d1d", "#b3141c")
    y = g.get("y", .62)
    css = f""".tb2{{position:absolute;left:50%;width:{W}px;margin-left:-{W / 2}px;top:{y * 800:.0f}px;transform:translateY(-50%);
       background:#e9dcae;border:3px solid #7a5a2a;padding:22px 30px;text-align:center;font-family:{SERIF};font-weight:700;font-size:38px;line-height:1.5;
       box-shadow:0 8px 24px rgba(0,0,0,.35);animation:fadeIn2 .15s {t0:.2f}s both}}"""
    sr = f"<div class='jsrc w'>출처 : {esc(g['source'])}</div>" if g.get("source") else ""
    return css, f"<div class=stage><div class=tb2>{txt}</div>{sr}</div>", "overlay"

# ---------------------------------------------------------------- 7 수치 카드
def statcards(si, g, at, ctx):
    t0 = at(si, g.get("at", 0)); cs = g["cards"]; n = len(cs); W = min(ctx["sw"] - 40, 420 * n); gap = 22; cw = (W - gap * (n - 1)) / n
    out = []
    for i, c in enumerate(cs):
        t = at(si, c["at"]) if "at" in c else t0
        (l1, v1), (l2, v2) = c["before"], c["after"]
        out.append(f"""<div class=sc2 style='left:{i * (cw + gap):.0f}px;width:{cw:.0f}px;animation:upIn .45s {t:.2f}s both cubic-bezier(.2,.8,.2,1)'>
          <div class=sch>{esc(c['title'])}</div>
          <div class=scb><div><small>{esc(l1)}</small><b>{esc(v1)}</b></div><div><small>{esc(l2)}</small><b style='color:{BLUE}'>{esc(v2)}</b></div></div>
          <div class=scf><span>{esc(c.get('chip', '변화'))}</span><b>{rich(esc(c['change']), RED)}</b></div></div>""")
    css = f""".scw{{position:absolute;left:50%;width:{W}px;margin-left:-{W / 2}px;top:{200 if g.get('title') else 140}px}}
    .sc2{{position:absolute;top:0;background:#fff;border-radius:14px;overflow:hidden;box-shadow:0 4px 16px rgba(0,0,0,.1)}}
    .sch{{background:{NAVY};color:#fff;text-align:center;font-size:36px;font-weight:700;height:78px;line-height:78px}}
    .scb{{display:flex;padding:26px 6px}}.scb div{{flex:1;text-align:center;border-right:2px solid #e2e4e8}}.scb div:last-child{{border:0}}
    .scb small{{display:block;font-size:26px;color:#444}}.scb b{{display:block;margin-top:10px;font-size:46px;font-weight:900;color:#1d1d1d;letter-spacing:-1px}}
    .scf{{background:{LBLUE};height:96px;display:flex;align-items:center;justify-content:center;gap:16px}}
    .scf span{{background:{NAVY};color:#fff;font-size:20px;font-weight:700;padding:5px 16px;border-radius:8px}}.scf b{{font-size:40px;font-weight:900;color:{NAVY}}}"""
    ti, sr = head(g, t0)
    return css, paper_wrap(f"{ti}<div class=scw>{''.join(out)}</div>", sr, ctx, t0), "paper"

# ---------------------------------------------------------------- 8 큰 숫자 (실사 위)
def number(si, g, at, ctx):
    t0 = at(si, g.get("at", 0)); col = g.get("color", "#a9cdf0")
    lab = f"<div class=nl style='animation:fadeIn2 .3s {t0:.2f}s both'>{esc(g['label'])}</div>" if g.get("label") else ""
    sub = f"<div class=ns style='animation:fadeIn2 .3s {t0 + .7:.2f}s both'>{esc(g['sub'])}</div>" if g.get("sub") else ""
    css = f""".nwrap{{position:absolute;left:0;right:0;top:{g.get('y', .42) * 800:.0f}px;transform:translateY(-50%);text-align:center}}
    .nl{{display:inline-block;background:#fff;border:3px solid #333;border-radius:24px;padding:4px 22px;font-size:30px;font-weight:700;color:#222;margin-bottom:10px}}
    .nn{{font-size:{g.get('size', 170)}px;font-weight:900;color:{col};letter-spacing:-4px;line-height:1.05;
        text-shadow:0 3px 0 #345,0 6px 0 #234,0 10px 24px rgba(0,0,0,.55);-webkit-text-stroke:3px #2b3f57;animation:blurIn .3s {t0:.2f}s both}}
    .nn small{{font-size:.5em;letter-spacing:0;margin-left:10px}}
    .ns{{font-size:28px;color:#fff;font-weight:700;text-shadow:0 2px 6px rgba(0,0,0,.8)}}"""
    num = count(g["value"], t0 + .1, g.get("count_seconds", .8), frm=g.get("from", 0))
    sr = f"<div class='jsrc w'>출처 : {esc(g['source'])}</div>" if g.get("source") else ""
    return css, (f"<div class=dim style='background:rgba(0,0,0,.35);animation:fadeIn2 .3s {t0:.2f}s both'></div><div class=stage><div class=nwrap>{lab}"
                 f"<div class=nn>{esc(g.get('prefix', ''))}{num}<small>{esc(g.get('suffix', ''))}</small></div>{sub}</div>{sr}</div>"), "overlay"

# ---------------------------------------------------------------- 9 흐린 사진 + 텍스트 (실사 위)
def faded(si, g, at, ctx):
    t0 = at(si, g.get("at", 0))
    txt = typed(g["lines"], t0 + .25, g.get("type_seconds", 2.4), "#1b1b1b", "#b3141c")
    css = f""".fd{{position:absolute;left:0;right:0;top:50%;transform:translateY(-50%);text-align:center;font-family:{SERIF};font-weight:700;font-size:{g.get('size', 40)}px;line-height:1.55}}"""
    sr = f"<div class=jsrc>출처 : {esc(g['source'])}</div>" if g.get("source") else ""
    return css, (f"<div class=dim style='background:rgba(255,255,255,.72);animation:fadeIn2 .35s {t0:.2f}s both'></div>"
                 f"<div class=stage><div class=fd>{txt}</div>{sr}</div>"), "overlay"

# ---------------------------------------------------------------- 10 말풍선 (실사 위)
def bubble(si, g, at, ctx):
    out = []
    for i, b in enumerate(g.get("bubbles", [g])):
        t = at(si, b.get("at", i)); x, y = b.get("x", .5) * ctx["sw"], b.get("y", .45) * 800; tail = b.get("tail", "right")
        origin = {"right": "right bottom", "left": "left bottom", "down": "center bottom"}[tail]
        tx = {"right": "78%", "left": "12%", "down": "45%"}[tail]
        out.append(f"""<div class=bb style='left:{x:.0f}px;top:{y:.0f}px;transform-origin:{origin};animation:bubbleIn .2s {t:.2f}s both'>{esc(b['text'])}
          <svg class=bt style='left:{tx}' width='44' height='40'><path d='M4 0 L40 0 L{36 if tail == 'right' else 6} 36 Z' fill='#fff' stroke='#111' stroke-width='4' stroke-linejoin='round'/>
          <rect x='2' y='-2' width='40' height='6' fill='#fff'/></svg></div>""")
    css = f""".bb{{position:absolute;translate:-50% -100%;background:#fff;border:4px solid #111;border-radius:40px;padding:14px 34px;
       font-family:{BUBBLE};font-weight:700;font-size:56px;color:#111;white-space:nowrap;box-shadow:0 4px 12px rgba(0,0,0,.25)}}
    .bt{{position:absolute;top:100%;margin-top:-3px}}"""
    return css, f"<div class=stage>{''.join(out)}</div>", "overlay"

# ---------------------------------------------------------------- 12 헤드라인 띠 (실사 위)
def headbar(si, g, at, ctx):
    out = []
    for i, h in enumerate(g.get("items", [g])):
        t = at(si, h.get("at", i)); y = h.get("y", .45 + i * .14) * 800
        out.append(f"<div class=hbx style='top:{y:.0f}px;animation:blurIn .25s {t:.2f}s both'>{rich(esc(h['text']), '#c8141c')}</div>")
    W = min(ctx["sw"], 1500)
    css = f""".hbx{{position:absolute;left:50%;width:{W}px;margin-left:-{W / 2}px;translate:0 -50%;background:#fff;padding:12px 24px;text-align:center;
       font-size:40px;font-weight:700;color:#111;box-shadow:0 4px 16px rgba(0,0,0,.35);word-break:keep-all}}"""
    sr = f"<div class='jsrc w'>출처 : {esc(g['source'])}</div>" if g.get("source") else ""
    return css, f"<div class=dim style='background:rgba(0,0,0,.25)'></div><div class=stage>{''.join(out)}{sr}</div>", "overlay"

# ---------------------------------------------------------------- 13 라벨 콜아웃 (실사 위)
def callout(si, g, at, ctx):
    out = []; sw = ctx["sw"]
    for i, c in enumerate(g.get("items", [g])):
        t = at(si, c.get("at", i)); px, py = c["x"] * sw, c["y"] * 800; lx, ly = c["lx"] * sw, c["ly"] * 800
        L = ((lx - px) ** 2 + (ly - py) ** 2) ** .5
        out.append(f"""<svg style='position:absolute;left:0;top:0;overflow:visible' width='{sw:.0f}' height='800'>
          <line x1='{px:.0f}' y1='{py:.0f}' x2='{lx:.0f}' y2='{ly:.0f}' stroke='#111' stroke-width='3'
            style='stroke-dasharray:{L:.0f};stroke-dashoffset:{L:.0f};animation:drawL .2s {t + .12:.2f}s both'/>
          <circle cx='{px:.0f}' cy='{py:.0f}' r='12' fill='#111' stroke='#fff' stroke-width='4' style='animation:fadeIn2 .1s {t:.2f}s both'/></svg>
          <div class=co style='left:{lx:.0f}px;top:{ly:.0f}px;animation:fadeIn2 .2s {t + .3:.2f}s both'><b>{esc(c['label'])}</b>{f"<small>{esc(c['sub'])}</small>" if c.get('sub') else ''}</div>""")
    css = f""".co{{position:absolute;translate:-50% -50%;background:#fff;border:3px solid #fff;border-radius:10px;padding:8px 18px;text-align:center;
       box-shadow:0 0 0 4px {BLUE},0 0 22px rgba(47,111,214,.8)}}.co b{{display:block;font-size:46px;font-weight:900;color:{NAVY};line-height:1.15}}
    .co small{{display:block;font-size:26px;color:{NAVY};font-weight:700}}"""
    return css, f"<div class=stage>{''.join(out)}</div>", "overlay"

# ---------------------------------------------------------------- 15 위치 핀 (실사 위)
def pin(si, g, at, ctx):
    out = []
    for i, p in enumerate(g.get("items", [g])):
        t = at(si, p.get("at", i)); x, y = p.get("x", .5) * ctx["sw"], p.get("y", .4) * 800
        out.append(f"""<div class=pn style='left:{x:.0f}px;top:{y:.0f}px;animation:blurIn .3s {t:.2f}s both'>
          <svg width='46' height='60' viewBox='0 0 46 60'><path d='M23 58 C23 58 4 34 4 22 A19 19 0 0 1 42 22 C42 34 23 58 23 58 Z' fill='#e8322f' stroke='#fff' stroke-width='3'/>
          <circle cx='23' cy='22' r='7' fill='#fff'/></svg><span>{esc(p['text'])}</span></div>""")
    css = """.pn{position:absolute;translate:-20px -100%;display:flex;align-items:flex-end;gap:10px}
    .pn span{font-size:56px;font-weight:900;color:#fff;letter-spacing:-1px;-webkit-text-stroke:2px #222;paint-order:stroke fill;text-shadow:0 4px 12px rgba(0,0,0,.6);line-height:1}"""
    return css, f"<div class=stage>{''.join(out)}</div>", "overlay"

# ---------------------------------------------------------------- 16 인물 인용 (어두운 배경 + 픽사베이 인물 사진)
def portrait(si, g, at, ctx):
    t0 = at(si, g.get("at", 0)); sw = ctx["sw"]; photo = g.get("src", "")
    txt = rich(esc(g["quote"]), YEL)
    css = f""".pbg{{position:absolute;inset:0;background:radial-gradient(ellipse at 70% 40%,#5a5a5a,#2a2a2a 70%)}}
    .pbg:after{{content:'';position:absolute;inset:0;background:repeating-radial-gradient(circle at 30% 20%,rgba(255,255,255,.03) 0 2px,transparent 2px 5px)}}
    .pph{{position:absolute;left:0;top:0;bottom:0;width:{min(sw * .42, 560):.0f}px;background:url('file://{photo}') center/cover;
         -webkit-mask:linear-gradient(90deg,#000 65%,transparent);animation:fadeIn2 .4s {t0:.2f}s both}}
    .pq{{position:absolute;left:{min(sw * .42, 560) - 20:.0f}px;right:0;top:50%;transform:translateY(-50%);font-family:{SERIF};font-weight:700;font-size:40px;
        line-height:1.6;word-break:keep-all;color:#fff;padding:60px 70px;animation:fadeIn2 .5s {t0 + .3:.2f}s both}}
    .pq:before,.pq:after{{position:absolute;font-family:Georgia,serif;font-size:120px;line-height:1;color:#fff;opacity:.9}}
    .pq:before{{content:'\\201C';left:0;top:-10px}}.pq:after{{content:'\\201D';right:10px;bottom:-60px}}
    .pnm{{position:absolute;left:30px;top:{g.get('name_y', .66) * 800:.0f}px;background:#f4f1ea;padding:8px 22px;transform:rotate(-5deg);
         font-family:{HAND};font-size:42px;color:#111;box-shadow:0 4px 12px rgba(0,0,0,.4);line-height:1.15;animation:fadeIn2 .4s {t0 + .6:.2f}s both}}"""
    name = f"<div class=pnm>{esc(g['name']).replace(chr(10), '<br>')}</div>" if g.get("name") else ""
    sr = f"<div class='jsrc w'>{esc(g.get('credit', '자료사진'))}</div>"
    return css, f"<div class=pbg></div><div class=stage><div class=pph></div><div class=pq>{txt}</div>{name}{sr}</div>", "dark"

# ---------------------------------------------------------------- 11 원형 비교
def circles(si, g, at, ctx):
    it = g["items"]; n = len(it); t0 = at(si, g.get("at", 0)); W = min(ctx["sw"], 330 * n + 60); d = min(300, (W - 60) / n - 30)
    style = g.get("style", "fill"); out = []
    for i, c in enumerate(it):
        t = at(si, c["at"]) if "at" in c else t0 + .2 + i * .3; cx = 30 + (W - 60) * (i + .5) / n
        if style == "ring":
            look = f"border:8px solid {BLUE};background:rgba(220,232,248,.35);color:{BLUE}"
        else:
            look = f"background:{c.get('color', ['#d6eed6', '#c4c4c4', '#dce8f8'][i % 3])};color:#1d1d1d"
        sym = f"<i>{esc(c['symbol'])}</i>" if c.get("symbol") else ""
        out.append(f"""<div class=cc style='left:{cx - d / 2:.0f}px;width:{d:.0f}px;height:{d:.0f}px;{look};animation:popO .35s {t:.2f}s both'>
          {sym}<b>{count(c['value'], t + .1, .6)}<small>{esc(c.get('suffix', '%'))}</small></b>{f"<em>{esc(c['sub'])}</em>" if c.get('sub') else ''}</div>
          <div class=cl style='left:{cx - d / 2:.0f}px;width:{d:.0f}px;animation:fadeIn2 .3s {t:.2f}s both'>{esc(c['label'])}</div>""")
    css = f""".ccw{{position:absolute;left:50%;width:{W}px;margin-left:-{W / 2}px;top:{170 if g.get('title') else 110}px}}
    .cc{{position:absolute;top:0;border-radius:50%;display:flex;flex-direction:column;align-items:center;justify-content:center}}
    .cc b{{font-size:{d * .24:.0f}px;font-weight:900;letter-spacing:-2px}}.cc small{{font-size:.55em}}.cc i{{font-style:normal;font-size:{d * .2:.0f}px;font-weight:900}}
    .cc em{{font-style:normal;font-size:20px;color:#555}}
    .cl{{position:absolute;top:{d + 26:.0f}px;text-align:center;font-size:30px;font-weight:700;color:#222;padding-top:10px;border-top:3px solid #333}}"""
    ti, sr = head(g, t0)
    return css + STAMP_CSS, paper_wrap(f"{ti}<div class=ccw>{''.join(out)}</div>{stamp_html(g, at, si)}", sr, ctx, t0), "paper"

# ---------------------------------------------------------------- 18 VS 숫자 (실사 위, 흐린 덮개)
def vsnum(si, g, at, ctx):
    a = g.get("at", [0, 1, 2]); L, R = g["left"], g["right"]; tL, tG, tR = at(si, a[0]), at(si, a[1]), at(si, a[2])
    def side(s, t, col):
        return (f"<div class=vsS><span class=vsC style='animation:fadeIn2 .3s {t:.2f}s both'>{esc(s['label'])}</span>"
                f"<div class=vsN style='color:{col};animation:blurIn .3s {t:.2f}s both'>{count(s['value'], t + .1, .7)}<small>{esc(s.get('suffix', ''))}</small></div></div>")
    memo = f"<div class=vsM style='animation:fadeIn2 .3s {tG + .2:.2f}s both'>{esc(g['memo'])}</div>" if g.get("memo") else ""
    css = f""".vsw{{position:absolute;left:0;right:0;top:{g.get('y', .5) * 800:.0f}px;transform:translateY(-50%);display:flex;align-items:flex-end;justify-content:center;gap:34px}}
    .vsS{{text-align:center}}.vsC{{display:inline-block;background:#fff;border:3px solid #333;border-radius:22px;padding:2px 22px;font-size:34px;font-weight:700;color:#222}}
    .vsN{{font-size:150px;font-weight:900;letter-spacing:-4px;line-height:1.05;-webkit-text-stroke:3px #2b3f57;text-shadow:0 4px 0 #2b3f57,0 8px 20px rgba(0,0,0,.35)}}
    .vsN small{{font-size:.62em;letter-spacing:-2px}}
    .vsG{{font-size:110px;font-weight:900;color:#3a3f47;line-height:1.1;position:relative}}
    .vsM{{position:absolute;left:50%;top:-70px;translate:-50% 0;font-family:{HAND};font-size:58px;color:#d98a00;white-space:nowrap;rotate:-6deg}}"""
    ti, sr = head(g, tL)
    body = (f"<div class=dim style='background:rgba(255,255,255,.55);animation:fadeIn2 .3s {tL:.2f}s both'></div><div class=stage>{ti}"
            f"<div class=vsw>{side(L, tL, '#8fc0ea')}<div class=vsG style='animation:popO .25s {tG:.2f}s both'>&gt;{memo}</div>{side(R, tR, '#aeb4bc')}</div>{sr}</div>")
    return css, body, "overlay"

# ---------------------------------------------------------------- 19 아이콘 흐름도
ICON = {
 "bank": "<path d='M8 26 L32 12 L56 26 Z M12 30 h40 M16 30 v18 M26 30 v18 M38 30 v18 M48 30 v18 M10 50 h44'/>",
 "building": "<rect x='16' y='10' width='32' height='42' rx='2'/><path d='M24 18h4M36 18h4M24 26h4M36 26h4M24 34h4M36 34h4M29 52v-10h6v10'/>",
 "school": "<path d='M8 24 L32 12 L56 24 L32 36 Z M18 30 v12 c8 6 20 6 28 0 v-12 M56 24 v14'/>",
 "phone": "<rect x='20' y='8' width='24' height='48' rx='5'/><path d='M29 14h6M30 50h4'/>",
 "camera": "<rect x='10' y='20' width='44' height='30' rx='5'/><circle cx='32' cy='35' r='9'/><path d='M24 20 l4-6 h8 l4 6'/>",
 "glasses": "<rect x='8' y='24' width='20' height='14' rx='6'/><rect x='36' y='24' width='20' height='14' rx='6'/><path d='M28 30h8M8 28 L4 24M56 28 L60 24'/>",
 "ai": "<rect x='16' y='16' width='32' height='32' rx='5'/><path d='M24 8v8M32 8v8M40 8v8M24 48v8M32 48v8M40 48v8M8 24h8M8 32h8M8 40h8M48 24h8M48 32h8M48 40h8'/><text x='32' y='37' text-anchor='middle' font-size='13' font-weight='900' stroke='none' fill='currentColor'>AI</text>",
 "document": "<path d='M18 8 h20 l10 10 v38 h-30 Z M38 8 v10 h10 M24 30h16M24 38h16M24 46h10'/>",
 "money": "<rect x='8' y='18' width='48' height='28' rx='4'/><circle cx='32' cy='32' r='7'/><path d='M14 24h4M46 40h4'/>",
 "person": "<circle cx='32' cy='22' r='10'/><path d='M14 54 c0-12 8-18 18-18 s18 6 18 18'/>",
 "people": "<circle cx='24' cy='24' r='8'/><circle cx='42' cy='24' r='8'/><path d='M8 50 c0-10 7-14 16-14 s16 4 16 14 M34 38 c8 0 18 2 18 12'/>",
 "check": "<circle cx='32' cy='32' r='22'/><path d='M22 32 l7 7 l13-14'/>",
 "warning": "<path d='M32 8 L58 54 H6 Z M32 24 v14 M32 45 v2'/>",
 "chart": "<path d='M10 54 h44 M16 46 v-10 M28 46 v-20 M40 46 v-14 M52 46 v-28'/>",
 "globe": "<circle cx='32' cy='32' r='22'/><path d='M10 32h44 M32 10 c-10 12 -10 32 0 44 M32 10 c10 12 10 32 0 44'/>",
 "lock": "<rect x='14' y='28' width='36' height='26' rx='4'/><path d='M22 28 v-8 a10 10 0 0 1 20 0 v8 M32 38 v8'/>",
 "search": "<circle cx='28' cy='28' r='14'/><path d='M38 38 L54 54'/>",
 "clock": "<circle cx='32' cy='32' r='22'/><path d='M32 18 v14 l10 6'/>",
}
def flow(si, g, at, ctx):
    st = g["steps"]; n = len(st); t0 = at(si, g.get("at", 0)); W = min(ctx["sw"] - 40, 380 * n); d = min(250, W / n - 110)
    out = []
    for i, s in enumerate(st):
        t = at(si, s["at"]) if "at" in s else t0 + .2 + i * .5; cx = W * (i + .5) / n
        out.append(f"""<div class=fc style='left:{cx - d / 2:.0f}px;width:{d:.0f}px;height:{d:.0f}px;animation:popO .3s {t:.2f}s both'>
          <svg viewBox='0 0 64 64' width='{d * .55:.0f}' height='{d * .55:.0f}' fill='none' stroke='{NAVY}' stroke-width='3.2' stroke-linecap='round' stroke-linejoin='round' style='color:{NAVY}'>{ICON.get(s.get('icon', 'check'), ICON['check'])}</svg>
          <span class=fch>{esc(s['text'])}</span></div>""")
        if i < n - 1:
            ax = cx + d / 2 + 14; aw = W / n - d - 28
            out.append(f"<div class=fa style='left:{ax:.0f}px;width:{aw:.0f}px;top:{d / 2 - 12:.0f}px;animation:growX .25s {t + .3:.2f}s both'></div>")
    css = f""".fw{{position:absolute;left:50%;width:{W}px;margin-left:-{W / 2}px;top:{(820 - d) / 2 - 30:.0f}px}}
    .fc{{position:absolute;top:0;border-radius:50%;background:#fff;border:6px solid #b8d2f2;box-shadow:0 0 0 2px #fff,0 6px 16px rgba(47,111,214,.25);display:flex;align-items:center;justify-content:center}}
    .fch{{position:absolute;bottom:-30px;left:50%;translate:-50% 0;background:{NAVY};color:#fff;font-size:34px;font-weight:700;padding:6px 22px;border-radius:30px;white-space:nowrap}}
    .fa{{position:absolute;height:24px;background:{BLUE};transform-origin:left;clip-path:polygon(0 30%,75% 30%,75% 0,100% 50%,75% 100%,75% 70%,0 70%)}}"""
    ti, sr = head(g, t0)
    return css, paper_wrap(f"{ti}<div class=fw>{''.join(out)}</div>", sr, ctx, t0), "paper"

# ---------------------------------------------------------------- 20 세로 연혁
def history(si, g, at, ctx):
    ev = g["events"]; n = len(ev); t0 = at(si, g.get("at", 0)); W = min(ctx["sw"], 900)
    top = 120 if g.get("title") else 50; rowh = min(80, (740 - top) / n); out = []
    for i, e in enumerate(ev):
        t = at(si, e["at"]) if "at" in e else t0 + .2 + i * g.get("row_seconds", .25); y = top + i * rowh
        hl = i in g.get("highlight", [])
        out.append(f"""<div class=hr style='top:{y:.0f}px;height:{rowh - 10:.0f}px;animation:fadeIn2 .3s {t:.2f}s both'>
          <span class=hd>{esc(e['date'])}</span><i></i><span class=hx style='{f"color:{RED};font-weight:800" if hl else ""}'>{rich(esc(e['text']), RED)}</span></div>""")
    css = f""".hw{{position:absolute;left:50%;width:{W}px;margin-left:-{W / 2}px;top:0;bottom:0}}
    .hline{{position:absolute;left:226px;top:{top}px;height:{n * rowh - 10:.0f}px;border-left:2px solid #bfc6d0}}
    .hr{{position:absolute;left:0;right:0;display:flex;align-items:center}}
    .hd{{width:200px;text-align:right;font-size:28px;font-weight:800;color:{NAVY};padding-right:18px}}
    .hr i{{width:16px;height:16px;border-radius:50%;background:{BLUE};margin:0 18px 0 -1px;box-shadow:0 0 0 4px #fff}}
    .hx{{flex:1;height:100%;display:flex;align-items:center;padding-left:22px;background:rgba(230,233,238,.75);font-size:28px;color:#222;font-weight:500;word-break:keep-all}}"""
    ti, sr = head(g, t0)
    return css, paper_wrap(f"{ti}<div class=hw><div class=hline></div>{''.join(out)}</div>", sr, ctx, t0), "paper"

# ---------------------------------------------------------------- 23 용어 정의 (글리치 배경)
def glitch(si, g, at, ctx):
    t0 = at(si, g.get("at", 0))
    css = f""".gbg{{position:absolute;inset:0;overflow:hidden;background:linear-gradient(180deg,#2b2140,#3b2b55 50%,#241a36)}}
    .gbg:before{{content:'';position:absolute;inset:-240px 0 0 0;background:repeating-linear-gradient(0deg,rgba(255,255,255,.07) 0 2px,transparent 2px 6px),
       repeating-linear-gradient(0deg,rgba(180,140,255,.18) 0 18px,transparent 18px 60px);animation:scan 2s linear infinite}}
    .gbg i{{position:absolute;left:-5%;width:110%;background:rgba(200,180,255,.22);animation:jitter .6s steps(4) infinite}}
    .gd{{position:absolute;left:40px;bottom:60px;right:40px;color:#fff}}
    .gd h2{{font-size:72px;font-weight:900;letter-spacing:-1px;animation:blurIn .3s {t0:.2f}s both}}
    .gd p{{margin-top:12px;font-size:32px;line-height:1.5;font-weight:500;animation:fadeIn2 .4s {t0 + .35:.2f}s both;word-break:keep-all}}"""
    bands = "".join(f"<i style='top:{y}%;height:{h}px;animation-delay:-{k * .13:.2f}s'></i>" for k, (y, h) in enumerate([(18, 10), (37, 4), (52, 16), (71, 6), (84, 3)]))
    return css, (f"<div class=gbg>{bands}</div><div class=stage><div class=gd><h2>{esc(g['term'])}</h2>"
                 f"<p>{rich(esc(g['definition']), '#ff9f3a')}</p></div></div>"), "dark"

# ---------------------------------------------------------------- 24 키네틱 큰 글자 (실사 위)
def kinetic(si, g, at, ctx):
    t0 = at(si, g.get("at", 0))
    css = f""".kw{{position:absolute;left:0;right:0;top:{g.get('y', .45) * 800:.0f}px;translate:0 -50%;text-align:center;font-family:{POSTER};
       font-size:{g.get('size', 220)}px;color:{g.get('color', '#fff')};letter-spacing:6px;line-height:1;
       text-shadow:0 6px 0 rgba(0,0,0,.35),0 14px 40px rgba(0,0,0,.6);animation:kinIn .35s {t0:.2f}s both cubic-bezier(.2,.8,.2,1)}}"""
    return css, f"<div class=dim style='background:rgba(0,0,0,.35)'></div><div class=stage><div class=kw>{esc(g['text'])}</div></div>", "overlay"

# ---------------------------------------------------------------- 25 강조 도장 (실사 위)
def stamp(si, g, at, ctx):
    return STAMP_CSS, f"<div class=stage>{stamp_html({'stamp': {**g, 'at': g.get('at', 0)}}, at, si)}</div>", "overlay"

JH = {"table": table, "hbar": hbar, "line": line, "vbar": vbar, "darkcard": darkcard, "tanbox": tanbox, "statcards": statcards,
      "number": number, "faded": faded, "bubble": bubble, "circles": circles, "headbar": headbar, "callout": callout, "pin": pin,
      "portrait": portrait, "vsnum": vsnum, "flow": flow, "history": history, "glitch": glitch, "kinetic": kinetic, "stamp": stamp}
DIM_CSS = ".dim{position:absolute;inset:0;background:rgba(0,0,0,.55)}"

def is_light(scene):
    """화면 틀(자막 바·이름표)을 밝은 슬라이드용 회색으로 쓸지."""
    if "frame" in scene: return scene["frame"] == "light"
    g = scene.get("graphic") or {}
    t = g.get("type")
    if not t or t in OVERLAY_TYPES or t in DARK_TYPES or t == "quote": return False
    if t == "vbar" and (scene.get("stock") or scene.get("pixabay_video") or scene.get("pixabay_image")): return False
    return True
