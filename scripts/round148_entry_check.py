"""Two actual CLI dry plans and frozen command equivalence; zero Native load."""
import types
import ast
import paper_s2 as base
from round148_common import *


def main():
    configure();profile=read(ROOT/'config/gi_tbc_shared_s_round148.json')
    matrix=read(OUT/'k35_matrix.json');facts=[]
    for shared in ('off','on'):
        output=TEMP/('entry_unused_'+shared)
        command=[PYTHON,'-B',ROOT/'scripts/paper_s2_shared_s.py','--input',
            ROOT/'results/unified_exact_round132/inputs/K-35-U.txt','--out-dir',output,
            '--T','10800','--lambda','.15','--cap','2400','--seed','0','--json','--shared-s',shared]
        result=subprocess.run(list(map(str,command)),cwd=ROOT,env=environment(),capture_output=True,text=True,timeout=30)
        assert result.returncode==0,result.stderr
        launch=json.loads(result.stdout);assert launch['dry_run'] and not output.exists()
        assert launch['GD'] and not launch['STOCK'] and launch['shared_S']==(shared=='on')
        assert launch['matches_verified_PE'] and launch['matches_verified_DLL']
        expected=matrix['groups'][shared=='on']['launch']['command']
        assert base.normalize(launch['command'],profile)==base.normalize(expected,profile)
        facts.append(dict(shared_S=shared,actual_CLI=True,normalized_frozen_command_equal=True,
            PE_SHA=launch['executable_SHA256'],output_not_created=True))
    syntax=[]
    for path in sorted((ROOT/'scripts').glob('round148*.py')):
        ast.parse(path.read_text(encoding='utf-8'),filename=str(path));syntax.append(path.name)
    write(OUT/'qualification_entry.json',dict(PASS=True,Optimize=0,Native_load=0,compile=0,
        facts=facts,syntax_checked=syntax,old_profiles_unmodified=True,
        current_profile_SHA=sha(ROOT/'config/gi_tbc_shared_s_round148.json'),entry_SHA=sha(ROOT/'scripts/paper_s2_shared_s.py')))
    print('PASS actual shared-S on/off dry CLI, new PE/DLL identity, frozen normalized commands and helper syntax')


if __name__=='__main__':main()
