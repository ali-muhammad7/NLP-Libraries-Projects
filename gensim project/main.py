"""
Gensim Star Chart
A Tkinter GUI for exploring word meaning using Gensim.
Styled as a night-sky star chart: words become stars (size = how
often the word appears), star color = topic group (from LDA topic
modeling), and clicking a star reveals its "nearest neighbor" words
(from a Word2Vec model trained on the input text).
"""

import math
import random
import tkinter as tk
from tkinter import messagebox

try:
    from gensim.models import Word2Vec, LdaModel
    from gensim.corpora import Dictionary
except ImportError:
    Word2Vec = None
    LdaModel = None
    Dictionary = None


# ==========================================================
# COLORS - night sky theme
# ==========================================================
SKY = "#050814"
SKY_DEEP = "#02040a"
PANEL = "#0b1024"
LINE_COLOR = "#1c2547"
GOLD = "#f4d35e"
SILVER = "#cdd6f4"
MUTED = "#6b7398"
SUN = "#ffb347"

TOPIC_COLORS = ["#f4d35e", "#7ec4cf", "#e88fb0"]  # gold, cyan, pink

STOPWORDS = {
    "the", "a", "an", "is", "are", "and", "or", "to", "of", "in", "for",
    "on", "with", "this", "that", "it", "its", "as", "be", "by", "at",
    "was", "were", "has", "have", "had", "but", "i", "you", "we"
}


def gensim_missing_warning():
    messagebox.showerror(
        "Gensim Not Installed",
        "The gensim library is not installed on this computer.\n\n"
        "Please open your terminal and run:\n\n"
        "pip install gensim\n\n"
        "Then restart this program."
    )


# ==========================================================
# TEXT PROCESSING HELPERS
# ==========================================================
def get_input_text():
    return input_box.get("1.0", tk.END).strip()


def tokenize_sentences(text):
    """
    Splits text into sentences, then each sentence into clean lowercase
    word tokens (punctuation removed, stopwords removed).
    Returns a list of sentences, each a list of words.
    """
    raw_sentences = [s.strip() for s in
                      __import__("re").split(r"(?<=[.!?])\s+", text) if s.strip()]
    tokenized = []
    for sent in raw_sentences:
        cleaned = __import__("re").sub(r"[^a-zA-Z\s]", " ", sent).lower()
        words = [w for w in cleaned.split() if w and w not in STOPWORDS]
        tokenized.append(words)
    return raw_sentences, tokenized


def simple_hash(word):
    """A stable hash so the same word always lands in the same spot on the chart."""
    h = 0
    for ch in word:
        h = (h * 31 + ord(ch)) % 1000003
    return h


# ==========================================================
# GENSIM-POWERED ANALYSIS
# ==========================================================
def build_topic_map(tokenized_sentences, num_topics=3):
    """
    Uses Gensim's LDA (Latent Dirichlet Allocation) to group words into
    topics. For each word, we check its probability under every topic
    and assign it to whichever topic scores it highest. Returns a
    dictionary mapping each word to a topic number (0,1,2).
    """
    dictionary = Dictionary(tokenized_sentences)
    corpus = [dictionary.doc2bow(sent) for sent in tokenized_sentences]

    lda = LdaModel(corpus, num_topics=num_topics, id2word=dictionary,
                    passes=25, random_state=42)

    topic_word_matrix = lda.get_topics()  # shape: (num_topics, vocab_size)

    word_topic = {}
    for word_id in range(len(dictionary)):
        word = dictionary[word_id]
        best_topic = max(range(num_topics), key=lambda t: topic_word_matrix[t][word_id])
        word_topic[word] = best_topic
    return word_topic


def build_word2vec(tokenized_sentences):
    """Trains a small Word2Vec model directly on the input text."""
    model = Word2Vec(
        sentences=tokenized_sentences, vector_size=50,
        window=4, min_count=1, sg=1, epochs=200
    )
    return model


def sentence_vector(model, words):
    """Averages the word vectors of a sentence to get one vector for it."""
    vectors = [model.wv[w] for w in words if w in model.wv]
    if not vectors:
        return None
    return [sum(v[i] for v in vectors) / len(vectors) for i in range(len(vectors[0]))]


def cosine_similarity(v1, v2):
    if v1 is None or v2 is None:
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    mag1 = math.sqrt(sum(a * a for a in v1))
    mag2 = math.sqrt(sum(b * b for b in v2))
    if mag1 == 0 or mag2 == 0:
        return 0.0
    return dot / (mag1 * mag2)


# ==========================================================
# DRAWING HELPERS (plain Tkinter Canvas)
# ==========================================================
def clear_canvas(canvas):
    canvas.delete("all")


def draw_background_stars(canvas, width, height, count=40):
    for _ in range(count):
        x, y = random.randint(0, width), random.randint(0, height)
        r = random.uniform(0.4, 1.2)
        canvas.create_oval(x - r, y - r, x + r, y + r, fill="#3a4270", outline="")


# ==========================================================
# MAIN ACTION: CHART THE SKY
# ==========================================================
word_positions = {}
word_topics = {}
star_ids = {}
word2vec_model = None


def chart_the_sky():
    global word_positions, word_topics, star_ids, word2vec_model

    if Word2Vec is None:
        gensim_missing_warning()
        return

    text = get_input_text()
    if not text:
        messagebox.showwarning("Empty Log", "Please enter some text first.")
        return

    raw_sentences, tokenized = tokenize_sentences(text)
    all_words = [w for sent in tokenized for w in sent]

    if not all_words:
        messagebox.showwarning("No Words Found", "Couldn't find any usable words in that text.")
        return

    # ---- Word frequency ----
    freq = {}
    for w in all_words:
        freq[w] = freq.get(w, 0) + 1
    unique_words = sorted(set(all_words), key=lambda w: -freq[w])[:14]

    # ---- Topic grouping (LDA) ----
    try:
        num_topics = min(3, max(1, len(tokenized)))
        word_topics = build_topic_map(tokenized, num_topics=num_topics)
    except Exception as e:
        messagebox.showerror("Topic Modeling Error", f"Could not build topics:\n{e}")
        word_topics = {}

    # ---- Word2Vec model (for neighbor lookups) ----
    try:
        word2vec_model = build_word2vec(tokenized)
    except Exception as e:
        messagebox.showerror("Word2Vec Error", f"Could not train Word2Vec:\n{e}")
        word2vec_model = None

    # ---- Draw the sky ----
    clear_canvas(sky_canvas)
    width, height = 900, 360
    draw_background_stars(sky_canvas, width, height)

    # Give each topic its own region of the sky (left / center / right)
    # and space words evenly within that region, so stars never pile up
    # on top of each other no matter how much room is available.
    region_bounds = [(40, 230), (330, 520), (610, 740)]  # x-range per topic (leaves room for labels)
    top_margin, bottom_margin = 45, height - 35

    words_by_topic = {0: [], 1: [], 2: []}
    for w in unique_words:
        words_by_topic[word_topics.get(w, 0) % 3].append(w)

    word_positions = {}
    for topic_id, group in words_by_topic.items():
        group.sort(key=lambda w: -freq[w])
        x_start, x_end = region_bounds[topic_id]
        count = len(group)
        for i, w in enumerate(group):
            y = top_margin if count == 1 else top_margin + i * (bottom_margin - top_margin) / (count - 1)
            x = x_start + ((i % 2) * (x_end - x_start))  # zig-zag left/right within region
            word_positions[w] = (x, y)

    # constellation lines: each topic group connects to its own "hub" word
    # (its most frequent word) instead of chaining every word together —
    # this looks like a real constellation instead of a tangled web.
    for topic_id in range(3):
        group = [w for w in unique_words if word_topics.get(w, 0) == topic_id]
        if len(group) < 2:
            continue
        hub = max(group, key=lambda w: freq[w])
        hx, hy = word_positions[hub]
        for w in group:
            if w == hub:
                continue
            x2, y2 = word_positions[w]
            sky_canvas.create_line(hx, hy, x2, y2, fill=TOPIC_COLORS[topic_id], width=1, dash=(2, 3))

    star_ids = {}
    for w in unique_words:
        x, y = word_positions[w]
        size = 5 + min(freq[w], 6) * 2.4
        color = TOPIC_COLORS[word_topics.get(w, 0) % 3]

        star = sky_canvas.create_oval(x - size, y - size, x + size, y + size, fill=color, outline="")
        sky_canvas.create_text(x + size + 5, y, text=w, fill=SILVER, font=("Consolas", 11, "bold"), anchor="w")
        sky_canvas.tag_bind(star, "<Button-1>", lambda e, word=w: show_neighbors(word))
        star_ids[w] = star

    neighbor_label.config(text="Click any star above to see its closest words in meaning.")
    draw_orbits(raw_sentences, tokenized)


def show_neighbors(word):
    if word2vec_model is None:
        return

    clear_lines()

    try:
        similar = word2vec_model.wv.most_similar(word, topn=4)
    except KeyError:
        similar = []

    x1, y1 = word_positions[word]
    for neighbor_word, _score in similar:
        if neighbor_word in word_positions:
            x2, y2 = word_positions[neighbor_word]
            line = sky_canvas.create_line(x1, y1, x2, y2, fill=GOLD, width=1.5, dash=(3, 3), tags="neighbor_line")

    if similar:
        text = f"'{word}' is closest to:\n" + "\n".join(f"→ {w} ({s:.2f})" for w, s in similar)
    else:
        text = f"No close neighbors found for '{word}' in this text."
    neighbor_label.config(text=text)


def clear_lines():
    sky_canvas.delete("neighbor_line")


def draw_orbits(raw_sentences, tokenized):
    clear_canvas(orbit_canvas)
    sun_x, sun_y = 34, 80

    orbit_canvas.create_oval(sun_x - 10, sun_y - 10, sun_x + 10, sun_y + 10, fill=SUN, outline="")
    orbit_canvas.create_text(sun_x, sun_y + 22, text="S1", fill=SILVER, font=("Consolas", 9, "bold"))

    if len(tokenized) <= 1 or word2vec_model is None:
        return

    base_vec = sentence_vector(word2vec_model, tokenized[0])
    others = tokenized[1:]
    count = len(others)

    for i, words in enumerate(others):
        vec = sentence_vector(word2vec_model, words)
        similarity = max(0.0, min(1.0, cosine_similarity(base_vec, vec)))

        # closer to the sun (left) = more similar; farther right = less similar
        distance = 60 + (1 - similarity) * 260
        px = sun_x + distance
        # spread multiple planets vertically so they don't overlap
        py = 40 + (i % 3) * 40

        # faint connecting line from sun to planet
        orbit_canvas.create_line(sun_x, sun_y, px, py, fill=LINE_COLOR, width=1)

        orbit_canvas.create_oval(px - 7, py - 7, px + 7, py + 7, fill="#7ec4cf", outline="")
        orbit_canvas.create_text(px, py - 14, text=f"S{i + 2}", fill=SILVER, font=("Consolas", 8, "bold"))
        orbit_canvas.create_text(px, py + 14, text=f"{similarity:.2f}", fill=MUTED, font=("Consolas", 8))


def clear_all():
    input_box.delete("1.0", tk.END)
    clear_canvas(sky_canvas)
    clear_canvas(orbit_canvas)
    neighbor_label.config(text="Click any star above to see its closest words in meaning.")


def exit_app():
    root.destroy()


# ==========================================================
# GUI SETUP
# ==========================================================
root = tk.Tk()
root.title("Gensim Star Chart")
root.geometry("1040x780")
root.configure(bg=SKY)

chart = tk.Frame(root, bg=PANEL, padx=26, pady=22, highlightbackground=LINE_COLOR, highlightthickness=1)
chart.pack(fill="both", expand=True, padx=18, pady=18)

# ---------- Header ----------
header = tk.Frame(chart, bg=PANEL)
header.pack(fill="x")

tk.Label(
    header, text="Gensim Star Chart", font=("Georgia", 22),
    bg=PANEL, fg=GOLD
).pack(side="left")

tk.Label(
    header, text="PLATE NO. VII  |  NLP OBSERVATORY . UNIT 07", font=("Consolas", 9),
    bg=PANEL, fg=MUTED
).pack(side="right")

tk.Label(
    chart, text="SEMANTIC CONSTELLATION EXPLORER", font=("Consolas", 9),
    bg=PANEL, fg=MUTED
).pack(anchor="w", pady=(0, 14))

tk.Frame(chart, bg=LINE_COLOR, height=1).pack(fill="x", pady=(0, 16))

# ---------- Input row ----------
input_row = tk.Frame(chart, bg=PANEL)
input_row.pack(fill="x", pady=(0, 16))

input_col = tk.Frame(input_row, bg=PANEL)
input_col.pack(side="left", fill="x", expand=True)

tk.Label(
    input_col, text="OBSERVATION LOG - ENTER TEXT", font=("Consolas", 9, "bold"),
    bg=PANEL, fg=GOLD
).pack(anchor="w")

input_box = tk.Text(
    input_col, height=3, font=("Consolas", 11), bg=SKY_DEEP, fg=SILVER,
    insertbackground=GOLD, relief="flat", padx=10, pady=8
)
input_box.pack(fill="x", pady=(4, 0))
input_box.insert(tk.END, "Dogs are loyal animals. Cats are independent animals. "
                          "Computers process data quickly. AI helps computers learn from data.")

tk.Button(
    input_row, text="\u2726 Chart the Sky", command=chart_the_sky,
    bg=GOLD, fg="#241a04", font=("Georgia", 11, "bold"),
    relief="flat", padx=16, pady=16, cursor="hand2"
).pack(side="right", padx=(14, 0), anchor="s")

# ---------- Sky canvas ----------
sky_canvas = tk.Canvas(chart, width=900, height=360, bg=SKY_DEEP, highlightthickness=1,
                         highlightbackground=LINE_COLOR)
sky_canvas.pack(pady=(0, 10))

# ---------- Legend ----------
legend = tk.Frame(chart, bg=PANEL)
legend.pack(fill="x", pady=(0, 14))

for text, color in [("Topic 1", TOPIC_COLORS[0]), ("Topic 2", TOPIC_COLORS[1]), ("Topic 3", TOPIC_COLORS[2])]:
    dot = tk.Canvas(legend, width=10, height=10, bg=PANEL, highlightthickness=0)
    dot.pack(side="left", padx=(0, 4))
    dot.create_oval(1, 1, 9, 9, fill=color, outline="")
    tk.Label(legend, text=text, bg=PANEL, fg=MUTED, font=("Consolas", 9)).pack(side="left", padx=(0, 16))

tk.Label(
    legend, text="Star size = word frequency  |  Click a star for nearest neighbors",
    bg=PANEL, fg=MUTED, font=("Consolas", 9)
).pack(side="left")

# ---------- Lower panels ----------
lower = tk.Frame(chart, bg=PANEL)
lower.pack(fill="x", pady=(0, 10))

neighbor_box = tk.Frame(lower, bg="#0b1024", padx=14, pady=12, highlightbackground=LINE_COLOR, highlightthickness=1)
neighbor_box.pack(side="left", fill="both", expand=True, padx=(0, 8))

tk.Label(neighbor_box, text="NEAREST NEIGHBORS", font=("Consolas", 9, "bold"),
          bg="#0b1024", fg=GOLD).pack(anchor="w", pady=(0, 8))

neighbor_label = tk.Label(
    neighbor_box, text="Click any star above to see its closest words in meaning.",
    bg="#0b1024", fg=SILVER, font=("Consolas", 10), justify="left", anchor="w"
)
neighbor_label.pack(anchor="w", fill="both")

orbit_box = tk.Frame(lower, bg="#0b1024", padx=14, pady=12, highlightbackground=LINE_COLOR, highlightthickness=1)
orbit_box.pack(side="left", fill="both", expand=True, padx=(8, 0))

tk.Label(orbit_box, text="SENTENCE ORBITS (SIMILARITY TO S1)", font=("Consolas", 9, "bold"),
          bg="#0b1024", fg=GOLD).pack(anchor="w", pady=(0, 8))

orbit_canvas = tk.Canvas(orbit_box, width=380, height=160, bg="#0b1024", highlightthickness=0)
orbit_canvas.pack()

# ---------- Bottom buttons ----------
bottom_row = tk.Frame(chart, bg=PANEL)
bottom_row.pack(fill="x")

tk.Button(
    bottom_row, text="Clear", command=clear_all,
    bg=LINE_COLOR, fg=SILVER, font=("Consolas", 9, "bold"),
    relief="flat", padx=18, pady=8, cursor="hand2"
).pack(side="left")

tk.Button(
    bottom_row, text="Exit", command=exit_app,
    bg="#7a2c22", fg="white", font=("Consolas", 9, "bold"),
    relief="flat", padx=18, pady=8, cursor="hand2"
).pack(side="left", padx=(10, 0))

# ---------- Run once with the default example text ----------
root.after(300, chart_the_sky)

root.mainloop()