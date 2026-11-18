"""Synchronize current repository navigation with the qualified Round171 paper."""

from round171_common import BRANCH, MASTER, OUT, PR_BASE, ROOT, read
from round171_writeup import describe, prose

REL = OUT.relative_to(ROOT).as_posix()
MASTER_REL = MASTER.relative_to(ROOT).as_posix()
PAPER = "results/unified_exact_round137"


def replace_once(text, previous, updated):
    assert text.count(previous) == 1, previous
    return text.replace(previous, updated, 1)


def repository_navigation():
    decision = read(OUT / "decision.json")
    stats = decision["stats"]
    master = read(OUT / "CSV_reconciliation.json")
    authority = f"[Authoritative benchmark CSV]({MASTER_REL})"
    first = ROOT / "README.md"
    text = first.read_text(encoding="utf-8-sig")
    text = replace_once(text, (
        "The current R170 manuscript includes\n"
        "the fixed paid-initialization confirmation and matched cold controls; the\n"
        "mixed/negative result closes further C169 optimization. C166/D167/C169 stay off."
    ), (
        "The current manuscript includes six prospective 50-station B/P comparisons at\n"
        "one 1,200-s cap. The earlier fixed paid-initialization confirmation closed\n"
        "the C169 line. C166, D167 and C169 stay off."
    ))
    text = replace_once(text, "the\n[advisor/coauthor review packet](docs/paper_review.md).", f"the\n[author review packet](docs/paper_review.md). {authority}.")
    text = replace_once(text, "[current author memo](results/unified_exact_round170/author_decision_memo.md)",
                        f"[current author memo]({REL}/author_decision_memo.md)")
    text = replace_once(text, (
        "performance value of the outer controller. The [R170 report](results/unified_exact_round170/final_report.md)\n"
        "separates nonrepeating candidate gains, C20 proof-cost regressions and three\n"
        "new same-budget B/P endpoint advantage observations."
    ), (
        f"performance value of the outer controller. The [Round171 report]({REL}/final_report.md)\n"
        "gives the new paired n50 endpoints and paid costs. The [Round170 report](results/unified_exact_round170/final_report.md)\n"
        "retains the fixed candidate and matched cold findings."
    ))
    text = replace_once(text, (
        "record. R170 uses the isolated " + chr(96) + "ExactEBRP-work/worktrees/round170" + chr(96) + " checkout\n"
        "from verified R169, retaining the dirty R155 " + chr(96) + "paper-current" + chr(96) + " entry."
    ), (
        "record. Round171 uses the isolated ExactEBRP-work/worktrees/round171 checkout\n"
        "from verified Round170."
    ))
    prose(first, text)

    path = ROOT / "docs/current_mainline.md"
    text = path.read_text(encoding="utf-8-sig")
    headline = "# Current manuscript and research mainline\n\n"
    section = f"""## Round171 prospective positive n50 evidence

{describe(stats)} B remains uniform, with C166, D167 and C169 disabled.
The main evidence appears in §4.7 and Supplement S171. The previous
n15/20/35 panels retain their original roles. The six n50 configurations
use archived source geometry, synthetic operational inputs and one Native
Seed. The scope at n50 is the complete-method comparison.

[Round171 report](../{REL}/final_report.md) · [Research decision](../{REL}/research_decision.md) ·
[Current paper](../{PAPER}/manuscript.md) · [Main PDF](../{PAPER}/manuscript.pdf) ·
[Supplement PDF](../{PAPER}/supplement.pdf) · [Authority and provenance](../{MASTER_REL})

The CSV authority contains {master['records']} records with its original 126-record
byte prefix. Six new rows link to the frozen data commit. The local
round directory keeps the increment and reconciliation.
[CSV reconciliation](../{REL}/CSV_reconciliation.json)

## Round170 candidate confirmation (historical)

"""
    prose(path, replace_once(text, headline, headline + section), preserve_newlines=True)

    path = ROOT / "docs/paper_review.md"
    text = path.read_text(encoding="utf-8-sig")
    start = text.index("There is one maintained paper directory.")
    stop = text.index("The retained Round166 evidence")
    text = text[:start] + f"""There is one maintained paper directory. The current [Round171 report](../{REL}/final_report.md),
[decision](../{REL}/research_decision.md) and [author memo](../{REL}/author_decision_memo.md)
give the six prospectively generated n50 comparisons. {describe(stats)}
The new main table is in §4.7 and the complete arm, cost and controller
evidence is in Supplement S171. B remains the uniform method. The preceding
[Round170 confirmation](../results/unified_exact_round170/final_report.md)
retains its mixed and adverse findings, including the fixed C169 decision.

""" + text[stop:]
    tail = text.index("Current independent mathematics, execution/data")
    text = text[:tail] + f"""Current mathematics, execution/data and research/manuscript checks are in
the [Round171 review directory](../{REL}/review). The
[benchmark CSV](../{MASTER_REL}) is the current authority, with an exact
126-record prefix and {master['new_B_records']} qualified new B rows.
[CSV reconciliation](../{REL}/CSV_reconciliation.json)

Build the current components with the Round171 document entry point.
Run assemble, pdf and qa in that order.
[Build script](../scripts/round171_documents.py) ·
[Build record](../{REL}/document_build.json) · [Page QA](../{REL}/document_qa.json)
"""
    prose(path, text, preserve_newlines=True)


def pr_body():
    stats = read(OUT / "decision.json")["stats"]
    cost = read(OUT / "cost_report.json")
    master = read(OUT / "CSV_reconciliation.json")
    uri = f"https://github.com/yifanXovo/TailoredExact/blob/{BRANCH}/"
    text = f"""The current pair-only GI-TBC had direct complete-method evidence through 35 stations.
Earlier K1 and M-B/ENS studies reached n50 and n100 under predecessor protocols.
This panel extends the direct evidence for the frozen method with six prospectively
generated positive-objective n50 configurations.

Each archived CITI, CABI and Divvy source contributes disjoint compact and regional
station sets. Operational quantities are synthetic or transformed. The frozen B
pays one full own H per process. Cold compact P uses zero submitted starts. All
12 Seed0 positions use the same C++ PE and Gurobi DLL and a serial 1,200-s whole-process
budget. The input-derived route horizon is separately fixed.

{describe(stats)} The 12 producer processes took {cost['process_outer_seconds']:.2f} s
in total. They executed {cost['LP']} LP and {cost['MIP']} MIP calls. B's controller
accepted {stats['B_split']} splits and recorded {stats['B_requeue']} child-target
parent requeues. The full/root controls leave the controller's independent speed
effect unresolved. The new scope is six finite archived-source shortage configurations
under one Native Seed and one cap.

The current manuscript keeps the earlier adverse results and the fixed C169 decision.
B remains the uniform main method. The authority keeps the exact 126-row byte prefix
and adds {master['new_B_records']} B observations and {master['new_strict_pairs']} strict matched pairs.
The stacked base is the Round170 delivery branch, {PR_BASE}.

- [Report and paired endpoints]({uri}{REL}/final_report.md)
- [Current main PDF]({uri}{PAPER}/manuscript.pdf) and [supplement PDF]({uri}{PAPER}/supplement.pdf)
- [Authority CSV]({uri}{MASTER_REL}) and [reconciliation]({uri}{REL}/CSV_reconciliation.json)
- [Independent review]({uri}{REL}/review) and [raw-member map]({uri}{REL}/evidence_archives.json)
"""
    prose(OUT / "PR_description.md", text)


if __name__ == "__main__":
    repository_navigation()
    pr_body()
