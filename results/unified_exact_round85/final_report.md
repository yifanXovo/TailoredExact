# Round85: remaining protection and a repeated D6 certificate

The unchanged ENS-C candidate repeats D6 certification in 3181.735 seconds,
while matched P-GRB and K1-R remain open at the common 3600-second cap.
E7 stays near P, S12 retains a nonzero small-role repair, and D3/C2 certify
while both controls remain open at 300 seconds. C6/C8 preserve and strengthen
the current K1 advantage at 600 seconds. This is exposed protection and finite
replication, not independent confirmation or overall-goal acceptance.

All 21 original runs are normal and valid: 9 certified, 12 open, 81 Optimize
starts and 81 returns, with 15456.440 seconds of paid process wall time.
Campaign, mechanism and replication audits pass. No run was repeated, replaced
or selected as a preferred realization. Publication status and exact heads are
recorded separately in `publication.json` and `status.md` after publication.

## Identity, contract and complete outcomes

Base: R84 final `ed0cd977ac2ea1cf7a7bf1236a15dd845a3ed948`, draft PR145.
Branch: `codex/round85-ensc-remaining-protection-replication`.
Final prelaunch freeze: `77dcc0ee1090d2e9f99d7d91d4cd60513967b24c`.
Qualified source: `4496078f25c0cdad1cf7a5c39835fd23121e8978`.
Executable: `build/round83/v1/ExactEBRP.exe`, SHA256
`25b7ec3a6d89d9f0f921c2984fbb1d9876f36f67e617af144275c88b44e6255e`.
Protocol and campaign identity bind all input hashes, mathematical parameters,
source/build/settings and exact launch commands.

ENS-C uses `research-round83-vds-equal-net-exchange`. K1-R uses
`research-round65-k1-h` with the same verified-candidate/zero-stop reliability
flags. P remains the original compact model with native defaults and no added
Start, cuts or imported information. Gurobi 13.0.2, Threads=1, Seed=0,
Presolve=Auto, zero requested gaps and original tolerances are shared.
Runs are serial on processor 2, mask 4; frequency is not locked. Whole-run
shutdown margin is 3 seconds, the external guard is cap minus 2 seconds,
and every native call receives the common remaining deadline. No component
time or Work slice is added. All costs below include startup and exit.

The following compact table complements all 21 U/L/signed-gap/relative-gap
rows in [result_tables.md](result_tables.md), exact [findings.json](findings.json),
and all 84 checkpoints/comparisons in `campaign/`. C means numerical
certificate; O means open. A displayed zero gap does not assert rational proof.

|Role; V/M/Q/T|Cap|P seconds; C/O; gap|ENS seconds; C/O; gap|K1 seconds; C/O; gap|
|---|---:|---|---|---|
|E7; 12/2/30/3600|120|1.469; C; 3.4694e-17|1.329; C; 0|5.656; C; 2.0817e-17|
|S12; 12/1/30/10800|120|5.656; C; 4.1633e-17|1.766; C; 2.7062e-16|40.781; C; 1.8735e-16|
|D3; 12/3/30/2850|300|297.078; O; .003514041568|139.047; C; -2.0817e-17|297.062; O; .001207412876|
|C2; 20/2/30/1800|300|297.063; O; .059019912446|113.766; C; 1.1102e-15|297.078; O; .032875031876|
|C6; 50/4/30/1800|600|597.109; O; .314012903008|597.156; O; .149427255735|597.125; O; .190677391518|
|C8; 30/3/30/3600|600|597.063; O; .229862167194|597.062; O; .137747763760|597.110; O; .172330809606|
|D6; 30/3/30/18000|3600|3597.188; O; .006438488775|3181.735; C; 4.1911e-15|3597.141; O; .008769893620|

For both-certified small roles (V <= 12 and both walls below 60 seconds),
material requires over 2 seconds and 20%; severe requires over 5 seconds and
50%. Other certified comparisons require over 10 seconds and 15%, or over
30 seconds and 50% for severe loss. Both-open material requires over .001 and
10%; severe loss requires over .01 and 50%. These frozen descriptive rules
are not statistical tests or algorithm gates. Certificate gains/losses are
separate; relative gap is (U-L)/abs(U), with missing/zero U left undefined.
Signed tiny gaps are retained, including D3's negative floating-point gap.

## Repairs, protection and limitations

E7 ENS/P is near under the frozen rule. K1/P's 4.187-second increase is
material but not severe. S12 ENS saves 3.890 seconds against P and 39.015
against K1 at a nonzero optimum. The current K1/P regression is severe.

D3 and C2 establish current certificate gains against both controls. K1's
HGA wall fields are only 2.0891961 and 2.7168636 seconds, followed by
294.7179997 and 293.6360002 native solver seconds. K1 also begins with better
physical objectives (.0494686826144 and .829963413172) than ENS
(.0781153026106 and .837091467555). These gains cannot be explained solely
by saved HGA seconds or zero-objective termination. No counterfactual time
is substituted. ENS accepts no neutral exchange/relocation on these two
roles, so these full-method gains do not identify accepted exchange as their
causal repair. Exact-phase starts, detailed native costs and all calls remain
in the original records.

C6 reduces P's gap by 52.4137% and K1's by 21.6335%, with both U and L
better than both controls. Its unclipped K1/P advantage retention is
1.334454654. C8 reduces P's gap by 40.0738% and K1's by 20.0678%, with
retention 1.601116457. Against K1, C8's U is worse by .005039866475 while
L is stronger by .039622912321. This gain is not uniformly better primal
search. Both C6/C8 comparisons are 600-second protection, not new long-window
validation. They were K1 advantages, not invented P-led regression roles.

All 84 checkpoint comparisons and 28 protection rows are retained. None
classifies ENS as a material/severe regression or loss of most K1/P advantage
under the frozen rules. This does not mean pointwise U/L dominance. D6 K1
has no observed physical U at 300 seconds; its U/gap are null there and its
qualified L remains visible. No startup witness is backdated.

D6 repeats R84's exact final U/L
(.15708313110317415 / .15708313110316996). R84 certified at 3171.157
seconds; R85 takes 10.578 seconds longer, near under the absolute-and-relative
rule. Both runs remain in evidence. All three D6 arms pass source, input,
binary, settings, cap and affinity matching; 18 checkpoint rows and 18 pair
comparisons were audited. D6 is first in R84 and last in R85, preserving
relative P/ENS/K1 order but changing whole-campaign position. This finite
repeat establishes neither statistical equivalence nor the cause of timing
variation. P's L decreases by .0000127948583; K1's by .0000047988340.
R84 K1 was a valid hard stop; R85 K1 returns normally. Current K1/P gap is
36.2104% larger, a material but not severe loss.

Earlier limitations remain: R84 D7 improves P gap by 47.2512% but loses
19.1258% against K1 at the final cap, retaining 84.8010% of K1's P advantage.
Its 1200-second K1 loss is severe, despite a strong P gain. R84 U6 repeats
a 13.5852% P gap gain with worse U and stronger L. These rows are not replaced
by current successes or averaged away. R82 outcomes used to revise ENS are
now development data.

## Actual mechanism and evidence

The unified method remains R83's independently verified physical startup,
VD-P inventory/product formulation, F0 strengthening, full-cover AM proof
core and actual full Start. Equal-net exchange and balanced relocation
preserve operations and inventory, checking recipient capacity prefixes and
complete directed route duration before strict objective closure resumes.
Finite lexicographic descent proves termination of that search, not speed or
global optimality. [unified_method.md](unified_method.md) links the inherited
mathematical definitions and unified parameters. No instance dispatch,
parameter tuning, tolerance change or default merge is introduced.

The source/receipt/physical/full-cover audits pass: 274 measured source
hashes, 274 physical witnesses (260 native and 14 startup), 19782 global
bound events and 20239 committed events. No uncommitted data or unseen
receipt appears in the 21 observation-coverage rows. Cross-arm bounds pass
on all seven roles. Every certificate is a Gurobi numerical certificate
under the original tolerances, not a verified rational certificate.

All seven ENS runs complete all 25 decoded paths; none takes mathematical
zero termination. Every final neutral-search route matches the outer
handoff. E7 accepts one exchange and one strict quantity move; D6 accepts
four exchanges and four quantity moves. C6 accepts one quantity move and
no neutral move; S12/D3/C2/C8 accept no neutral moves. Neighborhoods finish
exhausted, without deadline or verification failure. D6's logical startup
trace and initial/final routes match the existing R83 diagnostic, whose
routes were not supplied to the algorithm.

ENS startup witnesses become available at .079, .422, .094, .094, .250,
.234 and 5.969 seconds in role order. K1's corresponding observations are
4.313, 38.109, 2.140, 2.781, 2.969, 4.282 and 325.750 seconds. Availability
includes completed observation and is distinct from the HGA wall field.

Eleven actual Start decisions are eligible, independently mapped, checked
against all real model rows/bounds/types/objective, read back, and confirmed
accepted by native logs. Maximum actual row violation is 3.06505e-13;
maximum mapping difference 1.13687e-13; readback difference is zero. All 14
P/K1 controls are checked without added Start. Acceptance alone does not
establish causal performance benefit.

|Role|ENS LP/MIP calls|K1 LP/MIP calls|
|---|---|---|
|E7|3/1|3/2|
|S12|3/1|3/1|
|D3|3/2|3/2|
|C2|5/2|5/2|
|C6|3/2|3/2|
|C8|3/2|3/2|
|D6|5/1|5/2|

Every P arm makes one MIP call. D3/C2/C6/C8 ENS each pay two MIP calls:
the first mathematical proof target and the subsequent remaining obligation.
Neither call is hidden. D6's terminal MIP has 30485 rows, 8273 columns,
22900 nodes and 23816315 simplex iterations, the same node/iteration counts
as R84; native time is 3171.34 versus 3160.92 seconds. Rounded native-log
attribution is separate from formal whole-process cost.

## Cost, delivery and stage decision

The original plan allocated at most 16920 process seconds for 21 runs.
Actual paid process wall is 15456.440 seconds (about 4.293 hours).
There is no new build, CTest, native qualification, separate startup process
or generated input. R83's 62 tests and 165 qualification calls are inherited
by hash, without rerunning or charging again.

Measured offline work: preflight .993961900 seconds (including seven compact
exports totaling .673 seconds, zero Optimize); per-run replay .564712001;
campaign audit 3.696818300; mechanism audit 5.079803200; replication .023468300;
summary .020665300; package plus first verification 20.976196700; separate
verification 1.862484700; plotting 1.328778100. Interactive work is not a
complete machine-time census. Transport attempts and preparation errors are
retained separately; they are not solver failures or subtracted costs.

All 41210 files in 22 bundles are verified twice, without extraction or
optimization: 175822212 raw bytes and 26983737 bundle bytes. Source,
qualification and startup bundles are inherited from R83 by hash; no license,
credential or executable is delivered. All five D3/C2/C6/C8/D6 PNGs were
visually inspected; labels, ranges, missing observations and captions are
readable. SVGs and exact plotted checkpoints accompany them. Dashed segments
guide the eye and do not invent intermediate observations.

Evidence and architecture pass this stage's review. Overall acceptance remains
unmet: exposed successes and a finite repeat cannot replace an unadapted
check on varied structures including nonzero medium/large proof difficulty.
The prospective recipes and ignored local script drafts have generated no
data and allocated no extra solves. After publication, recheck resources,
freeze a finite confirmation scope before generation, review missing-UB
evidence handling, and retain every admitted outcome. No further run is
authorized by this report itself; admission is a separate recorded step under
the user's ongoing research authorization.
