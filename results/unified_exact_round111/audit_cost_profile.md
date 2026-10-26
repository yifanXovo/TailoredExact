# Actual audit cost profile and empirical envelope

The old arm42 original necessary audit was 29.69575260009151s. Its old native/audit/whole clocks and invalid eligibility remain immutable.
An unchanged old adapter was profiled with cProfile and stage timers: 60.2785013000248s inclusive. Instrumentation overhead prevents treating this as an uninstrumented speed ratio.
Nested times below overlap and must not be summed. The two earlier old-only comparison failures exposed only the nested neutral-exchange replay timer; their actual exits and complete measured adapter costs are retained. The timer whitelist correction preceded every new audit replay.

|Old measured stage|Seconds|
|---|---:|
|model_read_parse|18.645790|
|column_type_classification|0.263477|
|duplicate_row_Counter|0.144192|
|input_read_parse|0.013115|
|per_station_column_classification|29.492821|
|frozen_A_B_checks|0.006992|
|scope_check_including_Counter|0.169791|

cProfile additionally measures Seed proof 48.954s inclusive, original adapter 10.924s inclusive, neutral exchange/closure physical oracle 10.616s inclusive and native physical/journal audit .263s inclusive. No separate return-only timer exists; it stays inside Seed/native scope. Writes are included by replay receipts.

|Fresh new replay|Necessary postexit seconds|
|---|---:|
|new_arm37_replay01|0.148434000|
|new_arm38_replay01|0.254421100|
|new_arm39_replay01|3.946372900|
|new_arm40_replay01|0.719285700|
|new_arm41_replay01|4.308029700|
|new_arm42_replay01|14.315222800|
|new_arm42_replay02|14.474583100|
|new_arm42_replay03|14.515012300|

Maximum postexit 14.515012300s; measured identity admission 0.106102100s. Original combined preentry/exit offset upper observation 8.909504600s (includes its recorded admission); empirical 30s reserve remainder 6.469381000s.
These finite observations qualify the fixed machine envelope, not a Windows/IO worst-case guarantee. New CLI and every formal arm retain actual native_end, audit_end and whole receipts. No necessary check is moved outside cap.
