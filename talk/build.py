#!/usr/bin/env python3
"""Build present.html: the deck as one self-contained page, shown one slide at a time.

Reads deck.json (order, fonts) and slides/<id>.html. Run it again after editing a slide.
Keys: → / Space / PageDown / click = next build or slide, ← / PageUp = back,
Shift+→ / Shift+← = next / previous slide (skipping builds), A = reveal the whole slide,
Home / End, F = fullscreen, N = notes. URL #9.3 opens slide 9 with 3 builds shown.
"""
import html, json, re
from pathlib import Path

HERE = Path(__file__).resolve().parent
deck = json.loads((HERE / "deck.json").read_text(encoding="utf-8"))
fonts = "\n".join(f'<link rel="stylesheet" href="{html.escape(f["href"])}">'
                  for f in deck["faces"].values() if "href" in f)

slides, notes = [], []
for sid in deck["order"]:
    src = (HERE / "slides" / f"{sid}.html").read_text(encoding="utf-8")
    m = re.search(r"<aside>(.*?)</aside>", src, re.S)
    notes.append(m.group(1).strip() if m else "")
    slides.append(re.sub(r"<aside>.*?</aside>", "", src, flags=re.S))

page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(deck["title"])}</title>
{fonts}
<style>
html, body {{ margin: 0; height: 100%; background: #0d1017; overflow: hidden; cursor: default; }}
#stage {{ position: absolute; left: 50%; top: 50%; width: 1920px; height: 1080px; transform-origin: center; }}
#stage > section {{ box-sizing: border-box; position: absolute; inset: 0; width: 1920px; height: 1080px; overflow: hidden; }}
#stage > section:not(.on) {{ display: none !important; }}
section * {{ margin: 0; box-sizing: border-box; }}
section h1 {{ line-height: 1.1; }} section h2 {{ line-height: 1.15; }} section h3 {{ line-height: 1.2; }}
section p {{ line-height: 1.4; }}
section ul, section ol {{ padding-left: 1.2em; }}
section table {{ width: 100%; border-collapse: collapse; }}
section th, section td {{ padding: 0.35em 0.6em; border-bottom: 1px solid rgba(128,128,128,0.35); vertical-align: top; }}
section th {{ font-weight: 600; }}
x-shape {{ display: block; flex: none; }}
x-shape[kind="arrow-right"] {{ clip-path: polygon(0 30%, 60% 30%, 60% 0, 100% 50%, 60% 100%, 60% 70%, 0 70%); }}
x-shape[kind="arrow-left"] {{ clip-path: polygon(100% 30%, 40% 30%, 40% 0, 0 50%, 40% 100%, 40% 70%, 100% 70%); }}
x-shape[kind="ellipse"] {{ border-radius: 50%; }}
#count {{ position: fixed; right: 16px; bottom: 12px; font: 14px system-ui, sans-serif; color: #8a93a3; opacity: 0.6; }}
#notes {{ position: fixed; left: 0; right: 0; bottom: 0; max-height: 40vh; overflow: auto; display: none;
  padding: 16px 24px; background: rgba(13,16,23,0.94); color: #e6e2d8; font: 18px/1.5 system-ui, sans-serif; }}
body.notes #notes {{ display: block; }}
/* builds: hidden until revealed; "coal" dims earlier items of the same list */
.b-unit {{ transition: opacity 400ms ease, transform 400ms ease, filter 400ms ease; }}
.b-hidden {{ opacity: 0 !important; transform: translateY(18px) !important; }}
tr.b-hidden > td, tr.b-hidden > th {{ border-color: transparent; }}  /* collapsed borders don't fade with the row */
.b-past {{ opacity: 0.55; filter: grayscale(0.4); }}
.b-instant .b-unit {{ transition: none; }}
</style></head>
<body>
<div id="stage">
{"".join(slides)}
</div>
<div id="count"></div>
<div id="notes"></div>
<script>
const NOTES = {json.dumps(notes)};
const stage = document.getElementById("stage");
const slides = [...stage.querySelectorAll(":scope > section")];
let i = 0, step = 0;

// Build steps per slide, from data-build markers:
//   data-build="self"        the element appears as one step
//   data-build="items"       its children appear one by one (table: rows, minus a header row)
//   data-build="items coal"  same, and earlier children are dimmed once a later one appears
//   data-build-with="next"   on a child: appears together with the next child (arrows next to boxes)
// x-shape children always appear together with the next child. Steps run in document order,
// so a list inside a box comes right after the box.
const builds = slides.map(slide => {{
  const units = [];
  slide.querySelectorAll("[data-build]").forEach(el => {{
    const mode = el.dataset.build.split(/\\s+/);
    if (mode.includes("self")) {{ units.push({{ els: [el], list: null }}); return; }}
    let kids = el.tagName === "TABLE" ? [...el.querySelectorAll("tr")] : [...el.children];
    if (el.tagName === "TABLE" && kids[0] && kids[0].querySelector("th")) kids = kids.slice(1);
    const list = {{ coal: mode.includes("coal") }};
    let pending = [];
    for (const k of kids) {{
      pending.push(k);
      if (k.tagName === "X-SHAPE" || k.dataset.buildWith === "next") continue;
      units.push({{ els: pending, list }}); pending = [];
    }}
    if (pending.length) units.push({{ els: pending, list }});
  }});
  units.sort((a, b) => a.els[0].compareDocumentPosition(b.els[0]) & Node.DOCUMENT_POSITION_FOLLOWING ? -1 : 1);
  units.forEach(u => u.els.forEach(e => e.classList.add("b-unit")));
  return units;
}});

function render() {{
  const units = builds[i];
  const latest = new Map();  // list -> index of its most recently revealed unit
  units.forEach((u, k) => {{ if (k < step && u.list) latest.set(u.list, k); }});
  units.forEach((u, k) => u.els.forEach(e => {{
    e.classList.toggle("b-hidden", k >= step);
    e.classList.toggle("b-past", k < step && u.list && u.list.coal && latest.get(u.list) !== k);
  }}));
}}

function next() {{
  if (step < builds[i].length) {{ step++; render(); }}
  else if (i < slides.length - 1) show(i + 1, 0);
}}
function prev() {{
  if (step > 0) {{ step--; render(); }}
  else if (i > 0) show(i - 1, Infinity);
}}

function fit() {{
  const s = Math.min(innerWidth / 1920, innerHeight / 1080);
  stage.style.transform = `translate(-50%, -50%) scale(${{s}})`;
}}
function show(n, s = 0) {{
  i = Math.max(0, Math.min(slides.length - 1, n));
  step = Math.min(s, builds[i].length);
  slides.forEach((el, k) => el.classList.toggle("on", k === i));
  // jumping to a slide (back, Home/End, reload) shows its state at once, without animation
  stage.classList.add("b-instant"); render(); void stage.offsetWidth; stage.classList.remove("b-instant");
  document.getElementById("count").textContent = `${{i + 1}} / ${{slides.length}}`;
  document.getElementById("notes").textContent = NOTES[i] || "(no notes)";
  history.replaceState(null, "", "#" + (i + 1));
}}
addEventListener("keydown", e => {{
  if (e.shiftKey && e.key === "ArrowRight") show(i + 1);  // skip the rest of this slide's builds
  else if (e.shiftKey && e.key === "ArrowLeft") show(i - 1);
  else if (["ArrowRight", "ArrowDown", "PageDown", " ", "Enter"].includes(e.key)) next();
  else if (["ArrowLeft", "ArrowUp", "PageUp", "Backspace"].includes(e.key)) prev();
  else if (e.key === "Home") show(0);
  else if (e.key === "End") show(slides.length - 1, Infinity);
  else if (e.key === "a" || e.key === "A") show(i, Infinity);  // reveal all of this slide
  else if (e.key === "f" || e.key === "F") document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen();
  else if (e.key === "n" || e.key === "N") document.body.classList.toggle("notes");
  else return;
  e.preventDefault();
}});
addEventListener("click", e => {{ if (!e.target.closest("#notes")) next(); }});
addEventListener("contextmenu", e => {{ e.preventDefault(); prev(); }});
addEventListener("resize", fit);
fit();
const [hs, hb] = location.hash.slice(1).split(".");  // #9 = slide 9; #9.3 = slide 9 after 3 builds
show((parseInt(hs) || 1) - 1, parseInt(hb) || 0);
</script>
</body></html>
"""
(HERE / "present.html").write_text(page, encoding="utf-8")
print(f"wrote {HERE / 'present.html'} ({len(slides)} slides)")
