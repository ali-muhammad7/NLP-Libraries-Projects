"""
NLP Toolkit - NLTK
A beginner-friendly GUI for basic NLP operations using Tkinter and NLTK.
"""

import tkinter as tk
from tkinter import scrolledtext, messagebox

import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer, WordNetLemmatizer
from nltk import pos_tag
from nltk.probability import FreqDist


# ==========================================================
# HELPER: Get text from input box
# ==========================================================
def get_input_text():
    """Reads and returns the text typed by the user, removing extra spaces."""
    text = input_box.get("1.0", tk.END).strip()
    return text


def show_output(title, content):
    """Clears the output box and displays a new result with a heading."""
    output_box.delete("1.0", tk.END)
    output_box.insert(tk.END, f"{title}\n")
    output_box.insert(tk.END, "-" * 50 + "\n")
    output_box.insert(tk.END, content)


def missing_resource_message(error):
    """
    NLTK raises a LookupError when a required data package (like 'punkt')
    is not downloaded. This function turns that error into a friendly,
    understandable message for the user instead of crashing the app.
    """
    messagebox.showerror(
        "Missing NLTK Data",
        "Some required NLTK data is not downloaded on this computer.\n\n"
        "Please run this in Python once:\n\n"
        "import nltk\n"
        "nltk.download('punkt')\n"
        "nltk.download('punkt_tab')\n"
        "nltk.download('stopwords')\n"
        "nltk.download('wordnet')\n"
        "nltk.download('averaged_perceptron_tagger')\n"
        "nltk.download('averaged_perceptron_tagger_eng')\n\n"
        f"Technical detail: {error}"
    )


# ==========================================================
# NLP OPERATION FUNCTIONS
# Each button below calls one of these functions.
# ==========================================================

def do_general_tokenization():
    """Splits text into both sentences and words, shown together."""
    text = get_input_text()
    if not text:
        messagebox.showwarning("Empty Input", "Please enter some text first.")
        return
    try:
        sentences = sent_tokenize(text)
        words = word_tokenize(text)
        result = f"Sentences ({len(sentences)}):\n{sentences}\n\n"
        result += f"Words ({len(words)}):\n{words}"
        show_output("TOKENIZATION (Sentences + Words)", result)
    except LookupError as e:
        missing_resource_message(e)


def do_sentence_tokenization():
    """Splits the input text into individual sentences."""
    text = get_input_text()
    if not text:
        messagebox.showwarning("Empty Input", "Please enter some text first.")
        return
    try:
        sentences = sent_tokenize(text)
        result = "\n".join(f"{i+1}. {s}" for i, s in enumerate(sentences))
        show_output("SENTENCE TOKENIZATION", result)
    except LookupError as e:
        missing_resource_message(e)


def do_word_tokenization():
    """Splits the input text into individual words/tokens."""
    text = get_input_text()
    if not text:
        messagebox.showwarning("Empty Input", "Please enter some text first.")
        return
    try:
        words = word_tokenize(text)
        show_output("WORD TOKENIZATION", str(words))
    except LookupError as e:
        missing_resource_message(e)


def do_stopword_removal():
    """Removes common filler words (like 'the', 'is', 'a') from the text."""
    text = get_input_text()
    if not text:
        messagebox.showwarning("Empty Input", "Please enter some text first.")
        return
    try:
        words = word_tokenize(text)
        stop_words = set(stopwords.words("english"))
        filtered = [w for w in words if w.lower() not in stop_words and w.isalpha()]
        result = f"Original word count: {len(words)}\n"
        result += f"After removing stopwords: {len(filtered)}\n\n"
        result += str(filtered)
        show_output("STOPWORDS REMOVAL", result)
    except LookupError as e:
        missing_resource_message(e)


def do_stemming():
    """Reduces each word to its root/base form (e.g. 'running' -> 'run')."""
    text = get_input_text()
    if not text:
        messagebox.showwarning("Empty Input", "Please enter some text first.")
        return
    try:
        words = word_tokenize(text)
        stemmer = PorterStemmer()
        stemmed = [f"{w} -> {stemmer.stem(w)}" for w in words if w.isalpha()]
        show_output("STEMMING", "\n".join(stemmed))
    except LookupError as e:
        missing_resource_message(e)


def do_lemmatization():
    """
    Reduces each word to its dictionary base form (e.g. 'better' -> 'good',
    'studies' -> 'study'). More accurate than stemming, but slower.
    """
    text = get_input_text()
    if not text:
        messagebox.showwarning("Empty Input", "Please enter some text first.")
        return
    try:
        words = word_tokenize(text)
        lemmatizer = WordNetLemmatizer()
        lemmatized = [f"{w} -> {lemmatizer.lemmatize(w.lower())}" for w in words if w.isalpha()]
        show_output("LEMMATIZATION", "\n".join(lemmatized))
    except LookupError as e:
        missing_resource_message(e)


def do_pos_tagging():
    """Labels each word with its grammatical role (Noun, Verb, Adjective, etc.)."""
    text = get_input_text()
    if not text:
        messagebox.showwarning("Empty Input", "Please enter some text first.")
        return
    try:
        words = word_tokenize(text)
        tags = pos_tag(words)
        result = "\n".join(f"{word} -> {tag}" for word, tag in tags)
        show_output("PART OF SPEECH (POS) TAGGING", result)
    except LookupError as e:
        missing_resource_message(e)


def do_frequency_distribution():
    """Counts how many times each word appears in the text."""
    text = get_input_text()
    if not text:
        messagebox.showwarning("Empty Input", "Please enter some text first.")
        return
    try:
        words = word_tokenize(text)
        words = [w.lower() for w in words if w.isalpha()]
        freq = FreqDist(words)
        result = "\n".join(f"{word} : {count}" for word, count in freq.most_common())
        show_output("FREQUENCY DISTRIBUTION", result)
    except LookupError as e:
        missing_resource_message(e)


def clear_all():
    """Clears both the input and output boxes."""
    input_box.delete("1.0", tk.END)
    output_box.delete("1.0", tk.END)


def exit_app():
    """Closes the application."""
    root.destroy()


# ==========================================================
# GUI SETUP
# ==========================================================
root = tk.Tk()
root.title("NLP Toolkit - NLTK")
root.geometry("900x650")
root.configure(bg="#f0f4f3")

# ---------- Title Section ----------
tk.Label(
    root, text="NLP Toolkit - NLTK",
    font=("Segoe UI", 20, "bold"), bg="#f0f4f3", fg="#0f4c3a"
).pack(pady=(15, 0))

tk.Label(
    root, text="Natural Language Processing Lab",
    font=("Segoe UI", 11), bg="#f0f4f3", fg="#4a5d57"
).pack(pady=(0, 15))

# ---------- Main Container (splits into left and right) ----------
main_frame = tk.Frame(root, bg="#f0f4f3")
main_frame.pack(fill="both", expand=True, padx=20, pady=5)

# ---------- LEFT SIDE: Input box + Clear/Exit ----------
left_frame = tk.Frame(main_frame, bg="#f0f4f3")
left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

tk.Label(
    left_frame, text="Enter Text", font=("Segoe UI", 11, "bold"),
    bg="#f0f4f3", fg="#2f3e3b"
).pack(anchor="w")

input_box = scrolledtext.ScrolledText(
    left_frame, height=10, font=("Consolas", 11), bg="white", relief="flat", bd=2
)
input_box.pack(fill="both", expand=True, pady=(5, 10))

bottom_buttons = tk.Frame(left_frame, bg="#f0f4f3")
bottom_buttons.pack(fill="x")

tk.Button(
    bottom_buttons, text="Clear", command=clear_all,
    bg="#d9dedb", fg="#2f3e3b", font=("Segoe UI", 10, "bold"),
    relief="flat", padx=20, pady=8, cursor="hand2"
).pack(side="left", padx=(0, 10))

tk.Button(
    bottom_buttons, text="Exit", command=exit_app,
    bg="#b3402f", fg="white", font=("Segoe UI", 10, "bold"),
    relief="flat", padx=20, pady=8, cursor="hand2"
).pack(side="left")

# ---------- RIGHT SIDE: Operation buttons ----------
right_frame = tk.Frame(main_frame, bg="#f0f4f3", width=220)
right_frame.pack(side="right", fill="y")

tk.Label(
    right_frame, text="Operations", font=("Segoe UI", 11, "bold"),
    bg="#f0f4f3", fg="#2f3e3b"
).pack(anchor="w", pady=(0, 8))

operations = [
    ("Tokenization", do_general_tokenization),
    ("Sentence Tokenization", do_sentence_tokenization),
    ("Word Tokenization", do_word_tokenization),
    ("Stopwords Removal", do_stopword_removal),
    ("Stemming", do_stemming),
    ("Lemmatization", do_lemmatization),
    ("POS Tagging", do_pos_tagging),
    ("Frequency Distribution", do_frequency_distribution),
]

for label, command in operations:
    tk.Button(
        right_frame, text=label, command=command,
        bg="#0f4c3a", fg="white", font=("Segoe UI", 10),
        relief="flat", padx=10, pady=10, width=22, cursor="hand2",
        anchor="w"
    ).pack(pady=4)

# ---------- Output Section ----------
tk.Label(
    root, text="Output", font=("Segoe UI", 11, "bold"),
    bg="#f0f4f3", fg="#2f3e3b"
).pack(anchor="w", padx=20)

output_box = scrolledtext.ScrolledText(
    root, height=10, font=("Consolas", 10), bg="#ffffff", relief="flat", bd=2
)
output_box.pack(fill="both", expand=True, padx=20, pady=(5, 15))

# ---------- Run the App ----------
root.mainloop()