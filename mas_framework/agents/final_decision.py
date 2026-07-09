import re
from collections import Counter
from typing import List, Any, Dict, Optional

from mas_framework.graph.node import Node
from mas_framework.agents.agent_registry import AgentRegistry
from mas_framework.llm.llm_registry import LLMRegistry
from mas_framework.prompt.prompt_set_registry import PromptSetRegistry
from mas_framework.tools.coding.python_executor import PyExecutor

@AgentRegistry.register('FinalWriteCode')
class FinalWriteCode(Node):
    def __init__(self, id: Optional[str] =None, domain: str = "", llm_name: str = "", ):
        super().__init__(id, "FinalWriteCode" ,domain, llm_name)
        self.llm = LLMRegistry.get(llm_name)
        self.prompt_set = PromptSetRegistry.get(domain)

    def extract_example(self, prompt: str) -> list:
        prompt = prompt['task']
        lines = (line.strip() for line in prompt.split('\n') if line.strip())

        results = []
        lines_iter = iter(lines)
        for line in lines_iter:
            if line.startswith('>>>'):
                function_call = line[4:]
                expected_output = next(lines_iter, None)
                if expected_output:
                    results.append(f"assert {function_call} == {expected_output}")

        return results
    
    def _process_inputs(self, raw_inputs:Dict[str,str], spatial_info:Dict[str,Any], temporal_info:Dict[str,Any], **kwargs)->List[Any]:
        """ To be overriden by the descendant class """
        """ Process the raw_inputs(most of the time is a List[Dict]) """
        self.role = self.prompt_set.get_decision_role()
        self.constraint = self.prompt_set.get_decision_constraint()          
        system_prompt = f"{self.role}.\n {self.constraint}"
        spatial_str = ""
        for id, info in spatial_info.items():
            if info['output'].startswith("```python") and info['output'].endswith("```"):  # is python code
                self.internal_tests = self.extract_example(raw_inputs)
                output = info['output'].lstrip("```python\n").rstrip("\n```")
                is_solved, feedback, state = PyExecutor().execute(output, self.internal_tests, timeout=10)
                spatial_str += f"Agent {id} as a {info['role']}:\n\nThe code written by the agent is:\n\n{info['output']}\n\n Whether it passes internal testing? {is_solved}.\n\nThe feedback is:\n\n {feedback}.\n\n"
            else:
                spatial_str += f"Agent {id} as a {info['role']} provides the following info: {info['output']}\n\n"
        user_prompt = f"The task is:\n\n{raw_inputs['task']}.\n At the same time, the outputs and feedbacks of other agents are as follows:\n\n{spatial_str}\n\n"
        return system_prompt, user_prompt
                
    def _execute(self, input:Dict[str,str],  spatial_info:Dict[str,Any], temporal_info:Dict[str,Any],**kwargs):
        """ To be overriden by the descendant class """
        """ Use the processed input to get the result """
  
        system_prompt, user_prompt = self._process_inputs(input, spatial_info, temporal_info)
        message = [{'role':'system','content':system_prompt},{'role':'user','content':user_prompt}]
        response = self.llm.gen(message)
        return response
    
    async def _async_execute(self, input:Dict[str,str],  spatial_info:Dict[str,Any], temporal_info:Dict[str,Any],**kwargs):
        """ To be overriden by the descendant class """
        """ Use the processed input to get the result """
  
        system_prompt, user_prompt = self._process_inputs(input, spatial_info, temporal_info)
        message = [{'role':'system','content':system_prompt},{'role':'user','content':user_prompt}]
        response = await self.llm.agen(message)
        return response


@AgentRegistry.register('FinalRefer')
class FinalRefer(Node):
    def __init__(self, id: Optional[str] =None, domain: str = "", llm_name: str = "", ):
        super().__init__(id, "FinalRefer" ,domain, llm_name)
        self.llm = LLMRegistry.get(llm_name)
        self.prompt_set = PromptSetRegistry.get(domain)

    def _process_inputs(self, raw_inputs:Dict[str,str], spatial_info:Dict[str,Any], temporal_info:Dict[str,Any], **kwargs)->List[Any]:
        """ To be overriden by the descendant class """
        """ Process the raw_inputs(most of the time is a List[Dict]) """
        self.role = self.prompt_set.get_decision_role()
        self.constraint = self.prompt_set.get_decision_constraint()          
        system_prompt = f"{self.role}.\n {self.constraint}"
        
        spatial_str = ""
        for id, info in spatial_info.items():
            spatial_str += id + ": " + info['output'] + "\n\n"
        decision_few_shot = self.prompt_set.get_decision_few_shot()
        user_prompt = f"{decision_few_shot} The task is:\n\n {raw_inputs['task']}.\n At the same time, the output of other agents is as follows:\n\n{spatial_str}"
        return system_prompt, user_prompt
                
    def _execute(self, input:Dict[str,str],  spatial_info:Dict[str,Any], temporal_info:Dict[str,Any],**kwargs):
        """ To be overriden by the descendant class """
        """ Use the processed input to get the result """
  
        system_prompt, user_prompt = self._process_inputs(input, spatial_info, temporal_info)
        message = [{'role':'system','content':system_prompt},{'role':'user','content':user_prompt}]
        response = self.llm.gen(message)
        return response
    
    async def _async_execute(self, input:Dict[str,str],  spatial_info:Dict[str,Any], temporal_info:Dict[str,Any],**kwargs):
        """ To be overriden by the descendant class """
        """ Use the processed input to get the result """
  
        system_prompt, user_prompt = self._process_inputs(input, spatial_info, temporal_info)
        message = [{'role':'system','content':system_prompt},{'role':'user','content':user_prompt}]
        response = await self.llm.agen(message)
        # print(f"################system prompt:{system_prompt}")
        # print(f"################user prompt:{user_prompt}")
        # print(f"################response:{response}")
        return response

def _extract_multiple_choice_options(task: str) -> Dict[str, str]:
    if "Choices:" in task:
        task = task.split("Choices:", 1)[1]
    matches = re.finditer(r"([A-E])\)\s*(.*?)(?=\s+[A-E]\)|$)", task, flags=re.S)
    return {m.group(1): re.sub(r"\s+", " ", m.group(2)).strip() for m in matches}


def _compact_text(text: str, limit: int = 1800) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 20].rstrip() + " ...[truncated]"


def _extract_contract_field(text: str, field: str) -> str:
    match = re.search(rf"^{field}:\s*(.+)$", text or "", flags=re.I | re.M)
    return re.sub(r"\s+", " ", match.group(1)).strip() if match else ""


def _extract_final_option(text: str) -> Optional[str]:
    matches = re.findall(r"\bthe\s+answer\s+is\s+([A-E])\b", text or "", flags=re.I)
    if not matches:
        return None
    return matches[-1].upper()


def extract_router_contracts(spatial_info: Dict[str, Any]) -> List[Dict[str, str]]:
    contracts = []
    for node_id, info in spatial_info.items():
        output = info.get("output", "")
        if info.get("role") != "PN_Router" and "SUPPORTED_OPTION:" not in output:
            continue
        supported_option = _extract_contract_field(output, "SUPPORTED_OPTION").upper()
        binding_status = _extract_contract_field(output, "BINDING_STATUS").upper()
        evidence_summary = _extract_contract_field(output, "FINAL_EVIDENCE_SUMMARY")
        if not any([supported_option, binding_status, evidence_summary]):
            continue
        contracts.append({
            "node_id": node_id,
            "role": info.get("role", ""),
            "supported_option": supported_option,
            "binding_status": binding_status,
            "final_evidence_summary": evidence_summary,
            "raw_output": output,
        })
    return contracts


EDGE_REPAIR_MIN_CONFIDENCE = 0.8
EDGE_REPAIR_MAX_DISTANCE_RATIO = 0.001
EDGE_REPAIR_ALLOWED_STATUSES = {
    "NUMERIC_NEAREST_WITH_TYPO_CHECK",
    "NUMERIC_TYPO_REPAIR",
    "SYMBOLIC_EQUIVALENCE_REPAIR",
}


def _safe_float(value: str, default: float = 0.0) -> float:
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return default


def extract_edge_prompt_repair_candidates(spatial_info: Dict[str, Any]) -> List[Dict[str, Any]]:
    repairs = []
    for node_id, info in spatial_info.items():
        output = info.get("output", "")
        if info.get("role") != "PN_Router" and "REPAIR_OPTION:" not in output:
            continue
        repair_option = _extract_contract_field(output, "REPAIR_OPTION").upper()
        repair_binding_status = _extract_contract_field(output, "REPAIR_BINDING_STATUS").upper()
        if not repair_option and not repair_binding_status:
            continue
        repairs.append(
            {
                "node_id": node_id,
                "role": info.get("role", ""),
                "supported_option": _extract_contract_field(output, "SUPPORTED_OPTION").upper(),
                "binding_status": _extract_contract_field(output, "BINDING_STATUS").upper(),
                "repair_option": repair_option,
                "repair_binding_status": repair_binding_status,
                "repair_confidence": _safe_float(
                    _extract_contract_field(output, "REPAIR_CONFIDENCE")
                ),
                "repair_distance_ratio": _safe_float(
                    _extract_contract_field(output, "REPAIR_DISTANCE_RATIO"),
                    default=1.0,
                ),
                "final_evidence_summary": _extract_contract_field(
                    output, "FINAL_EVIDENCE_SUMMARY"
                ),
                "raw_output": output,
            }
        )
    return repairs


@AgentRegistry.register('RouterContractFinalRefer')
class RouterContractFinalRefer(FinalRefer):
    """Final decision that consumes terminal PN_Router answer contracts."""

    def __init__(self, id: Optional[str] = None, domain: str = "", llm_name: str = ""):
        Node.__init__(self, id, "RouterContractFinalRefer", domain, llm_name)
        self.agent_name = "RouterContractFinalRefer"
        self.llm = None if llm_name == "mock" else LLMRegistry.get(llm_name)
        self.prompt_set = PromptSetRegistry.get(domain)

    def _process_inputs(self, raw_inputs: Dict[str, str], spatial_info: Dict[str, Any],
                        temporal_info: Dict[str, Any], **kwargs) -> List[Any]:
        contracts = extract_router_contracts(spatial_info)
        if not contracts:
            return FinalRefer._process_inputs(self, raw_inputs, spatial_info, temporal_info, **kwargs)

        task = raw_inputs["task"]
        options = _extract_multiple_choice_options(task)
        option_lines = "\n".join(f"{k}) {v}" for k, v in options.items())
        contract_lines = []
        for idx, contract in enumerate(contracts, start=1):
            contract_lines.append(
                f"[router_contract_{idx}]\n"
                f"SUPPORTED_OPTION: {contract['supported_option']}\n"
                f"BINDING_STATUS: {contract['binding_status']}\n"
                f"FINAL_EVIDENCE_SUMMARY: {contract['final_evidence_summary']}\n"
                f"RAW_ROUTER_OUTPUT: {_compact_text(contract['raw_output'], 1600)}"
            )

        system_prompt = (
            "You are the final decision node for a multiple-choice task. "
            "Use terminal PN_Router contracts as the authoritative graph evidence. "
            "A supported A-E option with EXACT_MATCH or EQUIVALENT_FORM binding is strong evidence. "
            "NO_EXACT_OPTION, UNSUPPORTED_LABEL, and CONFLICT are weak evidence and must not be converted "
            "into a nearest-choice answer. Do not use hidden labels, row ids, memorized answers, or task-specific patches. "
            "The last line must be exactly: The answer is X"
        )
        user_prompt = (
            f"Task:\n{task}\n\n"
            f"Choices:\n{option_lines}\n\n"
            "Terminal router contracts:\n"
            + "\n\n".join(contract_lines)
            + "\n\n"
            "Select the best-supported listed option from the contracts. "
            "If the contract says NONE or has weak binding, explain the uncertainty briefly and still choose the "
            "best-supported A-E option from the available evidence without nearest-option rescue."
        )
        return system_prompt, user_prompt

    def _execute(self, input: Dict[str, str], spatial_info: Dict[str, Any],
                 temporal_info: Dict[str, Any], **kwargs):
        system_prompt, user_prompt = self._process_inputs(input, spatial_info, temporal_info, **kwargs)
        if self.llm is None:
            return user_prompt
        message = [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': user_prompt}]
        return self.llm.gen(message)

    async def _async_execute(self, input: Dict[str, str], spatial_info: Dict[str, Any],
                             temporal_info: Dict[str, Any], **kwargs):
        system_prompt, user_prompt = self._process_inputs(input, spatial_info, temporal_info, **kwargs)
        if self.llm is None:
            return user_prompt
        message = [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': user_prompt}]
        return await self.llm.agen(message)


def _is_strong_router_contract(contract: Dict[str, str]) -> bool:
    return (
        contract.get("supported_option", "").upper() in {"A", "B", "C", "D", "E"}
        and contract.get("binding_status", "").upper() in {"EXACT_MATCH", "EQUIVALENT_FORM", "EQUIVALENT"}
    )


def _non_prompt_node_spatial_info(spatial_info: Dict[str, Any]) -> Dict[str, Any]:
    filtered = {
        node_id: info
        for node_id, info in spatial_info.items()
        if not str(info.get("role", "")).startswith("PN_")
    }
    return filtered or spatial_info


def extract_direct_option_votes(spatial_info: Dict[str, Any]) -> List[str]:
    votes = []
    for info in spatial_info.values():
        if str(info.get("role", "")).startswith("PN_"):
            continue
        option = _extract_final_option(info.get("output", ""))
        if option:
            votes.append(option)
    return votes


def summarize_pn_utility_features(spatial_info: Dict[str, Any]) -> Dict[str, Any]:
    direct_votes = extract_direct_option_votes(spatial_info)
    vote_counts = Counter(direct_votes)
    if vote_counts:
        direct_majority_option, direct_majority_count = vote_counts.most_common(1)[0]
    else:
        direct_majority_option, direct_majority_count = None, 0

    router_contracts = extract_router_contracts(spatial_info)
    strong_contracts = [contract for contract in router_contracts if _is_strong_router_contract(contract)]
    strong_router_options = []
    for contract in strong_contracts:
        option = contract.get("supported_option", "").upper()
        if option not in strong_router_options:
            strong_router_options.append(option)

    return {
        "direct_votes": direct_votes,
        "direct_vote_counts": dict(vote_counts),
        "direct_valid_vote_count": len(direct_votes),
        "direct_majority_option": direct_majority_option,
        "direct_majority_count": direct_majority_count,
        "router_contract_count": len(router_contracts),
        "strong_router_options": strong_router_options,
        "all_router_contracts_weak": bool(router_contracts) and not strong_contracts,
        "strong_router_conflicts_with_direct_majority": (
            direct_majority_count >= 2
            and bool(strong_router_options)
            and direct_majority_option not in strong_router_options
        ),
    }


def select_calibrated_pn_utility_answer(spatial_info: Dict[str, Any]) -> Optional[str]:
    features = summarize_pn_utility_features(spatial_info)
    direct_majority = features["direct_majority_option"]
    direct_majority_count = features["direct_majority_count"]
    strong_router_options = features["strong_router_options"]

    if direct_majority_count >= 2 and features["all_router_contracts_weak"]:
        return direct_majority
    if direct_majority_count >= 2 and features["strong_router_conflicts_with_direct_majority"]:
        return direct_majority
    if features["direct_valid_vote_count"] == 0 and len(strong_router_options) == 1:
        return strong_router_options[0]
    return None


DETERMINISTIC_ABSTAIN = "__ABSTAIN__"


def select_deterministic_router_answer(spatial_info: Dict[str, Any]) -> Optional[str]:
    features = summarize_pn_utility_features(spatial_info)
    direct_majority = features["direct_majority_option"]
    direct_majority_count = features["direct_majority_count"]
    strong_router_options = features["strong_router_options"]

    if len(strong_router_options) == 1:
        return strong_router_options[0]
    if features["all_router_contracts_weak"]:
        if direct_majority_count >= 2 and direct_majority:
            return direct_majority
        return DETERMINISTIC_ABSTAIN
    return None


def _is_valid_repair_candidate(candidate: Dict[str, Any], spatial_info: Dict[str, Any]) -> bool:
    repair_option = candidate.get("repair_option", "").upper()
    repair_status = candidate.get("repair_binding_status", "").upper()
    binding_status = candidate.get("binding_status", "").upper()
    supported_option = candidate.get("supported_option", "").upper()
    if repair_option not in {"A", "B", "C", "D", "E"}:
        return False
    if supported_option != "NONE":
        return False
    if "NO_EXACT_OPTION" not in binding_status:
        return False
    if repair_status not in EDGE_REPAIR_ALLOWED_STATUSES:
        return False
    if float(candidate.get("repair_confidence") or 0.0) < EDGE_REPAIR_MIN_CONFIDENCE:
        return False
    if _safe_float(candidate.get("repair_distance_ratio"), default=1.0) > EDGE_REPAIR_MAX_DISTANCE_RATIO:
        return False

    features = summarize_pn_utility_features(spatial_info)
    direct_majority = features["direct_majority_option"]
    direct_majority_count = features["direct_majority_count"]
    if direct_majority_count >= 2 and direct_majority and direct_majority != repair_option:
        return False
    return True


def select_edge_prompt_repair_answer(spatial_info: Dict[str, Any]) -> Optional[str]:
    candidates = extract_edge_prompt_repair_candidates(spatial_info)
    valid_options = []
    for candidate in candidates:
        if _is_valid_repair_candidate(candidate, spatial_info):
            option = candidate["repair_option"]
            if option not in valid_options:
                valid_options.append(option)
    if len(valid_options) == 1:
        return valid_options[0]
    return None


def calibrate_edge_prompt_repair_confidence(
    candidate: Dict[str, Any], spatial_info: Dict[str, Any]
) -> float:
    """Calibrate forwarded repair confidence from generic evidence-consistency features."""
    repair_status = candidate.get("repair_binding_status", "").upper()
    distance = _safe_float(candidate.get("repair_distance_ratio"), default=1.0)
    features = summarize_pn_utility_features(spatial_info)
    direct_majority = features["direct_majority_option"]
    direct_majority_count = features["direct_majority_count"]
    direct_contradiction = (
        direct_majority_count >= 2
        and direct_majority
        and direct_majority != candidate.get("repair_option", "").upper()
    )

    base_by_status = {
        "NUMERIC_NEAREST_WITH_TYPO_CHECK": 0.55,
        "NUMERIC_TYPO_REPAIR": 0.65,
        "SYMBOLIC_EQUIVALENCE_REPAIR": 0.70,
    }
    score = base_by_status.get(repair_status, 0.20)
    if distance <= 0.0001:
        score += 0.25
    elif distance <= EDGE_REPAIR_MAX_DISTANCE_RATIO:
        score += 0.15
    else:
        score -= 0.20
    # A candidate emitted by PN_Router with repair fields is treated as verifier-router agreement;
    # direct-majority contradiction remains a hard negative signal below.
    if candidate.get("role") == "PN_Router":
        score += 0.10
    else:
        score -= 0.25
    if candidate.get("repair_option", "").upper() in {"A", "B", "C", "D", "E"}:
        score += 0.05
    if direct_contradiction:
        score -= 0.60
    return round(max(0.0, min(1.0, score)), 6)


def _is_valid_calibrated_repair_candidate(
    candidate: Dict[str, Any], spatial_info: Dict[str, Any]
) -> bool:
    repair_option = candidate.get("repair_option", "").upper()
    repair_status = candidate.get("repair_binding_status", "").upper()
    binding_status = candidate.get("binding_status", "").upper()
    supported_option = candidate.get("supported_option", "").upper()
    if repair_option not in {"A", "B", "C", "D", "E"}:
        return False
    if supported_option != "NONE":
        return False
    if "NO_EXACT_OPTION" not in binding_status:
        return False
    if repair_status not in EDGE_REPAIR_ALLOWED_STATUSES:
        return False
    if _safe_float(candidate.get("repair_distance_ratio"), default=1.0) > EDGE_REPAIR_MAX_DISTANCE_RATIO:
        return False
    if calibrate_edge_prompt_repair_confidence(candidate, spatial_info) < EDGE_REPAIR_MIN_CONFIDENCE:
        return False

    features = summarize_pn_utility_features(spatial_info)
    direct_majority = features["direct_majority_option"]
    direct_majority_count = features["direct_majority_count"]
    if direct_majority_count >= 2 and direct_majority and direct_majority != repair_option:
        return False
    return True


def select_calibrated_edge_prompt_repair_answer(
    spatial_info: Dict[str, Any]
) -> Optional[str]:
    candidates = extract_edge_prompt_repair_candidates(spatial_info)
    valid_options = []
    for candidate in candidates:
        if _is_valid_calibrated_repair_candidate(candidate, spatial_info):
            option = candidate["repair_option"]
            if option not in valid_options:
                valid_options.append(option)
    if len(valid_options) == 1:
        return valid_options[0]
    return None


@AgentRegistry.register('ConservativeRouterContractFinalRefer')
class ConservativeRouterContractFinalRefer(RouterContractFinalRefer):
    """Router-contract final node that lets weak PromptNode evidence abstain."""

    def __init__(self, id: Optional[str] = None, domain: str = "", llm_name: str = ""):
        super().__init__(id, domain, llm_name)
        self.role = "ConservativeRouterContractFinalRefer"
        self.agent_name = "ConservativeRouterContractFinalRefer"

    def _process_inputs(self, raw_inputs: Dict[str, str], spatial_info: Dict[str, Any],
                        temporal_info: Dict[str, Any], **kwargs) -> List[Any]:
        contracts = extract_router_contracts(spatial_info)
        strong_contracts = [contract for contract in contracts if _is_strong_router_contract(contract)]
        if contracts and not strong_contracts:
            fallback_info = _non_prompt_node_spatial_info(spatial_info)
            system_prompt, user_prompt = FinalRefer._process_inputs(
                self, raw_inputs, fallback_info, temporal_info, **kwargs
            )
            system_prompt += (
                "\nPromptNode router contracts were available but all abstained or had weak option binding, "
                "so they were excluded from the final evidence. Do not infer an answer from missing or nearest-choice "
                "PromptNode evidence."
            )
            return system_prompt, user_prompt
        return RouterContractFinalRefer._process_inputs(self, raw_inputs, spatial_info, temporal_info, **kwargs)


@AgentRegistry.register('DeterministicRouterContractFinalRefer')
class DeterministicRouterContractFinalRefer(ConservativeRouterContractFinalRefer):
    """Final node with deterministic handling for strong and abstaining router contracts."""

    def __init__(self, id: Optional[str] = None, domain: str = "", llm_name: str = ""):
        super().__init__(id, domain, llm_name)
        self.role = "DeterministicRouterContractFinalRefer"
        self.agent_name = "DeterministicRouterContractFinalRefer"

    def _execute(self, input: Dict[str, str], spatial_info: Dict[str, Any],
                 temporal_info: Dict[str, Any], **kwargs):
        selected = select_deterministic_router_answer(spatial_info)
        if selected == DETERMINISTIC_ABSTAIN:
            return "no valid option is supported"
        if selected:
            return f"The answer is {selected}"
        return super()._execute(input, spatial_info, temporal_info, **kwargs)

    async def _async_execute(self, input: Dict[str, str], spatial_info: Dict[str, Any],
                             temporal_info: Dict[str, Any], **kwargs):
        selected = select_deterministic_router_answer(spatial_info)
        if selected == DETERMINISTIC_ABSTAIN:
            return "no valid option is supported"
        if selected:
            return f"The answer is {selected}"
        return await super()._async_execute(input, spatial_info, temporal_info, **kwargs)


@AgentRegistry.register('EdgePromptRepairContractFinalRefer')
class EdgePromptRepairContractFinalRefer(DeterministicRouterContractFinalRefer):
    """Final node that accepts only explicit edge-prompt repair contracts."""

    def __init__(self, id: Optional[str] = None, domain: str = "", llm_name: str = ""):
        super().__init__(id, domain, llm_name)
        self.role = "EdgePromptRepairContractFinalRefer"
        self.agent_name = "EdgePromptRepairContractFinalRefer"

    def _select_answer(self, spatial_info: Dict[str, Any]) -> Optional[str]:
        features = summarize_pn_utility_features(spatial_info)
        strong_router_options = features["strong_router_options"]
        if len(strong_router_options) == 1:
            return strong_router_options[0]
        repair_option = select_edge_prompt_repair_answer(spatial_info)
        if repair_option:
            return repair_option
        return select_deterministic_router_answer(spatial_info)

    def _execute(self, input: Dict[str, str], spatial_info: Dict[str, Any],
                 temporal_info: Dict[str, Any], **kwargs):
        selected = self._select_answer(spatial_info)
        if selected == DETERMINISTIC_ABSTAIN:
            return "no valid option is supported"
        if selected:
            return f"The answer is {selected}"
        return super()._execute(input, spatial_info, temporal_info, **kwargs)

    async def _async_execute(self, input: Dict[str, str], spatial_info: Dict[str, Any],
                             temporal_info: Dict[str, Any], **kwargs):
        selected = self._select_answer(spatial_info)
        if selected == DETERMINISTIC_ABSTAIN:
            return "no valid option is supported"
        if selected:
            return f"The answer is {selected}"
        return await super()._async_execute(input, spatial_info, temporal_info, **kwargs)


@AgentRegistry.register('CalibratedPNUtilityFinalRefer')
class CalibratedPNUtilityFinalRefer(ConservativeRouterContractFinalRefer):
    """Final node that uses a calibrated PN utility gate before LLM aggregation."""

    def __init__(self, id: Optional[str] = None, domain: str = "", llm_name: str = ""):
        super().__init__(id, domain, llm_name)
        self.role = "CalibratedPNUtilityFinalRefer"
        self.agent_name = "CalibratedPNUtilityFinalRefer"

    def _execute(self, input: Dict[str, str], spatial_info: Dict[str, Any],
                 temporal_info: Dict[str, Any], **kwargs):
        selected = select_calibrated_pn_utility_answer(spatial_info)
        if selected:
            return f"The answer is {selected}"
        return super()._execute(input, spatial_info, temporal_info, **kwargs)

    async def _async_execute(self, input: Dict[str, str], spatial_info: Dict[str, Any],
                             temporal_info: Dict[str, Any], **kwargs):
        selected = select_calibrated_pn_utility_answer(spatial_info)
        if selected:
            return f"The answer is {selected}"
        return await super()._async_execute(input, spatial_info, temporal_info, **kwargs)


@AgentRegistry.register('CalibratedEdgePromptRepairContractFinalRefer')
class CalibratedEdgePromptRepairContractFinalRefer(EdgePromptRepairContractFinalRefer):
    """Final node with calibrated repair confidence for forwarded edge-prompt repairs."""

    def __init__(self, id: Optional[str] = None, domain: str = "", llm_name: str = ""):
        super().__init__(id, domain, llm_name)
        self.role = "CalibratedEdgePromptRepairContractFinalRefer"
        self.agent_name = "CalibratedEdgePromptRepairContractFinalRefer"

    def _select_answer(self, spatial_info: Dict[str, Any]) -> Optional[str]:
        features = summarize_pn_utility_features(spatial_info)
        strong_router_options = features["strong_router_options"]
        if len(strong_router_options) == 1:
            return strong_router_options[0]
        repair_option = select_calibrated_edge_prompt_repair_answer(spatial_info)
        if repair_option:
            return repair_option
        return select_deterministic_router_answer(spatial_info)


@AgentRegistry.register('SelectivePromptNodeFinalRefer')
class SelectivePromptNodeFinalRefer(FinalRefer):
    """Selective final gate for direct evidence and PromptNode contracts.

    This implements a lightweight lifecycle action: ordinary direct evidence is
    preserved, PN_Router contracts are treated as graph-organization evidence,
    and an Agent-like audit is requested only when conflict or option-binding
    risk appears in the PromptNode path.
    """

    def __init__(self, id: Optional[str] = None, domain: str = "", llm_name: str = ""):
        Node.__init__(self, id, "SelectivePromptNodeFinalRefer", domain, llm_name)
        self.agent_name = "SelectivePromptNodeFinalRefer"
        self.llm = None if llm_name == "mock" else LLMRegistry.get(llm_name)
        self.prompt_set = PromptSetRegistry.get(domain)

    def _format_spatial_evidence(self, spatial_info: Dict[str, Any]) -> str:
        lines = []
        for idx, (node_id, info) in enumerate(spatial_info.items(), start=1):
            lines.append(
                f"[evidence_{idx}] node_id={node_id}; role={info.get('role', 'Unknown')}\n"
                f"{_compact_text(info.get('output', ''), 1800)}"
            )
        return "\n\n".join(lines) if lines else "- no upstream evidence"

    def _format_router_contracts(self, contracts: List[Dict[str, str]]) -> str:
        lines = []
        for idx, contract in enumerate(contracts, start=1):
            lines.append(
                f"[router_contract_{idx}] node_id={contract['node_id']}; role={contract['role']}\n"
                f"SUPPORTED_OPTION: {contract['supported_option']}\n"
                f"BINDING_STATUS: {contract['binding_status']}\n"
                f"FINAL_EVIDENCE_SUMMARY: {contract['final_evidence_summary']}\n"
                f"RAW_ROUTER_OUTPUT: {_compact_text(contract['raw_output'], 1400)}"
            )
        return "\n\n".join(lines)

    def _process_inputs(self, raw_inputs: Dict[str, str], spatial_info: Dict[str, Any],
                        temporal_info: Dict[str, Any], **kwargs) -> List[Any]:
        contracts = extract_router_contracts(spatial_info)
        if not contracts:
            return FinalRefer._process_inputs(self, raw_inputs, spatial_info, temporal_info, **kwargs)

        task = raw_inputs["task"]
        options = _extract_multiple_choice_options(task)
        option_lines = "\n".join(f"{k}) {v}" for k, v in options.items())
        direct_and_pn_evidence = self._format_spatial_evidence(spatial_info)
        router_contracts = self._format_router_contracts(contracts)

        system_prompt = (
            "You are a selective virtual PromptNode final gate for an AQuA multiple-choice task. "
            "Your job is to compare direct agent evidence with PromptNode router contracts. "
            "Use virtual nodes as graph-organization mechanisms: Memory preserves evidence, Verifier audits "
            "target and option binding, Router decides whether evidence should flow, and Agent-like Prompt Node "
            "audits only when conflict or option-binding risk exists. "
            "Do not use hidden labels, row ids, memorized answers, task-specific fixes, or nearest-option rescue. "
            "Separate mathematical truth from the submission option when the choices are inconsistent. "
            "The last line must be exactly: The answer is X"
        )

        user_prompt = (
            f"Task:\n{task}\n\n"
            f"Choices:\n{option_lines}\n\n"
            "VIRTUAL LIFECYCLE GATE\n"
            "1. Memory Prompt Node: preserve direct agent outputs, PN outputs, candidate labels, computed values, "
            "formulas, and uncertainty as separate fields.\n"
            "2. Instruction / Verifier Prompt Node: audit target preservation, option binding, unsupported labels, "
            "and direct-vs-router conflicts.\n"
            "3. EIB-aware Router Prompt Node: choose whether to suppress risky evidence or propagate a verified "
            "insight.\n"
            "4. Agent-like Prompt Node: activate only if the router contract has CONFLICT, NO_EXACT_OPTION, "
            "UNSUPPORTED_LABEL, or direct evidence disagrees with router evidence. This audit may reason from "
            "the task, but it must not use hidden labels or pretend a non-listed mathematical truth is an exact "
            "listed option.\n\n"
            "Return these machine-readable fields before the explanation:\n"
            "PN_ACTION: ACCEPT_DIRECT / USE_ROUTER / ESCALATE_AGENTLIKE\n"
            "DIRECT_OPTION: A/B/C/D/E/NONE\n"
            "ROUTER_OPTION: A/B/C/D/E/NONE\n"
            "MATH_TRUTH: compact expression or UNKNOWN\n"
            "SUBMISSION_OPTION: A/B/C/D/E (must be one listed option; never NONE)\n"
            "BINDING_STATUS: EXACT_MATCH / EQUIVALENT_FORM / NO_EXACT_OPTION / UNSUPPORTED_LABEL / CONFLICT\n"
            "NOISE_RISK: LOW / MEDIUM / HIGH\n"
            "Never write `The answer is NONE`; the final answer line must contain exactly one of A, B, C, D, or E.\n\n"
            "All evidence visible to the final gate:\n"
            f"{direct_and_pn_evidence}\n\n"
            "Parsed router contracts:\n"
            f"{router_contracts}\n\n"
            "Decision rule:\n"
            "- Prefer direct evidence when PN evidence is weak or merely nearest-choice based.\n"
            "- Use router evidence when it has target-preserved EXACT_MATCH or EQUIVALENT_FORM support.\n"
            "- Escalate to Agent-like Prompt Node only for conflict or option-binding risk, and explicitly report "
            "math truth separately from the submission option.\n"
            "- Finish with the required last line."
        )
        return system_prompt, user_prompt

    def _execute(self, input: Dict[str, str], spatial_info: Dict[str, Any],
                 temporal_info: Dict[str, Any], **kwargs):
        system_prompt, user_prompt = self._process_inputs(input, spatial_info, temporal_info, **kwargs)
        if self.llm is None:
            return user_prompt
        message = [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': user_prompt}]
        return self.llm.gen(message, temperature=0.0)

    async def _async_execute(self, input: Dict[str, str], spatial_info: Dict[str, Any],
                             temporal_info: Dict[str, Any], **kwargs):
        system_prompt, user_prompt = self._process_inputs(input, spatial_info, temporal_info, **kwargs)
        if self.llm is None:
            return user_prompt
        message = [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': user_prompt}]
        return await self.llm.agen(message, temperature=0.0)


@AgentRegistry.register('PromptNodeFinalRefer')
class PromptNodeFinalRefer(FinalRefer):
    """Final decision with lightweight virtual Prompt Nodes around ARG evidence."""

    def __init__(self, id: Optional[str] = None, domain: str = "", llm_name: str = ""):
        super().__init__(id, domain, llm_name)
        self.agent_name = "PromptNodeFinalRefer"

    def _process_inputs(self, raw_inputs: Dict[str, str], spatial_info: Dict[str, Any],
                        temporal_info: Dict[str, Any], **kwargs) -> List[Any]:
        task = raw_inputs["task"]
        options = _extract_multiple_choice_options(task)
        option_lines = "\n".join(f"{k}) {v}" for k, v in options.items())

        agent_lines = []
        for idx, (node_id, info) in enumerate(spatial_info.items(), start=1):
            agent_lines.append(
                f"[producer_{idx}] role={info.get('role', 'Unknown')} node_id={node_id}\n"
                f"{_compact_text(info.get('output', ''))}"
            )
        agent_block = "\n\n".join(agent_lines)

        system_prompt = (
            "You are the top decision-maker for an AQuA multiple-choice math task. "
            "You must use the virtual Prompt Nodes provided in the user message. "
            "They are graph-organization nodes, not extra solvers: Memory stores evidence, "
            "Verifier checks target and option binding, and Router decides final authority. "
            "Do not use any hidden dataset labels, row ids, or memorized answers. "
            "Do not choose an option only because it is numerically nearest to a computed value. "
            "The last line must be exactly: The answer is X"
        )

        memory_node = (
            "VIRTUAL NODE: Memory Prompt Node\n"
            "- Store each producer's explicit answer, derivation signature, and computed value if present.\n"
            "- Preserve the target quantity from the question and the available choices.\n"
            "- Treat code output, textual derivation, and final option labels as separate evidence fields.\n"
            "- Do not invent new facts beyond the question and producer outputs."
        )
        verifier_node = (
            "VIRTUAL NODE: Instruction / Verifier Prompt Node\n"
            "- Restate the target quantity being asked.\n"
            "- Check whether each producer preserved that target or solved a shifted target.\n"
            "- Check option binding: exact match, equivalent form, no exact option, or unsupported label.\n"
            "- If there is no exact/equivalent option binding or producers disagree, create an Option-Contract check: "
            "for each option, infer the event, constraint, or quantity that option represents, then compare it to the "
            "question target and every stated condition.\n"
            "- For probability questions, preserve the full event scope. Exclusion clauses such as 'not via cheating' "
            "must be represented as explicit complement conditions, and answers that ignore a named participant or "
            "condition are weak even if their numeric value is plausible.\n"
            "- Prefer a listed option whose contract uses the stated independent conditions directly over a nearest "
            "numeric approximation or a label unsupported by producer reasoning.\n"
            "- If agents disagree, prefer the answer with target-preserved reasoning and exact/equivalent option binding.\n"
            "- If a computed value has no exact/equivalent option, mark it as option-binding risk; do not resolve by nearest-choice alone.\n"
            "- If an agent gives a label that is not supported by its own reasoning, mark it as weak evidence."
        )
        router_node = (
            "VIRTUAL NODE: EIB-aware Router Prompt Node\n"
            "- Error-suppression view: block unsupported labels, shifted targets, and nearest-only choices.\n"
            "- Insight-propagation view: keep independent producer evidence that preserves the target.\n"
            "- Final authority: choose the option with the strongest supported evidence after target and option-binding checks.\n"
            "- If evidence remains ambiguous, still output the best-supported A-E choice, but explain the uncertainty briefly."
        )

        user_prompt = (
            f"Task:\n{task}\n\n"
            f"Choices parsed by Memory node:\n{option_lines}\n\n"
            f"{memory_node}\n\n{verifier_node}\n\n{router_node}\n\n"
            f"ARG-Designer producer outputs connected to the virtual nodes:\n{agent_block}\n\n"
            "Apply the virtual nodes in order: Memory -> Verifier -> Router. "
            "Then give a concise decision rationale and finish with the required last line."
        )
        return system_prompt, user_prompt


@AgentRegistry.register('PromptNodeGuardedFinalRefer')
class PromptNodeGuardedFinalRefer(PromptNodeFinalRefer):
    """ARG-preserving Prompt Node final authority.

    ARG's ordinary final answer is treated as the current final. Virtual nodes may
    replace it only with independently supported, target-preserved, option-bound
    evidence. This prevents nearest-option rescue from becoming a hidden patch.
    """

    def __init__(self, id: Optional[str] = None, domain: str = "", llm_name: str = ""):
        super().__init__(id, domain, llm_name)
        self.agent_name = "PromptNodeGuardedFinalRefer"

    def _process_guarded_inputs(self, raw_inputs: Dict[str, str], spatial_info: Dict[str, Any],
                                baseline_answer: str) -> List[Any]:
        task = raw_inputs["task"]
        options = _extract_multiple_choice_options(task)
        option_lines = "\n".join(f"{k}) {v}" for k, v in options.items())

        agent_lines = []
        for idx, (node_id, info) in enumerate(spatial_info.items(), start=1):
            agent_lines.append(
                f"[producer_{idx}] role={info.get('role', 'Unknown')} node_id={node_id}\n"
                f"{_compact_text(info.get('output', ''))}"
            )
        agent_block = "\n\n".join(agent_lines)

        system_prompt = (
            "You are a guarded virtual Prompt Node final-authority router for AQuA. "
            "ARG-Designer's original final answer is the current final. "
            "Your default action is ACCEPT_CURRENT_FINAL. "
            "You may REPLACE_CURRENT_FINAL only when producer evidence provides a target-preserved derivation "
            "and exact/equivalent option binding for a different listed option. "
            "Never replace using nearest-option rescue, plausibility, memorized dataset quirks, row ids, or labels. "
            "If no listed option is exactly/equivalently supported, preserve the current final. "
            "The last line must be exactly: The answer is X"
        )

        user_prompt = (
            f"Task:\n{task}\n\n"
            f"Choices:\n{option_lines}\n\n"
            f"CURRENT_FINAL from ARG-Designer FinalRefer:\n{_compact_text(baseline_answer, 2200)}\n\n"
            "VIRTUAL NODE: Memory Prompt Node\n"
            "- Build an evidence ledger with producer answer, derivation signature, computed value, and option label.\n"
            "- Keep CURRENT_FINAL as a separate aggregator root, not as producer evidence.\n\n"
            "VIRTUAL NODE: Instruction / Verifier Prompt Node\n"
            "- Check target preservation for each producer and CURRENT_FINAL.\n"
            "- Check option binding for each candidate: EXACT_MATCH, EQUIVALENT_FORM, NO_EXACT_OPTION, or UNSUPPORTED_LABEL.\n"
            "- A candidate with NO_EXACT_OPTION cannot replace CURRENT_FINAL.\n"
            "- A nearest or most plausible listed option is not enough to replace CURRENT_FINAL.\n\n"
            "VIRTUAL NODE: EIB-aware Router Prompt Node\n"
            "- ACCEPT_CURRENT_FINAL unless a replacement has strong independent producer support and exact/equivalent option binding.\n"
            "- REPLACE_CURRENT_FINAL only when replacement evidence is stronger than CURRENT_FINAL under the checks above.\n"
            "- Report ACTION as ACCEPT_CURRENT_FINAL or REPLACE_CURRENT_FINAL before the final line.\n\n"
            f"Producer outputs:\n{agent_block}\n"
        )
        return system_prompt, user_prompt

    async def _async_execute(self, input: Dict[str, str], spatial_info: Dict[str, Any],
                             temporal_info: Dict[str, Any], **kwargs):
        baseline_answer = await FinalRefer._async_execute(self, input, spatial_info, temporal_info, **kwargs)
        system_prompt, user_prompt = self._process_guarded_inputs(input, spatial_info, baseline_answer)
        message = [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': user_prompt}]
        gated_response = await self.llm.agen(message)
        if "REPLACE_CURRENT_FINAL" not in gated_response:
            return baseline_answer
        return gated_response

    def _execute(self, input: Dict[str, str], spatial_info: Dict[str, Any],
                 temporal_info: Dict[str, Any], **kwargs):
        raise NotImplementedError("PromptNodeGuardedFinalRefer supports async execution only.")


@AgentRegistry.register('FinalDirect')
class FinalDirect(Node):
    def __init__(self, id: Optional[str] =None, domain: str = "", llm_name: str = "", ):
        """ Used for Directed IO """
        super().__init__(id, "FinalDirect")
        self.prompt_set = PromptSetRegistry.get(domain)
        
    def _process_inputs(self, raw_inputs:Dict[str,str], spatial_info:Dict[str,Any], temporal_info:Dict[str,Any], **kwargs)->List[Any]:
        """ To be overriden by the descendant class """
        """ Process the raw_inputs(most of the time is a List[Dict]) """
        return None
                
    def _execute(self, input:Dict[str,str],  spatial_info:Dict[str,Any], temporal_info:Dict[str,Any],**kwargs):
        """ To be overriden by the descendant class """
        """ Use the processed input to get the result """
        output = ""
        info_list = []
        for info in spatial_info.values():
            info_list.append(info['output'])
        if len(info_list):
            output = info_list[-1]
        return output
    
    async def _async_execute(self, input:Dict[str,str],  spatial_info:Dict[str,Any], temporal_info:Dict[str,Any],**kwargs):
        """ To be overriden by the descendant class """
        """ Use the processed input to get the result """
        output = ""
        info_list = []
        for info in spatial_info.values():
            info_list.append(info['output'])
        if len(info_list):
            output = info_list[-1]
        return output


@AgentRegistry.register('FinalMajorVote')
class FinalMajorVote(Node):
    def __init__(self, id: Optional[str] =None, domain: str = "", llm_name: str = "", ):
        """ Used for Directed IO """
        super().__init__(id, "FinalMajorVote")
        self.prompt_set = PromptSetRegistry.get(domain)
        
    def _process_inputs(self, raw_inputs:Dict[str,str], spatial_info:Dict[str,Any], temporal_info:Dict[str,Any], **kwargs)->List[Any]:
        """ To be overriden by the descendant class """
        """ Process the raw_inputs(most of the time is a List[Dict]) """
        return None
    
    def _execute(self, input:Dict[str,str],  spatial_info:Dict[str,Any], temporal_info:Dict[str,Any],**kwargs):
        """ To be overriden by the descendant class """
        """ Use the processed input to get the result """
        output_num = {}
        max_output = ""
        max_output_num = 0
        for info in spatial_info.values():
            processed_output = self.prompt_set.postprocess_answer(info['output'])
            if processed_output in output_num:
                output_num[processed_output] += 1
            else:
                output_num[processed_output] = 1
            if output_num[processed_output] > max_output_num:
                max_output = processed_output
                max_output_num = output_num[processed_output]
        return max_output
    
    async def _async_execute(self, input:Dict[str,str],  spatial_info:Dict[str,Any], temporal_info:Dict[str,Any],**kwargs):
        """ To be overriden by the descendant class """
        """ Use the processed input to get the result """
        output_num = {}
        max_output = ""
        max_output_num = 0
        for info in spatial_info.values():
            processed_output = self.prompt_set.postprocess_answer(info['output'])
            # print(processed_output)
            if processed_output in output_num:
                output_num[processed_output] += 1
            else:
                output_num[processed_output] = 1
            if output_num[processed_output] > max_output_num:
                max_output = processed_output
                max_output_num = output_num[processed_output]
        return max_output
