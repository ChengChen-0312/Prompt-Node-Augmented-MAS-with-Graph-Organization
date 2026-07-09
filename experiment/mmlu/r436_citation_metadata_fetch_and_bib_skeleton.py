from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple


SCRIPT_DIR = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


DEFAULT_CANDIDATES_JSON = ".aris/verify-papers/candidate_papers.json"
DEFAULT_REFERENCES_BIB = "paper/references.bib"
DEFAULT_METADATA_JSON = ".aris/verify-papers/r436_citation_metadata.json"
DEFAULT_SUMMARY_JSON = "experiment/mmlu/res_logs/mmlu_r436_citation_metadata_fetch_and_bib_skeleton_summary.json"
DEFAULT_REPORT_MD = "experiment/mmlu/run_logs/mmlu_r436_citation_metadata_fetch_and_bib_skeleton_report.md"

ARXIV_UPDATES = {
    "agent_prune": "2410.02506",
    "mas2": "2509.24323",
    "goagent": "2603.19677",
}

PREFERRED_SOURCES = {
    "agent_dropout": "https://aclanthology.org/2025.acl-long.1170.bib",
    "eib_learner": "https://aclanthology.org/2025.emnlp-main.623.bib",
    "agent_prune": "https://dblp.org/rec/conf/iclr/ZhangYLYWWCY025.bib",
}


def _repo_path(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else Path(REPO_ROOT) / p


def _load_json(path: str) -> Any:
    target = _repo_path(path)
    return json.loads(target.read_text(encoding="utf-8")) if target.exists() else []


def _write_json(path: str, payload: Any) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: str, text: str) -> None:
    target = _repo_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def _fetch_text(url: str, timeout: int = 20) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Codex-R436-citation-fetch/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read().decode("utf-8", "replace")


def _source_for(candidate: Dict[str, Any]) -> Tuple[str | None, str]:
    if candidate["id"] in PREFERRED_SOURCES:
        return PREFERRED_SOURCES[candidate["id"]], "preferred_published_metadata"
    arxiv_id = candidate.get("arxiv_id") or ARXIV_UPDATES.get(candidate["id"])
    if arxiv_id:
        return f"https://arxiv.org/bibtex/{arxiv_id}", "arxiv_metadata"
    return None, "no_fetch_source"


def _normalize_entry_key(raw_bib: str, bib_key: str) -> str:
    return re.sub(r"@([A-Za-z]+)\{[^,\s]+,", rf"@\1{{{bib_key},", raw_bib.strip(), count=1)


def _entry_count(bib_text: str) -> int:
    return len(re.findall(r"@\w+\{", bib_text))


def _maybe_backup_references(references_bib: str) -> str | None:
    target = _repo_path(references_bib)
    if not target.exists():
        return None
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    backup = _repo_path(f"{references_bib}.r436-backup-{stamp}")
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(target, backup)
    return str(backup.relative_to(REPO_ROOT))


def fetch_bib_entries(candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
    entries: List[str] = []
    metadata: List[Dict[str, Any]] = []
    failures: List[Dict[str, Any]] = []
    for candidate in candidates:
        arxiv_update = ARXIV_UPDATES.get(candidate["id"])
        if arxiv_update:
            candidate = dict(candidate)
            candidate["arxiv_id"] = candidate.get("arxiv_id") or arxiv_update
        source_url, source_type = _source_for(candidate)
        if not source_url:
            failures.append({"id": candidate["id"], "reason": "no_fetch_source"})
            continue
        try:
            raw_bib = _fetch_text(source_url)
            if "@" not in raw_bib:
                raise ValueError("response did not contain a BibTeX entry")
            normalized = _normalize_entry_key(raw_bib, candidate["bib_key"])
            entries.append(
                "\n".join(
                    [
                        f"% R436 source: {source_url}",
                        "% R436 audit_status: skeleton_needs_citation_audit",
                        normalized,
                        "",
                    ]
                )
            )
            metadata.append(
                {
                    "id": candidate["id"],
                    "bib_key": candidate["bib_key"],
                    "title": candidate["title"],
                    "source_url": source_url,
                    "source_type": source_type,
                    "arxiv_id": candidate.get("arxiv_id"),
                    "status": "fetched_needs_citation_audit",
                }
            )
        except Exception as exc:  # pragma: no cover - network fallback path
            failures.append({"id": candidate["id"], "source_url": source_url, "reason": str(exc)})
    return {"entries": entries, "metadata": metadata, "failures": failures}


def render_report(summary: Dict[str, Any], metadata: List[Dict[str, Any]]) -> str:
    rows = [
        "# R436 Citation Metadata Fetch And Bib Skeleton",
        "",
        f"**Claim boundary**: {summary['claim_boundary']}",
        "",
        f"- References BibTeX: `{summary['references_bib']}`",
        f"- Fetched BibTeX count: `{summary['fetched_bib_count']}`",
        f"- Final BibTeX authorized: `{summary['final_bib_authorized']}`",
        "",
        "## Entries",
        "",
    ]
    rows.extend(f"- `{row['bib_key']}` from {row['source_url']}" for row in metadata)
    rows.extend(["", f"- Next required run: `{summary['next_required_run']}`", ""])
    return "\n".join(rows)


def run_fetch(
    candidate_papers_json: str = DEFAULT_CANDIDATES_JSON,
    references_bib: str = DEFAULT_REFERENCES_BIB,
    metadata_json: str = DEFAULT_METADATA_JSON,
    summary_json: str = DEFAULT_SUMMARY_JSON,
    report_md: str = DEFAULT_REPORT_MD,
) -> Dict[str, Any]:
    candidates = _load_json(candidate_papers_json)
    fetched = fetch_bib_entries(candidates)
    bib_text = "\n".join(fetched["entries"])
    backup = _maybe_backup_references(references_bib)
    _write_text(references_bib, bib_text)
    _write_json(metadata_json, fetched["metadata"])
    summary: Dict[str, Any] = {
        "run_id": "R436",
        "title": "Citation metadata fetch and BibTeX skeleton",
        "claim_boundary": (
            "R436 fetches BibTeX skeleton entries from official or canonical metadata sources. "
            "These entries remain unaudited until citation contexts exist."
        ),
        "no_api": True,
        "broad_api": False,
        "candidate_papers_json": candidate_papers_json,
        "references_bib": references_bib,
        "metadata_json": metadata_json,
        "fetched_bib_count": len(fetched["metadata"]),
        "bib_entry_count": _entry_count(bib_text),
        "fetch_failures": fetched["failures"],
        "all_entries_have_source_url": all(row.get("source_url") for row in fetched["metadata"]),
        "citation_audit_required_before_use": True,
        "final_bib_authorized": False,
        "related_work_draft_authorized_next": True,
        "paper_claim_authorized": False,
        "sci_q2_ready": False,
        "backup_created": backup,
        "next_required_run": "R437_related_work_initial_draft",
    }
    summary.update({"summary_json": summary_json, "report_md": report_md})
    _write_json(summary_json, summary)
    _write_text(report_md, render_report(summary, fetched["metadata"]))
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch related-work BibTeX skeleton entries.")
    parser.add_argument("--candidate_papers_json", default=DEFAULT_CANDIDATES_JSON)
    parser.add_argument("--references_bib", default=DEFAULT_REFERENCES_BIB)
    parser.add_argument("--metadata_json", default=DEFAULT_METADATA_JSON)
    parser.add_argument("--summary_json", default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--report_md", default=DEFAULT_REPORT_MD)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(run_fetch(**vars(parse_args())), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
