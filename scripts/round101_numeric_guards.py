"""One-time bounded guard repair, admitted only after development is complete.

Preserves prior measurements and changes only the new fleet module/tests.
No Optimize. Build/qualification and final-source full arms remain separate.
"""
import json,sys
from round100_idle import ensure_idle
from round101_common import *

def repair(dry_run=False):
    if not dry_run:ensure_idle()
    campaign=OUT/'development01'
    identity=read(campaign/'identity.json')
    done=[json.loads(x) for x in (campaign/'summary.jsonl').read_text().splitlines()]
    if not dry_run:assert len(done)==6 and all(x['audit_passed'] for x in done)
    assert identity['source_hashes']==bindings()
    source=ROOT/'src/FleetEventCuts.cpp';old=source.read_text();new=old
    def change(a,b):
        nonlocal new
        assert new.count(a)==1,(a,new.count(a))
        new=new.replace(a,b)
    change('if(a==0||b==0)return 0;return std::max(0.0,down(a*static_cast<double>(b)));',
           'if(a==0||b==0)return 0;\n    // An inexact integer conversion cannot justify exclusion. Unknown weakens.\n    if(b<0||b>9007199254740992LL)return 0;\n    return std::max(0.0,down(a*static_cast<double>(b)));')
    change('if(!c.valid||!ready()||es.empty())return false;',
           'if(!c.valid||!ready()||es.empty()||es.size()>static_cast<std::size_t>(std::numeric_limits<int>::max())||\n        c.capacities.empty()||c.capacities.size()>static_cast<std::size_t>(std::numeric_limits<int>::max()/2))return false;')
    change('c.horizon_upper=up(in.total_time_limit+kPhysicalDurationTolerance);c.handling_lower=std::max(0.0,down(in.pickup_time+in.drop_time));c.travel_lower=in.dist;',
           'const double nominal_handling=in.pickup_time+in.drop_time;\n    c.horizon_upper=up(in.total_time_limit+kPhysicalDurationTolerance);c.handling_lower=std::max(0.0,down(nominal_handling));c.travel_lower=in.dist;')
    change('if(!ready()||in.V<1||in.M<1||in.Q.size()!=static_cast<std::size_t>(in.M)||',
           'if(!ready()||in.V<1||in.V==std::numeric_limits<int>::max()||in.M<1||in.M>std::numeric_limits<int>::max()/2||\n        !std::isfinite(nominal_handling)||in.Q.size()!=static_cast<std::size_t>(in.M)||')
    change('in.initial.size()!=static_cast<std::size_t>(in.V+1)',
           'in.initial.size()!=static_cast<std::size_t>(in.V)+1')
    change('const int n=static_cast<int>(m.names.size()),R=static_cast<int>(m.senses.size());c.columns=n;',
           'if(m.names.size()>static_cast<std::size_t>(std::numeric_limits<int>::max())||\n            m.senses.size()>=static_cast<std::size_t>(std::numeric_limits<int>::max())||\n            m.coefficients.size()>static_cast<std::size_t>(std::numeric_limits<int>::max()))throw std::runtime_error("unsupported_matrix_dimensions");\n        const int n=static_cast<int>(m.names.size()),R=static_cast<int>(m.senses.size());c.columns=n;')
    change('for(int v=L;v<=U;++v) {',
           'for(long long inventory=L;inventory<=U;++inventory) {\n                const int v=static_cast<int>(inventory);')
    change('if(!goodEvents(c,es)||es.size()>10){out.reason="invalid_or_unsupported_small_support";return out;}',
           'if(!goodEvents(c,es)||es.size()>10){out.rank=0;out.reason="invalid_or_unsupported_small_support";return out;}')
    change('if(!goodEvents(c,es)){out.reason="invalid_events_or_arithmetic";return out;}',
           'if(!goodEvents(c,es)){out.rank=0;out.reason="invalid_events_or_arithmetic";return out;}')
    # Avoid implementation-defined narrowing even for rejected caller input.
    assert new.count('out.rank=static_cast<int>(es.size());')==2
    new=new.replace('out.rank=static_cast<int>(es.size());',
        'out.rank=es.size()<=static_cast<std::size_t>(std::numeric_limits<int>::max())?static_cast<int>(es.size()):0;')
    change('std::vector<int> caps(2*M);int total=0;',
           'std::vector<int> caps(static_cast<std::size_t>(M)*2);long long total=0;')
    change('total+=caps[2*k]+caps[2*k+1];','total+=static_cast<long long>(caps[2*k])+caps[2*k+1];')
    change('int rank=total;','long long rank=total;')
    change('out.rank=std::min(static_cast<int>(es.size()),rank);',
           'out.rank=static_cast<int>(std::min(static_cast<long long>(es.size()),rank));')
    change('std::vector<FleetCut> rows;if(!c.valid||!ready()||point.size()!=static_cast<std::size_t>(c.columns)||',
           'std::vector<FleetCut> rows;if(!c.valid||!ready()||c.columns<=0||c.states.size()!=c.initial.size()||\n        c.capacities.empty()||point.size()!=static_cast<std::size_t>(c.columns)||')
    change('low[i].assign(maxQ+1,0);high[i].assign(maxQ+1,0);',
           'low[i].assign(static_cast<std::size_t>(maxQ)+1,0);high[i].assign(static_cast<std::size_t>(maxQ)+1,0);')
    change('for(auto [y,j]:c.states[i])for(int q=1;q<=maxQ;++q) {',
           'for(auto [y,j]:c.states[i])for(long long threshold=1;threshold<=maxQ;++threshold) {\n            const int q=static_cast<int>(threshold);')
    change('for(int sign:{-1,1})for(int q=1;q<=maxQ;++q) {\n        std::vector<FleetEvent> es;',
           'for(int sign:{-1,1})for(long long threshold=1;threshold<=maxQ;++threshold) {\n        const int q=static_cast<int>(threshold);\n        std::vector<FleetEvent> es;')
    change('q<static_cast<int>(mass[i].size())','static_cast<std::size_t>(q)<mass[i].size()')
    change('FleetEvent best;for(int sign:{-1,1})for(int q=1;q<=maxQ;++q) {',
           'FleetEvent best;for(int sign:{-1,1})for(long long threshold=1;threshold<=maxQ;++threshold) {\n                const int q=static_cast<int>(threshold);')
    change('if(2*count>static_cast<int>(std::min(row.proof.events.size(),old.proof.events.size())))overlap=true;',
           'if(2LL*count>static_cast<long long>(std::min(row.proof.events.size(),old.proof.events.size())))overlap=true;')
    tests=ROOT/'tests/round101_fleet_tests.cpp';old_tests=tests.read_text()
    assert '#include <limits>' not in old_tests
    new_tests=old_tests.replace('#include <iostream>','#include <iostream>\n#include <limits>')
    marker='    for(int M=1;M<=3;++M)'
    assert new_tests.count(marker)==1
    fixtures=r'''    in=instance(1,1,10,1,{1});in.drop_time=3*std::ldexp(1.0,-53);c=physicalFleetContract(in);
    check(c.valid&&c.handling_lower<=std::nextafter(1.0,2.0),"nonexact physical sum lower enclosure");
    FleetStatistics no_columns;
    check(separateFleetEvents(c,{},1e-5,no_columns).empty()&&no_columns.arithmetic_skips==1,"unmapped physical separator skipped");
    in.pickup_time=std::numeric_limits<double>::max();in.drop_time=in.pickup_time;
    check(!physicalFleetContract(in).valid,"nominal handling overflow rejected");
    in=instance(1,1,100,1,{1});in.initial[1]=in.capacity[1]=std::numeric_limits<int>::max();
    NativeOtB1LinearModel edge;
    edge.names={"Y_1","state_1_2147483647","p_0_1","d_0_1","z_0_1","mode_0_1","ord_0_1","x_0_0_1","x_0_1_0"};
    edge.types={'I','B','I','I','B','B','C','B','B'};
    const double imax=std::numeric_limits<int>::max();
    edge.lower_bounds={imax,0,0,0,0,0,0,0,0};edge.upper_bounds={imax,1,1,0,1,1,1,1,1};edge.row_starts={0};
    auto add=[&](char sense,double rhs,std::initializer_list<std::pair<int,double>> a) {
        edge.senses.push_back(sense);edge.rhs.push_back(rhs);
        for(auto [j,v]:a){edge.column_indices.push_back(j);edge.coefficients.push_back(v);}
        edge.row_starts.push_back(static_cast<int>(edge.coefficients.size()));
    };
    add('=',1,{{1,1}});add('=',0,{{0,1},{1,-imax}});
    add('<',0,{{5,1},{4,-1}});add('<',0,{{2,1},{5,-1}});add('<',0,{{3,1}});
    add('>',0,{{2,1},{3,1},{4,-1}});add('=',imax,{{0,1},{2,1},{3,-1}});add('<',1,{{4,1}});
    add('=',0,{{8,1},{4,-1}});add('=',0,{{7,1},{4,-1}});
    add('<',1,{{7,1}});add('=',0,{{7,1},{8,-1}});add('>',0,{{2,1},{3,-1}});add('<',100,{{2,1}});
    check(prepareFleetContract(in,edge).valid,"fixed INT_MAX inventory endpoint audit");
'''
    new_tests=new_tests.replace(marker,fixtures+marker)
    if dry_run:
        assert new!=old and new_tests!=old_tests
        print(json.dumps(dict(anchors_verified=True,production_files_written=False,Optimize=0)))
        return
    before=bindings();before_tests_sha256=sha(tests)
    source.write_text(new,encoding='utf-8',newline='\n')
    tests.write_text(new_tests,encoding='utf-8',newline='\n')
    write(OUT/'numeric_guard_revision.json',dict(before_source_hashes=before,after_source_hashes=bindings(),
        before_tests_sha256=before_tests_sha256,after_tests_sha256=sha(tests),
        development_identity_sha256=sha(campaign/'identity.json'),development_summary_sha256=sha(campaign/'summary.jsonl'),
        family_strength_range_unchanged=True,finite_case_handling_lower_unchanged=True,
        no_performance_gain_attribution=True,Optimize=0))
    print(json.dumps(dict(repaired=True,Optimize=0)))

if __name__=='__main__':repair('--dry-run' in sys.argv[1:])
