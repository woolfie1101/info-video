"""추가 그래픽 10종. graphics.py가 불러 쓴다. 모두 1000x800 무대 좌표, 등장 시점은 자막 번호(at).
line, donut, table, timeline, ranking, bignum, headline, steps, versus, photo
"""
import math

EXTRA_CSS = """
@keyframes draw{to{stroke-dashoffset:0}}
@keyframes growX{from{transform:scaleX(0)}to{transform:scaleX(1)}}
@keyframes slideUp{from{opacity:0;transform:translateY(60px)}to{opacity:1;transform:none}}
@keyframes rowIn{from{clip-path:inset(0 100% 0 0)}to{clip-path:inset(0 0 0 0)}}
@keyframes hl{from{background-size:0% 100%}to{background-size:100% 100%}}
@keyframes zoomSlow{from{transform:none}to{transform:none}}
@property --n{syntax:'<integer>';inherits:false;initial-value:0}
.cnt{counter-reset:n var(--n)}.cnt:before{content:counter(n)}
.hl{background:linear-gradient(#ffe45c,#ffe45c) no-repeat 0 88%/0% 40%;padding:0 4px}
"""

def _head(g):
    t = f"<div class=title style='animation:fadeIn .3s .05s both'>{g['title']}</div>" if g.get("title") else ""
    s = f"<div class=src style='animation:fadeIn .3s .2s both'>출처 : {g['source']}</div>" if g.get("source") else ""
    return t, s

def _paper(stage):
    return f"<div class=paper></div><div class=stage>{stage}</div>"

def _hl(text, words, t):
    for w in words or []:
        text = text.replace(w, f"<span class=hl style='animation:hl .45s {t:.2f}s both ease-out'>{w}</span>")
    return text

# ---------- line: 꺾은선이 왼쪽→오른쪽으로 그려지고 점·수치가 차례로 ----------
def line(si, g, at):
    data = g["data"]; n = len(data); vals = [v for _, v in data]
    lo = g.get("min", min(0, min(vals))); hi = g.get("max", max(vals) * 1.1)
    x0, x1, y0, y1 = 90, 930, 600, 170
    pts = [(x0 + (x1 - x0) * i / max(1, n - 1), y0 - (y0 - y1) * (v - lo) / (hi - lo)) for i, v in enumerate(vals)]
    L = sum(math.dist(pts[i], pts[i + 1]) for i in range(n - 1)) + 1
    t0 = at(si, g.get("at", 0)); dur = g.get("draw_seconds", 1.6); col = g.get("color", "#1749c9")
    suffix = g.get("suffix", ""); hi_idx = set(g.get("highlight", [n - 1]))
    dots = []
    for i, ((x, y), (lab, v)) in enumerate(zip(pts, data)):
        t = t0 + dur * i / max(1, n - 1)
        c = "#c62828" if i in hi_idx else col
        dots.append(f"""<div class=dot style="left:{x - 11:.0f}px;top:{y - 11:.0f}px;background:{c};animation:pop .3s {t:.2f}s both"></div>
        <div class=lv style="left:{x - 80:.0f}px;top:{y - 62:.0f}px;color:{c};animation:wipeUp .3s {t + .1:.2f}s both">{v:,}{suffix}</div>
        <div class=lx style="left:{x - 80:.0f}px">{lab}</div>""")
    poly = " ".join(f"{x:.0f},{y:.0f}" for x, y in pts)
    area = f"{x0},{y0} {poly} {x1},{y0}"
    css = """.lx{position:absolute;top:620px;width:160px;text-align:center;font-size:24px;font-weight:700;color:#333}
    .lv{position:absolute;width:160px;text-align:center;font-size:30px;font-weight:900;text-shadow:2px 2px 0 #fff,-2px -2px 0 #fff,2px -2px 0 #fff,-2px 2px 0 #fff}
    .dot{position:absolute;width:22px;height:22px;border-radius:50%;border:4px solid #fff;box-shadow:0 2px 6px rgba(0,0,0,.2)}
    svg.pl{position:absolute;left:0;top:0}"""
    t, s = _head(g)
    unit = f"<div style='position:absolute;left:30px;top:100px;font-size:22px;color:#555'>({g['unit']})</div>" if g.get("unit") else ""
    svg = f"""<svg class=pl width=1000 height=800><line x1=60 y1={y0} x2=960 y2={y0} stroke=#333 stroke-width="3" />
      <polygon points="{area}" fill="{col}" opacity=".10" style="animation:fadeIn .6s {t0 + dur:.2f}s both"/>
      <polyline points="{poly}" fill=none stroke="{col}" stroke-width=8 stroke-linejoin=round stroke-linecap=round
        style="stroke-dasharray:{L:.0f};stroke-dashoffset:{L:.0f};animation:draw {dur}s {t0:.2f}s both linear"/></svg>"""
    return css, _paper(t + unit + svg + "".join(dots) + s)

# ---------- donut: 원형 비율이 차오르고 가운데 %가 올라감 ----------
def donut(si, g, at):
    v = g["value"]; t0 = at(si, g.get("at", 0)); col = g.get("color", "#1749c9")
    r = 190; C = 2 * math.pi * r
    side = "".join(f"<p style='animation:slideUp .4s {at(si, x.get('at', i + 1)):.2f}s both'>{x['text']}</p>"
                   for i, x in enumerate(g.get("notes", [])))
    css = f"""@keyframes cD{{from{{--n:0}}to{{--n:{int(v)}}}}}
    .dn{{position:absolute;left:{60 if side else 260}px;top:150px;width:480px;height:480px}}
    .dn .num{{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-size:120px;font-weight:900;color:{col}}}
    .dn .num small{{font-size:56px;margin-left:4px}}
    .dn .lab{{position:absolute;top:300px;width:100%;text-align:center;font-size:30px;font-weight:700;color:#333}}
    .notes{{position:absolute;left:600px;top:220px;width:390px}}
    .notes p{{font-size:36px;font-weight:800;line-height:1.35;margin-bottom:34px;padding-left:20px;border-left:8px solid {col};word-break:keep-all}}"""
    t, s = _head(g)
    body = f"""{t}<div class=dn><svg width=480 height=480 viewBox="0 0 480 480" style="transform:rotate(-90deg)">
      <circle cx=240 cy=240 r={r} fill=none stroke="#dfe3ea" stroke-width="70" />
      <circle cx=240 cy=240 r={r} fill=none stroke="{col}" stroke-width=70
        style="stroke-dasharray:{C:.1f};stroke-dashoffset:{C:.1f};--o:{C * (1 - v / 100):.1f};animation:dfill 1.2s {t0:.2f}s both cubic-bezier(.2,.8,.2,1)"/></svg>
      <div class=num><span class=cnt style="animation:cD 1.2s {t0:.2f}s both ease-out"></span><small>%</small></div>
      <div class=lab>{g.get('label', '')}</div></div>
      {"<div class=notes>" + side + "</div>" if side else ""}{s}"""
    css += f"@keyframes dfill{{to{{stroke-dashoffset:{C * (1 - v / 100):.1f}}}}}"
    return css, _paper(body)

# ---------- table: 제목 → 머리행 → 행이 하나씩 왼쪽부터 닦이듯 ----------
def table(si, g, at):
    cols = g["columns"]; rows = g["rows"]; t0 = at(si, g.get("at", 0)); step = g.get("row_seconds", .35)
    at_row = {int(k): v for k, v in g.get("at_row", {}).items()}
    w = g.get("widths") or [1] * len(cols); tw = sum(w)
    grid = " ".join(f"{x / tw * 100:.1f}%" for x in w)
    hdr = "".join(f"<div>{c}</div>" for c in cols)
    rs = []
    for i, r in enumerate(rows):
        t = at(si, at_row[i]) if i in at_row else t0 + .3 + i * step
        hl = " hi" if i in g.get("highlight", []) else ""
        rs.append(f"<div class='tr{hl}' style='animation:rowIn .45s {t:.2f}s both ease-out'>" + "".join(f"<div>{c}</div>" for c in r) + "</div>")
    fs = 30 if len(rows) <= 5 else 26
    css = f""".tb{{position:absolute;left:20px;right:20px;top:110px}}
    .th,.tr{{display:grid;grid-template-columns:{grid};align-items:center}}
    .th{{background:#dbe8fb;font-size:28px;font-weight:800;color:#1749c9;height:64px}}
    .th div,.tr div{{padding:0 20px;word-break:keep-all}}
    .tr{{min-height:88px;border-bottom:2px solid #c9ced6;font-size:{fs}px;color:#222;line-height:1.3}}
    .tr div:first-child{{font-weight:900;color:#1749c9}}
    .tr.hi{{background:rgba(255,228,92,.45)}}"""
    t, s = _head(g)
    return css, _paper(f"{t}<div class=tb><div class=th style='animation:fadeIn .3s {t0:.2f}s both'>{hdr}</div>{''.join(rs)}</div>{s}")

# ---------- timeline: 가로선이 그려지고 시점 점이 차례로 ----------
def timeline(si, g, at):
    ev = g["events"]; n = len(ev); t0 = at(si, g.get("at", 0))
    x0, x1, y = 70, 930, 430
    items = []
    for i, e in enumerate(ev):
        x = x0 + (x1 - x0) * i / max(1, n - 1); t = at(si, e["at"]) if "at" in e else t0 + .4 + i * .45
        up = i % 2 == 0; c = "#c62828" if i in g.get("highlight", []) else "#1749c9"
        txt_top = y - 230 if up else y + 50
        items.append(f"""<div class=tdot style="left:{x - 18:.0f}px;top:{y - 18}px;background:{c};animation:pop .35s {t:.2f}s both"></div>
        <div class=tdate style="left:{x - 110:.0f}px;top:{(y - 78) if not up else (y + 34)}px;color:{c};animation:fadeIn .3s {t:.2f}s both">{e['date']}</div>
        <div class=ttxt style="left:{x - 120:.0f}px;top:{txt_top}px;animation:slideUp .4s {t + .1:.2f}s both;{'' if up else ''}">{e['text']}</div>""")
    css = f""".tline{{position:absolute;left:{x0 - 30}px;width:{x1 - x0 + 60}px;top:{y - 4}px;height:8px;border-radius:4px;background:#222;transform-origin:left}}
    .tdot{{position:absolute;width:36px;height:36px;border-radius:50%;border:6px solid #fff;box-shadow:0 2px 8px rgba(0,0,0,.25)}}
    .tdate{{position:absolute;width:220px;text-align:center;font-size:32px;font-weight:900}}
    .ttxt{{position:absolute;width:240px;min-height:150px;display:flex;align-items:center;justify-content:center;text-align:center;
          font-size:28px;font-weight:700;line-height:1.35;color:#222;background:#fff;border:4px solid #111;border-radius:22px;padding:14px;word-break:keep-all}}"""
    t, s = _head(g)
    return css, _paper(f"{t}<div class=tline style='animation:growX .7s {t0:.2f}s both cubic-bezier(.2,.8,.2,1)'></div>{''.join(items)}{s}")

# ---------- ranking: 순위 가로 막대가 왼쪽에서 자람 ----------
def ranking(si, g, at):
    it = g["items"]; n = len(it); t0 = at(si, g.get("at", 0)); vmax = max(v for _, v in it)
    suffix = g.get("suffix", ""); hi = set(g.get("highlight", [0]))
    rowh = min(110, 600 / n); rows = []
    order = list(range(n))[::-1] if g.get("reverse_reveal", True) else list(range(n))  # 기본: 5위부터 1위 순으로 공개
    for k, i in enumerate(order):
        lab, v = it[i]; y = 120 + i * rowh; t = t0 + k * .35; w = 560 * v / vmax
        c = "#c62828" if i in hi else "#0f2a5c"
        rows.append(f"""<div class=rk style="top:{y:.0f}px;height:{rowh - 18:.0f}px;animation:fadeIn .25s {t:.2f}s both">
          <div class=rn style="background:{c}">{i + 1}</div><div class=rl>{lab}</div>
          <div class=rb style="width:{w:.0f}px;background:{c};animation:growX .5s {t:.2f}s both cubic-bezier(.2,.8,.2,1)"></div>
          <div class=rv style="left:{390 + w + 14:.0f}px;color:{c};animation:wipeUp .3s {t + .35:.2f}s both">{v:,}{suffix}</div></div>""")
    css = """.rk{position:absolute;left:0;right:0}
    .rn{position:absolute;left:0;top:50%;margin-top:-30px;width:60px;height:60px;border-radius:50%;color:#fff;font-size:32px;font-weight:900;text-align:center;line-height:60px}
    .rl{position:absolute;left:76px;width:300px;top:50%;transform:translateY(-50%);font-size:32px;font-weight:800;color:#222;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
    .rb{position:absolute;left:390px;top:15%;bottom:15%;border-radius:0 8px 8px 0;transform-origin:left}
    .rv{position:absolute;top:50%;margin-top:-22px;font-size:34px;font-weight:900;white-space:nowrap}"""
    t, s = _head(g)
    return css, _paper(t + "".join(rows) + s)

# ---------- bignum: 큰 숫자 하나가 올라가며 강조 ----------
def bignum(si, g, at):
    t0 = at(si, g.get("at", 0)); col = g.get("color", "#c62828"); v = int(g["value"])
    cap_t = at(si, g.get("caption_at", g.get("at", 0))) + .6
    css = f"""@keyframes cB{{from{{--n:0}}to{{--n:{v}}}}}
    .bl{{position:absolute;top:150px;width:100%;text-align:center;font-size:44px;font-weight:800;color:#333}}
    .bn{{position:absolute;top:240px;width:100%;text-align:center;font-size:230px;font-weight:900;line-height:1;color:{col};letter-spacing:-6px}}
    .bn small{{font-size:90px;letter-spacing:0;margin-left:6px}}
    .bu{{position:absolute;left:300px;width:400px;top:500px;height:14px;border-radius:7px;background:{col};transform-origin:left}}
    .bc{{position:absolute;top:560px;left:40px;right:40px;text-align:center;font-size:40px;font-weight:700;color:#222;line-height:1.4;word-break:keep-all}}"""
    pre = g.get("prefix", ""); suf = g.get("suffix", "")
    body = f"""<div class=bl style='animation:fadeIn .3s {t0:.2f}s both'>{g.get('label', '')}</div>
      <div class=bn>{pre}<span class=cnt style="animation:cB 1.1s {t0 + .2:.2f}s both cubic-bezier(.2,.8,.2,1)"></span><small>{suf}</small></div>
      <div class=bu style="animation:growX .5s {t0 + 1.2:.2f}s both"></div>
      <div class=bc style="animation:slideUp .4s {cap_t:.2f}s both">{g.get('caption', '')}</div>"""
    t, s = _head(g)
    return css, _paper(t + body + s)

# ---------- headline: 기사 제목 카드가 겹겹이 올라오고 형광펜이 그어짐 ----------
def headline(si, g, at):
    it = g["items"]; n = len(it); cards = []
    for i, h in enumerate(it):
        t = at(si, h.get("at", i)); rot = [-2.5, 1.8, -1.2, 2.2][i % 4]
        top = 100 + i * (590 / max(1, n)); left = 30 + (i % 2) * 90
        title = _hl(h["title"], h.get("highlight"), t + .5)
        cards.append(f"""<div class=nc style="left:{left}px;top:{top:.0f}px;--r:{rot}deg;animation:ncIn .45s {t:.2f}s both cubic-bezier(.2,.8,.2,1)">
          <div class=no>{h.get('outlet', '')}<span>{h.get('date', '')}</span></div><div class=nt>{title}</div></div>""")
    css = """@keyframes ncIn{from{opacity:0;transform:translateY(80px) rotate(var(--r))}to{opacity:1;transform:rotate(var(--r))}}
    .nc{position:absolute;width:850px;background:#fff;border-radius:14px;padding:26px 34px;box-shadow:0 14px 30px rgba(0,0,0,.18);border-top:10px solid #222}
    .no{font-size:24px;font-weight:800;color:#666;margin-bottom:10px}.no span{margin-left:16px;font-weight:500;color:#999}
    .nt{font-size:36px;font-weight:900;line-height:1.35;color:#111;word-break:keep-all}"""
    t, s = _head(g)
    return css, _paper(t + "".join(cards) + s)

# ---------- steps: 1→2→3 단계가 화살표와 함께 차례로 ----------
def steps(si, g, at):
    st = g["steps"]; n = len(st); w = 1000 / n; out = []
    for i, x in enumerate(st):
        t = at(si, x["at"]) if "at" in x else at(si, g.get("at", 0)) + i * .6
        cx = w * i + w / 2
        out.append(f"""<div class=sc style="left:{cx - 100:.0f}px;animation:pop .4s {t:.2f}s both"><b>{i + 1}</b></div>
        <div class=sx style="left:{cx - w / 2 + 10:.0f}px;width:{w - 20:.0f}px;animation:slideUp .4s {t + .15:.2f}s both">{x['text']}</div>""")
        if i < n - 1:
            out.append(f"""<div class=sa style="left:{cx + 110:.0f}px;width:{w - 220:.0f}px;animation:growX .35s {t + .3:.2f}s both"></div>""")
    css = """.sc{position:absolute;top:200px;width:200px;height:200px;border-radius:50%;background:#fff;border:8px solid #111;box-shadow:8px 8px 0 rgba(0,0,0,.08)}
    .sc b{display:block;text-align:center;line-height:184px;font-size:96px;font-weight:900;color:#1749c9}
    .sx{position:absolute;top:440px;text-align:center;font-size:34px;font-weight:800;line-height:1.35;color:#222;word-break:keep-all}
    .sa{position:absolute;top:292px;height:16px;background:#111;border-radius:8px;transform-origin:left}
    .sa:after{content:'';position:absolute;right:-14px;top:-14px;border-left:28px solid #111;border-top:22px solid transparent;border-bottom:22px solid transparent}"""
    t, s = _head(g)
    return css, _paper(t + "".join(out) + s)

# ---------- versus: 두 편을 나란히, 가운데 VS ----------
def versus(si, g, at):
    L, R = g["left"], g["right"]; a = g.get("at", [0, 1])
    def col(side, x, t, c):
        items = "".join(f"<li style='animation:slideUp .35s {t + .3 + k * .25:.2f}s both'>{it}</li>" for k, it in enumerate(side.get("items", [])))
        return f"""<div class=vc style="left:{x}px;border-color:{c};animation:pop .4s {t:.2f}s both"><h3 style="background:{c}">{side['title']}</h3><ul>{items}</ul></div>"""
    css = """.vc{position:absolute;top:120px;width:430px;height:580px;background:#fff;border:6px solid;border-radius:30px;overflow:hidden;box-shadow:10px 10px 0 rgba(0,0,0,.08)}
    .vc h3{color:#fff;font-size:40px;font-weight:900;text-align:center;padding:22px 0}
    .vc ul{list-style:none;padding:24px 30px}.vc li{font-size:32px;font-weight:700;line-height:1.35;margin-bottom:22px;padding-left:34px;position:relative;word-break:keep-all}
    .vc li:before{content:'●';position:absolute;left:0;font-size:22px;top:6px;color:#999}
    .vs{position:absolute;left:430px;top:340px;width:140px;height:140px;border-radius:50%;background:#111;color:#ffe45c;font-size:56px;font-weight:900;text-align:center;line-height:140px;z-index:2}"""
    t, s = _head(g)
    body = (t + col(L, 0, at(si, a[0]), L.get("color", "#1749c9")) + col(R, 570, at(si, a[1]), R.get("color", "#c62828"))
            + f"<div class=vs style='animation:pop .4s {at(si, a[1]) - .2:.2f}s both'>VS</div>" + s)
    return css, _paper(body)

# ---------- photo: 픽사베이 사진을 액자처럼, 천천히 확대 + 설명 ----------
def photo(si, g, at, root=None):
    t0 = at(si, g.get("at", 0)); src = g.get("src", "")
    cap_t = at(si, g.get("caption_at", g.get("at", 0))) + .4
    css = """.pf{position:absolute;left:90px;top:90px;width:820px;height:540px;background:#fff;padding:18px;box-shadow:0 16px 36px rgba(0,0,0,.22);transform:rotate(-1.5deg)}
    .pf .im{width:100%;height:100%;overflow:hidden}.pf img{width:100%;height:100%;object-fit:cover}
    .pt{position:absolute;left:110px;top:60px;background:#111;color:#fff;font-size:24px;font-weight:800;padding:8px 18px;transform:rotate(-1.5deg);z-index:2}
    .pc{position:absolute;left:60px;right:60px;top:670px;text-align:center;font-size:40px;font-weight:800;color:#222;word-break:keep-all}"""
    tag = f"<div class=pt style='animation:fadeIn .3s {t0 + .3:.2f}s both'>{g['tag']}</div>" if g.get("tag") else ""
    body = f"""{tag}<div class=pf style="animation:slideUp .5s {t0:.2f}s both"><div class=im>
      <img src="file://{src}" style="animation:zoomSlow 8s {t0:.2f}s both linear"></div></div>
      <div class=pc style="animation:slideUp .4s {cap_t:.2f}s both">{_hl(g.get('caption', ''), g.get('highlight'), cap_t + .4)}</div>"""
    t, s = _head(g)
    return css, _paper(t + body + s)

MORE = {"line": line, "donut": donut, "table": table, "timeline": timeline, "ranking": ranking, "bignum": bignum,
        "headline": headline, "steps": steps, "versus": versus, "photo": photo}
