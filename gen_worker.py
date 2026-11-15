"""Generate one task in its own process, run from the pipeline's folder.

The team pipelines and Brain Connections each ship a package named `validate`, so they cannot share one Python
process. Usage: gen_worker.py team6|devtcu PIPELINE QUESTION_TYPE SEED OUT_DIR  (QUESTION_TYPE may be "")."""
import json
import os
import sys
from pathlib import Path

source, pipeline, qtype, seed, out = sys.argv[1:6]
sys.path.insert(0, os.getcwd())
Path(out).mkdir(parents=True, exist_ok=True)
if source == "team6":
    import factory
    spec = {"pipeline": pipeline, "seed": int(seed)}
    if qtype:
        spec["question_type"] = qtype
    task = factory.generate(spec, Path(out))
else:
    from generators.devtcu import adapter
    task = adapter.generate_task(int(seed), qtype or None, out)
    task.update(pipeline="brain_connections", member="devtcu")
print("@@TASK@@" + json.dumps(task, ensure_ascii=False))
