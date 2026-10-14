#!/usr/bin/env python3
"""Run only after Docker Desktop has stopped. Preserve every other setting."""
import json
from pathlib import Path
root = Path(__file__).resolve().parents[1]
p = Path.home() / 'Library/Group Containers/group.com.docker/settings-store.json'
d = json.loads(p.read_text())
backup = root / 'artifacts/step-02/docker-memory-before.json'
if not backup.exists():
    backup.write_text(json.dumps({'MemoryMiB_present': 'MemoryMiB' in d, 'MemoryMiB': d.get('MemoryMiB')}, indent=2)+'\n')
d['MemoryMiB'] = 16384
p.write_text(json.dumps(d, indent=2)+'\n')
print('Docker MemoryMiB set to 16384; other settings preserved.')
