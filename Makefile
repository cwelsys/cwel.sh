PY = python3
CHROME ?= chromium
OUT = public

build:
	$(PY) build.py

check:
	$(PY) test_build.py

pdf: build
	$(CHROME) --headless=new --no-sandbox --disable-gpu --no-pdf-header-footer \
	  --print-to-pdf=$(OUT)/resume.pdf file://$(CURDIR)/$(OUT)/resume/index.html

serve: build
	$(PY) -m http.server -d $(OUT) 8000

clean:
	rm -rf $(OUT)

.PHONY: build check pdf serve clean
