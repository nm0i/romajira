# romajira

romajira is a single-file terminal flashcard trainer for drilling the romaji readings of hiragana and katakana.

![romajira screenshot](scrshot.png)

Run it with `python3 romajira.py` or just `./romajira.py`.

## Dependencies

None. romajira is one Python 3 file using only the standard library (`curses`); any terminal with a UTF-8 locale works.

## Project intent

Reading kana has to become automatic before it's useful, and that only happens through fast, repeated recall. romajira is a minimal drill for exactly that: it shows one random character, you type the romaji, and it keeps score.

- Answers are checked leniently — common alternative romanizations are accepted (`shi`/`si`, `tsu`/`tu`, `wo`/`o`, `ji`/`zi`, …), so spelling conventions never interrupt the drilling.
- A first miss reveals a masked hint (one character hidden); a second miss shows the full answer, and the character stays up until you get it right.
- Tab switches between the hiragana and katakana pools.
- Ctrl+F / Ctrl+J toggles a full kana reference table you can keep open while drilling.

## Difficulty

The drill starts at the maximum difficulty, where every kana is in the random pool. Press `-` to make it easier and `+` (or `=`) to make it harder; the current level is shown in the top-left corner together with how many kana are in play.

| Level | Pool                                            |
| ----- | ----------------------------------------------- |
| 6     | all kana (includes "Rare in general text")      |
| 5     | up to "Less frequent"                           |
| 4     | up to "Less common"                             |
| 3     | up to "Moderately common"                       |
| 2     | up to "Common"                                  |
| 1     | "Very common" only (12 kana)                    |

