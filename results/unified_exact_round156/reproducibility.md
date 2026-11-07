# Reconstructing the finite Round156 evidence

The final public manifest binds only the necessary new Round156 evidence.
The old inputs, original root models, old price witnesses and R155 time
chains are references to fixed commits and archive members in
`reuse_index.json`. No old complete-Q or large inventory pool is repacked.
The source manifest distinguishes the measured production commit from the
later report/reader revisions. Each experimental launch also retains exact
new source bytes by digest, including the unsuccessful startup attempts.

Use the final scientific Git commit to obtain the source tree. The
`public_manifest.json` lists the new thin files, archive pieces, compressed
archive digests and exact member indexes. The bounded anonymous recovery
uses that fixed commit, checks all downloaded bytes and extracted members,
and performs no optimization or compilation. It does not claim that a
new-only evidence directory contains every inherited software dependency.
Resolve inherited modules and selected historical files through the fixed
Git/tree/member references before running a reader on another machine.

Residual models use one fixed `base.mps` per oracle and exact
`matrix_delta.json.gz` files. A delta contains the base digest, dynamic
rows, cost-variable bound changes, complete row order and complete semantic
digest. Original absolute paths are retained as provenance; they are not
silently rewritten in the scientific record. `round156_reconstruct.py`
maps a recorded path under the original workspace to an explicitly supplied
restored workspace, verifies the base SHA256, replaces the dynamic rows,
applies the exact bound changes and checks row order and semantic digest.
It rejects paths outside that original prefix or the restored root and
does not call Optimize. For example, in a Python process with the qualified
Gurobi binding and environment:

```python
from pathlib import Path
from round156_reconstruct import reconstruct

restored = Path(r"E:\codes\ExactEBRP-work\restore\accepted-evidence-tree")
original = Path(r"E:\codes\ExactEBRP-work\worktrees\round156")
delta = restored / "results/unified_exact_round156/oracle/R-X35-S-T2/residualU16384_v1/price_001/matrix_delta.json.gz"
with reconstruct(delta, gp, env, restored, original) as model:
    pass  # Full semantic readback has already passed; no Optimize is run.
```

Use the actual indexed delta filename; call positions are preserved rather
than renumbered during recovery. The online RN prices additionally retain
their complete `model.mps`, original-coefficient dictionaries, anchors,
numerical guard, actual objective correction and legal inventory stocks.
`round156_complete_review.py` reconstructs these prices separately from the
producer. Existing physical-route and chronological endpoint audits are
reused and hash checked; the reader does not overwrite a sealed audit.

Complete-arm launches in `confirmation_matrix.json` preserve the original
model T and lambda, own-H seed 20260626, Gurobi Seed 0/Threads 1, fleet and
AM settings. The experimental window is a separate quantity. B, E and E+
use the same new executable. E uses the unchanged 4096-node entry; E+ uses
the explicit RN16384 protocol. Each paid arm owns its own H, scope and
floor, and neither inventory uppers nor offline stocks enter a physical
incumbent. A reproduction must retain that separation and the full outer
cost rather than invoke the helper for free.

The exact new PE is retained under the Round156 build cache and bound by
its SHA256, measured source commit, compiler recipe and link inputs. The
preexisting Gurobi DLL and interpreter are referenced by exact identity
and reused read-only, not redistributed in the evidence archives.

All scientific outer receipts are counted once in `cost_report.json`.
Nested solver Runtime/Work, H and helper times are explanatory components.
The administrative setup gap, separate compilation, pure writing and
publication I/O are disclosed. Review means separate arithmetic/model
reconstruction by the same research agent; no independent nonimplementer
agent or previously unseen holdout is claimed.
