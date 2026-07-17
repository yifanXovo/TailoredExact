#!/usr/bin/env python3
"""Fail-closed Round 21 source audit for strict certificates and flow variants.

The audit is intentionally mechanical.  It does not prove the mathematical
claims in the accompanying proof documents, but it makes prohibited production
dependencies and the most dangerous certificate regressions visible with
source hashes and line-level evidence.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import os
import re
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence


DEFAULT_OUTPUT = Path(
    "results/gf_global_gini_tree_strict_flow_round/static_audit"
)

REQUIRED_SOURCES = (
    "scripts/round21_static_exactness_audit.py",
    "include/ConnectivityFlow.hpp",
    "src/ConnectivityFlow.cpp",
    "include/Instance.hpp",
    "src/CplexBaseline.cpp",
    "src/main.cpp",
    "include/TailoredBCCplexApi.hpp",
    "src/TailoredBCCplexApi.cpp",
    "include/StrictCertificate.hpp",
    "src/StrictCertificate.cpp",
    "include/Result.hpp",
    "src/Result.cpp",
)


@dataclass(frozen=True)
class Source:
    path: str
    data: bytes
    text: str
    sha256: str

    @property
    def lines(self) -> list[str]:
        return self.text.splitlines()


@dataclass(frozen=True)
class Scope:
    name: str
    source: Source
    text: str
    start_line: int
    end_line: int


@dataclass(frozen=True)
class Evidence:
    source: str
    sha256: str
    line: int
    kind: str
    text: str


@dataclass
class Check:
    check_id: str
    category: str
    requirement: str
    passed: bool
    detail: str
    evidence: list[Evidence] = field(default_factory=list)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_source(root: Path, relative: str) -> Source:
    path = root / relative
    if not path.is_file():
        raise FileNotFoundError(f"required source is missing: {relative}")
    data = path.read_bytes()
    if not data:
        raise ValueError(f"required source is empty: {relative}")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError(f"required source is not UTF-8: {relative}: {error}") from error
    return Source(relative.replace("\\", "/"), data, text, sha256_bytes(data))


def full_scope(source: Source, name: str | None = None) -> Scope:
    return Scope(
        name or source.path,
        source,
        source.text,
        1,
        max(1, len(source.lines)),
    )


def _find_balanced_brace(text: str, opening: int) -> int:
    """Return the matching brace while ignoring strings and C/C++ comments."""
    if opening < 0 or opening >= len(text) or text[opening] != "{":
        raise ValueError("balanced-brace scan did not start on an opening brace")
    depth = 0
    state = "code"
    quote = ""
    index = opening
    while index < len(text):
        ch = text[index]
        nxt = text[index + 1] if index + 1 < len(text) else ""
        if state == "line_comment":
            if ch == "\n":
                state = "code"
        elif state == "block_comment":
            if ch == "*" and nxt == "/":
                state = "code"
                index += 1
        elif state == "string":
            if ch == "\\":
                index += 1
            elif ch == quote:
                state = "code"
        else:
            if ch == "/" and nxt == "/":
                state = "line_comment"
                index += 1
            elif ch == "/" and nxt == "*":
                state = "block_comment"
                index += 1
            elif ch in ('"', "'"):
                state = "string"
                quote = ch
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return index
                if depth < 0:
                    break
        index += 1
    raise ValueError("unbalanced C++ source while extracting an audit scope")


def extract_function(source: Source, signature: str, scope_name: str) -> Scope:
    occurrences = [match.start() for match in re.finditer(re.escape(signature), source.text)]
    if len(occurrences) != 1:
        raise ValueError(
            f"expected one {signature!r} in {source.path}, found {len(occurrences)}"
        )
    start = occurrences[0]
    opening = source.text.find("{", start + len(signature))
    if opening < 0:
        raise ValueError(f"opening brace missing after {signature!r}")
    closing = _find_balanced_brace(source.text, opening)
    start_line = source.text.count("\n", 0, start) + 1
    end_line = source.text.count("\n", 0, closing) + 1
    return Scope(scope_name, source, source.text[start : closing + 1], start_line, end_line)


def extract_flow_writer_scope(source: Source) -> Scope:
    marker = "// Optional scalable connectivity-flow family."
    if source.text.count(marker) != 1:
        raise ValueError(
            f"expected one normalized-flow writer marker in {source.path}, "
            f"found {source.text.count(marker)}"
        )
    start = source.text.index(marker)
    conditional = "if (connectivityFlowEnabled(flow_variant))"
    opening = source.text.find("{", source.text.index(conditional, start))
    closing = _find_balanced_brace(source.text, opening)
    start_line = source.text.count("\n", 0, start) + 1
    end_line = source.text.count("\n", 0, closing) + 1
    return Scope(
        "writeCompactLp connectivity-flow block",
        source,
        source.text[start : closing + 1],
        start_line,
        end_line,
    )


def extract_flow_column_scope(source: Source) -> Scope:
    """Extract the x/connectivity-column declaration loop from writeCompactLp."""
    needle = "connectivityFlowArcUpperBound(flow_variant, V, i, j)"
    occurrences = [match.start() for match in re.finditer(re.escape(needle), source.text)]
    if len(occurrences) != 2:
        raise ValueError(
            f"expected two production flow-bound call sites in {source.path}, "
            f"found {len(occurrences)}"
        )
    first = occurrences[0]
    marker = "for (int i = 0; i <= V; ++i)"
    start = source.text.rfind(marker, 0, first)
    if start < 0:
        raise ValueError("could not locate the enclosing connectivity-column loop")
    opening = source.text.find("{", start + len(marker))
    closing = _find_balanced_brace(source.text, opening)
    if not (start <= first <= closing):
        raise ValueError("connectivity-column loop extraction excluded its bound call")
    start_line = source.text.count("\n", 0, start) + 1
    end_line = source.text.count("\n", 0, closing) + 1
    return Scope(
        "writeCompactLp connectivity-flow column block",
        source,
        source.text[start : closing + 1],
        start_line,
        end_line,
    )


def evidence_at(scope: Scope, offset: int, kind: str, fallback: str = "") -> Evidence:
    local_line = scope.text.count("\n", 0, max(0, offset))
    line_number = scope.start_line + local_line
    lines = scope.source.lines
    line_text = lines[line_number - 1].strip() if 1 <= line_number <= len(lines) else fallback
    return Evidence(scope.source.path, scope.source.sha256, line_number, kind, line_text)


def regex_hits(scope: Scope, pattern: str, flags: int = re.MULTILINE) -> list[Evidence]:
    compiled = re.compile(pattern, flags)
    return [evidence_at(scope, match.start(), "regex_match") for match in compiled.finditer(scope.text)]


def boundary_evidence(scope: Scope, kind: str = "scope_scanned") -> Evidence:
    text = f"{scope.name}: audited lines {scope.start_line}-{scope.end_line}"
    return Evidence(scope.source.path, scope.source.sha256, scope.start_line, kind, text)


def required_regex(
    check_id: str,
    category: str,
    requirement: str,
    scopes: Sequence[Scope],
    pattern: str,
    minimum: int = 1,
    maximum: int | None = None,
    flags: int = re.MULTILINE,
) -> Check:
    hits: list[Evidence] = []
    for scope in scopes:
        hits.extend(regex_hits(scope, pattern, flags))
    passed = len(hits) >= minimum and (maximum is None or len(hits) <= maximum)
    limit = f"at least {minimum}" if maximum is None else f"{minimum}..{maximum}"
    detail = f"found {len(hits)} matching source occurrence(s); required {limit}"
    if not hits:
        hits = [boundary_evidence(scope, "required_pattern_absent") for scope in scopes]
    return Check(check_id, category, requirement, passed, detail, hits)


def forbidden_regex(
    check_id: str,
    category: str,
    requirement: str,
    scopes: Sequence[Scope],
    pattern: str,
    flags: int = re.MULTILINE | re.IGNORECASE,
) -> Check:
    hits: list[Evidence] = []
    for scope in scopes:
        hits.extend(regex_hits(scope, pattern, flags))
    if hits:
        return Check(
            check_id,
            category,
            requirement,
            False,
            f"found {len(hits)} prohibited occurrence(s)",
            hits,
        )
    return Check(
        check_id,
        category,
        requirement,
        True,
        f"no prohibited occurrence in {len(scopes)} fail-closed scope(s)",
        [boundary_evidence(scope) for scope in scopes],
    )


def combine_required(
    check_id: str,
    category: str,
    requirement: str,
    clauses: Sequence[tuple[Scope, str]],
    flags: int = re.MULTILINE,
) -> Check:
    evidence: list[Evidence] = []
    missing: list[str] = []
    for scope, pattern in clauses:
        hits = regex_hits(scope, pattern, flags)
        if hits:
            evidence.extend(hits)
        else:
            missing.append(f"{scope.name}:{pattern}")
            evidence.append(boundary_evidence(scope, "required_clause_absent"))
    return Check(
        check_id,
        category,
        requirement,
        not missing,
        "all required clauses found" if not missing else "missing " + " | ".join(missing),
        evidence,
    )


def write_csv_atomic(path: Path, header: Sequence[str], rows: Iterable[Sequence[object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="",
        prefix=path.name + ".",
        suffix=".tmp",
        dir=path.parent,
        delete=False,
    )
    temporary = Path(handle.name)
    try:
        with handle:
            writer = csv.writer(handle, lineterminator="\n")
            writer.writerow(header)
            writer.writerows(rows)
        os.replace(temporary, path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def build_checks(sources: dict[str, Source]) -> list[Check]:
    flow_header = full_scope(sources["include/ConnectivityFlow.hpp"])
    flow_impl = full_scope(sources["src/ConnectivityFlow.cpp"])
    instance_options = full_scope(sources["include/Instance.hpp"])
    main = full_scope(sources["src/main.cpp"])
    api = full_scope(sources["src/TailoredBCCplexApi.cpp"])
    strict_impl = full_scope(sources["src/StrictCertificate.cpp"])
    result_impl = full_scope(sources["src/Result.cpp"])
    cplex = sources["src/CplexBaseline.cpp"]
    cplex_full = full_scope(cplex)
    flow_columns = extract_flow_column_scope(cplex)
    flow_writer = extract_flow_writer_scope(cplex)
    plain_solve = extract_function(cplex, "SolveResult solveCplexBaseline(", "solveCplexBaseline")
    global_solve = extract_function(cplex, "SolveResult solveGlobalGiniTree(", "solveGlobalGiniTree")
    plain_api = extract_function(
        sources["src/TailoredBCCplexApi.cpp"],
        "PlainCplexApiSolveResult solvePlainCplexWithStrictApi(",
        "solvePlainCplexWithStrictApi",
    )
    global_api = extract_function(
        sources["src/TailoredBCCplexApi.cpp"],
        "GlobalGiniTreeApiSolveResult solveGlobalGiniTreeWithTailoredBCCplexApi(",
        "solveGlobalGiniTreeWithTailoredBCCplexApi",
    )

    flow_scopes = (flow_header, flow_impl, flow_columns, flow_writer)
    checks: list[Check] = []
    checks.append(
        Check(
            "SRC001",
            "source_integrity",
            "all required production sources are present, nonempty, and UTF-8",
            True,
            f"loaded {len(sources)} required source files",
            [
                Evidence(source.path, source.sha256, 1, "source_loaded", "full source hashed")
                for source in sorted(sources.values(), key=lambda item: item.path)
            ],
        )
    )

    checks.extend(
        [
            forbidden_regex(
                "FLOW001",
                "flow_prohibited_logic",
                "normalized-flow production code contains no instance names, seeds, known benchmark labels, or known-objective literals",
                flow_scopes,
                r"moderate_seed|tight[_-]?t_seed|high_imbalance_seed|\bseed\d+\b|\bV(?:12|20)(?:_M[12])?\b|known[_ -]?objective|\d+\.\d{6,}",
            ),
            forbidden_regex(
                "FLOW002",
                "flow_prohibited_logic",
                "normalized-flow production code contains no filename, path, or artifact-dependent logic",
                flow_scopes,
                r"instance\s*\.\s*(?:name|path)|instance_name|input_path|output_path|log_path|manifest_path|std::filesystem|filesystem::|\.json\b|\.csv\b|\.lp\b",
            ),
            forbidden_regex(
                "FLOW003",
                "flow_prohibited_logic",
                "normalized-flow activation contains no V/M tier or scale-class threshold",
                flow_scopes,
                r"small_instance|large_instance|scale[_ -]?(?:class|tier)|\b(?:station_count|vehicle_count|instance\s*\.\s*[VM]|[VM])\s*(?:==|!=|<=|>=|<|>)\s*(?:[2-9]|\d{2,})\b",
            ),
            forbidden_regex(
                "FLOW004",
                "flow_prohibited_logic",
                "normalized-flow production code contains no route masks, subset enumeration, or restricted route pools",
                flow_scopes,
                r"route[_ -]?mask|route[_ -]?pool|restricted[_ -]?(?:route|path|column)[_ -]?pool|bit[_ -]?mask|all[_ -]?subsets|complete[_ -]?(?:route|subset)[_ -]?enumeration|\b1\s*<<",
            ),
            forbidden_regex(
                "FLOW005",
                "flow_prohibited_logic",
                "normalized-flow production scopes perform no auxiliary LP/MIP solve or child-process launch",
                flow_scopes,
                r"CPX(?:mip|lp|hybbar|prim|dual)opt|\b(?:mipopt|lpopt)\s*\(|solve(?:Plain|Root|Lp|MIP|Mip|Cplex)|IloCplex|std::system\s*\(|CreateProcess|ShellExecute|popen\s*\(|std::async",
            ),
            combine_required(
                "FLOW006",
                "flow_structure",
                "the production writer delegates column existence/bounds and all optional normalization layers to the shared flow variant policy",
                (
                    (flow_writer, r"connectivityFlowArcUpperBound\s*\("),
                    (flow_writer, r"connectivityFlowHasLowerLinks\s*\("),
                    (flow_writer, r"connectivityFlowHasStartCoupling\s*\("),
                    (flow_writer, r"hasConnectivityFlowColumn\s*\("),
                ),
            ),
            combine_required(
                "FLOW007",
                "flow_structure",
                "F1/F2/F3 eliminate return-flow columns and the depot equation uses only existing return columns",
                (
                    (flow_impl, r"return\s+connectivityFlowUsesReturnColumns\(variant\)\s*\|\|\s*to\s*!=\s*0\s*;"),
                    (flow_writer, r"if\s*\(hasConnectivityFlowColumn\(flow_variant,\s*V,\s*j,\s*0\)\)"),
                ),
            ),
            combine_required(
                "FLOW008",
                "flow_structure",
                "all required same-binary flow variants are recognized explicitly",
                tuple(
                    (flow_impl, re.escape(f'"{name}"'))
                    for name in (
                        "off",
                        "round20-current",
                        "zero-return",
                        "normalized",
                        "normalized-start-coupled",
                    )
                ),
            ),
        ]
    )

    # Production helper symbols must not migrate into unrelated algorithms.
    implementation_hits: list[Evidence] = []
    allowed_impl_paths = {"src/CplexBaseline.cpp", "src/ConnectivityFlow.cpp"}
    implementation_pattern = re.compile(
        r"\b(?:resolveConnectivityFlowVariant|connectivityFlow(?:VariantName|Enabled|UsesReturnColumns|HasLowerLinks|HasStartCoupling|ArcUpperBound|TheoreticalCounts|CanEmbedInto)|hasConnectivityFlowColumn|buildCanonicalConnectivityFlowProjection)\s*\("
    )
    for relative in sorted(path for path in sources if path.startswith("src/")):
        source = sources[relative]
        if source.path in allowed_impl_paths:
            continue
        scope = full_scope(source)
        for match in implementation_pattern.finditer(scope.text):
            implementation_hits.append(evidence_at(scope, match.start(), "unexpected_flow_call_site"))
    checks.append(
        Check(
            "FLOW009",
            "flow_prohibited_logic",
            "flow-policy call sites are confined to the formulation writer/policy implementation",
            not implementation_hits,
            "no unexpected production call site" if not implementation_hits else f"found {len(implementation_hits)} unexpected call site(s)",
            implementation_hits or [boundary_evidence(flow_writer), boundary_evidence(flow_impl)],
        )
    )

    checks.extend(
        [
            combine_required(
                "OPT001",
                "experiment_options",
                "legacy Round 20 Boolean flow switch and explicit Round 21 variant option both remain in SolveOptions and the CLI parser",
                (
                    (instance_options, r"bool\s+global_gini_tree_root_connectivity_flow\s*=\s*false\s*;"),
                    (instance_options, r"std::string\s+global_gini_tree_root_connectivity_flow_variant\s*;"),
                    (main, r'arg\s*==\s*"--global-gini-tree-root-connectivity-flow"'),
                    (main, r'arg\s*==\s*"--global-gini-tree-root-connectivity-flow-variant"'),
                ),
            ),
            combine_required(
                "OPT002",
                "experiment_options",
                "the CLI usage text exposes both legacy and explicit flow controls",
                (
                    (main, r'\[--global-gini-tree-root-connectivity-flow\s+true\|false\]'),
                    (main, r'\[--global-gini-tree-root-connectivity-flow-variant\s+off\|round20-current\|zero-return\|normalized\|normalized-start-coupled\]'),
                ),
            ),
            combine_required(
                "OPT003",
                "experiment_options",
                "primary flow-ablation defaults remain parent-copy, full inherited rows, deferred timing, and native MIP start off",
                (
                    (instance_options, r'global_gini_tree_child_estimate_mode\s*=\s*"parent-copy"'),
                    (instance_options, r'global_gini_tree_row_attachment_mode\s*=\s*"full-inherited-pack"'),
                    (instance_options, r'global_gini_tree_row_timing_mode\s*=\s*"deferred"'),
                    (instance_options, r"global_gini_tree_native_mip_start\s*=\s*false"),
                ),
            ),
            combine_required(
                "OPT004",
                "legacy_mechanisms",
                "factory-domain child estimates remain selectable and implemented",
                (
                    (main, r'arg\s*==\s*"--global-gini-tree-child-estimate"'),
                    (api, r'global_gini_tree_child_estimate_mode\s*==\s*\n?\s*"factory-domain"'),
                ),
            ),
            combine_required(
                "OPT005",
                "legacy_mechanisms",
                "exact incremental row delta remains selectable and implemented",
                (
                    (main, r'arg\s*==\s*"--global-gini-tree-row-attachment"'),
                    (api, r'global_gini_tree_row_attachment_mode\s*==\s*\n?\s*"exact-incremental-delta"'),
                ),
            ),
            combine_required(
                "OPT006",
                "legacy_mechanisms",
                "eager row timing remains selectable and implemented",
                (
                    (main, r'arg\s*==\s*"--global-gini-tree-row-timing"'),
                    (api, r'global_gini_tree_row_timing_mode\s*==\s*"eager"'),
                ),
            ),
            combine_required(
                "OPT007",
                "legacy_mechanisms",
                "verified native MIP start remains selectable and implemented",
                (
                    (main, r'arg\s*==\s*"--global-gini-tree-native-mip-start"'),
                    (api, r"options\.global_gini_tree_native_mip_start"),
                    (api, r"buildVerifiedNativeMipStart\s*\("),
                ),
            ),
        ]
    )

    # Flow-arm selection itself is allowed only at the neutral default and the
    # two explicit CLI parse sites.  This catches later name/seed/size-based
    # reassignment even if it is placed outside the formulation writer.
    option_assignment_pattern = re.compile(
        r"\b(?:opt\.)?global_gini_tree_root_connectivity_flow(?:_variant)?\s*=\s*[^;\n]+;"
    )
    allowed_option_assignments = (
        re.compile(r"global_gini_tree_root_connectivity_flow\s*=\s*false\s*;"),
        re.compile(
            r"opt\.global_gini_tree_root_connectivity_flow\s*=\s*"
            r"parseBoolValue\(requireValue\(i,\s*argc,\s*argv\)\)\s*;"
        ),
        re.compile(
            r"opt\.global_gini_tree_root_connectivity_flow_variant\s*=\s*"
            r"requireValue\(i,\s*argc,\s*argv\)\s*;"
        ),
    )
    option_assignment_evidence: list[Evidence] = []
    unexpected_assignments: list[Evidence] = []
    for relative in sorted(
        path for path in sources if path.endswith((".cpp", ".hpp"))
    ):
        scope = full_scope(sources[relative])
        for match in option_assignment_pattern.finditer(scope.text):
            item = evidence_at(scope, match.start(), "flow_option_assignment")
            option_assignment_evidence.append(item)
            statement = match.group(0)
            if not any(pattern.fullmatch(statement) for pattern in allowed_option_assignments):
                unexpected_assignments.append(
                    Evidence(
                        item.source,
                        item.sha256,
                        item.line,
                        "unexpected_flow_option_assignment",
                        item.text,
                    )
                )
    option_assignment_passed = (
        len(option_assignment_evidence) == 3 and not unexpected_assignments
    )
    checks.append(
        Check(
            "OPT008",
            "flow_prohibited_logic",
            "flow variant selection is assigned only by its neutral default or explicit CLI arguments",
            option_assignment_passed,
            (
                "found exactly the three permitted assignment sites"
                if option_assignment_passed
                else f"found {len(option_assignment_evidence)} assignment site(s), "
                f"including {len(unexpected_assignments)} prohibited site(s)"
            ),
            unexpected_assignments or option_assignment_evidence,
        )
    )

    checks.extend(
        [
            combine_required(
                "STRICT001",
                "strict_gap_parameters",
                "installed CPLEX relative and absolute MIP-gap parameter IDs are both explicit",
                (
                    (api, r"constexpr\s+int\s+kParamMipGap\s*=\s*2009\s*;"),
                    (api, r"constexpr\s+int\s+kParamAbsoluteMipGap\s*=\s*2008\s*;"),
                ),
            ),
            combine_required(
                "STRICT002",
                "strict_gap_parameters",
                "strict setup sets and reads back both relative and absolute gap parameters at zero",
                (
                    (api, r"setdblparam\(env,\s*kParamMipGap,\s*0\.0\)"),
                    (api, r"getdblparam\(\s*env,\s*kParamMipGap,\s*&evidence\.relative_gap\.effective\)"),
                    (api, r"setdblparam\(env,\s*kParamAbsoluteMipGap,\s*0\.0\)"),
                    (api, r"getdblparam\(\s*env,\s*kParamAbsoluteMipGap,\s*&evidence\.absolute_gap\.effective\)"),
                    (api, r"evidence\.strict_gap_configuration_valid\s*="),
                ),
            ),
            combine_required(
                "STRICT003",
                "strict_gap_parameters",
                "fresh plain CPLEX and global-tree solves both invoke the shared strict gap setup",
                (
                    (plain_api, r"configureStrictMipGaps\s*\("),
                    (global_api, r"configureStrictMipGaps\s*\("),
                ),
            ),
            combine_required(
                "STRICT004",
                "strict_gap_parameters",
                "fresh plain CPLEX and global-tree solves fail closed when strict gap setup fails",
                (
                    (plain_api, r"strict_gaps_ok"),
                    (plain_api, r"strict_plain_required_parameter_round_trip_failed"),
                    (global_api, r"required_parameter_round_trips\s*=[\s\S]*?strict_gaps_ok\s*;"),
                    (global_api, r"if\s*\(!required_parameter_round_trips\)"),
                    (global_api, r"required_parameter_configuration_failed"),
                ),
            ),
            combine_required(
                "STRICT005",
                "strict_result_mapping",
                "plain CPLEX and global-tree result mapping use the same strict classifier adapter",
                (
                    (plain_solve, r"evaluateAndPopulateStrictCertificate\s*\("),
                    (global_solve, r"evaluateAndPopulateStrictCertificate\s*\("),
                    (cplex_full, r"classifyStrictCertificate\s*\(input\)"),
                    (strict_impl, r"StrictCertificateDecision\s+classifyStrictCertificate\s*\("),
                ),
            ),
            combine_required(
                "STRICT006",
                "strict_result_mapping",
                "plain and global-tree serialized lower bounds are populated directly from raw CPXgetbestobjval evidence",
                (
                    (plain_solve, r"result\.lower_bound\s*=\s*api\.native\.best_bound\s*;"),
                    (global_solve, r"result\.lower_bound\s*=\s*api\.native\.best_bound\s*;"),
                    (cplex_full, r'"native_CPXgetbestobjval"'),
                ),
            ),
            forbidden_regex(
                "STRICT007",
                "strict_result_mapping",
                "strict plain/global result mapping never replaces native LB with an incumbent, objective, UB, or verified objective",
                (plain_solve, global_solve),
                r"result\.lower_bound\s*=\s*(?:result\.(?:objective|upper_bound)|api\.(?:objective|native\.objective)|verified_objective|native_candidate_objective)\s*;",
            ),
            forbidden_regex(
                "STRICT008",
                "strict_result_mapping",
                "strict plain/global mapping never hard-codes serialized gap zero",
                (plain_solve, global_solve),
                r"result\.gap\s*=\s*(?:0|0\.0+)\s*;",
                flags=re.MULTILINE,
            ),
            forbidden_regex(
                "STRICT009",
                "strict_result_mapping",
                "strict plain/global mapping does not infer exactness from status-text substring helpers",
                (plain_solve, global_solve),
                r"statusIs(?:Optimal|Infeasible|TimeLimited)\s*\(",
                flags=re.MULTILINE,
            ),
            combine_required(
                "STRICT010",
                "strict_serialization",
                "JSON serialization uses max_digits10 and emits raw LB/gap/native-bound fields observationally",
                (
                    (result_impl, r"setprecision\(std::numeric_limits<double>::max_digits10\)"),
                    (result_impl, r'"  \\"lower_bound\\": "[\s\S]{0,300}?writeOptionalDouble\([\s\S]{0,300}?result\.lower_bound\s*\)'),
                    (result_impl, r'"  \\"gap\\": "[\s\S]{0,300}?writeOptionalDouble\([\s\S]{0,300}?result\.gap\s*\)'),
                    (result_impl, r'"  \\"native_mip_best_bound\\": "'),
                ),
            ),
            forbidden_regex(
                "STRICT011",
                "strict_serialization",
                "the JSON serializer does not assign or recompute lower_bound/gap fields",
                (result_impl,),
                r"\b(?:result|guarded|guarded_result)\.(?:lower_bound|gap)\s*=",
                flags=re.MULTILINE,
            ),
        ]
    )
    return checks


def emit_outputs(output_dir: Path, sources: dict[str, Source], checks: Sequence[Check]) -> None:
    ordered_checks = sorted(checks, key=lambda item: item.check_id)
    write_csv_atomic(
        output_dir / "source_hashes.csv",
        ("source", "bytes", "sha256"),
        (
            (source.path, len(source.data), source.sha256)
            for source in sorted(sources.values(), key=lambda item: item.path)
        ),
    )
    write_csv_atomic(
        output_dir / "checks.csv",
        ("check_id", "category", "status", "requirement", "detail", "evidence_count"),
        (
            (
                check.check_id,
                check.category,
                "PASS" if check.passed else "FAIL",
                check.requirement,
                check.detail,
                len(check.evidence),
            )
            for check in ordered_checks
        ),
    )
    write_csv_atomic(
        output_dir / "line_evidence.csv",
        ("check_id", "status", "source", "source_sha256", "line", "evidence_kind", "line_text"),
        (
            (
                check.check_id,
                "PASS" if check.passed else "FAIL",
                evidence.source,
                evidence.sha256,
                evidence.line,
                evidence.kind,
                evidence.text,
            )
            for check in ordered_checks
            for evidence in sorted(
                check.evidence,
                key=lambda item: (item.source, item.line, item.kind, item.text),
            )
        ),
    )


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="repository root (default: parent of scripts/)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"CSV output directory relative to root (default: {DEFAULT_OUTPUT.as_posix()})",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    root = args.root.resolve()
    output_dir = args.output_dir
    if not output_dir.is_absolute():
        output_dir = root / output_dir

    try:
        sources = {relative: load_source(root, relative) for relative in REQUIRED_SOURCES}
        checks = build_checks(sources)
    except Exception as error:
        # Fail closed even if source layout changed before normal checks could
        # be constructed.  A deterministic one-row CSV preserves the blocker.
        output_dir.mkdir(parents=True, exist_ok=True)
        write_csv_atomic(
            output_dir / "checks.csv",
            ("check_id", "category", "status", "requirement", "detail", "evidence_count"),
            (("INTERNAL001", "audit_integrity", "FAIL", "audit construction completes", str(error), 0),),
        )
        write_csv_atomic(
            output_dir / "line_evidence.csv",
            ("check_id", "status", "source", "source_sha256", "line", "evidence_kind", "line_text"),
            (),
        )
        print(f"Round 21 static exactness audit: FAIL (construction error: {error})")
        return 2

    emit_outputs(output_dir, sources, checks)
    failures = [check for check in checks if not check.passed]
    print(
        "Round 21 static exactness audit: "
        f"{'PASS' if not failures else 'FAIL'} "
        f"({len(checks) - len(failures)}/{len(checks)} checks passed; "
        f"output={output_dir})"
    )
    for check in failures:
        print(f"  {check.check_id}: {check.requirement}: {check.detail}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
