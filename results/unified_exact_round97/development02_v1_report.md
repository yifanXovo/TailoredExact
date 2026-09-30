# V1 complete registered comparison

All three registered arms were attempted once with the same frozen v2 binary, input `dd841e57b2c22158002b0c9ec4940a9f071c11b8881a32b65168bbdb182f6829`, mathematical T=7200s and common process cap=1800s. OFF and original P-GRB returned normally without a certificate. FEEDBACK reached the preset hard stop; its original audit failure remains preserved, with a separate independently reviewed recovery described in `development02_v1_interruption.md`.

| Arm | Process seconds | U | Global L | Absolute gap | Evidence |
|---|---:|---:|---:|---:|---|
| OFF | 1797.141 | .17155123467659872 | .1534048797180084 | .01814635495859032 | Normal, uncertified |
| FEEDBACK, combined | 1798.078 | .16951364260212742 | .15346582763163313 | .01604781497049429 | Recovered interrupted endpoint |
| Original P-GRB | 1797.156 | .18441378964502725 | .15240199117470038 | .03201179847032687 | Normal, uncertified |

The combined arm's observed U improves 1.1877% against OFF and 8.0797% against P; its absolute gap improves 11.5645% and 49.8691%, respectively. Both exceed the preregistered quality thresholds. These are common-window observed quality gains, not certification gains or evidence of eventual speed. The interrupted arm has unknown normal-finalization certificate status, complete Optimize total and complete callback overhead. No costs are removed because of interruption.

This V1 result does not repeat the historical R96 startup-reordering regression: this experiment keeps the original 24+1 startup and applies closure only to eligible later native physical states. It also does not disprove that historical result, which tested a different mechanism. There is no same-build V1 old-closure-only complete control, so the whole-run gain cannot be assigned entirely to the new ordering operator.

## Mechanism and attribution

OFF records 36 MIPSOL events and 25 unique physical inputs; three Start-matching events are excluded and all 33 eligible events have positive node counts. FEEDBACK records 13 events and seven unique inputs; three are excluded and all ten eligible events have positive node counts. Independent actual-model checks pass 25 OFF and ten FEEDBACK retained input/mapped vectors. P is plain compact with one verified Optimize and no Start or new callback closure. The frozen launch's unused `operator=r83` metadata placeholder does not enable an operator in its command.

Three FEEDBACK closures produce three strictly improved candidates and successful API submissions. All three later have tolerance-based full-vector observations; this is processing evidence, not unique-source proof. At node11, event4 changes F=.2731235318632457 to old-closure F=.25075870081243257 and combined F=.18385034092393765; event5 changes F=.2441515231492018 to old F=.21084354944564712 and combined F=.17377347955132771. These two events provide direct fresh-state combined-operator increment. They record 15 ordering moves in total.

The best candidate comes from event8 at node386: F=.17355328820433558 to .16951364260212731. Here the initial old closure already reaches the final candidate and ordering adds no increment. Verification completes at process second79.1446573; the full-vector observation appears at83.0853125. Subsequent native events at nodes545,1975 and3941 show continued search in the same MIP call. No candidate-induced restart or archive handoff is observed. Three per-submission incumbent-threshold records refer to two distinct recorded `(call,value)` pairs; neither number is a complete count of native incumbent updates.

The retained completed solution records charge .2161749s of nested closure and .0207933s of nested mapping. Terminal call-return telemetry is missing, so .0342779s of completed-call callback telemetry is only a partial sum and must not be labeled total overhead. OFF's complete callback total is .3481601s. These nested measurements are explanatory and are not subtracted from outer process costs.

## Evidence and limitations

`analysis_views/development02_V1_v4_analysis` keeps the original failed-audit flag alongside the recovered endpoint; certificate and complete-call-count cells remain empty. Both feedback comparisons are explicitly classified as interrupted, with certification ordering and severity unknown. `trajectories/development02_v1` uses committed evidence availability: recovered lower bounds use only the independent complete-root MIP formula, never inherited LP/cover lower bounds. Normal final results remain untimed sidecars rather than invented certificate-time points.

The feedback witness reaches its eventual observed quality early: at120s its committed U is .16951364260212742; OFF's is .21926351584474377 and P's .3329112579679377. OFF later closes much of this difference. All full trajectories and final endpoints are retained; early lead alone is not the decision criterion.

The three V1 attempts cost 5392.375 outer seconds. Verified completed Optimize counts are five for OFF and one for P. FEEDBACK has five observed scopes, four returned, and unknown complete total. No arm was rerun. New reporting syntax, exact-recovery admission, wrong-role/raw-status rejection and null-quality checks passed, followed by actual analysis and trajectory generation, all with zero Optimize. Their measured wrappers are .1933941s,1.3087816s,.9247627s; these are separate offline costs.

The result supports practical native feedback on this development role, with an explicit finalization limitation. Next is the already registered F2 certification-protection comparison; no uniform candidate is frozen until development is interpreted. Confirmation inputs remain unused. ENS-C stays protected and no promotion or merge is proposed.
