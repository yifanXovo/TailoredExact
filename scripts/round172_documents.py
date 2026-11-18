"""Assemble and check the Round172 paper from its maintained components."""

import argparse
import csv
import json
import re
import subprocess
import sys
import time
from pathlib import Path

import round171_documents as previous
from round170_common import DLL_SHA, MEASURED, PE_SHA, bind, read, sha, utc

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "results/unified_exact_round137"
OUT = ROOT / "results/unified_exact_round172"
TEMP = ROOT.parents[1] / "temp/round172/pdf"
BASE = "e8c4a0d3ccbaf1c1a6e6f83242d9163fe29e74e4"
BRANCH = "codex/round172-journal-manuscript"
S171 = "## S171 Positive-objective 50-station configurations"
COMPONENTS = previous.COMPONENTS

# Rebind both the imported wrapper and its typography/assembly dependencies.
# No old entry point, candidate manifest, producer, or historic path is writable.
previous.ROOT, previous.PAPER, previous.OUT = ROOT, PAPER, OUT
previous.PDF_TEMP, previous.BASE, previous.BRANCH = TEMP, BASE, BRANCH
for module in (
    previous.predecessor, previous.predecessor.previous,
    previous.predecessor.previous.r168, previous.predecessor.previous.r168.previous,
    previous.old,
):
    module.ROOT, module.PAPER, module.OUT, module.TEMP, module.BASE = ROOT, PAPER, OUT, TEMP, BASE
old = previous.old


def write(path, value):
    # Bind final receipts to the published LF bytes. Maintained R137 JSON
    # retains the repository's existing byte-preserving CRLF representation.
    newline = "\n" if path.is_relative_to(OUT) else "\r\n"
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8", newline=newline)


def source(name):
    return (PAPER / name).read_text(encoding="utf-8-sig")


def baseline(name):
    path = (PAPER / name).relative_to(ROOT).as_posix()
    return subprocess.check_output(["git", "show", f"{BASE}:{path}"], cwd=ROOT).decode("utf-8-sig").replace("\r\n", "\n")


def rows(text, table):
    match = re.search(rf"^\*\*Table {re.escape(table)}\..*?\n\n((?:^\|[^\n]+\n)+)", text, re.M | re.S)
    return match[1].splitlines() if match else []


def anchors(text):
    headings = re.findall(r"^#{1,6} (.+)$", text, re.M)
    return {re.sub(r"\s", "-", re.sub(r"[^\w -]", "", h.lower())) for h in headings}


def checks(allow_pending_generated=False):
    report = old.source_checks(allow_pending_generated)
    errors = [e for e in report["errors"] if not e.startswith("Main table numbering is not unique/in order:")]
    report["errors"] = errors
    body, app, supp = map(source, ("paper_body.md", "model_and_algorithm_appendices.md", "supplement.md"))
    for name in COMPONENTS:
        for number, line in enumerate(source(name).split("\n"), 1):
            if re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", line):
                errors.append(f"Illegal control character in {name}:{number}")
    base_body, base_supp = map(baseline, ("paper_body.md", "supplement.md"))
    if report["main_tables"] != [str(i) for i in range(1, 11)]:
        errors.append("Main tables must be numbered 1 through 10")
    proofs = re.findall(r"^\*\*Proposition (\d+) ", body, re.M)
    if proofs != ["1", "2", "3", "4"] or body.count("**Algorithm 1.") != 1:
        errors.append("Main propositions and Algorithm 1 must have unique, sequential labels")
    app_ids = re.findall(r"^\*\*(?:Proposition|Lemma) (A\d+)\b", app, re.M)
    if len(app_ids) != len(set(app_ids)) or not {"A3", "A4", "A9", "A10", "A11"}.issubset(app_ids):
        errors.append("Appendix statements have a duplicate label or a missing coverage/representation proof")
    if "difference interval in Table 8" not in app or "numerical guards are those stated with Table 8" not in body:
        errors.append("Decision bounds must reference the main resource-value table")
    if "positive-target" in (body + supp).lower():
        errors.append("The shortage design should be called positive-objective")

    retained = {"2": "2", "3": "3", "4": "4", "5": "5", "7": "9", "8": "10", "9": "11", "10": "12"}
    for current, former in retained.items():
        if not rows(body, current) or rows(body, current) != rows(base_body, former):
            errors.append(f"Table {current} differs from the inherited rows of Table {former}")
    moved = {"S166.1": ("6", 6), "S170.6": ("7", 8)}
    for current, (former, count) in moved.items():
        moved_rows = rows(supp, current)
        if len(moved_rows) != count + 2 or moved_rows != rows(base_body, former):
            errors.append(f"Table {current} is missing or differs from its inherited rows")
        if f"[Table {current}](supplement.md#" not in body:
            errors.append(f"The main text must link to Table {current}")
    for number in range(1, 5):
        label = f"S171.{number}"
        if not rows(supp, label) or rows(supp, label) != rows(base_supp, label):
            errors.append(f"Table {label} differs from the inherited rows")

    source_csv = OUT.parent / "unified_exact_round171/comparison_BP.csv"
    with source_csv.open(encoding="utf-8-sig", newline="") as handle:
        exact = list(csv.DictReader(handle))
    names = ["CITI compact", "CITI regional", "CABI compact", "CABI regional", "Divvy compact", "Divvy regional"]
    expected = []
    for label, row in zip(names, exact, strict=True):
        assert (row["Native_Seed"], row["cap_seconds"], row["B_state"], row["P_state"]) == ("0", "1200", "OPEN", "OPEN")
        pairs = [f'{float(row[a]):.6f} / {float(row[b]):.6f}' for a, b in
                 [("B_U", "B_L"), ("P_U", "P_L"), ("B_absolute_gap", "P_absolute_gap")]]
        gap = " / ".join(f'{100 * float(row[metric]):.2f}' for metric in ["B_relative_gap", "P_relative_gap"])
        expected.append("| " + " | ".join([label, *pairs, gap]) + " |")
    if rows(body, "6")[2:] != expected or S171 not in supp:
        errors.append("Table 6 must contain all six recorded OPEN B/P comparisons and both gaps")
    if not (body.index("### 4.4 Complete-method endpoints") < body.index("**Table 6.") <
            body.index("### 4.5 Representation")):
        errors.append("Table 6 must appear with the complete-method evidence")

    supp_ids = anchors(supp)
    targets = re.findall(r"\]\(supplement\.md#([^)]+)\)", body)
    topic_map = supp.split("## Reading and source map", 1)[1].split("## Current detailed panel tables", 1)[0]
    targets.extend(re.findall(r"\]\(#([^)]+)\)", topic_map))
    for target in targets:
        if target not in supp_ids:
            errors.append(f"Missing supplement topic or evidence anchor: {target}")
    report.update(appendix_statements=app_ids, main_propositions=proofs,
                  moved_table_rows={key: count for key, (_, count) in moved.items()},
                  retained_tables=retained, supplement_anchors=targets, qualified_n50_pairs=len(exact))
    return report


previous_typeset = previous.compile_function(previous.typeset, [
    ("## S171 Prospective positive n50", S171),
    ("**Table 8. Qualified B and cold P endpoints", "**Table 6. Feasible objectives and qualified global bounds"),
])


def reserve_before(content, marker, lines):
    need = f"\\Needspace{{{lines}\\baselineskip}}\n\n"
    assert marker in content, marker
    return content.replace(marker, need + marker, 1)


def typeset(raw, supplement=False):
    title, content = previous_typeset(raw, supplement)
    if supplement:
        # Unlike GitHub, Pandoc retains periods in its default generated id.
        content = re.sub(r"\]\(#s167([234])-", r"](#s167.\1-", content)
        heading = "### Matched initialization endpoints by role and Seed"
        start = content.index(heading)
        end = content.index(S171, start)
        # Keep the moved table's heading, caption and body together.
        fragment = content[start:end]
        table_reservation = r"\Needspace{270pt}"
        assert table_reservation in fragment
        fence = chr(96) * 3
        fragment = fragment.replace(f"{fence}{{=latex}}\n{table_reservation}\n{fence}\n\n", "", 1)
        fragment = fragment.replace("\\clearpage\n\n", "", 1)
        content = content[:start] + reserve_before(fragment, heading, 16) + content[end:]
        content = reserve_before(content, S171, 23)
    else:
        content = content.replace("\\clearpage\n\n## Abstract", "## Abstract", 1)
        content = content.replace("\\clearpage\n\n## 6. Conclusions", "## 6. Conclusions", 1)
        for marker, lines in (
            ("**Table 1. Panel protocols", 24),
            ("### 4.2 Complete methods", 13),
            ("### 4.4 Complete-method endpoints", 17),
            ("### 5.2 Quality between sampled objective weights", 14),
            ("**Table 10. Continuous-weight", 11),
            ("## 6. Conclusions", 24),
        ):
            content = reserve_before(content, marker, lines)
    for relative in re.findall(r"(?<!!)\[[^\]]*\]\(([^)\s]+)\)", raw):
        if relative.startswith(("https:", "http:", "mailto:", "#")):
            continue
        name, fragment, tail = relative.partition("#")
        try:
            path = (PAPER / name).resolve().relative_to(ROOT).as_posix() + fragment + tail
        except ValueError:
            continue
        repository = "https://github.com/yifanXovo/TailoredExact/blob/"
        content = re.sub(rf"{re.escape(repository)}codex/round[^/]+/(?={re.escape(path)}\))",
                         f"{repository}{BRANCH}/", content)
    return title, content


def assemble():
    # Only document lineage is seeded. Historical measured C++ is a citation.
    write(OUT / "source_manifest.json", dict(
        historical_measurement=dict(source=MEASURED, PE_SHA256=PE_SHA, DLL_SHA256=DLL_SHA),
        document_base_commit=BASE, predecessor_branch="codex/round171-frozen-b-n50",
        branch=BRANCH, measured_runtime_created=False,
    ))
    write(OUT / "manuscript_word_counts.json", dict(
        before_whitespace_words=len(baseline("paper_body.md").split()),
        method="split on whitespace in Markdown source, including table cells and math",
        conclusions_before_whitespace_words=len(baseline("paper_body.md").split("## 6. Conclusions")[1].split()) + 3,
        conclusions_after_whitespace_words=len(source("paper_body.md").split("## 6. Conclusions")[1].split()) + 3,
    ))
    previous.compile_function(previous.predecessor.previous.r168.assemble, [
        ("round168-current-components-and-diagnostic-v1", "round172-current-components-v1"),
        ("current_revision=168", "current_revision=172"),
        ("current_round=168", "current_round=172"),
        ("/unified_exact_round168/", "/unified_exact_round172/"),
        ("Round168 components", "Round172 components"),
        ("generator=bind(Path(__file__))", "generator=bind(ROOT/'scripts/round172_documents.py')"),
        ("inherited_exporter=bind(ROOT/'scripts/round166_documents.py')", "inherited_exporter=bind(ROOT/'scripts/round171_documents.py')"),
    ], checks=checks, write=write)()


def pin_decision_figures(tex):
    def place(figure):
        if any(name in figure[0] for name in ("three_seed_endpoints.png", "parameter_quality_bands.png")):
            return figure[0].replace(r"\begin{figure}", r"\begin{figure}[H]", 1)
        return figure[0]

    return re.sub(r"\\begin\{figure\}.*?\\end\{figure\}", place, tex, flags=re.S)


def render():
    previous.compile_function(old.pdf, [
        ("typography_policy='round165-v3')", "typography_policy='round172-v1',document_date=stamp,template_SHA=sha(ROOT/'scripts/round172_documents.py'))"),
        ("commands=['python scripts/round165_audit.py evidence','python scripts/round165_documents.py assemble','python scripts/round165_documents.py pdf','python scripts/round165_documents.py qa']",
         "commands=[[sys.executable,'-B','scripts/round172_documents.py',stage] for stage in ('assemble','pdf','qa')]"),
        (r"\usepackage{pdflscape}", "\\usepackage{pdflscape}\n\\usepackage{float}"),
        ("value=tex.read_text(encoding='utf-8')",
         "value=tex.read_text(encoding='utf-8')\n"
         "        if stem == 'manuscript':\n"
         "            value=pin_decision_figures(value)",),
        ("current_round=165", "current_round=172"),
        ("unified_exact_round165/document_build.json", "unified_exact_round172/document_build.json"),
    ], source_checks=checks, typeset_text=typeset, pin_decision_figures=pin_decision_figures, write=write)()


def compact(value):
    return re.sub(r"\s+", "", value).casefold()


def qa():
    import pdfplumber

    started = time.perf_counter()
    references = read(OUT / "document_build.json")["outputs"]
    markers = {
        "manuscript": (
            "Abstract", "1. Introduction and related work", "Physical semantics and objective", "compact shared interface", "conditional joint representation",
            "to see what separate mixtures lose", "Algorithm 1. GI-TBC with complete parent continuation", "coverage).",
            *(f"Table {i}." for i in range(1, 11)),
            "Three-Seed endpoints on the six archived-source inputs", "What additional route time can achieve",
            "Original-objective endpoints at the two physical horizons", "Continuous-weight quality bands on four fixed physical families",
            "6. Conclusions", "A.6 Cutoff and coverage proof", "A.9 Compact supports", "A.10 Continuous decision bounds",
            "A.11 Conditional stock", "B.0 Complete leaf and cover", "B.4 Native requests",
            "B.4.1 Final independent and native proof rules",
        ),
        "supplement": (
            "Reading and source map", "Same-build compact-support endpoints", "Historical implementation identity",
            "Conditional representation diagnostics", "Continuous-weight archive and two-sided resource value",
            "S168 Complete route-family target attainability",
            "Matched initialization endpoints by role and Seed",
            "S171 Positive-objective 50-station configurations", "Table S166.1.", "Table S170.6.",
            *(f"Table S171.{i}." for i in range(1, 5)),
        ),
    }
    resource_values = (
        "0.2822618761", "0.2822620892", "0.2105292995", "0.2105295021",
        "0.1112611656", "0.3725317852", "0.0600858983", "0.3813035291",
    )
    documents = []
    for artifact in references:
        path = ROOT / artifact["path"]
        assert sha(path) == artifact["SHA256"]
        folder = TEMP / f"qa_{path.stem}_{artifact['SHA256'][:12]}"
        folder.mkdir(parents=True, exist_ok=True)
        pages, texts, links = [], [], set()
        with pdfplumber.open(path) as pdf:
            for number, page in enumerate(pdf.pages, 1):
                extracted = page.extract_text() or ""
                texts.append(extracted)
                (folder / f"page-{number:03d}.txt").write_text(extracted, encoding="utf-8")
                out_of_page = sum(c["x0"] < -.5 or c["x1"] > page.width + .5 or
                                  c["top"] < -.5 or c["bottom"] > page.height + .5 for c in page.chars)
                hits = [label for label in markers[path.stem] if compact(label) in compact(extracted)]
                pages.append(dict(page=number, markers=hits, outside=out_of_page, replacement=extracted.count("\ufffd")))
                links.update(link["uri"] for link in page.hyperlinks if link.get("uri"))
        assert all(not page["outside"] and not page["replacement"] for page in pages), path
        full = "\n".join(texts)
        assert all(value in full for value in resource_values), f"{path}: resource interval precision"
        required = (["Table 6.", "33.53 / 44.38", "0.180003 / 0.232440", "0.000000100002"]
                    if path.stem == "manuscript" else ["Table S166.1.", "Table S170.6.", "Table S171.4."])
        assert all(compact(value) in compact(full) for value in required), (path, required)
        paths = (
            ["results/unified_exact_round137/supplement.md#same-build-compact-support-endpoints",
             "results/unified_exact_round137/supplement.md#matched-initialization-endpoints-by-role-and-seed"]
            if path.stem == "manuscript" else
            [f"results/unified_exact_round171/{name}" for name in
             ("input_manifest.json", "matrix_frozen.json", "complete_arms.json", "activity.json")]
        )
        for link in paths:
            assert any(f"/blob/{BRANCH}/{link}" == url.split("yifanXovo/TailoredExact", 1)[-1]
                       for url in links), (path, link)
        hits = {row["page"] for row in pages if row["markers"]}
        selected = sorted({1, *[n + k for n in hits for k in (-1, 0, 1) if 1 <= n + k <= len(pages)]})
        for n in selected:
            subprocess.run(["pdftoppm", "-r", "115", "-png", "-f", str(n), "-l", str(n),
                            "-singlefile", str(path), str(folder / f"page-{n:03d}")],
                           check=True, capture_output=True)
        documents.append(dict(file=bind(path), page_count=len(pages), pages=pages,
                              rendered_pages=selected, render_root=str(folder)))
        print(path.name, len(pages), "pages total;", selected, str(folder))
    write(OUT / "document_qa.json", dict(
        UTC=utc(), status="AWAITING_VISUAL_INSPECTION", seconds=time.perf_counter() - started,
        resource_bound_readback=resource_values, links_checked=True, documents=documents,
    ))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=["paths", "assemble", "pdf", "qa"])
    stage = parser.parse_args().stage
    if stage == "paths":
        print(f"Branch: {BRANCH}\nBase: {BASE}\nCurrent paper: {PAPER}\nReceipts: {OUT}\nTemporary: {TEMP}")
    else:
        {"assemble": assemble, "pdf": render, "qa": qa}[stage]()
