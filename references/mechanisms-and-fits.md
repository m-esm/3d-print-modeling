# Mechanisms, fits, and what must be test-printed

Mechanical-design knowledge distilled from FDM gear/drive/enclosure projects. The recurring meta-lesson:
**friction, flex, and engagement cannot be verified virtually**, anything load-bearing or interference-fit
needs one physical test print to dial in. Flag those explicitly; don't claim a snap/clutch/press-fit "works"
from a render.

## Gears and worms

- **Three independent levers**, don't conflate them:
  - **Module** sets *size* (tooth + gear scale). Shrinking module compacts the drive without changing ratio.
  - **Tooth count / ratio** sets *torque multiplication*. A worm with N-tooth wheel = N:1.
  - **Lead angle** sets *efficiency and self-locking*. A single-start worm at a low lead angle (~5°) is
    self-locking (the output can't back-drive the input), the property that holds a load with no power.
- **Center distance = wheel pitch radius + worm pitch radius** is the one number the housing depends on.
  Derive worm pitch Ø from the lead angle, then everything else hangs off center distance.
- **Pressure angle 20°, backlash ~0.25 mm, bore clearance ~0.25 mm** were good defaults for FDM gears.
- **Spec conflicts resolve in favor of meshing physics.** When a requested OD and a requested module+teeth
  disagree, keep module + teeth (they fix the pitch diameter and the mesh) and let the OD fall out. When a
  requested worm body diameter fights the lead angle, keep the lead angle (it governs self-locking).
- **But the housing envelope is a hard constraint and the ratio is often negotiable.** The turntable's
  100-tooth ring gear pushed the pinion OD past the shell's shoulder radius; dropping the ring to 60T (4:1)
  let it tuck inside, and the lost reduction was recovered for free by the stepper's internal 64:1 gearbox.
  If there's an upstream reduction (geared motor, second stage), trade teeth for fit; the envelope won't move.
- **Self-locking worm + a stiff spring-return load is a trap for a rigid coupling**: the worm holds the
  wheel wherever the motor stops, so the load's own spring can't back-drive it. Solutions used: a **one-way
  clutch** in the drive (forward drive, free return), or **firmware that homes/parks** the output at rest.

## One-way clutches (ranked by what survived)

Through a high-ratio worm the motor's ~0.3 Nm becomes ~6 Nm (≤ ~20 Nm stall) at the output, landing on
small features at small radius → hundreds of N. Findings:
- **Printed multi-pawl freewheels / shallow ratchets SKIP under load**, the contact force cams the pawl out
  faster than it digs in. Dead end for real torque.
- **Undercut sawtooth ratchet** (locking face angled *past* radial so torque pulls the pawl into deeper
  engagement = self-energising) holds better than a radial ratchet, but **PLA teeth still crush at ~6 Nm**.
- **The durable answer is a bought steel one-way clutch bearing** (CSK / HF roller clutch). It moves the load
  off plastic entirely. **How it grips matters most:** a press-fit in *plastic* creeps and slips under
  sustained torque, take torque through **keyways**, not interference. Use a **CSK..PP clutch (keyways on
  both races)**: grow an integral lug into the outer keyway from the housing pocket and into the inner keyway
  from the adapter; add only light press (~0.15 mm) to locate. Drawn-cup HF clutches need a *steel* housing
  and a hardened-steel inner race, won't hold in plastic.
- **Direction is set on the bench, not virtually.** A clutch is directional; fit it (or flip the motor leads)
  so it locks the load-driving rotation. This is a test-print/assembly call.

## Keyed bores + manual override

- To transmit torque to a supplied shaft, **read the shaft's real profile** (slice the supplied STL at its
  constant section, transform to world XY, center it), offset outward by ~0.25 mm clearance, and CSG-subtract
  a **straight** prism of that profile from the gear. Straight, not helical, a helical bore won't pass a
  straight shaft.
- **Manual override = a swept keyed bore.** Union rotated copies of the key profile over an arc (e.g. 50°) to
  make a fan-shaped bore. That gives **angular lost motion**: the shaft can be hand-turned ~50° before its
  keys hit the bore wall (manual release), while the motor still drives it the rest of the way. The load's own
  return spring recenters it. Independent of any clutch (the fan can be cut into the clutch inner hub instead).

## Press-fits, snaps, and slide-together joints (all test-print-tuned)

- **Friction press-fit lids beat cantilever snaps** for reusable enclosures: a flat plate + a perimeter plug
  rim that friction-fits the cavity (plug = cavity − clearance per side). Prints plate-down (plug rim rises as
  self-supporting walls). Press to seat, pry to open.
- **Clamshell halves: in-wall tongue-and-groove** (shiplap) around the perimeter, living *inside* the wall so
  it never protrudes or intrudes into a pocket. Exclude any face that must butt another module flat.
- **Slide-together modules** (dovetail tongue + socket, or tongue + open mouth) let separate prints assemble
  without tools, each prints flat in its own best orientation.
- **FDM bias:** plugs print a touch oversize, cavities undersize, so a small *nominal* gap nets a snug fit.
  Start near 0.4–0.5 mm clearance, then **dial in on one test print**, loosen if too tight, tighten toward 0
  if loose. Lead-in chamfers help slide fits seat. None of this is verifiable from a render; say so.
- **Tool-free assembly = barbed push-pins + bayonet locks instead of screws.** The turntable assembles with
  zero fasteners: a `push_pin()` (Ø4 barbed pin into a Ø4.1 hole, ~0.1 mm interference at the barb) hand-presses
  motor ears, bearing blocks, and brackets together, and the top plate bayonet-twists onto the hub. Cheaper to
  print and iterate than tapped holes, but the barb interference and the bayonet engagement are exactly the
  features that need one physical test print, they flex and can shear; don't trust them from a render.

## Screws + nuts are the cheap structural upgrade (default to M2/M3/M4)

A printed joint that's press-fit or glued is fine until it sees real load, then it creeps, shears a
barb, or splits a layer line. **Common small metric screws + nuts (M2 / M3 / M4) are the easiest way
to make a part strong and serviceable**, and you almost certainly already have them in a drawer.
Reach for them before designing around large or specialty hardware (an M8 bolt, a long ground rod, a
weird shoulder screw) that the user has to go buy. Small screws are cheaper, ubiquitous, and let a
joint be taken apart and re-tightened, which press-fits and glue don't.

- **Captive hex-nut trap >> self-tapping into plastic.** Model a pocket the nut drops into (across-
  flats + ~0.2 mm, depth = nut thickness + ~0.2 mm), run a clearance bore through, bolt from the
  other side. The plastic never carries the thread, the metal does, so it survives repeated assembly.
  Self-tapping a screw straight into a printed boss strips after a few cycles; only acceptable for a
  one-time, low-load fix.
- **Heat-set brass inserts** (soldering-iron press-in) when a face is re-opened often or space is too
  tight for a nut trap. Boss hole = insert's lead diameter; leave a ~1.5 mm wall around it.
- **Default sizes:** M3 is the workhorse (brackets, motor mounts, lids). M2 for small/light/tight
  parts. M4 only where the load or the part size genuinely calls for it. Clearance hole = nominal +
  ~0.4 mm (M3 -> Ø3.4); tap-free, the nut does the holding.
- **Where a screw does NOT substitute:** a *shaft* that must run inside a specific bearing bore (an
  8 mm axle in a 608's 8 mm ID) has to be that diameter, you can't swap it for an M3. That's the one
  case to spec the real rod/bolt; everywhere else (clamping plates, mounting motors, joining
  modules, reinforcing a press-fit) prefer the small screws on hand.
- **Design the holes in `build.py` as parameters** (`M3_CLEAR=3.4`, `M3_NUT_AF=5.5`, `M3_NUT_T=2.4`)
  so the fastener plan is one edit, and so a render/print can verify the nut trap actually captures.

## Bearings and shafts

- **608 (8×22×7) deep-groove** bearings on shaft ends, in Ø~22.15 press-fit pockets split across a clamshell.
  Picked over MR105 (5 mm bore too small for a 5.5 mm motor-shaft bore). Press-fit + pocket locate them; with
  no shoulder at the seat, add a shaft shoulder or E-clip groove if end-float is a problem.
- **Don't neck a load-bearing shaft down to fit a bearing bore.** A shaft thinned to Ø7.8 to clear a top
  bearing's Ø8 bore **broke under load**. Removing the top bearing and keeping the shaft full thickness
  (locating the wheel by its rim in the pocket instead) fixed it *and* removed a bridged ceiling. Less is more.

## Motor coupling

- **Double-D (flatted) shaft bore keys the motor directly**, the flats carry torque, no slip; a set-screw
  becomes just axial retention. Model the real motor (e.g. TT gearmotor: ~64×22×19 mm slab + can + a
  side-exit Ø5.5 dual-D shaft with 3.7 mm flats) in the assembly preview so clearances are visible.
- **Mount = a locating pocket the gearbox nose plugs into, split across the clamshell** so closing the lid
  traps the motor, cleaner than bolting. Open risk: axial pullout under the drive reaction (the worm pushes
  the motor out); the clamshell pinch + set-screw help, may want an external bracket/zip-tie. Lengthen the
  shaft journal so the motor shaft engages the bore ~8 mm, not ~3.
- **Wire pass-throughs split on the clamshell seam** (a semicircle in each half) so leads drop in when the lid
  closes, no threading.

## Driving printed gears with steppers

- **Printed-gear backlash is ~0.3–0.5°, far more than a machined gear.** Open-loop step counts drift by that
  much per direction change. Expose `STEPS_PER_REV` / `STEPS_PER_DEG` as calibration constants and dial them
  on the first run against a physical reference mark; don't trust the nominal `motor_steps × ratio`.
- **A self-locking worm holds its load with the coils de-energized.** That's the big win for a battery or
  thermally-limited build: the tilt axis parks at 45° drawing zero holding current and zero heat. Release all
  coils after each move. (A back-drivable spur stage will creep, so park it against a hard stop or keep the
  last phase energized.)
- **Derive the step constant from the whole train,** including the motor's internal gearbox: a 28BYJ-48 is
  4096 half-steps/rev internally, so a 15T→60T external stage is `4096 × 60/15 = 27306` steps per output rev.

## Pivoting / gimbal mechanisms

- **Parameterize the pivot height independently and sweep clearance at the extreme angle.** On the turntable,
  putting the tilt pivot at the platter top kept the object still during tilt but made the assembly tall; moving
  it down to the cradle center made everything hang below the pivot as a stable pendulum, at the cost of the
  object swinging ~35 mm during a 45° tilt. That swing was acceptable only because the downstream tolerance (a
  3D scanner's 250 mm working-depth band) absorbed it. Decide the pivot from the *downstream* tolerance, then
  render the mechanism rotated to its max angle to confirm nothing collides or leaves the working envelope.

## Torque is a fuse, not a goal

A high-ratio drive easily exceeds what the load needs while PLA/PETG features shear well below stall. So
**current-limit the motor (treat stall current as a shear fuse)** and **home/park the output at a hard rest
position** so it never drives into a stop. **Grease the meshes**, lubrication was the single biggest life
factor in FDM-gear testing (5×+ life); design the running clearance as a grease reservoir.
