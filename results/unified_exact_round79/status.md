# Round79 original campaign active

Base R78 final d064fe38c14caf7f8bcc201212cd7654e99f52c1 / draft PR139,
verified published/open/draft/unmerged. Read plan.md. No C++ or parameter change;
reuse build/round78/v1, source4a0561e0f8193e3e874c1bd0bfa8bc381fb66f5e.
Exactly18 serial full runs E7,S12,N12,D3,C2,D4, each P/BDS-C/K1-R in that order;
first3 roles120s, last3 roles300s, total<=3780s, six zero-Optimize P references.
No new build/test/rerun/extension/confirmation. No overlapping heavy work.
Campaign driver round79_research.py must be committed before launch.

Inspect campaign/identity.json, processes.jsonl, summary.json, active_experiment
and driver_completion for recovery. Preserve failures; no automatic retry.
Post-run checkpoint, physical, coverage and actual Start audits plus lossless
bundles are due before independent stage draft PR. Overall goal remains unmet;
ordinary usage55% remaining, no reset consumed. Original dirty checkout untouched.

Live recovery: exec26444 / Python PID26312. First9 arms normal, valid and
certified; D3 P-GRB (launch10) active. E7 P/BDS/K1 walls1.422/1.235/5.750s;
S12 5.657/1.812/40.734s; N12 4.281/1.391/7.438s. These are normal endpoint
checks; final joint/actual-vector audits remain pending. Prepared analyzer,
mechanism and package scripts have not been executed. No heavy overlap.

Updated checkpoint: first12 complete and valid. D3 P-GRB normal297.062s,
U.045054162/L.041540120, uncertified. BDS-C certifies in138.968s, original
F.045001550056. K1-R normal297.078s, U.045054162/L.043855266, uncertified.
Original C2 P-GRB launch13 active; six allocated C2/D4 arms remain in total.
All monitor cells through1856 finished; exec26444 remains active. Two git
transport failures and successful third push are preserved in push_attempts;
remote branch reaches76f2f2784. No solver failure or rerun. Final joint/actual
Start-vector audit and packaging must wait until all18 original arms close.
