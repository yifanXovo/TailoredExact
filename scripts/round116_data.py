"""Preregister, fetch one official static snapshot, and adapt R57/R109 pure rules.

This module never imports a solver, opens the former private station source,
or launches native optimization. Existing evidence is never replaced.
"""
from __future__ import annotations
import argparse, ast, copy, csv, dataclasses, datetime, hashlib, inspect, itertools
import json, math, platform, shutil, statistics, subprocess, sys, time
import urllib.error, urllib.parse, urllib.request
from pathlib import Path
import generate_citibike443_regional_v1 as old
import round109_data as inherited

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/unified_exact_round116'
REFERENCE = ROOT / 'reference/round116_external'
BASE = '7eef812efb1bd3046c48e76ff6ac968de276a9b0'
SOURCE = 'd0014a7163e3996fe120471420e56b089c9715ae'
PE_SHA = 'a8356b6ad6a5ced47e0d41374ec2184669349c083370eabd76989fb9c11539a8'
DLL_SHA = '9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88'
PE = ROOT / 'build/research/round116-inherited/ExactEBRP.exe'
DLL = Path('D:/gurobi1302/win64/bin/gurobi130.dll')
DATA_DEPS = ROOT / 'build/research/round116-data-deps'
VERSION = 'round116-capital-external-v1'
ENTRY = 'https://capitalbikeshare.com/system-data'
LICENSE = 'https://capitalbikeshare.com/data-license-agreement'
DISCOVERY = 'https://gbfs.capitalbikeshare.com/gbfs/2.3/gbfs.json'
ROLE_ROWS = [
    ('E20-C1',20,2,'compact',1,'shortage',[30,30],3600,900,['P-GRB','P-S','ENS-C','M-B']),
    ('E20-R2',20,2,'regional',2,'balanced',[20,40],7200,900,['P-S','M-B','P-GRB','ENS-C']),
    ('E50-C1',50,4,'compact',1,'balanced',[30]*4,7200,1800,['ENS-C','P-GRB','M-B','P-S']),
    ('E50-R2',50,4,'regional',2,'surplus',[20,25,35,40],18000,1800,['M-B','ENS-C','P-S','P-GRB']),
    ('E100-C1',100,8,'compact',1,'shortage',[20,20,25,25,35,35,40,40],18000,3600,['P-GRB','ENS-C','P-S','M-B']),
    ('E100-R2',100,8,'regional',2,'surplus',[30]*8,18000,3600,['P-S','P-GRB','M-B','ENS-C']),
]
ROLES = [dict(number=n,id=i,V=v,M=m,geometry=g,replicate=r,inventory=s,
              Q_vector=q,Q_class='H' if len(set(q))==1 else 'X',T_seconds=T,
              cap_seconds=c,method_order=o,pickup_seconds=60,drop_seconds=60,
              **{'lambda':.15},gurobi_seed=0,panel_kind='external')
         for n,(i,v,m,g,r,s,q,T,c,o) in enumerate(ROLE_ROWS,1)]

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def utc(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def write(p,v):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,indent=2,ensure_ascii=False);f.write('\n')
def textfile(p,v):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8',newline='\n') as f:f.write(v.rstrip()+'\n')
def csvfile(p,rows,fields=None):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    fields=fields or list(rows[0])
    with p.open('x',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(rows)
def source_bindings():
    ps=[ROOT/'CMakeLists.txt']+sorted((ROOT/'src').rglob('*.cpp'))+sorted((ROOT/'src').glob('*.inc'))+sorted((ROOT/'include').rglob('*.hpp'))
    return {p.relative_to(ROOT).as_posix():sha(p) for p in ps}
def projection():
    sys.path.insert(0,str(DATA_DEPS));import pyproj
    assert pyproj.__version__=='3.7.2'
    tr=pyproj.Transformer.from_crs('EPSG:4326','EPSG:32618',always_xy=True)
    x,y=tr.transform(-75,0,errcheck=True);assert abs(x-500000)<1e-8 and abs(y)<1e-8
    a=pyproj.CRS.from_epsg(32618).area_of_use
    info=dict(pyproj_version=pyproj.__version__,PROJ_version=pyproj.proj_version_str,
              always_xy=True,source_CRS='EPSG:4326',target_CRS='EPSG:32618',
              definition=tr.definition,description=tr.description,
              source_WKT=tr.source_crs.to_wkt(),target_WKT=tr.target_crs.to_wkt(),
              area_of_use=dict(west=a.west,south=a.south,east=a.east,north=a.north,name=a.name),
              axis_fixture=dict(lon=-75,lat=0,x=x,y=y,expected_x=500000,expected_y=0),
              Python=sys.version,data_dependencies_isolated_from_solver=True)
    return tr,info

def freeze():
    tick=time.perf_counter();OUT.mkdir(parents=True,exist_ok=False)
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==BASE
    assert not subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],cwd=ROOT,text=True).strip()
    origin=Path('E:/codes/ExactEBRP-round115/build/research/round115-inherited/ExactEBRP.exe')
    assert sha(origin)==PE_SHA and sha(DLL)==DLL_SHA
    PE.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(origin,PE)
    production=read(ROOT/'results/unified_exact_round115/production_identity.json')
    assert production['source_bindings']==source_bindings() and len(source_bindings())==206
    write(OUT/'production_identity.json',dict(production,round116_inherited_PE_origin=str(origin),
          round115_head=BASE,production_recompiled=False,production_algorithm_or_parameters_changed=False))
    shutil.copyfile('C:/Users/Administrator/.codex/attachments/1292f984-ecd9-4f7e-8938-4e1f8792a1ed/已粘贴的文本.txt',OUT/'goal.md')
    _,proj=projection();write(OUT/'projection_contract.json',proj)
    recipe=dict(schema='round116-source-recipe-v1',frozen_UTC=utc(),version=VERSION,
        family_material=VERSION+'|source_sha256={first_valid_station_response_SHA256}',
        selection_id_format='cabi_V{V:02d}_{compact_or_regional}_r{replicate}',
        official_entry=ENTRY,official_license=LICENSE,official_discovery=DISCOVERY,
        station_endpoint='read contemporaneous English station_information from official discovery',
        system_endpoint='read contemporaneous English system_information from same discovery',
        max_attempts_per_endpoint=3,unique_snapshot='first HTTP-successful structurally valid complete stations response',
        retries='transport/HTTP failure or truncated/invalid JSON only; never dissatisfaction with count/geography/difficulty',
        denied_access='stop without bypass or changed proxy/account',source_interface='official GBFS only',
        allow_hosts=['capitalbikeshare.com','www.capitalbikeshare.com','gbfs.capitalbikeshare.com','gbfs.lyft.com'],
        static_station_rule=dict(station_id='nonempty JSON string; preserve exact UTF-8 bytes and leading zeros',
            capacity='finite JSON numeric integer value, excluding bool/string; 0<capacity<100; no rounding/imputation',
            coordinates='finite JSON numeric WGS84 longitude[-180,180] latitude[-90,90], excluding bool/string',
            virtual='exclude exactly is_virtual_station=true; no dynamic status or vehicle/user/trip records'),
        exclusions='record every original zero-based stations-array row, reasons, ID and original row',
        duplicates='same ID: physical capacity/lat/lon/explicit virtual flag must agree, otherwise DATA_BLOCKED; merge identical and retain all rows',
        different_ID_same_coordinate='retain separately',source_order='station_id UTF-8 byte lexicographic; zero-based unique source_row_index',
        minimum_qualified_stations=200,projection_contract_SHA=sha(OUT/'projection_contract.json'),
        projection_range='all qualified WGS84 rows must lie within EPSG:32618 area; otherwise DATA_BLOCKED, no geographic exclusion',
        coordinates='pyproj float64, record full output then Python round(x,3); inherited three-decimal serialization',
        geographic_regimes=['compact','regional'],replicates=[1,2],
        pure_rules=dict(anchors='R57 four anchors per V: first SHA256 ordering; others max min Euclidean; tie smaller source index',
            compact='anchor nearest V in distance then source-index order',
            regional='farthest-first V within nearest 2V; maximize min distance, then smaller anchor distance, then smaller source index',
            target='R57 .44+.12*hash_unit; floor(C*f+.5), clipped[1,C]',
            inventory='R109/R57 delta=max(V,floor(.12*sumD+.5)); shortage sumD-delta, balanced sumD, surplus min(sumC,sumD+delta); original perturbation, total adjustment and both-sign repair',
            weight='max(.1,(D/maxD)^2), Python round six decimals, maximum normalization, round six decimals',
            depot='arithmetic centroid of serialized service coordinates, three decimals, placeholders100000/50000/0',
            distance='only original production Parser reconstructs Euclidean/1.5; no supplied distance matrix',
            min_ratio='four-decimal compatibility only, no inventory floor'),
        roles=ROLES,thin_adapter_SHA=sha(__file__),original_generator_SHA=sha(old.__file__),
        inherited_math_adapter_SHA=sha(inherited.__file__),no_private_source=True,no_solver_pilot=True,
        retain_every_legal_draw=True,independent_cities_or_IID_claim=False,real_demand_claim=False,
        license_scope='non-commercial research source appendix only; no standalone raw dataset, logos or endorsement')
    write(OUT/'source_recipe.json',recipe)
    csvfile(OUT/'roles_frozen.csv',[dict(r,Q_vector=json.dumps(r['Q_vector']),method_order=json.dumps(r['method_order'])) for r in ROLES])
    shutil.copyfile(ROOT/'results/unified_exact_round115/measurement_policy_v2.md',OUT/'inherited_measurement_policy_v2.md')
    shutil.copyfile(ROOT/'results/unified_exact_round115/producer_dependency_graph.json',OUT/'producer_dependency_graph.json')
    shutil.copyfile(ROOT/'results/unified_exact_round115/inherited_claim_policy_r114.md',OUT/'inherited_claim_policy_r114.md')
    textfile(OUT/'research_question.md', '''# Round116 research question

The missing evidence is finite transfer to one preregistered external station-coordinate/capacity source. Additional win/loss measurements on the old five roles would not answer that question. The frozen ENS-C default, R111 finite M-B candidate, cold P-GRB primary benchmark, and independently paid P-S contribution control will be compared on six specified synthetic inputs from one official system snapshot. All 24 arms and 36 within-role pairs are required for a complete panel.

The three evidence axes are execution completeness, feasible-solution/backend comparisons, and numerical proof reliability. A legal positive fleet, an own strict zero certificate from Y=D and F>=0, and a reliable nonzero native certificate are different outcomes. SOURCE_REDUCED_OPEN retains own U and independent floor0 but cannot establish native proof progress or recover wrongly pruned search. Known R115 contradictions are inherited risks rather than Round116 discoveries.

R115 completed four G100 arms. Its P-S own zero at producer1306.5367294s establishes optimum0; ENS/M-B/P positive endpoints remain approximately .0055284553/.0114347383/.0399421005. All four have a rejected native call, including P-S. The historical ENS/P-S W/W/L/W/L and M-B/P-S W/W/L/T/L vectors are MIXED with heterogeneous old-whole/new-producer clocks. G50 missing cold clock, R114 ENS overwhole and R110 BLOCKED remain unchanged.

The new panel can support limited transfer, contradict that expectation, or expose numerical inconsistency. Each is a valid result. It is neither a final paper benchmark nor six independent cities, real demand validation, a new algorithm, or authorization to reopen stopped mechanism grids. No result-based redraw, seed/lambda sweep, formal retry or production adjustment is permitted. After full execution, apply exactly one preregistered A-D resource decision; a genuine blocker receives BLOCKED with its precise scope.''')
    textfile(OUT/'source_and_scope.md', '''# Source and synthetic scope

Only station coordinates and capacities change source. The official GBFS static station information belongs to the Capital Bikeshare system. Initial inventories, targets, weights, vehicles/capacities, route horizons and the artificial depot are deterministic same-family synthetic fields. One snapshot supplies all six inputs; source subsets may overlap. This tests finite cross-source transfer, not six independent cities, IID geographic replication or effectiveness on real demand schedules.

The source response is retained solely as source material for this non-commercial research study under the official data-license agreement. It is not a standalone raw-data service or repository. The external operator and jurisdictions do not endorse this research; no logo is used. Only official static metadata is requested; no trips, passengers, user or bicycle trajectories are requested. The discovery, license bytes, request receipts, filtering and projection record are part of the research appendix.''')
    textfile(OUT/'RESUME.md','Round116 data preregistration frozen. No source station response has yet been fetched, no reference exporter or Optimize started, and no formal arm started. Preserve the first valid response and every existing destination. Production algorithms and measurement-v2 producer/verification boundaries remain frozen. Total56 starts/65000 outer seconds; qualification16/1800 included. Expected formal30 starts/50400 nominal+720 administration. Resume from source acquisition and actual receipts; never repeat an existing formal launch.')
    write(OUT/'initialization_receipt.json',dict(UTC=utc(),seconds=time.perf_counter()-tick,Optimize=0,native_starts=0,
        managed_C_full_checkout_failed_disk_and_auto_cleaned=True,sparse_E_checkout=True,
        no_applicable_AGENTS_found=True,base_PR=177,base_head=BASE,
        original_workspace_branch='codex/round105-inventory-route-decomposition',
        original_workspace_tracked_changes=['results/gf_compact_bc_round/handling_convention_test/handling_convention.json',
            'results/gf_compact_bc_timeprofile_round/progress_traces/exact_moderate_seed3301_1200s_static300.progress.csv',
            'results/gf_compact_bc_timeprofile_round/raw/exact_moderate_seed3301_1200s_static300.json'],
        original_user_files_modified=False,PE_SHA=sha(PE),DLL_SHA=sha(DLL),production_source_count=206,
        projection_dependency=dict(version='pyproj3.7.2',certifi_version='2026.7.22',directory=str(DATA_DEPS),solver_environment_changed=False)))
    print(json.dumps(dict(frozen=True,recipe_SHA=sha(OUT/'source_recipe.json'),native_starts=0)))

def fetch_endpoint(name,url,kind):
    raise RuntimeError('Round117 supersedes raw webpage acquisition. Use publication_security.record_research_response; this historical campaign must not acquire or generate new inputs.')
    folder=OUT/'source/requests'/name;folder.mkdir(parents=True,exist_ok=False)
    hosts=set(read(OUT/'source_recipe.json')['allow_hosts'])
    assert urllib.parse.urlsplit(url).scheme=='https' and urllib.parse.urlsplit(url).hostname in hosts
    for attempt in range(1,4):
        t=time.perf_counter();started=utc();raw=b'';status=None;final=url;headers={};error=None;value=None
        try:
            request=urllib.request.Request(url,headers={'User-Agent':'Round116 non-commercial reproducibility study','Accept':'application/json' if kind!='html' else 'text/html'})
            with urllib.request.urlopen(request,timeout=45) as response:
                status=response.status;final=response.geturl();headers=dict(response.headers.items());raw=response.read()
            assert urllib.parse.urlsplit(final).hostname in hosts,'nonofficial redirect'
            if kind=='html':
                value=raw.decode('utf-8');assert len(raw)>1000 and '<html' in value.lower()
            else:
                value=json.loads(raw.decode('utf-8'))
                assert isinstance(value,dict) and isinstance(value.get('data'),dict)
                if kind=='stations':assert isinstance(value['data'].get('stations'),list) and all(isinstance(x,dict) for x in value['data']['stations'])
                if kind=='discovery':assert isinstance(value['data'].get('en',{}).get('feeds'),list)
                if kind=='system':assert isinstance(value['data'].get('system_id'),str)
            valid=True
        except urllib.error.HTTPError as exc:
            status=exc.code;final=exc.geturl();headers=dict(exc.headers.items());raw=exc.read();error=repr(exc);valid=False
        except Exception as exc:error=repr(exc);valid=False
        payload=folder/f'{attempt:02d}.response';payload.write_bytes(raw)
        write(folder/f'{attempt:02d}.json',dict(attempt=attempt,request_url=url,final_url=final,started_UTC=started,ended_UTC=utc(),
            seconds=time.perf_counter()-t,status=status,response_bytes=len(raw),response_SHA256=sha(payload),headers=headers,
            structure_valid=valid,error=error,kind=kind,recipe_SHA=sha(OUT/'source_recipe.json'),
            gbfs_version=value.get('version') if valid and isinstance(value,dict) else None,
            last_updated=value.get('last_updated') if valid and isinstance(value,dict) else None))
        if valid:return value,payload,read(folder/f'{attempt:02d}.json')
        if status in (401,403):break
    raise RuntimeError('DATA_OR_LICENSE_BLOCKED: no permitted complete valid '+name+' response')

def acquire():
    tick=time.perf_counter();recipe=read(OUT/'source_recipe.json');assert recipe['thin_adapter_SHA']==sha(__file__)
    assert not (OUT/'source/snapshot.json').exists()
    entry,ep,er=fetch_endpoint('system_data',ENTRY,'html')
    license_html,lp,lr=fetch_endpoint('license',LICENSE,'html')
    assert 'source material' in license_html and 'non-commercial purposes' in license_html and 'stand-alone dataset' in license_html,'DATA_OR_LICENSE_BLOCKED: license scope changed'
    assert 'gbfs.capitalbikeshare.com' in entry and 'General Bikeshare' in entry,'DATA_OR_LICENSE_BLOCKED: official discovery relationship not established'
    discovery,dp,dr=fetch_endpoint('discovery',DISCOVERY,'discovery')
    feeds=discovery['data']['en']['feeds'];su=[f['url'] for f in feeds if f.get('name')=='station_information'];iu=[f['url'] for f in feeds if f.get('name')=='system_information']
    assert len(su)==len(iu)==1
    assert urllib.parse.urlsplit(su[0]).netloc==urllib.parse.urlsplit(iu[0]).netloc and su[0].rsplit('/',1)[0]==iu[0].rsplit('/',1)[0]
    system,ip,ir=fetch_endpoint('system_information',iu[0],'system')
    assert 'capital bikeshare' in system['data'].get('name','').lower(),'DATA_OR_LICENSE_BLOCKED: wrong system'
    station,sp,sr=fetch_endpoint('station_information',su[0],'stations')
    assert station.get('version')==system.get('version')==discovery.get('version'),'DATA_BLOCKED: GBFS identity mismatch'
    write(OUT/'source/snapshot.json',dict(recipe_SHA=sha(OUT/'source_recipe.json'),UTC=utc(),station_response_path=sp.relative_to(ROOT).as_posix(),
        station_response_SHA=sha(sp),stations_original_count=len(station['data']['stations']),station_request=sr,
        discovery_path=dp.relative_to(ROOT).as_posix(),discovery_SHA=sha(dp),discovery_request=dr,
        system_path=ip.relative_to(ROOT).as_posix(),system_SHA=sha(ip),system_request=ir,system_identity=system['data'],
        license_path=lp.relative_to(ROOT).as_posix(),license_SHA=sha(lp),license_request=lr,
        entry_path=ep.relative_to(ROOT).as_posix(),entry_SHA=sha(ep),entry_request=er,
        gbfs_version=station.get('version'),last_updated=station.get('last_updated'),unique_first_valid_snapshot=True,
        copyright_and_license_URL=LICENSE,noncommercial_study_source_appendix_only=True,Optimize=0,native_starts=0,
        acquisition_seconds=time.perf_counter()-tick))
    print(json.dumps(dict(snapshot_SHA=sha(sp),original_count=len(station['data']['stations']),Optimize=0)))

@dataclasses.dataclass(frozen=True)
class SourceStation:
    source_row_index:int
    station_id:str
    capacity:int
    x:float
    y:float
    latitude:float
    longitude:float
    original_row_indices:tuple

def finite_number(x):return isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x)
def table():
    snapshot=read(OUT/'source/snapshot.json');raw=ROOT/snapshot['station_response_path'];assert sha(raw)==snapshot['station_response_SHA']
    rows=read(raw)['data']['stations'];groups={};decisions=[]
    for idx,r in enumerate(rows):
        sid=r.get('station_id');c=r.get('capacity');lat=r.get('lat');lon=r.get('lon');reasons=[]
        if not isinstance(sid,str) or not sid:reasons.append('missing_or_invalid_station_id')
        if not finite_number(c) or c<=0 or c>=100 or int(c)!=c:reasons.append('capacity_not_strict_positive_integer_below100')
        if not finite_number(lat) or not -90<=lat<=90 or not finite_number(lon) or not -180<=lon<=180:reasons.append('invalid_WGS84')
        if r.get('is_virtual_station') is True:reasons.append('explicit_virtual_station')
        if isinstance(sid,str) and sid:
            physical=(c,lat,lon,r.get('is_virtual_station') is True)
            if sid in groups and groups[sid]['physical']!=physical:
                write(OUT/'source/duplicate_conflict.json',dict(station_id=sid,prior_rows=groups[sid]['rows'],new_row=idx,prior_physical=groups[sid]['physical'],new_physical=physical))
                raise RuntimeError('DATA_BLOCKED: conflicting duplicate station ID')
            groups.setdefault(sid,dict(physical=physical,rows=[],valid=not reasons,original=r))['rows'].append(idx)
        decisions.append(dict(original_row_index=idx,station_id=sid,qualified_physical_row=not reasons,exclusion_reasons=reasons,original_row=r))
    write(OUT/'source/row_decisions.json',decisions)
    candidates=sorted((sid,g) for sid,g in groups.items() if g['valid'])
    candidates.sort(key=lambda t:t[0].encode('utf-8'));assert len(candidates)>=200,'DATA_BLOCKED: fewer than200 eligible static stations'
    tr,info=projection();assert info==read(OUT/'projection_contract.json');a=info['area_of_use'];stations=[];report=[]
    for j,(sid,g) in enumerate(candidates):
        c,lat,lon,_=g['physical'];assert a['west']<=lon<=a['east'] and a['south']<=lat<=a['north'],'DATA_BLOCKED: qualified coordinates outside UTM18N area'
        x,y=tr.transform(lon,lat,errcheck=True)
        assert math.isfinite(x) and math.isfinite(y) and 100000<x<900000 and 0<=y<9500000
        lon2,lat2=tr.transform(x,y,direction='INVERSE',errcheck=True);assert abs(lon-lon2)<1e-10 and abs(lat-lat2)<1e-10
        stations.append(SourceStation(j,sid,int(c),round(x,3),round(y,3),lat,lon,tuple(g['rows'])))
        report.append(dict(source_row_index=j,station_id=sid,capacity=int(c),latitude=lat,longitude=lon,
            utm18n_easting_unrounded_m=x,utm18n_northing_unrounded_m=y,utm18n_easting_m=f'{round(x,3):.3f}',
            utm18n_northing_m=f'{round(y,3):.3f}',original_row_indices=json.dumps(g['rows']),
            inverse_longitude=lon2,inverse_latitude=lat2,raw_source_SHA=snapshot['station_response_SHA']))
    csvfile(OUT/'source/source_station_table.csv',report)
    write(OUT/'source/source_qualification.json',dict(eligible_count=len(stations),original_count=len(rows),unique_IDs=len(groups),
        excluded_original_rows=sum(not d['qualified_physical_row'] for d in decisions),same_physical_duplicate_rows=sum(len(g['rows'])-1 for g in groups.values()),
        sorted_UTF8=True,projection_passed=True,source_table_SHA=sha(OUT/'source/source_station_table.csv'),
        projection_contract_SHA=sha(OUT/'projection_contract.json'),raw_source_SHA=snapshot['station_response_SHA'],Optimize=0))
    return stations

def configure(source_sha):
    family=VERSION+'|source_sha256='+source_sha;old.FAMILY=family;inherited.VERSION=family;inherited.SOURCE_SHA=source_sha
    return family
def select(stations,v,g,r):
    s=old.build_selection(stations,v,g,r)
    s['selection_id']=f'cabi_V{v:02d}_{g}_r{r}'
    return s
def landscape(selection,regime,stations):
    value=inherited.landscape(selection,regime,stations)
    inherited.assert_equivalent(selection,regime,stations,value)
    value['schema']='cabi-station-landscape-v1';value['source_hashes']={'official_station_response_SHA256':inherited.SOURCE_SHA}
    return value
def synthetic_equivalence():
    configure('0'*64)
    ss=[SourceStation(i,f'ID{i:03d}',10+i%25,500000.+13*i+3*(i%5),4300000.+7*i*i,38.,-75.,(i,)) for i in range(240)]
    prior=[old.SourceStation(s.source_row_index,s.source_row_index+1,s.capacity,s.x,s.y,-1,None,'artificial',s.station_id,'',s.latitude,s.longitude) for s in ss]
    checks=[]
    for v in [20,50,100]:
        for g,r in [('compact',1),('regional',2)]:
            s=select(ss,v,g,r);original=old.build_selection(prior,v,g,r);original['selection_id']=s['selection_id'];assert s==original
            for stock in ['shortage','balanced','surplus']:
                value=landscape(s,stock,ss);a=inherited.landscape(original,stock,prior)
                a['schema']=value['schema'];a['source_hashes']=value['source_hashes'];assert a==value
                checks.append(dict(V=v,geometry=g,replicate=r,inventory=stock,equal=True))
    write(OUT/'generation_equivalence.json',dict(artificial_source_rows=240,checks=checks,
        native_starts=0,Optimize=0,no_original_private_source_opened=True,source_adapter_changes_only=True))

def generate():
    tick=time.perf_counter();recipe=read(OUT/'source_recipe.json');assert recipe['thin_adapter_SHA']==sha(__file__)
    assert not REFERENCE.exists();synthetic_equivalence();stations=table();snapshot=read(OUT/'source/snapshot.json')
    family=configure(snapshot['station_response_SHA']);REFERENCE.mkdir(parents=True,exist_ok=False);roles=copy.deepcopy(ROLES);stats=[];subsets={}
    tree=subprocess.check_output(['git','ls-tree','-r','-z',BASE],cwd=ROOT).split(b'\0');historical_text=[];hashes={}
    # A single Git object reader hashes every historical tracked .txt byte stream.
    # This is only duplicate-input screening, not old solver/model re-auditing.
    for row in tree:
        if row:
            meta,path=row.split(b'\t',1)
            if path.endswith(b'.txt'):historical_text.append((meta.split()[2].decode(),path.decode('utf-8')))
    proc=subprocess.Popen(['git','cat-file','--batch'],cwd=ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
    for oid,path in historical_text:
        proc.stdin.write((oid+'\n').encode());proc.stdin.flush()
        header=proc.stdout.readline().split();assert header[1]==b'blob'
        remaining=int(header[2]);digest=hashlib.sha256()
        while remaining:
            chunk=proc.stdout.read(min(1024*1024,remaining));assert chunk;digest.update(chunk);remaining-=len(chunk)
        assert proc.stdout.read(1)==b'\n';hashes.setdefault(digest.hexdigest(),[]).append(path)
    proc.stdin.close();assert proc.wait()==0
    write(OUT/'historical_input_hash_index.json',dict(base=BASE,tracked_txt_streams=len(historical_text),SHA_to_paths=hashes,Optimize=0))
    for role in roles:
        s=select(stations,role['V'],role['geometry'],role['replicate']);s['schema']='cabi-geographic-selection-v1'
        obj=landscape(s,role['inventory'],stations);lines=old.instance_text(obj,role['M'],role['Q_vector'][0]).splitlines()
        lines[0]=f"{role['V']} {role['M']} {json.dumps(role['Q_vector'])}"
        path=REFERENCE/(role['id']+'.txt');textfile(path,'\n'.join(lines))
        assert sha(path) not in hashes,('DATA_BLOCKED: historical input byte duplicate',hashes.get(sha(path)))
        parsed=old.parse_instance_mirror(path)
        assert parsed['V']==role['V'] and parsed['M']==role['M'] and parsed['Q']==role['Q_vector']
        assert len(parsed['points'])==role['V']+1 and len(s['selected_source_station_row_indices'])==len(set(s['selected_source_station_row_indices']))==role['V']
        assert all(0<=b<=c and 0<d<=c for b,c,d in zip(obj['initial'],obj['capacities'],obj['target']))
        assert all(w>0 for w in obj['weights']) and max(obj['weights'])==1 and all(q>0 for q in role['Q_vector'])
        assert obj['depot']['coordinate_utm18n_meters']==[round(statistics.fmean(p[0] for p in parsed['points'][1:]),3),round(statistics.fmean(p[1] for p in parsed['points'][1:]),3)]
        write(REFERENCE/(role['id']+'_selection.json'),s);write(REFERENCE/(role['id']+'_landscape.json'),obj);write(REFERENCE/(role['id']+'_parsed.json'),parsed)
        mapping=[dict(local_station_index=j,source_row_index=i,station_id=stations[i].station_id,original_row_indices=stations[i].original_row_indices,
            capacity=stations[i].capacity,longitude=stations[i].longitude,latitude=stations[i].latitude,x=stations[i].x,y=stations[i].y,
            source_response_SHA=snapshot['station_response_SHA']) for j,i in enumerate(s['selected_source_station_row_indices'],1)]
        write(REFERENCE/(role['id']+'_source_mapping.json'),mapping);subsets[role['id']]=set(s['selected_source_station_row_indices'])
        role.update(input_path=path.relative_to(ROOT).as_posix(),input_sha256=sha(path),input_bytes=path.stat().st_size,
            instance_path=path.relative_to(ROOT).as_posix(),selection_path=(REFERENCE/(role['id']+'_selection.json')).relative_to(ROOT).as_posix(),
            landscape_path=(REFERENCE/(role['id']+'_landscape.json')).relative_to(ROOT).as_posix(),source_response_SHA=snapshot['station_response_SHA'],
            source_recipe_SHA=sha(OUT/'source_recipe.json'),role_identity='unmeasured_at_initial_freeze',total_initial=sum(obj['initial']),total_target=sum(obj['target']))
        stats.append(dict(id=role['id'],V=role['V'],M=role['M'],T_seconds=role['T_seconds'],cap_seconds=role['cap_seconds'],
            W=sum(obj['weights']),lambda_W=.15*sum(obj['weights']),B=sum(obj['initial']),sumD=sum(obj['target']),sumQ=sum(role['Q_vector']),
            B_lo=max(0,sum(obj['initial'])-sum(role['Q_vector'])),target_stock_necessary_feasible=max(0,sum(obj['initial'])-sum(role['Q_vector']))<=sum(obj['target'])<=sum(obj['initial']),**obj['statistics']))
    hpath=ROOT/'reference/round100_confirmation/H100.txt';assert sha(hpath)=='04cfc75a36585eddea81693964eed9ef4c207e62b687e955e63fd4fb00d7bf71'
    h=dict(id='H100',V=20,M=2,Q_vector=[13,21],T_seconds=5100,cap_seconds=120,method_order=['P-GRB','P-S','ENS-C','M-B'],
        input_path=hpath.relative_to(ROOT).as_posix(),instance_path=hpath.relative_to(ROOT).as_posix(),input_sha256=sha(hpath),
        pickup_seconds=60,drop_seconds=60,**{'lambda':.15},gurobi_seed=0,panel_kind='qualification')
    write(OUT/'input_manifest.json',dict(roles=roles,qualification_roles=[h],family=family,recipe_SHA=sha(OUT/'source_recipe.json'),
        raw_station_response_SHA=snapshot['station_response_SHA'],source_table_SHA=sha(OUT/'source/source_station_table.csv'),generated_once=True,
        historical_input_duplicates=False,zero_Optimize=True,panel_first_production_result_seen=False))
    write(OUT/'structure_statistics.json',stats)
    write(OUT/'source_subset_overlap.json',[dict(first=a,second=b,shared_stations=len(subsets[a]&subsets[b]),shared_source_indices=sorted(subsets[a]&subsets[b])) for a,b in itertools.combinations(subsets,2)])
    write(OUT/'generation_receipt.json',dict(UTC=utc(),seconds=time.perf_counter()-tick,inputs=6,native_starts=0,Optimize=0,
        unchanged_math_equivalence=True,historical_input_hashes_checked=len(historical_text),thin_adapter_SHA=sha(__file__),
        input_manifest_SHA=sha(OUT/'input_manifest.json'),no_result_screening=True))
    print(json.dumps(dict(generated_once=6,eligible_source=len(stations),Optimize=0)))

if __name__=='__main__':
    raise SystemExit('Historical Round116 data generation/acquisition is closed by AUTHOR_SCOPE_V_LE_60. Use existing safe data and Round117 offline validation; no new inputs are authorized.')
    try:{'freeze':freeze,'acquire':acquire,'generate':generate}[sys.argv[1]]()
    except BaseException as exc:
        if OUT.exists():
            p=OUT/'data_failure_'+sys.argv[1]+'.json'
            if not p.exists():write(p,dict(UTC=utc(),operation=sys.argv[1],error=repr(exc),Optimize=0,native_starts=0))
        raise
