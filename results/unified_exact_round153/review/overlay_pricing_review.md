# Common-refinement price aggregation: independent design review

Decision: **ACCEPT_OVERLAY_MATHEMATICAL_DESIGN** for research-only aggregation
of already qualified prices in a common full inventory domain. This review
uses mathematical reasoning and existing source inspection only. It does not
run Native, recompute a price, or grant an unseen implementation its interface
gate. The rule applies equally to any role whose evidence meets the same
identity conditions.

Let P(Y) be the fixed original-unit price `beta*f(Y) + sum d_i(Y_i)` on the
same complete hard-resource inventory domain R. Require identical scope,
nonnegative beta and exact d over the entire state set. For every imported
full price, L_j is a qualified lower on all R. For every imported conditional
price, l_k is a qualified lower on `R intersect {a_k <= S(Y) <= b_k}`. These
are transported original-unit lowers, not raw Native ObjBound values.

Recompute the common exact positive-S bounds [a,b]. Form a sorted rational
endpoint union containing a, b and all relevant conditional interval
endpoints. Consecutive endpoints form closed cells covering [a,b]; adjacent
cells overlap at their common endpoint. At each cell C define

`ell_C = max(hard-total DP lower, all full-domain L_j,
             all l_k for which C is a subset of [a_k,b_k])`.

Every lower entering this maximum is valid for every feasible Y in that
entire cell, so ell_C is valid there. Every positive feasible Y belongs to at
least one covered cell. It follows that the minimum of all ell_C is a lower
for all positive inventories. Include the exact legal zero-inventory price
as a separate branch when zero is feasible; take the minimum across these
branches and finally the maximum with the previously valid global lowers.
Both maximum and minimum directions are correct. Overlap of closed cells
does not invalidate the bound. Evidence for an interval that merely
intersects a cell cannot be used for that whole cell.

The following edge cases must be explicit in the implementation/auditor:

- If a=b>0, retain the singleton cell [a,a]. Do not silently replace a
  positive singleton domain by an empty list of cells.
- If there is no positive domain, the independently legal zero branch
  suffices. Lack of a Native result or an unsupported/INFEASIBLE Native
  status never proves a cell empty. Such evidence supplies only its admitted
  conservative fallback; a cell without useful conditional evidence still
  has the full-domain DP/global lower.
- Use exact rational containment and endpoints, without tolerance-based
  merging that could omit a region. Validate the common S bounds and full
  positive coverage from the source domain, not just a saved completeness
  flag.
- Bind every full result and imported child to its actual audited source,
  scope/direction, path and SHA. Preserve immutable inputs and an acyclic
  dependency chain. The final auditor must independently rebuild the same
  cells, containment choices and max/min arithmetic.

The upper is the minimum exact price after revalidating the union of all
available stocks in the original full domain and direction. It is a global
inventory-price upper, not a physical routing upper. Absence of a candidate
means an unavailable upper, not an empty domain. Round the published lower
outward down and upper outward up; preserve exact intermediate arithmetic.

For the saved master certificate, use only the resulting complete-domain
price lower and the original exact Q constant/true-column correction:

`C_Q + a_K - max(0, a_K - L_overlay) = C_Q + min(a_K, L_overlay)`.

Recheck the source Q/scope/beta/pi identities as in the admitted refinement
driver. No master re-solve, additional correction, changed feasible set, or
sum of independently corrected master bounds is justified by this
aggregation. Retain the old accumulated lower, upper, stocks, supports and
lineage. A useful overlay is possible when coarse and fine partitions have
complementary strong conditional bounds; no improvement is guaranteed.

Combining the already paid four- and sixteen-part calls requires no new
Native solve or solver-formulation qualification. The new aggregation and
its necessary audit still have their own serial outer cost in the Round153
ledger. This design does not change frozen production helpers or by itself
trigger a partitioned coupled continuation. The concrete new script and
recursive audit branch remain subject to static interface review.

## Concrete implementation review

**ACCEPT_CURRENT_MONOLITHIC_SOURCE_OVERLAY_INTERFACE.** Inspected source:

- `round153_overlay.py`: `6227a33c6ee7e43511ccfae28f5d234d048472462e60081a7d0823eb1f609989`.
- `round153_audit.py`: `8126408d5d0bcd60601baad4fa3d95dd249fbdf6fb08bd50790e9209ad027a53`.
- `round153_reports.py`: `db6fbf7012be5529c16051f56f5b3646d8731719667ee41561a5c802192c7052`.

The driver first audits every complete input and recursively its conditional
children. It binds source/prior/reference Q and scope, source certificate
qualification, beta and exact negative-pi direction. All endpoints and cell
containment comparisons use Fractions. The positive singleton and zero-only
cases are present. Missing child results leave the full-domain DP/global
lower in force. Every retained and imported stock is revalidated in the
same original domain/direction before its exact price is used. The prior
master upper and complete stock/support lineage are retained.

The saved refined certificate reuses the original C_Q and true-column a_K,
then makes exactly one correction with the improved full-price lower. Its
price paths contain the original monolithic result and the new overlay,
which the final refinement auditor can check under the already admitted
source identity rules. The overlay result stores source paths and hashes;
its audit branch rechecks those dependencies and reconstructs the rational
cells and all maximum/minimum operations. The explicit ancestor stack
rejects recursive provenance cycles before using the completed-result cache.
No solver or master optimization is introduced by the aggregation.

The current K35 source is the previously reviewed monolithic
`K-35-U_price_deep/iter00003`, with the four- and sixteen-part prices as
additional inputs. For that declared input pattern, the builder and auditor
agree and no mathematical/interface blocker was found. Execute only after
the active sixteen-part job is closed, and charge the new audit, file reads,
aggregation and writes in its own serial outer receipt. This static gate is
not an assertion that a new overlay result already exists or passed its
runtime audit.

One generic-input inconsistency was identified: the builder gathers
conditional children only from `parents[1:]`, whereas the auditor gathers
them from every parent. If the source iteration itself were partitioned,
the builder could omit useful endpoints/lowers that its auditor expects.
This cannot invalidate a lower (the omitted evidence only weakens it), but
can make the producer/auditor disagree. For a general input interface,
iterate all parents and import children only from partitioned full parents;
other complete parents contribute their global lower. Alternatively,
explicitly restrict the first input to a monolithic result. The current
admitted K35 invocation already has that restriction.

The new research report code reads actual local `iter*/result.json` files
instead of duplicating inherited record arrays, deduplicates complete price
paths with a set, and separates completed local records from phase summaries.
Partitioned parents count their actual child Native calls once; an overlay
has zero new Native calls. Nested or inherited seconds are labeled as such
and are not added to the outer-fee ledger. These descriptive tables do not
turn a checkpoint into a completed study or establish new performance claims.
