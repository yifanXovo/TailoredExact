"""One-time engineering correction of inherited clock wording; no numbers change."""
from round104_common import *
from round104_results import charged_clock_scope
import csv

def main():
    target=OUT/'reports_final02_clocks/discovery_certification.csv'
    original=OUT/'reader_provenance/report02.executed.py'
    identity=read(OUT/'reports_final02/reporting_identity.json')
    assert sha(original)==identity['source_sha256']
    prior=OUT/'reader_provenance/scope_annotation.json'
    if prior.exists():
        # The first engineering launch wrote the annotation/CSV, then failed
        # on the exclusive original identity writer. Preserve that identity.
        q=read(prior)
        assert sha(target)==q['after_sha256']
        assert sha(OUT/'reader_provenance/discovery_certification.before.csv')==q['before_sha256']
        with (OUT/'reader_provenance/discovery_certification.before.csv').open(newline='',encoding='utf-8') as f:
            before_rows=list(csv.DictReader(f))
        with target.open(newline='',encoding='utf-8') as f:after_rows=list(csv.DictReader(f))
        assert charged_clock_scope(before_rows)==after_rows
        print(json.dumps(dict(verified_prior_partial_annotation=True,original_identity_preserved=True,
            numeric_fields_unchanged=True,Optimize_calls=0,DP_calls=0,annotation_sha256=sha(prior))))
        return
    old=target.read_bytes();before=sha(target)
    with target.open(newline='',encoding='utf-8') as f:
        reader=csv.DictReader(f);fields=reader.fieldnames;rows=list(reader)
    original_rows=[dict(r) for r in rows]
    charged_clock_scope(rows)
    assert len(rows)==4
    assert all(a[k]==b[k] for a,b in zip(rows,original_rows) for k in fields if k!='scope')
    assert all(a['scope']!=b['scope'] for a,b in zip(rows,original_rows))
    (OUT/'reader_provenance/discovery_certification.before.csv').write_bytes(old)
    with target.open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    annotation=dict(source_sha256=sha(__file__),original_report_reader_sha256=sha(original),
        current_report_reader_sha256=sha(ROOT/'scripts/round104_results.py'),
        before_sha256=before,after_sha256=sha(target),rows=len(rows),changed_fields=['scope'],
        numeric_fields_unchanged=True,Optimize_calls=0,DP_calls=0,
        scope='Engineering wording correction after report02; no new performance or numerical review')
    write(OUT/'reader_provenance/scope_annotation.json',annotation)
    print(json.dumps(annotation))

if __name__=='__main__':main()
