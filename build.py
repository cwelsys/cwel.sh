#!/usr/bin/env python3
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
OUT = ROOT / "public"
LS = ["about", "resume", "patches", "github", "linkedin", "email", "keys"]
STRIP = re.compile(r"\x1b\[[0-9;]*m")
PATCH = re.compile(r"^(\S+) · (.+) \(([^()]+)\)$")
FAVICON = (
    "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'>"
    "<rect width='16' height='16' fill='%231e1e2e'/>"
    "<text x='3' y='13' font-size='13' fill='%23fab387' font-family='monospace'>%E2%9D%AF</text></svg>"
)


def load(path=ROOT / "resume.json"):
    return json.loads(Path(path).read_text())


def h(s):
    return html.escape(s or "", quote=True)


def text(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()


def items(resume, section):
    sec = resume["sections"].get(section) or {}
    if sec.get("hidden"):
        return []
    return [i for i in sec.get("items", []) if not i.get("hidden")]


def bullets(desc):
    return [text(li) for li in re.findall(r"<li>(.*?)</li>", desc or "", re.S)]


def patches(resume):
    oss = next((p for p in items(resume, "projects") if p["name"] == "Open Source"), None)
    if not oss:
        return []
    return [m.groups() for b in bullets(oss["description"]) if (m := PATCH.match(b))]


def links(resume):
    b = resume["basics"]
    out = {"email": "mailto:" + b["email"], "resume": "/resume", "keys": "/cwel.asc"}
    for f in b.get("customFields", []):
        if "github" in f.get("icon", ""):
            out["github"] = f["link"]
        if "linkedin" in f.get("icon", ""):
            out["linkedin"] = f["link"]
    return out


PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="icon" href="{favicon}">
<link rel="stylesheet" href="/style.css">
</head>
<body class="resume">
<main>
{body}
<p class="meta nav"><a href="/">~</a> · <a href="/resume.pdf">pdf</a></p>
</main>
</body>
</html>
"""


def _link(name, site):
    u = (site or {}).get("url")
    return f'<a href="{h(u)}">{h(name)}</a>' if u else h(name)


def _ul(desc):
    bs = bullets(desc)
    if bs:
        return "<ul>" + "".join(f"<li>{h(x)}</li>" for x in bs) + "</ul>"
    t = text(desc)
    return f"<p>{h(t)}</p>" if t else ""


def resume_html(resume):
    b = resume["basics"]
    L = links(resume)
    contacts = [("email", L["email"]), ("github", L.get("github")), ("linkedin", L.get("linkedin"))]
    head = (
        f'<header><h1>{h(b["name"])}</h1>'
        f'<p class="meta">{h(b["headline"])} · {h(b["location"])}</p>'
        '<p class="meta">' + " · ".join(f'<a href="{h(u)}">{n}</a>' for n, u in contacts if u) + "</p></header>"
    )
    parts = []
    s = resume.get("summary") or {}
    if s.get("content") and not s.get("hidden"):
        parts.append(f'<section><h2>Summary</h2><p>{h(text(s["content"]))}</p></section>')
    exp = items(resume, "experience")
    if exp:
        parts.append("<section><h2>Experience</h2>" + "".join(
            f'<article><h3>{h(e["position"])}</h3><p class="meta">{_link(e["company"], e.get("website"))} · {h(e["period"])}'
            + (f' · {h(e["location"])}' if e.get("location") else "")
            + f'</p>{_ul(e.get("description"))}</article>' for e in exp) + "</section>")
    pr = items(resume, "projects")
    if pr:
        parts.append("<section><h2>Projects</h2>" + "".join(
            f'<article><h3>{_link(p["name"], p.get("website"))}</h3>{_ul(p.get("description"))}</article>' for p in pr) + "</section>")
    sk = items(resume, "skills")
    if sk:
        parts.append("<section><h2>Skills</h2><dl>" + "".join(
            f'<dt>{h(k["name"])}</dt><dd>{h(", ".join(k.get("keywords") or []))}</dd>' for k in sk) + "</dl></section>")
    ce = items(resume, "certifications")
    if ce:
        parts.append("<section><h2>Certifications</h2><ul>" + "".join(
            f'<li>{_link(c["issuer"] + " " + c["title"], c.get("website"))} · {h(c["date"])}</li>' for c in ce) + "</ul></section>")
    ed = items(resume, "education")
    if ed:
        parts.append("<section><h2>Education</h2>" + "".join(
            f'<article><h3>{h(e["area"])}</h3><p class="meta">{_link(e["school"], e.get("website"))} · {h(e["period"])}</p></article>' for e in ed) + "</section>")
    return PAGE.format(title=h(b["name"]) + " resume", favicon=FAVICON, body=head + "".join(parts))
