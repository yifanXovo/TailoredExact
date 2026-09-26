"""Compact measured pairs, budget/readback and finite passive trajectory audit.

No optimization. Incomplete processes are retained in budget accounting and are
never used as completed performance evidence. Raw outputs are not overwritten.
"""
import csv
import json
import re
from collections import Counter, defaultdict
from round62_research import ROOT, OUT, RAW, previous, write, sha, panel
from analyze_round62 import performance, table


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def calls_for(e, folder):
    ledger = folder/'external'/'paper_optimize_ledger.csv'
    if ledger.exists():
        return len(list(csv.DictReader(ledger.open(newline='')))), str(ledger.relative_to(ROOT))
    for name in ['micro_result.json', 'oracle_result.json', 'audit_result.json']:
        path = folder/name
        if path.exists():
            result = read(path)
            if 'optimizer_calls' in result:
                return result['optimizer_calls'], str(path.relative_to(ROOT))
    if (folder/'native_calls.csv').exists():
        return len(list(csv.DictReader((folder/'native_calls.csv').open(newline='')))), 'write-ahead native_calls.csv'
    if e['kind'] in ['proof', 'build-only']:
        return 0, 'no optimizer in this executable/mode'
    if (folder/'completion.json').exists() and read(folder/'completion.json')['returncode'] == 0:
        if isinstance(e['solver_calls_planned'], int):
            return e['solver_calls_planned'], 'single synchronous native call; native log retained'
        if e['arm'] == 'P-GRB':
            return 1, 'original single synchronous compact P-GRB'
    return None, 'incomplete or missing finalized native ledger'


def budget():
    rows = []
    for e in previous.entries():
        folder = ROOT/e['destination']
        done = read(folder/'completion.json') if (folder/'completion.json').exists() else {}
        calls, evidence = calls_for(e, folder)
        rows.append(dict(number=e['charged_number'], charged=e['charged'], id=e['id'], stage=e['stage'],
            arm=e['arm'], kind=e['kind'], cap=e['cap_seconds'], complete=bool(done),
            optimizer_calls=calls, call_evidence=evidence, wall_seconds=done.get('wall_seconds'),
            watchdog=done.get('watchdog'), within_budget=done.get('within_budget'),
            returncode=done.get('returncode'), build_freeze=e.get('build_freeze'),
            executable_sha256=e['executable_sha256'], destination=e['destination']))
    charged = [r for r in rows if r['charged']]
    completed = [r for r in charged if r['complete']]
    summary = dict(charged_launches=len(charged), maximum=72,
        native_micro=sum(r['kind']=='native-micro' for r in charged), native_micro_maximum=4,
        by_kind=dict(Counter(r['kind'] for r in charged)),
        by_cap=dict(Counter(r['cap'] for r in charged)),
        complete=len(completed), incomplete=len(charged)-len(completed),
        recorded_internal_optimizer_calls=sum(r['optimizer_calls'] or 0 for r in rows),
        unknown_call_counts=[r['number'] for r in charged if r['optimizer_calls'] is None],
        watchdog_runs=[r['number'] for r in completed if r['watchdog']],
        over_budget_runs=[r['number'] for r in completed if not r['within_budget']],
        failed_runs=[r['number'] for r in completed if r['returncode']],
        excluded_performance_runs=[e['number'] for e in read(OUT/'run_exclusions.json') if e['exclude_performance']] if (OUT/'run_exclusions.json').exists() else [],
        charged_wall_seconds=sum(r['wall_seconds'] for r in completed))
    assert len(charged)<=72 and summary['native_micro']<=4
    table(OUT/'budget.csv', rows)
    write(OUT/'budget.json', summary)
    return summary


def certificate(r):
    return r.get('fixed_interval_certificate') if r.get('scope')=='fixed_F0_improving_domain' else r.get('strict_certified_original_problem')


def compare(a, b):
    assert a['exe_sha256']==b['exe_sha256'] and a['cap']==b['cap'] and a['scope']==b['scope']
    ca, cb = certificate(a), certificate(b)
    row = dict(id=a['id'], stage=a['stage'], scope=a['scope'], baseline=a['arm'], candidate=b['arm'],
        baseline_number=a['number'], candidate_number=b['number'], cap=a['cap'],
        baseline_certified=ca, candidate_certified=cb, baseline_wall=a['wall'], candidate_wall=b['wall'],
        baseline_UB=a['upper_bound'], candidate_UB=b['upper_bound'],
        baseline_LB=a['lower_bound'], candidate_LB=b['lower_bound'],
        baseline_absolute_gap=max(0,a['absolute_gap']), candidate_absolute_gap=max(0,b['absolute_gap']),
        baseline_relative_gap=a.get('gap'), candidate_relative_gap=b.get('gap'),
        baseline_Work=a.get('work'), candidate_Work=b.get('work'), exe_sha256=a['exe_sha256'])
    if ca != cb:
        row['decision']='certificate_gain' if cb else 'certificate_loss'
    elif ca and cb:
        delta = a['wall']-b['wall']
        row.update(certification_seconds_saved=delta, certification_fraction_saved=delta/a['wall'])
        row['decision']=('time_gain' if delta>0 else 'time_loss') if abs(delta)>=10 and abs(delta)/a['wall']>=.1 else 'below_time_threshold'
    else:
        delta=max(0,a['absolute_gap'])-max(0,b['absolute_gap'])
        fraction=delta/max(0,a['absolute_gap']) if a['absolute_gap']>1e-10 else None
        row.update(absolute_gap_saved=delta, gap_fraction_saved=fraction)
        row['decision']=('gap_gain' if delta>0 else 'gap_loss') if abs(delta)>=.001 and fraction is not None and abs(fraction)>=.05 else 'below_gap_threshold'
    return row


def pairs():
    groups=defaultdict(dict)
    all_runs=performance()
    for r in all_runs:
        if r.get('scope') and r['within_budget'] and not r['returncode'] and r['performance_eligible']:
            groups[(r['id'],r['stage'],r['cap'],r['scope'])][r['arm']]=r
    rows=[]
    for group in groups.values():
        for name, candidate in group.items():
            controls=[]
            if name.startswith(('Single-', 'K1-')):
                prefix=name.split('-')[0]
                base=prefix+'-off-off'
                if name!=base: controls.append(base)
                if name.startswith(prefix+'-passive-cert-') and name!=prefix+'-passive-cert-off':
                    threshold=name[len(prefix+'-passive-cert-'):]
                    controls += [prefix+'-off-'+threshold,prefix+'-passive-cert-off']
            elif name!='off':
                controls.append('off')
                if name=='conflicts': controls.append('events')
                if name=='service-conflicts': controls.append('service')
                if name=='projection-rlt': controls.append('projection')
                if name=='projection-service': controls.append('projection')
            for control in dict.fromkeys(controls):
                if control in group: rows.append(compare(group[control],candidate))
    references={r['arm']:r for r in all_runs if r['id']=='C2' and r['stage']=='references_v3' and r.get('scope')}
    candidates=[r for r in all_runs if r['id']=='C2' and r['stage']=='k1_v3' and r.get('scope')]
    for ref in references.values():
        for candidate in candidates:
            row=compare(ref,candidate);row['stage']='references_v3 -> k1_v3'
            row['comparison_kind']='unchanged complete-policy reference; not isolated mechanism attribution'
            rows.append(row)
    if 'P-GRB' in references and 'K1-H' in references:
        row=compare(references['P-GRB'],references['K1-H'])
        row['comparison_kind']='unchanged references';rows.append(row)
    table(OUT/'pairs.csv', rows)
    return rows


def passive_trajectory():
    group=RAW/'full_screen'/'D3'
    rows=[]; traces=[]
    for mode in ['off','passive-observe','passive-cert']:
        folder=group/('Single-'+mode+'-off')
        if not (folder/'completion.json').exists():return
        result=read(folder/'result.json')
        params={p:result['gurobi_'+p+'_effective'] for p in ['threads','seed','presolve','mip_gap','mip_gap_abs']}
        assert params==dict(threads=1,seed=0,presolve=-1,mip_gap=0,mip_gap_abs=0)
        assert all(result['gurobi_'+p+'_get_return_code']==0 for p in params)
        ledger=list(csv.DictReader((folder/'external'/'paper_optimize_ledger.csv').open(newline='')))
        path=folder/'external'/'native_logs'/'L0_terminal_mip.gurobi.log'
        text=path.read_text(errors='replace')
        # Incumbent events indexed by native node count, including current bound,
        # queue size and incumbent, with only elapsed wall time removed.
        logical=[]
        for line in text.splitlines():
            if re.match(r'^[H*]\s*\d',line):
                logical.append(re.sub(r'\s+\d+s\s*$','',line).split())
        traces.append(logical)
        rows.append(dict(mode=mode,parameters_read_back=params,
            call_sequence=[dict(kind=c['solve_kind'],status=c['native_status'],model=c['model_sha256'],work=float(c['work']),nodes=float(c['nodes'])) for c in ledger],
            incumbent_logical_events=logical, log_sha256=sha(path),
            archive_seconds=result['round62_archive_construction_seconds']))
    common=min(map(len,traces)); equal=all(t[:common]==traces[0][:common] for t in traces)
    write(OUT/'passive_trajectory.json',dict(id='D3',stage='full_screen',
        same_incumbent_events_at_same_native_nodes=equal, compared_events=common,
        all_event_counts=list(map(len,traces)),
        explanation='Finite native-node/event alignment and Work/call/parameter readback; wall-clock node totals need not coincide. This is not a theorem about every machine/run.', arms=rows))
    assert equal, 'inspect differing native logical trajectories before claiming non-interference'


def coverage_audit():
    """Independently aggregate recorded complete snapshots at observed callbacks.

    Does not invent callbacks or future closure points. The finalized C++ gate
    and independent physical witness audit remain separately necessary.
    """
    summary=[];panels=panel()
    for e in previous.entries():
        folder=ROOT/e['destination'];path=folder/'external'/'round62_coverage.csv'
        if not (folder/'completion.json').exists() or not path.exists():continue
        snapshots=defaultdict(list)
        for row in csv.DictReader(path.open(newline='')):snapshots[row['call']].append(row)
        points=list(csv.DictReader((path.parent/'round62_observations.csv').open(newline='')))
        checked=0;eligible=0;max_leaves=0;epochs=set()
        for point in points:
            s=snapshots[point['call']];head=s[0];epochs.add(int(head['epoch']))
            live=[r for r in s if r['status'] not in ['replaced','coalesced']]
            max_leaves=max(max_leaves,len(live))
            assert head['root_coverage']=='1' and head['tree_coverage']=='1'
            control=float(head['control_ub']);archive=float(head['archive_ub']);tol=1e-7
            active=head['active'];bound=control;covered=0
            assert sum(r['leaf']==active for r in live)==1
            for leaf in sorted(live,key=lambda r:float(r['gamma_L'])):
                assert float(leaf['gamma_L'])<=covered+tol
                covered=max(covered,float(leaf['gamma_U']))
                assert float(leaf['cutoff'])+tol>=control
                b=control if leaf['status']=='empty' else float(leaf['lower_bound'])
                if leaf['leaf']==active:b=max(b,float(point['native_bound']))
                bound=min(bound,b)
            n=int(panels[e['id']]['V']);assert covered+tol>=min(control,(n-1)/n)
            usable=min(control,archive)
            if point['valid']=='1':
                assert abs(bound-float(point['global_bound']))<tol
                assert abs(usable-float(point['usable_ub']))<tol
                assert bound<=usable+tol
                assert bool(int(point['eligible']))==(usable-bound<=tol)
            if point['termination_requested']=='1':assert point['valid']=='1' and point['eligible']=='1'
            eligible+=int(point['eligible']);checked+=1
        result=read(folder/'result.json')
        summary.append(dict(number=e['charged_number'],id=e['id'],stage=e['stage'],arm=e['arm'],
            recorded_snapshots=len(snapshots),observed_points_checked=checked,eligible_observations=eligible,
            maximum_live_leaves=max_leaves,epochs=sorted(epochs),
            final_control_UB=result['round62_control_upper_bound'],final_archive_UB=result['round62_archive_upper_bound'],
            final_strict_certificate=result['strict_certified_original_problem'],
            final_external_certificate=result['round62_external_certificate'],
            stop_requested=result['round62_external_stop_requested'],passed=True))
    write(OUT/'passive_coverage_verification.json',summary)


def appendix():
    """All completed observations, not just winning pairs; no optimizer."""
    runs=performance();summary=read(OUT/'budget.json')
    lines=['# Round 62 完整数据附录','',
        '由 `scripts/report_round62.py` 从逐启动 ledger 与已完成结果生成。未认证的墙钟数值是预算使用量，不能当作求解时间。',
        '固定 F0 证书与完整原问题证书分开；所有配对的构建、预算、作用域必须一致。','',
        '## 预算','',
        f"计费 {summary['charged_launches']}/72；完成 {summary['complete']}；未完成 {summary['incomplete']}；native micro {summary['native_micro']}/4；内部优化器调用 {summary['recorded_internal_optimizer_calls']}。",
        f"失败 {summary['failed_runs']}；watchdog {summary['watchdog_runs']}；超预算 {summary['over_budget_runs']}。全部详细启动及命令见 processes.jsonl、budget.csv。",'',
        f"排除性能归因的已计费记录：{summary['excluded_performance_runs']}，原因见 run_exclusions.json；下表仍完整保留其原始结果。",'',
        '## 全部固定区间及完整算法运行','',
        '| 编号 | 角色 | 阶段 | 配置 | cap/s | wall/s | 证书 | UB | LB | 绝对 gap | 相对 gap | Work | nodes |',
        '|---:|---|---|---|---:|---:|---|---:|---:|---:|---:|---:|---:|']
    def fmt(x,digits=8):return '—' if x is None else f'{x:.{digits}g}'
    for x in runs:
        if not x['charged'] or not x.get('scope'):continue
        values=[x['number'],x['id'],x['stage'],x['arm'],x['cap'],f"{x['wall']:.3f}",
            ('fixed ' if x['scope']=='fixed_F0_improving_domain' else 'original ')+('yes' if certificate(x) else 'no'),
            fmt(x['upper_bound']),fmt(x['lower_bound']),fmt(max(0,x['absolute_gap'])),fmt(x.get('gap')),
            fmt(x.get('work')),fmt(x.get('nodes'))]
        lines.append('| '+' | '.join(map(str,values))+' |')
    lines+=['','## 同构建配对及冻结双门槛','',
        '证书增减单列；均认证时需要 10 秒及 10%；均未认证时需要绝对 gap 0.001 及 5%。负值表示回退。','',
        '| 角色 | 阶段 | 编号 | 对照 → 候选 | 判定 | 认证秒数节省 | 未认证绝对 gap 节省 |',
        '|---|---|---|---|---|---:|---:|']
    for x in pairs():
        lines.append('| '+' | '.join(map(str,[x['id'],x['stage'],f"{x['baseline_number']}→{x['candidate_number']}",
            x['baseline']+' → '+x['candidate'],x['decision'],fmt(x.get('certification_seconds_saved')),
            fmt(x.get('absolute_gap_saved'))]))+' |')
    lines+=['','## 固定 F0 原生根处理及表示成本','',
        '| 编号 | 配置 | rows | cols | nonzeros | build/s | root LP | 根割后 bound | root Work | root/s |',
        '|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for x in runs:
        if x.get('scope')!='fixed_F0_improving_domain':continue
        lines.append('| '+' | '.join(map(str,[x['number'],x['id']+' '+x['arm'],x.get('rows'),x.get('columns'),x.get('nonzeros'),
            fmt(x.get('model_build_seconds')),fmt(x.get('root_relaxation_bound')),fmt(x.get('final_root_cut_bound')),
            fmt(x.get('root_work')),fmt(x.get('root_time_seconds'))]))+' |')
    lines+=['','## 完整算法生命周期','',
        '| 编号 | 角色 / 配置 | 调用数 | 末叶数 | 分裂数 | PREFIX/s | 外部停止 | 外部证书 | native statuses |',
        '|---:|---|---:|---:|---:|---:|---|---|---|']
    for x in runs:
        if x.get('scope')!='full_original_problem':continue
        lines.append('| '+' | '.join(map(str,[x['number'],x['id']+' '+x['arm'],x.get('optimizer_calls','—'),
            x.get('external_gini_tree_final_leaf_count','—'),x.get('external_gini_tree_split_count','—'),
            fmt(x.get('round62_archive_construction_seconds')),x.get('round62_external_stop_requested','—'),
            x.get('round62_external_certificate','—'),str(x.get('native_statuses','see original native log')).replace('|','; ')]))+' |')
    lines+=['','原始的 native-target INTERRUPTED、TIME_LIMIT、OPTIMAL 分开保存；外部逻辑证书不重写这些状态。',
        'LP 松弛及合法连续补全见 lp_comparison.csv、frozen_lp_completion.json；节点见 native_point_separation.json。',
        '投影包含关系查询见 projection_containment_verification.json 和 projection_audit/；自动冲突与原路线独立复核见 proofs/、witnesses/ 及对应 verification 文件。','']
    lines+=['','## 冻结面板','',
        '| 角色 | V | M | Q / Q向量 | T/s | lambda | pick/drop 秒 | 本轮角色 |',
        '|---|---:|---:|---|---:|---:|---|---|']
    for p in panel().values():
        lines.append('| '+' | '.join(map(str,[p['id'],p['V'],p['M'],p.get('complete_Q_vector',p['Q']),
            p['T_seconds'],p['lambda'],str(p['pickup_seconds'])+'/'+str(p['drop_seconds']),
            '开发/保护' if p['stage']=='development' else '未参与本轮选择的旧公开角色']))+' |')
    lines+=['','完整输入路径、SHA-256、manifest 来源和冻结规则见 protocol.json；D3 T=2850，D4 T=2400。','']
    (OUT/'data_appendix.md').write_text('\n'.join(lines),encoding='utf-8')


def main():
    summary=budget(); measured=pairs(); passive_trajectory();coverage_audit();appendix()
    print(json.dumps(summary,indent=2))
    print('paired comparisons',len(measured))


if __name__=='__main__':main()
