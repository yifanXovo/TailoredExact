# Automatically generated measured tables

Process wall includes setup and finalization. Uncertified wall is budget use, not time to solution. Fixed-F0 certificates have narrower scope than full original-problem certificates.


## screen_v1

| # | id | arm | cap | wall s | certificate | UB | LB | absolute gap | Work | calls | eligible |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 6 | D4 | off | 120 | 90.125 | yes | 0.506343 | 0.506343 | 3.19211e-10 | 140.873 | 1 | yes |
| 7 | D4 | explicit | 120 | 118.078 | no | 0.506343 | 0.483204 | 0.0231391 | 180.927 | 1 | no |
| 8 | D4 | simple | 120 | 115.828 | yes | 0.506343 | 0.506343 | 1.64375e-09 | 185.431 | 1 | yes |
| 9 | D4 | precrush | 120 | 89.593 | yes | 0.506343 | 0.506343 | 0 | 140.625 | 1 | yes |
| 10 | D4 | dry | 120 | 89.766 | yes | 0.506343 | 0.506343 | 0 | 140.625 | 1 | yes |
| 11 | D4 | cuts | 120 | 95.89 | yes | 0.506343 | 0.506343 | 1.22125e-15 | 149.887 | 1 | yes |
| 12 | D7 | off | 120 | 118.437 | no | 0.671237 | 0.195076 | 0.476161 | 285.728 | 1 | yes |
| 13 | D7 | explicit | 120 | 118.5 | no | 0.365027 | 0.195501 | 0.169526 | 268.236 | 1 | yes |
| 14 | D7 | simple | 120 | 118.453 | no | 0.709797 | 0.194506 | 0.51529 | 289.482 | 1 | yes |
| 15 | D7 | precrush | 120 | 118.438 | no | 0.506339 | 0.195218 | 0.311121 | 287.368 | 1 | yes |
| 16 | D7 | dry | 120 | 118.438 | no | 0.506339 | 0.195218 | 0.311121 | 286.804 | 1 | yes |
| 17 | D7 | cuts | 120 | 118.453 | no | 0.559389 | 0.195131 | 0.364258 | 286.901 | 1 | yes |


## repeat_v1

| # | id | arm | cap | wall s | certificate | UB | LB | absolute gap | Work | calls | eligible |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 18 | D4 | explicit | 120 | 118.094 | no | 0.506343 | 0.483399 | 0.0229441 | 181.351 | 1 | yes |


## micro_root_v2

| # | id | arm | cap | wall s | certificate | UB | LB | absolute gap | Work | calls | eligible |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 19 | micro-root | root | 20 | 0.094 | yes | 0.325 | 0.325 | -5.55112e-17 | 0.00152885 | 2 | yes |


## failure_diagnostic_v2

| # | id | arm | cap | wall s | certificate | UB | LB | absolute gap | Work | calls | eligible |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 20 | D7 | cuts | 120 | 118.453 | no | 0.559389 | 0.195131 | 0.364258 | 287.284 | 1 | yes |


## screen_root_v2

| # | id | arm | cap | wall s | certificate | UB | LB | absolute gap | Work | calls | eligible |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 21 | D4 | off | 120 | 90.156 | yes | 0.506343 | 0.506343 | 3.19211e-10 | 140.873 | 1 | yes |
| 22 | D4 | root-dry | 120 | 90.125 | yes | 0.506343 | 0.506343 | 3.19211e-10 | 140.987 | 2 | yes |
| 23 | D4 | root | 120 | 118.093 | no | 0.506343 | 0.491086 | 0.0152568 | 187.561 | 2 | yes |
| 24 | D7 | off | 120 | 118.422 | no | 0.671237 | 0.195076 | 0.476161 | 284.546 | 1 | yes |
| 25 | D7 | root-dry | 120 | 118.438 | no | 0.671237 | 0.195076 | 0.476161 | 285.569 | 2 | yes |
| 26 | D7 | root | 120 | 118.437 | no | 0.63257 | 0.195138 | 0.437432 | 283.778 | 2 | yes |


## Predeclared dual-threshold decisions

| id | scope | baseline # | candidate # | baseline | candidate | decision |
| --- | --- | --- | --- | --- | --- | --- |
| D4 | fixed_F0_improving_domain | 6 | 8 | off | simple | time_loss |
| D4 | fixed_F0_improving_domain | 6 | 9 | off | precrush | below_time_threshold |
| D4 | fixed_F0_improving_domain | 6 | 10 | off | dry | below_time_threshold |
| D4 | fixed_F0_improving_domain | 6 | 11 | off | cuts | below_time_threshold |
| D4 | fixed_F0_improving_domain | 9 | 10 | precrush | dry | below_time_threshold |
| D4 | fixed_F0_improving_domain | 10 | 11 | dry | cuts | below_time_threshold |
| D7 | fixed_F0_improving_domain | 12 | 13 | off | explicit | gap_gain |
| D7 | fixed_F0_improving_domain | 12 | 14 | off | simple | gap_loss |
| D7 | fixed_F0_improving_domain | 12 | 15 | off | precrush | gap_gain |
| D7 | fixed_F0_improving_domain | 12 | 16 | off | dry | gap_gain |
| D7 | fixed_F0_improving_domain | 12 | 17 | off | cuts | gap_gain |
| D7 | fixed_F0_improving_domain | 15 | 16 | precrush | dry | below_gap_threshold |
| D7 | fixed_F0_improving_domain | 16 | 17 | dry | cuts | gap_loss |
| D7 | fixed_F0_improving_domain | 14 | 13 | simple | explicit | gap_gain |
| D4 | fixed_F0_improving_domain | 21 | 22 | off | root-dry | below_time_threshold |
| D4 | fixed_F0_improving_domain | 21 | 23 | off | root | certificate_loss |
| D4 | fixed_F0_improving_domain | 22 | 23 | root-dry | root | certificate_loss |
| D7 | fixed_F0_improving_domain | 24 | 25 | off | root-dry | below_gap_threshold |
| D7 | fixed_F0_improving_domain | 24 | 26 | off | root | gap_gain |
| D7 | fixed_F0_improving_domain | 25 | 26 | root-dry | root | gap_gain |
| D4 | fixed_F0_improving_domain | 6 | 18 | off | explicit | certificate_loss |
