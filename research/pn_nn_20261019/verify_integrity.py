#!/usr/bin/env python3
"""Verify this release only; never import generation or scoring sources."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent
manifest = json.loads((root / 'MANIFEST.json').read_text())
actual = {str(p.relative_to(root)) for p in root.rglob('*')
          if p.is_file() and 'reproduced' not in p.relative_to(root).parts
          and '__pycache__' not in p.relative_to(root).parts
          and p.name != 'MANIFEST.json'}
expected = {row['path'] for row in manifest['files']}
assert actual == expected, {'missing': sorted(expected-actual), 'extra': sorted(actual-expected)}
for row in manifest['files']:
    data = (root / row['path']).read_bytes()
    assert len(data) == row['bytes'] and hashlib.sha256(data).hexdigest() == row['sha256'], row['path']
print(json.dumps({'status': 'PASS', 'files': len(expected), 'model_calls': 0,
                  'candidate_executions': 0, 'rescoring': 0}))
