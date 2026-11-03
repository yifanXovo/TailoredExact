"""Finite evidence-driven stage entry; no optimizer, Native load or compilation."""
import time
_started=time.perf_counter()
from round149_common import *


def k35():
    import round149_campaign as campaign
    configure();before=budget();assert not before['unclosed']
    full=read(OUT/'reports/full.json');assert not full['pending']
    assert len(full['comparisons'])==1;comparison=full['comparisons'][0]
    assert comparison['role']=='K-35-U' and comparison['U_improvement_percent']>1
    assert not comparison['serious_double_open_regression']
    assert before['remaining_G1_seconds']>=4800+1800
    reason=('K35 same-new-PE full pair improves physical U 2.003483% and signed gap 6.691554%, '
        'with supported L .877536% lower; both open. This useful but finite tradeoff justifies '
        'one RB35-T2 pressure pair to test preservation of standalone D incumbent benefit '
        'under a resource-shortage floor. It does not justify promotion, extra seeds or an automatic proof panel.')
    write(OUT/'reports/k35_snapshot.json',full)
    role=read(ROOT/'results/unified_exact_round148/rb35_matrix.json')['groups'][0]['launch']['id']
    campaign.freeze('rb35',[dict(role=role,method=m,cap=2400) for m in ['D','D_PF']],reason)
    write(OUT/'stages/k35_decision.json',dict(decision='PROCEED_RB35_PRESSURE_PAIR',reason=reason,
        comparison=comparison,budget_before=before,complete_cap_reserved=4800,verification_reserve=1800,
        no_K20_RX20_or_Seed_panel_admitted=True,new_PE_unchanged=True,
        matrix_SHA=sha(OUT/'rb35_matrix.json'),independent_admission_required=True,
        Optimize=0,Native_load=0,compile=0))


def versions():
    current=(ROOT/'scripts/round149_writer.cpp').read_text(encoding='utf-8')
    v2=current.replace('name=="e_1"&&tag!="fixed"','name=="e_1"')
    v2=v2.replace('name.rfind("r_",0)==0&&name.size()>2&&name[2]>=\'0\'&&name[2]<=\'9\'',
        'name.rfind("r_",0)==0')
    start=v2.index('        // W_SP is the existing ratio-sum')
    end=v2.index('        point(dir/"nonminimal_epigraph.json"',start)
    initial=v2[:start]+v2[end:]
    target=OUT/'engineering/helper_versions';target.mkdir(parents=True,exist_ok=True)
    facts=[]
    for tag,data,receipt in [('initial',initial,'writer_driver.json'),('v2',v2,'writer_driver_v2.json')]:
        expected=read(OUT/receipt)['source_SHA'];path=target/f'round149_writer_{tag}.cpp'
        raw=data.encode();assert hashlib.sha256(raw).hexdigest()==expected,(tag,expected,hashlib.sha256(raw).hexdigest())
        assert not path.exists();path.write_bytes(raw)
        facts.append(dict(version=tag,source=path.relative_to(ROOT).as_posix(),SHA256=expected,
            reconstructed_from_final_by_only_recorded_fixture_differences=True,new_compile=0))
    for name in ['round149_math.py','round149_lp.py','round149_common.py']:
        data=git('show','380a85f866bffb914036190f8ee2700ce8b55978:scripts/'+name)
        expected=read(OUT/'LP/K-35-U_PF/result.json')['helper_SHA'][name]
        # Git text normalization is admitted only when the exact recorded bytes
        # are recovered; never replace a source hash with a semantic match.
        if hashlib.sha256(data).hexdigest()!=expected:
            data=data.replace(b'\n',b'\r\n')
        assert hashlib.sha256(data).hexdigest()==expected,name
        path=target/('LP_'+name);path.write_bytes(data)
        facts.append(dict(version='LP_executed',source=path.relative_to(ROOT).as_posix(),
            SHA256=expected,Git_commit='380a85f866bffb914036190f8ee2700ce8b55978'))
    write(OUT/'engineering/helper_version_recovery.json',dict(PASS=True,records=facts,
        Optimize=0,Native_load=0,compile=0,only_exact_recorded_byte_hashes_accepted=True))


if __name__=='__main__':
    action=sys.argv[1];globals()[action]()
    configure();path=OUT/'infra/external_costs.json';value=read(path)
    elapsed=time.perf_counter()-_started
    value['processes'].append(dict(kind='diagnostic',outer_seconds=elapsed,label='stage_'+action,
        basis='One measured Python outer frame, includes imports/arithmetic/metadata; no Optimize/Native/compile; final startup allowance disclosed'))
    write(path,value);print(json.dumps(dict(action=action,seconds=elapsed,budget=budget())))
