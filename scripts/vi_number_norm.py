"""Vietnamese number-word → digit normalization for STT metric variants.

Applied ON TOP of the baseline normalize_text() (lowercase, punctuation
removed, whitespace collapsed). It converts unambiguous spoken number
phrases to digit form so that e.g. GT "số 304" can match a prediction of
"số ba trăm lẻ bốn".

One direction only: words → digits. Digits are never expanded to words,
because Vietnamese digit strings have multiple valid readings
("205" = "hai trăm linh/lẻ năm" or "hai lẻ năm"), which would be ambiguous.

Supported patterns (all tokens must be consumed for a replacement):
  <U> trăm [lẻ|linh <U>]                 → N0U   ("hai trăm lẻ năm" = 205)
  <U> trăm mười [<U>]                    → N1U   ("một trăm mười hai" = 112)
  <U> trăm <U> mươi [<U>]                → NMU   ("ba trăm bốn mươi lăm" = 345)
  <U> nghìn|ngàn|triệu [<trăm-part>]     → N000… ("hai nghìn lẻ năm" = 2005)
  <U> mươi [<U>]                         → NU    ("hai mươi mốt" = 21)
  mười [<U>]                             → 1U    ("mười hai" = 12)
  lone unit word (except "không"/"năm")  → d     ("tầng hai" → "tầng 2")

Context-restricted digit shorthand (ONLY right after "số" or "phòng",
i.e. explicit room-number context, to avoid changing utterance meaning):
  "số <U> lẻ|linh <U>"   → "số N0U"  ("số ba lẻ bốn" = số 304)
  "số <U> không <U>"     → "số N0U"  ("số ba không bốn" = số 304)

Explicitly NOT normalized (documented limitations):
  - "không" as a standalone word (it is usually the negation "not", not zero)
  - "<U> trăm <U>" without mươi/lẻ (ambiguous: "hai trăm năm" = 205 or "year 200"?)
  - misheard markers like "lấy" in "ba lấy bốn" (a model error, not a number form)
  - multipliers without a leading unit (bare "trăm", "mươi" alone)
"""

from __future__ import annotations

UNITS = {
    "không": 0, "một": 1, "mốt": 1, "hai": 2, "ba": 3, "bốn": 4, "tư": 4,
    "năm": 5, "lăm": 5, "sáu": 6, "bảy": 7, "tám": 8, "chín": 9,
}
BIG = {"triệu": 1_000_000, "nghìn": 1_000, "ngàn": 1_000}
ZERO_MARKER = ("lẻ", "linh")
NUMBER_CONTEXT = ("số", "phòng")


def _parse_at(tok: list[str], i: int) -> tuple[int | None, int]:
    """Try to parse a full number phrase at tok[i]. Returns (value, end) or (None, i)."""
    n = len(tok)
    j = i
    val = 0

    # leading <U> <triệu|nghìn|ngàn> groups, e.g. "hai triệu ba trăm ..."
    while (j + 1 < n and tok[j] in UNITS and tok[j + 1] in BIG):
        val += UNITS[tok[j]] * BIG[tok[j + 1]]
        j += 2

    matched = j > i

    # <U> trăm …
    if j + 1 < n and tok[j] in UNITS and tok[j + 1] == "trăm":
        val += UNITS[tok[j]] * 100
        j += 2
        matched = True
        if j + 1 < n and tok[j] in ZERO_MARKER and tok[j + 1] in UNITS:
            val += UNITS[tok[j + 1]]          # "trăm lẻ U" -> +U (tens = 0)
            j += 2
        elif j < n and tok[j] == "mười":
            val += 10
            j += 1
            if j < n and tok[j] in UNITS:
                val += UNITS[tok[j]]
                j += 1
        elif j + 1 < n and tok[j] in UNITS and tok[j + 1] == "mươi":
            val += UNITS[tok[j]] * 10
            j += 2
            if j < n and tok[j] in UNITS:
                val += UNITS[tok[j]]
                j += 1
        # "<U> trăm <U>" without mươi/lẻ is intentionally left as words:
        # ambiguous ("hai trăm năm" = 205 or "năm 200-ish").

    # <U> mươi [<U>]
    elif j + 1 < n and tok[j] in UNITS and tok[j + 1] == "mươi":
        val += UNITS[tok[j]] * 10
        j += 2
        matched = True
        if j < n and tok[j] in UNITS:
            val += UNITS[tok[j]]
            j += 1

    # mười [<U>]
    elif j < n and tok[j] == "mười":
        val += 10
        j += 1
        matched = True
        if j < n and tok[j] in UNITS:
            val += UNITS[tok[j]]
            j += 1

    # tail "lẻ U" only after a hundreds/thousands group, e.g. "hai nghìn lẻ năm" = 2005
    if matched and val >= 100 and j + 1 < n and tok[j] in ZERO_MARKER and tok[j + 1] in UNITS:
        val += UNITS[tok[j + 1]]
        j += 2

    return (val, j) if matched else (None, i)


def normalize_numbers(text: str) -> str:
    """Replace unambiguous Vietnamese number phrases with digit strings."""
    tok = text.split()
    out: list[str] = []
    i = 0
    n = len(tok)
    while i < n:
        t = tok[i]
        # context shorthand: "số/phòng <U> lẻ|không <U>" -> N0U
        if (
            t in NUMBER_CONTEXT
            and i + 3 < n
            and tok[i + 1] in UNITS
            and tok[i + 3] in UNITS
            and tok[i + 2] in ZERO_MARKER + ("không",)
        ):
            out.append(t)
            out.append(str(UNITS[tok[i + 1]] * 100 + UNITS[tok[i + 3]]))
            i += 4
            continue
        val, j = _parse_at(tok, i)
        if val is not None and j > i:
            out.append(str(val))
            i = j
            continue
        # lone unit -> digit, except dual-use words that are usually
        # non-numeric standalone: "không" (negation) and "năm" (year)
        if t in UNITS and t not in ("không", "năm"):
            out.append(str(UNITS[t]))
        else:
            out.append(t)
        i += 1
    return " ".join(out)
