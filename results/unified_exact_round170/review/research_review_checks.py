"""Independent, standard-library-only endpoint/manuscript reconciliation.

Never imports project solver/model code or invokes any executable. Writes only
this review's derived arithmetic evidence. Run from the Round170 worktree.
"""
import csv
import datetime as dt
import hashlib
import io
import json
import math
import re
from collections import Counter
from pathlib import Path

ROOT = Path.cwd()
R = ROOT / "results/unified_exact_round170"
PAPER = ROOT / "results/unified_exact_round137"
CHECKS = []


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def check(name, condition, detail=None):
    item = {"check": name, "passed": bool(condition)}
    if detail is not None:
        item["detail"] = detail
    CHECKS.append(item)


def close(a, b, tol=1e-12):
    if a is None or b is None:
        return a is None and b is None
    return math.isclose(a, b, rel_tol=tol, abs_tol=tol)


def binding(path):
    data = path.read_bytes()
    return {"path": path.relative_to(ROOT).as_posix(), "bytes": len(data),
            "SHA256": hashlib.sha256(data).hexdigest()}


rows = read_json(R / "complete_arms.json")["rows"]
index = {(x["role"], x["Native_Seed"], x["arm"]): x for x in rows}
by_id = {x["run_id"]: x for x in rows}
frozen = read_json(R / "matrix_frozen.json")["positions"]
check("22 unique frozen positions", len(rows) == len(index) == len(frozen) == 22)
check("arms 8B/8C/3M/3P", Counter(x["arm"] for x in rows) == {"B": 8, "C": 8, "M": 3, "P": 3})
check("all same 600s cap and Threads=1", all(x["cap_seconds"] == 600 and x["Threads"] == 1 for x in rows))
check("M and P only n35 Seed1", all(x["Native_Seed"] == 1 and "35" in x["role"] for x in rows if x["arm"] in {"M", "P"}))
check("all n35 OPEN, four C20 CERT", all(x["state"] == ("CERT" if "C20" in x["role"] else "OPEN") for x in rows))
check("exact four selected exposed physical inputs", len({x["role"] for x in rows}) == 4)
for x, f in zip(rows, frozen):
    check(f"frozen identity {x['run_id']}", all(x[k] == f[k] for k in ["position", "role", "Native_Seed", "arm"]))
    data = (ROOT / x["input_path"]).read_bytes()
    check(f"actual input hash {x['run_id']}", hashlib.sha256(data).hexdigest() == x["input_SHA256"])
    audit = read_json(ROOT / x["audit_path"])
    check(f"endpoint matches actual audit {x['run_id']}", audit["passed"] and all(close(x[k], audit[k]) for k in ["U", "L", "absolute_gap", "relative_gap"]) and x["certificate"] == audit["certificate"])
    check(f"process and counts match audit {x['run_id']}", close(x["process_outer_seconds"], audit["completion"]["process_outer_seconds"]) and all(x[k] == audit[k] for k in ["actual_Optimize", "LP", "MIP", "Native_Seed"]))
    check(f"own original G/P/F {x['run_id']}", close(x["U"], x["G"] + x["lambda_value"] * x["P"]))
    check(f"own gap and certified clock {x['run_id']}", close(x["signed_absolute_gap"], x["U"] - x["L"]) and (close(x["T_cert_process"], x["process_outer_seconds"]) if x["certificate"] else x["T_cert_process"] is None))

def csv_equal(value, expected):
    if expected is None:
        return value == ''
    if isinstance(expected,(dict,list)):
        return json.loads(value) == expected
    return value == str(expected)


for basename in ['complete_arms','comparison_CB','comparison_CM','comparison_BP','comparison_CP']:
    csv_records = list(csv.DictReader(io.StringIO((R/(basename+'.csv')).read_text(encoding='utf-8-sig'))))
    json_records = read_json(R/(basename+'.json'))['rows']
    check(f"{basename} CSV row count agrees",len(csv_records) == len(json_records))
    for i,(c,j) in enumerate(zip(csv_records,json_records),1):
        check(f"{basename} CSV row{i} all fields agree",set(c)==set(j) and all(csv_equal(c[k],j[k]) for k in c))

independent_pairs = {}
for group, subject, reference, expected in [("CB", "C", "B", 8), ("CM", "C", "M", 3), ("BP", "B", "P", 3), ("CP", "C", "P", 3)]:
    comparisons = read_json(R / f"comparison_{group}.json")["rows"]
    check(f"comparison {group} count", len(comparisons) == expected)
    independent_pairs[group] = []
    for p in comparisons:
        a = index[p["role"], p["Native_Seed"], subject]
        b = index[p["role"], p["Native_Seed"], reference]
        derived = {"role": a["role"], "Native_Seed": a["Native_Seed"], "subject": subject, "reference": reference}
        check(f"comparison {group} identities {a['run_id']}", p["subject_run"] == a["run_id"] and p["reference_run"] == b["run_id"])
        for metric in ["U", "L", "absolute_gap", "relative_gap", "process_outer_seconds", "H_seconds", "Native_seconds", "Work", "nodes"]:
            val = a[metric] - b[metric]
            derived[metric + "_difference"] = val
            check(f"{group} {a['run_id']} {metric} exact endpoints", close(p["subject"][metric], a[metric]) and close(p["reference"][metric], b[metric]) and close(p[metric + "_difference"], val))
        derived["U_change_percent"] = 100 * (a["U"] - b["U"]) / b["U"]
        derived["delta"] = max(1e-6, .001 * max(abs(b["U"]), 1e-12))
        check(f"{group} {a['run_id']} percent and materiality", close(p["U_change_percent"], derived["U_change_percent"]) and close(p["delta"], derived["delta"]))
        both_cert = a["certificate"] and b["certificate"]
        derived["T_cert_ratio"] = a["T_cert_process"] / b["T_cert_process"] if both_cert else None
        check(f"{group} {a['run_id']} no OPEN time ratio", close(p["T_cert_ratio"], derived["T_cert_ratio"]))
        independent_pairs[group].append(derived)

cb35 = [x for x in independent_pairs["CB"] if "35" in x["role"]]
check("C/B n35 U two improve/four regress", sum(x["U_difference"] < -x["delta"] for x in cb35) == 2 and sum(x["U_difference"] > x["delta"] for x in cb35) == 4)
check("only B35Seed1 improves absolute gap", [(x["role"], x["Native_Seed"]) for x in cb35 if x["absolute_gap_difference"] < -x["delta"]] == [("R163-B35-S", 1)])
check("C35 U worse both seeds", all(x["U_difference"] > 0 for x in cb35 if "C35" in x["role"]))
for role in ["R163-B35-S", "R163-X35-S"]:
    pair = {x["Native_Seed"]: x for x in cb35 if x["role"] == role}
    check(f"{role} U improves onlySeed1", pair[1]["U_difference"] < 0 < pair[2]["U_difference"])
check("C20 both certificate-time regressions", all(x["T_cert_ratio"] > 1 for x in independent_pairs["CB"] if "C20" in x["role"]))
check("all new B/P and C/P improve U/L/both gaps without certificates", all(x["U_difference"] < 0 and x["L_difference"] > 0 and x["absolute_gap_difference"] < 0 and x["relative_gap_difference"] < 0 and x["T_cert_ratio"] is None for g in ["BP", "CP"] for x in independent_pairs[g]))

mechanism = []
for role in ["R163-C35-U", "R163-B35-S", "R163-X35-S"]:
    b, m, c = [index[role, 1, arm] for arm in ["B", "M", "C"]]
    delta_restart = b["initial_U"] - m["initial_U"]
    delta_weight = m["initial_U"] - c["initial_U"]
    mechanism.append({"role": role, "Delta_restart": delta_restart, "Delta_weight": delta_weight, "M_U_minus_B_U": m["U"] - b["U"]})
    check(f"{role} matched M equality and C initialization benefit", delta_restart == 0 and m["U"] == b["U"] and delta_weight > 0)

paths = read_json(R / "h_path_results.json")["rows"]
check("41 complete paid H paths", len(paths) == sum(x["H_calls"] for x in rows) == 41 and all(all(x[k] for k in ["valid", "complete", "joint_complete", "descent_complete", "closure_complete"]) for x in paths))
check("84 Optimize =57LP+27MIP", sum(x["actual_Optimize"] for x in rows) == 84 and sum(x["LP"] for x in rows) == 57 and sum(x["MIP"] for x in rows) == 27)
cost = read_json(R / "cost_report.json")
interruption = read_json(R / "work_interruption.json")
check("cost process total", close(cost["process_outer_seconds"], sum(x["process_outer_seconds"] for x in rows), 1e-9))
check("inactive gap explicitly separates gross and charged work", close(cost["science_gross_wall_seconds"] - cost["inactive_postcompletion_gap_seconds"], cost["science_charged_seconds"], 1e-9) and close(interruption["inactive_postcompletion_gap_seconds"], cost["inactive_postcompletion_gap_seconds"], 1e-9) and cost["science_charged_seconds"] <= 21600 < cost["science_gross_wall_seconds"])

csv_path = R / "GI_TBC_R170_B_increment_28col.csv"
csv_data = csv_path.read_bytes()
csv_rows = list(csv.DictReader(io.StringIO(csv_data.decode("utf-8-sig"))))
reconciliation = read_json(R / "CSV_reconciliation.json")
check("increment UTF8 BOM/8rows/28columns", csv_data.startswith(b'\xef\xbb\xbf') and len(csv_rows) == 8 and all(len(x) == 28 for x in csv_rows))
check("missing118 base; no fabricated126 master", reconciliation["authoritative_118_available"] is False and reconciliation["actual_master_rows_appended"] == 0 and reconciliation["actual_master"] is None)
pair_count = 0
unpaired_count = 0
for record in csv_rows:
    role, seed = record["实例"], int(record["Gurobi_Seed"])
    b = index[role, seed, "B"]
    check(f"CSV B endpoints {role}/{seed}", close(float(record["GI_TBC_UB"]), b["U"]) and close(float(record["GI_TBC_LB"]), b["L"]) and record["求解时限_秒"] == "600" and record["数据轮次"] == "170")
    if b["certificate"]:
        check(f"CSV CERT process clock {role}/{seed}", close(float(record["GI_TBC_收敛时间_秒"]), b["T_cert_process"]) and record["GI_TBC_未收敛Gap_百分比"] == "")
    else:
        check(f"CSV OPEN gap in percent {role}/{seed}", close(float(record["GI_TBC_未收敛Gap_百分比"]), 100*b["relative_gap"]) and record["GI_TBC_收敛时间_秒"] == "")
    if (role, seed, "P") in index:
        p = index[role, seed, "P"]
        pair_count += 1
        check(f"CSV actual P endpoints {role}/{seed}", close(float(record["P_GRB_UB"]), p["U"]) and close(float(record["P_GRB_LB"]), p["L"]) and close(float(record["P_GRB_未收敛Gap_百分比"]), 100*p["relative_gap"]) and record["P_GRB_状态"] == "未收敛" and record["P_GRB_收敛时间_秒"] == "")
    else:
        unpaired_count += 1
        check(f"CSV explicit N/A-P {role}/{seed}", record["P_GRB_状态"] == "无配对结果" and record["对比结果"] == "N/A" and "N/A-P" in record["对比说明"] and record["P_GRB_UB"] == record["P_GRB_LB"] == "")
check("CSV3 paired/5unpaired", pair_count == 3 and unpaired_count == 5)

body = (PAPER / "paper_body.md").read_text(encoding="utf-8-sig")
manuscript = (PAPER / "manuscript.md").read_text(encoding="utf-8-sig")
supplement = (PAPER / "supplement.md").read_text(encoding="utf-8-sig")
check("assembled manuscript begins with current paper body", manuscript.startswith(body.rstrip()))
conclusions = body.split("## 6. Conclusions", 1)[1]
check("Conclusions has no paid result table", "|" not in conclusions and "Table 11" not in conclusions)
section46 = body.split("### 4.6 Paid objective diversification", 1)[1].split("## 5.", 1)[0]
check("one compact main table in experimental4.6", section46.count("**Table ") == 1 and "**Table 7." in section46)
check("S169andS170 retained", "## S169 " in supplement and "## S170 " in supplement)
check("all main table numbers1to11 exactly once", re.findall(r"\*\*Table (\d+)\.", body) == [str(x) for x in range(1, 12)])

def md_table(caption, text):
    tail = text.split(caption, 1)[1]
    lines = tail.splitlines()
    table = []
    started = False
    for line in lines:
        if line.startswith("|"):
            started = True
            table.append([x.strip() for x in line.strip().strip("|").split("|")])
        elif started:
            break
    return table[2:]


tab7 = md_table("**Table 7.", body)
check("main Table7 eight rows", len(tab7) == 8)
short = {x.split("-")[1]: x for x in {r["role"] for r in rows}}
for cells in tab7:
    role_code, seed_string = cells[0].split("/")
    role = next(x for x in short.values() if x.startswith("R163-" + role_code + "-"))
    seed = int(seed_string)
    for arm, cell in zip(["B", "C", "M", "P"], cells[1:]):
        x = index.get((role, seed, arm))
        expected_cell = "-" if x is None else f"{x['U']:.6g}/{x['L']:.6g}" + (" C" if x["certificate"] else "")
        check(f"main Table7 source cell {role}/{seed}/{arm}", cell == expected_cell)

for number, expected in [("S169.1",7),("S169.2",7),("S169.3",18),("S169.4",18),("S170.1",22),("S170.2",22),("S170.3",8),("S170.4",9),("S170.5",3)]:
    check(f"complete supplementary Table{number}", len(md_table("**Table " + number + ".", supplement)) == expected)

tables170 = {n: md_table(f"**Table S170.{n}.", supplement) for n in [1,2]}
for cells,x in zip(tables170[1],rows):
    label = f"{x['role'].split('-')[1]}/{x['Native_Seed']}/{x['arm']}"
    expected = [label,"-" if x['initial_U'] is None else f"{x['initial_U']:.9g}",f"{x['U']:.9g}",f"{x['L']:.9g}",f"{100*x['relative_gap']:.9g}",x['state'],f"{x['process_outer_seconds']:.9g}"]
    check(f"complete S170.1 endpoint row{x['position']}", cells == expected)

for cells,x in zip(tables170[2],rows):
    label = f"{x['role'].split('-')[1]}/{x['Native_Seed']}/{x['arm']}"
    expected = [label,f"{x['H_seconds']:.9g}","-" if x['all_model_build_seconds'] is None else f"{x['all_model_build_seconds']:.9g}",f"{x['LP']}/{x['MIP']}",f"{x['Native_seconds']:.9g}",f"{x['Work']:.9g}",f"{x['nodes']:.9g}",f"{x['audit_seconds']:.9g}"]
    check(f"complete S170.2 cost row{x['position']}", cells == expected)

for cells,x in zip(md_table("**Table S170.3.",supplement),independent_pairs['CB']):
    label = f"{x['role'].split('-')[1]}/{x['Native_Seed']}"
    expected = [label,f"{x['U_difference']:.9g} ({x['U_change_percent']:.9g}%)",f"{x['L_difference']:.9g}",f"{x['absolute_gap_difference']:.9g}","-" if x['T_cert_ratio'] is None else f"{x['T_cert_ratio']:.9g}"]
    check(f"S170.3 independent paired row{label}", cells == expected)

for cells,x in zip(md_table("**Table S170.4.",supplement),[x for g in ['CM','BP','CP'] for x in independent_pairs[g]]):
    expected = [x['role'].split('-')[1],x['subject']+'/'+x['reference'],f"{x['U_difference']:.9g}",f"{x['U_change_percent']:.9g}",f"{x['L_difference']:.9g}",f"{x['absolute_gap_difference']:.9g}"]
    check(f"S170.4 independent paired row{expected[0]}/{expected[1]}", cells == expected)

historic = ROOT / 'results/unified_exact_round169'
old_rows = read_json(historic / 'complete_arms.json')['rows']
old_h = read_json(historic / 'h_results.json')['rows']
old_pool = read_json(historic / 'h_pool_costs.json')['rows']
for cells,x in zip(md_table('**Table S169.1.',supplement),old_h):
    expected = [x['role'],f"{x['B']:.9g}",f"{x['C']:.9g}",f"{x['Delta_restart']:.9g}",f"{x['Delta_weight']:.9g}",x['selected_C']]
    check(f"historical S169.1 preserved {x['role']}",cells == expected)
for cells,x in zip(md_table('**Table S169.2.',supplement),old_pool):
    expected = [x['role'],f"{x['B_path_seconds']:.9g}",f"{x['M_pool_path_seconds']:.9g}",f"{x['C_pool_path_seconds']:.9g}"]
    check(f"historical S169.2 preserved {x['role']}",cells == expected)
for cells,x in zip(md_table('**Table S169.3.',supplement),old_rows):
    expected = [x['role']+'/'+x['arm'],f"{x['initial_U']:.9g}",f"{x['U']:.9g}",f"{x['L']:.9g}",f"{max(0,x['relative_gap']):.9g}",'CERT' if x['certificate'] else 'OPEN',f"{x['process_outer_seconds']:.9g}"]
    check(f"historical S169.3 preserved row{x['position']}",cells == expected)
for cells,x in zip(md_table('**Table S169.4.',supplement),old_rows):
    expected = [x['role']+'/'+x['arm'],f"{x['H_seconds']:.9g}",f"{x['all_model_build_seconds']:.9g}",f"{x['LP']} / {x['MIP']}",f"{x['Native_seconds']:.9g}",f"{x['Work']:.9g}",f"{x['nodes']:.9g}"]
    check(f"historical S169.4 preserved row{x['position']}",cells == expected)

data = {"schema":"round170-independent-research-arithmetic-v1", "UTC":dt.datetime.now(dt.timezone.utc).isoformat(), "reviewerID":"/root/research_review", "Optimize":0, "H_calls":0,
        "passed":all(x["passed"] for x in CHECKS),"checks":CHECKS,"failed_checks":[x for x in CHECKS if not x["passed"]],"independently_recomputed_comparisons":independent_pairs,"independently_recomputed_initialization":mechanism,
        "CSV":{"records":len(csv_rows),"columns":len(csv_rows[0]),"new_strict_B_P_pairs":pair_count,"unpaired":unpaired_count,"new_physical_inputs":0,"actual_master_rows_appended":reconciliation["actual_master_rows_appended"],"increment":binding(csv_path)},
        "limitations":"Source/data/derived-table reconciliation, not new optimization, model construction or a replacement for independent physical/proof audit. PDF visual findings are recorded separately.",
        "bindings":[binding(R/n) for n in ["complete_arms.json","complete_arms.csv","comparison_CB.json","comparison_CB.csv","comparison_CM.json","comparison_CM.csv","comparison_BP.json","comparison_BP.csv","comparison_CP.json","comparison_CP.csv","matrix_frozen.json","h_path_results.json","cost_report.json","work_interruption.json","CSV_reconciliation.json"]] + [binding(PAPER/n) for n in ["paper_body.md","manuscript.md","supplement.md","references.bib"]] + [binding(historic/n) for n in ['complete_arms.json','h_results.json','h_pool_costs.json']]}
(R / "review/research_review_arithmetic.json").write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"passed":data["passed"],"checks":len(CHECKS),"failed_checks":data["failed_checks"],"comparison_counts":{k:len(v) for k,v in independent_pairs.items()},"CSV":data["CSV"]},ensure_ascii=False,indent=2))
