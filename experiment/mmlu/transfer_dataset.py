import json
import re
from typing import Any, Dict, Iterator, List, Optional, Sequence, Union


VALID_OPTIONS = {"A", "B", "C", "D"}


def _load_jsonl(path: str) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if stripped:
                records.append(json.loads(stripped))
    return records


def _load_json(path: str) -> Dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _apply_split(records: Sequence[Dict[str, Any]], split_path: Optional[str]) -> List[Dict[str, Any]]:
    if not split_path:
        return list(records)
    split = _load_json(split_path)
    if "test_indices" in split:
        selected = []
        for index in split["test_indices"]:
            selected.append(records[int(index)])
        return selected
    if "task_ids" in split:
        by_id = {str(record.get("task_id") or record.get("id")): record for record in records}
        return [by_id[str(task_id)] for task_id in split["task_ids"]]
    return list(records)


class MMLUTransferDataset:
    def __init__(self, records_jsonl: str, split_path: Optional[str] = None) -> None:
        self.records_jsonl = records_jsonl
        self.split_path = split_path
        self._records = _apply_split(_load_jsonl(records_jsonl), split_path)

    @staticmethod
    def get_domain() -> str:
        return "mmlu"

    def __len__(self) -> int:
        return len(self._records)

    def __iter__(self) -> Iterator[Dict[str, Any]]:
        return iter(self._records)

    def __getitem__(self, index: int) -> Dict[str, Any]:
        return self._records[index]

    @staticmethod
    def record_to_input(record: Dict[str, Any]) -> Dict[str, Any]:
        task_text = record.get("task") or record.get("question") or ""
        return {"task": str(task_text)}

    @staticmethod
    def record_to_target_answer(record: Dict[str, Any]) -> str:
        answer = str(record.get("answer") or record.get("correct_answer") or "").strip().upper()
        return answer[:1] if answer[:1] in VALID_OPTIONS else ""

    @staticmethod
    def postprocess_answer(answer: Union[str, List[str]]) -> str:
        if isinstance(answer, list):
            answer = answer[0] if answer else ""
        if not isinstance(answer, str):
            raise TypeError(f"Expected string or list answer, got {type(answer)!r}")

        text = answer.strip().upper()
        if not text:
            return ""

        answer_is = re.search(r"ANSWER\s+IS\s+(?:OPTION\s+)?([A-D])\b", text)
        if answer_is:
            return answer_is.group(1)

        option = re.search(r"\bOPTION\s+([A-D])\b", text)
        if option:
            return option.group(1)

        bare = re.search(r"\b([A-D])\b", text)
        return bare.group(1) if bare else ""
