#!/usr/bin/env python3

import curses
import locale
import os
import random
import unicodedata
from curses import ascii as cascii

LBLW = 3
CELLW = 8
FIELD = 16
HELP = "tab:script | difficulty:-/+ | ctrl+f/j:table | enter | esc"
MIN_W = len(HELP) + 1
MIN_H = 11
MIN_LEVEL = 1
MAX_LEVEL = 6
QUIT_KEYS = (3, 27)  # ctrl+c and esc
TABLE_KEYS = (6, 10)  # ctrl+f and ctrl+j
SCRIPT_KEY = 9  # tab
ENTER_KEYS = (13, curses.KEY_ENTER)  # enter
BACKSPACE_KEYS = (8, 127, curses.KEY_BACKSPACE)  # backspace and delete
DIFF_UP = (43, 61)  # '+' and '='
DIFF_DOWN = 45  # '-'

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

LEVEL = {
    # 1  Very common
    "い": 1,
    "し": 1,
    "う": 1,
    "ん": 1,
    "の": 1,
    "か": 1,
    "と": 1,
    "に": 1,
    "は": 1,
    "た": 1,
    "て": 1,
    "る": 1,
    # 2  Common
    "な": 2,
    "で": 2,
    "す": 2,
    "き": 2,
    "く": 2,
    "り": 2,
    "れ": 2,
    "ら": 2,
    "も": 2,
    "あ": 2,
    # 3  Moderately common
    "こ": 3,
    "ま": 3,
    "お": 3,
    "け": 3,
    "つ": 3,
    "さ": 3,
    "ち": 3,
    "ど": 3,
    "が": 3,
    "み": 3,
    "や": 3,
    # 4  Less common
    "わ": 4,
    "え": 4,
    "せ": 4,
    "じ": 4,
    "ほ": 4,
    "だ": 4,
    "ね": 4,
    "そ": 4,
    "よ": 4,
    "ば": 4,
    "め": 4,
    # 5  Less frequent
    "ふ": 5,
    "ゆ": 5,
    "へ": 5,
    "ろ": 5,
    "ひ": 5,
    "び": 5,
    "ご": 5,
    "む": 5,
    "ず": 5,
    "ぎ": 5,
    "ぶ": 5,
    # 6  Rare in general text
    "ぬ": 6,
    "ぐ": 6,
    "ざ": 6,
    "ぞ": 6,
    "ぜ": 6,
    "ぱ": 6,
    "ぽ": 6,
    "ぴ": 6,
    "ぷ": 6,
    "ぺ": 6,
}

TABLE_W = LBLW + 5 * CELLW
TABLE_H = len(KANA_ROWS) + 2


def to_kata(hiragana):
    return chr(ord(hiragana) + 0x60)


def kana(hiragana, script):
    return hiragana if script == 0 else to_kata(hiragana)


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


def put(scr, y, x, s, attr=curses.A_NORMAL):
    H, W = scr.getmaxyx()
    if 0 <= y < H and 0 <= x < W:
        try:
            scr.addstr(y, x, clip(s, W - x), attr)
        except curses.error:
            pass


def pool(script):
    out = []
    for _, cells in KANA_ROWS:
        for cell in cells:
            if cell is None:
                continue
            hiragana, romaji = cell
            out.append(
                (
                    kana(hiragana, script),
                    romaji,
                    {romaji} | ALT.get(hiragana, set()),
                    LEVEL.get(hiragana, MAX_LEVEL),
                )
            )
    return out


POOLS = [pool(0), pool(1)]


def pool_size(difficulty):
    return sum(1 for entry in POOLS[0] if entry[3] <= difficulty)


def pick(script, difficulty, avoid=None):
    candidates = [entry for entry in POOLS[script] if entry[3] <= difficulty]
    while True:
        char, romaji, accepted, _ = random.choice(candidates)
        if char != avoid:
            return char, romaji, accepted


def masked(romaji, accepted):
    if len(romaji) < 2:
        return "*"
    others = sorted(accepted - {romaji})
    if others:
        parts = [romaji[:-1] + "*"] + [o[:-1] + "*" for o in others]
        return " / ".join(parts)
    if random.getrandbits(1):
        return romaji[:-1] + "*"
    return "*" + romaji[-1]


def draw_table(scr, top, W, script, difficulty):
    title = "Hiragana to romaji" if script == 0 else "Katakana to romaji"
    left = max(0, (W - TABLE_W) // 2)
    put(scr, top, left + max(0, (TABLE_W - wlen(title)) // 2), title)
    header = pad("", LBLW) + "".join(pad(vowel, CELLW) for vowel in "aiueo")
    put(scr, top + 1, left, header)
    for row, (label, cells) in enumerate(KANA_ROWS):
        y = top + 2 + row
        x = left
        put(scr, y, x, pad(label, LBLW))
        x += LBLW
        for cell in cells:
            if cell is not None:
                hiragana, romaji = cell
                if LEVEL.get(hiragana, MAX_LEVEL) <= difficulty:
                    glyph = kana(hiragana, script)
                    put(scr, y, x, glyph + " " + romaji)
                    put(scr, y, x + wlen(glyph) + 1, romaji, curses.A_BOLD)
            x += CELLW


def draw_core(
    scr, H, W, char, user_input, message, correct, total, difficulty
):
    char_row = H - 6
    input_row = H - 4
    msg_row = H - 2
    lead = "What is this character:  ["
    line = lead + char + "]"
    x = max(0, (W - wlen(line)) // 2)
    # Keep wide glyphs on even columns: some terminals render double-width
    # characters misaligned (or as garbage) when they start on an odd column.
    x += x & 1  # Aligning to even
    put(scr, char_row, x, line)
    field = "[" + user_input.ljust(FIELD) + "]"
    fx = max(0, (W - wlen(field)) // 2)
    put(scr, input_row, fx, field)
    if message:
        mx = max(0, (W - wlen(message)) // 2)
        # Same even-column rule as above: the answer hint shows wide
        # characters (e.g. the kana itself) on some terminals.
        mx += mx & 1  # Aligning to even
        put(scr, msg_row, mx, message)
    put(scr, H - 1, 1, HELP)
    stats = "%d/%d" % (correct, total)
    put(scr, 0, max(1, W - wlen(stats) - 1), stats)
    diff = "difficulty %d/%d (%d kana)" % (
        difficulty,
        MAX_LEVEL,
        pool_size(difficulty),
    )
    put(scr, 0, 1, diff)


class Quiz:
    """State of the running drill: current card, score, and settings."""

    def __init__(self):
        self.script = 0
        self.show_table = True
        self.difficulty = MAX_LEVEL
        self.char, self.romaji, self.accepted = pick(0, self.difficulty)
        self.user_input = ""
        self.message = ""
        self.fails = 0
        self.correct = 0
        self.total = 0

    def reset_card(self, avoid=None):
        """Show a fresh card, clearing input, message, and miss count."""
        self.char, self.romaji, self.accepted = pick(
            self.script, self.difficulty, avoid
        )
        self.user_input = ""
        self.message = ""
        self.fails = 0

    def toggle_table(self):
        self.show_table = not self.show_table

    def switch_script(self):
        self.script = 1 - self.script
        self.reset_card()

    def set_difficulty(self, difficulty):
        if MIN_LEVEL <= difficulty <= MAX_LEVEL:
            self.difficulty = difficulty
            self.reset_card()
        elif difficulty < MIN_LEVEL:
            self.message = "Already at the easiest difficulty."
        else:
            self.message = "Already at the hardest difficulty."

    def submit(self):
        if not self.user_input.strip():
            self.message = "🐱"  # easter egg
            return
        self.total += 1
        if self.user_input.strip().lower() in self.accepted:
            self.correct += 1
            self.reset_card(avoid=self.char)
        else:
            self.fails += 1
            self.message = "Try again, it's " + (
                masked(self.romaji, self.accepted)
                if self.fails == 1
                else self.romaji
            )

    def backspace(self):
        self.user_input = self.user_input[:-1]

    def type_char(self, key):
        self.user_input = (self.user_input + chr(key))[:FIELD]


def handle_key(quiz, key):
    if key in TABLE_KEYS:
        quiz.toggle_table()
    elif key == SCRIPT_KEY:
        quiz.switch_script()
    elif key in ENTER_KEYS:
        quiz.submit()
    elif key in BACKSPACE_KEYS:
        quiz.backspace()
    elif key == DIFF_DOWN:
        quiz.set_difficulty(quiz.difficulty - 1)
    elif key in DIFF_UP:
        quiz.set_difficulty(quiz.difficulty + 1)
    elif cascii.isprint(key):
        quiz.type_char(key)


def draw_screen(scr, quiz):
    """Render one frame; returns False when the terminal is too small."""
    H, W = scr.getmaxyx()
    scr.erase()
    if W < MIN_W or H < MIN_H:
        put(scr, H // 2 - 1, 1, "Terminal too small.")
        put(
            scr,
            H // 2,
            1,
            "Need at least %dx%d. Now %dx%d." % (MIN_W, MIN_H, W, H),
        )
        put(scr, H // 2 + 1, 1, "Resize, or press ctrl+c to quit.")
        return False
    if quiz.show_table:
        if W >= TABLE_W and H >= TABLE_H + 8:
            draw_table(scr, 1, W, quiz.script, quiz.difficulty)
        else:
            put(
                scr,
                2,
                max(0, (W - 40) // 2),
                "Table doesn't fit. Enlarge the terminal.",
            )
    draw_core(
        scr,
        H,
        W,
        quiz.char,
        quiz.user_input,
        quiz.message,
        quiz.correct,
        quiz.total,
        quiz.difficulty,
    )
    return True


def main(scr):
    scr.keypad(True)
    curses.nonl()
    try:
        curses.curs_set(0)
    except curses.error:
        pass
    quiz = Quiz()
    while True:
        too_small = not draw_screen(scr, quiz)
        scr.refresh()
        key = scr.getch()
        if key in QUIT_KEYS:
            break
        if key == curses.KEY_RESIZE or too_small:
            continue
        handle_key(quiz, key)
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
