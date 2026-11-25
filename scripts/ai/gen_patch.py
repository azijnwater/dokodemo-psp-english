#!/usr/bin/env python3
"""
AI translation tooling: worklists and Atlas patch generation.

  python scripts/ai/gen_patch.py worklist <char>   -> ai_work/<char>/worklist.tsv
  python scripts/ai/gen_patch.py build <char>      -> patches/<char>_ai_messages.txt
                                                      (ricky: patches/ricky_messages.txt)

Translations live in ai_work/<char>/*.tsv (except worklist.tsv), one per line:
  OFFSET<TAB>English text[<TAB>?unsure reason]
OFFSET is the hex offset printed in the worklist. The translation is applied
to every string in the .KSC file whose Japanese text is identical.
English "-" means: skip (internal label / not real text).
Shorthands: {DASU} = <$17><$19><$00>, {HAA} = <$17><$1B><$00>, {C18} = <$17><$18><$00>.

Byte lengths are measured with shiftjis.tbl; an entry that does not fit in
the original string length, or uses a character missing from the table, is
reported as an error and not written.
"""
import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kscparse  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
CHARS = {
    'toro': ('NEKO', 'Toro'),
    'suzuki': ('ROBO', 'Suzuki'),
    'jun': ('USAGI', 'Jun'),
    'pierre': ('INU', 'Pierre'),
    'ricky': ('KAERU', 'Ricky'),
}
MAXW = 140

HEADER = """// Doko Demo Issyo PSP English Translation Project - {ksc}.KSC Atlas script ({name} messages, AI translation)
// © pumpkinhasapatch 2024 <https://github.com/pumpkinhasapatch/dokodemo-psp-english>

// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.

// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.

// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

// GENERATED FILE - machine (AI) translation, not yet reviewed by a human.
// Source: ai_work/{char}/*.tsv, generator: scripts/ai/gen_patch.py
// Entries marked "AI-UNSURE" need a human check. See docs/STYLE_NOTES.md.

#SETTARGETFILE("insert/{ksc}.KSC")
#VAR(Table, TABLE)
#ADDTBL("shiftjis.tbl", Table)
#ACTIVETBL(Table)

"""


def load_table():
    enc = {}
    for line in open(os.path.join(ROOT, 'shiftjis.tbl'), encoding='utf-8'):
        line = line.rstrip('\r\n')
        if '=' not in line:
            continue
        h, t = line.split('=', 1)
        if t == '' and h != '20':
            continue
        enc.setdefault(t, len(h) // 2)
    enc[' '] = 1
    return enc


TBL = load_table()
MAXTOK = max(len(k) for k in TBL)


def encode_len(s):
    """Return (byte length, list of unencodable chars) using greedy longest match like Atlas."""
    i = 0
    n = 0
    bad = []
    while i < len(s):
        m = re.match(r'<\$[0-9A-Fa-f]{2}>', s[i:])
        if m:
            n += 1; i += len(m.group(0)); continue
        for L in range(min(MAXTOK, len(s) - i), 0, -1):
            if s[i:i + L] in TBL:
                n += TBL[s[i:i + L]]; i += L
                break
        else:
            bad.append(s[i]); i += 1
    return n, bad


WIDTHS = {}
for _l in open(os.path.join(ROOT, 'scripts', 'char_widths.txt'), encoding='utf-8'):
    _l = _l.rstrip('\r\n')
    if len(_l) >= 3 and _l[1] == '=':
        WIDTHS[_l[0]] = int(_l[2:])


def width(s):
    s = re.sub(r'\[WORD\d+\]', 'WWWWWW', s)
    s = re.sub(r'\[VAR\d+\]', 'WWWW', s)
    s = re.sub(r'\[NYA\]|\[KERO\]|<\$17><\$..><\$00>', 'meow', s)
    s = re.sub(r'<\$..>', '', s)
    return sum(WIDTHS.get(c, 10) for c in s)


def wrap(text):
    """Insert [LR] at spaces so that no line is wider than MAXW."""
    parts = text.split('[LR]')
    out = []
    for p in parts:
        words = p.split(' ')
        line = ''
        lines = []
        for w in words:
            cand = w if line == '' else line + ' ' + w
            if line != '' and width(cand) > MAXW:
                lines.append(line)
                line = w
            else:
                line = cand
        lines.append(line)
        out.append('[LR]'.join(lines))
    return '[LR]'.join(out)


# Catchphrase codes (expanded by the game from a table, with no leading space).
CODE_RE = r'(?:\[KERO\]|\[NYA\]|<\$17><\$1[789AB]><\$00>)'
TIC_RE = r'(?:\[KERO\]|<\$17><\$19><\$00>)'   # Ricky's ケロ / ダス


def space_codes(en):
    """Put a space before a catchphrase code that directly follows a word or
    punctuation, so 'Meanie<dasu>' shows as 'Meanie dasu' (like 'know [NYA]～')."""
    def rep(m):
        i = m.start()
        before = en[:i]
        if i == 0 or before[-1] == ' ' or before.endswith('[LR]'):
            return m.group(0)
        return ' ' + m.group(0)
    return re.sub(CODE_RE, rep, en)


def restore_tic(jp, en):
    """If the Japanese uses Ricky's kero/dasu codes but the English kept none of
    them (nor a literal kero/dasu), put the last one back at the end of the
    final clause. The drop step removes it again if there is no room."""
    codes = re.findall(TIC_RE, jp)
    if not codes or re.search(TIC_RE, en) or re.search(r'(?i)(kero|dasu)', en):
        return en
    m = re.search(r'([!?…～♪♥.,\s]|\[LR\])*$', en)
    cut = m.start() if m else len(en)
    if cut == 0:
        return en
    return en[:cut] + ' ' + codes[-1] + en[cut:]


def human_pairs():
    """Japanese -> English pairs from the human-written patch files, so identical
    strings in other characters' files reuse the human translation."""
    pairs = {}
    for f in sorted(glob.glob(os.path.join(ROOT, 'patches', '*.txt'))):
        b = os.path.basename(f)
        if b.startswith('ricky_') or '_ai_' in b or b in ('boot.txt', 'param.txt'):
            continue
        lines = open(f, encoding='utf-8').read().splitlines()
        jp = None
        injmp = False
        buf = []
        for line in lines:
            st = line.strip()
            if st.startswith('//'):
                c = st[2:].split(' -- ')[0].strip()
                if c.endswith('<END>'):
                    jp = c[:-5]
                elif re.search('[぀-ヿ一-鿿]', c):
                    jp = c
                continue
            if st.startswith('#JMP'):
                injmp = True
                buf = []
                continue
            if st.startswith('#') or not st:
                continue
            if injmp:
                buf.append(st)
                if st.endswith('<END>'):
                    en = ''.join(buf)[:-5]
                    if jp and jp not in pairs:
                        pairs[jp] = en
                    injmp = False
                    jp = None
    return pairs


def covered(char):
    s = set()
    for f in sorted(glob.glob(os.path.join(ROOT, 'patches', '%s*.txt' % char))):
        if f.endswith('_dictionary.txt') or os.path.basename(f).startswith('%s_ai' % char):
            continue
        if char == 'ricky':
            continue
        for m in re.finditer(r'#JMP\(\$([0-9A-Fa-f]+)\)', open(f, encoding='utf-8').read()):
            s.add(int(m.group(1), 16))
    return s


LABEL = re.compile(r'[^\[\]<>$ ]*_\d+[a-z]?')


def is_label(t):
    """Internal script labels such as 'におい_43b' or '入力_34' are never shown."""
    return bool(LABEL.fullmatch(t))


def strings(char):
    ksc = CHARS[char][0]
    return kscparse.extract(os.path.join(ROOT, 'extract', ksc + '.KSC'))


def worklist(char):
    cov = covered(char)
    hp = human_pairs()
    seen = {}
    rows = []
    for off, ln, t in strings(char):
        if off in cov or is_label(t) or t in hp:
            continue
        if t in seen:
            seen[t][1] += 1
            continue
        r = [off, 1, ln, t]
        seen[t] = r
        rows.append(r)
    os.makedirs(os.path.join(ROOT, 'ai_work', char), exist_ok=True)
    with open(os.path.join(ROOT, 'ai_work', char, 'worklist.tsv'), 'w', encoding='utf-8') as f:
        for off, cnt, ln, t in rows:
            f.write('%X\t%d\t%d\t%s\n' % (off, ln, cnt, t))
    print('%s: %d unique untranslated strings' % (char, len(rows)))


# Shorthands allowed in ai_work/*.tsv for catchphrase codes without a table name
ALIASES = {'{DASU}': '<$17><$19><$00>', '{HAA}': '<$17><$1B><$00>', '{C18}': '<$17><$18><$00>'}


def load_translations(char):
    tr = {}
    for f in sorted(glob.glob(os.path.join(ROOT, 'ai_work', char, '*.tsv'))):
        if os.path.basename(f) == 'worklist.tsv':
            continue
        for i, line in enumerate(open(f, encoding='utf-8')):
            line = line.rstrip('\r\n')
            if not line.strip() or line.startswith('#'):
                continue
            cols = line.split('\t')
            if len(cols) < 2:
                print('%s:%d: bad line' % (f, i + 1)); continue
            for a, b in ALIASES.items():
                cols[1] = cols[1].replace(a, b)
            unsure = cols[2][1:].strip() if len(cols) > 2 and cols[2].startswith('?') else None
            tr[int(cols[0], 16)] = (cols[1], unsure, '%s:%d' % (os.path.basename(f), i + 1))
    return tr


def build(char):
    ksc, name = CHARS[char]
    strs = strings(char)
    cov = covered(char)
    byoff = {o: (l, t) for o, l, t in strs}
    tr = load_translations(char)
    bytext = {}
    errors = 0
    for off, (en, unsure, src) in tr.items():
        if off not in byoff:
            print('%s: offset %X is not a known string start' % (src, off)); errors += 1; continue
        bytext[byoff[off][1]] = (en, unsure, src)
    for jp, en in human_pairs().items():
        if jp not in bytext:
            bytext[jp] = (en, None, 'human:' + jp[:12])
    out = [HEADER.format(ksc=ksc, name=name, char=char)]
    n = 0
    nun = 0
    nskip = 0
    reported = set()
    for off, ln, t in strs:
        if off in cov or t not in bytext:
            continue
        en, unsure, src = bytext[t]
        if en == '-':
            nskip += 1
            continue
        raw = space_codes(restore_tic(t, en))

        def fit(text):
            text = wrap(text) if '[LR]' in t else text
            return (text,) + encode_len(text)
        en, blen, bad = fit(raw)
        # Like the human translators: if it does not fit, drop catchphrase codes
        # (and the space in front of them) first, then decorative wave dashes /
        # notes, then the Haa～ filler code. Done on the unwrapped text.
        for pat in (r' ?(?:\[KERO\]|\[NYA\]|<\$17><\$1[89]><\$00>)',
                    r'(?<=\S)[～♪](?=[!?…\[]|$)',
                    r' ?<\$17><\$1B><\$00> ?'):
            if blen <= ln:
                break
            raw2 = re.sub(pat, '', raw)
            if raw2 != raw:
                raw = raw2
                en, blen, bad = fit(raw)
        if (bad or blen > ln) and src.startswith('human:'):
            continue  # reused human translation that does not fit here: leave it
        if bad or blen > ln:
            if src not in reported:
                reported.add(src)
                if bad:
                    print('%s: %X unencodable chars %r' % (src, off, ''.join(bad)))
                else:
                    print('%s: %X too long (%d > %d): %s' % (src, off, blen, ln, en))
            errors += 1
            continue
        if unsure:
            out.append('// AI-UNSURE: %s\n' % unsure); nun += 1
        out.append('//%s<END>\n#JMP($%X)\n#FIXEDLENGTH(%d,0)\n%s<END>\n\n'
                   % (t, off, ln, en.replace('[LR]', '[LR]\n').rstrip('\n')))
        n += 1
    fn = 'ricky_messages.txt' if char == 'ricky' else '%s_ai_messages.txt' % char
    with open(os.path.join(ROOT, 'patches', fn), 'w', encoding='utf-8', newline='\n') as f:
        f.write(''.join(out))
    print('%s: wrote %d entries (%d AI-UNSURE, %d skipped as non-text), %d errors'
          % (fn, n, nun, nskip, errors))
    return errors


if __name__ == '__main__':
    cmd, char = sys.argv[1], sys.argv[2]
    if cmd == 'worklist':
        worklist(char)
    else:
        sys.exit(1 if build(char) else 0)
