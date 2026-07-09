import re
from typing import Any, Dict, Optional

from mas_framework.agents.agent_registry import AgentRegistry
from mas_framework.graph.node import Node
from mas_framework.llm.llm_registry import LLMRegistry


def _compact(text: Any, limit: int = 1200) -> str:
    value = re.sub(r"\s+", " ", str(text or "")).strip()
    if len(value) <= limit:
        return value
    return value[: limit - 20].rstrip() + " ...[truncated]"


def _extract_multiple_choice_options(task: str) -> Dict[str, str]:
    if "Choices:" in task:
        task = task.split("Choices:", 1)[1]
    pattern = re.compile(
        r"(?:^|\n|\r|\s)(?:Option\s+)?([A-E])\s*[\):.]\s*(.*?)(?=(?:\n|\r|\s)(?:Option\s+)?[A-E]\s*[\):.]|$)",
        flags=re.I | re.S,
    )
    matches = pattern.finditer(task)
    return {
        m.group(1).upper(): re.sub(r"\s+", " ", m.group(2)).strip()
        for m in matches
    }


def _format_options(options: Dict[str, str]) -> str:
    if not options:
        return "- no parsed A-E choices"
    return "\n".join(f"{label}) {text}" for label, text in options.items())


@AgentRegistry.register("PromptNode")
class PromptNode(Node):
    """Lightweight virtual node for graph organization, not answer solving."""

    def __init__(
        self,
        id: Optional[str] = None,
        role: str = "PN_Memory",
        domain: str = "",
        llm_name: str = "",
        constraint: Optional[str] = None,
    ):
        super().__init__(id, "PromptNode", domain, llm_name)
        self.role = role
        self.constraint = constraint or ""
        self.llm = None if llm_name == "mock" else LLMRegistry.get(llm_name)
        self.trace: Dict[str, Any] = {}

    def _system_prompt(self) -> str:
        common = (
            "You are a virtual Prompt Node inside a multi-agent graph. "
            "You organize, verify, or route evidence. You are not a standalone solver. "
            "Do not use hidden labels, row ids, memorized answers, or nearest-choice rescue."
        )
        if self.role == "PN_Verifier":
            return (
                common
                + " Produce a structured audit of target preservation and option binding. "
                "Do not output a final A-E answer unless it is already supported by upstream evidence."
            )
        if self.role == "PN_Router":
            return (
                common
                + " Forward only target-preserved, option-bound evidence and suppress unsupported labels."
            )
        return common + " Build an evidence ledger without solving from scratch."

    def _role_contract(self, options: Dict[str, str]) -> str:
        option_labels = sorted(label for label in options if re.match(r"^[A-Z]$", label))
        label_list = "/".join(option_labels) if option_labels else "A/B/C/D/E"
        label_or_none = f"{label_list}/NONE"
        if self.role == "PN_Verifier":
            return (
                "instruction:\n"
                "TARGET_AUDIT: restate the exact target quantity/event from the task and note any shifted-target evidence.\n"
                "CANDIDATE_AUDIT: extract each upstream candidate label, computed value, formula, and stated rationale.\n"
                "OPTION_BINDING_AUDIT: compare every candidate value or formula against the parsed choices below; "
                "mark EXACT_MATCH, EQUIVALENT_FORM, NO_EXACT_OPTION, or UNSUPPORTED_LABEL.\n"
                "NO_NEAREST_OPTION_RESCUE: if a computed value is not exactly/equivalently present, do not endorse the nearest label.\n"
                "REPAIR_CANDIDATE_AUDIT: if NO_EXACT_OPTION occurs, assess whether a label-noise repair is plausible. "
                "Report repair_option, repair_binding_status, repair_confidence, repair_distance_ratio, and repair_reason. "
                "Allowed repair_binding_status values are NUMERIC_NEAREST_WITH_TYPO_CHECK, NUMERIC_TYPO_REPAIR, "
                "or SYMBOLIC_EQUIVALENCE_REPAIR; never use EXACT_MATCH or EQUIVALENT_FORM as repair_binding_status. "
                "Use repair_option=NONE when evidence is weak. This is only an auditable edge prompt; "
                "do not convert repair into final A-E support.\n"
                "CONFLICT_AUDIT: identify contradictions between labels, values, and target conditions.\n"
                "VERDICT: summarize which evidence should be trusted by the router and which labels should be suppressed."
            )
        if self.role == "PN_Router":
            return (
                "instruction:\n"
                "ROUTE_VERIFIED_EVIDENCE: forward only evidence that passed target and option-binding checks.\n"
                "SUPPRESS_UNSUPPORTED_LABELS: block nearest-only choices, shifted targets, and labels not supported by their own derivation.\n"
                "PARTIAL_OVERLAP_IS_NOT_EXACT: if a computed interval/value only partially overlaps an option, exceeds an option bound, "
                "or contradicts the option text, do not mark EXACT_MATCH.\n"
                "TRUNCATED_VERIFIER_IS_WEAK: if verifier evidence is truncated, unresolved, or internally contradictory, "
                "emit SUPPORTED_OPTION: NONE with BINDING_STATUS: NO_EXACT_OPTION/CONFLICT instead of inventing support.\n"
                "Emit the following machine-readable contract before any explanation:\n"
                f"SUPPORTED_OPTION: {label_or_none}\n"
                "BINDING_STATUS: EXACT_MATCH/EQUIVALENT_FORM/NO_EXACT_OPTION/UNSUPPORTED_LABEL/CONFLICT\n"
                f"REPAIR_OPTION: {label_or_none}\n"
                "REPAIR_BINDING_STATUS: NONE/NUMERIC_NEAREST_WITH_TYPO_CHECK/NUMERIC_TYPO_REPAIR/SYMBOLIC_EQUIVALENCE_REPAIR\n"
                "REPAIR_CONFIDENCE: decimal between 0.00 and 1.00\n"
                "REPAIR_DISTANCE_RATIO: decimal distance normalized by computed magnitude or 1.0 when unavailable\n"
                "Only fill REPAIR_OPTION from an explicit verifier REPAIR_CANDIDATE_AUDIT; otherwise use "
                "REPAIR_OPTION: NONE, REPAIR_BINDING_STATUS: NONE, REPAIR_CONFIDENCE: 0.0, and REPAIR_DISTANCE_RATIO: 1.0.\n"
                f"REPAIR_FORWARDING_REQUIRED: if verifier evidence contains repair_option={label_list} with a repair_confidence "
                "and repair_distance_ratio, copy that repair candidate into REPAIR_OPTION, REPAIR_CONFIDENCE, and "
                "REPAIR_DISTANCE_RATIO unless there is an explicit contradiction. SUPPORTED_OPTION: NONE may coexist with "
                f"REPAIR_OPTION: {label_list}; do not reset repair fields to NONE merely because exact option binding is absent.\n"
                "When PARTIAL_OVERLAP_IS_NOT_EXACT or TRUNCATED_VERIFIER_IS_WEAK applies, use exactly "
                "SUPPORTED_OPTION: NONE and BINDING_STATUS: NO_EXACT_OPTION/CONFLICT.\n"
                "FINAL_EVIDENCE_SUMMARY: one compact sentence preserving the verified reasoning and uncertainty.\n"
                "ROUTER_SUMMARY: provide compact evidence for the final decision node without solving from scratch."
            )
        return (
            "instruction:\n"
            "MEMORY_LEDGER: store upstream source id, role, candidate label, computed value, formula, and uncertainty.\n"
            "TARGET_MEMORY: preserve the task target and parsed options for downstream verifier checks.\n"
            "Do not solve from scratch or invent new facts."
        )

    def _format_evidence(
        self,
        raw_inputs: Dict[str, str],
        spatial_info: Dict[str, Dict],
        temporal_info: Dict[str, Dict],
    ) -> str:
        evidence_lines = []
        for source, info in {**spatial_info, **temporal_info}.items():
            evidence_lines.append(
                f"- source={source}; role={info.get('role', 'Unknown')}; "
                f"output={_compact(info.get('output', ''))}"
            )
        if not evidence_lines:
            evidence_lines.append("- no upstream evidence")

        task = _compact(raw_inputs.get("task", ""))
        options = _extract_multiple_choice_options(raw_inputs.get("task", ""))
        return (
            f"VIRTUAL PROMPT NODE\n"
            f"role: {self.role}\n"
            f"task: {task}\n"
            f"parsed_choices:\n{_format_options(options)}\n"
            f"evidence:\n" + "\n".join(evidence_lines) + "\n"
            f"{self._role_contract(options)}"
        )

    def _process_inputs(
        self,
        raw_inputs: Dict[str, str],
        spatial_info: Dict[str, Dict],
        temporal_info: Dict[str, Dict],
        **kwargs,
    ):
        evidence = self._format_evidence(raw_inputs, spatial_info, temporal_info)
        system_prompt = self._system_prompt()
        user_prompt = evidence
        self.trace = {
            "role": self.role,
            "num_spatial_inputs": len(spatial_info),
            "num_temporal_inputs": len(temporal_info),
            "used_llm": self.llm is not None,
        }
        return system_prompt, user_prompt

    def _execute(
        self,
        input: Dict[str, str],
        spatial_info: Dict[str, Any],
        temporal_info: Dict[str, Any],
        **kwargs,
    ):
        system_prompt, user_prompt = self._process_inputs(
            input, spatial_info, temporal_info, **kwargs
        )
        if self.llm is None:
            return user_prompt
        message = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        return self.llm.gen(message, max_tokens=850, temperature=0.0)

    async def _async_execute(
        self,
        input: Dict[str, str],
        spatial_info: Dict[str, Any],
        temporal_info: Dict[str, Any],
        **kwargs,
    ):
        system_prompt, user_prompt = self._process_inputs(
            input, spatial_info, temporal_info, **kwargs
        )
        if self.llm is None:
            return user_prompt
        message = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        return await self.llm.agen(message, max_tokens=850, temperature=0.0)
