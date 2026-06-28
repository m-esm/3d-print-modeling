---
name: 3d-print-modeling
description: Author and iterate on 3D-printable parts as parametric Python (trimesh + manifold3d + shapely), then view and screenshot them headlessly to verify. Use when the user wants to design, modify, or print a mechanical part, gear/worm drive, enclosure, bracket, or any FDM/resin model, anything involving STL/3MF/GLB, build123d-style geometry, watertight CSG, or "make this part / make it bigger / make it printable". Covers the view-screenshot-iterate loop and FDM design rules. For Bambu .3mf slicer export see the bambu-3mf-export skill; for importing STEP/IGES/foreign CAD see foreign-cad-import.
---

# 3D-print modeling (Python-parametric, view-driven)

This is the workflow distilled from a series of FDM projects (worm-gear door drive, window
blind coupler, vortex shower head, tripod, turntable mount). The throughline: **geometry is
generated parametrically in Python, viewed in a browser, screenshotted headlessly, and
checked by eye on every change.** No GUI CAD (OpenSCAD/FreeCAD/Fusion) is needed, the geometry
engine is pip-installable Python: `build123d`/`CadQuery` (BREP) for new parts, `trimesh`+`manifold3d`
for meshes. See "Pick the engine first" below.

## The non-negotiable loop

1. **`build.py` is the single source of truth.** Put a `PARAMETERS` block at the top with
   every tunable + a one-line comment on *why* each value is what it is. Edit params, rerun,
   never hand-edit the mesh output.
2. **After every geometry change: rebuild, then LOOK at the render from multiple angles.**
   This is the non-negotiable verification step, not optional polish. Numeric and watertight
   checks miss the bugs that actually bite, wrong orientation, parts floating, collisions,
   holes not piercing, features distorted, a stretched-wrong axis. The drill:
   - `python3 serve.py 8765` (once), then `python3 shoot.py <model>.glb chk` after each rebuild.
   - That writes **iso / front / side / top + two section cuts** into **`.claude/renders/chk_*.png`**
     (the script always renders there, never the project root, so screenshots don't pollute the
     working dir). One angle is never enough, a part can look right head-on and be floating or
     colliding when seen from the side; the section cuts are how you confirm internal features
     (bores piercing, cavities connecting, wall thickness).
   - **Downscale, then actually Read every PNG**
     (`sips -Z 1400 .claude/renders/chk_iso.png --out .claude/renders/chk_iso_s.png`). Looking at
     the file path is not looking at the render. Read the image into the conversation and check it
     against what you intended.
   - Only then say done. If you couldn't render (no browser, no GLB), say so plainly instead of
     claiming the change works.
3. **Git checkpoint after each meaningful change.** These designs iterate fast and you want
   cheap reverts: `git add -A && git commit -m "<what changed>"`. Don't leave the tree dirty
   across iterations. (`git init` if the project isn't a repo yet.) Commit the source and the
   one current `web/assembly.glb`; gitignore renders and scratch iterations. See **Project layout**
   below for the exact commit-vs-ignore rule, it's the line the dual-axis-turntable got wrong
   (every `_t_*.glb`/`.3mf` iteration tracked at the repo root until it was unreadable).
4. **Keep a project `CLAUDE.md`** that records the mechanical intent, key numbers (and the
   tradeoff behind each), print orientation, and every hard-won gotcha. The next session reads
   it first. Update it as decisions land, don't wait for the end.

## Project layout (set this up before modeling, not after)

Every multi-part project here converged on the same shape. **finnish-doors is the reference layout,
copy it.** Retrofitting organization onto a littered root (the dual-axis-turntable's actual state:
loose `_t_*.glb`, `bambu_*.3mf`, and STLs all at top level) is the tax you pay for skipping this.
The discipline: **all Python in `src/`, output routed into `stl/<subsystem>/`, the live assembly in
`web/`, a `Makefile` as the front door, and `requirements.txt` pinned.**

```
project/
├── CLAUDE.md           mechanical intent, key numbers + the tradeoff behind each, print
│                       orientation, every gotcha. Read first each session; update as you go.
├── Makefile            the front door: make build / export / viewer / shot / all. Self-
│                       documenting via `## ` comments; a new session runs `make help` first.
├── README.md           one paragraph: what it is + how to build.
├── requirements.txt    PINNED deps (trimesh + manifold3d as a pair). `make install` runs it.
├── .gitignore          see "what to commit" below.
├── docs/               ASSEMBLY.md (BOM, which part on which plate, assembly order), motor/
│                       bearing datasheets, one reference Bambu .3mf for the profile template.
├── src/                ALL Python, run from repo root (`python3 src/build.py`):
│   ├── build.py          source of truth, PARAMETERS block at top
│   ├── build_<sub>.py    one per independent subsystem (keypad, conduit, ...), standalone
│   ├── stlpaths.py       routes stlp("worm.stl") -> stl/drive/worm.stl by name prefix
│   ├── export_bambu.py   packs parts onto plates, writes sliceable .3mf (bambu-3mf-export skill)
│   ├── bambu3mf.py        the .3mf writer
│   ├── serve.py          localhost viewer server
│   └── shoot.py          headless multi-angle renders -> .claude/renders/
├── stl/<subsystem>/    organized output: drive/, housing/, keypad/, ... (routed by stlpaths.py)
├── web/                viewer_glb.html + assembly.glb + assembly_dims.json. serve.py serves THIS
│                       dir (so the viewer is at /, the model at /assembly.glb); auto-reloads on rebuild.
├── exports/            Bambu .3mf plates, one per profile/material group.
└── firmware/           only if the project has electronics: the sketch + WIRING.md (pin map,
                        driver wiring, calibration constants). See dual-axis-turntable.
```

**`stlpaths.py` is the small piece that keeps the root clean.** Writers and readers both call
`stlp(name)`, which routes a bare filename to `stl/<subsystem>/name` by a prefix rule
(`worm_*`→drive, `housing_*`→housing). One rule, so the build, the assembly loader, and the Bambu
export stay in sync and nothing lands at the root. Bundled in `scripts/stlpaths.py`.

**The Makefile is the front door.** Targets seen across projects: `build` (rebuild all STLs +
`web/assembly.glb`), `export` (write Bambu plates), `viewer` (serve), `shot` (headless render),
`install`, `all`. End each target line with a trailing `## comment` so `make help` lists them.
A subsystem with its own script gets its own target (`make keypad` → `python3 src/build_rotary_keypad.py`).
Bundled in `scripts/Makefile`.

**Conditional builds via env vars, not commented-out code.** dual-axis-turntable drives one
`build.py` with `EXPORT=1` (write STLs, else just the GLB for the viewer), `SHELL=0`, `TILT=45`
(preview tilt clearance at 45°), `NOZZLE08=1`. Clean way to get preview/variant modes out of a
single source of truth without forking the file.

**What to commit vs ignore** (the line the turntable got wrong):
- **Commit:** `src/`, `stl/`, `web/assembly.glb` + `web/assembly_dims.json`, `docs/`, `CLAUDE.md`,
  `Makefile`, `requirements.txt`. Committing the current `assembly.glb` means a fresh clone shows
  the part in the viewer with no rebuild, and you get a visual diff history.
- **Ignore:** `.claude/renders/`, scratch/iteration GLBs (`_t_*`, `_test_*`), `exports/*.3mf`
  (regenerable), videos (`*.mp4 *.mov *.avi`), `__pycache__/`. Minimum `.gitignore`:
  ```
  .claude/renders/
  _t_*
  _test_*
  exports/*.3mf
  *.mp4
  *.mov
  __pycache__/
  ```
  The anti-pattern: tracking every `_t_*.glb`/`.3mf` iteration at the repo root. It works, but the
  root becomes unreadable. Route outputs into `stl/` + `exports/` and ignore the scratch.

### Variants on the layout

- **Single quick part:** skip `src/`, just `build.py` + the bundled scripts at root. Graduate to the
  full layout the moment a second part appears.
- **Part-by-part** (user drives one part at a time: "now a bolt", "now a nut that fits it"):
  `build_all.py` at root discovers `parts/*.py` via importlib, each module defining `build() ->
  trimesh mesh`; shared helpers in `lib.py` (`save(mesh,name) -> stl/<name>.stl`, plus reusable
  generators like `threaded_rod(major_d,pitch,length)` feeding both the bolt and the nut). Keep
  `lib.py` + `build_all.py` at the ROOT (parts do `from lib import ...`; moving lib breaks that);
  scripts in `tools/` compute ROOT from `__file__` so they run from anywhere.
- **Foreign-CAD-centric** (you start from a downloaded STEP, not parametric source): `cad/` holds
  the STEP, `parts/<subassembly>/` holds pre-exported STLs grouped by subassembly with design
  iterations kept side by side (`Spool_V1/`, `Spool_V2/`), `tools/` holds the import/analysis
  scripts. This is the finnish-windows shape; see the **foreign-cad-import** skill for the gmsh
  tessellation + OCP hole/screw-BOM pipeline.

## Generating a parts KIT (multi-agent fan-out)

When the user wants MANY independent parts at once ("add connectors and function parts",
"a family of bolt variants"), and they've opted into multi-agent work, **fan out one subagent
per part, in parallel** (all Agent calls in one message). Measured on this project: 10 + 9 parts,
every one watertight on first build, ~44k tokens / ~1 min each. Rules that made it work:

- **Each agent creates ONLY its own `parts/<name>.py`** and verifies it
  (`python3 -c "from parts.<name> import build; m=build(); print(m.is_volume, ...)"`). It must NOT
  run `build_all.py`, touch `lib.py`, or edit other parts. Distinct new files = safe concurrent
  writes, no merge conflict. The orchestrator runs `build_all.py` ONCE after all agents return.
- **The speedup is SHARED HELPERS, not the agents.** Without them every agent re-derives the same
  geometry and re-types the same constants with *drifting names* (`INNER` vs `SLEEVE_IN` vs `43.0`),
  which also breaks single-source-of-truth (change the section once and 20 files silently disagree).
  So FIRST factor the common geometry + a constants block into `lib.py`
  (e.g. `SEC`, `SLEEVE_INNER`, `BORE`, `NUT_SQ` + `sleeve()`, `bolt_hole()`, `nut_pocket()`,
  `countersink()`), THEN **hand the helper API to each agent in its prompt** so they compose instead
  of invent. Drop a `parts/_template.py` (import line + helper cheat-sheet) to copy from.
- **Batch a tight family into ONE agent** when the members are variations of one parametric idea
  (corner/tee/cross = "N sleeves at a junction" → one `junction(dirs)` function), to avoid
  triplicated code. Reserve the strong model for hard geometry; trivial parts (caps, washers, plain
  blocks) are fine on a cheaper/faster model via the Agent `model` override.
- Give every agent the SAME system block (exact mm: section, clearances, thread spec) so parts
  actually interconnect; reference an existing canonical part ("copy the body of `parts/nut.py`").

## Viewer for a kit: categories + on-part labels

`parts_viewer.py` reads each part's one-line **docstring via `ast.get_docstring`** (no import) for a
description, groups the panel by a name→category map, and floats a CSS2D **name + short description
label above each part** (toggleable, like the dim labels). Keep the on-part description to the first
clause / ~44 chars single-line (full sentences wrap into tall overlapping columns); put the full
text in the side panel.

**Threaded meshes are HEAVY.** An M30 `threaded_rod` at `n_theta=96, steps_per_pitch=12` is ~99k
faces; a dozen threaded parts base64-embedded blew the self-contained viewer to 31 MB. Drop the
thread resolution (64/6 → 13 MB, still fine for both viewer and a utility-bolt print). Quadric
decimation (`simplify_quadric_decimation`) may be unavailable on system Python 3.9 (a `type | None`
type-union bug), so lowering generation resolution beats decimating after.

## Pick the engine first: BREP (build123d/CadQuery) vs mesh (trimesh)

These projects historically built everything in **trimesh** because "OpenSCAD/FreeCAD aren't
installed." That reasoning is stale, and it's worth correcting before you start a new part:

- **For NEW parametric parts, prefer a real BREP kernel: `build123d` (or `CadQuery`).** Both are
  `pip install` (they ship their own OpenCascade via the `cadquery-ocp` wheel, so NO system CAD
  install and no macOS Gatekeeper problem, which was the original blocker). They give you true
  solids with native fillets, chamfers, lofts, sweeps, and threads, and they **import AND export
  STEP** plus STL/3MF. `bd_warehouse` adds parametric gears/threads/fasteners to build123d, so you
  don't hand-roll involute math. This is far more productive than reconstructing geometry from
  triangle arrays. Caveat: needs **Python ≥3.10** (the system `python3` here is 3.9, use a newer
  interpreter or a venv). build123d and CadQuery share the OCP wrapper, so objects interchange.
- **Use trimesh + manifold3d when the input IS a mesh** (downloaded STL/3MF, mesh surgery on a part
  with no parametric source), or as the robust boolean engine on triangle soups. It's battle-tested
  and exports a named GLB straight to the viewer. It does NOT read STEP (see foreign-cad-import).
- **They compose:** model the part in build123d, export STL, then use the trimesh viewer/`shoot.py`
  loop and the FDM checks below. The view-screenshot-iterate loop is identical regardless of engine.

The rest of this skill's report/verify/print guidance is engine-agnostic. The notes below describe
the trimesh path (what these projects used); the same checks apply to build123d output.

## Toolchain (all via `pip3 install --user`, or a venv for build123d)

- **trimesh 4.12 + manifold3d**, boolean CSG (`engine="manifold"`): holes, pockets, bores,
  keyed profiles, housings. manifold3d is still the recommended robust, guaranteed-manifold CSG
  backend for Python meshes. **All boolean inputs must be watertight volumes** or manifold throws
  "Not all meshes are volumes!", check `mesh.is_volume` per part when a union/difference fails.
  **Pin the pair** (`trimesh`+`manifold3d`) together, a major manifold3d bump has broken
  `trimesh.boolean` before; upgrade them in lockstep, not piecemeal.
- **numpy**, vertex/tooth math. **shapely**, 2D profiles, then `extrude_polygon` / `revolve`
  to 3D (gear teeth, threads, revolved chambers). **scipy / networkx / rtree**, as needed for
  sections and multi-loop work.
- **trimesh exports GLB directly** with named, vertex-colored nodes, no 3MFLoader needed in
  the browser. Gear/worm tooth profiles are computed from first principles (involute wheel,
  trapezoidal thread), then fed to trimesh; CSG only does holes and housings.
- **playwright + Chromium**, headless viewer screenshots (swiftshader GL, no real GPU needed).

In the trimesh path you generate tooth/thread profiles from first principles and reach for CSG
(manifold) only for holes, pockets, and housing booleans. In build123d, prefer `bd_warehouse` for
gears/threads instead of hand-rolling them. Either way: a helical *bore* through a straight shaft
must be cut **straight**, not helical, or the shaft won't pass.

## Bundled scripts (copy into the project, they're generic)

Everything in `scripts/` is project-agnostic. Copy what you need:

- **`serve.py`**, tiny localhost static server (browsers won't fetch `.glb`/`.stl` over
  `file://`). `python3 serve.py 8765` → `http://localhost:8765/viewer_glb.html`. Sets
  `Cache-Control: no-store` and the `.glb` mime type.
- **`viewer_glb.html`**, the main Three.js (0.169, jsdelivr) GLB viewer for **multi-part
  assemblies**, and the single viewer that carries every feature the projects evolved. `?m=<file>.glb`.
  Per-part toggles (auto-built from node names), deterministic per-name colors, **ghost-outline**
  default for housing-like parts (translucent + edge lines) with a **solid** toggle, **per-part
  L/W/H axis dimension lines + labels** (the wall-shelf-clamp dimension feature, toggleable;
  X=length red, Y=width green, Z=height blue), an **explode** slider (parts fly out radially), a
  **section cut on any axis** (X/Y/Z select + slider), a **spin** toggle, a print-bed grid, Z-up,
  ACES tone mapping, and auto-reload on rebuild. Exposes `window._scene/_cam/_controls/THREE` and
  sets `window.__ready` for headless control by `shoot.py`. The dimension labels use `CSS2DRenderer`
  so they always face the camera and follow their part through explode.
- **`viewer_stl.html`**, simpler single-STL viewer for mesh-surgery work. `?file=<f>.stl&view=iso`,
  print-bed grid, axes, bbox HUD.
- **`parts_viewer.py`**, bundles every STL in a dir into ONE self-contained `parts_viewer.html`
  (base64-embedded, **no server, double-click to open**). Multi-part grid / "in place" layout,
  per-part show/hide, CAD-style **L/W/H dimension lines** on each bbox, spin/fit, and an OPTIONAL
  data-driven **assembly view** (drop an `assembly.json` of 4x4 poses next to the STLs). This is the
  viewer for the **part-by-part workflow** (many independent STLs you iterate on and want to see
  together + dimensioned); `viewer_glb.html` is for a single live-reloading assembly GLB instead.
- **`shoot.py`**, headless multi-angle renders via Playwright. `python3 shoot.py model.glb tag
  [port]` writes `.claude/renders/tag_{iso,front,side,top,sec_mid,sec_iso}.png` (always into
  `.claude/renders/`, created on demand, so renders never clutter the project root). Auto-detects
  STL vs GLB by extension. Pairs with `serve.py`.
- **`stlpaths.py`**, the subsystem router from **Project layout**. `stlp("worm.stl")` →
  `stl/drive/worm.stl` by filename prefix; `webpath()` / `exportpath()` / `rootpath()` for the
  other dirs. Drop it in `src/`, edit the `SUBSYSTEMS` prefix table per project. Keeps every export
  out of the repo root and the assembly loader + Bambu export reading the same paths the build wrote.
- **`Makefile`**, the front door (`make build / export / viewer / shot / install / all`),
  self-documenting via trailing `## ` comments (`make help` lists them). Add one target per extra
  `build_<sub>.py`.
- **`requirements.txt`**, the pinned toolchain (`trimesh>=4.12` + `manifold3d>=2.5` as a pair,
  numpy/scipy/shapely/networkx/rtree/matplotlib/playwright). `make install` runs it + `playwright
  install chromium`.

**Image cap:** renders are @2x and phone/Retina-scale captures exceed the 2000px many-image
limit, which poisons the whole session. Always downscale before reading a PNG inline:
`sips -Z 1400 .claude/renders/in.png --out .claude/renders/in_s.png` (or `-Z 1100` for the
densest scenes).

**Don't reopen the user's browser tab.** The viewer auto-reloads `assembly.glb` on rebuild
(polls Last-Modified), the user watches changes land live. `shoot.py` is a separate headless
context for *your* verification.

**Viewer gotchas baked into the templates** (carried from real breakage):
- Three.js `3MFLoader` ignores Bambu's multi-file production extension → bake to GLB instead.
- trimesh writes colors as *vertex* colors, so `material.color` is unreliable, classify parts
  by **mesh name**, not color.
- GLB normals often arrive inverted/unlit → `computeVertexNormals()` + `DoubleSide`.
- Without ACES tone mapping, raw light intensities clip to white.
- `top`/`bottom` camera views are degenerate (camera-up parallel to view dir) → on-screen axis
  orientation is arbitrary; trust `iso`/`front`/`side` for axes.
- `matplotlib` 3D (`Poly3DCollection`) has no occlusion → muddy and misleading. Use the Three.js
  viewer for anything you actually need to read.
- **Z-up the right way: `cam.up=(0,0,1)`, a `GridHelper` with `rotation.x=PI/2`, sit parts on the
  ground via `mesh.position.z = -bbox.min.z`, spin about Z.** Do NOT rotate the geometry to Three's
  default Y-up to fake it, it fights OrbitControls and renders cylinders / bores lying on their side.
- **The headless browser caches `localhost:<port>/<file>` per port.** A stale `serve.py` from a
  prior project on the same port silently serves the WRONG model (you debug geometry that's fine).
  Use a fresh unique port and `pkill -f serve.py` first whenever a render looks like someone else's part.
- **CSS2D dimension labels:** `CSS2DRenderer` + a second `.render(scene,cam)` in the loop gives crisp
  bbox L/W/H tags that always face the camera; attach them as children of the mesh so they follow it.

## Verify before "done"

- `mesh.is_watertight` and `mesh.is_winding_consistent` after every edit.
- Print a feature-size report: smallest wall / tooth tip / thread crest. **< ~0.6 mm won't print**
  (the slicer's Arachne generator smooths it away).
- For "does this hole actually pierce / does this cavity connect" use `mesh.contains()` probes
  along the **real feature axis**, a naive horizontal/planar sample misses slanted or staggered
  holes and falsely reports "no hole."
- **Then render from multiple angles and read every PNG (the iso/front/side/top + section cuts
  from `shoot.py`).** This is the step that catches what the numbers can't: watertight + correct
  measurements still hides orientation, collision, floating-part, and feature-distortion bugs.
  Treat "I looked at all the angles and they match intent" as the bar for done, not "it's watertight."

## Deeper references (read on demand)

- **`references/fdm-design-rules.md`**, print orientation, self-supporting geometry (45° roofs,
  run-outs), min feature size, support strategy, PLA vs PETG, hoop stress for pressure parts,
  warp/adhesion, the "slicer settings beat geometry hollowing" lesson.
- **`references/mechanisms-and-fits.md`**, gears/worms (module vs teeth vs lead angle), keyed
  bores + manual override, press-fits / clearances / snap vs friction joints, bearings, one-way
  clutches, motor coupling, and which of these *must* be dialed in on a test print.

## Related skills

- **bambu-3mf-export**, turn finished STLs into a real Bambu Studio `.3mf` project with print
  settings baked in (no "not from Bambu Lab" warning), FINE/FAST profile splits, support strategy.
- **foreign-cad-import**, bring in STEP/IGES/F3D you don't have parametric source for (gmsh
  tessellation → GLB), 3MF read/write gotchas, mesh surgery, BambuStudio-CLI slicing for measurement.
