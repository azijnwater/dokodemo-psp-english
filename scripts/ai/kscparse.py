"""
Locate text strings inside a Doko Demo Issyo PSP .KSC script file.

Used by the AI translation tooling (see docs/AI_TRANSLATION_LOG.md).
A string is a run of Shift-JIS text / control codes ending in a 0x00 byte
that is not part of a control code. Strings start either right after a 0x48
or 0x8E "text" marker byte, or right after the 0x00 terminator of the previous
string (string tables, e.g. diary words).

Control codes (see shiftjis.tbl):
  0A             [LR]
  85 40          heart
  17 xx 00       catchphrase codes ([NYA] = 17 17 00, [KERO] = 17 1A 00, others
                 are written as raw <$17><$xx><$00>)
  16 14 xx 00 16 [WORDxx]
  14 xx 00       [VARxx]
"""
import re
import sys


def lead(b):
    return 0x81 <= b <= 0x9F or 0xE0 <= b <= 0xFC


def trail(b):
    return 0x40 <= b <= 0x7E or 0x80 <= b <= 0xFC


CODE17 = {0x17: '[NYA]', 0x1A: '[KERO]'}


def parse_at(d, s):
    """Parse the string starting at s up to its 0x00 terminator.
    Returns (end, text, ok, badness)."""
    j = s
    out = []
    n = len(d)
    bad = 0
    while j < n:
        b = d[j]
        if b == 0:
            return j, ''.join(out), True, bad
        if j + 1 >= n:
            break
        if b == 0x0A:
            out.append('[LR]'); j += 1; continue
        if b == 0x85 and d[j + 1] == 0x40:
            out.append('♥'); j += 2; continue
        if b == 0x17 and j + 2 < n and d[j + 2] == 0:
            c = d[j + 1]
            out.append(CODE17.get(c, '<$17><$%02X><$00>' % c)); j += 3
            if c not in (0x17, 0x18, 0x19, 0x1A, 0x1B):
                bad += 3
            continue
        if b == 0x16 and j + 4 < n and d[j + 1] == 0x14 and d[j + 3] == 0 and d[j + 4] == 0x16:
            out.append('[WORD%d]' % d[j + 2]); j += 5
            if d[j - 3] > 15:
                bad += 3
            continue
        if b == 0x14 and j + 2 < n and d[j + 2] == 0:
            out.append('[VAR%d]' % d[j + 1]); j += 3
            if d[j - 2] > 15:
                bad += 3
            continue
        if 0x20 <= b <= 0x7E:
            out.append(chr(b)); j += 1; continue
        if 0xA1 <= b <= 0xDF:
            out.append(bytes([b]).decode('cp932')); j += 1; bad += 1; continue
        if lead(b) and trail(d[j + 1]):
            if b >= 0xF0 or b in (0x85, 0x86, 0x87):
                bad += 5  # user-defined / unused Shift-JIS rows: not real text
            try:
                out.append(d[j:j + 2].decode('cp932'))
            except UnicodeDecodeError:
                out.append('<$%02X><$%02X>' % (b, d[j + 1])); bad += 5
            j += 2
            continue
        return j, ''.join(out), False, bad
    return j, ''.join(out), False, bad


JPc = '぀-ヿ一-鿿！-～　-〿'
JP = re.compile('[%s]' % JPc)
KANA = re.compile('[぀-ヿ]')
ADJ = re.compile(r'(?<![\[$_A-Za-z0-9])[A-Za-z](?=[぀-ヿ一-鿿])'
                 r'|(?<=[぀-ヿ一-鿿])[A-Za-z](?![A-Za-z0-9\]])')


def score(t, bad):
    s = bad + 3 * len(ADJ.findall(re.sub(r'\[[A-Z]+\d*\]|\$_[A-Z0-9]+', '', t)))
    if re.match('[A-Za-z]', t):
        s += 1
    return s


def extract(path):
    d = open(path, 'rb').read()
    n = len(d)
    best = {}  # end -> (score, start, text)
    for p in range(1, n - 1):
        if d[p - 1] not in (0x00, 0x48, 0x8E) or d[p] == 0:
            continue
        e, t, ok, bad = parse_at(d, p)
        if not ok or e - p < 2 or not JP.search(t):
            continue
        sc = score(t, bad)
        if d[p + 1] == 0x51 and d[p + 2] == 0x48:
            sc += 5  # "xx 51 48" is an opcode followed by the 0x48 text marker
        cur = best.get(e)
        if cur is None or sc < cur[0] or (sc == cur[0] and p < cur[1]):
            best[e] = (sc, p, t)
    res = []
    for e, (sc, p, t) in sorted(best.items(), key=lambda x: x[1][1]):
        if sc > 2:
            continue
        if not KANA.search(t) and len(JP.findall(t)) < 2:
            continue
        res.append((p, e - p, t))
    out = []
    last_end = -1
    for p, l, t in res:
        if p < last_end:
            continue
        out.append((p, l, t))
        last_end = p + l
    return out


if __name__ == '__main__':
    for s, l, t in extract(sys.argv[1]):
        print('%X\t%d\t%s' % (s, l, t))
