#!/usr/bin/env python3
"""Generate patches/boot_ai.txt from ai_work/boot/*.tsv (BOOT.BIN strings not in boot.txt).

BOOT.BIN is executable code: only offsets listed in the TSVs are touched, each with
#FIXEDLENGTH equal to the original string length so the following bytes (the
terminator and whatever comes after it) stay untouched.
Needs an unmodified BOOT.BIN at ai_scratch/BOOT.BIN (extract it from the ISO with
tools/7-Zip/7z.exe e -oai_scratch <iso> PSP_GAME/SYSDIR/BOOT.BIN).
"""
import glob
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE)
import gen_patch as g  # noqa: E402

d = open(os.path.join(ROOT, 'ai_scratch', 'BOOT.BIN'), 'rb').read()
out = ['// Doko Demo Issyo PSP English Translation Project\n',
       '// GENERATED FILE - machine (AI) translation of BOOT.BIN text not covered by patches/boot.txt.\n',
       '// Regenerate with: python scripts/ai/gen_boot.py   (applied after boot.txt)\n\n',
       '#SETTARGETFILE("build/PSP_GAME/SYSDIR/BOOT.BIN")\n#VAR(Table, TABLE)\n#ADDTBL("shiftjis.tbl", Table)\n#ACTIVETBL(Table)\n\n']
n = err = 0
for f in sorted(glob.glob(os.path.join(ROOT, 'ai_work', 'boot', '0*.tsv'))):
    for line in open(f, encoding='utf-8'):
        line = line.rstrip('\n')
        if not line or line.startswith('#'):
            continue
        p = line.split('\t')
        off, en = int(p[0], 16), p[1]
        unsure = p[2][1:] if len(p) > 2 and p[2].startswith('?') else ''
        if d[off - 1] != 0:
            print('%X: not at a string start, skipped' % off); err += 1; continue
        ln = d.index(b'\0', off) - off
        jp = d[off:off + ln].decode('cp932')
        blen, bad = g.encode_len(en)
        if bad or blen > ln:
            print('%X too long/unencodable (%d > %d): %s' % (off, blen, ln, en)); err += 1; continue
        if unsure:
            out.append('// AI-UNSURE: %s\n' % unsure)
        out.append('//%s\n#JMP($%X)\n#FIXEDLENGTH(%d,0)\n%s<END>\n\n' % (jp.replace('\n', '\n'), off, ln, en))
        n += 1
with open(os.path.join(ROOT, 'patches', 'boot_ai.txt'), 'w', encoding='utf-8', newline='\n') as fh:
    fh.write(''.join(out))
print('boot_ai.txt: wrote %d entries, %d errors' % (n, err))
