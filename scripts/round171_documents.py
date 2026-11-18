"""Assemble and render the current manuscript using the preceding paper pipeline."""

import argparse
import inspect
from pathlib import Path
import re
import subprocess
import time

import round170_documents as predecessor
from round171_common import BASE, BRANCH, OUT, ROOT, TEMP, bind, read, sha, utc, write

PAPER = ROOT / "results/unified_exact_round137"
PDF_TEMP = TEMP / "pdf"
old = predecessor.old
COMPONENTS = predecessor.COMPONENTS
for module in (predecessor, predecessor.previous, predecessor.previous.r168, predecessor.previous.r168.previous, old):
    module.ROOT = ROOT
    module.PAPER = PAPER
    module.OUT = OUT
    module.TEMP = PDF_TEMP
    module.BASE = BASE


def checks(allow_pending_generated=False):
    report = old.source_checks(allow_pending_generated)
    report["errors"] = [error for error in report["errors"]
                        if not error.startswith("Main table numbering is not unique/in order:")]
    if report["main_tables"] != [str(n) for n in range(1, 13)]:
        report["errors"].append("Main table numbers must run from 1 through 12")
    body = (PAPER / "paper_body.md").read_text(encoding="utf-8-sig")
    appendix = (PAPER / "model_and_algorithm_appendices.md").read_text(encoding="utf-8-sig")
    supplement = (PAPER / "supplement.md").read_text(encoding="utf-8-sig")
    if body.count("### 4.7 Prospective positive n50") != 1 or supplement.count("## S171 Prospective positive n50") != 1:
        report["errors"].append("Missing n50 main section or supplement")
    if len(re.findall(r"^\*\*Table S171\.[1-4]\.", supplement, flags=re.M)) != 4:
        report["errors"].append("Missing one of the four supplement tables")
    if "Table 10" not in appendix:
        report["errors"].append("The appendix should reference the renumbered resource-value table")
    return report


def typeset(raw, supplement=False):
    title, content = predecessor.typeset(raw, supplement)
    for target in re.findall(r"(?<!!)\[[^\]]*\]\(([^)\s]+)\)", raw):
        if target.startswith(("https:", "http:", "mailto:", "#")):
            continue
        location, separator, fragment = target.partition("#")
        try:
            relative = (PAPER / location).resolve().relative_to(ROOT).as_posix() + separator + fragment
        except ValueError:
            continue
        prefix = "https://github.com/yifanXovo/TailoredExact/blob/"
        for old_branch in ("codex/round169-primal-reweight", "codex/round170-reweight-confirmation"):
            content = content.replace(prefix + old_branch + "/" + relative + ")",
                                      prefix + BRANCH + "/" + relative + ")")
    if supplement:
        at = content.index("## S171 Prospective positive n50")
        before, portion = content[:at], content[at:]
        portion = portion.replace("## S171 Prospective positive n50", "\\clearpage\n\n## S171 Prospective positive n50", 1)
        for number, need in ((1, 15), (2, 24), (3, 24), (4, 17)):
            label = f"**Table S171.{number}."
            portion = portion.replace(label, f"\\Needspace{{{need}\\baselineskip}}\n\n{label}", 1)
        return title, before + portion
    label = "**Table 8. Qualified B and cold P endpoints"
    content = content.replace(label, "\\Needspace{15\\baselineskip}\n\n" + label, 1)
    return title, content


def compile_function(function, replacements, **kwargs):
    content = inspect.getsource(function)
    for original, updated in replacements:
        assert original in content, original
        content = content.replace(original, updated)
    scope = dict(function.__globals__)
    scope.update(ROOT=ROOT, PAPER=PAPER, OUT=OUT, TEMP=PDF_TEMP, BASE=BASE, __file__=__file__, **kwargs)
    exec(compile(content, f"{__file__}::{function.__name__}", "exec"), scope)
    return scope[function.__name__]


def assemble():
    path = OUT / "source_manifest.json"
    if not path.exists():
        write(path, dict(measured_source_commit=read(OUT / "candidate_manifest.json")["source_commit"],
                         frozen_Cplusplus_unchanged=True))
    compile_function(predecessor.previous.r168.assemble, [
        ("round168", "round171"), ("Round168", "Round171"),
        ("current_revision=168", "current_revision=171"), ("current_round=168", "current_round=171"),
    ], checks=checks)()


def render():
    compile_function(old.pdf, [
        ("typography_policy='round165-v3')", "typography_policy='round171-v1',document_date=stamp,date_timezone='Asia/Shanghai')"),
        ("'python scripts/round165_audit.py evidence'", "'python scripts/round171_writeup.py manuscript'"),
        ("scripts/round165_documents.py", "scripts/round171_documents.py"),
        ("current_round=165", "current_round=171"),
        ("unified_exact_round165/document_build.json", "unified_exact_round171/document_build.json"),
    ], source_checks=checks, typeset_text=typeset)()


def compact_text(value):
    return re.sub(r"\s+", "", value).casefold()


def qa():
    import pdfplumber

    start = time.perf_counter()
    views = []
    markers = {
        "manuscript": ("4.7 Prospective positive n50", "Qualified B and cold P endpoints", "Prospective positive n50",
                       "n50", "6. Conclusions", "The prospective n50 comparison adds"),
        "supplement": ("The precommitted generation draws", "Table S171.1", "Table S171.2",
                       "Table S171.3", "Table S171.4"),
    }
    old_resource_values = ("0.2822618761", "0.2822620892", "0.2105292995", "0.2105295021",
                           "0.1112611656", "0.3725317852", "0.0600858983", "0.3813035291")
    for artifact in read(OUT / "document_build.json")["outputs"]:
        path = ROOT / artifact["path"]
        assert sha(path) == artifact["SHA256"]
        folder = PDF_TEMP / f"QA_{path.stem}_{artifact['SHA256'][:12]}"
        folder.mkdir(parents=True, exist_ok=True)
        report = []
        links = set()
        with pdfplumber.open(path) as pdf:
            for number, page in enumerate(pdf.pages, 1):
                label = f"page-{number:03d}"
                extracted = page.extract_text() or ""
                (folder / f"{label}.txt").write_text(extracted, encoding="utf-8")
                outside = sum(char["x0"] < -.5 or char["x1"] > page.width + .5 or
                              char["top"] < -.5 or char["bottom"] > page.height + .5 for char in page.chars)
                links.update(link["uri"] for link in page.hyperlinks if link.get("uri"))
                matched = [mark for mark in markers[path.stem] if compact_text(mark) in compact_text(extracted)]
                report.append(dict(page=number, markers=matched, outside=outside, replacement=extracted.count("\ufffd")))
        assert all(not row["outside"] and not row["replacement"] for row in report)
        full = "\n".join(p.read_text(encoding="utf-8") for p in sorted(folder.glob("*.txt")))
        assert all(token in full for token in old_resource_values)
        if path.stem == "manuscript":
            assert "table8.qualifiedbandcoldpendpoints" in compact_text(full)
            assert "theprospectiven50comparisonadds" in compact_text(full)
        else:
            assert all(f"tables171.{i}." in compact_text(full) for i in range(1, 5))
            for name in ("input_manifest.json", "matrix_frozen.json", "complete_arms.json", "activity.json"):
                assert f"blob/{BRANCH}/results/unified_exact_round171/{name}" in " ".join(links), name
        focus = {page["page"] for page in report if page["markers"]}
        selected = sorted({1, *[n + offset for n in focus for offset in (-1, 0, 1) if 1 <= n + offset <= len(report)]})
        images = []
        for n in selected:
            prefix = folder / f"page-{n:03d}"
            subprocess.run(["pdftoppm", "-r", "110", "-png", "-f", str(n), "-l", str(n),
                            "-singlefile", str(path), str(prefix)], check=True, capture_output=True)
            images.append(bind(prefix.with_suffix(".png")))
        views.append(dict(file=bind(path), page_count=len(report), pages=report,
                          rendered_pages=selected, render_root=str(folder), PNGs=images))
    write(OUT / "document_qa.json", dict(
        UTC=utc(), out_of_page_or_encoding_defects=0, status="AWAITING_VISUAL_INSPECTION",
        seconds=time.perf_counter() - start, documents=views,
        renumbered_resources_match=old_resource_values,
    ))
    for item in views:
        print(item["file"]["path"], item["rendered_pages"], item["render_root"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=["assemble", "pdf", "qa"])
    args = parser.parse_args()
    {"assemble": assemble, "pdf": render, "qa": qa}[args.stage]()
