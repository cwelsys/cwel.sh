#!/usr/bin/env python3
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
OUT = ROOT / "public"
LS = ["about", "resume", "github", "linkedin", "email", "keys"]
STRIP = re.compile(r"\x1b\[[0-9;]*m")
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


def custom(resume):
    return [s for s in resume.get("customSections", []) if not s.get("hidden")]


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
<link rel="stylesheet" href="../style.css">
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


def _row(title, period, meta):
    return f'<div class="row"><h3>{title}</h3><span class="meta">{h(period)}</span></div><p class="meta">{meta}</p>'


def resume_html(resume):
    b = resume["basics"]
    L = links(resume)
    contacts = [("email", L["email"]), ("github", L.get("github")), ("linkedin", L.get("linkedin"))]
    head = (
        f'<header><h1>{h(b["name"])}</h1>'
        f'<p class="meta">{h(b["headline"])} · {h(b["location"])} · '
        + " · ".join(f'<a href="{h(u)}">{n}</a>' for n, u in contacts if u) + "</p></header>"
    )
    parts = []
    s = resume.get("summary") or {}
    if s.get("content") and not s.get("hidden"):
        paras = [t for t in (text(x) for x in re.split(r"</p>|<br\s*/?>", s["content"])) if t]
        parts.append('<section><h2>Summary</h2>' + "".join(f'<p class="line">{h(t)}</p>' for t in paras) + "</section>")
    exp = items(resume, "experience")
    if exp:
        parts.append("<section><h2>Experience</h2>" + "".join(
            "<article>" + _row(h(e["position"]), e["period"], _link(e["company"], e.get("website"))
                                + (f' · {h(e["location"])}' if e.get("location") else ""))
            + f'{_ul(e.get("description"))}</article>' for e in exp) + "</section>")
    for sec in custom(resume):
        its = [i for i in sec.get("items", []) if not i.get("hidden")]
        if its:
            parts.append(f'<section><h2>{h(sec["title"])}</h2><dl>' + "".join(
                f'<dt>{_link(i["name"], i.get("website"))}</dt><dd>{h(text(i.get("description")))}</dd>' for i in its) + "</dl></section>")
    pr = items(resume, "projects")
    if pr:
        parts.append("<section><h2>Projects</h2>" + "".join(
            f'<p class="item"><b>{_link(p["name"], p.get("website"))}</b> {h(text(p.get("description")))}</p>' for p in pr) + "</section>")
    sk = items(resume, "skills")
    if sk:
        parts.append("<section><h2>Skills</h2><dl>" + "".join(
            f'<dt>{h(k["name"])}</dt><dd>{h(", ".join(k.get("keywords") or []))}</dd>' for k in sk) + "</dl></section>")
    ce = items(resume, "certifications")
    if ce:
        parts.append("<section><h2>Certifications</h2><p>" + " · ".join(
            f'{_link(c["issuer"] + " " + c["title"], c.get("website"))} ({h(c["date"])})' for c in ce) + "</p></section>")
    ed = items(resume, "education")
    if ed:
        parts.append("<section><h2>Education</h2>" + "".join(
            f'<p class="item"><b>{h(e["area"])}</b> {_link(e["school"], e.get("website"))} · {h(e["period"])}</p>' for e in ed) + "</section>")
    return PAGE.format(title=h(b["name"]) + " resume", favicon=FAVICON, body=head + "".join(parts))


ANSI = {
    "blue": "38;2;137;180;250", "peach": "38;2;250;179;135", "green": "38;2;166;227;161",
    "yellow": "38;2;249;226;175", "mauve": "38;2;203;166;247", "dim": "38;2;108;112;134",
}


def ansi(color, s):
    return f"\x1b[{ANSI[color]}m{s}\x1b[0m"


def man_text(root=ROOT):
    env = {**os.environ, "GROFF_NO_SGR": "1"}
    g = subprocess.run(["groff", "-mandoc", "-Tascii", "-rLL=78n", "-rHY=0", "-dAD=l", str(root / "cwel.1")],
                       capture_output=True, text=True, check=True, env=env)
    c = subprocess.run(["col", "-bx"], input=g.stdout, capture_output=True, text=True, check=True)
    return c.stdout.strip("\n")


def _is_section(line):
    return re.fullmatch(r"[A-Z][A-Z ]+", line) is not None


def man_html(man):
    out = []
    for line in man.splitlines():
        e = h(line)
        if _is_section(line):
            e = f'<span class="y">{e}</span>'
        elif "CWEL(1)" in line:
            e = f'<span class="k">{e}</span>'
        e = re.sub(r"(https?://[^\s,]+)", r'<a href="\1">\1</a>', e)
        e = re.sub(r"(?<![\w/])([\w.+-]+@[\w-]+\.[\w.]+)", r'<a href="mailto:\1">\1</a>', e)
        out.append(e)
    return "\n".join(out)


def man_txt(man):
    out = []
    for line in man.splitlines():
        if _is_section(line):
            line = ansi("yellow", line)
        elif "CWEL(1)" in line:
            line = ansi("mauve", line)
        out.append(line)
    return "\n".join(out)


def ls_html(resume):
    L = links(resume)
    return "  ".join(f'<a href="{h(L[n])}">{n}</a>' if n in L else n for n in LS)


def about_text(index_html):
    m = re.search(r'<pre id="about">(.*?)</pre>', index_html, re.S)
    return text(m.group(1)) if m else ""


def index_txt(resume, about, man):
    L = links(resume)
    P = f'{ansi("blue", "~")} {ansi("peach", "❯")}'
    ls = "  ".join(ansi("blue", n) if n in L else n for n in LS)
    return "\n".join([
        f"{P} cat about", about, "",
        f"{P} ls", ls, "",
        f"{P} man cwel", man_txt(man), "",
        f"{P} ",
        "resume:   https://cwel.sh/resume",
        "pdf:      https://cwel.sh/resume.pdf",
        "man:      curl -s cwel.sh/cwel.1 | man -l -",
        f"github:   {L['github']}",
        f"linkedin: {L['linkedin']}",
        "",
    ])


def zb32(data):
    alphabet = "ybndrfg8ejkmcpqxot1uwisza345h769"
    bits = "".join(f"{b:08b}" for b in data)
    return "".join(alphabet[int(bits[i:i + 5].ljust(5, "0"), 2)] for i in range(0, len(bits), 5))


def write_keys(out, email, root=ROOT):
    asc = root / "cwel.asc"
    shutil.copy(asc, out / "cwel.asc")
    local, domain = email.lower().split("@")
    name = zb32(hashlib.sha1(local.encode()).digest())
    binary = subprocess.run(["gpg", "--dearmor"], input=asc.read_bytes(), capture_output=True, check=True).stdout
    for base in (out / ".well-known" / "openpgpkey", out / ".well-known" / "openpgpkey" / domain):
        (base / "hu").mkdir(parents=True)
        (base / "policy").write_text("")
        (base / "hu" / name).write_bytes(binary)


def build(out=OUT, root=ROOT):
    src = root / "src"
    resume = load(root / "resume.json") if (root / "resume.json").exists() else load()
    if out.exists():
        shutil.rmtree(out)
    (out / "resume").mkdir(parents=True)
    for f in ("style.css", "shell.js", "404.html", "_headers"):
        shutil.copy(src / f, out / f)
    shutil.copy(root / "cwel.1", out / "cwel.1")
    man = man_text(root)
    index = (src / "index.html").read_text()
    page = index.replace("{{ls}}", ls_html(resume)).replace("{{man}}", man_html(man))
    (out / "index.html").write_text(page)
    (out / "index.txt").write_text(index_txt(resume, about_text(index), man))
    (out / "resume" / "index.html").write_text(resume_html(resume))
    write_keys(out, resume["basics"]["email"], root)


if __name__ == "__main__":
    build()
    print(f"built {OUT}", file=sys.stderr)
