import json
import posixpath
import re
import shutil
import tempfile
from pathlib import Path

import build

resume = build.load()

assert len(build.items(resume, "experience")) >= 1
assert build.bullets("<ul><li><p>a</p></li><li>b &amp; c</li></ul>") == ["a", "b & c"]

oss = [s for s in build.custom(resume) if s["title"] == "Open Source"]
assert len(oss) == 1 and len(oss[0]["items"]) >= 5
assert all(i["website"]["url"].startswith("https://") for i in oss[0]["items"])

L = build.links(resume)
assert L["github"].startswith("https://github.com/")
assert L["linkedin"].startswith("https://www.linkedin.com/")
assert L["email"].startswith("mailto:")

page = build.resume_html(resume)
assert resume["basics"]["name"] in page
assert not resume["basics"]["phone"], "phone must stay out of the public repo"
assert "<p>" not in page.split("<ul>")[1].split("</ul>")[0]
assert "<h2>Open Source</h2>" in page and page.index("<h2>Open Source</h2>") < page.index("<h2>Projects</h2>")
assert 'href="https://github.com/kovidgoyal/kitty/pull/10094">kitty</a>' in page
assert "Owner" in page and "Registered Apprenticeship" not in page
assert page.count('<div class="row">') == len(build.items(resume, "experience")) + len(build.items(resume, "education"))

r = json.loads(json.dumps(resume))
r["sections"]["experience"]["items"][0]["hidden"] = True
assert r["sections"]["experience"]["items"][0]["position"] not in build.resume_html(r)
r["sections"]["certifications"]["hidden"] = True
assert "Certifications" not in build.resume_html(r)

with tempfile.TemporaryDirectory() as d:
    root = Path(d)
    (root / "src").mkdir()
    for f in ("style.css", "shell.js", "logos.js", "nf.woff2", "braille.woff2", "favicon.svg", "404.html", "_headers"):
        src = build.SRC / f
        (root / "src" / f).write_bytes(src.read_bytes() if src.exists() else b"")
    idx = build.SRC / "index.html"
    (root / "src" / "index.html").write_text(idx.read_text() if idx.exists() else
        '<pre id="login">{{login}} from localhost</pre><pre id="about">x &amp; y</pre><pre id="ls">{{ls}}</pre>{{man}}')
    shutil.copy(build.ROOT / "cwel.1", root / "cwel.1")
    shutil.copy(build.ROOT / "cwel.asc", root / "cwel.asc")
    out = root / "public"
    build.build(out, root=root)
    files = {p.relative_to(out).as_posix(): p for p in out.rglob("*") if p.is_file()}
    for f in ("index.html", "index.txt", "resume/index.html", "cwel.1", "_headers", "404.html", "style.css", "shell.js", "logos.js", "nf.woff2", "braille.woff2", "favicon.svg", "cwel.asc", ".well-known/openpgpkey/policy"):
        assert f in files, f
    assert len([f for f in files if f.startswith(".well-known/openpgpkey/hu/")]) == 1
    domain = resume["basics"]["email"].split("@")[1]
    assert f".well-known/openpgpkey/{domain}/policy" in files
    direct = [f for f in files if f.startswith(".well-known/openpgpkey/hu/")][0]
    assert direct.replace("openpgpkey/hu/", f"openpgpkey/{domain}/hu/") in files
    phone = resume["basics"]["phone"]
    if phone:
        for p in files.values():
            assert phone not in p.read_bytes().decode("utf-8", "ignore"), p
    for page in ("index.html", "resume/index.html"):
        for href in set(re.findall(r'href="([^"#]+)"', files[page].read_text())):
            if href.startswith(("http", "mailto:", "data:")):
                continue
            t = posixpath.normpath(posixpath.join(posixpath.dirname(page), href)) if not href.startswith("/") else href.lstrip("/")
            t = t or "index.html"
            assert t in files or t + "/index.html" in files or t == "resume.pdf", (page, href)
    txt = files["index.txt"].read_text()
    for line in txt.splitlines():
        assert len(build.STRIP.sub("", line)) <= 80, line
    assert "NAME" in txt and "SEE ALSO" in txt
    assert build.about_text((root / "src" / "index.html").read_text()) in txt
    assert build.about_text('<pre id="about">x &amp; y</pre>') == "x & y"
    assert "cat patches" not in txt and "keys" not in txt
    assert "Last login: " in txt and "from localhost" in txt
    html = files["index.html"].read_text()
    assert "from localhost" in html and 'href="/cwel.asc">pgp</a>' in html and ">dotfiles</a>" in html
    assert "{{" not in html and "{{" not in txt
    assert re.search(r'data-built="\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ"', html)
    assert "\u2014" not in txt

js = (build.SRC / "shell.js").read_text()
assert js.count("__proto__: null") == 3, "cmds, files and links must have null prototypes"

css = (build.SRC / "style.css").read_text()
tokens = dict(re.findall(r"--(\w+): (#[0-9a-f]{6})", css))


def lum(hexc):
    c = [int(hexc[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def contrast(a, b):
    la, lb = lum(tokens[a]), lum(tokens[b])
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


for sel, tok in re.findall(r"\n(\.\w+) \{ color: var\(--(\w+)\); \}", css):
    assert contrast(tok, "base") >= 4.5, (sel, tok, round(contrast(tok, "base"), 2))

for f in ("build.py", "test_build.py", "cwel.1", "Makefile", "src/index.html", "src/style.css", "src/shell.js", "src/404.html", "functions/index.js", ".github/workflows/deploy.yml"):
    assert "\u2014" not in (build.ROOT / f).read_text(), f

print("ok")

headers = (build.SRC / "_headers").read_text()
for asset in ("/shell.js", "/logos.js", "/style.css"):
    assert re.search(rf"^{re.escape(asset)}\n  Cache-Control: public, max-age=0, must-revalidate", headers, re.M), asset
