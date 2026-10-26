# Aggregate state penalty: validity, projection and historical control

The accepted production reference is R134 S2 / ms2, including its own complete H, shared M-B inventory/service representation, VD-P, pair support, controller and proof rules. AP is a default-off research row. It is not a restoration of the older VD-J formulation.

## 1. State mixing and validity

On a legal finite support, let \(s_{iy}\ge0\), \(\sum_y s_{iy}=1\), and \(r_i=\sum_y\rho_{iy}s_{iy}\). In the ideal model \(\rho_{iy}=y/D_i\). Define

\[
\phi_i=\sum_y|\rho_{iy}-1|s_{iy},\quad
a_i^+=\sum_y(\rho_{iy}-1)_+s_{iy},\quad
a_i^-=\sum_y(1-\rho_{iy})_+s_{iy}.
\]

Then \(\phi_i=a_i^++a_i^-\), \(r_i-1=a_i^+-a_i^-\), and

\[
\phi_i-|r_i-1|=2\min(a_i^+,a_i^-)\ge0.
\]

This is a finite convexity/Jensen calculation, not a new general theorem. The difference is zero on one-sided state mass. It measures cancellation at a given mixture, not the objective change after reoptimization. The saved base-point diagnostics reported cancellation at 20/20 K-20-S stations and 31/35 K-35-U stations; after IND, significant cancellation was reported at 0/20 and 3/35. These are reused point diagnostics, distinct from the full reoptimized objective values.

Write \(P_e=\sum_i\omega_i e_i\) and \(\Phi=\sum_i\omega_i\phi_i\), with nonnegative weights. The stationwise inequalities IND, \(e_i\ge\phi_i\), imply the single AP row \(P_e\ge\Phi\). Every integer physical fleet has an objective-preserving extension: select its integer inventory state and set \(e_i=|Y_i/D_i-1|\). Thus AP does not remove physical fleets or alter their original objective.

## 2. A conditional projection result

Let \(x\) include every variable except \(e\). On a fixed legal domain assume:

1. Outside its own local lower and upper bounds (including the two absolute-value inequalities), \(e\) occurs in constraints and the objective only through \(P_e\).
2. Each state penalty is at least every applicable local lower bound and at most the actual finite local upper bound \(M_i\).

Then the original model plus AP and the original model plus IND have identical projections onto \((x,P_e)\).

**Proof.** IND implies AP. For an AP point define \(C=\sum_i\omega_i(M_i-\phi_i)\). Original upper bounds and AP give \(0\le P_e-\Phi\le C\). If \(C>0\), set

\[
t=(P_e-\Phi)/C,\qquad e'_i=\phi_i+t(M_i-\phi_i).
\]

Now \(0\le t\le1\), \(\phi_i\le e'_i\le M_i\), and \(\sum_i\omega_i e'_i=P_e\). All original local lower bounds hold by assumption; every other row and the objective sees the same \(x,P_e\). If \(C=0\), AP and upper bounds give \(P_e=\Phi\), so set \(e'_i=\phi_i\). Zero weights are harmless in both cases. This constructs the IND extension. \(\square\)

The conclusion concerns a projection, not each \(e_i\) coordinate, and not the VD-J equalities. Independent products \(T_{SP,i}\simeq Se_i\), nonaggregate uses of individual \(e_i\), or incompatible local bounds invalidate this proof. Aggregate \(W_{SP}\simeq SP_e\) is compatible because the construction preserves \(P_e\).

## 3. Actual domains and implementation boundary

Pure parsing of both inherited roots finds seven global P-type rows and only local absolute-value/cutoff bounds for the other uses of \(e\). No individual \(T_{SP,i}\) product is active. Their ideal state supports are compatible with the cutoff bounds.

The actual ratio row loads the binary64 coefficient \(c_i=1/D_i\). AP uses \(|c_i y-1|\) with the same binary64 weights. Correctly rounded fma evaluates \(c_i y-1\) once; moving its absolute value one representable step toward zero supplies a lower bound. Multiplication by the weight and a second step toward zero preserve a lower bound on the exact weighted coefficient. RHS terms at most \(10^{-12}\) may be omitted, which only weakens the row. AP coefficients are printed with full binary64 round-trip precision; the legacy near-one abbreviation is bypassed only for this new row. Construction takes place once while building each model, never as a node audit.

The mathematical theorem describes the ideal expression. In the loaded matrix, separately rounded P coefficients need not be exactly collinear as rational numbers. In K-20-S four local state-deviation maxima exceed the old local \(e_i\le1\) bound by about \(0.56\) to \(1.11\times10^{-16}\); K-35-U has no such exception. These do not justify claiming strict rational projection equality for the loaded matrix. The two incremental LPs instead confirm the intended numerical equality under the unchanged policy. No old bound, tolerance, product expression or certificate rule is rewritten.

Default-off exports are byte-identical to the inherited R134 matrices. AP exports differ only by the added row; bounds, types, objective and all other rows remain unchanged. All 990 state coefficients in the two roots pass an independent exact-Fraction downward check. The known complete physical startup fleets have valid selected-state extensions satisfying AP within the existing row tolerance. Every new production Start is additionally checked by the established full mapping/row audit, which includes AP. Existing native model reuse is per leaf and requires the identical canonical-model fingerprint; a changed fingerprint cannot silently reuse a model. Child domains are emitted through the same writer, and LP-to-MIP reuse retains AP while restoring the original variable types.

## 4. R55 is a tested adverse antecedent

At fixed commit 06b4c0634cbb85d3440be88511c736dd3282fdc9, VD-J added stationwise joint ratio and penalty equalities to VD-P. It entered root, pilot and development. The complete R55 stages contain 108 root rows, 32 pilot rows and 42 development rows across candidates; these are not counts of distinct VD-J instances.

The original D13 input is reference/hard_stress/V20_M3/high_imbalance_seed3201.txt, SHA256 ce60fd4e74ad23174be2d4a08ca6e52c0043cee22f3c9b17153b9e8bbcfdbe42. In the old 300-second L0.1.0 subinterval comparison, VD-P certifies with Work 370.2633658; VD-J has no certificate, gap about 0.00772747 and Work 562.3032609. Stronger root bounds did not produce a faster MIP. Only the subsequent penalty-cover DP branch had zero live rows because its prerequisite failed.

R135 uses that same physical input with its original 3,600-second route horizon and the current complete S2 method. Its 600-second whole-method cap is distinct from the historical 300-second subinterval cap. New S2/AP whole-method results are compared only to each other. The later shared service representation and one-row lower bound distinguish AP from VD-J but do not predict its performance.

## 5. Finite decision

Exactly two new continuous LPs compare AP to reused S2/IND values. The whole-method plan freezes 10 first-stage arms (8,760 cap-seconds) and 22 conditional remaining arms (14,760 cap-seconds), totaling 32 arms, 16 pairs and 23,520 cap-seconds. The hard new-computation ceiling is 28,800 seconds. Stage entry is decided by certification, complete time or original-objective endpoints, never by root bounds, Work or nodes alone. All entered adverse and open observations remain in the reports.
