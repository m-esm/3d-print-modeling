# Front door for a 3D-print project (see the 3d-print-modeling skill's "Project layout").
# All Python lives in src/; outputs route into stl/<subsystem>/ and web/. Run `make help`.
PORT ?= 8765

.PHONY: help install build export viewer shot all

help:                ## List targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN{FS=":.*?## "}{printf "  make %-10s %s\n", $$1, $$2}'

install:             ## Install the build toolchain + headless browser
	python3 -m pip install -r requirements.txt
	python3 -m playwright install chromium

build:               ## Rebuild every STL + web/assembly.glb (source of truth: src/build.py)
	python3 src/build.py

export:              ## Write sliceable Bambu .3mf plates into exports/
	python3 src/export_bambu.py

viewer:              ## Serve the live viewer (auto-reloads on rebuild; override with PORT=)
	python3 src/serve.py $(PORT)

shot:                ## Headless multi-angle render to .claude/renders/ (needs `make viewer` running)
	python3 src/shoot.py assembly.glb chk $(PORT)

all: build export    ## Rebuild all parts + Bambu plates

# Add one target per extra subsystem script, e.g.:
# keypad:            ## Rebuild the rotary keypad parts
# 	python3 src/build_rotary_keypad.py
