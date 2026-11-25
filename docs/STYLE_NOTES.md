# Translation style notes

These notes record how the existing human fan translations (`toro_messages.txt`,
`toro_diary.txt`, `suzuki_messages.txt`, `jun_messages.txt`, `pierre_excel.txt`,
`boot.txt`) render the game, so that the AI-assisted translations on the
`ai-translation` branch match their voice. Faithfulness to the Japanese comes first:
keep each Pokepi's verbal tics, cuteness and jokes, and keep Japanese-specific
things recognizable instead of swapping in Western equivalents.

## Characters and their speech

| File | Pokepi | Speech in Japanese | How it is rendered |
|------|--------|--------------------|--------------------|
| NEKO.KSC | **Toro** (cat) | ends sentences with ニャ (`[NYA]`), says ふにゃ～, にゃ♥ | keeps `[NYA]` where it falls in the sentence; literal ニャ written as "nya"/"meow" ("Oh nya～", "Nya ♥", "smarter again, meow!"). Childlike, eager, wants to become human. |
| ROBO.KSC | **Suzuki** (robot) | 〜なのだ, scientific/know-it-all, ナリ | slightly formal, nerdy ("My dream is～ … I will unravel it all!"). Catchphrase table entry ロボ → "beep". |
| USAGI.KSC | **Jun** (rabbit) | ピョン catchphrase, casual girly, ～♥, ぉ/ー stretching | bubbly, casual ("I'll always be here to look out for you! ♥"). Catchphrase table entry ピョン → "squeak". |
| INU.KSC | **Pierre** (dog) | ワン-style ending code, polite but airy, ♥ a lot | gentle, refined; drops the code when there is no room. |
| KAERU.KSC | **Ricky** (frog) | ケロ (`[KERO]`), ダス (rustic copula, code `<$17><$19><$00>`), ハァ～ filler (`<$17><$1B><$00>`), ～ッス, オラ (rural "I"); dreams of being 世界最強 (the strongest in the world), martial-arts 修行 (training) | rustic, earnest, a bit of a country boy. The `[KERO]` and ダス codes are kept at the end of the clause like Toro's `[NYA]`; literal ケロ/ダス in the text become "kero"/"dasu". 修行 = "training". 世界最強 = "the strongest in the world". |

### Catchphrase codes (`17 xx 00`)
The game expands these codes at run time from a small per-character string table
(NEKO.KSC `$8E1C8` ニャ → "meow", USAGI.KSC `$67F6C` ピョン → "squeak", ROBO.KSC
`$6C088` ロボ → "beep"). Only `[NYA]` (17 17 00) and `[KERO]` (17 1A 00) have names
in `shiftjis.tbl`; the others are written as raw bytes, e.g. `<$17><$19><$00>`.
Keep them in roughly the same place as in the Japanese (usually the end of a
clause, before the punctuation): `おしえて ほしい[NYA]～` → `I want to know [NYA]～`.
If there is no room, the human translators drop the code; that is acceptable.

Ricky's table at KAERU.KSC `$6BF54`: オラ / ケロ / ダス / ハァ～. Observed usage:
`[NYA]` (17 17) = オラ "I" (used once), `<$17><$19><$00>` = ダス, `[KERO]` (17 1A) = ケロ,
`<$17><$1B><$00>` = ハァ～ (a thinking/sighing filler, often alone on a line), `<$17><$18><$00>`
(rare, question endings) = unknown. AI translation of the table: ケロ → `kero`, ダス → `dasu`,
ハァ～ → `Haa～`; オラ left as is (unused in the English text).

## Control codes and variables
- `[LR]` line break. Original strings almost always end with `[LR]`; keep it at the end.
  The human translators break long lines with extra `[LR]`s (about 140px per line,
  see `scripts/char_widths.txt` / `scripts/word_wrap.py`); the generator does this automatically.
- `[WORD0]`, `[WORD1]` … a word the player taught (or the player's name, depending on
  the scene). Keep every `[WORDn]` / `[VARn]` / `<$14><$xx><$00>` that the original has.
  Possessive: humans write `[WORD1]'s` (sometimes `[WORD1]s` when short of bytes).
- `$_YOU` (player), `$_WORD`, `$_W1`, `$_W2`, `$_OPP` (opposite sex) in diary/item strings
  are plain ASCII tokens interpreted by the game — copy them exactly.
- Strings without a final `[LR]` are usually menu choices, labels, or the first half of a
  line that the next string continues; don't add `[LR]` to those.

## Punctuation and typography
- Ellipsis: use `…` (one full-width character, 2 bytes) like the humans, not `...`.
- Wave dash `～` for drawn-out/singsong endings ("Um～", "Tsk～", "I want to know [NYA]～").
- `♥` (2 bytes, table entry 8540) and `♪` (81F4) kept as in Japanese, usually right
  after the word: "Thanks for teaching me, [NYA] ♥".
- `！`/`？` full-width or `!`/`?` ASCII are both in the table; prefer ASCII (1 byte).
- Japanese quote brackets 「」 become straight double quotes `"…"` (curly quotes are NOT in the table).
- Only characters present in `shiftjis.tbl` may be used (no curly apostrophes, no
  non-breaking spaces). Use ASCII `'`.
- Capitalize sentence starts; lower-case after `…` when the sentence continues.

## Honorifics and names
- Keep honorifics as suffixes: さん → `-san`, ちゃん → `-chan`, くん → `-kun`, さま → `sama`,
  先生 → `-sei` (truncated "sensei", length-limited) / "teacher"/"master" in prose.
- Pokepi names: Toro, Suzuki, Jun, Pierre, Ricky, Kuro.
- ポケピ → "Pokepi".

## Recurring vocabulary (glossary)

| Japanese | English | Notes |
|----------|---------|-------|
| ことばメモ / コトバメモ | word memo / Notebook | humans use both; AI uses "word memo" |
| ともだちノート | friend notes / friend list | |
| おしえる (teach a word) | teach / tell | "What can you teach me?" |
| 人間になる | become (a) human | Toro's dream |
| 日記 / えにっき | diary | |
| しりとり | shiritori | word-chain game, keep Japanese name |
| めいし交換 | business card exchange | |
| プレゼント交換 | present exchange | |
| おみやげ | souvenir | |
| 修行 | training | Ricky's martial-arts training |
| 世界最強 | the strongest in the world | Ricky's goal |
| 先生 | master / teacher / -sei | |
| ニャ / [NYA] | nya / meow / [NYA] | |
| ケロ / [KERO] | kero / [KERO] | |
| ダス | dasu | |
| 正月 | New Year's | keep Japanese customs: 初詣 = first shrine visit of the year |
| おせち | osechi (New Year's food) | |
| こたつ | kotatsu | |
| お花見 | hanami / cherry-blossom viewing | |
| ひなまつり | Hinamatsuri | Dolls' Day |
| コドモの日 | Children's Day | |
| 七夕 | Tanabata | |
| お盆 | Obon | |
| 神社 | shrine | |
| お寺 / 寺 | temple | |
| 大福 | daifuku | |
| おむすび / おにぎり | rice ball | |
| 納豆 | natto | |
| エライ人 / 上の人 / 同じぐらいの人 / 下の人 | Greatest / Higher / Same ranking / Lower | menu |
| 大好き / 好き / ふつう / キライ / 大キライ | Loved / Like / Normal / Dislike / Hated | menu |
| 男の人 / 女の人 | man / woman | menu |
| バイバイ | Bye bye | |
| やっぱヤメ | Never mind | menu |

Add new terms here as they come up.

## Interjections (as rendered by humans)
| Japanese | English |
|----------|---------|
| あのね | You know / You know what |
| えっと / えとね | Um / Well |
| ねぇねぇ | Hey hey |
| ふにゃ～ | Oh nya～ |
| ちぇ～ | Tsk～ / Tut～ |
| ほひゃあ!? / うひゃぁ!? | Hoiyah!? / Uhyaa!? |
| そっか | I see |
| ふむふむ | Hmmmm |
| あ！ | Ah! / Oh! |
| む～ | Mmm～ |
| ハァ～ | Haa～ |
