"""
FASTTEXT GENOME LAB - Subword DNA Sequencing Terminal
=======================================================
A Tkinter desktop GUI that explains FastText using a DNA / genetics lab
theme.

HOW THE THEME MAPS TO FASTTEXT:
  - A WORD               -> an Organism being sequenced
  - SUBWORDS (n-grams)   -> Gene Fragments extracted from its DNA
  - WORD VECTOR          -> its Genetic Fingerprint (radial barcode)
  - SIMILAR WORDS        -> Related Species shown on a Family Tree
  - UNKNOWN/MISSPELLED   -> a New Species (still gets a fingerprint,
                            rebuilt purely from its gene fragments)

MODEL BACKEND
  - If the real "fasttext" library (pip install fasttext) is installed,
    you can load a real .bin model, or train a small real unsupervised
    model on a bundled demo corpus with one click.
  - If it is not installed, the app falls back to an engine that still
    builds subwords using FastText's own documented rule (character
    n-grams, n = 3..6, word wrapped in "<" and ">"), plus a simple
    hashed vector, so the interface works end-to-end for demonstration.
    This fallback mode is always labeled clearly in the UI.

Run with:  python fasttext_genome_lab.py
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import math
import hashlib
import os
import tempfile

try:
    import fasttext
    FASTTEXT_AVAILABLE = True
except ImportError:
    FASTTEXT_AVAILABLE = False


# =========================================================================
# COLOR THEME - DNA / genetics lab palette
# =========================================================================
COL_BG = "#060a12"
COL_PANEL = "#0a0f1c"
COL_PANEL_EDGE = "#16233a"
COL_GLASS = "#0d1424"
COL_CANVAS_BG = "#050810"
COL_TEXT = "#dbe6ff"
COL_SUB = "#5f7396"
COL_DNA1 = "#00ffb3"
COL_DNA2 = "#00b3ff"
COL_GENE = "#ff3d9a"
COL_ALERT = "#ffce3d"
COL_TREE = "#7cffb2"

SPECIES_COLORS = ["#00ffb3", "#ff3d9a", "#00b3ff", "#ffce3d",
                  "#7cffb2", "#c084fc", "#ff8a5c", "#5ce1ff"]

FONT_TITLE = ("Segoe UI", 18, "bold")
FONT_SUBTITLE = ("Consolas", 9)
FONT_H2 = ("Segoe UI", 10, "bold")
FONT_BODY = ("Consolas", 10)
FONT_BODY_B = ("Consolas", 10, "bold")
FONT_SMALL = ("Consolas", 8)


# =========================================================================
# DEMO CORPUS - used only if training a quick real FastText model
# =========================================================================
DEMO_CORPUS_TEXT = """
the quick racing car speeds down the track past the pit lane
the driver checks engine performance before the race starts
running is a common word used in many different sentences
the runner was running fast around the running track today
similar words often share meaning and similar spelling patterns
the team studied similarity between vectors and word meaning
technology and machine learning are changing how computers understand language
the neural network learned word representations from a large corpus
misspelled words still get a vector because of subword information
character n grams help represent rare and unknown words correctly
data science students studied fasttext word embeddings this semester
artificial intelligence models process text using numerical vectors
scientists sequence genes to study organisms and species
the laboratory analyzed dna fragments from every specimen
the family tree showed how closely related the species were
"""


# =========================================================================
# FASTTEXT ENGINE WRAPPER
# =========================================================================
class FastTextEngine:
    def __init__(self):
        self.model = None
        self.mode = "NONE"
        self.vocab = []
        self._build_fallback_vocab()

    def _build_fallback_vocab(self):
        words = set()
        for line in DEMO_CORPUS_TEXT.strip().split("\n"):
            for w in line.strip().split():
                if w.isalpha():
                    words.add(w.lower())
        self.vocab = sorted(words)

    def load_model(self, path):
        if not FASTTEXT_AVAILABLE:
            raise RuntimeError("The 'fasttext' library is not installed.")
        self.model = fasttext.load_model(path)
        self.mode = "REAL"

    def train_demo_model(self):
        if not FASTTEXT_AVAILABLE:
            self.mode = "FALLBACK"
            return
        tmp_dir = tempfile.gettempdir()
        corpus_path = os.path.join(tmp_dir, "fasttext_genome_corpus.txt")
        with open(corpus_path, "w", encoding="utf-8") as f:
            f.write(DEMO_CORPUS_TEXT.strip())
        self.model = fasttext.train_unsupervised(
            corpus_path, model="skipgram", dim=50, minn=3, maxn=6,
            epoch=25, minCount=1
        )
        self.mode = "REAL"

    def use_fallback(self):
        self.mode = "FALLBACK"

    def get_subwords(self, word):
        word = word.lower()
        if self.mode == "REAL":
            subwords, _ids = self.model.get_subwords(word)
            return list(subwords)
        return self._fallback_subwords(word)

    @staticmethod
    def _fallback_subwords(word, minn=3, maxn=6):
        w = "<" + word + ">"
        grams = []
        for n in range(minn, maxn + 1):
            if n > len(w):
                break
            for i in range(len(w) - n + 1):
                grams.append(w[i:i + n])
        if w not in grams:
            grams.append(w)
        seen = set()
        ordered = []
        for g in grams:
            if g not in seen:
                seen.add(g)
                ordered.append(g)
        return ordered

    def get_vector(self, word):
        word = word.lower()
        if self.mode == "REAL":
            return list(self.model.get_word_vector(word))
        return self._fallback_vector(word)

    def _fallback_vector(self, word, dim=24):
        grams = self._fallback_subwords(word)
        vec = [0.0] * dim
        for g in grams:
            h = int(hashlib.md5(g.encode("utf-8")).hexdigest(), 16)
            idx = h % dim
            sign = 1.0 if (h // dim) % 2 == 0 else -1.0
            vec[idx] += sign * (1.0 / len(grams))
        return vec

    def in_vocab(self, word):
        word = word.lower()
        if self.mode == "REAL":
            return word in self.model.get_words()
        return word in self.vocab

    def nearest_neighbors(self, word, k=5):
        word = word.lower()
        if self.mode == "REAL":
            try:
                results = self.model.get_nearest_neighbors(word, k=k)
                return [(score, w) for score, w in results]
            except Exception:
                pass
        target = self._fallback_vector(word)
        scored = []
        for v in self.vocab:
            if v == word:
                continue
            score = self._cosine(target, self._fallback_vector(v))
            scored.append((score, v))
        scored.sort(key=lambda x: -x[0])
        return scored[:k]

    @staticmethod
    def _cosine(a, b):
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(y * y for y in b))
        if na == 0 or nb == 0:
            return 0.0
        return dot / (na * nb)


# =========================================================================
# MAIN APPLICATION
# =========================================================================
class GenomeLabApp:
    def __init__(self, root):
        self.root = root
        self.root.title("FastText Genome Lab - Subword DNA Sequencing Terminal")
        self.root.geometry("1280x820")
        self.root.configure(bg=COL_BG)
        self.root.minsize(1100, 740)

        self.engine = FastTextEngine()
        self.engine.use_fallback()

        self.current_word = None
        self.current_neighbors = []
        self.current_subwords = []
        self.current_vector = []
        self.wildcard_mode = False

        self._build_header()
        self._build_body()
        self._build_status_bar()

    # ------------------------------------------------------------------
    def _build_header(self):
        header = tk.Frame(self.root, bg=COL_PANEL, height=70,
                           highlightbackground=COL_PANEL_EDGE, highlightthickness=1)
        header.pack(side="top", fill="x")
        header.pack_propagate(False)

        left = tk.Frame(header, bg=COL_PANEL)
        left.pack(side="left", padx=20, pady=8)
        tk.Label(left, text="FASTTEXT GENOME LAB", font=FONT_TITLE,
                 bg=COL_PANEL, fg=COL_DNA1).pack(anchor="w")
        tk.Label(left, text="SUBWORD DNA SEQUENCING TERMINAL", font=FONT_SUBTITLE,
                 bg=COL_PANEL, fg=COL_SUB).pack(anchor="w")

        right = tk.Frame(header, bg=COL_PANEL)
        right.pack(side="right", padx=20)
        self.status_pill = tk.Label(right, text="SEQUENCER READY", font=FONT_SMALL,
                                     bg=COL_PANEL, fg=COL_DNA1, padx=10, pady=4,
                                     highlightbackground=COL_DNA1, highlightthickness=1)
        self.status_pill.pack()

    def _set_pill(self, text, color):
        self.status_pill.config(text=text, fg=color, highlightbackground=color)

    # ------------------------------------------------------------------
    def _build_body(self):
        body = tk.Frame(self.root, bg=COL_BG)
        body.pack(side="top", fill="both", expand=True)
        self._build_control_panel(body)

        center_wrap = tk.Frame(body, bg=COL_BG)
        center_wrap.pack(side="left", fill="both", expand=True, padx=(0, 10), pady=10)

        self._build_helix_panel(center_wrap)

        bottom_row = tk.Frame(center_wrap, bg=COL_BG)
        bottom_row.pack(side="top", fill="x", pady=(10, 0))

        self._build_gene_strip_panel(bottom_row)
        self._build_fingerprint_panel(bottom_row)

    # ------------------------------------------------------------------
    def _build_control_panel(self, parent):
        panel = tk.Frame(parent, bg=COL_PANEL, width=250,
                          highlightbackground=COL_PANEL_EDGE, highlightthickness=1)
        panel.pack(side="left", fill="y", padx=10, pady=10)
        panel.pack_propagate(False)

        tk.Label(panel, text="LAB CONSOLE", font=FONT_H2, bg=COL_PANEL,
                 fg=COL_TEXT).pack(anchor="w", padx=14, pady=(14, 2))
        tk.Label(panel, text="Enter an organism (word) to sequence its DNA",
                 font=FONT_SMALL, bg=COL_PANEL, fg=COL_SUB, wraplength=220,
                 justify="left").pack(anchor="w", padx=14, pady=(0, 10))

        self.word_entry = tk.Entry(panel, font=FONT_BODY_B, bg="#050810",
                                    fg=COL_DNA1, insertbackground=COL_DNA1,
                                    relief="flat", highlightthickness=1,
                                    highlightbackground=COL_PANEL_EDGE,
                                    highlightcolor=COL_DNA1)
        self.word_entry.insert(0, "running")
        self.word_entry.pack(fill="x", padx=14, ipady=8)
        self.word_entry.bind("<Return>", lambda e: self.analyze_word())

        self._separator(panel)
        self._make_button(panel, "SEQUENCE ORGANISM", COL_DNA2, self.analyze_word)
        self._make_button(panel, "FIND RELATED SPECIES", COL_TREE, self.find_similar)
        self._make_button(panel, "EXTRACT GENE FRAGMENTS", COL_GENE, self.show_subwords)

        self._separator(panel)
        tk.Label(panel, text="COMPARE SPECIES", font=FONT_H2, bg=COL_PANEL,
                 fg=COL_TEXT).pack(anchor="w", padx=14, pady=(6, 4))
        self.compare_entry_a = tk.Entry(panel, font=FONT_BODY, bg="#050810",
                                         fg=COL_TEXT, relief="flat",
                                         highlightthickness=1,
                                         highlightbackground=COL_PANEL_EDGE)
        self.compare_entry_a.insert(0, "running")
        self.compare_entry_a.pack(fill="x", padx=14, ipady=5, pady=2)
        self.compare_entry_b = tk.Entry(panel, font=FONT_BODY, bg="#050810",
                                         fg=COL_TEXT, relief="flat",
                                         highlightthickness=1,
                                         highlightbackground=COL_PANEL_EDGE)
        self.compare_entry_b.insert(0, "runner")
        self.compare_entry_b.pack(fill="x", padx=14, ipady=5, pady=2)
        self._make_button(panel, "RUN DNA MATCH TEST", COL_ALERT, self.compare_words)

        self._separator(panel)
        self.wildcard_var = tk.BooleanVar(value=False)
        wc = tk.Checkbutton(panel, text="Force New Species Mode",
                             variable=self.wildcard_var, font=FONT_SMALL,
                             bg=COL_PANEL, fg=COL_ALERT, selectcolor=COL_PANEL,
                             activebackground=COL_PANEL, activeforeground=COL_ALERT)
        wc.pack(anchor="w", padx=14, pady=(4, 10))
        self._make_button(panel, "RESET LAB", "#ff5c5c", self.clear_reset)

        self._separator(panel)
        tk.Label(panel, text="MODEL", font=FONT_H2, bg=COL_PANEL,
                 fg=COL_TEXT).pack(anchor="w", padx=14, pady=(6, 4))
        self._make_button(panel, "LOAD .bin MODEL", COL_SUB, self.load_model_dialog,
                           small=True)
        self._make_button(panel, "TRAIN DEMO MODEL", COL_SUB, self.train_demo_model,
                           small=True)
        self.model_status_label = tk.Label(
            panel,
            text=("Mode: FALLBACK (demo, no fasttext lib)" if not FASTTEXT_AVAILABLE
                  else "Mode: FALLBACK (click Train Demo Model)"),
            font=("Consolas", 8), bg=COL_PANEL, fg=COL_SUB, wraplength=220,
            justify="left")
        self.model_status_label.pack(anchor="w", padx=14, pady=(6, 14))

    def _separator(self, parent):
        tk.Frame(parent, bg=COL_PANEL_EDGE, height=1).pack(fill="x", padx=14, pady=10)

    def _make_button(self, parent, text, color, command, small=False):
        btn = tk.Button(parent, text=text, command=command, bg=COL_GLASS, fg=color,
                         activebackground=color, activeforeground=COL_BG,
                         relief="flat", font=FONT_SMALL if small else FONT_BODY_B,
                         cursor="hand2", bd=0,
                         highlightbackground=color, highlightthickness=1)
        btn.pack(fill="x", padx=14, pady=4, ipady=6 if not small else 3)
        return btn

    # ------------------------------------------------------------------
    def _build_helix_panel(self, parent):
        panel = tk.Frame(parent, bg=COL_PANEL,
                          highlightbackground=COL_PANEL_EDGE, highlightthickness=1)
        panel.pack(side="top", fill="both", expand=True)

        title_row = tk.Frame(panel, bg=COL_PANEL)
        title_row.pack(fill="x", padx=14, pady=(10, 0))
        tk.Label(title_row, text="DNA HELIX & FAMILY TREE", font=FONT_H2, bg=COL_PANEL,
                 fg=COL_TEXT).pack(side="left")
        self.lap_label = tk.Label(title_row, text="NO SEQUENCE LOADED",
                                   font=FONT_SMALL, bg=COL_PANEL, fg=COL_SUB)
        self.lap_label.pack(side="right")

        self.helix_canvas = tk.Canvas(panel, bg=COL_CANVAS_BG, highlightthickness=0,
                                       height=380)
        self.helix_canvas.pack(fill="both", expand=True, padx=14, pady=10)
        self.helix_canvas.bind("<Configure>", lambda e: self._draw_helix())

    def _draw_helix(self):
        c = self.helix_canvas
        c.delete("all")
        w = c.winfo_width() or 900
        h = c.winfo_height() or 380

        if not self.current_word:
            c.create_text(w / 2, h / 2, text="No sequence loaded — enter an organism to begin",
                          fill=COL_SUB, font=FONT_BODY)
            return

        helix_w = w * 0.5
        amp = min(40, helix_w * 0.15)
        mid_x = helix_w / 2 + 30
        turns = 3
        steps = 80
        top, bottom = 25, h - 25

        pts_a, pts_b = [], []
        for i in range(steps + 1):
            frac = i / steps
            y = top + (bottom - top) * frac
            phase = frac * turns * 2 * math.pi
            xa = mid_x + amp * math.sin(phase)
            xb = mid_x - amp * math.sin(phase)
            pts_a.extend([xa, y])
            pts_b.extend([xb, y])
        c.create_line(*pts_a, fill=COL_DNA1, width=3, smooth=True)
        c.create_line(*pts_b, fill=COL_DNA2, width=3, smooth=True)

        n = min(len(self.current_subwords), 9)
        for i in range(n):
            frac = (i + 0.5) / n
            y = top + (bottom - top) * frac
            phase = frac * turns * 2 * math.pi
            xa = mid_x + amp * math.sin(phase)
            xb = mid_x - amp * math.sin(phase)
            color = SPECIES_COLORS[i % len(SPECIES_COLORS)]
            c.create_line(xa, y, xb, y, fill=color, width=2)
            c.create_oval(xa - 4, y - 4, xa + 4, y + 4, fill=color, outline="")
            c.create_oval(xb - 4, y - 4, xb + 4, y + 4, fill=color, outline="")
            c.create_text(xb - 12, y, text=self.current_subwords[i], fill=color,
                          font=("Consolas", 8, "bold"), anchor="e")

        name_tag = ("\u2716 NEW SPECIES: " if self.wildcard_mode else "") + self.current_word.upper()
        c.create_text(mid_x, 12, text=name_tag, fill=COL_TEXT, font=("Segoe UI", 11, "bold"))

        if self.wildcard_mode:
            c.create_text(mid_x, h - 8, text="\u26A0 UNKNOWN DNA - RECONSTRUCTED FROM FRAGMENTS",
                          fill=COL_ALERT, font=("Consolas", 9, "bold"))

        # family tree
        if self.current_neighbors:
            root_x, root_y = helix_w + 90, h / 2
            c.create_oval(root_x - 7, root_y - 7, root_x + 7, root_y + 7, fill=COL_TEXT, outline="")
            c.create_text(root_x, root_y - 16, text=self.current_word, fill=COL_TEXT,
                          font=("Consolas", 9, "bold"))

            n2 = len(self.current_neighbors)
            spread_top, spread_bottom = 25, h - 25
            branch_x = w - 60
            for i, (score, word) in enumerate(self.current_neighbors):
                branch_y = spread_top + (spread_bottom - spread_top) * (i / max(n2 - 1, 1))
                color = SPECIES_COLORS[(i + 2) % len(SPECIES_COLORS)]
                mid_ctrl_x = root_x + (branch_x - root_x) * 0.5
                c.create_line(root_x, root_y, mid_ctrl_x, branch_y, branch_x, branch_y,
                              fill=color, width=max(1, int(1 + score * 3)), smooth=True)
                c.create_oval(branch_x - 5, branch_y - 5, branch_x + 5, branch_y + 5,
                              fill=color, outline="")
                c.create_text(branch_x + 10, branch_y, text=f"{word} ({score:.2f})",
                              fill=color, font=("Consolas", 8, "bold"), anchor="w")

    # ------------------------------------------------------------------
    def _build_gene_strip_panel(self, parent):
        panel = tk.Frame(parent, bg=COL_PANEL,
                          highlightbackground=COL_PANEL_EDGE, highlightthickness=1)
        panel.pack(side="left", fill="both", expand=True, padx=(0, 5))

        tk.Label(panel, text="GENE SEQUENCER (FRAGMENTS)", font=FONT_H2,
                 bg=COL_PANEL, fg=COL_TEXT).pack(anchor="w", padx=12, pady=(10, 6))

        self.gene_canvas = tk.Canvas(panel, bg=COL_CANVAS_BG, highlightthickness=0,
                                      height=150)
        self.gene_canvas.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.gene_canvas.bind("<Configure>", lambda e: self._draw_gene_strip())

    def _draw_gene_strip(self):
        c = self.gene_canvas
        c.delete("all")
        w = c.winfo_width() or 500
        h = c.winfo_height() or 150

        if not self.current_subwords:
            c.create_text(20, 20, anchor="nw", text="No fragments extracted yet.",
                          fill=COL_SUB, font=FONT_SMALL)
            return

        n = len(self.current_subwords)
        lane_w = w / n
        mid_y = h / 2
        for i, sw in enumerate(self.current_subwords):
            color = SPECIES_COLORS[i % len(SPECIES_COLORS)]
            band_h = 10 + len(sw) * 4
            x0 = i * lane_w + lane_w * 0.15
            bw = lane_w * 0.7
            y0 = mid_y - band_h / 2 - 10
            c.create_rectangle(x0, y0, x0 + bw, y0 + band_h, fill=color, outline="")
            c.create_text(x0 + bw / 2, mid_y + 40, text=sw, fill=color,
                          font=("Consolas", 8, "bold"))

    # ------------------------------------------------------------------
    def _build_fingerprint_panel(self, parent):
        panel = tk.Frame(parent, bg=COL_PANEL, width=320,
                          highlightbackground=COL_PANEL_EDGE, highlightthickness=1)
        panel.pack(side="left", fill="both", padx=(5, 0))
        panel.pack_propagate(False)

        tk.Label(panel, text="GENETIC FINGERPRINT", font=FONT_H2, bg=COL_PANEL,
                 fg=COL_TEXT).pack(anchor="w", padx=12, pady=(10, 6))

        self.fp_stats = tk.Label(panel, text="No organism sequenced yet.", font=FONT_SMALL,
                                  bg=COL_PANEL, fg=COL_TEXT, justify="left", anchor="w")
        self.fp_stats.pack(fill="x", padx=12)

        self.fp_canvas = tk.Canvas(panel, bg=COL_CANVAS_BG, highlightthickness=0,
                                    height=140)
        self.fp_canvas.pack(fill="both", expand=True, padx=12, pady=(8, 12))
        self.fp_canvas.bind("<Configure>", lambda e: self._draw_fingerprint())

    def _draw_fingerprint(self):
        c = self.fp_canvas
        c.delete("all")
        if not self.current_vector:
            self.fp_stats.config(text="No organism sequenced yet.")
            return

        v = self.current_vector
        norm = math.sqrt(sum(x * x for x in v))
        vmax, vmin = max(v), min(v)
        self.fp_stats.config(text=(
            f"DIMENSIONS:  {len(v)}\n"
            f"DNA STRENGTH (norm): {norm:.3f}\n"
            f"PEAK MARKER: {vmax:.3f}\n"
            f"LOW MARKER:  {vmin:.3f}"))

        w = c.winfo_width() or 260
        h = c.winfo_height() or 140
        cx, cy = w / 2, h / 2
        r_base = min(w, h) * 0.22
        r_max = min(w, h) * 0.45
        span = max(abs(vmax), abs(vmin), 1e-6)
        n = len(v)

        c.create_oval(cx - r_base, cy - r_base, cx + r_base, cy + r_base,
                      outline=COL_PANEL_EDGE, width=1)

        for i in range(n):
            angle = (2 * math.pi * i) / n - math.pi / 2
            val = v[i]
            length = (abs(val) / span) * (r_max - r_base)
            r1, r2 = r_base, r_base + length
            x1, y1 = cx + r1 * math.cos(angle), cy + r1 * math.sin(angle)
            x2, y2 = cx + r2 * math.cos(angle), cy + r2 * math.sin(angle)
            color = COL_DNA1 if val >= 0 else COL_GENE
            c.create_line(x1, y1, x2, y2, fill=color, width=2, capstyle="round")

        c.create_oval(cx - 3, cy - 3, cx + 3, cy + 3, fill=COL_TEXT, outline="")

    # ------------------------------------------------------------------
    def _build_status_bar(self):
        bar = tk.Frame(self.root, bg=COL_PANEL, height=26,
                        highlightbackground=COL_PANEL_EDGE, highlightthickness=1)
        bar.pack(side="bottom", fill="x")
        self.status_var = tk.StringVar(value="Ready. Type a word and click SEQUENCE ORGANISM.")
        tk.Label(bar, textvariable=self.status_var, font=FONT_SMALL, bg=COL_PANEL,
                 fg=COL_SUB, anchor="w").pack(side="left", padx=12)

    def _set_status(self, text):
        self.status_var.set(text)

    # ------------------------------------------------------------------
    # ACTIONS
    # ------------------------------------------------------------------
    def _get_word(self):
        word = self.word_entry.get().strip()
        if not word:
            messagebox.showinfo("FastText Genome Lab", "Type a word first.")
            return None
        return word

    def _render_all(self):
        self._draw_helix()
        self._draw_gene_strip()
        self._draw_fingerprint()

    def analyze_word(self):
        word = self._get_word()
        if not word:
            return
        self.current_word = word
        self.wildcard_mode = self.wildcard_var.get() or not self.engine.in_vocab(word)
        self.current_subwords = self.engine.get_subwords(word)
        self.current_vector = self.engine.get_vector(word)
        self.current_neighbors = self.engine.nearest_neighbors(word, k=5)
        self._render_all()

        self.lap_label.config(text=f"SEQUENCED: {word.upper()} - {len(self.current_neighbors)} related species")
        if self.wildcard_mode:
            self._set_pill("NEW SPECIES DETECTED", COL_ALERT)
            self._set_status(f"New species '{word}' detected. DNA reconstructed from "
                              f"{len(self.current_subwords)} gene fragments.")
        else:
            self._set_pill("SEQUENCE COMPLETE", COL_DNA1)
            self._set_status(f"Sequenced '{word}'. {len(self.current_subwords)} gene "
                              f"fragments extracted and profiled.")

    def find_similar(self):
        word = self._get_word()
        if not word:
            return
        self.current_word = word
        self.wildcard_mode = self.wildcard_var.get() or not self.engine.in_vocab(word)
        self.current_neighbors = self.engine.nearest_neighbors(word, k=6)
        self._draw_helix()
        self.lap_label.config(text=f"FAMILY TREE FOR: {word.upper()}")
        self._set_status(f"Found {len(self.current_neighbors)} related species based on DNA similarity.")

    def show_subwords(self):
        word = self._get_word()
        if not word:
            return
        self.current_word = word
        self.current_subwords = self.engine.get_subwords(word)
        self.current_vector = self.engine.get_vector(word)
        self._draw_gene_strip()
        self._draw_fingerprint()
        self._set_status(f"Extracted {len(self.current_subwords)} gene fragments from '{word}'.")

    def compare_words(self):
        a = self.compare_entry_a.get().strip()
        b = self.compare_entry_b.get().strip()
        if not a or not b:
            messagebox.showinfo("FastText Genome Lab", "Enter both species to compare.")
            return
        va = self.engine.get_vector(a)
        vb = self.engine.get_vector(b)
        score = self.engine._cosine(va, vb)

        self.current_word = a
        self.current_neighbors = [(score, b)]
        self.current_subwords = self.engine.get_subwords(a)
        self.current_vector = va
        self.wildcard_mode = False
        self._render_all()

        self.lap_label.config(text=f"DNA MATCH: {a.upper()} vs {b.upper()} = {score:.3f}")
        self._set_status(f"DNA match score between '{a}' and '{b}': {score:.3f} "
                          f"(1.0 = same species, 0 = unrelated).")

    def clear_reset(self):
        self.word_entry.delete(0, "end")
        self.compare_entry_a.delete(0, "end")
        self.compare_entry_b.delete(0, "end")
        self.current_word = None
        self.current_neighbors = []
        self.current_subwords = []
        self.current_vector = []
        self.wildcard_var.set(False)
        self.wildcard_mode = False
        self._render_all()
        self.lap_label.config(text="NO SEQUENCE LOADED")
        self._set_pill("SEQUENCER READY", COL_DNA1)
        self._set_status("Lab reset. Ready for a new organism.")

    def load_model_dialog(self):
        if not FASTTEXT_AVAILABLE:
            messagebox.showwarning(
                "FastText Genome Lab",
                "The 'fasttext' Python library is not installed.\n"
                "Run: pip install fasttext\nStaying in FALLBACK demo mode.")
            return
        path = filedialog.askopenfilename(
            title="Select a FastText .bin model",
            filetypes=[("FastText model", "*.bin"), ("All files", "*.*")])
        if not path:
            return
        try:
            self._set_status("Loading model...")
            self.root.update_idletasks()
            self.engine.load_model(path)
            self.model_status_label.config(text=f"Mode: REAL MODEL\n{os.path.basename(path)}")
            self._set_status("Real FastText model loaded successfully.")
        except Exception as e:
            messagebox.showerror("FastText Genome Lab", f"Could not load model:\n{e}")
            self._set_status("Model load failed. Staying in previous mode.")

    def train_demo_model(self):
        if not FASTTEXT_AVAILABLE:
            messagebox.showwarning(
                "FastText Genome Lab",
                "The 'fasttext' Python library is not installed.\n"
                "Run: pip install fasttext\nStaying in FALLBACK demo mode.")
            return
        self._set_status("Training a small real FastText model on the demo corpus...")
        self.root.update_idletasks()
        try:
            self.engine.train_demo_model()
            self.model_status_label.config(text="Mode: REAL MODEL (trained on demo corpus)")
            self._set_status("Demo model trained. All results now come from real FastText.")
        except Exception as e:
            messagebox.showerror("FastText Genome Lab", f"Training failed:\n{e}")


# =========================================================================
# ENTRY POINT
# =========================================================================
def main():
    root = tk.Tk()
    app = GenomeLabApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
    