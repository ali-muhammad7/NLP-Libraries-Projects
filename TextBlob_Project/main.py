"""
TextBlob Text Analyzer
A beginner-friendly GUI for NLP text analysis using Tkinter and TextBlob.
Styled as a handwritten notebook / journal page.
"""

import tkinter as tk
from tkinter import scrolledtext, messagebox, Canvas

from textblob import TextBlob


# ==========================================================
# COLORS - warm "paper notebook" theme
# ==========================================================
PAPER = "#fdf6e3"
PAPER_LINE = "#e3d5b8"
INK = "#3b2f2f"
INK_SOFT = "#7a6a58"
MARGIN_RED = "#c1666b"
HIGHLIGHT = "#f4a259"
STICKY_YELLOW = "#fff3b0"
STICKY_GREEN = "#cdeac0"
STICKY_BLUE = "#c7ecee"
STICKY_PINK = "#f7d6e0"


# ==========================================================
# HELPER FUNCTIONS
# ==========================================================
def get_input_text():
    return input_box.get("1.0", tk.END).strip()


def classify_sentiment(polarity):
    if polarity > 0:
        return "Positive", "😊", STICKY_GREEN
    elif polarity < 0:
        return "Negative", "😞", STICKY_PINK
    else:
        return "Neutral", "😐", STICKY_YELLOW


def draw_mood_meter(polarity):
    """
    Draws a small horizontal 'mood meter' bar on the canvas:
    a line from -1 to +1 with a marker showing where this text falls.
    """
    mood_canvas.delete("all")
    w = 300
    h = 40
    mood_canvas.config(width=w, height=h)

    # baseline
    mood_canvas.create_line(10, h // 2, w - 10, h // 2, fill=INK_SOFT, width=2)
    # end labels
    mood_canvas.create_text(10, h - 8, text="-1", fill=INK_SOFT, font=("Comic Sans MS", 8))
    mood_canvas.create_text(w - 10, h - 8, text="+1", fill=INK_SOFT, font=("Comic Sans MS", 8))
    mood_canvas.create_text(w // 2, h - 8, text="0", fill=INK_SOFT, font=("Comic Sans MS", 8))

    # marker position: map polarity (-1..1) to x range (20..w-20)
    x = 20 + ((polarity + 1) / 2) * (w - 40)
    mood_canvas.create_oval(x - 8, h // 2 - 8, x + 8, h // 2 + 8, fill=HIGHLIGHT, outline=INK)


def make_sticky_note(parent, title, color):
    """Creates a 'sticky note' style frame with a title label, returns the content Text widget."""
    note = tk.Frame(parent, bg=color, padx=12, pady=10, highlightbackground=INK, highlightthickness=1)
    tk.Label(
        note, text=title, font=("Comic Sans MS", 11, "bold"),
        bg=color, fg=INK
    ).pack(anchor="w")
    text_widget = tk.Text(
        note, font=("Consolas", 9), bg=color, fg=INK, relief="flat",
        height=6, wrap="word", borderwidth=0, highlightthickness=0
    )
    text_widget.pack(fill="both", expand=True, pady=(5, 0))
    return note, text_widget


def fill_note(text_widget, content):
    text_widget.config(state="normal")
    text_widget.delete("1.0", tk.END)
    text_widget.insert(tk.END, content)
    text_widget.config(state="disabled")


# ==========================================================
# MAIN ANALYZE FUNCTION
# ==========================================================
def analyze_text():
    text = get_input_text()

    if not text:
        messagebox.showwarning("Empty Page", "Please write something in the notebook first.")
        return

    try:
        blob = TextBlob(text)
    except Exception as e:
        messagebox.showerror("TextBlob Error", f"Something went wrong while analyzing text:\n{e}")
        return

    # ---------- Sentiment ----------
    polarity = blob.sentiment.polarity
    subjectivity = blob.sentiment.subjectivity
    label, emoji, color = classify_sentiment(polarity)

    mood_label.config(text=f"{emoji}  {label}", bg=color)
    mood_detail.config(
        text=f"Polarity: {polarity:.2f}   |   Subjectivity: {subjectivity:.2f}"
    )
    draw_mood_meter(polarity)

    # ---------- Text Statistics ----------
    stats_text = (
        f"Words: {len(blob.words)}\n"
        f"Sentences: {len(blob.sentences)}\n"
        f"Characters: {len(text)}"
    )
    fill_note(stats_note_text, stats_text)

    # ---------- Noun Phrases ----------
    if blob.noun_phrases:
        phrases_text = "\n".join(f"• {p}" for p in blob.noun_phrases)
    else:
        phrases_text = "No noun phrases found."
    fill_note(phrases_note_text, phrases_text)

    # ---------- Word Info (POS tags) ----------
    tags_text = "\n".join(f"{w}  ->  {t}" for w, t in blob.tags)
    fill_note(tags_note_text, tags_text)


# ==========================================================
# SPELLING CORRECTION
# ==========================================================
def correct_spelling():
    text = get_input_text()

    if not text:
        messagebox.showwarning("Empty Page", "Please write something in the notebook first.")
        return

    try:
        blob = TextBlob(text)
        corrected = str(blob.correct())
    except Exception as e:
        messagebox.showerror("TextBlob Error", f"Could not correct spelling:\n{e}")
        return

    correction_box.config(state="normal")
    correction_box.delete("1.0", tk.END)
    correction_box.insert(tk.END, corrected)
    correction_box.config(state="disabled")


# ==========================================================
# CLEAR / EXIT
# ==========================================================
def clear_all():
    input_box.delete("1.0", tk.END)

    mood_label.config(text="—  Waiting...", bg=STICKY_YELLOW)
    mood_detail.config(text="Polarity: --   |   Subjectivity: --")
    mood_canvas.delete("all")

    for widget in (stats_note_text, phrases_note_text, tags_note_text):
        fill_note(widget, "")

    correction_box.config(state="normal")
    correction_box.delete("1.0", tk.END)
    correction_box.config(state="disabled")


def exit_app():
    root.destroy()


# ==========================================================
# GUI SETUP - Notebook / Journal Theme
# ==========================================================
root = tk.Tk()
root.title("TextBlob Notebook")
root.geometry("1000x760")
root.configure(bg=PAPER)

# ---------- Notebook "spiral binding" strip on the left ----------
spiral = tk.Canvas(root, width=30, bg="#e8ddc0", highlightthickness=0)
spiral.pack(side="left", fill="y")
for y in range(20, 800, 34):
    spiral.create_oval(8, y, 22, y + 14, fill="#b0a48a", outline="")

# ---------- Main page area ----------
page = tk.Frame(root, bg=PAPER)
page.pack(side="left", fill="both", expand=True, padx=25, pady=20)

# ---------- Title (handwritten style) ----------
tk.Label(
    page, text="📓 TextBlob Notebook", font=("Comic Sans MS", 24, "bold"),
    bg=PAPER, fg=INK
).pack(anchor="w")

tk.Label(
    page, text="my little NLP journal for text analysis", font=("Comic Sans MS", 11, "italic"),
    bg=PAPER, fg=INK_SOFT
).pack(anchor="w", pady=(0, 15))

# ---------- Input "notebook page" ----------
input_frame = tk.Frame(page, bg=PAPER, highlightbackground=MARGIN_RED, highlightthickness=0)
input_frame.pack(fill="x")

tk.Label(
    input_frame, text="Write something here:", font=("Comic Sans MS", 11, "bold"),
    bg=PAPER, fg=INK
).pack(anchor="w")

input_box = tk.Text(
    input_frame, height=5, font=("Comic Sans MS", 11), bg="#fffdf5", fg=INK,
    relief="flat", highlightbackground=PAPER_LINE, highlightthickness=1,
    padx=10, pady=8
)
input_box.pack(fill="x", pady=(5, 10))

# ---------- Buttons (like sticky tabs) ----------
button_frame = tk.Frame(page, bg=PAPER)
button_frame.pack(fill="x", pady=(0, 15))

tk.Button(
    button_frame, text="✏️  Analyze", command=analyze_text,
    bg=HIGHLIGHT, fg=INK, font=("Comic Sans MS", 10, "bold"),
    relief="flat", padx=18, pady=8, cursor="hand2"
).pack(side="left", padx=(0, 8))

tk.Button(
    button_frame, text="🔤  Fix Spelling", command=correct_spelling,
    bg=STICKY_BLUE, fg=INK, font=("Comic Sans MS", 10, "bold"),
    relief="flat", padx=18, pady=8, cursor="hand2"
).pack(side="left", padx=(0, 8))

tk.Button(
    button_frame, text="🧹  Clear Page", command=clear_all,
    bg="#e8ddc0", fg=INK, font=("Comic Sans MS", 10, "bold"),
    relief="flat", padx=18, pady=8, cursor="hand2"
).pack(side="left", padx=(0, 8))

tk.Button(
    button_frame, text="✖  Exit", command=exit_app,
    bg=MARGIN_RED, fg="white", font=("Comic Sans MS", 10, "bold"),
    relief="flat", padx=18, pady=8, cursor="hand2"
).pack(side="left")

# ---------- Mood Meter Section ----------
mood_frame = tk.Frame(page, bg=PAPER)
mood_frame.pack(fill="x", pady=(0, 15))

tk.Label(
    mood_frame, text="Mood of the text:", font=("Comic Sans MS", 11, "bold"),
    bg=PAPER, fg=INK
).grid(row=0, column=0, sticky="w")

mood_label = tk.Label(
    mood_frame, text="—  Waiting...", font=("Comic Sans MS", 13, "bold"),
    bg=STICKY_YELLOW, fg=INK, padx=14, pady=6
)
mood_label.grid(row=0, column=1, padx=(10, 0), sticky="w")

mood_detail = tk.Label(
    mood_frame, text="Polarity: --   |   Subjectivity: --",
    font=("Consolas", 9), bg=PAPER, fg=INK_SOFT
)
mood_detail.grid(row=1, column=0, columnspan=2, sticky="w", pady=(5, 5))

mood_canvas = tk.Canvas(mood_frame, bg=PAPER, highlightthickness=0)
mood_canvas.grid(row=2, column=0, columnspan=2, sticky="w")

# ---------- Sticky Notes Row (Stats / Noun Phrases / POS Tags) ----------
notes_frame = tk.Frame(page, bg=PAPER)
notes_frame.pack(fill="both", expand=True, pady=(0, 15))

stats_note, stats_note_text = make_sticky_note(notes_frame, "📊 Text Stats", STICKY_YELLOW)
stats_note.pack(side="left", fill="both", expand=True, padx=(0, 8))

phrases_note, phrases_note_text = make_sticky_note(notes_frame, "🌿 Noun Phrases", STICKY_GREEN)
phrases_note.pack(side="left", fill="both", expand=True, padx=(0, 8))

tags_note, tags_note_text = make_sticky_note(notes_frame, "🔤 Word Tags", STICKY_BLUE)
tags_note.pack(side="left", fill="both", expand=True)

# ---------- Spelling Correction "margin note" ----------
correction_frame = tk.Frame(page, bg=PAPER)
correction_frame.pack(fill="x")

tk.Label(
    correction_frame, text="✅ Corrected version:", font=("Comic Sans MS", 11, "bold"),
    bg=PAPER, fg=INK
).pack(anchor="w")

correction_box = tk.Text(
    correction_frame, height=3, font=("Comic Sans MS", 10), bg=STICKY_PINK, fg=INK,
    relief="flat", padx=10, pady=8, state="disabled"
)
correction_box.pack(fill="x", pady=(5, 0))

# ---------- Run ----------
root.mainloop()