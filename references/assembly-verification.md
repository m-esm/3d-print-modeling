# Assembly verification: the gate between "renders nicely" and "actually assembles"

The single most expensive failure mode across every project: **parts that pass watertight
checks, feature-size reports, and six-angle renders, and still cannot be physically
assembled.** Real examples that shipped to plastic: bayonet lugs at r14 against entry
notches opening to r9; a cradle whose lightening window gutted its own trunnion seat; a
plain round bore on a flatted double-D motor shaft (freewheels); spur teeth meshed against
a helical worm (binds); a "lid" whose bearing pocket was a sealed internal void; a motor
housing with no opening the motor fits through; a worm wheel freewheeling on a plain bore
while the review called the drive "done". None of these are visible in an iso render, and
none violate watertightness.

## The gate (run before every export, and before saying "done")

1. **`assembly_check.py` on the assembly GLB** (bundled in `scripts/`): pairwise boolean
   intersection (any un-whitelisted overlap FAILS, exit 1, make it a Makefile gate) +
   min-clearance warnings below 0.3 mm. Whitelist only meshing gear teeth and designed
   press-fit interference via `--allow a:b`.
2. **Motion sweep for anything that moves**: `--sweep part=AXIS:start:end:steps` re-runs
   the overlap check across the whole travel. "Tilt binds at -11 deg against a +/-30 spec,
   and the committed preview pose itself collides" is exactly what this catches. Sweep to
   the EXTREMES of travel, not the rest pose, and if the joint homes by stalling against
   hard stops, sweep to the STALL angles, not the nominal software limit (a +/-90 spec
   with stall stops at +/-93.3 really visits +/-93.3). Two refinements from a pan/tilt
   head build:
   - **The sweep is also a design INPUT, not just a pass/fail gate.** When a moving
     drivetrain must live inside a shell, probe the mechanism at N steps across full
     travel FIRST, record the max intrusion envelope (x/y/z extents of everything that
     pokes past the wall plane), then size the cavity or relief from the MEASURED swept
     envelope plus margin, and re-sweep after modeling. desk-pi's rear pod door: 21 tilt
     steps to the +/-33.8 stalls gave a swept intrusion of x +/-13.5 / y to -78.1; the
     pod cavity was sized to swallow exactly that, final worst-case clearance 1.85 mm.
     Guessing the cavity from the neutral pose undersizes it every time.
   - **Sweep against the right part sets.** In a kinematic chain, a moving part must be
     checked against the FIXED parts and against its PARENT group separately (the head's
     door rides the head, the tilt drivetrain rides the pan group; they move relative to
     each other AND relative to the chassis).
3. **Insertion-path audit, part by part** (eyes + section cuts, no script can do this):
   for every bought part (bearing, motor, board, battery, nut), answer "through which
   opening does it enter, in what order, and does anything printed later block it?" A part
   can have perfect clearance in its final pose and be unreachable. If assembly order
   matters, write it into `docs/ASSEMBLY.md` while checking.
4. **Torque-path audit for every driven part**: walk the chain motor -> output and name
   the feature that carries torque at each interface (D-flat, key, spline, designed
   interference + retention). "Plain bore + friction" is a freewheel, and "press-fit on a
   smooth rod" creeps loose in plastic. `checks_template.py::bore_is_keyed` encodes the
   numeric version.
5. **Fastener reach**: screw length vs stack height per joint, nut pocket actually
   captures (across-flats + depth), driver access to every head. Zero-bite pilot holes
   ("every pilot is a clearance hole, no screw bites anywhere") pass every render.

## Fit map: clearance is a measurement, not a boolean (fitmap.py)

The gate above has a blind spot that shipped a seized gearbox: **boolean "no overlap"
proves parts don't collide, NOT that they aren't pressed.** A printed planetary passed
every pairwise intersection check while its planets sat in the ring at 0.00° of backlash
(the tips bottomed radially; a phase-scan minimum of "0.0013 mm²" had been read as zero
when it was a graze). Assembled, the stage would have ground itself to death. The user's
eyeball caught it; the numbers had said "verified". Three rules fell out of that failure:

1. **Measure fits, don't boolean them.** `scripts/fitmap.py assembly.glb` samples every
   close pair's surfaces and takes signed distances: per-pair minimum clearance or press
   depth, the closest-approach point, and a **contact patch** (every sample within 0.6 mm,
   with its own clearance) tracing the SHAPE of each contact — a rib line, a bore ring,
   gear-flank stripes. Pair enumeration is automatic, which is the point: its first run on
   a real assembly caught three defects that hand-picked boolean checks had missed (a
   motor's nose boss pressing 0.3 into a gear hub, a gearbox axle-pin end stabbing a
   planet 0.55, a ring-cage arc buried 0.5 in the OTHER clamshell half — nobody had
   thought to check against the lid). Exit code is nonzero when any press exists: designed
   press fits get whitelisted by inspection, every other press row is a bug. The same
   whitelist doubles as a CONTACT AUDIT — "red only where it should be": every pair that
   TOUCHES (clearance ≤ 0.005) must be a named, intended seat or press (`--allow a:b`);
   an unexpected touching pair fails the exit code just like an unlisted press. Run it in
   the build so a new contact anywhere in the assembly announces itself immediately.
2. **For gears, measure BACKLASH from the built meshes**: section the exported STLs at the
   tooth band, then rotate-until-contact in BOTH directions (shapely `rotate` + overlap
   bisection). A healthy mesh has symmetric play in the design ballpark; 0.00° in either
   direction is a bind even when booleans pass. Sun/planet ~1°, planet/ring ~2.7° were the
   healthy numbers on a m1.0 printed planetary; internal (ring) teeth print undersize, so
   err loose on the fixed-ring side where slop is harmless.
3. **Verify the insertion PATH, not just the assembled state** — states vs processes. A
   carrier plate cleared the assembled ring by 0.35 mm yet could NEVER be installed: its
   Ø30.8 disc had to pass the ring's Ø28 tooth-tip opening. Sweep each part along its real
   insertion axis (translate in steps, boolean at every step, expect 0.000 the whole way),
   with the parts present at that stage of assembly (the lid is off while gears go in).
   Two standard planetary facts while you're there: gears enter internal teeth AXIALLY
   while meshed (like a spline), so planets always have a path — smooth discs larger than
   the tooth-tip circle do not; and a part can be trapped by a feature added LATER for
   another part (a cage's seat ledge sealed the pinion's only entry — the fix was a
   top-loading shaft with the cage hanging from a flange).

The companion viewer (`scripts/viewer_glb.html`) auto-detects `fit_report.json` next to
the model and adds a **fits** section: rows sorted tightest-first, and a 3D overlay of the
contact patches colored by clearance (red press / amber <0.15 / yellow <0.4 / green free),
drawn through the housing; click a row to isolate one pair's patch. The overview reads
like a CAD contact heatmap — the clamshell split traces as a ring, gear meshes as flank
stripes — and makes "which surfaces rub, and how hard" a thing you see rather than infer.

**Articulated assemblies:** run the canonical fit report at the NEUTRAL pose (e.g.
`make fits` = `FITS=1 PAN=0 TILT=0`). Same-group pairs (bores, seats, presses within one
kinematic group) are pose-independent; cross-group numbers change with the joints, so a
report baked at a preview pose is not the reference. Store the patch coords in neutral
pose and have the viewer re-pose them per kinematic group (a patch belongs to the MORE
moving of its two parts: child group > parent group > fixed), so the 3D overlay stays
correct at any joint-slider pose and on any baked GLB. And keep the fit pass OPT-IN
behind a flag: a full-assembly report costs minutes, which kills a ~2 s watch loop.

## Design-invariant checks: unit tests for geometry

User-approved features get silently deleted by later, unrelated edits. It happened
repeatedly (a manual override removed three times, each caught by the user, not the
tooling; agent fix-ledgers marked `[~]` for edits that never applied). The fix is
mechanical, not attentional:

- Keep `src/checks.py` (start from `scripts/checks_template.py`), called at the END of
  every `build.py` run.
- **The same turn the user approves a requirement, add one check for it** ("override
  present", "tilt reaches +/-30", "pocket open from +Z", "fits the 256 bed").
- Never delete or weaken a check without explicit user sign-off. A failing check means
  the geometry regressed.
- This also makes subagent fix-ledgers verifiable: an item is done when its check passes,
  not when the agent says so.

## The multi-agent pre-print review (promote it from rescue to routine)

The highest-value pattern observed in real sessions was ALWAYS invoked too late, after a
failed print or a user revolt: 3+ parallel review agents, each with a distinct lens,
measuring the actual STLs/GLB and reporting numbered, severity-ranked defects. One such
review found ~20 real defects in a "committed" model; another caught a 67-degree
over-throw and unprintable 0.38 mm gear tips before the next print. Run it as a standard
step before the FIRST print of any multi-part mechanism (needs the user's multi-agent
opt-in):

- **geometry probe agent**: loads meshes, measures the claimed fits/clearances/travels
- **assembly-walk agent**: attempts the insertion-path audit part by part
- **mechanical-loads agent**: torque paths, lever arms, weak features, printability of
  load-bearing details
Agents must return MEASURED numbers with part/coordinate citations, not impressions.
Keep fix agents' scopes small (one subsystem each) and their output terse; a 64k-output
fix agent dies mid-edit and leaves a lying ledger.

## Orientation protocol (spatial language is the #2 iteration burner)

Verbal pose instructions map ambiguously onto 3D. Real costs: six correction rounds to
pose two L-brackets ("you got it wrong again"), resolved only by asking which two ends
touch; "above" meaning +Y along a door, implemented as +Z; "turn upside down" implemented
as face-down; an imported differential mounted pinion-down and called "finalized".
Rules:

- **Restate every spatial instruction in axis terms before implementing it**: "long tip
  of L1 touches short tip of L2, both flat on XY, opening toward +X. Correct?" One
  question beats four wrong builds. When the user corrects you twice on the same pose,
  STOP iterating and ask which faces/edges mate.
- **Never compose rotations from memory.** Rx180 then Ry180 equals Rz180; if you can't
  state the net axis-angle, print the transform and check extents before rendering.
- **Define rotation constants with degrees**, `R(deg)` helpers, not fractions of a TAU
  someone may have mis-defined (`TAU = np.pi` silently halved every rotation in a real
  project: 90-degree turns became 45, "flips" laid parts on their backs).
- **For imported/foreign meshes, interrogate, don't eyeball**: print `mesh.extents` and
  `mesh.bounds`, probe candidate bore axes for solid fraction ("roll=90 gives solid
  fraction 0.00 = clean through-bore"), and render with other parts hidden. Renders of
  unfamiliar geometry get axes mislabeled ("that 'side' tag is actually end-on").

## Render legibility (make the look-at-it loop able to see)

- **Bottom view is part of the standard set** (`shoot.py` now renders it). Bed-facing
  bugs, floating discs, raised features that should be engraved, hide from iso/front/side.
- **Distinct per-part colors always**; single-color renders forced a session to debug an
  LCD orientation numerically because the screen couldn't be told from the head.
- **Ghost/translucent mode HIDES interference.** It exists to show internal layout, not
  to verify it: a translucent shell rendered "fine" over parts breaching its wall by 1 mm.
  Contact and breach questions get NUMBERS (`assembly_check.py`, `wallcheck.py`), never a
  ghost render. When the user says two parts touch and the render looks clear, run the
  numeric check before arguing; occlusion and translucency have both produced false
  "it's fine" reads.
- **Isolate to diagnose**: a debug render mode that hides occluders (wheels off, lid off)
  is worth the two minutes it takes; welded-in geometry is invisible inside a 675k-face
  shell.
