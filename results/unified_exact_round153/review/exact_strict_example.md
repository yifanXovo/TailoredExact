# Independent exact verification of the strengthened fixed-marginal example

The stdlib-only reviewer script checked **169 rows and 68 variable bounds**
with Fraction arithmetic. The saved original 117-row matrix and rational
extension are fixed R152 carrier members; their hashes were checked. The
reviewer independently reconstructed the 44 RN rows, two scaled-stock rows,
NC1/NC2 and TS1--TS4. No solver, Native API, Optimize or compiler was used.

The original G/state_g/zprod extension is scaled by 10/9. The new coordinates
are t=4/9, nonzero w=(4/9,1/3,1/9,2/9,2/9) on (11,21,22,32,33),
Yhat=(4/9,5/9,10/9), and hhat=(1/6,1/6,0). Every original and appended row
and every original and appended variable bound is satisfied exactly.

At the fixed marginal, u=w22 and v=w33 give 2t+u/2+v/4=1. Both NC rows give
Hhat>=1-3t/2, while the two differences against station 1 give Hhat>=3t-1.
The weighted sum (2/3,1/3) proves Hhat>=1/3 and g>=1/9. The extension attains
this lower bound, so its fixed-marginal optimum is exactly **59/288**.

The hard resource excludes the fourth 2-by-2 corner (1,2,3). The unique
compatible distribution assigns (1/4,1/2,1/4) to (1,1,2), (1,1,3), (1,2,2).
Consequently H=3/32, Gamma=161/1080 and Theta=1049/4320. The remaining exact
fixed-marginal gap is **41/1080**.

This statement is restricted to the declared inventory block. It does not
establish a complete routing extension or domination of all historical
disjunctions. The old global-floor gap is not inherited: the global integer
floor remains 47/240, and floor minus the new reference is **-13/1440**.

Full exact coordinates, all row slacks, all bound checks, source identities
and the lower proof are in [exact_strict_example.json](exact_strict_example.json).
The parent serial ledger charges this one verification process; the script's
0.022197 seconds are a nested observation.
