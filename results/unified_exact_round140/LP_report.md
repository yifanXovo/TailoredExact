# Round140 finite same-domain LP evidence

Nine new continuous LPs, plus four matching R138 reference pairs. All new solves explicitly use Seed0, one thread and serial execution. The failed Path-type attempt occurred before Optimize, is preserved, and is charged. The same validated U, exact g endpoints, cutoff and source model SHA are retained within each role.

| Role | STK L | STK+TC L | STK+TC+TC2 L | TC2 increment | thresholds | ell>0 |
|---|---|---|---|---|---|---|
| K-20-S | 0.2045904392 | 0.2245420209 | 0.2348218779 | 0.01027985698 | 137 | 57 |
| R-B35-S-T2 | 0.1291512915 | 0.1342432954 | 0.1354492348 | 0.001205939385 | 96 | 30 |
| R-X35-S-T2 | 0.1931361142 | 0.1945218656 | 0.1947597626 | 0.0002378970184 | 66 | 15 |
| K-35-U | 0.218088779 | 0.218088779 | 0.2260440515 | 0.007955272454 | 130 | 120 |
| R-X20-S-T1 | 0.3775575303 | 0.3775575303 | 0.377563941 | 6.410663424e-06 | 44 | 17 |

Saved-point violation, an optimized bound increment and a complete-method outcome are different claims. All five new optimized bounds rise over old TC+stock; RX20 is a small increment of about 0.0000064. The new rows add two aggregates and no columns over stock. Full-precision H_sum, G, J, tau, U, quality, row counts, construction/Optimize cost and frozen identities are in reports/LP.json and the original per-position result records.

| Role | budget adds q>0 | forced-only ell>0 | maximum q |
|---|---|---|---|
| K-20-S | 30 | 27 | 3 |
| R-B35-S-T2 | 30 | 0 | 9 |
| R-X35-S-T2 | 15 | 0 | 5 |
| K-35-U | 56 | 64 | 11 |
| R-X20-S-T1 | 0 | 17 | 0 |

RB35-T2 and RX35-T2 have no forced-high stations at any threshold: the positive lower counts and resulting bound increments require the inventory lower budget. RX20 has q=0 at every threshold; its small TC2 improvement instead comes from using forced-high support information that the old zero-lower chord did not use. K20 and K35 combine both sources, without an unsupported additive allocation of their objective gains.

| Role | G | H_sum | J | tau | validated U |
|---|---|---|---|---|---|
| K-20-S | 0.06273816025 | 24.41972501 | 13.04953733 | 208 | 0.7752127578 |
| R-B35-S-T2 | 0.01082702034 | 12.64351094 | 2.555176799 | 236 | 0.445489809 |
| R-X35-S-T2 | 0.01097567639 | 14.96350547 | 1.602448753 | 146 | 0.4246498452 |
| K-35-U | 0.0645055729 | 95.4750034 | 21.02881676 | 295 | 0.7674566047 |
| R-X20-S-T1 | 0.1466823302 | 53.37373737 | 9.534351461 | 65 | 0.7530539181 |

The K20 no-stock complement is fully matched: BASE .19514915244120534; old TC .20262525298673523; TC+TC2 0.20858139786972. Stock+TC+TC2 reaches 0.23482187788475. The RB35-T2 no-stock TC+TC2 auxiliary reaches 0.13009679814596; it is not represented as a complete no-stock BASE/TC ablation panel.

The related return-product alternative is screened offline only. All four old stock points admit an extension within numerical residuals. K35 old TC+stock violates one linear R_k<=Q_k upper bound before any product claim; B=326, tau=295. No third complete-method benchmark line is introduced.
