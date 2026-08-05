# Hard-won patterns (2026-07/08: Klonk + Fermax intercom)

Patterns paid for with printed plastic, false-green gates, or multi-hour pad-position
thrash. Cite these in reviews. Pair with `design-rules-checklist.md` (R1–R8 floor).

## 1. Seat pad ≠ clamp (retention physics)

**Symptom:** cover/lid "clamps" still rattle or lift after endless pad XY/Z tweaks; gates
report solid area under the pad and 0.05 mm gap, yet the user says it does not hold.

**Cause:** a pad that only *rests* on a return deck has no +Z (or peel) preload. Top
tenons under a ledge clamp; bottom windows that open the *opposite* way cannot share the
same slide, so pad-only south is structurally free.

**Rules:**

- Name the preload path: undercut ledge, screw into a plug, captive nut + bolt, interference
  snap. If the answer is only "friction on a face," it is not a clamp.
- When pocket mouths face opposite ends, **do not** invent one rigid finger that rides both
  on a single −Y (or +Y) slide. Use a separate south/north plug + screw, or accept a second
  assembly motion.
- Gate **clamp force**, not only pad solid area. A green "solid A under pad" while lock
  blocks are deleted is a lying design.
- Restoring a proven screwed plug beats another pad-geometry rev. Archive why the plug was
  removed; do not delete preload paths to "simplify" without a replacement.

## 2. Honest designed-contact whitelists

**Symptom:** pairwise dig 50+ mm³ "passes" because `paddle × servo` (or similar) is listed
as DESIGNED; real geometry is wrong.

**Cause:** a pair-name whitelist blesses *any* intersection volume for that pair, including
paddle body into gear cap, web through ears, etc.

**Rules:**

- Whitelist only the *intended kiss* with a volume floor (e.g. horn×spline ≤ 0.05 mm³),
  never a broad parent pair that can hide digs elsewhere on the same meshes.
- Prefer explicit positive gates: "paddle clears servo swept 0.000 over N poses,"
  "west-face clears gear-cap ≥ 1.5 mm," instead of a blanket allow.
- Unmasking a whitelist often reveals a second pre-existing red; fix both the same turn.

## 3. Datum off the real stack, not a convenient face

**Symptom:** paddle "doesn't fit the servo"; pocket floor misses the horn; spline tip
stands proud; arm digs the gear cap.

**Cause:** plane hung off gear-cap thickness + half plane-width while the printed arm is
wider; OEM M2 clamps the horn socket onto the **spline tip**, not the cap face.

**Rules:**

- For horn/servo/blade stacks: measure STEP/scan for socket depth, collar OD/proud, arm
  thickness; set pocket floor = tip + (arm_t − socket_depth) (or the real OEM rule).
- Pocket outline = convex hull of the *measured* arm slab (+print clear), not a parametric
  trapezoid that pinches real flank taper.
- Through-bores for collar + head + driver when the OEM head seats on the *bought* part's
  own step, not on printed plastic.
- Caliper note: reference STEP socket depths often differ from OEM (e.g. 1.0 vs 2.4–2.6);
  absorb with through bore + margin, do not freeze the wrong number as truth.

## 4. Model interacting bought parts as geometry

**Symptom:** green gates, springs bind the moving skirt; coils fall off pins; solid length
wrong.

**Cause:** metal springs (or other bought coils/pins) never existed in the mesh, so no
boolean or clearance gate could see them.

**Rules:**

- Display meshes for return springs, pins, horns that occupy volume during motion.
  NON_PRINTED is fine; absence is not.
- Coil-bind length = **counted coils × wire diameter**, not free_L / guess. Gate
  `CAPSPR_COILS` and bind clearance ≥ 1.5 mm at full travel.
- Spring OD vs guide skirt / pocket flute: measure radial clearance at the station radius;
  first model of the coils often proves stations are too far inboard.
- Retention pins: multi-coil engagement + light barb holds better than a 0.7 mm stub; free
  cantilever strength for side load is only the *unsupported tip* once coils brace the pin.
- Print orientation: fixed spring barrels must not stand proud of the cosmetic face if
  FLIP_X lands that face on the bed (gate "well fixed flush").

## 5. Reach and kinematics need multi-axis gates

**Symptom:** 1-D "press reach" green; pad rebuilt south of the arm's max Y; foot never
touches.

**Cause:** reach gated only in Z (or only centerline distance) while the pad moved off the
foot track in Y/X.

**Rules:**

- Gate foot track ⊆ pad extents with margin (X and Y), pad vs servo body clear, and mesh
  kiss at the press pose (min dist + dig volume).
- Stroke sweep: N poses, paddle×cap dig, paddle×statics dig.
- Firmware angles must match geometry-derived park/touch/press; hardcoded 20°/70° vs
  geometric 43°/71° stalls every cycle.

## 6. Frozen printed interfaces

**Symptom:** redesign of already-printed collar/frame to suit a new cover; user reprints
everything; freeze gate missing.

**Rules:**

- Archive as-printed STLs (`cad/.../printed/`) with content hashes; fail-closed freeze
  gates (sym-diff + bounds) on those parts.
- Cover-side params may move; frame-side window/cutter values live in a FROZEN INTERFACE
  block and stay byte-stable with the archive.
- Redesign the *unprinted* mate (cover, blocks, pads) around the frozen part.

## 7. Strength: measure mesh sections, not only params

**Symptom:** 3×3 mm lugs / Ø2.6×0.7 spigots pass W×H floors then snap by hand.

**Rules:**

- Plane-cut section area and section modulus S along the span from the exported mesh.
- Multi-load util: slot side, peel (layer derate), spigot lateral with Kt, spigot axial
  peel. Design SF on normal-use forces (e.g. 2×) so util ≤ 1 means real margin.
- Size floors (min A, min S, min spigot L/D) are backups; util is the primary.
- Parts that break by hand get strength gates the same turn, not after the next reprint.

## 8. Housing for bought modules: snug + crush, not hang

**Symptom:** servo "in" a pocket with 2 mm/side slop; only two M2s hold it; pilots half in
void.

**Rules:**

- Pocket clearance per side is a named param (e.g. 0.30); recenter on measured body
  center, not the first parametric guess.
- Crush ribs (small interference past the published face) after cuts so the relief does
  not gut them.
- Pilot meat gates: annulus volume around the pilot in solid plastic.
- Floor near-seat gap (0.05), not a floating body.

## 9. CSG order: late unions reseal cuts

**Symptom:** M3 access wells modeled and cut; mesh still solid at the pilot; watertight
fails after "fix."

**Cause:** corner gussets (or any late union) re-fill subtracts; or the same trimesh
instance is both a cutter and a keepout and gets consumed.

**Rules:**

- Any solid unioned *after* `difference(body, cuts)` must subtract the same functional
  keepouts (driver wells, cable exits, screw corridors).
- Build **fresh** keepout meshes for the post-union pass; do not reuse cutter instances
  already fed to manifold.
- Prefer structural deck/underface first, openings second; never hollow a free-span face
  membrane then "hope" ribs appear.

## 10. Voids, decks, and solid probes

**Symptom:** seat pad parked "over" a window Y-range that is actually open from the side;
gap reads ~3 mm (air); next rev parks only on solid deck.

**Rules:**

- Pocket open from the outer face under a solid roof is not a through-void. Probe solid
  *under the pad slab* (frame ∩ thin box just below ret_top), not only Y-overlap with
  window bounds.
- Short feet that clear approach/shell may still miss the clamp deck; prefer full pad on
  solid roof when scan budget allows.

## 11. Viewer and pose artifacts stay fresh

**Symptom:** user stares at old arm length in the viewer; animation sinks the cap before
the foot arrives.

**Rules:**

- After kinematics change, rebuild **both** `assembly.glb` and `assembly.pose.json`
  (or fixture equivalents). Gate pose freshness against datums.
- Cap/follower motion should track contact (sampled lift profile), not a linear lie from
  stroke 0.
- Display springs should squash about the fixed pocket floor in sync with press, not
  rigid-translate through the moving face.

## 12. Printed pins under bending / layer peel

**Symptom:** PETG stub snaps at shoulder root; M5 stud needs metal mod the user rejects.

**Rules:**

- Prefer glue-slip printed journal + stock screw core across the layer-failure plane when
  metal mods are banned.
- Glue-slip races (+0.0 to +0.05 over press) when press cracks thin tubes. Redimensioning
  a failed press-fit never closed one of these bugs; only a fit-class change (glue-slip)
  or a steel core did. Treat "print again with tighter/looser interference" as a smell.
- Vertical-print pins: steel across Z-layer plane beats pure PLA at the root.
- Self-tap pilot sizing: shank minus ~0.3 (M3 → Ø2.7, M5 → Ø4.25). Bury the head in an
  internal counterbore so the part's OD (and its mating bores) stay untouched.
- Order of operations when a screw core meets a glued race: CA the stub into the race
  FIRST, drive the screw after cure — the race gives hoop confinement while the thread
  bites; the reverse order splits the stub.
- Thin necks between fat features are where vertical prints break. Fatten torque tubes to
  the neighboring collar diameter with 45° cones (0.9 → 1.78 mm wall was ~3.8× torsion J
  at the failure plane).
- Glue that commits a bought part (motor shaft into a printed bore) is a one-way door:
  bench-verify mesh sense / throw / click direction first, glue last.
- Print-in-place compliant features (accordion/serpentine springs, flexures) must never
  sit in the torque path — they only reseat or return (a few N); drive load goes through
  rigid bosses. Any flexing member carrying drive torque is a redesign flag.

## 13. Snap clips vs rigid retention (interlayer)

**Symptom:** cantilever snap arms break at root (10–22% strain vs ~1–3% PETG interlayer).

**Rules:**

- Living snaps loaded across layers are a fatigue time bomb for daily open/close.
- Prefer rigid tenons + screws/plugs, or snaps only where layer direction carries flex and
  strain is gated.

## 14. File size and module shape (agent context)

Agents re-read megafiles every turn. Soft target 200–500 lines for a builder/gate module;
smell >1000. When you edit a fat file, peel a coherent part/region into a sibling module
the same change; keep params coarser (one params surface per product). Thin facades so
`import build` / gates stay stable.

## Quick self-check before "done" on retention or drive mates

1. What feature provides **preload** (not just contact)?
2. Is every DESIGNED pair limited by volume or a positive clear gate?
3. Is the kinematic datum the OEM stack, measured?
4. Are bought coils/pins/horns in the mesh for the poses that matter?
5. Do freeze archives still match printed plastic?
6. Would a late gusset/union reseal this hole?
7. Did the viewer artifacts regenerate?
