# AI translation log

Branch: `ai-translation` (fork only — machine translation, not reviewed by the
upstream translation team). Style rules: [STYLE_NOTES.md](STYLE_NOTES.md).

## How it works

1. `python scripts/ai/gen_patch.py worklist <char>` scans the character's `.KSC`
   (`extract/<FILE>.KSC`) for every text string (`scripts/ai/kscparse.py`), drops
   the ones already covered by a `#JMP` in the human patch files, de-duplicates
   identical Japanese, and writes `ai_work/<char>/worklist.tsv`
   (offset, byte length, number of copies, Japanese). The worklist is gitignored
   because it is regenerated from the game files.
2. Translations are written to `ai_work/<char>/NNNN.tsv` as
   `OFFSET<TAB>English[<TAB>?reason]` (a `?reason` becomes an `// AI-UNSURE:` comment;
   `-` means "not real text, leave as is").
3. `python scripts/ai/gen_patch.py build <char>` writes the Atlas patch
   (`patches/ricky_messages.txt`, or `patches/<char>_ai_messages.txt` for the other
   characters). It applies each translation to every copy of the same Japanese
   string, measures the byte length with `shiftjis.tbl`, word-wraps at 140px with
   `[LR]` (only for strings that contain `[LR]` in the original), drops catchphrase
   codes / decorative `～♪` if needed to fit, and refuses anything that still does
   not fit or uses a character missing from the table.
4. Validation: copy `extract/*.KSC`/`*.DIC` into `insert/`, then run
   `tools/Atlas/Atlas.exe insert/<FILE>.KSC patches/<file>.txt` for every patch in
   build order; every file must report `Insertion - 0 error(s)`.

`python scripts/ai/stats.py` prints the progress numbers below.

## Progress

| File | Patch | Strings found in KSC | Human JMPs | AI entries | AI-UNSURE | Skipped (non-text) | Still untranslated (unique) |
|------|-------|---------------------:|-----------:|-----------:|----------:|-------------------:|----------------------------:|
| KAERU.KSC (Ricky) | `patches/ricky_messages.txt` | 10,798 | 0 | 9,915 (+252 reused human) | 16 | 169 | 0 |
| NEKO.KSC (Toro) | — | 14,497 | 844 | 0 | 0 | 0 | 12,326 |
| ROBO.KSC (Suzuki) | — | 10,003 | 17 | 0 | 0 | 0 | 9,294 |
| USAGI.KSC (Jun) | — | 10,629 | 13 | 0 | 0 | 0 | 9,762 |
| INU.KSC (Pierre) | — | 11,522 | 29 | 0 | 0 | 0 | 10,418 |

"AI entries" counts every patched offset (one translation can cover several
identical strings). **Ricky is complete** (all detected KAERU.KSC strings are translated, reused from an
identical human Toro/Jun/Suzuki/Pierre translation, or skipped as non-text). Internal
script labels such as `におい_43b` are filtered out automatically. Identical Japanese
strings that already have a human translation in another patch file (mostly diary
item names shared with Toro) reuse that translation when it fits ("reused human").

## Notes and problems

- **String detection**: the extractor (`scripts/ai/kscparse.py`) finds strings after
  a `0x48`/`0x8E` text marker or after the previous string's terminator. A few
  hundred hits per file are binary noise (e.g. `渦遺｣`, `!エ`, internal labels such as
  `入力_34`); these are marked `-` (skipped) when met. Single-kanji table entries
  (e.g. 海, 手) are not detected.
- **Catchphrase codes**: KAERU.KSC uses `17 17 00` … `17 1B 00`. Meanings inferred
  from context (see STYLE_NOTES.md); `<$17><$18><$00>` (61 uses) is still unknown.
  Ricky's catchphrase table (KAERU.KSC `$6BF54`) is translated: ケロ → `kero`,
  ダス → `dasu`, ハァ～ → `Haa～` (オラ left untranslated, unused). The generator puts a
  space before each code and restores a dropped kero/dasu when it fits; of 3,620
  Ricky entries whose Japanese has a kero/dasu code, 2,902 keep the tic in English
  (the rest had no room).
- **Length limits**: English often does not fit in the Japanese byte length; lines
  were shortened (sometimes dropping the `dasu`/`kero` code, as the human translators
  also do). Some 4-byte proper nouns could not be translated and were left in
  Japanese: hot-spring names 登別/草津/別府/鬼怒川, スシ, ピザ, 弁当, and a few
  4-byte place names in reply menus (浅草, 恐山, 鹿島, 八甲田, 桜井, 東京 …). Town
  signboard texts (KAERU.KSC ~$76700–$773D0) are heavily abbreviated
  (e.g. "Pachinko$_WORD", "$_WORDShrn").
- **Skipped as non-text (169 in KAERU.KSC)**: binary noise the extractor picked up,
  test strings (最大文字数八文字 …) and a few names that cannot be shortened.
- **Toro diary / messages**: in the current `fix/build-and-docs` base the strings
  after the `// TODO` comment in `patches/toro_diary.txt` already have
  `#JMP`/`#FIXEDLENGTH`; only ~25 commented-only words at the end of the file and
  some commented-only lines in `toro_messages.txt` remain. Rather than editing the
  human files, all NEKO.KSC strings without a `#JMP` anywhere are handled by the
  Toro worklist (patch `patches/toro_ai_messages.txt`, not started yet).
