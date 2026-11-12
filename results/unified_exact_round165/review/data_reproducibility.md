# Independent data and reproducibility review

Reviewer: actual separately spawned agent `/root/data_review`.
Review completed: 2026-11-13 04:24–04:25 Asia/Shanghai.
This is an independent agent read and offline recomputation, not an independent
human review or a licensed performance replication. No solver call, production
build, new performance observation or user-file mutation was performed.

**Result: numeric/CSV/source-assembly checks PASS.** There is no finding that
changes a reported certificate, endpoint, method decision or scientific
denominator. Two presentation/provenance defects and one study-map omission
should be repaired before the final document freeze. All were communicated to
the parent while the review was active; the parent acknowledged the first two
and is applying targeted export/figure fixes.

## Actionable findings

| Location at review time | Finding | Consequence and repair |
|---|---|---|
| `scripts/round165_audit.py:150–165`; `figures/three_seed_endpoints.png`, B20-B subplot; main PDF p.18 | The certified B20 endpoints auto-scale to a roughly 1e-10 axis span with an offset near .423232181. It visibly magnifies residuals far below the declared 1e-7 endpoint-equivalence scale. | No source value is wrong, but the visual implies a meaningful within-input difference where the paper classifies equivalence. Use a sensible minimum objective-axis span or an explicitly equivalent display, keeping the raw 36-row analysis CSV unchanged. |
| `results/unified_exact_round165/document_build.json`, `versions.xelatex`; `scripts/round165_documents.py` version collection | The captured value is the first combined-output line, `xelatex: security risk: running with elevated privileges`, rather than a XeTeX/MiKTeX version. | The required tool-version trace is incomplete. Retain the actual version line or full `xelatex --version` output; no PDF or experiment rerun is needed solely to obtain that metadata. |
| `paper_body.md:257–267`, Table 1 | The registered-study map lists the historical R137 blocks and the subsequent cohort Seeds1/2, but has no explicit Seed0 B/E+/P row identifying its 18 observations, including six E+ runs. Section 5.5 and Table 8 state the correct scope. | A study-map completeness issue, not a false denominator. Add a six-configuration/18-arm Seed0 cohort row, and describe the later 24 new B/P arms as reusing the 12 historical B/P observations. Do not sum shared observations twice. |

The root agent separately reported export-flow problems found during its PDF
visual review (Table 1 split, isolated landscape headings and a small appendix
spill). Those are not represented here as independent discoveries by this
reviewer. My own visual inspection of the actual data figure established the
B20-axis finding above.

## Independent checks and evidence

The retained [offline check script](data_review_check.py) executes only data,
hash and assembly reads. [Its receipt](data_review_checks.json) records **233
checks with zero failures**, plus the actual reviewed source/PDF hashes.

- All 24 current R164 complete-arm records equal the fixed numerical JSON at
  `b93a8a01ff1b7f3cbee67807be3ac6591db4767f`, and all 18 historical R163
  records equal the R163 delivery version. Every one of the 18 paired
  records' U, final proof L, state and paid certificate time matches its
  original arm; all signed differences recompute correctly.
- The six inputs yield 18 B/P pairs and 36 distinct method observations.
  Seeds1/2 contribute 24 new observations; Seed0 is historical reuse. Each
  Seed has B3/6, P1/6 and a joint-CERT intersection of B20 alone, 1/6.
  Every n35 B/P observation remains OPEN with null certificate time.
- The exact 36-row figure CSV reproduces all original U/L and states. The
  six panel labels, historical/additional Seed distinction and CERT/open
  marker definitions are appropriate, subject to the B20-axis repair.
- C35 has signed U directions +/−/− and L directions +/+/+. Its historical
  P Seed0 objective `.09331934374779818` is below every B objective
  `.12956638965196035/.10742986645444105/.10808393649972804`. These facts
  are stated together in the maintained text and survive PDF extraction.
- E+ is confined to six historical Seed0 observations. All six E+/B U
  endpoints are equal. Only X35's final proof L changes materially,
  `.3949882559151472` to `.42319954961578576`. Its three joint-CERT paid
  increases recompute as 26.1043577623, 1.6982945520 and 6.1773453336 s;
  only C20 exceeds max(10 s, 10% of the faster time). No new certificate or
  E+ multi-Seed inference is introduced.
- All 36 original target-arrival records retain false exact-first-discovery
  and production-target-use flags. The table preserves observed availability
  intervals versus censoring. C35 B never reaches the pre-frozen target;
  both added X35 B observations remain unreached. The main text explicitly
  keeps these absolute-target deficits alongside favorable relative signs.
- R137 has 120 unique measured positions. Breadth certificates are 9/12,
  7/12 and 7/12, and resource certificates are 4/8, 0/8 and 0/8. Open
  observations across the three generations retain null T_cert. The main
  text conditions runtime ratios on joint-CERT subsets and retains distinct
  historical panels rather than pooling a new overall success rate.
- Actual available CSVs are 91/91/103 rows. The 103-row working master has
  28 columns, and each of the 12 exact R164 increment rows occurs once.
  Both actual external user-file hashes and the working-master hash remain
  unchanged. No 106-row input was found or claimed; the three unavailable
  historical N/A-P rows are explicitly recorded. There is no new row to add.
- The assembly is exactly current body plus complete Appendix A/B. Every
  component hash and both output PDF hashes match their current manifests
  at this review snapshot. The body/appendix source identities are distinct
  from later measured C++ `e920b92e199e825ec89a2932f701861ff158e0d4` and
  the fixed numerical/science/delivery commits.

## PDF/readback scope and limits

I extracted the complete actual 53-page manuscript and 48-page supplement
PDFs and checked the latest cohort tables, C35 absolute objectives, E+
endpoint and three-Seed narrative against their maintained sources. Removal
of extraction whitespace recovers the full-precision C35/E+ constants in
the main PDF. I inspected the actual three-Seed figure visually. I do not
claim an independent full-page typography review of every PDF page; root's
actual page-render QA supplies that separate acceptance.

The receipt binds the reviewed initial PDF hashes
`36e42223ab2ee6e45e2ff9d612dd7dfcd38ef438c331ed2a901ccaf03adb1fd0`
and `f09ca0004d918918db5dda04244528864266c0c9e148e90e21ee255143ab4b9e`.
Later repairs should update document identities and verify only the affected
figure, study-map row, tool metadata and PDF pages; unchanged history does
not require a solver or wholesale raw-data replay.

## Post-correction targeted closure

The parent requested a bounded readback of the three findings. All three are
**CLOSED**. I read the corrected Table 1, the plot's current axis rule and full
version receipt, and visually inspected the actual revised endpoint figure.
B20 now has a .04 objective-axis span centred near .423232181 and no offset
notation; sub-tolerance residuals are no longer visually exaggerated. The
analysis CSV still has 36 rows with exactly the original paired U/L values;
no endpoint or raw source was changed. Table 1 explicitly lists six inputs
and 18 B/E+/P Seed0 observations, while the next row retains the 24 added B/P
arms and their 12 historical B/P comparison observations. The build receipt
now retains full version text including **MiKTeX-XeTeX 4.16 (MiKTeX 25.12)**.

Current readback identities:

| Object | SHA256 |
|---|---|
| Maintained body | `eaed6620eafb6e85619480e556562a9dfd58447dec0bc0224c884500a54e1dbf` |
| Corrected three-Seed figure | `d13d9b41d03fd291ba9e2b307115ab7a126456ac15513faafab3f661291f4fa6` |
| Original-valued analysis CSV | `af907e40f2f20a6596c2ab88650868724628754b8a5799a1e9d4b20648a168cb` |
| Actual current main PDF, 52 pages | `3b24cdd828e666cb491dcb7a421889fdc4623eb05a2fe6b7a9087d290957dc71` |
| Actual current supplement PDF, 39 pages | `5bebe69ae5d7b090ebe4dc0de8114e276ad5d1a9a1e72c234575cfde89cebbeb` |

Both current PDF hashes match `document_build.json`. Page counts were read
directly from the current PDFs, not inferred from a file's existence. At this
targeted read, the QA receipt still carried an intermediate 41-page supplement
count; the parent was notified to synchronize that receipt to the actual
39-page output. This closure does not claim another independent full-page
visual pass or repeat the 233 unchanged historical checks. **Data review is
PASS with no remaining scientific/data finding.**
