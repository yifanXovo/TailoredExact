"""Process-local decimal serialization for trusted, bounded exact evidence.

The stock/RMP algorithms and their qualification remain unchanged. Python's
integer-to-text digit limit is disabled only in this metered worker, so a
large exact Fraction is not rounded or dropped when saving its proof.
"""
from fractions import Fraction as F
import runpy
from round153_common import *


ALLOWED = {'round153_primal_pool.py', 'round153_coupled.py', 'round153_finalize.py'}


def enable():
    previous = sys.get_int_max_str_digits()
    sys.set_int_max_str_digits(0)
    assert sys.get_int_max_str_digits() == 0
    return previous


def qualify(label):
    configure(); previous = enable()
    target = OUT/'qualification'/label
    target.mkdir(parents=True, exist_ok=False)
    value = F(10**5000+1, 10**4999+7)
    encoded = str(value)
    assert len(encoded) > 4300 and F(encoded) == value
    encoded_json = json.dumps(dict(exact=encoded), allow_nan=False)
    assert F(json.loads(encoded_json)['exact']) == value
    path = target/'roundtrip.json.gz'
    save_gz(path, dict(exact=encoded))
    assert F(load_gz(path)['exact']) == value
    write(target/'result.json', dict(PASS=True, previous_process_digit_limit=previous,
        active_process_digit_limit=0, serialized_fraction_characters=len(encoded),
        exact_text_JSON_gzip_roundtrip=True, Optimize=0, Native_model_reads=0,
        no_stock_or_master_algorithm_change=True, process_local_only=True,
        outer_fee_label=os.environ['ROUND140_METERED_PARENT_LABEL'],
        source_SHA=sha(Path(__file__)), Python=sys.executable,
        roundtrip_evidence_SHA=sha(path)))
    print(json.dumps(read(target/'result.json')), flush=True)


def execute(label, script, qualification, *arguments):
    configure()
    assert script in ALLOWED
    assert os.environ.get('ROUND140_METERED_PARENT_LABEL') == label
    qualification_path = OUT/'qualification'/qualification/'result.json'
    proof = read(qualification_path)
    assert proof['PASS'] and proof['source_SHA'] == sha(Path(__file__))
    previous = enable()
    target = OUT/'engineering/exact_integer_runtime'/f'{label}.json'
    assert not target.exists()
    program = ROOT/'scripts'/script
    write(target, dict(UTC=utc(), outer_fee_label=label, script=script,
        script_SHA=sha(program), arguments=list(arguments),
        previous_process_digit_limit=previous, active_process_digit_limit=0,
        process_local_only=True, bounded_by_existing_outer_receipt=True,
        qualification_SHA=sha(qualification_path), wrapper_SHA=sha(Path(__file__)),
        no_lower_precision_or_changed_stock_algebra=True))
    sys.argv = [str(program), *arguments]
    runpy.run_path(str(program), run_name='__main__')


if __name__ == '__main__': globals()[sys.argv[1]](*sys.argv[2:])
