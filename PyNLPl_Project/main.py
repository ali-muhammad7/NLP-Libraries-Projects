"""
PyNLPl Fruit Stand
A Tkinter GUI for basic text-processing tools using PyNLPl.
"PyNLPl" is pronounced like "pineapple" - hence the fruit stand theme!

DEBUG VERSION: this has extra print() statements so we can see in the
terminal exactly what's happening when a crate is clicked.
"""

import tkinter as tk
from tkinter import messagebox
import traceback

print("STEP 1: Script started")

try:
    from pynlpl.textprocessors import Windower
    from pynlpl.statistics import FrequencyList, levenshtein
    print("STEP 2: pynlpl imported successfully")
except ImportError as e:
    Windower = None
    FrequencyList = None
    levenshtein = None
    print("STEP 2: pynlpl import FAILED:", e)


def pynlpl_missing_warning():
    messagebox.showerror(
        "PyNLPl Not Installed",
        "The pynlpl library is not installed on this computer.\n\n"
        "Please open your terminal and run:\n\n"
        "pip install pynlpl\n\n"
        "Then restart this program."
    )


# ==========================================================
# COLORS - tropical fruit stand theme
# ==========================================================
SKY = "#fff6de"
WOOD = "#a9713f"
WOOD_DARK = "#7d5230"
CRATE = "#e8b563"
LEAF_DARK = "#2c6b3a"
TOMATO = "#e0553f"
INK = "#3a2b1a"
PAPER = "#fffaf0"


# ==========================================================
# HELPERS
# ==========================================================
def get_words():
    text = input_box.get("1.0", tk.END).strip().lower()
    cleaned = "".join(ch if ch.isalpha() or ch.isspace() else " " for ch in text)
    return cleaned.split()


def force_redraw():
    """
    Workaround for a rare Windows Tk repaint bug: nudging the window
    size by 1 pixel and back forces Windows to fully redraw it.
    """
    w = root.winfo_width()
    h = root.winfo_height()
    root.geometry(f"{w+1}x{h}")
    root.update()
    root.geometry(f"{w}x{h}")
    root.update()


def set_basket(title, lines):
    print("STEP: set_basket called with title:", title)
    basket_output.delete("1.0", tk.END)
    basket_output.insert(tk.END, f"{title}\n\n")
    basket_output.insert(tk.END, "\n".join(lines))
    basket_output.update_idletasks()
    root.update_idletasks()
    force_redraw()
    print("STEP: set_basket finished writing to the basket box")


def check_ready():
    if Windower is None:
        pynlpl_missing_warning()
        return False
    words = get_words()
    if not words:
        messagebox.showwarning("Empty Basket", "Please enter some text first.")
        return False
    return True


# ==========================================================
# PYNLPL-POWERED OPERATIONS
# ==========================================================
def do_ngrams():
    print(">>> N-Gram crate CLICKED")
    try:
        if not check_ready():
            return
        words = get_words()
        bigrams = list(Windower(words, n=2, beginmarker=None, endmarker=None))
        lines = [f"{i+1}. {' '.join(gram)}" for i, gram in enumerate(bigrams)]
        set_basket("N-GRAMS (bigrams found)", lines if lines else ["Not enough words for a bigram."])
    except Exception:
        print("ERROR in do_ngrams:")
        traceback.print_exc()


def do_frequency():
    print(">>> Frequency crate CLICKED")
    try:
        if not check_ready():
            return
        words = get_words()
        freqlist = FrequencyList(words)
        lines = [f"{word} : {count}" for word, count in freqlist]
        set_basket("WORD FREQUENCY", lines)
    except Exception:
        print("ERROR in do_frequency:")
        traceback.print_exc()


def do_levenshtein():
    print(">>> Levenshtein crate CLICKED")
    try:
        if Windower is None:
            pynlpl_missing_warning()
            return

        word_a = word_a_entry.get().strip().lower()
        word_b = word_b_entry.get().strip().lower()

        if not word_a or not word_b:
            messagebox.showwarning("Missing Words", "Please enter both words to compare.")
            return

        distance = levenshtein(word_a, word_b)
        set_basket("LEVENSHTEIN DISTANCE", [
            f'"{word_a}" vs "{word_b}"',
            f"Distance: {distance} edit(s) needed",
            "(Lower = more similar. 0 means identical.)"
        ])
    except Exception:
        print("ERROR in do_levenshtein:")
        traceback.print_exc()


def do_stats():
    print(">>> Stats crate CLICKED")
    try:
        if not check_ready():
            return
        words = get_words()
        freqlist = FrequencyList(words)

        total_words = len(words)
        unique_words = len(freqlist)
        avg_len = sum(len(w) for w in words) / total_words
        ttr = unique_words / total_words

        set_basket("TEXT STATISTICS", [
            f"Total words: {total_words}",
            f"Unique words: {unique_words}",
            f"Average word length: {avg_len:.2f} letters",
            f"Type-Token Ratio: {ttr:.3f}  (higher = more varied vocabulary)"
        ])
    except Exception:
        print("ERROR in do_stats:")
        traceback.print_exc()


def clear_all():
    input_box.delete("1.0", tk.END)
    word_a_entry.delete(0, tk.END)
    word_b_entry.delete(0, tk.END)
    basket_output.delete("1.0", tk.END)
    basket_output.insert(tk.END, "Click a crate above to fill your basket!")


def exit_app():
    root.destroy()


def make_clickable(widget, command):
    widget.bind("<Button-1>", lambda e: command())
    widget.config(cursor="hand2")
    for child in widget.winfo_children():
        make_clickable(child, command)


def make_crate(parent, tag_text, title_text, desc_text, command):
    crate = tk.Frame(parent, bg=CRATE, highlightbackground=WOOD_DARK, highlightthickness=3,
                       padx=10, pady=10)

    tag = tk.Label(crate, text=tag_text, bg=TOMATO, fg="white", font=("Trebuchet MS", 8, "bold"),
                    padx=8, pady=2)
    tag.pack(anchor="e")

    title = tk.Label(crate, text=title_text, bg=PAPER, fg=LEAF_DARK, font=("Trebuchet MS", 12, "bold"),
                       padx=6, pady=6)
    title.pack(fill="x", pady=(4, 4))

    desc = tk.Label(crate, text=desc_text, bg=CRATE, fg="#5a3d1e", font=("Trebuchet MS", 9),
                      wraplength=200)
    desc.pack()

    make_clickable(crate, command)
    return crate


print("STEP 3: Building the window now...")

# ==========================================================
# GUI SETUP
# ==========================================================
root = tk.Tk()
root.title("PyNLPl Fruit Stand - DEBUG")
root.geometry("880x760")
root.configure(bg=SKY)

stand = tk.Frame(root, bg=WOOD, highlightbackground=WOOD_DARK, highlightthickness=6, padx=24, pady=20)
stand.pack(fill="both", expand=True, padx=18, pady=18)

# ---------- Header ----------
tk.Label(
    stand, text="\U0001F34D PyNLPl Fruit Stand", font=("Trebuchet MS", 24, "bold"),
    bg=WOOD, fg="#fff8e6"
).pack()

tk.Label(
    stand, text='"PyNLPl" is pronounced like "pineapple" - true story!', font=("Trebuchet MS", 10, "italic"),
    bg=WOOD, fg="#ffe9c2"
).pack(pady=(2, 6))

tk.Label(
    stand, text="  FRESH TEXT TOOLS \u00b7 DAILY PICK  ", font=("Trebuchet MS", 8, "bold"),
    bg=TOMATO, fg="white"
).pack(pady=(0, 14))

# ---------- Counter (input area) ----------
counter = tk.Frame(stand, bg=PAPER, highlightbackground=CRATE, highlightthickness=3, padx=16, pady=14)
counter.pack(fill="x", pady=(0, 16))

tk.Label(counter, text="\U0001F9FA Bring Your Text to the Stand", font=("Trebuchet MS", 10, "bold"),
          bg=PAPER, fg=LEAF_DARK).pack(anchor="w")

input_box = tk.Text(counter, height=3, font=("Trebuchet MS", 11), bg="#fffef8", fg=INK, relief="flat",
                      highlightbackground=CRATE, highlightthickness=1, padx=8, pady=6)
input_box.pack(fill="x", pady=(4, 10))
input_box.insert(tk.END, "The quick brown fox jumps over the lazy dog. The dog barks at the fox.")

tk.Label(counter, text="\U0001F347 Compare two words (for Levenshtein Crate)", font=("Trebuchet MS", 10, "bold"),
          bg=PAPER, fg=LEAF_DARK).pack(anchor="w")

word_row = tk.Frame(counter, bg=PAPER)
word_row.pack(fill="x", pady=(4, 0))

word_a_entry = tk.Entry(word_row, font=("Trebuchet MS", 11), highlightbackground=CRATE, highlightthickness=1)
word_a_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
word_a_entry.insert(0, "kitten")

word_b_entry = tk.Entry(word_row, font=("Trebuchet MS", 11), highlightbackground=CRATE, highlightthickness=1)
word_b_entry.pack(side="left", fill="x", expand=True)
word_b_entry.insert(0, "sitting")

# ---------- Stalls (2x2 crate grid) ----------
stalls = tk.Frame(stand, bg=WOOD)
stalls.pack(fill="x", pady=(0, 16))

stalls.columnconfigure(0, weight=1)
stalls.columnconfigure(1, weight=1)

crate1 = make_crate(stalls, "FRESH", "\U0001F34A N-Gram Crate",
                      "Groups of words that sit next to each other", do_ngrams)
crate1.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=(0, 8))

crate2 = make_crate(stalls, "POPULAR", "\U0001F34E Frequency Basket",
                      "Which words appear most often", do_frequency)
crate2.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=(0, 8))

crate3 = make_crate(stalls, "2-FOR-1", "\U0001F347 Levenshtein Crate",
                      "How different are two words, letter by letter", do_levenshtein)
crate3.grid(row=1, column=0, sticky="nsew", padx=(0, 8))

crate4 = make_crate(stalls, "DAILY", "\U0001F34B Stats Stall",
                      "Average word length & text variety", do_stats)
crate4.grid(row=1, column=1, sticky="nsew", padx=(8, 0))

# ---------- Basket (results) ----------
basket = tk.Frame(stand, bg=PAPER, highlightbackground=LEAF_DARK, highlightthickness=3, padx=16, pady=12)
basket.pack(fill="both", expand=True, pady=(0, 14))

tk.Label(basket, text="\U0001F9FA Your Basket (Results)", font=("Trebuchet MS", 11, "bold"),
          bg=PAPER, fg=LEAF_DARK).pack(anchor="w", pady=(0, 8))

basket_output = tk.Text(basket, font=("Consolas", 10), bg="#fffef8", fg=INK, relief="flat",
                          wrap="word")
basket_output.pack(fill="both", expand=True)
basket_output.insert(tk.END, "Click a crate above to fill your basket!")

# ---------- Bottom buttons ----------
bottom_row = tk.Frame(stand, bg=WOOD)
bottom_row.pack(fill="x")

tk.Button(
    bottom_row, text="Clear", command=clear_all,
    bg=CRATE, fg=INK, font=("Trebuchet MS", 9, "bold"),
    relief="flat", padx=18, pady=8, cursor="hand2"
).pack(side="left")

tk.Button(
    bottom_row, text="Exit", command=exit_app,
    bg=TOMATO, fg="white", font=("Trebuchet MS", 9, "bold"),
    relief="flat", padx=18, pady=8, cursor="hand2"
).pack(side="left", padx=(10, 0))

print("STEP 4: Window built, about to start mainloop")

root.after(300, do_frequency)

root.mainloop()

print("STEP 5: Window closed, script ending")