# Round 50 cut-family baseline audit

The native root-cut census is observational; it does not prove that a static model row family is useful or redundant. Aggregate native counts were:

- bqp: 105 native root cuts across 14 rows
- clique: 149 native root cuts across 14 rows
- cover: 869 native root cuts across 14 rows
- flow cover: 2564 native root cuts across 14 rows
- gomory: 77 native root cuts across 14 rows
- gub cover: 55 native root cuts across 14 rows
- implied bound: 2341 native root cuts across 14 rows
- inf proof: 32 native root cuts across 14 rows
- learned: 174 native root cuts across 14 rows
- lift-and-project: 2 native root cuts across 14 rows
- mir: 2254 native root cuts across 14 rows
- network: 240 native root cuts across 14 rows
- projected implied bound: 220 native root cuts across 14 rows
- psd: 4 native root cuts across 14 rows
- relax-and-lift: 607 native root cuts across 14 rows
- rlt: 256 native root cuts across 14 rows
- strongcg: 163 native root cuts across 14 rows
- zero half: 55 native root cuts across 14 rows

High cut count alone does not track total Work: D2 is easy despite hundreds of cuts, while several hard rows spend most Work after the root. Therefore no generic Gurobi `Cuts` parameter change is permitted. Iteration 2 must first build the complete static row-family registry, duplicate/dominance audit, and leave-one-block evidence before deciding whether any exact candidate exists.
