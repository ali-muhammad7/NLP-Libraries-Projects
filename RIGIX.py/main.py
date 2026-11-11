import tkinter as tk
from tkinter import messagebox
import re


# -----------------------------
# Check Regex Function
# -----------------------------
def check_regex():
    pattern = regex_entry.get()
    text = text_box.get("1.0", tk.END).strip()

    if not pattern:
        messagebox.showwarning("Warning", "Please enter a regular expression.")
        return

    try:
        matches = re.findall(pattern, text)

        result_box.delete("1.0", tk.END)

        if matches:
            result_box.insert(tk.END, ">> MATCHES FOUND\n\n")

            for i, match in enumerate(matches, start=1):
                if isinstance(match, tuple):
                    match = " | ".join(match)
                result_box.insert(tk.END, f"[{i}]  {match}\n")

            result_box.insert(
                tk.END,
                f"\n>> TOTAL: {len(matches)} match(es)"
            )
        else:
            result_box.insert(tk.END, ">> No matches found.")

    except re.error as e:
        messagebox.showerror(
            "Regex Error",
            f"Invalid Regular Expression!\n\n{e}"
        )


# -----------------------------
# Clear Function
# -----------------------------
def clear():
    regex_entry.delete(0, tk.END)
    text_box.delete("1.0", tk.END)
    result_box.delete("1.0", tk.END)


# -----------------------------
# Load a Quick Pattern (small extra feature to make it feel different)
# -----------------------------
def load_pattern(pattern):
    regex_entry.delete(0, tk.END)
    regex_entry.insert(0, pattern)


# -----------------------------
# Main Window
# -----------------------------
root = tk.Tk()
root.title("RegexLab :: Pattern Matcher")
root.geometry("750x680")
root.configure(bg="#0d1117")  # GitHub-dark-style background

FONT_MONO = ("Consolas", 11)
ACCENT = "#39d353"   # terminal green
ACCENT_DIM = "#1f6feb"
BG_PANEL = "#161b22"
BG_INPUT = "#010409"
TEXT_MUTED = "#8b949e"


# ---------- Title Bar ----------
title_frame = tk.Frame(root, bg="#0d1117")
title_frame.pack(fill="x", pady=(20, 5), padx=25)

tk.Label(
    title_frame, text="RegexLab", font=("Consolas", 22, "bold"),
    bg="#0d1117", fg=ACCENT
).pack(side="left")

tk.Label(
    title_frame, text="  pattern matcher", font=("Consolas", 12),
    bg="#0d1117", fg=TEXT_MUTED
).pack(side="left", padx=(2, 0))

# ---------- Pattern Input ----------
pattern_frame = tk.Frame(root, bg="#0d1117")
pattern_frame.pack(fill="x", padx=25, pady=(15, 5))

tk.Label(
    pattern_frame, text="$ pattern", font=FONT_MONO,
    bg="#0d1117", fg=ACCENT_DIM
).pack(anchor="w")

regex_entry = tk.Entry(
    pattern_frame, font=("Consolas", 13), bg=BG_INPUT, fg=ACCENT,
    insertbackground=ACCENT, relief="flat"
)
regex_entry.pack(fill="x", ipady=10, pady=(5, 5))

# ---------- Quick Pattern Chips ----------
chips_frame = tk.Frame(root, bg="#0d1117")
chips_frame.pack(fill="x", padx=25, pady=(0, 15))

quick_patterns = [
    ("Email", r"\w+@\w+\.\w+"),
    ("Phone", r"\d{4}-\d{7}"),
    ("URL", r"https?://\S+"),
    ("Digits", r"\d+"),
]

for label, pattern in quick_patterns:
    tk.Button(
        chips_frame, text=label, font=("Consolas", 9),
        bg=BG_PANEL, fg=TEXT_MUTED, relief="flat",
        padx=12, pady=5, cursor="hand2",
        command=lambda p=pattern: load_pattern(p)
    ).pack(side="left", padx=(0, 8))

# ---------- Input Text ----------
text_frame = tk.Frame(root, bg="#0d1117")
text_frame.pack(fill="x", padx=25)

tk.Label(
    text_frame, text="$ input_text", font=FONT_MONO,
    bg="#0d1117", fg=ACCENT_DIM
).pack(anchor="w")

text_box = tk.Text(
    text_frame, height=6, font=FONT_MONO, bg=BG_INPUT, fg="#c9d1d9",
    insertbackground=ACCENT, relief="flat"
)
text_box.pack(fill="x", pady=(5, 15))

# ---------- Buttons ----------
button_frame = tk.Frame(root, bg="#0d1117")
button_frame.pack(padx=25, fill="x")

tk.Button(
    button_frame, text="RUN MATCH", command=check_regex,
    bg=ACCENT, fg="#0d1117", font=("Consolas", 11, "bold"),
    relief="flat", padx=25, pady=10, cursor="hand2"
).pack(side="left", padx=(0, 10))

tk.Button(
    button_frame, text="CLEAR", command=clear,
    bg=BG_PANEL, fg=TEXT_MUTED, font=("Consolas", 11, "bold"),
    relief="flat", padx=25, pady=10, cursor="hand2"
).pack(side="left")

# ---------- Result Section ----------
result_frame = tk.Frame(root, bg="#0d1117")
result_frame.pack(fill="both", expand=True, padx=25, pady=(20, 20))

tk.Label(
    result_frame, text="$ output", font=FONT_MONO,
    bg="#0d1117", fg=ACCENT_DIM
).pack(anchor="w")

result_box = tk.Text(
    result_frame, font=FONT_MONO, bg=BG_PANEL, fg=ACCENT,
    relief="flat", insertbackground=ACCENT
)
result_box.pack(fill="both", expand=True, pady=(5, 0))

# ---------- Run ----------
root.mainloop()