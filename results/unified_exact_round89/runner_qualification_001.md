# Round89 native-B1 G3 runner qualification 001 — zero Optimize

The toy003 owner explicitly released the computation slot before this single check. The check returned exit 0 in **0.1252175 s outer wall** using `D:/msys64/ucrt64/bin/python.exe`. It imported the runner, called only `panel_and_identity`, `launches_for`, and `harness_hashes`, and created no campaign directory. It did not call `prepare`, launch ExactEBRP, export a model, or call Optimize. The [JSON receipt](runner_qualification_001.json) retains all 16 exact constructed command arrays and all harness hashes.

The invoked Python payload was:

```powershell
$code = @'
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / "scripts"))
import round89_native_b1_g3 as runner
prereg = runner.read(runner.PREREG)
input_audit = runner.panel_and_identity(prereg)
launches = runner.launches_for(prereg)
harness = runner.harness_hashes()
assert len(launches) == 16
assert not runner.CAMPAIGN.exists()
print(json.dumps({"schema":"round89-native-b1-runner-qualification-001-v1","checks":["module_import","panel_and_identity","launches_for","harness_hashes"],"source_runner_sha256":runner.sha(Path(runner.__file__)),"preregistration_sha256":runner.sha(runner.PREREG),"input_audit_sha256":runner.sha(runner.INPUT_AUDIT),"input_audit_role_count":input_audit["role_count"],"historical_p_role_count":len(prereg["historical_round88_p_timing"]["raw_receipts_by_role"]),"harness_hashes":harness,"launches":launches,"campaign_exists_after":runner.CAMPAIGN.exists(),"prepare_invoked":False,"optimize_invoked":False},sort_keys=True))
'@
D:/msys64/ucrt64/bin/python.exe -c $code
```

The PowerShell wrapper checked that the campaign directory was absent before and after, timed the one Python process with `System.Diagnostics.Stopwatch`, required exit 0, and wrote the captured JSON to `runner_qualification_001.json`. The imported runner SHA was `c13162f93ce3c616cc3e97379bef0012093d4be08fec649fde2d14f9bd3473c8`; preregistration SHA was `122ddeadd76a40cdff794baa71632687dae140e1f954a9c11f96faa9a1823cb8`. The input identity audit SHA was `133e5f159385c21f8bc130e24f8ea3acd31f3643b3abbe5182edda4cd30a6ff6`; its 19-role source ledger passed the eight selected-role checks. All eight historical Round88 P launch/audit receipt hashes in the preregistration matched. The JSON receipt records exact eight-component harness hashes; the runner component equals the runner SHA above.

This is a source/evidence identity qualification only. It does not qualify the final Round89 binary or callback behavior. Gate binding, smoke lease, and real screening remain separate decisions by root.
