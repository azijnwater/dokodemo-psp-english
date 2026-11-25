#!/usr/bin/env python3
"""Print per-character AI translation progress (used for docs/AI_TRANSLATION_LOG.md)."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_patch as g  # noqa: E402

for char in g.CHARS:
    strs = g.strings(char)
    cov = g.covered(char)
    tr = g.load_translations(char)
    byoff = {o: t for o, l, t in strs}
    texts = {byoff[o]: v for o, v in tr.items() if o in byoff}
    done = skip = unsure = 0
    left = set()
    for o, l, t in strs:
        if o in cov:
            continue
        if t in texts:
            en, un, _ = texts[t]
            if en == '-':
                skip += 1
            else:
                done += 1
                unsure += 1 if un else 0
        else:
            left.add(t)
    print('%-7s strings in file: %5d | already human-translated (JMP in existing patches): %4d | AI entries: %5d '
          '(AI-UNSURE %d) | skipped as non-text: %d | still untranslated (unique texts): %d'
          % (char, len(strs), len(cov), done, unsure, skip, len(left)))
