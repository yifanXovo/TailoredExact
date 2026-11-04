# Independent readback of closed cut-pricing evidence

Reviewer: `/root/independent_review`, 2026-11-04 (Asia/Shanghai).

Decision: **ACCEPT_SMALL_QUALIFICATION_AND_BOUNDED_RESULT_CLAIMS**.
Only closed JSON metadata, plans and receipts were read. The reviewer did
not replay a flow certificate, enumerate stocks, load a Native model,
Optimize, compile or inspect the active NC20 long-price work. This closes
the small interface admission at the inspected source identity; the final
finite scientific audit remains required.

## Small qualification

`qualification/graphcut_v1/result.json` has SHA256
`1688b330caaf52fec579051434c910e30698874c2d0a59ae33077321893e3f70`
and reports PASS with the admitted graph source
`6cb2fa990c259e15d5faf696c4626f1c86165dbef55489de3ab9a72f3ca986c4`.
All six complete-price controls bind the frozen price core SHA
`8ed325356a9171a3e1aaafbc4a5c0526a764f0c35148dd6de2ea15d0d925e558`.
The record contains 3744 Cartesian energy checks and three rejected altered
flow records. The station domains have 125, 25 and 6 Cartesian labels,
with 49, 5 and 5 truly legal stocks respectively.

Both beta=0 and beta=1.7 are covered. Some controls close at the exact DP
and a legal stock without graph calls; other controls, including the tight
G-cap beta-zero control, exercise saved integer flows and candidate LPs.
Their true enumerated minima lie in the reported brackets. The wide small
brackets are not mislabeled as exact price solutions. There are 22 Native
candidate LP calls in total: this is zero Native MIP pricing, not zero
Native Optimize. The clean outer receipt charges `1.5005382001399994`
seconds, with observed exit zero, no timeout and no supervisor failure.

## Two fixed-direction probes

Both plans reference the previously admitted exact source certificate,
price and Q identities. Both use 16 positive-S slices, a maximum of 20
candidates per slice and a 600-second offline search allowance. The saved
records show all 16 slices completed, the same qualified graph/core source,
and complete-domain status. Their candidate search stopped before the
allowance; it was not necessary to spend the unused cap.

| Probe | Price lower | True-stock price upper | Integer flows | Candidate LPs | Charged outer seconds |
|---|---:|---:|---:|---:|---:|
| NC20, continued iter00008 | -0.05657158567373699 | 0.00726560247528965 | 64 | 64 | 10.837436700006947 |
| K35, price_deep iter00003 | 0.010065412826406828 | 0.021471812805363297 | 73 | 73 | 13.800380900036544 |

Both price decisions remain UNDECIDED. Both probe receipts are cleanly
closed, and neither runs a new restricted master. NC20 preserves the
complete-hull interval
`[0.1794922765112552, 0.1906059418573794]` and retains 282 legal columns,
four more than the earlier continuation. K35 preserves
`[0.2826236515522649, 0.28749181051555994]` and retains 1043 columns,
seven more than the preceding long-price result. These are strengthened-LP
value intervals; the inventory price uppers are not physical routing
incumbents.

The price result SHAs are respectively
`c962f4182beaacf1ab9eeafa092c122f1d7064fd9df7436ff303e4d5b2cb0419`
and
`880c7369eb9f358b148336f5f51ad5830fc191430876f62872531e518b620e98`.
The NC20 source remains `N-C20-U_level_zero_continued/iter00008`, Q SHA
`fefd769b819d36a93dfaa8dc39670512109323cdd0123366e768443cdf2a1d45`.
The K35 source remains `K-35-U_price_deep/iter00003`, Q SHA
`9816772328dd5e53c0dfd00e5f714fbaf08d2f93ac3cf0652ce5226a2452fcb5`.

## K35 long-price reference and interpretation

The immediately preceding K35 3600-second, one-positive-slice refinement
closed normally with outer cost `3601.784241599962` seconds. Its qualified
Native TIME_LIMIT return records runtime 3600 seconds and 621815 nodes.
Its price bracket is
`[0.020410302194370473, 0.021471812805363297]`, still about `0.00106151`
wide. The same Q/source direction yields the improved cumulative lower
`0.2826236515522649`, with unchanged upper `0.28749181051555994` and gap
`0.004868158963295066`. Its saved result has 1036 columns. The price JSON
SHA is `c74b9c20a16a098ef1566d18ed6514aa785337d48ddc7a494eb8783b3ec25173`.

Thus the longer qualified price produced useful progress, while both short
cut probes produced weaker price lowers and some extra legal columns.
Describe the cut probes as fast but yielding loose attained bounds on
these two fixed directions. The evidence does not isolate denominator
relaxation, resource/Lagrangian relaxation, the finite parameter box and
candidate search as separate causes, and does not prove an unavoidable
relaxation gap or a family-wide negative result.

Retaining the stronger prior bounds and declining a graph-oracle switch
is consistent with the predeclared probe scope. The admitted original
NC20 long price, both zero_pool continuations, free-Q support transfers
and frozen eight-arm comparison remain in force. No production adoption,
new engineering or new experiment is requested by this readback. These
wide intervals remain active research checkpoints, not study completion.
