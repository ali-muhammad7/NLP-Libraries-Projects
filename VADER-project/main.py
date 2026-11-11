"""
VADER Signal Desk
A Tkinter GUI for sentiment analysis using NLTK's VADER
(Valence Aware Dictionary and sEntiment Reasoner).
Styled as a retro audio mixing console with analog VU-meter gauges.
"""

import math
import tkinter as tk
from tkinter import messagebox

import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk.tokenize import sent_tokenize


# ==========================================================
# LOAD VADER
# VADER needs its own lexicon file downloaded separately from
# the other NLTK data we used before.
# ==========================================================
analyzer = None
try:
    analyzer = SentimentIntensityAnalyzer()
except LookupError:
    analyzer = None


def lexicon_missing_warning():
    messagebox.showerror(
        "VADER Lexicon Not Found",
        "The VADER sentiment lexicon is not downloaded on this computer.\n\n"
        "Please run this in Python once:\n\n"
        "import nltk\n"
        "nltk.download('vader_lexicon')\n"
        "nltk.download('punkt')\n"
        "nltk.download('punkt_tab')\n\n"
        "Then restart this program."
    )


# ==========================================================
# COLORS - retro mixing-console theme
# ==========================================================
BG = "#171310"
PANEL = "#211b16"
PANEL_LIGHT = "#2e2721"
METAL = "#46392e"
CREAM = "#ece3d3"
MUTED = "#9c8f7c"
AMBER = "#e8a33d"
RED = "#e0503f"
GREEN = "#7fae6a"
NEU_COLOR = "#c9bfae"
READOUT_BG = "#0e0c0a"


# ==========================================================
# GAUGE DRAWING HELPERS (plain Tkinter Canvas, no SVG)
# ==========================================================
def make_gauge(parent, needle_color):
    """
    Creates one semi-circle gauge on a Canvas: a background arc,
    a needle line, and a small pivot dot. Returns the canvas plus
    the needle's item id so it can be redrawn later.
    """
    canvas = tk.Canvas(parent, width=170, height=95, bg=PANEL, highlightthickness=0)
    canvas.pack()

    cx, cy, radius = 85, 80, 68

    # background arc track
    canvas.create_arc(
        cx - radius, cy - radius, cx + radius, cy + radius,
        start=0, extent=180, style="arc", outline="#3a2f26", width=9
    )

    # pivot dot
    canvas.create_oval(cx - 5, cy - 5, cx + 5, cy + 5, fill=needle_color, outline="")

    # needle (initially pointing straight up)
    needle_id = canvas.create_line(cx, cy, cx, cy - 60, fill=needle_color, width=3)

    return {"canvas": canvas, "needle": needle_id, "cx": cx, "cy": cy, "length": 60}


def set_gauge_needle(gauge, angle_deg):
    """
    Rotates a gauge's needle. angle_deg = 0 means pointing straight up,
    negative = tilted left, positive = tilted right (like a clock hand).
    """
    angle_rad = math.radians(angle_deg)
    cx, cy, length = gauge["cx"], gauge["cy"], gauge["length"]
    tip_x = cx + length * math.sin(angle_rad)
    tip_y = cy - length * math.cos(angle_rad)
    gauge["canvas"].coords(gauge["needle"], cx, cy, tip_x, tip_y)


def make_led(parent, size=10):
    """Creates a small circular LED indicator (off by default)."""
    canvas = tk.Canvas(parent, width=size + 4, height=size + 4, bg=PANEL, highlightthickness=0)
    canvas.pack(pady=(6, 0))
    led_id = canvas.create_oval(2, 2, size + 2, size + 2, fill="#3a2f26", outline="")
    return {"canvas": canvas, "id": led_id}


def set_led(led, color, on):
    led["canvas"].itemconfig(led["id"], fill=(color if on else "#3a2f26"))


# ==========================================================
# CORE ANALYSIS FUNCTION
# ==========================================================
def run_level_check():
    if analyzer is None:
        lexicon_missing_warning()
        return

    text = input_box.get("1.0", tk.END).strip()
    if not text:
        messagebox.showwarning("No Signal", "Please type or paste some text first.")
        return

    # ---- Overall scores from VADER ----
    scores = analyzer.polarity_scores(text)
    pos, neg, neu, compound = scores["pos"], scores["neg"], scores["neu"], scores["compound"]

    # Needles: pos/neg/neu sweep 0..1 across -80..+80 degrees.
    # Compound sweeps -1..+1 across the same range.
    set_gauge_needle(gauge_pos, -80 + min(pos, 1) * 160)
    set_gauge_needle(gauge_neg, -80 + min(neg, 1) * 160)
    set_gauge_needle(gauge_neu, -80 + min(neu, 1) * 160)
    set_gauge_needle(gauge_comp, compound * 80)

    readout_pos.config(text=f"{pos:.3f}")
    readout_neg.config(text=f"{neg:.3f}")
    readout_neu.config(text=f"{neu:.3f}")
    readout_comp.config(text=f"{compound:.4f}")

    set_led(led_pos, AMBER, pos > 0.15)
    set_led(led_neg, AMBER, neg > 0.15)
    set_led(led_neu, AMBER, neu > 0.6)
    set_led(led_comp, RED, abs(compound) > 0.4)

    # ---- Sentence-by-sentence peak meter ----
    for widget in ladder_frame.winfo_children():
        widget.destroy()

    try:
        sentences = sent_tokenize(text)
    except LookupError:
        sentences = [text]

    if not sentences:
        tk.Label(ladder_frame, text="No sentences detected.", bg=PANEL, fg=MUTED,
                  font=("Arial", 9, "italic")).pack(side="left")

    for i, sentence in enumerate(sentences, start=1):
        s_scores = analyzer.polarity_scores(sentence)
        s_compound = s_scores["compound"]

        if s_compound > 0.15:
            color = GREEN
        elif s_compound < -0.15:
            color = RED
        else:
            color = AMBER

        unit = tk.Frame(ladder_frame, bg=PANEL)
        unit.pack(side="left", padx=6)

        bulb = tk.Canvas(unit, width=18, height=18, bg=PANEL, highlightthickness=0)
        bulb.pack()
        bulb.create_oval(2, 2, 16, 16, fill=color, outline="")

        tk.Label(unit, text=f"S{i}", bg=PANEL, fg=MUTED, font=("Consolas", 8)).pack()


def clear_all():
    input_box.delete("1.0", tk.END)
    for gauge in (gauge_pos, gauge_neg, gauge_neu):
        set_gauge_needle(gauge, -80)
    set_gauge_needle(gauge_comp, 0)
    readout_pos.config(text="0.000")
    readout_neg.config(text="0.000")
    readout_neu.config(text="0.000")
    readout_comp.config(text="0.0000")
    for led in (led_pos, led_neg, led_neu, led_comp):
        set_led(led, AMBER, False)
    for widget in ladder_frame.winfo_children():
        widget.destroy()
    tk.Label(ladder_frame, text="Run a Level Check to populate the meter.",
              bg=PANEL, fg=MUTED, font=("Arial", 9, "italic")).pack(side="left")


def exit_app():
    root.destroy()


# ==========================================================
# GUI SETUP
# ==========================================================
root = tk.Tk()
root.title("VADER Signal Desk")
root.geometry("980x680")
root.configure(bg=BG)

desk = tk.Frame(root, bg=PANEL_LIGHT, padx=26, pady=22)
desk.pack(fill="both", expand=True, padx=18, pady=18)

# ---------- Header ----------
header = tk.Frame(desk, bg=PANEL_LIGHT)
header.pack(fill="x")

title_row = tk.Frame(header, bg=PANEL_LIGHT)
title_row.pack(side="left", anchor="w")

tk.Label(
    title_row, text="VADER Signal Desk", font=("Georgia", 22, "bold"),
    bg=PANEL_LIGHT, fg=CREAM
).pack(side="left")

tk.Label(
    header, text="MODEL NLTK-VS4  |  NLP LAB . UNIT 06", font=("Consolas", 9),
    bg=PANEL_LIGHT, fg=MUTED
).pack(side="right", anchor="e")

tk.Label(
    desk, text="VALENCE-AWARE SENTIMENT CONSOLE", font=("Arial", 9),
    bg=PANEL_LIGHT, fg=MUTED
).pack(anchor="w", pady=(0, 14))

tk.Frame(desk, bg=METAL, height=2).pack(fill="x", pady=(0, 18))

# ---------- Input strip ----------
input_strip = tk.Frame(desk, bg=PANEL_LIGHT)
input_strip.pack(fill="x", pady=(0, 20))

input_col = tk.Frame(input_strip, bg=PANEL_LIGHT)
input_col.pack(side="left", fill="x", expand=True)

tk.Label(
    input_col, text="MIC INPUT - PASTE TEXT", font=("Arial", 9, "bold"),
    bg=PANEL_LIGHT, fg=AMBER
).pack(anchor="w")

input_box = tk.Text(
    input_col, height=4, font=("Consolas", 11), bg=READOUT_BG, fg="#cfead1",
    insertbackground=AMBER, relief="flat", padx=10, pady=8
)
input_box.pack(fill="x", pady=(4, 0))
input_box.insert(tk.END, "I really love this course but the assignment was confusing.")

tk.Button(
    input_strip, text="Level Check", command=run_level_check,
    bg="#d68f33", fg="#241505", font=("Arial", 10, "bold"),
    relief="flat", padx=16, pady=18, cursor="hand2"
).pack(side="right", padx=(14, 0), anchor="s")

# ---------- Channel strips ----------
channels = tk.Frame(desk, bg=PANEL_LIGHT)
channels.pack(fill="x", pady=(0, 20))

def make_channel(parent, label_text, needle_color, is_compound=False):
    ch = tk.Frame(parent, bg=PANEL, padx=10, pady=12,
                  highlightbackground="#0b0908", highlightthickness=1)
    ch.pack(side="left", fill="both", expand=True, padx=6)

    tk.Label(ch, text=label_text, font=("Arial", 9, "bold"),
              bg=PANEL, fg=(AMBER if is_compound else MUTED)).pack()

    gauge = make_gauge(ch, needle_color)

    readout = tk.Label(ch, text="0.000" if not is_compound else "0.0000",
                         font=("Consolas", 14), bg=READOUT_BG, fg=CREAM, width=8)
    readout.pack(pady=(4, 0))

    led = make_led(ch)

    return gauge, readout, led


gauge_pos, readout_pos, led_pos = make_channel(channels, "POSITIVE", AMBER)
gauge_neg, readout_neg, led_neg = make_channel(channels, "NEGATIVE", RED)
gauge_neu, readout_neu, led_neu = make_channel(channels, "NEUTRAL", NEU_COLOR)
gauge_comp, readout_comp, led_comp = make_channel(channels, "COMPOUND", "#f2b64c", is_compound=True)

# ---------- Sentence ladder ----------
ladder_section = tk.Frame(desk, bg=PANEL, padx=14, pady=12,
                            highlightbackground="#0b0908", highlightthickness=1)
ladder_section.pack(fill="x", pady=(0, 16))

tk.Label(
    ladder_section, text="SENTENCE-BY-SENTENCE PEAK METER", font=("Arial", 9, "bold"),
    bg=PANEL, fg=MUTED
).pack(anchor="w", pady=(0, 8))

ladder_frame = tk.Frame(ladder_section, bg=PANEL)
ladder_frame.pack(anchor="w", fill="x")

tk.Label(ladder_frame, text="Run a Level Check to populate the meter.",
          bg=PANEL, fg=MUTED, font=("Arial", 9, "italic")).pack(side="left")

# ---------- Bottom buttons ----------
bottom_row = tk.Frame(desk, bg=PANEL_LIGHT)
bottom_row.pack(fill="x")

tk.Button(
    bottom_row, text="Clear", command=clear_all,
    bg=METAL, fg=CREAM, font=("Arial", 9, "bold"),
    relief="flat", padx=18, pady=8, cursor="hand2"
).pack(side="left")

tk.Button(
    bottom_row, text="Exit", command=exit_app,
    bg="#7a2c22", fg="white", font=("Arial", 9, "bold"),
    relief="flat", padx=18, pady=8, cursor="hand2"
).pack(side="left", padx=(10, 0))

# ---------- Run once with the default example text ----------
root.after(300, run_level_check)

root.mainloop()