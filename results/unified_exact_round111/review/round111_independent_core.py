"""Root-only six-arm independent adapter over the fixed signed R109 kernel.

No production helper is imported. The only scientific changes to the inherited
kernel are removal of its obsolete historical tuple dispatch and deferment of
the cap decision until the actual new complete-clock receipts are retained.
An over-cap record remains invalid; its physical mathematics may still be read.
"""
from pathlib import Path
from collections import Counter
from fractions import Fraction
import ast
import csv
import hashlib
import json
import math
import re
import runpy

ROUND = 'results/unified_exact_round111'
AUTHORITY = ROUND+'/review/inherited_main03/authority'
PE = 'c0384284aefd5aa2acc5d885ef37b0cfad6f93d083a5feb9ee693c41a786b411'
DLL = '9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88'
TOL = 1e-7
ZERO = 1e-12
SETTINGS = dict(Threads=1,Presolve=-1,MIPGap=0,MIPGapAbs=0,
                FeasibilityTol=1e-6,IntFeasTol=1e-5,OptimalityTol=1e-6)
TRUSTED = {
    'round109_independent_parser.py':'ecfb894faa24bc8c5889a0466051f5cc709cfa2969c3ca6529ab826c237acb3a',
    'round109_independent_kernel.py':'3bb8f84f4949ca59cc8720a4acd04d568a41f9eac1382f26138066d5c49f6287',
    'round109_independent_decision.py':'b518597b8ccaf100607e4e6738688be9032957039396e5bb23a3f0ebe817a926',
    'round109_independent_seed_scope.py':'847092a0354fb69ad6151dbe45e9d4c175ea39687c597a1fab8bae6ed5adf8b9',
}


class Audit:
    def __init__(self,root,destination):
        self.root = Path(root).resolve()
        self.out = self.root/ROUND
        self.destination = Path(destination).resolve()
        assert self.destination.is_relative_to(self.out/'review')
        self.reads,self.cache,self.milestones,self.scope_calls = {},{},[],{}
        self.checks = 0
        self._load()

    def require(self,condition,message):
        self.checks += 1
        if not condition:
            raise AssertionError(message)

    def data(self,path):
        path = Path(path).resolve()
        self.require(path.is_relative_to(self.root),'independent read remains in explicit root')
        raw = path.read_bytes()
        self.reads[path.relative_to(self.root).as_posix()] = hashlib.sha256(raw).hexdigest()
        return raw

    def sha(self,path):
        return hashlib.sha256(self.data(path)).hexdigest()

    def txt(self,path):
        return self.data(path).decode('utf-8-sig')

    def obj(self,path):
        return json.loads(self.txt(path))

    def rows(self,path):
        return list(csv.DictReader(self.txt(path).splitlines()))

    def local(self,value):
        normalized = str(value).replace('\\','/')
        for marker in ('results/','reference/','src/','include/','scripts/','tests/','build/'):
            if marker in normalized:
                path = (self.root/normalized[normalized.index(marker):]).resolve()
                self.require(path.is_relative_to(self.root),'retained path normalizes to explicit root')
                return path
        path = Path(normalized)
        self.require(not path.is_absolute(),'no external retained path fallback')
        path = (self.root/path).resolve()
        self.require(path.is_relative_to(self.root),'relative explicit-root retained path')
        return path

    def save(self,path,value):
        path = Path(path).resolve()
        self.require(path.is_relative_to(self.destination),'exclusive independent output')
        with path.open('x',encoding='utf-8',newline='\n') as stream:
            json.dump(value,stream,indent=2,ensure_ascii=False,allow_nan=False)
            stream.write('\n')

    @staticmethod
    def near(a,b,tol=TOL):
        return math.isfinite(a) and math.isfinite(b) and abs(a-b) <= tol

    def model(self,path):
        digest = self.sha(path)
        if digest not in self.cache:
            self.cache[digest] = self.functions['lp'](path)
            self.require(self.sha(path) == digest,'saved bytes remain immutable during independent parse')
        return self.cache[digest]

    def reference_path(self,p):
        path = p.get('reference_path')
        if path:
            return self.local(path)
        # These are explicit finite inherited reference dependencies. The caller
        # carries only the four used roles; there is no original-root fallback.
        return self.root/'results/unified_exact_round110/qualification/reference'/p['id']/'original.lp'

    def reference_build(self,p):
        path = p.get('reference_build_path')
        if path:
            return self.obj(self.local(path))
        return self.obj(self.root/'results/unified_exact_round110/qualification/reference'/p['id']/'build.json')

    def scope_qualified(self,c):
        proof = self.scope_calls.get(c['call'])
        if proof is None:
            return c['native_preconditions'] == 1
        self.require(c['native_preconditions'] == 0 and proof['model_SHA'] == c['model_sha256'] and
                     proof['facts']['actual_settings'] == c['settings'],'current computed scope retains raw false flag')
        return proof['computed_native_scope_qualified']

    def set_scope(self,proof):
        self.scope_calls = {p['call']:p for p in proof['proofs']} if proof else {}

    def checkpoints(self,arm,launch,timeline):
        return []

    def seed_scope(self,launch):
        return self.scope_functions['audit'](self.root,launch)

    def _load(self):
        paths = {n:self.root/AUTHORITY/n for n in TRUSTED}
        for name,path in paths.items():
            self.require(self.sha(path) == TRUSTED[name],'fixed previously signed independent source '+name)
        parser = runpy.run_path(str(paths['round109_independent_parser.py']))
        for name in ('input_file','physical','terms','lp'):
            parser[name].__globals__.update(data=self.data,txt=self.txt,require=self.require,near=self.near)
        self.decision = runpy.run_path(str(paths['round109_independent_decision.py']))
        namespace = dict(ROOT=self.root,OUT=self.out,DEST=self.destination,Counter=Counter,re=re,math=math,hashlib=hashlib,
                         json=json,Fraction=Fraction,TOL=TOL,ZERO=ZERO,SETTINGS=SETTINGS,data=self.data,txt=self.txt,
                         obj=self.obj,sha=self.sha,rows=self.rows,save=self.save,require=self.require,near=self.near,
                         under_root=self.local,model=self.model,reference_path=self.reference_path,
                         production_pe_sha=lambda:PE,native_dll_sha=lambda:DLL,native_scope_qualified=self.scope_qualified,
                         set_qualified_scope=self.set_scope,independent_seed_scope=self.seed_scope,
                         independent_numerical_recovery=lambda launch,formal:None,independent_checkpoints=self.checkpoints,
                         milestones=self.milestones)
        namespace.update({name:parser[name] for name in ('input_file','physical','lp')})
        tree = ast.parse(self.txt(paths['round109_independent_kernel.py']))
        altered = 0
        for function in tree.body:
            if isinstance(function,ast.FunctionDef) and function.name == 'audit_arm':
                self.require(isinstance(function.body[0],ast.If) and 'independent_main06_arm' in ast.unparse(function.body[0]),
                             'exact obsolete historical tuple dispatch recognized')
                function.body = function.body[1:]
                for statement in function.body:
                    if (isinstance(statement,ast.Expr) and isinstance(statement.value,ast.Call) and
                        isinstance(statement.value.func,ast.Name) and statement.value.func.id == 'require' and
                        len(statement.value.args) == 2 and 'complete arm within original cap' in ast.unparse(statement.value.args[1])):
                        self.require(ast.unparse(statement.value.args[0]) == "0 <= offset + 1e-09 and complete <= launch['cap_seconds']",
                                     'exact original complete-clock predicate recognized')
                        statement.value.args[0] = statement.value.args[0].values[0]
                        statement.value.args[1] = ast.Constant('retain exact complete clock before strict final adjudication')
                        altered += 1
        self.require(altered == 1,'only single early cap abort deferred; no scientific predicate removed')
        ast.fix_missing_locations(tree)
        exec(compile(tree,str(paths['round109_independent_kernel.py'])+'::R111', 'exec'),namespace)
        self.functions = namespace
        scope = runpy.run_path(str(paths['round109_independent_seed_scope.py']))
        scope['audit'].__globals__.update(obj=self.obj,txt=self.txt,sha=self.sha,rows=self.rows,require=self.require,
                                        reference_build=self.reference_build)
        tree = ast.parse(self.txt(paths['round109_independent_seed_scope.py']))
        function = next(v for v in tree.body if isinstance(v,ast.FunctionDef) and v.name == 'audit')
        transformer = ScopePaths(self,paths)
        function = transformer.visit(function)
        self.require(transformer.build_replacements == 1,'only original reference build source redirected to explicit inherited dependency')
        ast.fix_missing_locations(function)
        exec(compile(ast.Module(body=[function],type_ignores=[]),str(paths['round109_independent_seed_scope.py'])+'::R111', 'exec'),scope['audit'].__globals__)
        self.scope_functions = scope['audit'].__globals__

    def arm(self,launch,identity):
        self.cache.clear()
        self.scope_calls.clear()
        try:
            result,models,q = self.functions['audit_arm'](launch,identity,True)
            directory = self.local(launch['destination'])
            native,audit,whole = [self.obj(directory/name) for name in
                                  ('native_end_receipt.json','postexit_audit_receipt.json','whole_arm_receipt.json')]
            self.require(native['completion_SHA'] == self.sha(directory/'completion.json') and
                         native['observations_SHA'] == self.sha(directory/'observations.json') and
                         audit['audit_SHA'] == whole['audit_SHA'] == self.sha(directory/'audit.json') and audit['audit_passed'],
                         'new native/audit/whole receipts bind actual raw return and necessary audit')
            n,a,w = native['complete_seconds_until_native_end'],audit['complete_seconds_until_audit_end'],whole['complete_seconds']
            self.require(0 < n <= a <= w == result['complete_seconds'],'all actual complete clocks ordered and untrimmed')
            valid = w <= launch['cap_seconds']
            result.update(number=launch['number'],cap_seconds=launch['cap_seconds'],formal_protocol_qualified=valid,
                          full_clock_within_frozen_cap=valid,formal_performance=valid,full_clock_cap_excess_seconds=max(0.,w-launch['cap_seconds']),
                          native_end_seconds=n,required_audit_end_seconds=a,whole_seconds=w,necessary_postaudit_seconds=a-n,
                          original_native_within_cap=result['normal_completion']['within_cap'])
            if not valid:
                result['formal_protocol_failure'] = 'CURRENT_COMPLETE_CLOCK_EXCEEDS_FROZEN_CAP'
            return result,models,q
        finally:
            self.cache.clear()
            self.scope_calls.clear()


class ScopePaths(ast.NodeTransformer):
    def __init__(self,a,paths):
        self.a,self.paths = a,paths
        self.build_replacements = 0

    def visit_Constant(self,node):
        if isinstance(node.value,str):
            if node.value == 'results/unified_exact_round109':
                node.value = ROUND
            elif node.value == 'candidate_contract_freeze.json':
                node.value = 'production_identity.json'
            elif node.value in ('round109_independent_parser.py','round109_independent_kernel.py'):
                node.value = 'inherited_main03/authority/'+node.value
        return node

    def visit_Call(self,node):
        if (isinstance(node.func,ast.Name) and node.func.id == 'obj' and len(node.args) == 1 and
            ast.unparse(node.args[0]) == "out / 'qualification/reference' / p['id'] / 'build.json'"):
            self.build_replacements += 1
            return ast.copy_location(ast.Call(func=ast.Name(id='reference_build',ctx=ast.Load()),args=[ast.Name(id='p',ctx=ast.Load())],keywords=[]),node)
        return self.generic_visit(node)
