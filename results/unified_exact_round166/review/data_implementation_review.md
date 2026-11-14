# Independent implementation review, initial static pass

Reviewer: the independent `data_review` agent. Reviewed 2026-11-14 (Asia/Shanghai).
No Optimize calls or source edits were made by this reviewer. This pass covers
the actual working-tree implementation; the new C++ qualification driver and
the formal B/C166 matrix are still pending and are not claimed as reviewed.

## Finding and correction

**Entry identity bypass (corrected, read back).** Initially, C166's algorithm
identity and isolated-B compatibility checks in `src/main.cpp` depended only
on `round166Breakpoint()`, while the public uniform-policy parser independently
accepted `round166-breakpoint-bit`. A caller supplying only the policy could
therefore select the new matrix without selecting the new reported algorithm
identity or running the new compatibility guard. I reported the concrete
entry to the primary agent. The primary agent added, immediately after
`applyAlgorithmPreset(opt)`, an error when the C166 policy appears without
the explicit candidate flag; with the flag, the policy is set explicitly.
I read back that correction and searched all references to
`external_gini_interval_mip_policy` in the full CLI source. There is no later
explicit-argument restoration overwriting the binding. The normalization
before the preset is followed by the corrected binding after the preset.
The frozen formal matrix is expected to use `--round166-breakpoint on`.

## Positive static checks

- `include/Round166Research.hpp` is a default-off process-local research
  switch. Support generation uses only legal lower/upper/initial stocks;
  it returns an empty vector for an empty interval and deduplicates endpoints.
  No instance alias, historical outcome, hardware feature or elapsed time
  enters support selection. `long long` is used around initial +/-1.
- `src/Round50IntervalMip.cpp` has a separately named C166 policy resolving
  to `station_state_formulation="breakpoint-bit"`; it keeps default native
  branching, no subset-duration variant, and the same clean callback policy.
- In `src/CplexBaseline.cpp`, `station_state_c166` is deliberately *outside*
  `station_state_value_disaggregated`. It consequently adds continuous
  breakpoint t/q columns **and** retains the original absolute-Y binary
  bit/product columns. In particular, the shared interval-row filter at
  approximately lines 1160-1165 filters tightened bit McCormick rows only
  for the old value-disaggregated modes; it does not filter them for C166.
  The original 3 per-bit product inequalities, interval tightening, and
  Y/Z reconstruction therefore remain in the actual new matrix.
- The breakpoint block at approximately lines 2995-3023 emits mass,
  inventory, aggregate movement, aggregate visits, g reconstruction and
  Z reconstruction with the declared coefficients. The q bounds are
  alpha*t <= q <= beta*t. The visit row is written as
  sum_k z_ki - sum_{a!=b} t_ia = 0, algebraically equivalent to B's
  sum_k z_ki + state_i,b = 1. No additional linked-direction or vehicle
  theta equation is inserted.
- Original r/Y and e epigraph constraints remain outside both representation
  blocks; C166 does not emit VD-J ratio/penalty equalities. The original
  objective still uses G + lambda*sum_i omega_i e_i. Physical SCF/MTZ,
  unique assignment, direction, load and route-time rows are unchanged.
- Empty tightened domains retain `domain_infeasible` and the explicit
  impossible row `0 <= -1` at approximately lines 1205-1208. Reset storage
  bounds do not revive physical feasibility.
- `src/MipStartMapping.cpp` obtains each station's *actual generated* t
  support from the native column names. It assigns an interior physical Y
  to its adjacent support endpoints, and q=G*t. All unused t/q columns get
  zero. The pre-existing semantic cases still map bit=the absolute-Y bit,
  prod=G*bit, and Z=G*Y. Bounds/integrality checks remain in place and the
  native Start path still reads the full matrix and checks its rows and
  original objective. A legal non-breakpoint physical inventory is retained.
- `src/GurobiBaseline.cpp::prepareRound68Start` explicitly accepts the new
  policy, including its validation-only path. This avoids disabling own-H
  Start merely because one-hot selectors no longer exist.
- LP-to-MIP restoration in `GurobiBaseline.cpp` captures and restores the
  complete native VType vector, rather than applying state-name heuristics.
  Thus the generated bit binaries and continuous t/q receive their proper
  types. Failed restoration invalidates the LP result. Actual runtime
  restoration still requires the scheduled diagnostic evidence.
- `PaperExternalGiniTree.cpp::ensureArtifact` obtains the representation
  from `parseRound50IntervalMipPolicy` for root, child and epoch artifacts.
  It retains immutable generation-specific LP files, SHA-bound row identity,
  and discards the leaf's native model and LP evidence on cutoff-epoch changes.
  The backend rejects retained models whose requested canonical SHA changed.
  Generic SHA/type machinery therefore recognizes the new actual columns;
  it does not require a new opaque-state migration scheme.
- The CLI guard rejects AP, stock/count/selector/RN and later research
  combinations, linked/projection/vehicle-state service, omitted A/B/CR/CG,
  R101-R107 extensions and both newer physical-completion controls. Existing
  isolated-ENS checks reject unrelated old route/load/callback mechanisms.
  Writer-side stock-RLT already rejects any non-VD-P representation, in
  addition to the new direct guard against AP/count/RN. There is no silent
  state-column substitution for unsupported combinations.
- With C166 off and the old VD-P spec, every new emission block is skipped,
  and none increments the row ID or adds a column. A canonical byte/diff
  check is still required to substantiate unchanged B export semantics.

## Scope still requiring actual evidence

The static implementation is consistent with the declared isolated-B
representation after the entry fix. This is not yet formal-batch admission.
The primary agent must retain the scheduled C++ LP/MIP driver outputs,
non-breakpoint tiny physical optimum, all-six matched roots/two children,
complete Start row/objective residuals, generic type restoration, source/PE/DLL
bindings and actual native parameter readback. Complete paired producer logs,
cost/coverage qualification and CSV semantics need a later independent pass.

The six recovered R163 parent fleets under `qualification/parents/` are
explicitly offline qualification fixtures. Their manifest pins the historical
B owner, input/carrier/member/output hashes and independent physical checks.
They must not be supplied to either formal performance arm.
