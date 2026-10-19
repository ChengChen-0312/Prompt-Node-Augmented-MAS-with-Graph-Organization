# Prompt Node: shared-plan code generation — research artifacts

This directory accompanies **Prompt Node: Guiding Code Generation with Shared Plans**.
It is a separate release from the earlier graph-organization/MAS study elsewhere in
this repository. Those earlier files and results are preserved.

The release contains saved task-level outcomes and resource records, the fixed task
identities, exact archived prompt templates, selected implementation files, and
scripts for checking the published numbers offline. It does **not** provide a
complete portable generation-to-scoring runner.

## Start here

| Directory | Contents |
|---|---|
| `statistics/` | Saved paired outcomes, resource summaries, and runnable offline calculations |
| `cohorts/` | The 600 fixed task identities: USACO110, TACO231, OJBench28, and LCB231 |
| `records/qwen_lcb231/` | 231 paired task rows, 1,101 completed request resource rows, and the recorded output-limit revision |
| `records/previous_supplement/prompt_templates.json` | Exact archived LCB prompts and plan-extraction rule |
| `code/source_for_inspection/` | Selected original generation, extraction, execution, and report sources; intentionally stored as `.py.txt` |
| `protocol/` | Source hashes, method boundaries, and what a new run would still require |
| `verification/` | Checks performed while preparing this release |
| `manuscript/english/tables/shared_start_table.tex` | One exact result table used by the offline table check; the article and submission files are not included |

## Results represented here

| Model and task set | Shared starting selection | Independent | Prompt Node |
|---|---:|---:|---:|
| GPT-4o, USACO110 | 17/110 | 22/110 | 19/110 |
| GPT-4o, TACO231 | 67/231 | 69/231 | 71/231 |
| GPT-4o, OJBench28 | 6/28 | 7/28 | 6/28 |
| GPT-4o, LCB231 | 101/231 | 109/231 | 113/231 |
| Local Qwen, LCB231 | 141/231 | 149/231 | 169/231 |

Independent is the archived A1 branch. Prompt Node (PN) is A2-Plan/A2. PN-Feedback
and PN-Refine are separate extensions. Stored filenames and labels retain their
original names so that results can be traced. The later USACO PN-only rerun and an
earlier LCB comparison are kept separate in the statistics, rather than substituted
into the primary table.

Each primary pair shares its three initial candidates. If all three fail public
tests, each arm produces three more candidates before testing that batch. PN reads
three, four, then five plans, appending only its own additions. The first candidate
passing public tests is selected; otherwise the first initial candidate is selected.
Final scoring takes place after selection is frozen.

The Qwen result is a comparison of the complete prompt strategies. It does not
separate plan content, accumulation, exploration instructions, and the position of
the output reminder. Delivery of a complete program remains part of solving the
task; missing-code outcomes are not removed. The GPT-4o comparisons show both gains
and losses, and their task-paired intervals include zero.

## Reproduce the numerical summaries without a model

Use Python 3.10+ and NumPy. `statistics/requirements.txt` records the earlier checked
version. The release verification records the actual environment used for this
copy. From this directory:

```bash
python3 verify_integrity.py
python3 statistics/run_offline.py --output reproduced/statistics
python3 statistics/verify_main_table.py
python3 statistics/verify_qwen_lcb.py --output reproduced/qwen_lcb.json
```

Choose a new output directory on a subsequent run. These commands read saved scalar
labels and usage rows. They do not call a model, execute generated programs, fetch
benchmark tests, or perform scoring. The main table is reconstructed byte for byte.
The statistical check includes 600 primary pairs and 231 earlier LCB pairs kept as
a separate comparison. The Qwen check verifies all 693 selected labels, 21 PN-only
versus one Independent-only success, and request/token accounting.

## Scope and access

No task statements, public or final test payloads, model weights, full model reply
archives, credentials, personal author forms, or submission ZIPs are included.
External datasets and model dependencies must be obtained under their own terms.
The source-inspection files are useful for checking what the original workflows did;
renaming them to `.py` does not supply their missing dependencies or archives.
See [protocol/REPRODUCTION_SCOPE.md](protocol/REPRODUCTION_SCOPE.md).

The copied result rows are unchanged. [protocol/copied_source_manifest.json](protocol/copied_source_manifest.json)
records their source hashes; `MANIFEST.json` binds the distributed files. No new
experiment or rescore was performed to publish this directory.

The repository's existing [MIT license](../../LICENSE) applies to the author's
original contributions. See [RIGHTS.md](RIGHTS.md) for the limits of that grant.
