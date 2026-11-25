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
    hp = g.human_pairs() if char == 'ricky' or True else {}
    patch = 'ricky_messages.txt' if char == 'ricky' else '%s_ai_messages.txt' % char
    pf = os.path.join(g.ROOT, 'patches', patch)
    import re
    written = set(int(x, 16) for x in re.findall(r'#JMP\(\$(\w+)\)', open(pf, encoding='utf-8').read())) if os.path.exists(pf) else set()
    reused = 0
    done = skip = unsure = 0
    left = set()
    for o, l, t in strs:
        if o in cov or g.is_label(t):
            continue
        if t in texts:
            en, un, _ = texts[t]
            if en == '-':
                skip += 1
            else:
                done += 1
                unsure += 1 if un else 0
        elif o in written:
            reused += 1
        else:
            left.add(t)
    print('%-7s strings in file: %5d | already human-translated (JMP in existing patches): %4d | AI entries: %5d '
          '(AI-UNSURE %d) | reused human translations: %d | skipped as non-text: %d | still untranslated (unique texts): %d'
          % (char, len(strs), len(cov), done, unsure, reused, skip, len(left)))
