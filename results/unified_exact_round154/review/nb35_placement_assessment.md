# Preliminary actual placement comparison: NB35 B/E/J

Reviewer: independent nonimplementer under section H of the adopted Round154
goal. All three NB35 arms are now complete. This assessment reads only their
small sealed endpoints, closeouts, producer/total/outer receipts, frozen
identities, control summaries and first-AM CSVs. It does not run Optimize,
compilation, new qualification, or large raw/audit/model I/O. The other six
registered full arms and final zero-Optimize evidence audit remain outstanding.
This is a preliminary placement result, not nine-arm approval or adoption.

## Paid matched endpoint comparison

All three endpoints have the same NB35 input SHA
`80c75e509adba393e0f693043de0fff7412d97f92ee295465edaa011bde98c98`,
PE SHA `0d3a94183285cc2794676c717a23dc75a47c872ad48c26d2237dd8634f1a5a01`,
DLL, source commit, Seed0 and 2400s cap. All record a complete own-H, and their
sealed closeouts qualify implementation, evidence completeness and performance
eligibility. Their equal own-H outputs are consistent with the frozen
deterministic seed and independent own-H protocol.

| Field | B | E, proof ledger | J, formal floor row |
| --- | ---: | ---: | ---: |
| Own feasible U | 0.450291503262878 | 0.450291503262878 | 0.46039474835411914 |
| Supported L | 0.38931060164210607 | 0.3959564087240911 | 0.39595640872409654 |
| Absolute gap | 0.06098090162077191 | 0.05433509453878688 | 0.0644383396300226 |
| Own-floor helper seconds | None | 14.5403498 | 14.9066291 |
| T_produce | 2371.656277666334 | 2371.3379457800183 | 2371.4636987848207 |
| T_verify | 2.8259734997991472 | 7.515714599983767 | 5.070444399956614 |
| T_total | 2374.482251166133 | 2378.853660380002 | 2376.5341431847773 |
| Outer metered G1 | 2374.5538700998295 | 2378.9349014000036 | 2376.6162244000006 |
| Certificate / T_cert | Open / null | Open / null | Open / null |

All three are verified open endpoints, not closed certificates. Both E and J
pay for the unchanged own-root helper inside T_produce and the original cap;
neither receives a free historical floor. Their helper lower is the same
`0.3959564087240911`, with the same scoped root model, helper and helper
manifest identities. The helper is root-once, node limit 4096, price target
`1e-4`, and uses no offline columns or extra formal root LP.

E preserves B's U and improves the supported lower by
`0.0066458070819850334`. J's supported lower differs from E by only
`5.440092820663267e-15`, while its U is worse by `0.010103245091241164`.
Consequently J's absolute gap is `0.010103245091235724` larger than E's and
`0.0034574380092506907` larger than B's. The tiny J/E lower difference is not
a meaningful scientific gain.

## Actual first AM inputs and selected action

The complete small B and E AM CSVs are byte-identical and contain two rows.
Their first decision has the same root interval, parent/child bounds, score
and selected action. J has one recorded AM decision with different inputs:

| First AM field | B | E | J |
| --- | ---: | ---: | ---: |
| Parent B_p | 0.32783377217711612 | 0.32783377217711612 | 0.39595640872409099 |
| Left B_L | 0.33461961536187856 | 0.33461961536187856 | 0.3959564087240911 |
| Right B_R | 0.5331089723194401 | 0.5331089723194401 | 0.53310897231943999 |
| U at decision | 0.57721794463887988 | 0.57721794463887988 | 0.57721794463887988 |
| Raw left gain | 0.027210400394607499 | 0.027210400394607499 | 6.1249785787265581e-16 |
| S_AM | 0.01156902990287594 | 0.01156902990287594 | 2.3172497954388298e-16 |
| selected_action | native-target | native-target | exact-close |
| native_target | 0.33461961536187856 | 0.33461961536187856 | Empty |

B/E report the reason `adaptive_mass_score_below_tau_native_target`; J reports
`adaptive_mass_no_strict_child_improvement`. Thus J's formal floor raises the
logged parent and left-child inputs to the same floor level and eliminates
their strict left improvement at this decision. The same AM policy then logs
a different action. E leaves those search/AM inputs identical to B in this
actual comparison. The string `exact-close` names a selected action; it does
not mean J obtained a final global certificate.

## Formal model identity and proof placement

The E control summaries record three actually called models, with equal
base/model SHA for each and zero formal floor rows, and five passing Native
floor audits. J has the same three base-model SHA values, a different final
model SHA for each, and exactly one floor row in each model; its four Native
floor audits pass. Both control summaries preserve original columns, bounds
and objective, report zero formal new columns and confirm helper payment
inside the process. This is direct small-summary evidence of a placement
contrast, rather than a different own-floor producer.

E additionally retains raw search L `0.3892936193183539`, below B's L, and
uses the qualified complete-root scoped floor in its separate proof ledger.
That ledger reports source live, zero Native floor rows,
`AM_uses_search_bounds=true`, and `proof_stopped=false`.

The observations identify the local mechanism: putting the floor in J's
formal model changes the bounds delivered to the first AM calculation,
whereas E's placement preserves the B inputs there. They do not establish
that this first AM decision alone caused J's poorer U. Paid helper time,
different formal-model solve behavior and subsequent legal search choices
also alter the finite trajectory. No sole-AM or universal performance claim
is justified by this single-role, single-seed placement comparison.

## Small identities and scope of verification

I checked the small closeout, producer/total receipt and frozen group identity
hash links, endpoint time tuples, zero exit codes and all three open/null
certificate states. Endpoint audit SHA references agree with their closeouts.
Large audit bodies and MPSs were not reopened during the active Native queue;
the final finite audit retains those duties.

| Evidence | B SHA256 | E SHA256 | J SHA256 |
| --- | --- | --- | --- |
| Endpoint | `474a1275fbe4720bbd9bddbd47084552cb3f90bcf1d7c8739a3b0ed628d2fa53` | `c44ef27c6235c496f9aab85ca13e9fc4c6b1008722c6b2afa07fec692b86b218` | `a5b6cc5e4cc2a6f5081cabac837a22e013788161cf47f59908fb8a18428a98ee` |
| R153 control summary | `18caf406b5a9c3280c22bd977386ab3f671a2a9bc6795241ec325776548afd17` | `2997029a5021509d306577d8c65bbc679ff87f6c2ab7f95ea691cf6fec93d4de` | `d385e31d454d01de3254f5a2333745139056b8e38586999155ce38625ec972ad` |
| AM CSV | `865ace245097630b68771f7b39c78bf8892367d30438443de392f52bcd811104` | `865ace245097630b68771f7b39c78bf8892367d30438443de392f52bcd811104` | `00f2b1933bc0cc64b3e0a2e592b8bc6f0d8dc8adb9965e2f8f9873e154c730f1` |

The three closeout hashes are respectively
`2baaf183209461ec6111bf4fc91fcfed5e405972c58afbe0336df82f5f5635ea`,
`75f1557cec4641b45e4239d9bb06ff4ea339a3e6a50fad85066440993e24aa95`,
and `399c9eb4ce0cdf9234b3940faa40757968a6a107627949196cf9038d870155fc`.

Disposition: NB35 exhibits a useful paid E proof-bound gain while keeping B's
U, and confirms that J changes the actual AM inputs and action. Retain this
finite result without adopting E or J. Final panel and scientific approval
remain held until all nine arms, actual finite audit and final claim review.
