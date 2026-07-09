# R445 External Audit Payload: experiment_integrity_audit

This payload is prepared for a fresh external reviewer. It has not been submitted by Codex.

## Audit Prompt

# R441 External Experiment Integrity Audit Prompt

Audit whether the reported PromptNode-Augmented MAS results are grounded in result files, use ARG-Designer as the baseline, and avoid broad nonmath/general claims.

## Files To Inspect

- `experiment/aqua/res_logs/aqua_tail34_r271_final_claim_table_summary.json`
- `experiment/mmlu/res_logs/mmlu_r321_paper_evidence_table_and_training_gate_summary.json`
- `experiment/mmlu/res_logs/mmlu_r396_larger_mixed_nonmath_fresh_analysis_summary.json`
- `experiment/mmlu/res_logs/mmlu_r414_definition_challenge_gate_analysis_summary.json`
- `experiment/mmlu/res_logs/mmlu_r419_lifecycle_trace_replay_summary.json`
- `experiment/mmlu/res_logs/mmlu_r426_update_cost_table_with_stem_probe_and_goal_audit_summary.json`
- `experiment/mmlu/res_logs/mmlu_r440_paper_claim_number_static_audit_summary.json`

## Required Output

Return PASS/WARN/FAIL with file:line evidence and concrete fixes.

## Attached File Contents

### `experiment/aqua/res_logs/aqua_tail34_r271_final_claim_table_summary.json`

```json
{
  "run_id": "R271",
  "title": "Tail34 final official/audit-clean claim table",
  "claim_boundary": "paper_table_generation_only_no_new_api",
  "variants": {
    "ARG": {
      "official": "28/34",
      "audit_clean_exclude_59_139_228": "28/31",
      "correct_task114": "29/31",
      "exclude_task114": "28/30",
      "cost": 0.93285,
      "claim_role": "baseline"
    },
    "R065": {
      "official": "31/34",
      "audit_clean_exclude_59_139_228": "31/31",
      "correct_task114": "30/31",
      "exclude_task114": "30/30",
      "cost": 5.050805,
      "claim_role": "highest official replay score, noisy task114 risk"
    },
    "R068": {
      "official": "31/34",
      "audit_clean_exclude_59_139_228": "31/31",
      "correct_task114": "30/31",
      "exclude_task114": "30/30",
      "cost": 3.597409,
      "claim_role": "cost-reduced replay retaining R065 score"
    },
    "R095": {
      "official": "30/34",
      "audit_clean_exclude_59_139_228": "30/31",
      "correct_task114": "31/31",
      "exclude_task114": "30/30",
      "cost": 5.050805,
      "claim_role": "safety-gated replay, not cost-reduced"
    },
    "R267": {
      "official": "30/34",
      "audit_clean_exclude_59_139_228": "30/31",
      "correct_task114": "31/31",
      "exclude_task114": "30/30",
      "cost": 3.597409,
      "claim_role": "cost-reduced plus safety-gated replay"
    }
  },
  "recommended_main_text_claim": "official_plus_audit_clean_scope_limited",
  "recommended_wording": "Report official and audit-clean columns side by side. Use R065/R068 for the official improvement signal and R095/R267 for the safety/audit-clean interpretation. Do not claim broad transfer superiority."
}

```

### `experiment/mmlu/res_logs/mmlu_r321_paper_evidence_table_and_training_gate_summary.json`

```json
{
  "run_id": "R321",
  "title": "Paper evidence table and selector-training gate",
  "claim_boundary": "R321 translates the current results into paper-facing tables and freezes the next training gate. It permits a selector-training preflight, but does not permit training execution yet.",
  "no_api": true,
  "broad_api": false,
  "paper_main_results": [
    {
      "slice": "AQuA_audit_clean_tail31",
      "baseline": "28/31",
      "promptnode": "31/31",
      "delta_correct": 3,
      "fix_harm": "-",
      "paper_claim": "positive_clean_improvement",
      "note": "Audit-clean after excluding task_59/task_139/task_228."
    },
    {
      "slice": "AQuA_conservative_remove_114_tail30",
      "baseline": "28/30",
      "promptnode": "30/30",
      "delta_correct": 2,
      "fix_harm": "-",
      "paper_claim": "positive_under_boundary_label_removal",
      "note": "Sensitivity check if task_114 is treated as a boundary label case."
    },
    {
      "slice": "MMLU_STEM_main97",
      "baseline": "88/97",
      "promptnode": "95/97",
      "delta_correct": 7,
      "fix_harm": "7/0",
      "paper_claim": "positive_with_completed_controls",
      "note": "R306 keeps +7 correct over ARG after negative controls and ablations."
    },
    {
      "slice": "MMLU_nonSTEM40_safety_replay",
      "baseline": "37/40",
      "promptnode": "37/40",
      "delta_correct": 0,
      "fix_harm": "0/0",
      "paper_claim": "no_harm_boundary_only",
      "note": "Warning-only semantic nodes cannot be claimed as non-STEM improvement."
    },
    {
      "slice": "MMLU_nonSTEM40_raw_warning_override",
      "baseline": "37/40",
      "promptnode": "34/40",
      "delta_correct": -3,
      "fix_harm": "0/3",
      "paper_claim": "negative_transfer_limitation",
      "note": "This row belongs in limitations or appendix, not as a main positive result."
    }
  ],
  "paper_claim_draft": "PromptNode/PromptEdge graph organization improves audited AQuA tail and MMLU STEM while preserving a no-harm boundary on non-STEM after lifecycle safety replay.",
  "paper_claim_forbidden": [
    "Do not claim universal improvement across all multi-choice tasks.",
    "Do not present warning-only non-STEM nodes as answer-improving nodes.",
    "Do not hide the raw non-STEM negative transfer row."
  ],
  "ablation_summary": {
    "completed_count": 10,
    "priority_pending": [],
    "key_controls": [
      "remove_safety_gate",
      "remove_lifecycle_prune",
      "remove_promptedge_text",
      "remove_symbolic_verifier_family",
      "cost_matched_plain_requery"
    ]
  },
  "selector_training_gate": {
    "preflight_authorized": true,
    "execute_training_authorized": false,
    "reason_execution_blocked": "A prospective train/dev/test split and leakage check must be frozen before selector training can run.",
    "allowed_training_target": "Learn a graph-policy selector for PromptNode type, PromptEdge read/write/forward permission, and lifecycle action; do not train a direct answer predictor.",
    "required_features": [
      "arg_node_state_features",
      "promptnode_type_features",
      "promptedge_text_features",
      "read_write_forward_permission_features",
      "lifecycle_action_features",
      "budget_and_cost_features",
      "agreement_conflict_features"
    ],
    "forbidden_training_signals": [
      "ground_truth_answer_text",
      "label_audited_noisy_items",
      "warning_only_promptnode_override",
      "dataset_specific_task_id_rules",
      "posthoc_wrong_item_memorization"
    ],
    "minimum_success_criteria_for_execution": {
      "heldout_positive_slice": "Beat ARG on at least one clean held-out slice.",
      "transfer_boundary": "No significant harm on a non-STEM or non-formula multiple-choice split.",
      "cost_boundary": "Do not lose to cost-matched plain requery on the claimed positive slice.",
      "claim_boundary": "Keep broad general PromptNode claim disabled unless transfer becomes positive."
    },
    "current_claim_permissions": {
      "aqua_clean_improvement_allowed": true,
      "mmlu_stem_improvement_allowed": true,
      "mmlu_nonstem_no_harm_allowed": true,
      "mmlu_nonstem_improvement_allowed": false,
      "broad_general_promptnode_claim_allowed": false,
      "training_authorized": false,
      "sci_q2_ready": false
    }
  },
  "next_required_run": "R322_selector_training_preflight",
  "summary_json": "experiment/mmlu/res_logs/mmlu_r321_paper_evidence_table_and_training_gate_summary.json",
  "report_md": "experiment/mmlu/run_logs/mmlu_r321_paper_evidence_table_and_training_gate_report.md"
}

```

### `experiment/mmlu/res_logs/mmlu_r396_larger_mixed_nonmath_fresh_analysis_summary.json`

```json
{
  "run_id": "R396",
  "title": "Larger mixed nonmath fresh analysis and goal audit",
  "claim_boundary": "R396 analyzes R395 and performs the five-iteration goal audit for R391-R395. The larger mixed nonmath run supports no-harm transfer, but not positive gain.",
  "no_api": true,
  "broad_api": false,
  "records": 48,
  "arg_correct": 41,
  "hybrid_correct": 41,
  "delta_correct": 0,
  "arg_accuracy": 0.854167,
  "hybrid_accuracy": 0.854167,
  "candidate_label_count": 43,
  "gate_forward_count": 24,
  "fixes": 0,
  "harms": 0,
  "wrong_forward_count": 3,
  "missed_fix_count": 4,
  "candidate_correct_but_blocked_count": 1,
  "fix_task_ids": [],
  "harm_task_ids": [],
  "wrong_forward_task_ids": [
    "MMLU-nonstem-moral_disputes_test-24",
    "MMLU-nonstem-logical_fallacies_test-17",
    "MMLU-nonstem-logical_fallacies_test-18"
  ],
  "missed_fix_task_ids": [
    "MMLU-nonstem-sociology_test-23",
    "MMLU-nonstem-world_religions_test-21",
    "MMLU-nonstem-philosophy_test-25",
    "MMLU-nonstem-business_ethics_test-19"
  ],
  "candidate_correct_but_blocked_task_ids": [
    "MMLU-nonstem-philosophy_test-25"
  ],
  "subject_breakdown": {
    "business_ethics": {
      "records": 6,
      "arg_correct": 5,
      "hybrid_correct": 5,
      "fixes": 0,
      "harms": 0,
      "wrong_forward": 0,
      "delta": 0
    },
    "high_school_government_and_politics": {
      "records": 6,
      "arg_correct": 6,
      "hybrid_correct": 6,
      "fixes": 0,
      "harms": 0,
      "wrong_forward": 0,
      "delta": 0
    },
    "high_school_world_history": {
      "records": 6,
      "arg_correct": 6,
      "hybrid_correct": 6,
      "fixes": 0,
      "harms": 0,
      "wrong_forward": 0,
      "delta": 0
    },
    "logical_fallacies": {
      "records": 6,
      "arg_correct": 4,
      "hybrid_correct": 4,
      "fixes": 0,
      "harms": 0,
      "wrong_forward": 2,
      "delta": 0
    },
    "moral_disputes": {
      "records": 6,
      "arg_correct": 5,
      "hybrid_correct": 5,
      "fixes": 0,
      "harms": 0,
      "wrong_forward": 1,
      "delta": 0
    },
    "philosophy": {
      "records": 6,
      "arg_correct": 5,
      "hybrid_correct": 5,
      "fixes": 0,
      "harms": 0,
      "wrong_forward": 0,
      "delta": 0
    },
    "sociology": {
      "records": 6,
      "arg_correct": 5,
      "hybrid_correct": 5,
      "fixes": 0,
      "harms": 0,
      "wrong_forward": 0,
      "delta": 0
    },
    "world_religions": {
      "records": 6,
      "arg_correct": 5,
      "hybrid_correct": 5,
      "fixes": 0,
      "harms": 0,
      "wrong_forward": 0,
      "delta": 0
    }
  },
  "candidate_type_counts": {
    "Option": 17,
    "multiple-choice": 7,
    "option": 8,
    "option_binding_promptedge": 9,
    "single": 3,
    "single-choice": 4
  },
  "iterations_since_last_goal_check": [
    "R391",
    "R392",
    "R393",
    "R394",
    "R395"
  ],
  "goal_alignment": {
    "still_aligned_with_sci_q2_goal": true,
    "larger_mixed_no_harm": true,
    "larger_mixed_positive": false,
    "error_taxonomy_required": true,
    "overclaiming_blocked": true
  },
  "claim_permissions": {
    "larger_mixed_no_harm_claim_allowed": true,
    "positive_mixed_nonmath_claim_allowed": false,
    "error_taxonomy_allowed_next": true,
    "api_execution_allowed_now": false,
    "main_paper_claim_allowed": false,
    "sci_q2_ready": false
  },
  "api_cost": 0.26203,
  "prompt_tokens": 21086,
  "completion_tokens": 10440,
  "paper_claim_authorized": false,
  "sci_q2_ready": false,
  "next_required_run": "R397_larger_mixed_error_taxonomy",
  "summary_json": "experiment/mmlu/res_logs/mmlu_r396_larger_mixed_nonmath_fresh_analysis_summary.json",
  "report_md": "experiment/mmlu/run_logs/mmlu_r396_larger_mixed_nonmath_fresh_analysis_report.md"
}

```

### `experiment/mmlu/res_logs/mmlu_r414_definition_challenge_gate_analysis_summary.json`

```json
{
  "run_id": "R414",
  "title": "DefinitionChallenge gate analysis",
  "claim_boundary": "R414 analyzes a fresh targeted nonmath split. It supports only a narrow DefinitionChallenge positive/no-harm claim; it does not support broad nonmath generalization.",
  "no_api": true,
  "broad_api": false,
  "records": 24,
  "arg_correct": 21,
  "hybrid_correct": 22,
  "candidate_correct": 21,
  "delta_correct": 1,
  "candidate_pool_delta": 0,
  "arg_accuracy": 0.875,
  "hybrid_accuracy": 0.916667,
  "candidate_accuracy": 0.875,
  "gate_forward_count": 11,
  "fixes": 1,
  "harms": 0,
  "wrong_forward_count": 0,
  "fix_task_ids": [
    "MMLU-nonstem-moral_disputes_test-14"
  ],
  "harm_task_ids": [],
  "wrong_forward_task_ids": [],
  "candidate_oracle_fix_task_ids": [
    "MMLU-nonstem-moral_disputes_test-14"
  ],
  "candidate_oracle_harm_task_ids": [
    "MMLU-nonstem-logical_fallacies_test-12"
  ],
  "selection_contribution": {
    "gate_improves_over_arg": true,
    "gate_improves_over_candidate_pool": true,
    "candidate_pool_alone_not_better_than_arg": true,
    "pruned_candidate_harms": 1,
    "pruned_candidate_harm_task_ids": [
      "MMLU-nonstem-logical_fallacies_test-12"
    ]
  },
  "subject_breakdown": {
    "logical_fallacies": {
      "records": 8,
      "arg_correct": 7,
      "candidate_correct": 6,
      "hybrid_correct": 7,
      "delta_correct": 0,
      "gate_forward_count": 2,
      "fixes": 0,
      "harms": 0,
      "wrong_forward_count": 0
    },
    "moral_disputes": {
      "records": 8,
      "arg_correct": 6,
      "candidate_correct": 7,
      "hybrid_correct": 7,
      "delta_correct": 1,
      "gate_forward_count": 4,
      "fixes": 1,
      "harms": 0,
      "wrong_forward_count": 0
    },
    "philosophy": {
      "records": 8,
      "arg_correct": 8,
      "candidate_correct": 8,
      "hybrid_correct": 8,
      "delta_correct": 0,
      "gate_forward_count": 5,
      "fixes": 0,
      "harms": 0,
      "wrong_forward_count": 0
    }
  },
  "gate_block_reason_counts": {
    "low_node_agreement": 13,
    "weak_definition_anchor": 13,
    "adversarial_challenge_failed": 13,
    "small_distractor_margin": 13,
    "option_binding_contract_failed": 13,
    "weak_memory_bridge": 13
  },
  "claim_permissions": {
    "narrow_definition_challenge_claim_allowed": true,
    "broad_nonmath_claim_allowed": false,
    "main_paper_claim_allowed": false,
    "needs_external_integrity_audit": true,
    "sci_q2_ready": false
  },
  "paper_claim_authorized": false,
  "sci_q2_ready": false,
  "next_required_run": "R415_update_claim_matrix_after_nonmath_positive",
  "input_jsonl": "experiment/mmlu/run_logs/mmlu_r413_definition_challenge_gate_api_results.jsonl",
  "summary_json": "experiment/mmlu/res_logs/mmlu_r414_definition_challenge_gate_analysis_summary.json",
  "report_md": "experiment/mmlu/run_logs/mmlu_r414_definition_challenge_gate_analysis_report.md"
}

```

### `experiment/mmlu/res_logs/mmlu_r419_lifecycle_trace_replay_summary.json`

```json
{
  "run_id": "R419",
  "title": "Lifecycle trace replay",
  "claim_boundary": "R419 replays existing R413 outputs into lifecycle events. It supports case-study visualization, not new accuracy claims.",
  "no_api": true,
  "broad_api": false,
  "source_jsonl": "experiment/mmlu/run_logs/mmlu_r413_definition_challenge_gate_api_results.jsonl",
  "source_records": 24,
  "events": 121,
  "event_counts": {
    "PromptEdgeForward": 11,
    "PromptNodeCompress": 24,
    "PromptNodeMerge": 24,
    "PromptNodePrune": 13,
    "PromptNodeUpdate": 24,
    "PromptNodeUpgrade": 1,
    "PromptNodeWrite": 24
  },
  "forwarded_tasks": 11,
  "pruned_tasks": 13,
  "upgrade_task_ids": [
    "MMLU-nonstem-moral_disputes_test-14"
  ],
  "forward_task_ids": [
    "MMLU-nonstem-logical_fallacies_test-13",
    "MMLU-nonstem-logical_fallacies_test-23",
    "MMLU-nonstem-moral_disputes_test-12",
    "MMLU-nonstem-moral_disputes_test-13",
    "MMLU-nonstem-moral_disputes_test-14",
    "MMLU-nonstem-moral_disputes_test-15",
    "MMLU-nonstem-philosophy_test-15",
    "MMLU-nonstem-philosophy_test-16",
    "MMLU-nonstem-philosophy_test-27",
    "MMLU-nonstem-philosophy_test-28",
    "MMLU-nonstem-philosophy_test-29"
  ],
  "prune_task_ids": [
    "MMLU-nonstem-logical_fallacies_test-12",
    "MMLU-nonstem-logical_fallacies_test-14",
    "MMLU-nonstem-logical_fallacies_test-15",
    "MMLU-nonstem-logical_fallacies_test-16",
    "MMLU-nonstem-logical_fallacies_test-24",
    "MMLU-nonstem-logical_fallacies_test-25",
    "MMLU-nonstem-moral_disputes_test-16",
    "MMLU-nonstem-moral_disputes_test-27",
    "MMLU-nonstem-moral_disputes_test-28",
    "MMLU-nonstem-moral_disputes_test-29",
    "MMLU-nonstem-philosophy_test-12",
    "MMLU-nonstem-philosophy_test-13",
    "MMLU-nonstem-philosophy_test-14"
  ],
  "case_study_trace_available": true,
  "paper_claim_authorized": false,
  "sci_q2_ready": false,
  "next_required_run": "R420_paper_asset_table_refresh",
  "trace_jsonl": "experiment/mmlu/run_logs/mmlu_r419_lifecycle_trace_events.jsonl",
  "summary_json": "experiment/mmlu/res_logs/mmlu_r419_lifecycle_trace_replay_summary.json",
  "report_md": "experiment/mmlu/run_logs/mmlu_r419_lifecycle_trace_replay_report.md"
}

```

### `experiment/mmlu/res_logs/mmlu_r426_update_cost_table_with_stem_probe_and_goal_audit_summary.json`

```json
{
  "run_id": "R426",
  "title": "Update cost table with STEM probe and goal audit",
  "claim_boundary": "R426 replaces the missing MMLU STEM cost row with a probe estimate. This improves draft completeness but does not make submission cost evidence exact or audited.",
  "no_api": true,
  "broad_api": false,
  "cost_rows": [
    {
      "id": "AQuA_ARG_baseline",
      "slice": "AQuA_tail34_official",
      "score": "28/34",
      "accuracy": 0.823529,
      "cost": 0.93285,
      "cost_per_task": 0.027437,
      "correct_per_cost": 30.015544,
      "accuracy_per_cost": 0.88281,
      "prompt_tokens": null,
      "completion_tokens": null,
      "fix_harm_wrong": "n/a",
      "source": "experiment/aqua/res_logs/aqua_tail34_r271_final_claim_table_summary.json",
      "role": "ARG baseline",
      "note": "AQuA replay cost from R271.",
      "cost_evidence": "direct_or_existing_summary"
    },
    {
      "id": "AQuA_R068_cost_reduced",
      "slice": "AQuA_tail34_official",
      "score": "31/34",
      "accuracy": 0.911765,
      "cost": 3.597409,
      "cost_per_task": 0.105806,
      "correct_per_cost": 8.617313,
      "accuracy_per_cost": 0.25345,
      "prompt_tokens": null,
      "completion_tokens": null,
      "fix_harm_wrong": "n/a",
      "source": "experiment/aqua/res_logs/aqua_tail34_r271_final_claim_table_summary.json",
      "role": "cost-reduced PromptNode replay",
      "note": "Retains R065 official score with lower multi-view cost.",
      "cost_evidence": "direct_or_existing_summary"
    },
    {
      "id": "AQuA_R267_safety_cost",
      "slice": "AQuA_tail34_audit_boundary",
      "score": "31/31",
      "accuracy": 1.0,
      "cost": 3.597409,
      "cost_per_task": 0.116045,
      "correct_per_cost": 8.617313,
      "accuracy_per_cost": 0.277978,
      "prompt_tokens": null,
      "completion_tokens": null,
      "fix_harm_wrong": "n/a",
      "source": "experiment/aqua/res_logs/aqua_tail34_r271_final_claim_table_summary.json",
      "role": "cost-reduced plus safety-gated replay",
      "note": "Audit-boundary interpretation; not the highest official score.",
      "cost_evidence": "direct_or_existing_summary"
    },
    {
      "id": "MMLU_STEM_R306_probe_estimate",
      "slice": "MMLU_STEM_main97",
      "score": "95/97",
      "accuracy": 0.979381,
      "cost": 0.676454,
      "cost_per_task": 0.006974,
      "correct_per_cost": 140.438226,
      "accuracy_per_cost": 1.447816,
      "prompt_tokens": null,
      "completion_tokens": null,
      "fix_harm_wrong": "2/0/n/a",
      "source": "experiment/mmlu/res_logs/mmlu_r425_analyze_mmlu_stem_cost_probe_summary.json",
      "role": "MMLU STEM positive result with probe-estimated cost",
      "note": "Cost is extrapolated from R424 12-task probe; not exact R306 accounting.",
      "cost_evidence": "probe_estimate_not_exact"
    },
    {
      "id": "MMLU_DefinitionChallenge_R413",
      "slice": "MMLU_definition_challenge_fresh24",
      "score": "22/24",
      "accuracy": 0.916667,
      "cost": 0.220095,
      "cost_per_task": 0.009171,
      "correct_per_cost": 99.956837,
      "accuracy_per_cost": 4.16487,
      "prompt_tokens": 13092,
      "completion_tokens": 10309,
      "fix_harm_wrong": "1/0/0",
      "source": "experiment/mmlu/res_logs/mmlu_r413_definition_challenge_gate_api_execution_summary.json",
      "role": "fresh targeted nonmath PromptNode/PromptEdge gate",
      "note": "Cost includes both ARG direct baseline and DefinitionChallenge candidate calls.",
      "cost_evidence": "direct_or_existing_summary"
    },
    {
      "id": "MMLU_plain_requery_R316",
      "slice": "MMLU_nonSTEM40_plain_requery_control",
      "score": "37/40",
      "accuracy": 0.925,
      "cost": 0.11794,
      "cost_per_task": 0.002949,
      "correct_per_cost": 313.71884,
      "accuracy_per_cost": 7.842971,
      "prompt_tokens": null,
      "completion_tokens": null,
      "fix_harm_wrong": "1/1/n/a",
      "source": "experiment/mmlu/res_logs/mmlu_r316_promptedge_cost_controls_summary.json",
      "role": "cost-matched plain requery control",
      "note": "Approximate half of R316 total API cost, because node-only and plain-requery each made 40 API calls.",
      "cost_evidence": "direct_or_existing_summary"
    }
  ],
  "missing_cost_evidence": [
    "independent_integrity_audit_missing"
  ],
  "cost_table_complete_for_draft": true,
  "cost_table_complete_for_submission": false,
  "iterations_since_last_goal_check": [
    "R422",
    "R423",
    "R424",
    "R425",
    "R426"
  ],
  "goal_alignment": {
    "still_aligned_with_sci_q2_goal": true,
    "arg_designer_remains_main_baseline": true,
    "promptnode_first_class_boundary_preserved": true,
    "mmlu_stem_cost_gap_reduced": true,
    "estimate_not_misrepresented_as_exact": true,
    "external_audit_still_required": true,
    "overclaiming_blocked": true
  },
  "claim_permissions": {
    "cost_table_for_draft_allowed": true,
    "cost_table_for_submission_allowed": false,
    "main_paper_claim_allowed": false,
    "sci_q2_ready": false
  },
  "paper_claim_authorized": false,
  "sci_q2_ready": false,
  "next_required_run": "R427_external_integrity_audit_refresh",
  "summary_json": "experiment/mmlu/res_logs/mmlu_r426_update_cost_table_with_stem_probe_and_goal_audit_summary.json",
  "report_md": "experiment/mmlu/run_logs/mmlu_r426_update_cost_table_with_stem_probe_and_goal_audit_report.md"
}

```

### `experiment/mmlu/res_logs/mmlu_r440_paper_claim_number_static_audit_summary.json`

```json
{
  "run_id": "R440",
  "title": "Paper claim number static audit",
  "claim_boundary": "R440 checks paper numbers against known result files deterministically. It does not replace a fresh zero-context paper-claim audit.",
  "no_api": true,
  "broad_api": false,
  "claim_count": 20,
  "verified_claims": [
    {
      "id": "aqua_arg_clean",
      "paper_pattern": "28/31",
      "evidence_value": "28/31"
    },
    {
      "id": "aqua_pn_clean",
      "paper_pattern": "31/31",
      "evidence_value": "31/31"
    },
    {
      "id": "aqua_arg_tail30",
      "paper_pattern": "28/30",
      "evidence_value": "28/30"
    },
    {
      "id": "aqua_pn_tail30",
      "paper_pattern": "30/30",
      "evidence_value": "30/30"
    },
    {
      "id": "mmlu_stem_arg",
      "paper_pattern": "88/97",
      "evidence_value": "88/97"
    },
    {
      "id": "mmlu_stem_pn",
      "paper_pattern": "95/97",
      "evidence_value": "95/97"
    },
    {
      "id": "mmlu_stem_fix_harm",
      "paper_pattern": "7/0",
      "evidence_value": "7/0"
    },
    {
      "id": "mmlu_stem_cost",
      "paper_pattern": "0.676454",
      "evidence_value": "0.676454"
    },
    {
      "id": "mixed_arg",
      "paper_pattern": "41/48",
      "evidence_value": "41/48"
    },
    {
      "id": "mixed_hybrid",
      "paper_pattern": "41/48",
      "evidence_value": "41/48"
    },
    {
      "id": "definition_arg",
      "paper_pattern": "21/24",
      "evidence_value": "21/24"
    },
    {
      "id": "definition_hybrid",
      "paper_pattern": "22/24",
      "evidence_value": "22/24"
    },
    {
      "id": "definition_candidate",
      "paper_pattern": "21/24",
      "evidence_value": "21/24"
    },
    {
      "id": "definition_fix_harm_wrong",
      "paper_pattern": "1/0/0",
      "evidence_value": "1/0/0"
    },
    {
      "id": "plain_requery_score",
      "paper_pattern": "37/40",
      "evidence_value": "37/40"
    },
    {
      "id": "plain_requery_fix_harm",
      "paper_pattern": "1/1",
      "evidence_value": "1/1"
    },
    {
      "id": "lifecycle_events",
      "paper_pattern": "121",
      "evidence_value": "121"
    },
    {
      "id": "lifecycle_forward",
      "paper_pattern": "11 forward",
      "evidence_value": "11"
    },
    {
      "id": "lifecycle_prune",
      "paper_pattern": "13 prune",
      "evidence_value": "13"
    },
    {
      "id": "lifecycle_upgrade",
      "paper_pattern": "one upgrade",
      "evidence_value": "1"
    }
  ],
  "mismatches": [],
  "unsupported_claims": [],
  "static_number_audit_pass": true,
  "external_paper_claim_audit_required": true,
  "paper_claim_authorized": false,
  "sci_q2_ready": false,
  "next_required_run": "R441_external_audit_package_refresh",
  "summary_json": "experiment/mmlu/res_logs/mmlu_r440_paper_claim_number_static_audit_summary.json",
  "report_md": "experiment/mmlu/run_logs/mmlu_r440_paper_claim_number_static_audit_report.md"
}

```
