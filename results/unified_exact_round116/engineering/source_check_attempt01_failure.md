The new offline lineage check's first execution failed when comparing Python
coordinate tuples with their JSON-serialized lists. All source/selection/
landscape/input-byte checks reached that point successfully. The old script is
retained as source_check_attempt01.py. The only repair normalizes the parser's
object through JSON before comparing it with the saved JSON mirror:

```diff
-assert parsed == saved_json
+assert json.loads(json.dumps(parsed)) == saved_json
```

No admitted reader/helper, producer, source, input, native output, fee, clock or
qualification changed. This engineering failure did not start native work and
does not repair the formal ENS-C return-audit failure. The repaired read-only
lineage check has its own actual output receipt.
