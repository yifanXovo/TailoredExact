"""Portable arithmetic/table reconstruction from finite published authorities only.

No optimization, solver library, process launch, network or new instance generation.
"""
import argparse
import ast
import csv
import hashlib
import io
import json
import math
import time
from collections import Counter
from pathlib import Path

def load(p):
    return json.loads(p.read_text(encoding="utf-8-sig"))

def write_csv(path, rows, columns):
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

def table(headers, rows):
    return "| " + " | ".join(headers) + " |\n|" + "|".join(["---"]*len(headers)) + "|\n" + "".join(
        "| " + " | ".join(str(v) for v in row) + " |\n" for row in rows)

def classify(c, r):
    if not c["numbers_qualified"] or not r["numbers_qualified"]:
        return "UNEVALUABLE"
    if c["certificate"] != r["certificate"]:
        return "WIN" if c["certificate"] else "LOSS"
    if c["certificate"]:
        d = c["T_produce"]-r["T_produce"]
        a = max(30.0, .1*r["T_produce"])
        return "WIN" if d <= -a else "LOSS" if d >= a else "TIE"
    du, dg = c["U"]-r["U"], c["gap"]-r["gap"]
    au, ag = max(.001, .01*abs(r["U"])), max(.001, .1*abs(r["gap"]))
    better, worse = (du <= -au or dg <= -ag), (du >= au or dg >= ag)
    return "MIXED" if better and worse else "WIN" if better else "LOSS" if worse else "TIE"

def replay(instance, arm):
    lines = instance.splitlines()
    V, M = map(int, lines[0].split()[:2])
    Q = ast.literal_eval(lines[0][lines[0].index("["):])
    d = {line.split("=",1)[0].strip(): ast.literal_eval(line.split("=",1)[1].strip())
         for line in lines[1:] if "=" in line}
    xy = next(v for k,v in d.items() if isinstance(v,list) and v and isinstance(v[0],tuple))
    Y = d["initial"][:]
    seen = set()
    durations, returns = [], []
    routes = arm["final_physical"]["routes"]
    assert len(routes) == M and {r["vehicle"] for r in routes} == set(range(M))
    for r in routes:
        nodes, k = r["nodes"], r["vehicle"]
        assert nodes[0] == nodes[-1] == 0
        load_k = pickups = 0
        ops = {o["station"]: (o["pickup"],o["drop"]) for o in r["operations"]}
        assert len(ops) == len(nodes)-2
        for i in nodes[1:-1]:
            assert 1 <= i <= V and i not in seen
            seen.add(i)
            p, q = ops[i]
            assert p == int(p) and q == int(q) and p+q >= 1 and p*q == 0
            load_k += p-q
            assert 0 <= load_k <= Q[k]
            Y[i] += q-p
            assert 0 <= Y[i] <= d["capacities"][i]
            pickups += p
        travel = sum(math.hypot(xy[i][0]-xy[j][0],xy[i][1]-xy[j][1])/1.5
                     for i,j in zip(nodes,nodes[1:]))
        duration = travel+120*pickups
        assert duration <= 10800+1e-7
        durations.append(duration)
        returns.append(load_k)
    ratios = [Y[i]/d["target"][i] for i in range(1,V+1)]
    S = sum(ratios)
    G = sum(abs(a-b) for i,a in enumerate(ratios) for b in ratios[i+1:])/(V*S) if S else 0
    P = sum(d["weights"][i]*abs(ratios[i-1]-1) for i in range(1,V+1))
    F = G+.15*P
    assert Y == arm["final_physical"]["Y"]
    assert abs(F-arm["final_U"]) < 2e-14
    assert sum(Y[1:])+sum(returns) == sum(d["initial"][1:])
    return {"arm":arm["arm"],"U_recomputed":F,"G":G,"P":P,
            "duration_max":max(durations),"return_loads":returns,"stations_served":len(seen)}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1])
    args=ap.parse_args()
    start=time.perf_counter()
    out=args.root/"results/unified_exact_round124"
    auth=out/"authorities"
    dst=out/"tables"
    dst.mkdir(exist_ok=True)
    arms=load(auth/"r122_arms.json")
    pairs=load(auth/"r122_pairs.json")
    core=load(auth/"r123_finite.json")
    assert len(arms)==32 and len(pairs)==48 and len(core["arms"])==3
    assert len({a["id"] for a in arms})==6
    for group in [arms,core["arms"]]:
        for a in group:
            assert abs((a["U"]-a["L"])-a["gap"])<1e-15
            assert abs(a["T_total"]-a["T_produce"]-a["T_verify"])<1e-10
            assert not a["source_reduced"] and a["numbers_qualified"]
    checked=[]
    for aa,pp in [(arms,pairs),(core["arms"],core["pairs"])]:
        for p in pp:
            block=[a for a in aa if a["id"]==p["id"] and a.get("seed",0)==p.get("seed",0)]
            c=next(a for a in block if a["arm"]==p["candidate"])
            r=next(a for a in block if a["arm"]==p["control"])
            cls=classify(c,r)
            assert cls==p["classification"], (p,cls)
            checked.append({"id":p["id"],"seed":p.get("seed",0),"pair":p["candidate"]+"/"+p["control"],"classification":cls})
    fields=["group_number","id","source","V","seed","arm","cap_seconds","U","L","gap",
            "certificate","proof_evidence","T_produce","T_verify","T_total"]
    write_csv(dst/"r122_arms.csv",arms,fields)
    write_csv(dst/"r123_arms.csv",core["arms"],fields)
    write_csv(dst/"r122_pairs.csv",pairs,["group_number","id","seed","candidate","control","classification","severe_regression","dU","dL","dgap","certified_time_ratio"])
    write_csv(dst/"r123_pairs.csv",core["pairs"],["id","seed","candidate","control","classification","severe_regression","dU","dL","dgap","certified_time_ratio"])
    cp=core["checkpoints"]
    write_csv(dst/"r123_checkpoints.csv",cp,["arm","checkpoint_seconds","actual_end_seconds","source","U_final","last_witness_F","last_witness_raw_process_available_seconds","last_witness_available_upper_seconds","L","L_raw_process_available_seconds","L_available_upper_seconds"])
    # Full precision is kept in CSV and source JSON; print enough digits in the paper.
    fmt=lambda x: format(x,".17g") if isinstance(x,float) else str(x)
    headers=["Block","Role","Seed","Method","Cap (s)","U","L","Signed gap","Tier","T_produce","T_verify","T_total"]
    def rows(aa):
        return [[a.get("group_number",1),a["id"],a.get("seed",0),a["arm"],a["cap_seconds"],fmt(a["U"]),fmt(a["L"]),fmt(a["gap"]),"N" if a["certificate"] else "O",fmt(a["T_produce"]),fmt(a["T_verify"]),fmt(a["T_total"])] for a in aa]
    md="# Complete published-result supplement\n\nGenerated by `scripts/round124_derive.py` from the finite authorities. N: nonzero numerical certificate; O: qualified open bound (including the explicitly independent zero floor). Zero certificates, source-reduced results and missing arms: zero in both panels. Tiny signed gaps are unchanged.\n\n## Table S1: all 32 R122 arms\n\n"+table(headers,rows(arms))
    md+="\n## Table S2: all 48 R122 directed pairs\n\n"+table(["Block","Role","Seed","Pair","Class","Severe"],[[p["group_number"],p["id"],p["seed"],p["candidate"]+"/"+p["control"],p["classification"],p["severe_regression"]] for p in pairs])
    md+="\n## Table S3: single known R123 long-window problem\n\n"+table(headers,rows(core["arms"]))
    md+="\n## Table S4: all three R123 pairs\n\n"+table(["Pair","Class","dU","dL","d(gap)","Certified time ratio"],[[p["candidate"]+"/"+p["control"],p["classification"],fmt(p["dU"]),fmt(p["dL"]),fmt(p["dgap"]),"unknown"] for p in core["pairs"]])
    md+="\n## Table S5: existing checkpoints\n\n"+table(["Method","Time (s)","U/last witness","L","Source"],[[p["arm"],p["checkpoint_seconds"] if p["checkpoint_seconds"] is not None else "end "+fmt(p["actual_end_seconds"]),fmt(p.get("last_witness_F",p.get("U_final"))) if p.get("last_witness_F",p.get("U_final")) is not None else "unknown",fmt(p.get("L")) if p.get("L") is not None else "unknown",p["source"]] for p in cp])
    (dst/"complete_results.md").write_text(md,encoding="utf-8",newline="\n")
    # Every result table in the continuous paper is generated, not transcribed.
    inputs=load(auth/"r122_inputs.json")
    designs=inputs["roles"][:6]
    main_tables={
        "DESIGN":table(["Role","Source","n/m","Geometry / inventory","Q","Physical T (s)","Cap (s)","sum weights","lambda sum weights"],
           [[d["id"],d["source"],str(d["V"])+"/"+str(d["M"]),d["geometry"]+" / "+d["inventory"],str(d["Q_vector"]),d["T_seconds"],d["cap_seconds"],fmt(d["sum_weights"]),fmt(d["lambda_sum_weights"])] for d in designs]),
        "R122":table(["Role","Seed","Method","Cap (s)","U","L","Signed gap","Tier","T_produce (s)"],
           [[a["id"],a["seed"],a["arm"],a["cap_seconds"],format(a["U"],".10g"),format(a["L"],".10g"),format(a["gap"],".10g"),"N" if a["certificate"] else "O",format(a["T_produce"],".8g")] for a in arms]),
        "R123":table(["Method","Cap (s)","U","L","Signed gap","Certified","T_produce","T_verify","T_total"],
           [[a["arm"],18000,fmt(a["U"]),fmt(a["L"]),fmt(a["gap"]),False,format(a["T_produce"],".12g"),format(a["T_verify"],".12g"),format(a["T_total"],".12g")] for a in core["arms"]])}
    aggregate=[]
    for seed in [0,1]:
        for candidate,control in [("MB-D1","P-GRB"),("M-B","P-GRB"),("ENS-C","P-GRB"),("MB-D1","M-B"),("MB-D1","ENS-C"),("M-B","ENS-C")]:
            count=Counter(p["classification"] for p in pairs if p["seed"]==seed and p["candidate"]==candidate and p["control"]==control)
            aggregate.append([seed,"6 new problems" if seed==0 else "2 fixed repeats",candidate+"/"+control]+[count[t] for t in ["WIN","LOSS","MIXED","TIE","UNEVALUABLE"]])
    main_tables["PAIRS"]=table(["Seed","Denominator","Pair","WIN","LOSS","MIXED","TIE","UNEVALUABLE"],aggregate)
    cover_rows=[]
    for ob in core["proof_obligations"]:
        for v in ob["active_cover"]:
            cover_rows.append([ob["arm"],v["leaf_id"],v["gamma_L"],v["gamma_U"],v["lower_bound"],v["status"]])
    main_tables["COVER"]=table(["Method","Unit","True-G lower","True-G upper","Regional floor","State"],cover_rows)
    manuscript=out/"manuscript.md"
    if manuscript.exists():
        import re
        body=manuscript.read_text(encoding="utf-8")
        for key,value in main_tables.items():
            begin,end="<!-- "+key+"_START -->","<!-- "+key+"_END -->"
            assert begin in body and end in body, key
            body=re.sub(re.escape(begin)+r"[\s\S]*?"+re.escape(end),lambda _:begin+"\n\n"+value+"\n"+end,body)
        manuscript.write_text(body,encoding="utf-8",newline="\n")
    negatives=[p for p in pairs if p["classification"] in ["LOSS","MIXED"]]
    assert len(negatives)==9
    unknown=[p for p in cp if p["arm"]=="ENS-C" and p["checkpoint_seconds"] is not None and p.get("last_witness_F") is None]
    assert len(unknown)==4
    physical=[replay((auth/"PB-C50-S.txt").read_text(),a) for a in core["own_fleets"]]
    cover_checks=[]
    for ob in core["proof_obligations"]:
        if not ob["active_cover"]:continue
        cc=sorted(ob["active_cover"],key=lambda x:float(x["gamma_L"]))
        assert float(cc[0]["gamma_L"])==0
        assert all(float(a["gamma_U"])==float(b["gamma_L"]) for a,b in zip(cc,cc[1:]))
        assert float(cc[-1]["gamma_U"])==ob["U"]
        L=min([ob["U"]]+[float(c["lower_bound"]) for c in cc])
        assert L==ob["L"]
        cover_checks.append({"arm":ob["arm"],"L":L,"unresolved":sum(x["status"]=="open" for x in cc)})
    mb=next(a for a in core["arms"] if a["arm"]=="M-B")
    ob=next(a for a in core["proof_obligations"] if a["arm"]=="M-B")
    low=sorted(ob["active_cover"],key=lambda x:float(x["gamma_L"]))[:2]
    counter={"fixed_U":mb["U"],"fixed_L0":float(low[0]["lower_bound"]),"fixed_L1":float(low[1]["lower_bound"]),
             "close_I0_remaining_gap":mb["U"]-float(low[1]["lower_bound"]),
             "close_I1_global_L":float(low[0]["lower_bound"]),"performance_prediction":False}
    receipt={"R122_arms":32,"R122_pairs":48,"new_problems":6,"fixed_Seed1_blocks":2,
             "R123_arms_on_one_known_problem":3,"R123_pairs":3,"negative_mixed_pairs":len(negatives),
             "ENS_unknown_prefix_checkpoints":len(unknown),"recomputed_pairs":checked,
             "physical_endpoints_replayed":physical,"cover_checks":cover_checks,"counterfactual_ledger":counter,
             "source_hashes":{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(auth.iterdir())},
             "optimization_calls":0,"solver_process_starts":0,"production_compilations":0,
             "elapsed_seconds":time.perf_counter()-start}
    (out/"arithmetic_checks.json").write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf-8",newline="\n")
    print(json.dumps({k:receipt[k] for k in ["R122_arms","R122_pairs","negative_mixed_pairs","ENS_unknown_prefix_checkpoints","elapsed_seconds"]}))

if __name__=="__main__":main()
