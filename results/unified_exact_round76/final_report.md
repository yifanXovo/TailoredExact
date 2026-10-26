# Round76: physical closure improves D7 startup; complete performance remains open

The new default-off JDS-C preset closes the current JDS-X physical witness
under unvisited-station insertion and served-station quantity improvement.
On D7 it accepts two insertions followed by five quantity changes, lowering
the original startup objective from0.380773687462 to0.331621561270
(12.908%). The other four fresh startup pairs have unchanged
objectives and route hashes. This establishes a cheap physical handoff repair,
not a repaired complete-method regression or an overall successful algorithm.

Base: published R75 commit692cf9f0ef8852d4ee0d62c5ed206c081658d158 / draft PR136.
Branch: codex/round76-physical-route-closure. Draft PR137 is open:
https://github.com/yifanXovo/TailoredExact/pull/137 . publication.json records
the verified evidence head/base; ordinary Git push preserves measured history.
No main merge or default change.

## Diagnosis, method and scope

R75 quantity descent finds no improving move at the original D7 endpoint.
The R73 constructor runs before final decoded descent and therefore does not
establish insertion closure of that final witness. A fixed-witness diagnostic
finds two legal residual pickup/drop insertions on vehicle2, serving four
previously unvisited stations and reducing F to0.336367943448. D6 is unchanged.
All six initial/accepted/final witnesses pass independent physical replay.
The fixed routes are explicitly diagnostic and never enter the formal preset.

JDS-C inherits JDS-X and all25 descent seeds. At each current witness it asks
R73 for the best insertion gain/duration proposal and R75 for the minimum-F
quantity proposal, chooses the smaller proposed F, then adopts only a strictly
improving full original physical witness. This is not a minimum-F oracle over
the neighborhood union. It repeats until both neighborhoods are exhausted or
the sole whole-run deadline ends the algorithm. Finite bounded integer
inventories and strict original F descent give finite termination without
an arbitrary move cap. Numerical mismatch is explicit experimental failure.

The full coupled Gini objective, empty departure, loaded return, nonzero one-
way service, stock, prefix Q and travel/handling duration retain their original
meaning. The exact domain, validated native Start and complete VD-S proof are
unchanged. The outer incumbent threshold remains1e-10. Generic insertion and
quantity repair are established ideas; no theoretical novelty is claimed.
See mathematics.md for the exact scope and primary-literature references.

## Actual qualification and startup evidence

Measured source 4f6254c2639972ce3ac2b80906ce6d4ebd701f3e.
Binary SHA256 df1de39a0c74a42633f80a939dcbed4218192ad1466760061b45d73f948451fc.
The sole qualification passes58/58 tests without a repair. The new structural
composition test independently replays a trajectory using both proposal types,
checks every original F/G/P and load/time constraint, unique finite inventory
states, both endpoint neighborhoods, deterministic output, empty/fixed inputs,
invalid physical input and the whole deadline. R73/R75 exhaustive proposal
oracles remain enabled. A real JDS-C CLI and inherited same-binary JDS-X CLI
both certify the tiny optimum5/24 numerically. Each actual submitted Start is
accepted and observed in MIPSOL; independent full167-row vector checks pass.
These are integration/correctness tests, not performance or rational-proof claims.

All ten startup-only runs finish normally, complete25 seeds and invoke zero
Optimize. All25 logical descent paths match in every fresh pair. Every new
move is independently reconstructed from its trace and physically verified.
Owned launcher and children use logical2/mask4 with checked restoration;
all startup work, snapshots, process launch and exit are paid.

|Role|JDS-X wall s|JDS-C wall s|JDS-X UB|JDS-C UB|Insertions / quantity changes|
|---|---:|---:|---:|---:|---:|
|D3|0.063|0.063|0.078115302611|0.078115302611|0 / 0|
|C2|0.062|0.078|0.837091467555|0.837091467555|0 / 0|
|D4|0.079|0.078|0.506422789224|0.506422789224|0 / 0|
|D6|5.797|5.828|0.160027280604|0.160027280604|0 / 0|
|D7|10.219|10.235|0.380773687462|0.331621561270|2 / 5|

D7's two insertions reproduce the separate diagnostic. They unlock five
quantity-pair improvements that did not exist at the R75 starting endpoint.
All five are within one vehicle; one reverses a station's operation direction.
There are no zero-stop deletions or neutral moves in this observed trajectory.
The final witness serves50 stations. Some improvements increase deviation P
while lowering full F through Gini, so a separable penalty proxy would not
represent this criterion. Nine initial/accepted/final D7 closure witnesses are
independently checked. The traced closure interval is0.0069522s, excluding its
initial/final snapshot overhead; full startup time above includes all work.
Tiny wall differences on unchanged roles do not establish statistical equality.

## Cost, acceptance and next step

The fixed diagnosis costs1.640808s including its
1.417177s compile and two runs, with zero Optimize.
The qualification costs101.889281s and129 actual
Optimize calls, below the prospective150 cap. The optional repair is unused.
Ten startup processes cost32.502000s/zero Optimize; their
independent replay costs0.188310s. Other offline
and delivery costs are in resource_summary.json; nested diagnostic components
are explicitly not counted twice. Interactive editing is not a complete
machine-time census. No solver failure, rerun or reset credit is involved.

All619 selected raw evidence files are delivered in three lossless bundles:
3634822 original bytes,527816 compressed bytes; every member SHA256 passes.
The bundles include all actual native qualification logs/models/witnesses,
structural traces, startup and fixed-diagnostic raw outputs. Executables remain
local with hashes. reproduce.md gives guarded commands and path limitations.

Evidence is credible and the default-off architecture is admissible. The
increment is a demonstrated current-witness insertion/quantity interaction.
It provides no new full P-GRB or K1 comparison, LB gain, certificate-speed gain
or independent confirmation. R74's severe D7 gap regression and lost K1
protection remain unresolved. R73 small-role performance is not relabelled as
a new JDS-C benefit, and unchanged starters do not prove unchanged MIP timing.

Publish this substantive implementation/screen stage, then separately admit a
fresh matched D7 complete-method comparison on the frozen qualified build.
A better UB alone must not repeat the unsupported efficiency inference exposed
by R74. If complete performance remains poor, reconsider the route/quantity
search and decomposition rather than indefinitely adjusting this closure.
The sustained overall research goal remains active and unmet.
