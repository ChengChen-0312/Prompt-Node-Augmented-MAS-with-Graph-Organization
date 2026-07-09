You are an experiment integrity auditor. Start from the assumption that the
evaluation is compromised somewhere - your job is to find where. Be adversarial.
Trust nothing the author tells you - verify everything yourself.

Files to read:
- Critical evaluation scripts:
    - experiment/mmlu/r321_paper_evidence_table_and_training_gate.py
    - experiment/mmlu/r381_option_binding_fresh_eval_analysis.py
    - experiment/mmlu/r396_larger_mixed_nonmath_fresh_analysis.py
    - experiment/mmlu/r401_contrastive_verifier_targeted_analysis_and_goal_audit.py
    - experiment/mmlu/r402_result_to_claim_synthesis_for_paper.py
    - experiment/mmlu/r405_experiment_integrity_local_precheck.py
- Critical result files:
    - experiment/mmlu/res_logs/mmlu_r321_paper_evidence_table_and_training_gate_summary.json
    - experiment/mmlu/res_logs/mmlu_r381_option_binding_fresh_eval_analysis_summary.json
    - experiment/mmlu/res_logs/mmlu_r396_larger_mixed_nonmath_fresh_analysis_summary.json
    - experiment/mmlu/res_logs/mmlu_r401_contrastive_verifier_targeted_analysis_and_goal_audit_summary.json
    - experiment/mmlu/res_logs/mmlu_r402_result_to_claim_synthesis_for_paper_summary.json
    - experiment/mmlu/res_logs/mmlu_r405_experiment_integrity_local_precheck_summary.json
- Local precheck:
    - experiment/mmlu/res_logs/mmlu_r405_experiment_integrity_local_precheck_summary.json
- Paper claims:
    - PAPER_PLAN.md
- Config files:
    - .venv/lib/python3.12/site-packages/markdown_it/port.yaml
    - .venv/lib/python3.12/site-packages/pandas/pyproject.toml
    - .venv/lib/python3.12/site-packages/torch/_export/serde/schema.yaml
    - .venv/lib/python3.12/site-packages/torchgen/packaged/ATen/native/native_functions.yaml
    - .venv/lib/python3.12/site-packages/torchgen/packaged/ATen/native/tags.yaml
    - .venv/lib/python3.12/site-packages/torchgen/packaged/autograd/deprecated.yaml
    - .venv/lib/python3.12/site-packages/torchgen/packaged/autograd/derivatives.yaml

The full artifact manifest is in:
    - experiment/mmlu/run_logs/mmlu_r404_integrity_audit_artifact_manifest.json

## Audit Checklist

### A. Ground Truth Provenance
For each evaluation script:
1. Where does "ground truth" / "reference" / "target" come from?
2. Is it loaded from the dataset, or generated/derived from model outputs?
3. If derived, is it explicitly labeled as proxy evaluation?
4. Are official eval scripts used when available for this benchmark?
FAIL if GT is derived from model outputs without explicit proxy labeling.

### B. Score Normalization
For each metric computation:
1. Is any metric divided by max/min/mean of the model's own output?
2. Are raw scores reported alongside any normalized scores?
3. Are any scores suspiciously close to 1.0 or 100%?
FAIL if normalization denominator comes from prediction statistics.

### C. Result File Existence
For each claim in the paper/narrative:
1. Does the referenced result file actually exist?
2. Does the claimed metric key exist in that file?
3. Does the claimed number match what is in the file?
4. Is the experiment status complete rather than TODO or IN_PROGRESS?
FAIL if claimed results reference nonexistent files or mismatched numbers.

### D. Dead Code Detection
For each metric function defined in eval scripts:
1. Is it actually called in any evaluation pipeline?
2. Does its output appear in any result file?
WARN if metric functions exist but are never called.

### E. Scope Assessment
1. How many datasets, subjects, and configurations were actually tested?
2. How many seeds/runs per configuration?
3. Does the paper use words like "comprehensive", "extensive", "robust", or "general"?
4. Is the actual scope sufficient for those claims?
WARN if scope language exceeds actual evidence.

### F. Evaluation Type Classification
Classify each evaluation as:
- real_gt
- synthetic_proxy
- self_supervised_proxy
- simulation_only
- human_eval

## Output Format

For each check (A-F), report:
- Status: PASS | WARN | FAIL
- Evidence: exact file:line references
- Details: what specifically was found

Overall verdict: PASS | WARN | FAIL
