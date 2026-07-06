#!/usr/bin/env python3
"""fitmap.py — pairwise FIT / FRICTION map for an assembled model (GLB with named parts).

For every pair of parts whose AABBs come within `--near` mm, sample the smaller part's
surface and take signed distances into the other. Emits fit_report.json:

    [{"a": "ring_gear", "b": "planet_a",
      "mm": 0.18,            # + = min clearance, − = press/interference depth
      "press": false,
      "at": [x, y, z],       # the closest-approach sample point
      "patch": [[x,y,z,d]]}] # every sample within --patch mm of the other part, with its
                             # own clearance — a point cloud tracing the SHAPE of the
                             # contact area (a rib line, a bore ring, gear-flank stripes)

The companion viewer (viewer_glb.html) renders fit_report.json as a "Fits" panel: rows
sorted tightest-first plus color-coded 3D contact patches (red press / amber <0.15 /
yellow <0.4 / green free), click a row to isolate one pair.

WHY THIS EXISTS (each clause a real shipped failure):
 - Boolean "no overlap" proves parts don't collide, NOT that they aren't PRESSED: a ring
   gear passed every interference check while its planets sat at 0.00° backlash (seized).
   Only a clearance MEASUREMENT distinguishes a free fit from a bind.
 - Pair enumeration is automatic, so it checks pairs you didn't think to check: its first
   run on a real assembly caught 3 defects hand-picked boolean checks had missed (a motor
   nose boss pressing into a gear hub, a gearbox axle pin stabbing a planet, a cage arc
   buried in the OTHER housing half — nobody had booleaned against the lid).
 - Designed press fits show up as PRESS rows — assert them, and treat any OTHER press row
   as a bug (like assembly_check.py's --allow whitelist).

Usage:
    python3 fitmap.py assembly.glb [-o fit_report.json] [--near 2.5] [--patch 0.6]
                      [--samples 2600] [--skip door battery] [--far 2.0]
"""
import argparse, json, sys
import numpy as np
import trimesh


def placed_meshes(path, skip=()):
    """name -> world-transformed mesh, from a GLB scene (or a single mesh file)."""
    loaded = trimesh.load(path)
    out = {}
    if isinstance(loaded, trimesh.Scene):
        for node in loaded.graph.nodes_geometry:
            T, gname = loaded.graph[node]
            name = node if node else gname
            if any(k in name.lower() for k in skip):
                continue
            m = loaded.geometry[gname].copy()
            m.apply_transform(T)
            out[name] = m
    else:
        out[path] = loaded
    return out


def fit_map(meshes, near=2.5, patch_band=0.6, samples=2600, far=2.0, seed=0, max_patch=260):
    names = sorted(meshes)
    rows = []
    rng = np.random.default_rng(seed)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = meshes[names[i]], meshes[names[j]]
            lo = np.maximum(a.bounds[0], b.bounds[0])
            hi = np.minimum(a.bounds[1], b.bounds[1])
            if np.any(lo - hi > near):
                continue                                   # AABBs further apart than `near`
            small, big = (a, b) if a.area <= b.area else (b, a)
            try:
                pts, _ = trimesh.sample.sample_surface(small, samples)
                d = trimesh.proximity.signed_distance(big, pts)   # >0 = inside `big`
            except Exception as e:
                print("  ! %s <-> %s failed: %s" % (names[i], names[j], e), file=sys.stderr)
                continue
            k = int(np.argmax(d))
            if d[k] < -far:
                continue                                   # nothing meaningfully close
            sel = np.where(d > -patch_band)[0]
            if len(sel) > max_patch:
                sel = rng.choice(sel, max_patch, replace=False)
            rows.append(dict(
                a=names[i], b=names[j],
                mm=round(float(-d[k]), 3),
                press=bool(d[k] > 0.005),
                at=[round(float(x), 2) for x in pts[k]],
                patch=[[round(float(pts[q][0]), 2), round(float(pts[q][1]), 2),
                        round(float(pts[q][2]), 2), round(float(-d[q]), 3)] for q in sel]))
    rows.sort(key=lambda r: (-1e3 - r["mm"]) if r["press"] else r["mm"])
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("model", help="assembly GLB (named parts) or a mesh file")
    ap.add_argument("-o", "--out", default="fit_report.json")
    ap.add_argument("--near", type=float, default=2.5, help="AABB gap that counts as 'close' (mm)")
    ap.add_argument("--patch", type=float, default=0.6, help="patch band: samples within this of the other part (mm)")
    ap.add_argument("--samples", type=int, default=2600, help="surface samples per pair")
    ap.add_argument("--far", type=float, default=2.0, help="drop pairs whose closest approach exceeds this (mm)")
    ap.add_argument("--skip", nargs="*", default=[], help="substring name filters to exclude (context parts)")
    args = ap.parse_args()

    meshes = placed_meshes(args.model, skip=[s.lower() for s in args.skip])
    rows = fit_map(meshes, near=args.near, patch_band=args.patch,
                   samples=args.samples, far=args.far)
    json.dump(rows, open(args.out, "w"), indent=1)
    presses = [r for r in rows if r["press"]]
    print("wrote %s: %d close pairs, %d press" % (args.out, len(rows), len(presses)))
    for r in presses:
        print("  PRESS %.2f  %s <-> %s at %s" % (-r["mm"], r["a"], r["b"], r["at"]))
    return 1 if presses else 0    # nonzero exit if any press — whitelist by inspection


if __name__ == "__main__":
    sys.exit(main())
