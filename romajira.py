#!/usr/bin/env python3

import curses
import locale
import os
import random
import unicodedata

LBLW = 3
CELLW = 8
FIELD = 16
MIN_W = 40
MIN_H = 11
QUIT_KEYS = (3, 27)
TABLE_KEYS = (6, 10)
SCRIPT_KEY = 9
ENTER_KEYS = (13, curses.KEY_ENTER)
BACKSPACE_KEYS = (8, 127, curses.KEY_BACKSPACE)

KANA_ROWS = [
    ("", [("あ", "a"), ("い", "i"), ("う", "u"), ("え", "e"), ("お", "o")]),
    (
        "k",
        [("か", "ka"), ("き", "ki"), ("く", "ku"), ("け", "ke"), ("こ", "ko")],
    ),
    (
        "s",
        [
            ("さ", "sa"),
            ("し", "shi"),
            ("す", "su"),
            ("せ", "se"),
            ("そ", "so"),
        ],
    ),
    (
        "t",
        [
            ("た", "ta"),
            ("ち", "chi"),
            ("つ", "tsu"),
            ("て", "te"),
            ("と", "to"),
        ],
    ),
    (
        "n",
        [("な", "na"), ("に", "ni"), ("ぬ", "nu"), ("ね", "ne"), ("の", "no")],
    ),
    (
        "h",
        [("は", "ha"), ("ひ", "hi"), ("ふ", "fu"), ("へ", "he"), ("ほ", "ho")],
    ),
    (
        "m",
        [("ま", "ma"), ("み", "mi"), ("む", "mu"), ("め", "me"), ("も", "mo")],
    ),
    ("y", [("や", "ya"), None, ("ゆ", "yu"), None, ("よ", "yo")]),
    (
        "r",
        [("ら", "ra"), ("り", "ri"), ("る", "ru"), ("れ", "re"), ("ろ", "ro")],
    ),
    ("w", [("わ", "wa"), None, None, None, ("を", "wo")]),
    ("n", [("ん", "n"), None, None, None, None]),
    (
        "g",
        [("が", "ga"), ("ぎ", "gi"), ("ぐ", "gu"), ("げ", "ge"), ("ご", "go")],
    ),
    (
        "z",
        [("ざ", "za"), ("じ", "ji"), ("ず", "zu"), ("ぜ", "ze"), ("ぞ", "zo")],
    ),
    (
        "d",
        [("だ", "da"), ("ぢ", "ji"), ("づ", "zu"), ("で", "de"), ("ど", "do")],
    ),
    (
        "b",
        [("ば", "ba"), ("び", "bi"), ("ぶ", "bu"), ("べ", "be"), ("ぼ", "bo")],
    ),
    (
        "p",
        [("ぱ", "pa"), ("ぴ", "pi"), ("ぷ", "pu"), ("ぺ", "pe"), ("ぽ", "po")],
    ),
]

ALT = {
    "し": {"shi", "si"},
    "ち": {"chi", "ti"},
    "つ": {"tsu", "tu"},
    "ふ": {"fu", "hu"},
    "を": {"wo", "o"},
    "じ": {"ji", "zi"},
    "ぢ": {"ji", "di"},
    "づ": {"zu", "du"},
    "ん": {"n", "nn"},
}

TABLE_W = LBLW + 5 * CELLW
TABLE_H = len(KANA_ROWS) + 2


def to_kata(h):
    return chr(ord(h) + 0x60)


def kana(h, script):
    return h if script == 0 else to_kata(h)


def wlen(s):
    return sum(
        2 if unicodedata.east_asian_width(c) in ("W", "F") else 1 for c in s
    )


def pad(s, w):
    d = w - wlen(s)
    return s + (" " * d if d > 0 else "")


def clip(s, w):
    out = []
    cur = 0
    for c in s:
        cw = 2 if unicodedata.east_asian_width(c) in ("W", "F") else 1
        if cur + cw > w:
            break
        out.append(c)
        cur += cw
    return "".join(out)


def put(scr, y, x, s):
    H, W = scr.getmaxyx()
    if 0 <= y < H and 0 <= x < W:
        try:
            scr.addstr(y, x, clip(s, W - x))
        except curses.error:
            pass


def pool(script):
    out = []
    for _, cells in KANA_ROWS:
        for c in cells:
            if c is None:
                continue
            h, r = c
            out.append((kana(h, script), r, {r} | ALT.get(h, set())))
    return out


POOLS = [pool(0), pool(1)]


def pick(script, avoid=None):
    p = POOLS[script]
    while True:
        ch, r, acc = random.choice(p)
        if ch != avoid:
            return ch, r, acc


def masked(r, accepted):
    if len(r) < 2:
        return "*"
    if r[-1] in accepted:
        return r[:-1] + "*"
    if random.getrandbits(1):
        return r[:-1] + "*"
    return "*" + r[-1]


def table_lines(script):
    lines = []
    for label, cells in KANA_ROWS:
        parts = [pad(label, LBLW)]
        for c in cells:
            if c is None:
                parts.append(" " * CELLW)
            else:
                h, r = c
                parts.append(pad(kana(h, script) + " " + r, CELLW))
        lines.append("".join(parts))
    return lines


def draw_table(scr, top, W, script):
    lines = table_lines(script)
    header = pad("", LBLW) + "".join(pad(v, CELLW) for v in "aiueo")
    content = [header] + lines
    title = "Hiragana to romaji" if script == 0 else "Katakana to romaji"
    inner = max(wlen(l) for l in content)
    left = max(0, (W - inner) // 2)
    put(scr, top, left + max(0, (inner - wlen(title)) // 2), title)
    for i, l in enumerate(content):
        put(scr, top + 1 + i, left, l)


def draw_core(scr, H, W, ch, user_input, message, correct, total):
    char_row = H - 6
    input_row = H - 4
    msg_row = H - 2
    lead = "What is this character:  ["
    line = lead + ch + "]"
    x = max(0, (W - wlen(line)) // 2)
    x += x & 1
    put(scr, char_row, x, line)
    field = "[" + user_input.ljust(FIELD) + "]"
    fx = max(0, (W - wlen(field)) // 2)
    put(scr, input_row, fx, field)
    if message:
        mx = max(0, (W - wlen(message)) // 2)
        put(scr, msg_row, mx, message)
    put(scr, H - 1, 1, "tab:script | ctrl+f/j:table | enter | esc")
    stats = "%d/%d" % (correct, total)
    put(scr, 0, max(1, W - wlen(stats) - 1), stats)


def main(scr):
    scr.keypad(True)
    curses.nonl()
    try:
        curses.curs_set(0)
    except curses.error:
        pass
    script = 0
    show_table = False
    ch, romaji, accepted = pick(0)
    user_input = ""
    message = ""
    fails = 0
    correct = 0
    total = 0
    while True:
        H, W = scr.getmaxyx()
        scr.erase()
        too_small = W < MIN_W or H < MIN_H
        if too_small:
            put(scr, H // 2 - 1, 1, "Terminal too small.")
            put(
                scr,
                H // 2,
                1,
                "Need at least %dx%d. Now %dx%d." % (MIN_W, MIN_H, W, H),
            )
            put(scr, H // 2 + 1, 1, "Resize, or press ctrl+c to quit.")
        else:
            fits = W >= TABLE_W and H >= TABLE_H + 8
            if show_table:
                if fits:
                    draw_table(scr, 1, W, script)
                else:
                    put(
                        scr,
                        2,
                        max(0, (W - 40) // 2),
                        "Table doesn't fit. Enlarge the terminal.",
                    )
            draw_core(scr, H, W, ch, user_input, message, correct, total)
        scr.refresh()
        key = scr.getch()
        if key in QUIT_KEYS:
            break
        if key == curses.KEY_RESIZE:
            continue
        if too_small:
            continue
        if key in TABLE_KEYS:
            show_table = not show_table
        elif key == SCRIPT_KEY:
            script = 1 - script
            ch, romaji, accepted = pick(script)
            user_input = ""
            message = ""
            fails = 0
        elif key in ENTER_KEYS:
            total += 1
            if user_input.strip().lower() in accepted:
                correct += 1
                ch, romaji, accepted = pick(script, ch)
                user_input = ""
                message = ""
                fails = 0
            else:
                fails += 1
                message = "Try again, it's " + (
                    masked(romaji, accepted) if fails == 1 else romaji
                )
        elif key in BACKSPACE_KEYS:
            user_input = user_input[:-1]
        elif 32 <= key <= 126:
            user_input = (user_input + chr(key))[:FIELD]
    try:
        curses.curs_set(1)
    except curses.error:
        pass


if __name__ == "__main__":
    locale.setlocale(locale.LC_ALL, "")
    if "utf" not in locale.getpreferredencoding(False).lower():
        print("romajira needs a UTF-8 terminal locale")
        raise SystemExit(1)
    os.environ["ESCDELAY"] = "25"
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
