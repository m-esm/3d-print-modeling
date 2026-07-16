# CSG robustness: the trimesh/manifold3d boolean playbook

Boolean artifacts are the #1 pure-geometry time sink: phantom "windows" in housings,
half-circle slivers around screw pockets, wall "fins" hanging off lids, sealed voids where
cavities should connect, and "Not all meshes are volumes!" storms (318 watertight failures
logged in one project). This is the playbook distilled from what actually fixed them.

## Prevention

- **One boolean call, many operands.** `difference(base, [c1, c2, ...])` /
  `union([a, b, c])` in a single call is dramatically more robust than chaining
  `base - c1 - c2 - ...`. A sequential per-ear subtraction produced corrupt geometry the
  single-call version didn't. manifold re-canonicalizes once instead of accumulating
  near-degenerate intermediates.
- **Do the thinking in 2D (shapely), extrude late.** 2D polygon ops are exact and
  debuggable; 3D boolean surgery on the result is where artifacts breed. When a 2D clip
  region leaks arcs into the extrusion (the "half circles everywhere" bug: a circular
  clip boundary contaminating ear outlines), **morphological close** the polygon first:
  `poly.buffer(+w).buffer(-w)` removes boundary slivers below width `w`.
- **Coincident geometry is the enemy.** Faces, edges, or vertices that exactly touch
  (gear tooth feet on a root circle, a cutter flush with a wall) generate zero-thickness
  shards. Jitter one operand by 0.01 mm (`buffer(0.01).buffer(-0.01)` in 2D, or oversize
  a cutter 0.1 mm past the face it exits) so nothing is exactly coplanar.
- **Cutters must fully pierce.** A subtraction whose cutter ends exactly at a surface
  leaves a membrane. Extend cutters well past both faces.
- **A cutter can erase a smaller positive.** `difference` after `union` deletes any
  feature that lives inside the cut volume (a collar smaller than the port hole being
  subtracted vanished entirely). Order: cut the openings first, then union small external
  features, or exclude the feature's volume from the cutter.

## Diagnosis, when a boolean output is wrong anyway

- `mesh.is_volume` per INPUT, not just the output. manifold throws "Not all meshes are
  volumes!" naming neither operand; bisect by checking each input.
- `mesh.split(only_watertight=False)` on the output: an artifact usually shows up as
  extra small bodies (a "1882-body" part happened). Keeping `max(bodies, key=volume)` is
  a legitimate last-resort cleanup for known-good outer shells, but treat it as a bandage
  and find the coincident geometry that produced the shards.
- A parameter change that "tips a fragile boolean into non-watertight" (bezel overlap
  3.5 -> 1.5 broke a build) means two features started sharing a face at the new value.
  Don't hunt the magic number; jitter or restructure the operands.
- When an artifact resists two fix attempts, stop tweaking offsets and re-derive the 2D
  outline; research agents found root causes in the profile construction both times this
  happened.

## The deeper fix: stop hand-rolling BREP problems in mesh land

The skill already says it, and no project has done it yet, so here is the on-ramp. For
NEW parametric parts with fillets/chamfers/threads, build123d avoids the entire artifact
class above (true solids, exact booleans):

```bash
python3.11 -m venv .venv && .venv/bin/pip install build123d bd_warehouse
```
```python
from build123d import *          # needs Python >= 3.10
with BuildPart() as p:
    Box(40, 30, 12)
    with Locations((0, 0, 6)):   # pocket, filleted, exact
        Box(30, 20, 8, mode=Mode.SUBTRACT)
    fillet(p.edges().filter_by(Axis.Z), 2)
export_stl(p.part, "part.stl")   # then the normal viewer/shoot loop applies unchanged
```
Keep trimesh+manifold for mesh inputs (downloaded STLs, scan surgery) and as the boolean
engine of last resort. The viewer/verify loop is identical either way.

## Iteration speed: don't rebuild the world per tweak

100+ full `build.py` runs per session is normal; make each run cheap:

- **Cache expensive imports.** An 85 MB STEP re-tessellated on every build made sweeps
  "too slow to run". Hash the source file, cache the tessellated mesh
  (`.claude/cache/<sha>.npz` or pickle), load instead of re-importing.
- **`PREVIEW=1` mode**: lower `n_theta`/segment counts, skip STL export (GLB only), skip
  the heaviest decorative parts. Full resolution only for `EXPORT=1`. Threaded parts at
  preview resolution are ~10x fewer faces and visually identical in the viewer.
- **Per-part rebuild targets** (`make housing`), so a housing tweak doesn't regenerate
  gears.
- **Placement/parameter sweeps against a coarse proxy.** Optimize against a decimated or
  voxel-remeshed skin (~5x faster per evaluation), then validate the winner against the
  full-res mesh (see `wallcheck.py`). Precompute anything reused across evaluations
  (centerline lookup tables); a sweep that recomputes a centerline per point earns a kill.
- Long sweeps: run foregrounded with progress prints and unbuffered output
  (`python3 -u`), not backgrounded-and-polled; buffered background jobs look hung, invite
  duplicate launches ("three duplicate sweeps competing"), and time out monitors.


## trimesh's boolean wrapper injects phantom geometry (desk-pi, 2026-07-14)

On complex meshes, `trimesh.boolean.union/difference/intersection(engine="manifold")`
(trimesh 4.12) can HALLUCINATE material neither input has: an intersection grew a
0.2 mm bulge on a rib face; a compound union of overlapping coplanar boxes grew
150 mm3 inside a probe window its inputs couldn't fill. The same operands through
manifold3d's own API came out exact. Rules that ended it:

- Call manifold3d DIRECTLY (f32 `Mesh`; rewrap with `Trimesh(..., process=False)`).
  The f64 `Mesh64` path produced its own artifacts on this trimesh/manifold combo.
- Never union many overlapping coplanar volumes in one call. Build capture regions
  as ONE shapely 2D `unary_union` extruded once; union added bodies PAIRWISE.
- `trimesh.contains()` is ray-parity and LIES near coincident faces. Probe with a
  manifold cube intersection instead: `(Manifold(mesh) ^ cube_at_point).volume()`.
- Boolean facet residue owns the last ~0.02 mm3: keep placeholder-to-part design
  clearances >= 0.3, and expect zero-thickness sheets where a cut plane lies
  exactly on an open face (shave 1 micron with a capped slice).
- Silent tooling corollary: `str.replace` edits without an assert and gates run
  through `| tail` (exit code masked) let two of these "fixes" no-op unnoticed.
