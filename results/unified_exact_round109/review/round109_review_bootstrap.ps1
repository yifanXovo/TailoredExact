$ErrorActionPreference = 'Stop'
$TaskRoot = 'E:/codes/ExactEBRP-round109'
$ReviewRoot = Join-Path $TaskRoot 'results/unified_exact_round109/review'
New-Item -ItemType Directory -Force -Path $ReviewRoot | Out-Null
$OldParser = Join-Path $TaskRoot 'results/unified_exact_round108/review/current_qualification_audit01.py'
$OldAudit = Join-Path $TaskRoot 'results/unified_exact_round108/review/campaign_raw_audit01.py'
$ParserSource = [IO.File]::ReadAllText($OldParser)
$ParserBody = $ParserSource.Substring($ParserSource.IndexOf('def input_file('), $ParserSource.IndexOf('def norm_native(') - $ParserSource.IndexOf('def input_file('))
$ParserPrefix = @'
"""R109 independent stdlib input, physical fleet and strict LP parser.

The mathematical parser/functions below are inherited byte-for-byte from the
audited R108 independent reviewer, rather than the campaign reconstruction.
The caller replaces IO/require functions with explicit-root guarded versions.
No import, call or operation creates a native environment or solves a model.
"""
from pathlib import Path
import ast, csv, hashlib, json, math, re
def data(path):return Path(path).read_bytes()
def txt(path):return data(path).decode('utf-8-sig')
def require(condition,message):
    if not condition:raise AssertionError(message)
def near(a,b,tol=1e-7):return math.isfinite(a) and math.isfinite(b) and abs(a-b)<=tol

'@
[IO.File]::WriteAllText((Join-Path $ReviewRoot 'round109_independent_parser.py'), $ParserPrefix + "`n" + $ParserBody, [Text.UTF8Encoding]::new($false))
$AuditSource = [IO.File]::ReadAllText($OldAudit)
$AuditBody = $AuditSource.Substring($AuditSource.IndexOf('def full_physics('), $AuditSource.IndexOf('def own_pair(') - $AuditSource.IndexOf('def full_physics('))
$AuditBody = $AuditBody.Replace("dict(read_return_code=0,**base['SETTINGS'])", "dict(read_return_code=0,**SETTINGS,Seed=p['gurobi_seed'])")
$AuditBody = $AuditBody.Replace("for (callid,c),r in zip(calls.items(),ledger or [", "for (callid,c),r in zip(((i,c) for i,c in calls.items() if i in returns),ledger if arm!='P-GRB' else [")
$AuditBody = $AuditBody.Replace("ref=d.parent.parent/'reference'/p['id']/'original.lp'", "ref=reference_path(p)")
$AuditBody = $AuditBody.Replace("id=p['id'],arm=arm,U=ph['U']", "id=p['id'],seed=p['gurobi_seed'],panel_kind=launch.get('panel_kind',launch.get('stage')),arm=arm,U=ph['U']")
$AuditBody = $AuditBody.Replace("p['id']+'_'+arm.replace('-','_')", "p['id']+'_seed'+str(p['gurobi_seed'])+'_'+arm.replace('-','_')")
$AuditBody = $AuditBody.Replace("    else:`n        initial=obj(d/'external/initial_witness.json');initialph=full_physics(q,initial['routes'],p)", "    elif ph['U']<=ZERO and not calls:`n        require(p['lambda']>=0 and all(x>=0 for x in q['weights'][1:]),'zero own physical U and globally nonnegative original objective')`n        L=0.;cert=True;cover=dict(independent_nonnegative_objective_floor=True,whole_improving_domain_covered=True,all_relevant_closed=True,open_relevant_leaves=0)`n    else:`n        initial=obj(d/'external/initial_witness.json');initialph=full_physics(q,initial['routes'],p)")
# The checked-in inherited file may use CRLF; handle that exact source form too.
$AuditBody = $AuditBody.Replace("    else:`r`n        initial=obj(d/'external/initial_witness.json');initialph=full_physics(q,initial['routes'],p)", "    elif ph['U']<=ZERO and not calls:`n        require(p['lambda']>=0 and all(x>=0 for x in q['weights'][1:]),'zero own physical U and globally nonnegative original objective')`n        L=0.;cert=True;cover=dict(independent_nonnegative_objective_floor=True,whole_improving_domain_covered=True,all_relevant_closed=True,open_relevant_leaves=0)`n    else:`n        initial=obj(d/'external/initial_witness.json');initialph=full_physics(q,initial['routes'],p)")
[IO.File]::WriteAllText((Join-Path $ReviewRoot 'round109_independent_kernel.py'), '"""Inherited R108 independently computed physics/model/Start/coverage kernel, adapted for per-arm Seed, zero objective and R109 paths. No main; caller injects explicit-root IO."""' + "`n" + $AuditBody, [Text.UTF8Encoding]::new($false))
$Bindings = [ordered]@{
    source_commit = 'd11c94d81e6a2c5dcd64dad8c54b390f3cb4a027'
    inherited_parser_path = 'results/unified_exact_round108/review/current_qualification_audit01.py'
    inherited_parser_SHA = (Get-FileHash -LiteralPath $OldParser -Algorithm SHA256).Hash.ToLowerInvariant()
    inherited_raw_audit_path = 'results/unified_exact_round108/review/campaign_raw_audit01.py'
    inherited_raw_audit_SHA = (Get-FileHash -LiteralPath $OldAudit -Algorithm SHA256).Hash.ToLowerInvariant()
    parser_SHA = (Get-FileHash -LiteralPath (Join-Path $ReviewRoot 'round109_independent_parser.py') -Algorithm SHA256).Hash.ToLowerInvariant()
    kernel_SHA = (Get-FileHash -LiteralPath (Join-Path $ReviewRoot 'round109_independent_kernel.py') -Algorithm SHA256).Hash.ToLowerInvariant()
    changes = @('Remove historical fixed qualification, bridge and early cancellation', 'Native per-call Seed comes from frozen arm panel', 'Role plus Seed output keys avoid repeated-role collisions', 'Reference model path supplied by explicit R109 adapter', 'Returned native calls checked separately from actual no-Optimize skips', 'Zero own physical objective independently proves nonnegative floor without saved leaf')
    Optimize = 0
    native_environment = 0
    production_edits = 0
}
[IO.File]::WriteAllText((Join-Path $ReviewRoot 'reviewer_inheritance.json'), ($Bindings | ConvertTo-Json -Depth 8) + "`n", [Text.UTF8Encoding]::new($false))
