#!/usr/bin/env python3
"""news-image-20261123 (third account) — "The Wire", Monday 23 November 2026.
Compact tabular front page. Pure stdlib PNG renderer (no Pillow). 1024x1024.
36 stories, all verified and dated/reported 23 Nov 2026 (see NEWS23-BRISK.md).
Writes entry.png to MAKEFUN_OUTPUT_DIR when set, else local output/ dir.
"""
import hashlib
import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
PAPER = (252, 250, 244)
INK = (14, 14, 14)
INK_SOFT = (66, 64, 58)
GREY = (130, 126, 116)
LINE = (200, 192, 176)
NAVY = (12, 30, 54)
NAVY_LT = (30, 60, 98)
TEAL = (10, 94, 90)
RED = (174, 30, 24)
GOLD = (170, 126, 26)
CREAM = (242, 232, 208)
SKY = (208, 224, 234)
WHITE = (255, 255, 255)
BLACK = (8, 8, 8)

REGION_COLORS = {
    "EUROPE": (24, 64, 120),
    "MIDDLE EAST": (174, 30, 24),
    "ASIA": (10, 94, 90),
    "AFRICA": (170, 126, 26),
    "AMERICAS": (96, 48, 120),
    "OCEANIA": (32, 120, 96),
    "GLOBAL": (66, 64, 58),
}

# ---------------------------------------------------------------- 5x7 font
# Each glyph: 7 rows, 5 bits (bit 4 = leftmost pixel).
FONT = {
    "A": (0x0E, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    "B": (0x1E, 0x11, 0x11, 0x1E, 0x11, 0x11, 0x1E),
    "C": (0x0E, 0x11, 0x10, 0x10, 0x10, 0x11, 0x0E),
    "D": (0x1E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x1E),
    "E": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x1F),
    "F": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x10),
    "G": (0x0E, 0x11, 0x10, 0x17, 0x11, 0x11, 0x0F),
    "H": (0x11, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    "I": (0x0E, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "J": (0x07, 0x02, 0x02, 0x02, 0x02, 0x12, 0x0C),
    "K": (0x11, 0x12, 0x14, 0x18, 0x14, 0x12, 0x11),
    "L": (0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x1F),
    "M": (0x11, 0x1B, 0x15, 0x15, 0x11, 0x11, 0x11),
    "N": (0x11, 0x19, 0x15, 0x13, 0x11, 0x11, 0x11),
    "O": (0x0E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    "P": (0x1E, 0x11, 0x11, 0x1E, 0x10, 0x10, 0x10),
    "Q": (0x0E, 0x11, 0x11, 0x11, 0x15, 0x12, 0x0D),
    "R": (0x1E, 0x11, 0x11, 0x1E, 0x14, 0x12, 0x11),
    "S": (0x0F, 0x10, 0x10, 0x0E, 0x01, 0x01, 0x1E),
    "T": (0x1F, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04),
    "U": (0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    "V": (0x11, 0x11, 0x11, 0x11, 0x11, 0x0A, 0x04),
    "W": (0x11, 0x11, 0x11, 0x15, 0x15, 0x1B, 0x11),
    "X": (0x11, 0x11, 0x0A, 0x04, 0x0A, 0x11, 0x11),
    "Y": (0x11, 0x11, 0x0A, 0x04, 0x04, 0x04, 0x04),
    "Z": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x10, 0x1F),
    "a": (0x00, 0x00, 0x0E, 0x01, 0x0F, 0x11, 0x0F),
    "b": (0x10, 0x10, 0x1E, 0x11, 0x11, 0x11, 0x1E),
    "c": (0x00, 0x00, 0x0E, 0x10, 0x10, 0x10, 0x0E),
    "d": (0x01, 0x01, 0x0F, 0x11, 0x11, 0x11, 0x0F),
    "e": (0x00, 0x00, 0x0E, 0x11, 0x1F, 0x10, 0x0E),
    "f": (0x06, 0x08, 0x08, 0x1E, 0x08, 0x08, 0x08),
    "g": (0x00, 0x0F, 0x11, 0x11, 0x0F, 0x01, 0x0E),
    "h": (0x10, 0x10, 0x1E, 0x11, 0x11, 0x11, 0x11),
    "i": (0x04, 0x00, 0x0C, 0x04, 0x04, 0x04, 0x0E),
    "j": (0x02, 0x00, 0x06, 0x02, 0x02, 0x12, 0x0C),
    "k": (0x10, 0x10, 0x12, 0x14, 0x18, 0x14, 0x12),
    "l": (0x0C, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "m": (0x00, 0x00, 0x1A, 0x15, 0x15, 0x15, 0x15),
    "n": (0x00, 0x00, 0x1E, 0x11, 0x11, 0x11, 0x11),
    "o": (0x00, 0x00, 0x0E, 0x11, 0x11, 0x11, 0x0E),
    "p": (0x00, 0x00, 0x1E, 0x11, 0x11, 0x1E, 0x10),
    "q": (0x00, 0x00, 0x0F, 0x11, 0x11, 0x0F, 0x01),
    "r": (0x00, 0x00, 0x16, 0x19, 0x10, 0x10, 0x10),
    "s": (0x00, 0x00, 0x0F, 0x10, 0x0E, 0x01, 0x1E),
    "t": (0x08, 0x08, 0x1E, 0x08, 0x08, 0x09, 0x06),
    "u": (0x00, 0x00, 0x11, 0x11, 0x11, 0x13, 0x0D),
    "v": (0x00, 0x00, 0x11, 0x11, 0x11, 0x0A, 0x04),
    "w": (0x00, 0x00, 0x11, 0x11, 0x15, 0x15, 0x0A),
    "x": (0x00, 0x00, 0x11, 0x0A, 0x04, 0x0A, 0x11),
    "y": (0x00, 0x00, 0x11, 0x11, 0x0F, 0x01, 0x0E),
    "z": (0x00, 0x00, 0x1F, 0x02, 0x04, 0x08, 0x1F),
    "0": (0x0E, 0x11, 0x13, 0x15, 0x19, 0x11, 0x0E),
    "1": (0x04, 0x0C, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "2": (0x0E, 0x11, 0x01, 0x06, 0x08, 0x10, 0x1F),
    "3": (0x1F, 0x02, 0x04, 0x06, 0x01, 0x11, 0x0E),
    "4": (0x02, 0x06, 0x0A, 0x12, 0x1F, 0x02, 0x02),
    "5": (0x1F, 0x10, 0x1E, 0x01, 0x01, 0x11, 0x0E),
    "6": (0x06, 0x08, 0x10, 0x1E, 0x11, 0x11, 0x0E),
    "7": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08),
    "8": (0x0E, 0x11, 0x11, 0x0E, 0x11, 0x11, 0x0E),
    "9": (0x0E, 0x11, 0x11, 0x0F, 0x01, 0x02, 0x0C),
    " ": (0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00),
    ".": (0x00, 0x00, 0x00, 0x00, 0x00, 0x0C, 0x0C),
    ",": (0x00, 0x00, 0x00, 0x00, 0x0C, 0x04, 0x08),
    ":": (0x00, 0x0C, 0x0C, 0x00, 0x0C, 0x0C, 0x00),
    ";": (0x00, 0x0C, 0x0C, 0x00, 0x0C, 0x04, 0x08),
    "!": (0x04, 0x04, 0x04, 0x04, 0x04, 0x00, 0x04),
    "?": (0x0E, 0x11, 0x01, 0x02, 0x04, 0x00, 0x04),
    "'": (0x04, 0x04, 0x08, 0x00, 0x00, 0x00, 0x00),
    '"': (0x0A, 0x0A, 0x00, 0x00, 0x00, 0x00, 0x00),
    "-": (0x00, 0x00, 0x00, 0x1F, 0x00, 0x00, 0x00),
    "–": (0x00, 0x00, 0x00, 0x1F, 0x00, 0x00, 0x00),
    "—": (0x00, 0x00, 0x00, 0x1F, 0x00, 0x00, 0x00),
    "·": (0x00, 0x00, 0x00, 0x0C, 0x0C, 0x00, 0x00),
    "•": (0x00, 0x0E, 0x11, 0x11, 0x11, 0x0E, 0x00),
    "(": (0x02, 0x04, 0x08, 0x08, 0x08, 0x04, 0x02),
    ")": (0x08, 0x04, 0x02, 0x02, 0x02, 0x04, 0x08),
    "/": (0x01, 0x01, 0x02, 0x04, 0x08, 0x10, 0x10),
    "%": (0x19, 0x19, 0x02, 0x04, 0x08, 0x13, 0x13),
    "$": (0x04, 0x0F, 0x14, 0x0E, 0x05, 0x1E, 0x04),
    "’": (0x04, 0x04, 0x08, 0x00, 0x00, 0x00, 0x00),
    "‘": (0x08, 0x04, 0x04, 0x00, 0x00, 0x00, 0x00),
    "“": (0x0A, 0x0A, 0x00, 0x00, 0x00, 0x00, 0x00),
    "”": (0x0A, 0x0A, 0x00, 0x00, 0x00, 0x00, 0x00),
    "×": (0x00, 0x11, 0x0A, 0x04, 0x0A, 0x11, 0x00),
}

# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bytes(bg) * (w * h))

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = c

    def rect(self, x, y, w, h, c):
        for yy in range(max(0, y), min(self.h, y + h)):
            for xx in range(max(0, x), min(self.w, x + w)):
                self.set(xx, yy, c)

    def hline(self, x, y, w, c):
        self.rect(x, y, w, 1, c)

    def vline(self, x, y, h, c):
        self.rect(x, y, 1, h, c)

    def circle(self, cx, cy, r, c):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.set(xx, yy, c)

    def text(self, x, y, s, scale, c):
        cx = x
        for ch in s:
            g = FONT.get(ch, FONT[" "])
            for row in range(7):
                bits = g[row]
                for col in range(5):
                    if bits & (1 << (4 - col)):
                        self.rect(cx + col * scale, y + row * scale, scale, scale, c)
            cx += 6 * scale
        return cx

    def text_w(self, s, scale):
        return len(s) * 6 * scale - scale

    def wrap(self, s, scale, max_w):
        words = s.split()
        lines = []
        cur = ""
        for wd in words:
            trial = (cur + " " + wd).strip()
            if self.text_w(trial, scale) <= max_w:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = wd
        if cur:
            lines.append(cur)
        return lines

    def para(self, x, y, s, scale, max_w, c, lh):
        lines = self.wrap(s, scale, max_w)
        for i, ln in enumerate(lines):
            self.text(x, y + i * lh, ln, scale, c)
        return y + len(lines) * lh


def png_bytes(cv):
    raw = bytearray()
    for y in range(cv.h):
        raw.append(0)
        raw.extend(cv.px[y * cv.w * 3:(y + 1) * cv.w * 3])
    comp = zlib.compress(bytes(raw), 9)

    def chunk(typ, data):
        c = struct.pack(">I", len(data)) + typ + data
        c += struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
        return c

    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", comp)
        + chunk(b"IEND", b"")
    )

# ---------------------------------------------------------------- stories
# All verified, dated/reported Monday 23 November 2026. Source per story.
# (title, deck, source, region)
HERO = (
    "COP31 COLLAPSES",
    "UN climate talks in Antalya end with no deal after 44 hours of overtime — the longest COP ever. The final text never mentions fossil fuels; the EU and others refuse to endorse it. Guterres is deeply disappointed.",
    "REUTERS",
    "GLOBAL",
)
SECOND = [
    (
        "DRONE HITS KYIV FLATS; 14 MISSING",
        "A Russian drone hits a five-storey block in Dymer, north of Kyiv. 14 missing under rubble.",
        "REUTERS / AP",
        "EUROPE",
    ),
    (
        "TRUMP BACKS 10% CARD-RATE CAP",
        "President Trump says he will work with Democrats to cap credit-card interest at 10% for a year.",
        "FOX NEWS / AP",
        "AMERICAS",
    ),
]
# The wire table: (number, headline, source, region) — one line each.
WIRE = [
    (4, "FIFTY MISSING AFTER CANDY FACTORY FIRE", "REUTERS", "ASIA"),
    (5, "MEXICO CAPTURES FBI MOST-WANTED 'CHAPO ISIDRO'", "AP", "AMERICAS"),
    (6, "NATO MEETS ON MISSILES OVER POLAND", "REUTERS", "EUROPE"),
    (7, "NEPAL PM HOLDS TALKS WITH MODI", "PTI", "ASIA"),
    (8, "MINISTER QUITS OVER AI EXAM-CHEATING SCANDAL", "REUTERS", "ASIA"),
    (9, "LIVERPOOL ROUT UNITED 4-0 IN POCHETTINO DEBUT", "ESPN / BBC", "EUROPE"),
    (10, "VERSTAPPEN WINS CHAOTIC VEGAS GRAND PRIX", "ESPN / SKY", "AMERICAS"),
    (11, "INDIA POST RECORD 720/9 IN WELLINGTON TEST", "ESPNCRICINFO", "OCEANIA"),
    (12, "ATTACK LEAVES 24 CIVILIANS DEAD IN SOUTH SUDAN", "ARAB NEWS", "AFRICA"),
    (13, "ANT FUNDS LAUNCH AS NASDAQ ENDS WORST WEEK SINCE 2020", "CNBC", "AMERICAS"),
    (14, "LAVROV CALLS KYIV 'ANCESTRAL RUSSIAN LANDS'", "INDEPENDENT", "EUROPE"),
    (15, "RUSSIAN CORVETTE HIT AT BENGHAZI", "REUTERS", "AFRICA"),
    (16, "ODESA SCHOOLS GO REMOTE 23-27 NOV", "WASHINGTON POST", "EUROPE"),
    (17, "EU PROPOSES SMALLER BUDGET, 100BN EURO FOR UKRAINE", "EU", "EUROPE"),
    (18, "THOUSANDS MARCH IN LISBON OVER LIVING COSTS", "REUTERS", "EUROPE"),
    (19, "THOUSANDS PROTEST MEDIA CLOSURES IN ISTANBUL", "AP", "EUROPE"),
    (20, "UN TALKS ON LETHAL AI WEAPONS TO CONTINUE", "UN", "GLOBAL"),
    (21, "TWO TANKERS HIT IN STRAIT OF HORMUZ", "UKMTO", "MIDDLE EAST"),
    (22, "EISENKOT: SETTLER VIOLENCE IS 'JEWISH TERRORISM'", "AL JAZEERA", "MIDDLE EAST"),
    (23, "SAUDI COALITION INTERCEPTS HOUTHI MISSILE", "ARAB NEWS", "MIDDLE EAST"),
    (24, "PAKISTAN FM HOPEFUL ON US-IRAN DEAL", "ARAB NEWS", "MIDDLE EAST"),
    (25, "FIGHTING NEAR CONGO EBOLA AREA DISRUPTS RESPONSE", "WHO", "AFRICA"),
    (26, "PHILIPPINES LEADS ASIA-PACIFIC FARM TALKS", "DA / FAO", "ASIA"),
    (27, "SHIP FIRE AT CHINESE PORT KILLS 25", "AP", "ASIA"),
    (28, "AMIT SHAH LAUNCHES 4,000-CRORE INFRA PUSH", "PTI", "ASIA"),
    (29, "FBI PROBES BREACH OF ITS CRIME DATABASE", "AP", "AMERICAS"),
    (30, "DEMOCRATS CLINCH 258-SEAT HOUSE MAJORITY", "AP", "AMERICAS"),
    (31, "WASHINGTON GOVERNOR: ICE 'OUT OF CONTROL'", "AP", "AMERICAS"),
    (32, "THREE KILLED AT OHIO BABY SHOWER", "AP", "AMERICAS"),
    (33, "'SUNRISE ON THE REAPING' OPENS AT $120M", "EXHIBITOR RELATIONS", "GLOBAL"),
    (34, "MILEY CYRUS MARRIES MAXX MORANDO", "AP", "GLOBAL"),
    (35, "FRANCE ROUT ARGENTINA 45-17", "AFP", "EUROPE"),
    (36, "BOWEN: COP31 OUTCOME 'VERY DISAPPOINTING'", "REUTERS", "OCEANIA"),
]
STATS = [
    ("258", "DEM SEATS"),
    ("0", "COP31 DEAL"),
    ("50", "MISSING · JAVA"),
    ("10%", "CARD CAP"),
    ("2,700", "DRONES / WEEK"),
    ("720/9", "INDIA TEST"),
]

# ---------------------------------------------------------------- layout
def render():
    cv = Canvas(W, H, PAPER)
    M = 28  # margin
    # --- masthead band (navy) ---
    cv.rect(0, 0, W, 96, NAVY)
    cv.text(M, 14, "THE WIRE", 6, WHITE)
    cv.text(M, 56, "MONDAY 23 NOVEMBER 2026 · 36 STORIES · 7 REGIONS", 2, (200, 210, 224))
    # right: big date numerals
    cv.text(W - M - cv.text_w("23 NOV", 3), 24, "23 NOV", 3, GOLD)
    cv.rect(0, 96, W, 4, RED)

    # --- hero feature (COP31) with overtime bar ---
    hy = 112
    cv.text(M, hy, "THE LEAD — ANTALYA, TURKIYE", 2, RED)
    cv.hline(M, hy + 20, W - 2 * M, LINE)
    # overtime bar (right side of hero)
    bx = W - M - 240
    by = hy + 34
    cv.rect(bx, by, 240, 16, NAVY)  # full bar: 44 hrs overtime
    cv.text(bx, by + 24, "44 HRS OVERTIME", 2, NAVY)
    cv.text(bx, by + 46, "LONGEST COP EVER", 2, NAVY)
    cv.text(bx, by + 68, "~200 NATIONS · NO DEAL", 2, GREY)
    # hero text (left of bar)
    tx = M
    tw = bx - M - 24
    y = hy + 30
    y = cv.para(tx, y, HERO[0], 5, tw, INK, 42)
    y += 4
    y = cv.para(tx, y, HERO[1], 2, tw, INK_SOFT, 20)
    y += 8
    cv.rect(tx, y, 120, 22, RED)
    cv.text(tx + 10, y + 4, "GLOBAL · CLIMATE", 2, WHITE)
    cv.text(tx + 132, y + 4, "SOURCE: " + HERO[2], 2, GREY)

    # --- second row: two features side by side ---
    sy = 312
    col_w = (W - 2 * M - 20) // 2
    for i, (t, d, src, reg) in enumerate(SECOND):
        x = M + i * (col_w + 20)
        cv.rect(x, sy, col_w, 3, REGION_COLORS[reg])
        y = sy + 10
        y = cv.para(x, y, t, 3, col_w, INK, 26)
        y += 2
        y = cv.para(x, y, d, 2, col_w, INK_SOFT, 18)
        y += 4
        cv.text(x, y, reg + "  ·  SOURCE: " + src, 2, GREY)
    dy = sy + 150
    cv.hline(M, dy, W - 2 * M, LINE)

    # --- numbers strip ---
    ny = dy + 12
    seg_w = (W - 2 * M) // len(STATS)
    for i, (num, lab) in enumerate(STATS):
        x = M + i * seg_w
        cv.text(x, ny, num, 3, NAVY)
        cv.text(x, ny + 26, lab, 1, GREY)
        if i:
            cv.vline(x - 8, ny + 2, 34, LINE)
    ty = ny + 48
    cv.hline(M, ty, W - 2 * M, LINE)

    # --- the wire table: two columns, one line per story ---
    wy = ty + 12
    cv.text(M, wy, "THE WIRE — EVERYTHING ELSE TODAY", 2, RED)
    wy += 22
    row_h = 20
    per_col = 17
    for i, (n, t, src, reg) in enumerate(WIRE):
        col = i // per_col
        row = i % per_col
        x = M + col * (col_w + 20)
        y = wy + row * row_h
        if row % 2 == 0:
            cv.rect(x, y - 2, col_w, row_h, (246, 242, 232))
        cv.rect(x + 2, y + 2, 6, 6, REGION_COLORS[reg])
        cv.text(x + 14, y, str(n) + ".", 1, REGION_COLORS[reg])
        cv.text(x + 44, y, t, 1, INK)
        sw = cv.text_w(src, 1)
        cv.text(x + col_w - sw, y, src, 1, GREY)

    # --- region counts strip ---
    ry = wy + per_col * row_h + 14
    cv.hline(M, ry, W - 2 * M, LINE)
    ry += 10
    cv.text(M, ry, "BY REGION", 2, RED)
    ry += 20
    regions = [("EUROPE", 9), ("ASIA", 6), ("MIDDLE EAST", 4), ("AFRICA", 3), ("AMERICAS", 8), ("OCEANIA", 2), ("GLOBAL", 4)]
    seg2 = (W - 2 * M) // len(regions)
    for i, (reg, cnt) in enumerate(regions):
        x = M + i * seg2
        cv.rect(x, ry, 8, 8, REGION_COLORS[reg])
        cv.text(x + 14, ry, reg + " " + str(cnt), 2, INK)

    # --- footer ---
    fy = ry + 34
    cv.hline(M, fy, W - 2 * M, LINE)
    fy += 8
    cv.text(M, fy, "All stories verified against Reuters, AP, BBC, ESPN, Sky, Fox News, PTI, AFP, UKMTO, UN, WHO, Arab News and Al Jazeera — dated Monday 23 November 2026.", 1, GREY)
    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    os.makedirs(out_dir, exist_ok=True)
    cv = render()
    data = png_bytes(cv)
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as f:
        f.write(data)
    print("wrote", path, len(data), "bytes", "sha256", hashlib.sha256(data).hexdigest())


if __name__ == "__main__":
    main()
