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

p = build.patches(resume)
assert len(p) >= 1 and all(len(t) == 3 for t in p), p
assert not any(n.startswith("More") for n, _, _ in p)
assert any(l == "C++" for _, _, l in p)

L = build.links(resume)
assert L["github"].startswith("https://github.com/")
assert L["linkedin"].startswith("https://www.linkedin.com/")
assert L["email"].startswith("mailto:")

page = build.resume_html(resume)
assert resume["basics"]["name"] in page
assert resume["basics"]["phone"] not in page
assert "<p>" not in page.split("<ul>")[1].split("</ul>")[0]

r = json.loads(json.dumps(resume))
r["sections"]["experience"]["items"][0]["hidden"] = True
assert r["sections"]["experience"]["items"][0]["position"] not in build.resume_html(r)
r["sections"]["certifications"]["hidden"] = True
assert "Certifications" not in build.resume_html(r)

with tempfile.TemporaryDirectory() as d:
    root = Path(d)
    (root / "src").mkdir()
    for f in ("style.css", "shell.js", "404.html", "_headers"):
        src = build.SRC / f
        (root / "src" / f).write_text(src.read_text() if src.exists() else "")
    idx = build.SRC / "index.html"
    (root / "src" / "index.html").write_text(idx.read_text() if idx.exists() else
        '<pre id="about">x &amp; y</pre><pre id="ls">{{ls}}</pre>{{patches}}{{man}}')
    shutil.copy(build.ROOT / "cwel.1", root / "cwel.1")
    shutil.copy(build.ROOT / "cwel.asc", root / "cwel.asc")
    out = root / "public"
    build.build(out, root=root)
    files = {p.relative_to(out).as_posix(): p for p in out.rglob("*") if p.is_file()}
    for f in ("index.html", "index.txt", "resume/index.html", "cwel.1", "_headers", "404.html", "style.css", "shell.js", "cwel.asc", ".well-known/openpgpkey/policy"):
        assert f in files, f
    assert len([f for f in files if f.startswith(".well-known/openpgpkey/hu/")]) == 1
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
    assert "cat patches" in txt
    assert "—" not in txt

print("ok")
