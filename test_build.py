import json
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

print("ok")
