"""
NLP Toolkit - spaCy
A beginner-friendly GUI for common spaCy NLP operations using Tkinter.
Styled as a card-based dashboard.
"""

import tkinter as tk
from tkinter import scrolledtext, messagebox

import spacy


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
        "The English model 'en_core_web_sm' is not installed.\n\n"
        "Please open your terminal and run:\n\n"
        "python -m spacy download en_core_web_sm\n\n"
        "Then restart this program."
    )


# ==========================================================
# HELPER FUNCTIONS
# ==========================================================
def get_input_text():
    return input_box.get("1.0", tk.END).strip()


def show_output(title, content, count_text=""):
    """Updates the dashboard card: title, small stat badge, and content."""
    card_title.config(text=title)
    card_badge.config(text=count_text)
    output_box.config(state="normal")
    output_box.delete("1.0", tk.END)
    output_box.insert(tk.END, content)
    output_box.config(state="disabled")


def check_ready():
    if nlp is None:
        model_missing_warning()
        return None
    text = get_input_text()
    if not text:
        messagebox.showwarning("Empty Input", "Please enter some text first.")
        return None
    return nlp(text)


def set_active_card(name):
    """Highlights the selected operation card in the sidebar."""
    for key, btn in nav_cards.items():
        if key == name:
            btn.config(bg=ACCENT, fg="white")
        else:
            btn.config(bg=CARD_BG, fg=TEXT_DARK)


# ==========================================================
# NLP OPERATION FUNCTIONS
# ==========================================================

def do_tokenization():
    doc = check_ready()
    if doc is None:
        return
    set_active_card("Tokenization")
    tokens = [token.text for token in doc]
    result = "\n".join(f"{i+1}.  {t}" for i, t in enumerate(tokens))
    show_output("Tokenization", result, f"{len(tokens)} tokens")


def do_pos_tagging():
    doc = check_ready()
    if doc is None:
        return
    set_active_card("POS Tagging")
    header = f"{'WORD':<15}{'POS':<10}{'DETAILED TAG'}\n" + "-" * 45 + "\n"
    lines = [f"{token.text:<15}{token.pos_:<10}{token.tag_}" for token in doc if not token.is_space]
    show_output("Part-of-Speech Tagging", header + "\n".join(lines), f"{len(lines)} words")


def do_ner():
    doc = check_ready()
    if doc is None:
        return
    set_active_card("Named Entities")
    if not doc.ents:
        show_output("Named Entity Recognition", "No named entities were found in this text.", "0 entities")
        return
    header = f"{'ENTITY':<25}{'LABEL':<10}{'DESCRIPTION'}\n" + "-" * 65 + "\n"
    lines = [f"{ent.text:<25}{ent.label_:<10}{spacy.explain(ent.label_)}" for ent in doc.ents]
    show_output("Named Entity Recognition", header + "\n".join(lines), f"{len(doc.ents)} entities")


def do_lemmatization():
    doc = check_ready()
    if doc is None:
        return
    set_active_card("Lemmatization")
    header = f"{'ORIGINAL WORD':<20}{'LEMMA'}\n" + "-" * 35 + "\n"
    lines = [f"{token.text:<20}{token.lemma_}" for token in doc if token.is_alpha]
    show_output("Lemmatization", header + "\n".join(lines), f"{len(lines)} words")


def do_sentence_segmentation():
    doc = check_ready()
    if doc is None:
        return
    set_active_card("Sentences")
    sentences = list(doc.sents)
    result = "\n\n".join(f"{i+1}.  {sent.text.strip()}" for i, sent in enumerate(sentences))
    show_output("Sentence Segmentation", result, f"{len(sentences)} sentences")


def do_dependency_parsing():
    doc = check_ready()
    if doc is None:
        return
    set_active_card("Dependencies")
    header = f"{'WORD':<15}{'DEPENDENCY':<15}{'HEAD WORD'}\n" + "-" * 45 + "\n"
    lines = [f"{token.text:<15}{token.dep_:<15}{token.head.text}" for token in doc if not token.is_space]
    show_output("Dependency Parsing", header + "\n".join(lines), f"{len(lines)} words")


def clear_all():
    input_box.delete("1.0", tk.END)
    card_title.config(text="No analysis yet")
    card_badge.config(text="")
    output_box.config(state="normal")
    output_box.delete("1.0", tk.END)
    output_box.insert(tk.END, "Type some text above and choose an operation from the left panel to see results here.")
    output_box.config(state="disabled")
    update_button_state()
    for btn in nav_cards.values():
        btn.config(bg=CARD_BG, fg=TEXT_DARK)


def exit_app():
    root.destroy()


def update_button_state(event=None):
    has_text = bool(input_box.get("1.0", tk.END).strip())
    state = "normal" if has_text else "disabled"
    for btn in nav_cards.values():
        btn.config(state=state)


# ==========================================================
# GUI SETUP - Card Dashboard Theme
# ==========================================================
root = tk.Tk()
root.title("spaCy Dashboard")
root.geometry("1050x680")

BG = "#eef1f8"
SIDEBAR_BG = "#ffffff"
CARD_BG = "#f4f6fb"
ACCENT = "#4361ee"
TEXT_DARK = "#1b1f3b"
TEXT_MUTED = "#6b7094"

root.configure(bg=BG)

# ---------- Top Bar ----------
top_bar = tk.Frame(root, bg=BG)
top_bar.pack(fill="x", padx=25, pady=(20, 10))

tk.Label(
    top_bar, text="spaCy Dashboard", font=("Segoe UI", 20, "bold"),
    bg=BG, fg=TEXT_DARK
).pack(side="left")

tk.Label(
    top_bar, text="  •  NLP Lab Project", font=("Segoe UI", 11),
    bg=BG, fg=TEXT_MUTED
).pack(side="left")

tk.Button(
    top_bar, text="Exit", command=exit_app,
    bg="#ef476f", fg="white", font=("Segoe UI", 9, "bold"),
    relief="flat", padx=16, pady=6, cursor="hand2"
).pack(side="right")

# ---------- Input Card ----------
input_card = tk.Frame(root, bg=SIDEBAR_BG, padx=20, pady=15)
input_card.pack(fill="x", padx=25, pady=(0, 15))

tk.Label(
    input_card, text="INPUT TEXT", font=("Segoe UI", 9, "bold"),
    bg=SIDEBAR_BG, fg=TEXT_MUTED
).pack(anchor="w")

input_box = scrolledtext.ScrolledText(
    input_card, height=4, font=("Consolas", 11), bg=CARD_BG, relief="flat", bd=0
)
input_box.pack(fill="x", pady=(8, 10))
input_box.bind("<KeyRelease>", update_button_state)

tk.Button(
    input_card, text="Clear", command=clear_all,
    bg="#e5e9f5", fg=TEXT_DARK, font=("Segoe UI", 9, "bold"),
    relief="flat", padx=16, pady=6, cursor="hand2"
).pack(anchor="e")

# ---------- Main Split: Sidebar (operation cards) + Result Card ----------
main_frame = tk.Frame(root, bg=BG)
main_frame.pack(fill="both", expand=True, padx=25, pady=(0, 20))

# ---------- Sidebar of operation "cards" ----------
sidebar = tk.Frame(main_frame, bg=BG, width=220)
sidebar.pack(side="left", fill="y", padx=(0, 15))

tk.Label(
    sidebar, text="OPERATIONS", font=("Segoe UI", 9, "bold"),
    bg=BG, fg=TEXT_MUTED
).pack(anchor="w", pady=(0, 8))

nav_cards = {}
operations = [
    ("Tokenization", do_tokenization),
    ("POS Tagging", do_pos_tagging),
    ("Named Entities", do_ner),
    ("Lemmatization", do_lemmatization),
    ("Sentences", do_sentence_segmentation),
    ("Dependencies", do_dependency_parsing),
]

for label, command in operations:
    btn = tk.Button(
        sidebar, text=label, command=command,
        bg=CARD_BG, fg=TEXT_DARK, font=("Segoe UI", 10, "bold"),
        relief="flat", padx=14, pady=14, width=20, anchor="w",
        cursor="hand2", state="disabled"
    )
    btn.pack(pady=5, fill="x")
    nav_cards[label] = btn

# ---------- Result Card ----------
result_card = tk.Frame(main_frame, bg=SIDEBAR_BG, padx=20, pady=18)
result_card.pack(side="right", fill="both", expand=True)

result_header = tk.Frame(result_card, bg=SIDEBAR_BG)
result_header.pack(fill="x")

card_title = tk.Label(
    result_header, text="No analysis yet", font=("Segoe UI", 14, "bold"),
    bg=SIDEBAR_BG, fg=TEXT_DARK
)
card_title.pack(side="left")

card_badge = tk.Label(
    result_header, text="", font=("Segoe UI", 9, "bold"),
    bg=ACCENT, fg="white", padx=10, pady=3
)
card_badge.pack(side="right")

output_box = scrolledtext.ScrolledText(
    result_card, font=("Consolas", 10), bg=CARD_BG, fg=TEXT_DARK,
    relief="flat", bd=0, state="normal"
)
output_box.insert(tk.END, "Type some text above and choose an operation from the left panel to see results here.")
output_box.config(state="disabled")
output_box.pack(fill="both", expand=True, pady=(15, 0))

# ---------- Run ----------
root.mainloop()