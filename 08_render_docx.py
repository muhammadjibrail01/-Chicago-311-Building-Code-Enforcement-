"""Step 8: render manuscript/paper4.md to Word with docx-js (the renderer and styling used for the other papers in this series).
Parses the markdown into blocks (title, headings, paragraphs, tables, figures, references), writes work/content4.json, and calls render.js."""
import re, subprocess
from PIL import Image
from common4 import *
md = open(os.path.join(OUT_DIR, "paper4.md"), encoding="utf-8").read()
m = re.match(r'---\ntitle: "(.*?)"\n---\n', md, re.S); title = m.group(1); body = md[m.end():]
def inline(s):
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s, flags=re.S)
    return re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<i>\1</i>", s, flags=re.S)
TOTAL = 9360                                      # text width in DXA (US Letter, 1-inch side margins)
def parse_table(p):
    lines = p.split("\n"); cells = lambda ln: [c.strip() for c in ln.strip().strip("|").split("|")]
    header, dashes = cells(lines[0]), [len(c) for c in cells(lines[1])]
    rows = []
    for ln in lines[2:]:
        r = cells(ln)
        if all(c == "" for c in r[1:]) and re.fullmatch(r"\*[^*]+\*", r[0]): rows.append([r[0].strip("*")])      # spanning sub-header row
        else: rows.append([inline(c) for c in r])
    cols = [round(TOTAL * d / sum(dashes)) for d in dashes]; cols[-1] += TOTAL - sum(cols)
    return [inline(h) for h in header], rows, cols
paras = [q for q in re.split(r"\n\s*\n", body) if q.strip()]
blocks = [{"t": "title", "text": title}]; section = ""; cap = None; panel = None; last_table = None
for para in paras:
    para = para.strip("\n")
    if para.startswith("# "): section = para[2:].strip(); blocks.append({"t": "h1", "text": section}); continue
    if para.startswith("## "): blocks.append({"t": "h2", "text": para[3:].strip()}); continue
    if para.startswith("|"):
        header, rows, cols = parse_table(para)
        ttl = cap if cap else (panel or "")
        if cap and panel: ttl = f"{cap} — {panel}"
        align = ["l", "l"] if header[:1] == ["Variable"] else ["l"] + ["c"] * (len(header) - 1)
        last_table = {"t": "table", "title": ttl, "header": header, "rows": rows, "cols": cols, "align": align, "note": ""}
        blocks.append(last_table); cap = None; panel = None; continue
    mm = re.fullmatch(r"\*\*(Table [A-Z]?\d+\..*)\*\*", para)
    if mm: cap = mm.group(1); continue
    mm = re.fullmatch(r"\*(Panel [A-Z]\..*)\*", para)
    if mm: panel = mm.group(1); continue
    if para.startswith("*Notes:*") and last_table is not None: last_table["note"] = inline(para[len("*Notes:*"):].strip()); last_table = None; continue
    mm = re.fullmatch(r"!\[(.*)\]\((.*?)\)\{width=([\d.]+)in\}", para, re.S)
    if mm:
        parts = re.split(r"(?<=\.)\s+(?=[A-Z])", mm.group(1).strip()); path = os.path.join(OUT_DIR, mm.group(2)); w, h = Image.open(path).size
        blocks.append({"t": "figure", "path": path, "caption": " ".join(parts[:2]), "note": " ".join(parts[2:]), "width_in": float(mm.group(3)), "w": w, "h": h}); continue
    if section == "": blocks.append({"t": "center", "text": inline(para)}); continue
    if section == "Abstract" and not any(b["t"] == "abstract" for b in blocks): blocks.append({"t": "abstract", "text": inline(para)}); continue
    if section == "References": blocks.append({"t": "ref", "text": inline(para)}); continue
    blocks.append({"t": "hyp" if re.match(r"\*\*H\d ", para) else "p", "text": inline(para)})
content = {"title": title, "running": "Reactive Enforcement: Hardship and Building Code Violations in Chicago", "blocks": blocks}
jdump(content, W("content4.json"))
out = os.path.join(OUT_DIR, "Paper4_Building_Code_Enforcement_Chicago.docx")
if os.path.exists(out): os.remove(out)
subprocess.run(["node", os.path.join(os.path.dirname(os.path.abspath(__file__)), "render.js"), W("content4.json"), out], check=True)
kinds = {}; [kinds.__setitem__(b["t"], kinds.get(b["t"], 0) + 1) for b in blocks]; print("blocks:", kinds)
