"""Thin R110 adapter over the signed R109 independent arithmetic.

The adapter performs no native/environment/solver operation. All reads are
explicit-root guarded. Historical R109 numerical tuple dispatches are removed
from audit_arm before execution: they have no authority over new R110 calls.
New damaged-call evidence must be independently adjudicated before use.
"""
from pathlib import Path
from collections import Counter
import ast, csv, hashlib, json, math, re, runpy

ROUND = 'results/unified_exact_round110'
OLD_REVIEW = 'results/unified_exact_round109/review'
TOL = 1e-7
ZERO = 1e-12
SETTINGS = dict(Threads=1, Presolve=-1, MIPGap=0, MIPGapAbs=0,
                FeasibilityTol=1e-6, IntFeasTol=1e-5, OptimalityTol=1e-6)
OLD_PE = '4647ee9f146a010ae4bc48f191ec12d4b9113e167b8eeccf0e43a3764e0a8ee0'
DLL_SHA = '9b5fccef82043cc9a0f052d31fa9c12b6d59cec999ad0cc19ca1b68ed6d18a88'
TRUSTED_MODULE_SHA = {
    'round109_independent_parser.py': 'ecfb894faa24bc8c5889a0466051f5cc709cfa2969c3ca6529ab826c237acb3a',
    'round109_independent_kernel.py': '3bb8f84f4949ca59cc8720a4acd04d568a41f9eac1382f26138066d5c49f6287',
    'round109_independent_decision.py': 'b518597b8ccaf100607e4e6738688be9032957039396e5bb23a3f0ebe817a926',
    'round109_independent_seed_scope.py': '847092a0354fb69ad6151dbe45e9d4c175ea39687c597a1fab8bae6ed5adf8b9',
}


class Audit:
    def __init__(self, root, destination, pe_sha, dll_sha=DLL_SHA, dll=None):
        self.root = Path(root).resolve()
        self.out = self.root / ROUND
        self.destination = Path(destination).resolve()
        assert self.destination.is_relative_to(self.out / 'review')
        self.pe_sha, self.dll_sha = pe_sha, dll_sha
        self.dll = Path(dll).resolve() if dll else None
        self.reads, self.checks, self.cache, self.milestones = {}, 0, {}, []
        self.scope_calls = {}
        self.module_bindings = {}
        self._load()

    def require(self, condition, message):
        self.checks += 1
        if not condition:
            raise AssertionError(message)

    def data(self, path):
        path = Path(path).resolve()
        self.require(path.is_relative_to(self.root) or path == self.dll,
                     'read remains in supplied evidence root or declared local DLL')
        raw = path.read_bytes()
        self.reads[path.relative_to(self.root).as_posix() if path.is_relative_to(self.root)
                   else str(path)] = hashlib.sha256(raw).hexdigest()
        return raw

    def sha(self, path):
        return hashlib.sha256(self.data(path)).hexdigest()

    def txt(self, path):
        return self.data(path).decode('utf-8-sig')

    def obj(self, path):
        return json.loads(self.txt(path))

    def rows(self, path):
        return list(csv.DictReader(self.txt(path).splitlines()))

    def save(self, path, value):
        path = Path(path).resolve()
        self.require(path.is_relative_to(self.destination), 'exclusive reviewer output')
        with path.open('x', encoding='utf-8', newline='\n') as f:
            json.dump(value, f, indent=2, ensure_ascii=False, allow_nan=False)
            f.write('\n')

    def local(self, value):
        normalized = str(value).replace('\\', '/')
        for marker in ('results/', 'reference/', 'build/', 'scripts/', 'src/', 'include/', 'tests/'):
            if marker in normalized:
                path = (self.root / normalized[normalized.index(marker):]).resolve()
                self.require(path.is_relative_to(self.root), 'normalized retained path stays in root')
                return path
        path = Path(normalized)
        self.require(not path.is_absolute(), 'unsupported retained external path')
        path = (self.root / path).resolve()
        self.require(path.is_relative_to(self.root), 'relative path stays in root')
        return path

    @staticmethod
    def near(a, b, tol=TOL):
        return math.isfinite(a) and math.isfinite(b) and abs(a-b) <= tol

    def model(self, path):
        digest = self.sha(path)
        if digest not in self.cache:
            self.cache[digest] = self.functions['lp'](path)
        return self.cache[digest]

    def reference_path(self, panel):
        # The native reference is inherited, never generated from a Python mirror.
        references = self.obj(self.out / 'campaign/identity.json')['references']
        value = references[panel['id']]
        for key in ('path', 'model_path', 'canonical_path'):
            if key in value:
                return self.local(value[key])
        own = self.out / 'qualification/reference' / panel['id'] / 'original.lp'
        if own.exists():
            return own
        return self.root / 'results/unified_exact_round109/qualification/reference' / panel['id'] / 'original.lp'

    def _scope_qualified(self, call):
        proof = self.scope_calls.get(call['call'])
        if proof is None:
            return call['native_preconditions'] == 1
        self.require(call['native_preconditions'] == 0 and proof['model_SHA'] == call['model_sha256'],
                     'computed scope preserves original false flag and exact current model')
        return proof['computed_native_scope_qualified'] and proof['facts']['actual_settings'] == call['settings']

    def _set_scope(self, proof):
        self.scope_calls = {p['call']: p for p in proof['proofs']} if proof else {}

    def _seed_scope(self, launch):
        functions = self.seed_functions
        # Historical helper's model/source predicates are reused with R110 root
        # and current contract; its old PE constant is informational only.
        return functions['audit'](self.root, launch)

    def _load(self):
        parser_path = self.root / OLD_REVIEW / 'round109_independent_parser.py'
        kernel_path = self.root / OLD_REVIEW / 'round109_independent_kernel.py'
        decision_path = self.root / OLD_REVIEW / 'round109_independent_decision.py'
        seed_path = self.root / OLD_REVIEW / 'round109_independent_seed_scope.py'
        for path in (parser_path, kernel_path, decision_path, seed_path):
            self.module_bindings[path.relative_to(self.root).as_posix()] = self.sha(path)
            self.require(self.module_bindings[path.relative_to(self.root).as_posix()] == TRUSTED_MODULE_SHA[path.name],
                         'exact latest signed R109 shared kernel '+path.name)
        parser = runpy.run_path(str(parser_path))
        for name in ('input_file', 'physical', 'terms', 'lp'):
            parser[name].__globals__.update(data=self.data, txt=self.txt,
                                            require=self.require, near=self.near)
        self.decision = runpy.run_path(str(decision_path))
        namespace = dict(ROOT=self.root, OUT=self.out, DEST=self.destination,
                         Counter=Counter, re=re, math=math, hashlib=hashlib,
                         json=json, Fraction=__import__('fractions').Fraction,
                         TOL=TOL, ZERO=ZERO, SETTINGS=SETTINGS,
                         data=self.data, txt=self.txt, obj=self.obj, sha=self.sha,
                         rows=self.rows, save=self.save, require=self.require,
                         near=self.near, under_root=self.local, model=self.model,
                         reference_path=self.reference_path,
                         production_pe_sha=lambda: self.pe_sha,
                         native_dll_sha=lambda: self.dll_sha,
                         native_scope_qualified=self._scope_qualified,
                         set_qualified_scope=self._set_scope,
                         independent_seed_scope=self._seed_scope,
                         independent_numerical_recovery=lambda launch, formal: None,
                         independent_checkpoints=self.checkpoints,
                         milestones=self.milestones)
        namespace.update({name: parser[name] for name in ('input_file', 'physical', 'lp')})
        tree = ast.parse(self.txt(kernel_path), filename=str(kernel_path))
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name == 'audit_arm':
                # Delete the historical (17,G50-C2,Seed0,P) dispatch; retaining
                # that tuple would silently import a different campaign proof.
                first = node.body[0]
                self.require(isinstance(first, ast.If) and
                             'independent_main06_arm' in ast.unparse(first),
                             'recognized exact historical dispatch removed')
                node.body = node.body[1:]
        ast.fix_missing_locations(tree)
        exec(compile(tree, str(kernel_path), 'exec'), namespace)
        self.functions = namespace
        self.seed_functions = runpy.run_path(str(seed_path))
        audit_function = self.seed_functions['audit']
        body = ast.parse(self.txt(seed_path), filename=str(seed_path))
        for node in body.body:
            if isinstance(node, ast.FunctionDef) and node.name == 'audit':
                # Only path constants change, not any scientific predicate.
                node = _RoundPath().visit(node)
                ast.fix_missing_locations(node)
                exec(compile(ast.Module(body=[node], type_ignores=[]), str(seed_path), 'exec'),
                     audit_function.__globals__)
        audit_function.__globals__.update(obj=self.obj, txt=self.txt, sha=self.sha,
                                         rows=self.rows, require=self.require)
        self.seed_functions['audit'] = audit_function.__globals__['audit']
        self.seed_functions['audit'].__globals__.update(obj=self.obj, txt=self.txt, sha=self.sha,
                                                       rows=self.rows, require=self.require)

    def checkpoints(self, arm, launch, timeline):
        points = []
        for second in (300, 600, 900, 1800, 3600):
            if second > launch['cap_seconds']:
                continue
            events = [r for r in timeline if r['safe_complete_arm_available'] <= second]
            complete = arm['complete_seconds']
            lower = complete if complete is not None else arm['complete_seconds_interval'][0]
            if second > lower or not events:
                points.append(dict(seconds=second, observed=False, U=None, L=None, gap=None,
                                   reason='process ended or no qualified committed own evidence'))
            else:
                event = events[-1]
                points.append(dict(seconds=second, observed=True, U=event['own_U'],
                                   L=event['committed_global_L'], gap=event['signed_gap'],
                                   sequence=event['sequence'], native_first_find_exact=False))
        return points

    def arm(self, launch, identity, formal):
        side = self.out/'campaign/reader_recovery'/f'{launch["number"]:02d}_{launch["id"]}_S{launch["seed"]}_{launch["arm"]}.json'
        if formal and side.exists():
            self.require(launch['arm'] == 'P-GRB', 'scoped damaged call requires a separate domain-specific proof')
            proposed = self.obj(side)
            signed_path = self.local(proposed['independent_audit_path'])
            self.require(signed_path.is_relative_to(self.out/'review') and
                         self.sha(signed_path) == proposed['independent_audit_SHA'], 'current independent rejection signature bytes')
            signed = self.obj(signed_path)
            self.require(signed['decision'] == 'ACCEPT_CURRENT_CALL_REJECTION' and
                         signed['current_key'] == proposed['key'] and signed['production_PE_SHA'] == self.pe_sha and
                         signed['campaign_identity_SHA'] == proposed['campaign_identity_SHA'] and
                         signed['complete_seconds_interval'] == proposed['time']['interval'],
                         'signature belongs to the exact current campaign/call and original bounded clock')
            import round110_independent_cold_rejection as cold
            self.sha(Path(cold.__file__))
            rebuilt, result, models, q = cold.audit(self, launch, identity, proposed)
            for name in ('current_model_SHA', 'exact_vector_SHA', 'exact_objective', 'raw_bindings', 'own_U',
                         'certificate_from_own_exact_zero', 'missing_returned_journal_preserved'):
                self.require(rebuilt[name] == signed[name], 'independent current proof rechecked '+name)
            d = self.local(launch['destination'])
            observations = self.obj(d/'observations.json')
            offset = result['complete_seconds_interval'][1]-result['normal_completion']['fully_observed_end_to_end_seconds']
            timeline, own_U = [], math.inf
            for observed in observations:
                e = observed['payload']
                if e['kind'] == 'witness':
                    ph = self.functions['full_physics'](q, e['routes'], launch['panel'])
                    own_U = min(own_U, ph['U'])
                if math.isfinite(own_U):
                    timeline.append(dict(sequence=e['sequence'], kind=e['kind'], own_U=own_U,
                                         committed_global_L=0., signed_gap=own_U,
                                         safe_complete_arm_available=observed['effective_available_seconds']+offset,
                                         lower_bound_source='own original complete-domain nonnegative floor',
                                         native_bounds_mathematically_qualified=False))
            result['checkpoints'] = self.checkpoints(result, launch, timeline)
            filename = launch['id']+'_seed'+str(launch['seed'])+'_P_GRB'
            self.save(self.destination/(filename+'_timeline.json'), timeline)
            self.save(self.destination/(filename+'_cover_chronology.json'), [])
            self.milestones.append(launch['id']+' P-GRB current rejection')
            self.cache.clear()
            return result, models, q
        # No signed current proof means this path deliberately HOLDs damaged
        # native evidence; it never searches for a historical tuple sidecar.
        result = self.functions['audit_arm'](launch, identity, formal)
        self.cache.clear()
        return result

    def budget(self, fees, remaining_groups, overhead=0):
        starts = sum(x['conservative_process_starts'] for x in fees)
        seconds = sum(x['outer_seconds'] for x in fees)
        qualification = [x for x in fees if x['qualification']]
        qstarts = sum(x['conservative_process_starts'] for x in qualification)
        qseconds = sum(x['outer_seconds'] for x in qualification)
        remaining_starts = sum(1+len(methods) for cap, methods in remaining_groups)
        nominal = sum(cap*len(methods) for cap, methods in remaining_groups)
        self.require(starts+remaining_starts <= 96 and seconds+nominal+overhead <= 110000,
                     'all remaining formal nominal/start reserve fits R110 ceiling')
        self.require(qstarts <= 20 and qseconds <= 2000,
                     'all native qualification and enclosing wrappers within 20/2000')
        return dict(paid_starts=starts, paid_outer_seconds=seconds,
                    qualification_starts=qstarts, qualification_outer_seconds=qseconds,
                    remaining_formal_starts=remaining_starts, remaining_nominal_seconds=nominal,
                    remaining_overhead_seconds=overhead, max_starts=96, max_outer_seconds=110000,
                    unknown_early_stop_savings_credited=False, nested_native_seconds_added=False)


class _RoundPath(ast.NodeTransformer):
    def visit_Constant(self, node):
        if isinstance(node.value, str):
            node.value = node.value.replace('results/unified_exact_round109', ROUND)
            # R109 parser/kernel are the signed shared code dependency.
            if node.value in ('round109_independent_parser.py', 'round109_independent_kernel.py'):
                node.value = '../../unified_exact_round109/review/' + node.value
        return node
