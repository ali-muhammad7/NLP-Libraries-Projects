"""
Textacy Text Insights
A beginner-friendly GUI for text analysis using Tkinter and textacy.
Styled as a dark analytics console with a sidebar and metric cards.
"""

import tkinter as tk
from tkinter import scrolledtext, messagebox

import spacy
import textacy
from textacy import extract
from textacy import text_stats


# ==========================================================
# COLORS - dark analytics dashboard theme
# ==========================================================
BG_DARK = "#0f172a"
SIDEBAR = "#111827"
PANEL = "#1e293b"
ACCENT = "#22d3ee"
ACCENT_2 = "#f472b6"
TEXT_LIGHT = "#e5e7eb"
TEXT_MUTED = "#94a3b8"


# ==========================================================
# LOAD THE SPACY MODEL
# ==========================================================
nlp = None
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    nlp = None


def model_missing_warning():
    messagebox.showerror(
        "spaCy Model Not Found",
        "The English model 'en_core_web_sm' is required by textacy.\n\n"
        "Please open your terminal and run:\n\n"
        "python -m spacy download en_core_web_sm\n\n"
        "Then restart this program."
    )


# ==========================================================
# HELPER FUNCTIONS
# ==========================================================
def get_input_text():
    return input_box.get("1.0", tk.END).strip()


def check_ready():
    if nlp is None:
        model_missing_warning()
        return None
    text = get_input_text()
    if not text:
        messagebox.showwarning("Empty Input", "Please enter some text first.")
        return None
    return textacy.make_spacy_doc(text, lang=nlp)


def set_active_nav(name):
    for key, btn in nav_buttons.items():
        if key == name:
            btn.config(bg=ACCENT, fg="#0f172a")
        else:
            btn.config(bg=SIDEBAR, fg=TEXT_LIGHT)


def show_report(title, subtitle, content):
    """Fills the main report panel (text-based results)."""
    report_title.config(text=title)
    report_subtitle.config(text=subtitle)
    output_box.config(state="normal")
    output_box.delete("1.0", tk.END)
    output_box.insert(tk.END, content)
    output_box.config(state="disabled")


def clear_metric_cards():
    for card in metric_cards:
        card["value"].config(text="--")


def set_metric_cards(pairs):
    """pairs: list of (label, value) tuples, fills up to 4 cards."""
    for i, card in enumerate(metric_cards):
        if i < len(pairs):
            label, value = pairs[i]
            card["label"].config(text=label)
            card["value"].config(text=str(value))
        else:
            card["label"].config(text="")
            card["value"].config(text="")


def draw_score_bar(score, max_score=100, bar_label="Score"):
    """Draws a simple horizontal bar chart on the canvas to visualize a 0-100 score."""
    chart_canvas.delete("all")
    w = 400
    h = 60
    chart_canvas.config(width=w, height=h)

    # background track
    chart_canvas.create_rectangle(10, 25, w - 10, 45, fill=PANEL, outline="")

    # filled portion
    clamped = max(0, min(score, max_score))
    fill_width = 10 + (clamped / max_score) * (w - 20)
    chart_canvas.create_rectangle(10, 25, fill_width, 45, fill=ACCENT, outline="")

    chart_canvas.create_text(
        10, 12, anchor="w", text=f"{bar_label}: {score:.1f} / {max_score}",
        fill=TEXT_LIGHT, font=("Segoe UI", 10, "bold")
    )


# ==========================================================
# NLP OPERATION FUNCTIONS
# ==========================================================

def do_keyterms():
    doc = check_ready()
    if doc is None:
        return
    set_active_nav("Key Terms")
    try:
        terms = list(extract.keyterms.textrank(doc, topn=10))
        if not terms:
            show_report("Key Terms", "TextRank extraction", "No key terms could be extracted (text may be too short).")
            clear_metric_cards()
            chart_canvas.delete("all")
            return
        lines = [f"{i+1}. {term}   (score: {score:.3f})" for i, (term, score) in enumerate(terms)]
        show_report("Key Terms", "Top ranked words & phrases (TextRank)", "\n".join(lines))
        set_metric_cards([("Terms Found", len(terms)), ("Top Term", terms[0][0]), ("Top Score", f"{terms[0][1]:.3f}"), ("", "")])
        chart_canvas.delete("all")
    except Exception as e:
        messagebox.showerror("Error", f"Could not extract key terms:\n{e}")


def do_readability():
    doc = check_ready()
    if doc is None:
        return
    set_active_nav("Readability")
    try:
        stats = text_stats.TextStats(doc)
        flesch_ease = stats.readability("flesch_reading_ease")
        flesch_grade = stats.readability("flesch_kincaid_grade_level")

        result = ""
        result += f"Word count           : {stats.n_words}\n"
        result += f"Sentence count       : {stats.n_sents}\n"
        result += f"Syllable count       : {stats.n_syllables}\n"
        result += f"Avg words/sentence   : {stats.n_words / stats.n_sents:.2f}\n\n"
        result += f"Flesch Reading Ease  : {flesch_ease:.2f}\n"
        result += "   (Higher = easier to read. 60-70 is considered 'plain English'.)\n\n"
        result += f"Flesch-Kincaid Grade : {flesch_grade:.2f}\n"
        result += "   (Roughly the US school grade level needed to understand the text.)"

        show_report("Readability", "How easy is this text to read?", result)
        set_metric_cards([
            ("Flesch Ease", f"{flesch_ease:.1f}"),
            ("Grade Level", f"{flesch_grade:.1f}"),
            ("Words", stats.n_words),
            ("Sentences", stats.n_sents),
        ])
        # Flesch Reading Ease is roughly 0-100
        draw_score_bar(max(0, min(flesch_ease, 100)), 100, "Flesch Reading Ease")
    except Exception as e:
        messagebox.showerror("Error", f"Could not calculate readability:\n{e}")


def do_ngrams():
    doc = check_ready()
    if doc is None:
        return
    set_active_nav("N-Grams")
    try:
        bigrams = [ng.text for ng in extract.ngrams(doc, n=2, filter_stops=True, filter_punct=True)]
        trigrams = [ng.text for ng in extract.ngrams(doc, n=3, filter_stops=True, filter_punct=True)]

        result = "BIGRAMS (2-word phrases)\n" + "-" * 40 + "\n"
        result += "\n".join(bigrams[:15]) if bigrams else "None found."
        result += "\n\n" + "TRIGRAMS (3-word phrases)\n" + "-" * 40 + "\n"
        result += "\n".join(trigrams[:15]) if trigrams else "None found."

        show_report("N-Grams", "Common word combinations", result)
        set_metric_cards([("Bigrams", len(bigrams)), ("Trigrams", len(trigrams)), ("", ""), ("", "")])
        chart_canvas.delete("all")
    except Exception as e:
        messagebox.showerror("Error", f"Could not extract n-grams:\n{e}")


def do_basic_stats():
    doc = check_ready()
    if doc is None:
        return
    set_active_nav("Basic Stats")
    try:
        stats = text_stats.TextStats(doc)
        text = get_input_text()
        unique_words = len(set(token.text.lower() for token in doc if token.is_alpha))

        result = ""
        result += f"Characters        : {len(text)}\n"
        result += f"Words             : {stats.n_words}\n"
        result += f"Unique words      : {unique_words}\n"
        result += f"Sentences         : {stats.n_sents}\n"
        result += f"Syllables         : {stats.n_syllables}\n"
        result += f"Long words (7+)   : {stats.n_long_words}"

        show_report("Basic Stats", "Overview of the raw text", result)
        set_metric_cards([
            ("Words", stats.n_words),
            ("Unique Words", unique_words),
            ("Sentences", stats.n_sents),
            ("Characters", len(text)),
        ])
        chart_canvas.delete("all")
    except Exception as e:
        messagebox.showerror("Error", f"Could not calculate statistics:\n{e}")


def clear_all():
    input_box.delete("1.0", tk.END)
    report_title.config(text="No report yet")
    report_subtitle.config(text="Choose a metric from the left to generate a report")
    output_box.config(state="normal")
    output_box.delete("1.0", tk.END)
    output_box.config(state="disabled")
    clear_metric_cards()
    chart_canvas.delete("all")
    for btn in nav_buttons.values():
        btn.config(bg=SIDEBAR, fg=TEXT_LIGHT)


def exit_app():
    root.destroy()


# ==========================================================
# GUI SETUP - Dark Analytics Console
# ==========================================================
root = tk.Tk()
root.title("Textacy Insights Console")
root.geometry("1100x700")
root.configure(bg=BG_DARK)

# ---------- Sidebar ----------
sidebar = tk.Frame(root, bg=SIDEBAR, width=200)
sidebar.pack(side="left", fill="y")
sidebar.pack_propagate(False)

tk.Label(
    sidebar, text="📈 Textacy", font=("Segoe UI", 16, "bold"),
    bg=SIDEBAR, fg=ACCENT
).pack(anchor="w", padx=20, pady=(25, 0))

tk.Label(
    sidebar, text="Insights Console", font=("Segoe UI", 9),
    bg=SIDEBAR, fg=TEXT_MUTED
).pack(anchor="w", padx=20, pady=(0, 25))

nav_buttons = {}
operations = [
    ("Key Terms", do_keyterms),
    ("Readability", do_readability),
    ("N-Grams", do_ngrams),
    ("Basic Stats", do_basic_stats),
]

for label, command in operations:
    btn = tk.Button(
        sidebar, text="  " + label, command=command,
        bg=SIDEBAR, fg=TEXT_LIGHT, font=("Segoe UI", 10, "bold"),
        relief="flat", anchor="w", padx=10, pady=12, cursor="hand2"
    )
    btn.pack(fill="x", padx=10, pady=3)
    nav_buttons[label] = btn

tk.Frame(sidebar, bg=SIDEBAR).pack(fill="both", expand=True)  # spacer

tk.Button(
    sidebar, text="  Clear", command=clear_all,
    bg=SIDEBAR, fg=TEXT_MUTED, font=("Segoe UI", 10),
    relief="flat", anchor="w", padx=10, pady=10, cursor="hand2"
).pack(fill="x", padx=10, pady=2)

tk.Button(
    sidebar, text="  Exit", command=exit_app,
    bg="#7f1d1d", fg="white", font=("Segoe UI", 10, "bold"),
    relief="flat", anchor="w", padx=10, pady=10, cursor="hand2"
).pack(fill="x", padx=10, pady=(2, 20))

# ---------- Main Content Area ----------
content = tk.Frame(root, bg=BG_DARK)
content.pack(side="left", fill="both", expand=True, padx=25, pady=20)

# ---------- Input Box ----------
tk.Label(
    content, text="INPUT TEXT", font=("Segoe UI", 9, "bold"),
    bg=BG_DARK, fg=TEXT_MUTED
).pack(anchor="w")

input_box = scrolledtext.ScrolledText(
    content, height=4, font=("Consolas", 11), bg=PANEL, fg=TEXT_LIGHT,
    insertbackground=TEXT_LIGHT, relief="flat"
)
input_box.pack(fill="x", pady=(6, 15))

# ---------- Metric Cards Row ----------
cards_frame = tk.Frame(content, bg=BG_DARK)
cards_frame.pack(fill="x", pady=(0, 15))

metric_cards = []
for i in range(4):
    card = tk.Frame(cards_frame, bg=PANEL, padx=15, pady=12)
    card.pack(side="left", fill="both", expand=True, padx=(0 if i == 0 else 8, 0))

    lbl = tk.Label(card, text="", font=("Segoe UI", 9), bg=PANEL, fg=TEXT_MUTED)
    lbl.pack(anchor="w")

    val = tk.Label(card, text="--", font=("Segoe UI", 18, "bold"), bg=PANEL, fg=ACCENT_2)
    val.pack(anchor="w")

    metric_cards.append({"label": lbl, "value": val})

# ---------- Score Bar Chart ----------
chart_canvas = tk.Canvas(content, bg=BG_DARK, highlightthickness=0, height=60)
chart_canvas.pack(fill="x", pady=(0, 15))

# ---------- Report Panel ----------
report_panel = tk.Frame(content, bg=PANEL, padx=20, pady=15)
report_panel.pack(fill="both", expand=True)

report_title = tk.Label(
    report_panel, text="No report yet", font=("Segoe UI", 15, "bold"),
    bg=PANEL, fg=TEXT_LIGHT
)
report_title.pack(anchor="w")

report_subtitle = tk.Label(
    report_panel, text="Choose a metric from the left to generate a report",
    font=("Segoe UI", 9), bg=PANEL, fg=TEXT_MUTED
)
report_subtitle.pack(anchor="w", pady=(0, 10))

output_box = scrolledtext.ScrolledText(
    report_panel, font=("Consolas", 10), bg="#0b1220", fg="#c7f9ff",
    relief="flat", state="disabled"
)
output_box.pack(fill="both", expand=True)

# ---------- Run ----------
root.mainloop()