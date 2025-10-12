#!/usr/bin/env python3
"""
Simple cleanup: replace occurrences of the regex-artifact prefix
'Event Payload:\s*(\{.*\}): ' and 'Single Event:\s*(\{.*\}): '
with clean labels 'Event Payload: ' and 'Single Event: '.
"""
import re
from pathlib import Path

p = Path('android_events.txt')
if not p.exists():
    print('android_events.txt not found')
    raise SystemExit(1)

text = p.read_text()

# Replace the literal artifact sequences that were written earlier.
# The file contains backslashes and parentheses literally, e.g.:
# Event Payload:\s*(\{.*\}): {"networkMode":...}
# We'll replace the prefix up to the opening brace with the clean label.

text = re.sub(r'Event Payload:\\s\*\(\\\{.*?\\\}\):\s*', 'Event Payload: ', text)
text = re.sub(r'Single Event:\\s\*\(\\\{.*?\\\}\):\s*', 'Single Event: ', text)

# Also handle a slightly different artifact without double-escaping (if present)
text = re.sub(r'Event Payload:\\s\*\(\{.*?\}\):\s*', 'Event Payload: ', text)
text = re.sub(r'Single Event:\\s\*\(\{.*?\}\):\s*', 'Single Event: ', text)

# Last fallback: replace the visible sequence 'Event Payload:\s*(\{.*\}): ' if present
text = text.replace('Event Payload:\s*(\{.*\}): ', 'Event Payload: ')
text = text.replace('Single Event:\s*(\{.*\}): ', 'Single Event: ')

# Backup file
bak = p.with_suffix('.txt.bak')
if not bak.exists():
    bak.write_text(text)  # backup will actually be same as cleaned; but we keep the original below

# Save cleaned output to a new file (overwrite original)
# To keep an original backup, write original content to .orig if not exists
orig = p.with_suffix('.txt.orig')
if not orig.exists():
    orig.write_text(p.read_text())

p.write_text(text)
print('Cleaned android_events.txt — please verify. Original saved as', orig)
