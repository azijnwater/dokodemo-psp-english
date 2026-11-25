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
| NEKO.KSC (Toro) | `patches/toro_ai_messages.txt` | 14,497 | 844 | 13,377 (+251 reused human) | 185 | 63 | 0 |
| ROBO.KSC (Suzuki) | — | 10,003 | 17 | 0 | 0 | 0 | 9,294 |
| USAGI.KSC (Jun) | — | 10,629 | 13 | 0 | 0 | 0 | 9,762 |
| INU.KSC (Pierre) | — | 11,522 | 29 | 0 | 0 | 0 | 10,418 |

"AI entries" counts every patched offset (one translation can cover several
identical strings). **Ricky and Toro are complete** (all detected KAERU.KSC strings are translated, reused from an
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
  Toro worklist (patch `patches/toro_ai_messages.txt`, complete).
- **Atlas `#` gotcha**: a script line that starts with `#` is read as an Atlas command
  ("Nonalphabetical character in command"). `gen_patch.py` now never breaks a line in
  front of `#` and rejects text that would start with `#`.

## Toro save coverage

Scope (user decision): everything a player sees in a save where they picked Toro.
Suzuki (ROBO), Jun (USAGI) and Pierre (INU) are parked until the user has played Toro.

| Phase | What | Status |
|------|------|--------|
| 1 | NEKO.KSC (all Toro dialogue, diary/outing/room-item/menu strings) | **done**: 0 untranslated |
| 2 | NEKO.DIC (Toro's dictionary) | **done**: 151 of 160 words (9 left in Japanese) |
| 3 | BOOT.BIN system text | **done** for real menu/system text (56 strings); keyboards and staff names deliberately left |
| 4 | Other DATA.BP text | **surveyed**: no other script text; nothing to patch |
| 5 | GUI textures with Japanese | **reported** (2 groups left for a human) |

### Phase 1 notes (NEKO.KSC)
- 185 entries are marked `// AI-UNSURE` in `patches/toro_ai_messages.txt`. Most are
  **typed-answer match words**: groups such as ふとん/フトン/布団 or さかな/サカナ that Toro
  compares against what the player typed. They were translated to the English word
  (sometimes truncated to fit, e.g. `Chor`, `Mout`). If the English build's keyboard
  produces different spellings, these matches will not trigger; a human should check
  them against the keyboard in `patches/boot.txt`.
- Negative adjective stems (`胸キュンじゃ`, `カワイく` …, KSC ~$97FB7–$98097) are used
  inside sentence templates; they were translated as full negatives ("Not cute").
- Speech-ending choices です/でござる/でちゅ ($9DEF2–$9DF00) were romanised
  (`desu`, `degozaru`, `dechu`).
- A few single-particle fragments (に, は, を, には, て, も, け, き, め) were left in Japanese
  (skipped): their use in templates is unclear and English has no equivalent.
- Signboards, shop names and room-item names are often heavily abbreviated to fit
  (e.g. `$_WORDTast`, `Shd1`). One item lost its `$_WORD`: "Umbrella" ($93B76).
- Test strings (最大文字数八文字 …) and binary noise were skipped.

### Phase 2 notes (NEKO.DIC)
- New patch `patches/toro_ai_dictionary.txt`, generated by `scripts/ai/gen_dic.py build toro`
  from `ai_work/toro_dic/0001.tsv`. It covers the 160 dictionary words not in the human
  `patches/toro_dictionary.txt`.
- A .DIC entry is `<index kana> 00 20 <display> 00 <reading> 00`. Like the human patch,
  the same English goes into both fields, so it must fit the shorter of the two.
- Words are lowercase nouns without articles ("cat", "miso", "pillow fight"), because
  [WORD]/$_WORD drops them mid-sentence ("I wanna eat [WORD1]"). Proper nouns and
  "PC" are capitalised.
- Left in Japanese (no English fits 2–4 bytes): 顔, 目, 恋, 愛, スシ, 新宿, 原宿, 浅草, 学校.
  Shortened to fit, e.g. 早起き → "up early", 肩たたき → "back rub",
  歯ブラシ → "brush", 図書館 → "books", 勉強 → "cram".
- `build.cmd` and `build.sh` now send any `patches/<char>*dictionary*.txt` to the .DIC
  (previously only `<char>_dictionary.txt`). In `build.cmd` this is
  `set "pname=%%~nF"` + `if /I not "!pname:dictionary=!"=="!pname!"` (delayed expansion
  is already enabled at the top of the script). Not run, by instruction; checked by reading.

### Phase 3 notes (BOOT.BIN)
- New patch `patches/boot_ai.txt` (generated by `scripts/ai/gen_boot.py` from
  `ai_work/boot/0001.tsv`). `build.cmd` and `build.sh` apply it right after `boot.txt`.
  The unmodified BOOT.BIN comes from the ISO
  (`tools-Zipz.exe e -oai_scratch ddipsp.iso PSP_GAME/SYSDIR/BOOT.BIN`, gitignored
  `ai_scratch/`).
- Scan method: every null-terminated Shift-JIS string in BOOT.BIN; the real text sits at
  $D8000–$DFC00 (everything else was binary noise). All bytes changed by boot.txt +
  boot_ai.txt are between $D8194 and $DE4F7; every string is replaced with
  `#FIXEDLENGTH` = its original length, so the terminator after it is never touched.
- Translated: the second Pokepi name table ($D8B10–$D8B54; アイコ → "Aiko", use unknown,
  AI-UNSURE), "○：確認" prompt ($D8BE4), a date format ($DBA68 → `%2d/%2d`), the ad-hoc
  "connecting" message ($DD9D0), and the **staff credits** role titles and company
  names ($DDE34–$DE4E8).
- **Left for a human:**
  - Staff names in the credits stay in Japanese: their readings (e.g. 對馬, 鍛代, 五十峯)
    can't be romanised reliably. Company readings marked AI-UNSURE: オニグンソー, あら井鮨,
    光念寺, 大栄製菓, 健和.
  - Keyboard tables: boot.txt already turned the hiragana keypad ($D92C8–$D9494) into
    letters, and the game has its own abc/ABC pads ($D95D0–$D9684). Still kana: the
    katakana pad ($D9364, $D9468–$D95B8) and the hiragana-only pad ($D9630–$D973C,
    probably the word-reading input). The latter feeds the kana range table at $D9F48
    (used for sorting/validation), so changing it could break word entry; not patched.
  - `%s 反転状態にします` / `%s 通常状態にします` ($DFA94/$DFAAC) look like debug output; not patched.
  - Full-width symbol/letter tables ($D9B4C–$D9CC0) and bracket lists ($D89F8) are character
    sets, not text; not patched.
- Typed-answer match words in NEKO.KSC (phase 1) should now work: the default keypad
  types English letters.

### Phase 4 notes (other DATA.BP text)
- DATA.BP (from the ISO, gitignored `ai_scratch/`) was unpacked with
  `toolsparpar_cosmo.com -x`: 731 BPMs. Families: `F*` fonts (68), `W*/E*/D*/S*`
  (≈490, each a single GIM: picture-diary photos/drawings and event pictures per Pokepi,
  `_N` = Toro), `BG_*` backgrounds and room-item 3D models, `*CG` character models,
  `KS*` (KSC/DIC, already handled) and the GUI archives (DATA, TITLE, OPTION, ENIKKI,
  ENIKKI_O, MKOTOBA, MTOMO, MOCHI, MEISHI, PRESENT, SHIRITORI, TSUUSHIN, QUICK).
- Every non-image file in those archives was scanned for Shift-JIS text:
  - GUI layout files (`*.CB2A`) and models (`*.DVS/*.DAK/*.ASC`): no text, only noise.
  - `DATA/GUI/DIC/NJ*.A`, `CUSTOM.A`: the software keyboard's kana→kanji conversion
    dictionary (IME). Conversion candidates, not displayed game text; left alone.
  - `DATA/FONT/FONT.XFT`: the font.
  - `SBOARD.BPM` only holds a dummy texture: town signboard text comes from NEKO.KSC
    (translated in phase 1).
- Result: in a Toro save, all script text lives in NEKO.KSC, NEKO.DIC and BOOT.BIN.
  Item, gift, shiritori and name-card *text* is in NEKO.KSC (done); what's left
  is in textures (phase 5). No build-script changes were needed for phase 4.
- The diary/event pictures are real photos and drawings. Some photos contain incidental
  Japanese signs, which are scenery, not UI text.

### Phase 5 notes (GUI textures, report only)
All 781 GUI GIMs from the archives above were converted to PNG and compared against the
198 already-translated textures in `textures/GUI/`. Of the 583 not yet replaced, almost
all are frames, bars, icons or already-English (abc/ABC keypad keys, "Yes/No",
"Option", "COUNTDOWN", name-card labels). **Still Japanese and visible in normal Toro
play:**

| Texture (DATA.BP path) | Contents | Notes |
|---|---|---|
| `GUI/TITLE/ALERT.GIM` | CERO "rating pending" + "this software may differ from the retail version…" boot warning | Shown at boot. Plain white text on black, easy to remake. |
| `GUI/KOTOBA_MEMO/TABMENU1.GIM`–`TABMENU10.GIM` | Kana index tabs あ か さ た な は ま や ら わ of the word memo (ABC tab TABMENU11 is already English) | Words are still filed under their Japanese index kana (the .DIC index field was not changed), so these tabs still match the data. Changing them needs a decision on sorting English words. |

Not counted as text: tiny item icons in `GUI/MOCHIMONO` (`I_*.GIM`, e.g. a poster or shop
sign drawn on an icon).
No new images were made: these need someone who can match the existing translated
textures' style.
