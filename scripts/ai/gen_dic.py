#!/usr/bin/env python3
"""Generate an Atlas patch for a Pokepi dictionary (.DIC) from AI translations.

A .DIC word entry is: <index kana> 00 20 <display> 00 <reading> 00 ...
The display form is what [WORD]/$_WORD codes insert into sentences; the reading is
used for sorting/lookup. Both get the same English text (like the human
patches/toro_dictionary.txt does), so it must fit min(display, reading) bytes.

usage: python scripts/ai/gen_dic.py worklist <char>   -> ai_work/<char>_dic/words.tsv
       python scripts/ai/gen_dic.py build <char>      -> patches/<char>_ai_dictionary.txt
Translations: ai_work/<char>_dic/*.tsv, lines "OFF<TAB>English" (OFF = display offset,
"-" = leave Japanese).
"""
import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE)
import gen_patch as g  # noqa: E402

DIC = {'toro': 'NEKO', 'suzuki': 'ROBO', 'jun': 'USAGI', 'pierre': 'INU', 'ricky': 'KAERU'}


def entries(char):
    d = open(os.path.join(ROOT, 'extract', DIC[char] + '.DIC'), 'rb').read()
    out = []
    for k in range(3, len(d) - 2):
        if d[k] == 0x20 and d[k - 1] == 0 and (0x81 <= d[k - 3] <= 0x9f or 0xe0 <= d[k - 3] <= 0xef):
            try:
                j = d.index(b'\0', k + 1)
                j2 = d.index(b'\0', j + 1)
                disp = d[k + 1:j].decode('cp932')
                read = d[j + 1:j2].decode('cp932')
            except (ValueError, UnicodeDecodeError):
                continue
            if disp and read:
                out.append((k + 1, j - k - 1, disp, j + 1, j2 - j - 1, read))
    return out


def human_covered(char):
    cov = set()
    for f in glob.glob(os.path.join(ROOT, 'patches', '%s_dictionary.txt' % char)):
        cov |= set(int(x, 16) for x in re.findall(r'#JMP\(\$(\w+)\)', open(f, encoding='utf-8').read()))
    return cov


def main():
    cmd, char = sys.argv[1], sys.argv[2]
    ents = [e for e in entries(char) if e[0] not in human_covered(char)]
    wdir = os.path.join(ROOT, 'ai_work', char + '_dic')
    if cmd == 'worklist':
        os.makedirs(wdir, exist_ok=True)
        with open(os.path.join(wdir, 'words.tsv'), 'w', encoding='utf-8') as f:
            for e in ents:
                f.write('%X\t%d\t%s\t%X\t%d\t%s\n' % e)
        print('%d words' % len(ents))
        return
    tr = {}
    for f in sorted(glob.glob(os.path.join(wdir, '0*.tsv'))):
        for line in open(f, encoding='utf-8'):
            line = line.rstrip('\n')
            if not line or line.startswith('#'):
                continue
            off, en = line.split('\t')[:2]
            tr[int(off, 16)] = en
    out = ['// Doko Demo Issyo PSP English Translation Project\n',
           '// GENERATED FILE - machine (AI) translation of dictionary words not covered by\n',
           '// patches/%s_dictionary.txt. Regenerate with: python scripts/ai/gen_dic.py build %s\n\n' % (char, char),
           '#SETTARGETFILE("insert/%s.DIC")\n#VAR(Table, TABLE)\n#ADDTBL("shiftjis.tbl", Table)\n#ACTIVETBL(Table)\n\n' % DIC[char]]
    n = err = 0
    for doff, dl, disp, roff, rl, read in ents:
        en = tr.get(doff)
        if en is None or en == '-':
            continue
        blen, bad = g.encode_len(en)
        if bad or blen > min(dl, rl):
            print('%X too long/unencodable (%d > %d): %s' % (doff, blen, min(dl, rl), en))
            err += 1
            continue
        out.append('//%s (%s)\n#FIXEDLENGTH(%d,0)\n#JMP($%X)\n%s<END>\n#FIXEDLENGTH(%d,0)\n#JMP($%X)\n%s<END>\n\n'
                   % (disp, read, dl, doff, en, rl, roff, en))
        n += 1
    fn = os.path.join(ROOT, 'patches', '%s_ai_dictionary.txt' % char)
    with open(fn, 'w', encoding='utf-8', newline='\n') as f:
        f.write(''.join(out))
    print('%s: wrote %d words, %d errors' % (os.path.basename(fn), n, err))


if __name__ == '__main__':
    main()
