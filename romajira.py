#!/usr/bin/env python3

import argparse
import curses
import locale
import os
import random
import unicodedata
from curses import ascii as cascii

# Magic values

LBLW = 3  # width of the consonant-label column in the reference table
CELLW = 8  # width of one kana cell in the reference table
FIELD = 16  # max length of the typed romaji input
HELP = "tab:script | difficulty:-/+ | ctrl+f/j:table | enter | esc"
MIN_W = len(HELP) + 1  # minimum terminal width: must fit the help line
MIN_H = 11  # minimum terminal height for the card UI
MIN_LEVEL = 0  # lowest selectable level; 0 selects the adaptive ladder
MAX_LEVEL = 7  # highest difficulty: all base kana plus contracted sounds
START_LEVEL = 0  # difficulty at launch; 0 = adaptive ladder
LADDER_START = 3  # number of kana the adaptive ladder starts with
LADDER_ADD = 7  # first-try streak that adds the next kana
LADDER_DROP = 5  # miss streak that removes a kana
LADDER_MIN = 3  # smallest size the adaptive ladder may shrink to
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

DIGRAPH_ROWS = [
    (
        "k",
        [("きゃ", "kya"), ("きゅ", "kyu"), ("きょ", "kyo")],
    ),
    (
        "s",
        [("しゃ", "sha"), ("しゅ", "shu"), ("しょ", "sho")],
    ),
    (
        "t",
        [("ちゃ", "cha"), ("ちゅ", "chu"), ("ちょ", "cho")],
    ),
    (
        "n",
        [("にゃ", "nya"), ("にゅ", "nyu"), ("にょ", "nyo")],
    ),
    (
        "h",
        [("ひゃ", "hya"), ("ひゅ", "hyu"), ("ひょ", "hyo")],
    ),
    (
        "m",
        [("みゃ", "mya"), ("みゅ", "myu"), ("みょ", "myo")],
    ),
    (
        "r",
        [("りゃ", "rya"), ("りゅ", "ryu"), ("りょ", "ryo")],
    ),
    (
        "g",
        [("ぎゃ", "gya"), ("ぎゅ", "gyu"), ("ぎょ", "gyo")],
    ),
    (
        "j",
        [("じゃ", "ja"), ("じゅ", "ju"), ("じょ", "jo")],
    ),
    (
        "b",
        [("びゃ", "bya"), ("びゅ", "byu"), ("びょ", "byo")],
    ),
    (
        "p",
        [("ぴゃ", "pya"), ("ぴゅ", "pyu"), ("ぴょ", "pyo")],
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
    "しゃ": {"sha", "sya"},
    "しゅ": {"shu", "syu"},
    "しょ": {"sho", "syo"},
    "ちゃ": {"cha", "tya"},
    "ちゅ": {"chu", "tyu"},
    "ちょ": {"cho", "tyo"},
    "じゃ": {"ja", "jya", "zya"},
    "じゅ": {"ju", "jyu", "zyu"},
    "じょ": {"jo", "jyo", "zyo"},
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
    "を": 2,
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
    "げ": 6,
    "ぢ": 6,
    "づ": 6,
    "べ": 6,
    "ぼ": 6,
    # 7  Contracted sounds
    "きゃ": 7,
    "きゅ": 7,
    "きょ": 7,
    "しゃ": 7,
    "しゅ": 7,
    "しょ": 7,
    "ちゃ": 7,
    "ちゅ": 7,
    "ちょ": 7,
    "にゃ": 7,
    "にゅ": 7,
    "にょ": 7,
    "ひゃ": 7,
    "ひゅ": 7,
    "ひょ": 7,
    "みゃ": 7,
    "みゅ": 7,
    "みょ": 7,
    "りゃ": 7,
    "りゅ": 7,
    "りょ": 7,
    "ぎゃ": 7,
    "ぎゅ": 7,
    "ぎょ": 7,
    "じゃ": 7,
    "じゅ": 7,
    "じょ": 7,
    "びゃ": 7,
    "びゅ": 7,
    "びょ": 7,
    "ぴゃ": 7,
    "ぴゅ": 7,
    "ぴょ": 7,
}

all_kana = {
    cell[0]
    for rows in (KANA_ROWS, DIGRAPH_ROWS)
    for _, cells in rows
    for cell in cells
    if cell
}
assert (
    set(LEVEL) == all_kana
), "every kana in KANA_ROWS must have a LEVEL entry"

TABLE_ORDER = [
    cell[0] for _, cells in KANA_ROWS + DIGRAPH_ROWS for cell in cells if cell
]
LADDER_ORDER = sorted(TABLE_ORDER, key=lambda key: LEVEL[key])

TABLE_W = LBLW + 5 * CELLW


def visible_kana(difficulty, active=None):
    if active is None:
        return lambda key: LEVEL[key] <= difficulty
    active = set(active)
    return lambda key: key in active


def digraph_rows(visible):
    return [
        (label, cells)
        for label, cells in DIGRAPH_ROWS
        if any(cell and visible(cell[0]) for cell in cells)
    ]


def table_height(difficulty, active=None):
    height = len(KANA_ROWS) + 2
    rows = digraph_rows(visible_kana(difficulty, active))
    if rows:
        height += len(rows) + 3
    return height


def to_kata(hiragana):
    return "".join(chr(ord(c) + 0x60) for c in hiragana)


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
    for _, cells in KANA_ROWS + DIGRAPH_ROWS:
        for cell in cells:
            if cell is None:
                continue
            hiragana, romaji = cell
            accepted = {romaji} | ALT.get(hiragana, set())
            out.append(
                (
                    kana(hiragana, script),
                    romaji,
                    accepted,
                    LEVEL[hiragana],
                    hiragana,
                )
            )
    return out


POOLS = [pool(0), pool(1)]


def pool_size(difficulty):
    return sum(1 for entry in POOLS[0] if entry[3] <= difficulty)


def pick(script, difficulty, avoid=None, active=None):
    visible = visible_kana(difficulty, active)
    candidates = [entry for entry in POOLS[script] if visible(entry[4])]
    if not candidates:
        raise ValueError("no glyphs at difficulty %d" % difficulty)
    if len(candidates) == 1:
        char, romaji, accepted, _, hiragana = candidates[0]
        return char, romaji, accepted, hiragana
    while True:
        char, romaji, accepted, _, hiragana = random.choice(candidates)
        if char != avoid:
            return char, romaji, accepted, hiragana


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


def draw_section(scr, top, W, script, rows, vowels, title, visible):
    left = max(0, (W - TABLE_W) // 2)
    put(scr, top, left + max(0, (TABLE_W - wlen(title)) // 2), title)
    header = pad("", LBLW) + "".join(pad(vowel, CELLW) for vowel in vowels)
    put(scr, top + 1, left, header)
    for row, (label, cells) in enumerate(rows):
        y = top + 2 + row
        x = left
        put(scr, y, x, pad(label, LBLW))
        x += LBLW
        for cell in cells:
            if cell is not None:
                hiragana, romaji = cell
                if visible(hiragana):
                    glyph = kana(hiragana, script)
                    put(scr, y, x, glyph + " " + romaji)
                    put(scr, y, x + wlen(glyph) + 1, romaji, curses.A_BOLD)
            x += CELLW


def draw_table(scr, top, W, script, difficulty, active=None):
    visible = visible_kana(difficulty, active)
    title = "Hiragana to romaji" if script == 0 else "Katakana to romaji"
    draw_section(scr, top, W, script, KANA_ROWS, "aiueo", title, visible)
    rows = digraph_rows(visible)
    if rows:
        top += len(KANA_ROWS) + 3
        draw_section(
            scr, top, W, script, rows, "auo", "Contracted sounds", visible
        )


def draw_core(
    scr,
    H,
    W,
    char,
    user_input,
    message,
    correct,
    total,
    difficulty,
    active=None,
    streak=0,
):
    char_row = H - 6
    input_row = H - 4
    msg_row = H - 2
    lead = "What is this character:  ["
    line = lead + char + "]"
    x = max(0, (W - wlen(line)) // 2)
    put(scr, char_row, x, line)
    field = "[" + user_input.ljust(FIELD) + "]"
    fx = max(0, (W - wlen(field)) // 2)
    put(scr, input_row, fx, field)
    if message:
        mx = max(0, (W - wlen(message)) // 2)
        put(scr, msg_row, mx, message)
    put(scr, H - 1, 1, HELP)
    stats = "%d/%d" % (correct, total)
    put(scr, 0, max(1, W - wlen(stats) - 1), stats)
    if active is None:
        diff = "difficulty %d/%d (%d kana)" % (
            difficulty,
            MAX_LEVEL,
            pool_size(difficulty),
        )
    else:
        diff = "adaptive: %d kana (streak %+d)" % (len(active), streak)
    put(scr, 0, 1, diff)


class Quiz:
    """State of the running drill: current card, score, and settings."""

    def __init__(self):
        self.script = 0
        self.show_table = True
        self.difficulty = START_LEVEL
        self.active = LADDER_ORDER[:LADDER_START] if START_LEVEL == 0 else None
        self.streak = 0
        self.failed_key = None
        self.user_input = ""
        self.message = ""
        self.fails = 0
        self.correct = 0
        self.total = 0
        self.reset_card()

    def adaptive(self):
        return self.active is not None

    def reset_card(self, avoid=None):
        """Show a fresh card, clearing input, message, and miss count."""
        self.char, self.romaji, self.accepted, self.key = pick(
            self.script, self.difficulty, avoid, self.active
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
        if difficulty == 0 and not self.adaptive():
            self.difficulty = 0
            self.active = LADDER_ORDER[:LADDER_START]
            self.streak = 0
            self.failed_key = None
            self.reset_card()
        elif difficulty < MIN_LEVEL:
            self.message = "Already at the easiest difficulty."
        elif difficulty > MAX_LEVEL:
            self.message = "Already at the hardest difficulty."
        else:
            self.difficulty = difficulty
            self.active = None
            self.streak = 0
            self.reset_card()

    def ladder_step(self, first_try):
        """Fold one answered card into the ladder; announce add or removal."""
        if first_try:
            self.streak += 1
            if self.streak < LADDER_ADD:
                return None
            self.streak = 0
            if len(self.active) == len(LADDER_ORDER):
                return None
            added = next(k for k in LADDER_ORDER if k not in self.active)
            self.active.append(added)
            return "+ %s added" % kana(added, self.script)
        self.failed_key = self.key
        self.streak = min(self.streak, 0) - 1
        if self.streak > -LADDER_DROP or len(self.active) <= LADDER_MIN:
            return None
        self.streak = 0
        drop = (
            self.failed_key
            if self.failed_key in self.active
            else self.active[-1]
        )
        self.active.remove(drop)
        self.reset_card()
        return "- %s removed" % kana(drop, self.script)

    def submit(self):
        if not self.user_input.strip():
            self.message = "🐱"  # easter egg
            return
        first_try = self.fails == 0
        self.total += 1
        if self.user_input.strip().lower() in self.accepted:
            self.correct += 1
            announce = self.ladder_step(first_try) if self.adaptive() else None
            self.reset_card(avoid=self.char)
            self.message = announce or ""
        else:
            self.fails += 1
            self.message = "Try again, it's " + (
                masked(self.romaji, self.accepted)
                if self.fails == 1
                else self.romaji
            )
            if self.adaptive():
                announce = self.ladder_step(False)
                if announce:
                    self.message = announce

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
        height = table_height(quiz.difficulty, quiz.active)
        if W >= TABLE_W and H >= height + 8:
            draw_table(scr, 1, W, quiz.script, quiz.difficulty, quiz.active)
        else:
            note = "Table doesn't fit. Enlarge the terminal to %dx%d." % (
                TABLE_W,
                height + 8,
            )
            put(scr, 2, max(0, (W - wlen(note)) // 2), note)
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
        quiz.active,
        quiz.streak,
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
    parser = argparse.ArgumentParser(
        description="Terminal flashcard trainer for kana romaji readings."
    )
    parser.add_argument(
        "--force-utf",
        action="store_true",
        help="bypass the UTF-8 terminal locale check",
    )
    args = parser.parse_args()
    locale.setlocale(locale.LC_ALL, "")
    if (
        "utf" not in locale.getpreferredencoding(False).lower()
        and not args.force_utf
    ):
        print(
            "romajira needs a UTF-8 terminal. You can force it with --force-utf"
        )
        raise SystemExit(1)
    os.environ["ESCDELAY"] = "25"
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
