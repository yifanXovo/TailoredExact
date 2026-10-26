# Historical panel fields versus Round67 experiment scope

protocol.json copies the original panel rows to preserve their input and
historical selection metadata. Their nested `stage`, `role`, `method_first`,
`method_second` and `selection_status` fields belong to prior rounds. In
particular C2's inherited `stage: confirmation` does NOT denote a Round67
confirmation experiment. Every current non-micro launch is development, as
declared in plan.md and recorded by processes.jsonl's actual `stage` field.
protocol.json's top-level `confirmation_opened` remains false. No source row,
input, threshold or result is changed by this clarification.

Some inherited V/M/Q fields are strings and others integers. Audit code
normalizes the numeric type when checking expected variable counts. This is
an evidence-reader detail and does not change the frozen experiment driver or
the native parsed instance.
