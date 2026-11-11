import tkinter as tk
from tkinter import font as tkfont
import random
import math

# ===================== THEME =====================
BG        = "#0a0e14"
PANEL     = "#10151f"
PANEL2    = "#141b26"
BORDER    = "#232d3a"
TEXT      = "#e6edf3"
MUTED     = "#5f6b7a"
CYAN      = "#39c9e8"
CYAN_DIM  = "#1b5a68"
VIOLET    = "#9b8cf2"
AMBER     = "#e0a640"
GREEN     = "#35d68a"
RED       = "#e0566a"

F_MONO   = ("Consolas", 10)
F_MONO_B = ("Consolas", 10, "bold")
F_TITLE  = ("Consolas", 22, "bold")
F_SMALL  = ("Consolas", 8)
F_LABEL  = ("Consolas", 9, "bold")

LABEL_COLORS = {
    "PERSON": CYAN,
    "LOCATION": VIOLET,
    "ORG": AMBER,
    "TIME": GREEN,
    "O": MUTED,
}

# ===================== DEMO NLP ENGINE (mock, per spec) =====================
DEMO_WORDS = {
    "elon":       ("PROPN", "PERSON", 98.2),
    "visited":    ("VERB",  "O",      96.4),
    "karachi":    ("PROPN", "LOCATION", 94.7),
    "yesterday":  ("NOUN",  "TIME",   96.8),
    "ali":        ("PROPN", "PERSON", 97.5),
    "hyderabad":  ("PROPN", "LOCATION", 95.1),
    "university": ("NOUN",  "ORG",    93.4),
    "sarah":      ("PROPN", "PERSON", 96.9),
    "google":     ("PROPN", "ORG",    97.8),
    "california": ("PROPN", "LOCATION", 95.6),
    "today":      ("NOUN",  "TIME",   95.9),
    "tomorrow":   ("NOUN",  "TIME",   95.2),
     "raheel":     ("PROPN", "PERSON", 98.6),
    "sir":        ("NOUN",  "O",      92.3),
}
TIME_WORDS = {"today", "tomorrow", "yesterday", "now", "soon", "tonight"}


def analyze_sentence(sentence):
    clean = sentence.strip().rstrip(".?!")
    words = clean.split()
    tokens = []
    for w in words:
        lw = w.lower()
        if lw in DEMO_WORDS:
            pos, label, conf = DEMO_WORDS[lw]
        else:
            seed = sum(ord(c) for c in lw)
            if lw in TIME_WORDS:
                pos, label = "NOUN", "TIME"
            elif w[:1].isupper():
                pos = "PROPN"
                label = ["PERSON", "LOCATION", "ORG"][seed % 3]
            elif lw.endswith("ed") or lw.endswith("ing") or lw.endswith("s") and len(lw) > 4:
                pos, label = "VERB", "O"
            else:
                pos, label = "NOUN", "O"
            conf = round(85 + (seed % 9) + random.random(), 1)
        lemma = lw[:-2] if pos == "VERB" and lw.endswith("ed") else lw
        tokens.append({"text": w, "pos": pos, "lemma": lemma, "label": label, "conf": conf})
    return tokens


# ===================== MAIN APP =====================
class FlairSignalCenter(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("FLAIR — NLP SIGNAL COMMAND CENTER")
        self.geometry("1180x830")
        self.configure(bg=BG)

        self.tokens = []
        self.selected_idx = None
        self.node_boxes = {}
        self.wave_phase = 0
        self.wave_state = "idle"   # idle / scanning / locked
        self.wave_job = None

        self._build_header()
        self._build_input()
        self._build_main_area()
        self._build_bottom_area()
        self._build_status_strip()

        self._animate_waveform()

    # ---------- generic panel factory ----------
    def _panel(self, parent, **pack_kw):
        p = tk.Frame(parent, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        p.pack(**pack_kw)
        return p

    def _section_title(self, parent, text, color=CYAN):
        tk.Label(parent, text=text, font=F_LABEL, bg=PANEL, fg=color).pack(
            anchor="w", padx=14, pady=(10, 6))

    # ================= HEADER =================
    def _build_header(self):
        header = tk.Frame(self, bg=BG)
        header.pack(fill="x", padx=18, pady=(16, 8))

        left = tk.Frame(header, bg=BG)
        left.pack(side="left")
        tk.Label(left, text="FLAIR", font=F_TITLE, bg=BG, fg=TEXT).pack(anchor="w")
        tk.Label(left, text="NLP SIGNAL COMMAND CENTER", font=("Consolas", 10, "bold"),
                 bg=BG, fg=CYAN).pack(anchor="w")
        tk.Label(left, text="CONTEXTUAL LANGUAGE ANALYSIS SYSTEM", font=F_SMALL,
                 bg=BG, fg=MUTED).pack(anchor="w", pady=(2, 0))

        right = tk.Frame(header, bg=BG)
        right.pack(side="right")

        row = tk.Frame(right, bg=BG)
        row.pack(anchor="e")
        tk.Label(row, text="●", fg=GREEN, bg=BG, font=F_SMALL).pack(side="left")
        tk.Label(row, text=" SYSTEM ONLINE", fg=TEXT, bg=BG, font=F_SMALL).pack(side="left")

        self.signal_status_var = tk.StringVar(value="SIGNAL STATUS: READY")
        tk.Label(right, textvariable=self.signal_status_var, fg=CYAN, bg=BG,
                 font=F_SMALL).pack(anchor="e", pady=(4, 0))

        self.analysis_status_var = tk.StringVar(value="ANALYSIS: STANDBY")
        tk.Label(right, textvariable=self.analysis_status_var, fg=MUTED, bg=BG,
                 font=F_SMALL).pack(anchor="e", pady=(2, 0))

        self.header_wave = tk.Canvas(right, width=140, height=26, bg=BG, highlightthickness=0)
        self.header_wave.pack(anchor="e", pady=(6, 0))

    # ================= INPUT =================
    def _build_input(self):
        panel = self._panel(self, fill="x", padx=18, pady=6)
        self._section_title(panel, "INCOMING TEXT SIGNAL")

        row = tk.Frame(panel, bg=PANEL)
        row.pack(fill="x", padx=14, pady=(0, 10))

        entry_wrap = tk.Frame(row, bg=PANEL2, highlightbackground=CYAN_DIM, highlightthickness=1)
        entry_wrap.pack(side="left", fill="x", expand=True)
        self.input_entry = tk.Entry(entry_wrap, font=("Consolas", 12), bg=PANEL2, fg=TEXT,
                                     insertbackground=CYAN, relief="flat", bd=0)
        self.input_entry.insert(0, "Elon visited Karachi yesterday.")
        self.input_entry.pack(fill="x", padx=10, pady=8)

        btn_row = tk.Frame(panel, bg=PANEL)
        btn_row.pack(anchor="w", padx=14, pady=(0, 12))

        self.analyze_btn = tk.Button(btn_row, text="▸ ANALYZE SIGNAL", font=F_MONO_B,
                                      fg=BG, bg=CYAN, activebackground=VIOLET,
                                      relief="flat", padx=16, pady=6, bd=0,
                                      command=self.run_analysis)
        self.analyze_btn.pack(side="left", padx=(0, 10))

        self.clear_btn = tk.Button(btn_row, text="CLEAR SIGNAL", font=F_MONO_B,
                                    fg=RED, bg=PANEL2, activebackground="#2a1820",
                                    relief="flat", padx=16, pady=6, bd=0,
                                    command=self.clear_all)
        self.clear_btn.pack(side="left")

    # ================= MAIN AREA (signal map + side panels) =================
    def _build_main_area(self):
        wrap = tk.Frame(self, bg=BG)
        wrap.pack(fill="both", expand=True, padx=18, pady=6)

        # ---- left: context signal map ----
        left = self._panel(wrap, side="left", fill="both", expand=True, padx=(0, 8))
        self._section_title(left, "CONTEXT SIGNAL MAP")
        self.map_canvas = tk.Canvas(left, bg=PANEL2, height=230, highlightthickness=0)
        self.map_canvas.pack(fill="both", expand=True, padx=14, pady=(0, 12))
        self.map_canvas.bind("<Button-1>", self._on_map_click)
        self._draw_map_placeholder()

        # ---- right: stacked panels ----
        right = tk.Frame(wrap, bg=BG, width=340)
        right.pack(side="left", fill="y")

        ctx = self._panel(right, fill="x")
        self._section_title(ctx, "CONTEXT ANALYSIS")
        self.ctx_text = tk.Label(ctx, text="TARGET\n—", font=F_MONO, bg=PANEL, fg=TEXT,
                                  justify="left", anchor="w")
        self.ctx_text.pack(anchor="w", padx=14, pady=(0, 12))

        cls = self._panel(right, fill="x", pady=(10, 0))
        self._section_title(cls, "SIGNAL CLASSIFICATION")
        self.cls_frame = tk.Frame(cls, bg=PANEL)
        self.cls_frame.pack(anchor="w", fill="x", padx=14, pady=(0, 12))

        ent = self._panel(right, fill="x", pady=(10, 0))
        self._section_title(ent, "ENTITY DETECTION")
        self.ent_frame = tk.Frame(ent, bg=PANEL)
        self.ent_frame.pack(anchor="w", fill="x", padx=14, pady=(0, 12))

    # ================= BOTTOM AREA (linguistic table + waveform + output + confidence) =================
    def _build_bottom_area(self):
        wrap = tk.Frame(self, bg=BG)
        wrap.pack(fill="x", padx=18, pady=6)

        # linguistic analysis table
        ling = self._panel(wrap, side="left", fill="both", expand=True, padx=(0, 8))
        self._section_title(ling, "LINGUISTIC ANALYSIS")
        header_row = tk.Frame(ling, bg=PANEL)
        header_row.pack(fill="x", padx=14)
        for txt, w in [("TOKEN", 12), ("POS", 8), ("LEMMA", 10), ("LABEL", 10), ("CONF", 6)]:
            tk.Label(header_row, text=txt, font=F_SMALL, bg=PANEL, fg=MUTED,
                     width=w, anchor="w").pack(side="left")
        self.ling_rows_frame = tk.Frame(ling, bg=PANEL)
        self.ling_rows_frame.pack(fill="x", padx=14, pady=(4, 12))

        # right column: waveform + output + confidence
        right = tk.Frame(wrap, bg=BG, width=340)
        right.pack(side="left", fill="y")

        wave_panel = self._panel(right, fill="x")
        self._section_title(wave_panel, "SIGNAL WAVEFORM")
        self.wave_canvas = tk.Canvas(wave_panel, bg=PANEL2, height=60, highlightthickness=0)
        self.wave_canvas.pack(fill="x", padx=14, pady=(0, 4))
        self.wave_state_var = tk.StringVar(value="IDLE")
        tk.Label(wave_panel, textvariable=self.wave_state_var, font=F_SMALL,
                 bg=PANEL, fg=CYAN).pack(anchor="e", padx=14, pady=(0, 10))

        out_panel = self._panel(right, fill="x", pady=(10, 0))
        self._section_title(out_panel, "INTELLIGENCE OUTPUT")
        self.output_text = tk.Label(out_panel, text=self._output_str(0, 0, 0, 0, "STANDBY"),
                                     font=F_MONO, bg=PANEL, fg=TEXT, justify="left", anchor="w")
        self.output_text.pack(anchor="w", padx=14, pady=(0, 12))

        conf_panel = self._panel(right, fill="x", pady=(10, 0))
        self._section_title(conf_panel, "CONFIDENCE SIGNAL")
        self.conf_canvas = tk.Canvas(conf_panel, bg=PANEL2, height=110, highlightthickness=0)
        self.conf_canvas.pack(fill="x", padx=14, pady=(0, 12))

    def _output_str(self, tokens, entities, labels, high_conf, status):
        return (f"TOKENS ANALYZED     {tokens:02d}\n"
                f"ENTITIES DETECTED   {entities:02d}\n"
                f"LABELS GENERATED    {labels:02d}\n"
                f"HIGH CONFIDENCE     {high_conf:02d}\n"
                f"SIGNAL STATUS       {status}")

    # ================= SYSTEM STATUS STRIP =================
    def _build_status_strip(self):
        strip = tk.Frame(self, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        strip.pack(fill="x", padx=18, pady=(6, 16))
        items = [("SYSTEM", "ONLINE", GREEN), ("SIGNAL", "READY", CYAN),
                  ("CONTEXT ENGINE", "READY", CYAN), ("CLASSIFIER", "READY", CYAN),
                  ("CASE", "ACTIVE", AMBER)]
        self.status_labels = {}
        for name, val, color in items:
            f = tk.Frame(strip, bg=PANEL)
            f.pack(side="left", expand=True, pady=10)
            tk.Label(f, text="● ", fg=color, bg=PANEL, font=F_SMALL).pack(side="left")
            tk.Label(f, text=f"{name}: ", fg=MUTED, bg=PANEL, font=F_SMALL).pack(side="left")
            lbl = tk.Label(f, text=val, fg=TEXT, bg=PANEL, font=("Consolas", 8, "bold"))
            lbl.pack(side="left")
            self.status_labels[name] = lbl

    # ================= WAVEFORM ANIMATION =================
    def _draw_wave(self, canvas, amplitude, color, speed=0.25):
        canvas.delete("wave")
        w = canvas.winfo_width() or 300
        h = canvas.winfo_height() or 60
        mid = h / 2
        points = []
        for x in range(0, w, 4):
            y = mid + amplitude * math.sin((x * 0.05) + self.wave_phase * speed)
            points.extend([x, y])
        if len(points) >= 4:
            canvas.create_line(*points, fill=color, width=1.6, tags="wave", smooth=True)

    def _animate_waveform(self):
        self.wave_phase += 1
        if self.wave_state == "idle":
            self._draw_wave(self.wave_canvas, 4, CYAN_DIM, speed=0.15)
            self._draw_wave(self.header_wave, 3, CYAN_DIM, speed=0.15)
        elif self.wave_state == "scanning":
            self._draw_wave(self.wave_canvas, 18, CYAN, speed=0.6)
            self._draw_wave(self.header_wave, 8, CYAN, speed=0.6)
        elif self.wave_state == "locked":
            self._draw_wave(self.wave_canvas, 10, GREEN, speed=0.2)
            self._draw_wave(self.header_wave, 4, GREEN, speed=0.2)
        self.wave_job = self.after(60, self._animate_waveform)

    # ================= SIGNAL MAP DRAWING =================
    def _draw_map_placeholder(self):
        self.map_canvas.delete("all")
        w = self.map_canvas.winfo_width() or 700
        h = self.map_canvas.winfo_height() or 230
        self.map_canvas.create_text(w / 2, h / 2, text="NO SIGNAL — CLICK ANALYZE SIGNAL",
                                     fill=MUTED, font=F_SMALL)

    def _draw_signal_map(self):
        c = self.map_canvas
        c.delete("all")
        self.node_boxes = {}
        w = c.winfo_width() or 800
        h = c.winfo_height() or 230
        n = len(self.tokens)
        if n == 0:
            self._draw_map_placeholder()
            return

        box_w, box_h = 108, 56
        gap = max(20, (w - n * box_w - 40) // max(1, n - 1)) if n > 1 else 0
        total_w = n * box_w + (n - 1) * gap
        start_x = max(20, (w - total_w) / 2)
        y = h / 2 - box_h / 2

        centers = []
        for i, t in enumerate(self.tokens):
            x = start_x + i * (box_w + gap)
            color = LABEL_COLORS.get(t["label"], MUTED)
            fill = PANEL if i != self.selected_idx else "#1a2433"
            rect = c.create_rectangle(x, y, x + box_w, y + box_h,
                                       outline=color, width=1.6, fill=fill)
            c.create_text(x + box_w / 2, y + box_h / 2 - 10, text=t["text"],
                          fill=TEXT, font=F_MONO_B)
            c.create_text(x + box_w / 2, y + box_h / 2 + 12, text=t["label"],
                          fill=color, font=F_SMALL)
            self.node_boxes[rect] = i
            centers.append((x + box_w / 2, y + box_h / 2, x + box_w, x))

        # connection lines with small pulse marker at midpoint
        for i in range(n - 1):
            _, cy, right_x, _ = centers[i]
            _, _, _, left_x2 = centers[i + 1]
            c.create_line(right_x, cy, left_x2, cy, fill=CYAN_DIM, width=1.4, arrow=tk.LAST,
                          arrowshape=(8, 10, 3))
            midx = (right_x + left_x2) / 2
            c.create_oval(midx - 2, cy - 2, midx + 2, cy + 2, fill=CYAN, outline="")

    def _on_map_click(self, event):
        item = self.map_canvas.find_closest(event.x, event.y)
        if not item:
            return
        idx = self.node_boxes.get(item[0])
        if idx is None:
            return
        self.selected_idx = idx
        self._draw_signal_map()
        self._update_context_panel(idx)

    # ================= PANEL UPDATES =================
    def _update_context_panel(self, idx):
        t = self.tokens[idx]
        prev_w = self.tokens[idx - 1]["text"] if idx > 0 else "—"
        next_w = self.tokens[idx + 1]["text"] if idx < len(self.tokens) - 1 else "—"
        text = (f"TARGET\n{t['text']}\n\n"
                f"PREVIOUS CONTEXT\n{prev_w}\n\n"
                f"NEXT CONTEXT\n{next_w}\n\n"
                f"PREDICTED LABEL\n{t['label']}\n\n"
                f"CONFIDENCE\n{t['conf']}%")
        self.ctx_text.configure(text=text)

    def _update_classification_panel(self):
        for w in self.cls_frame.winfo_children():
            w.destroy()
        for t in self.tokens:
            color = LABEL_COLORS.get(t["label"], MUTED)
            row = tk.Frame(self.cls_frame, bg=PANEL)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=t["text"], font=F_MONO, bg=PANEL, fg=TEXT,
                     width=14, anchor="w").pack(side="left")
            badge = tk.Label(row, text=f" {t['label']} ", font=("Consolas", 8, "bold"),
                              bg=PANEL2, fg=color, relief="solid", bd=1)
            badge.pack(side="left")

    def _update_entity_panel(self):
        for w in self.ent_frame.winfo_children():
            w.destroy()
        entities = [t for t in self.tokens if t["label"] != "O"]
        if not entities:
            tk.Label(self.ent_frame, text="NO ENTITIES DETECTED", font=F_SMALL,
                     bg=PANEL, fg=MUTED).pack(anchor="w")
            return
        for t in entities:
            color = LABEL_COLORS.get(t["label"], MUTED)
            row = tk.Frame(self.ent_frame, bg=PANEL)
            row.pack(fill="x", pady=3, anchor="w")
            tk.Label(row, text=f"[ {t['label']} ]", font=("Consolas", 8, "bold"),
                     bg=PANEL, fg=color).pack(side="left")
            tk.Label(row, text=f"  {t['text']}", font=F_MONO, bg=PANEL, fg=TEXT).pack(side="left")

    def _update_linguistic_table(self):
        for w in self.ling_rows_frame.winfo_children():
            w.destroy()
        for t in self.tokens:
            color = LABEL_COLORS.get(t["label"], MUTED)
            row = tk.Frame(self.ling_rows_frame, bg=PANEL)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=t["text"], font=F_MONO, bg=PANEL, fg=TEXT, width=12, anchor="w").pack(side="left")
            tk.Label(row, text=t["pos"], font=F_MONO, bg=PANEL, fg=MUTED, width=8, anchor="w").pack(side="left")
            tk.Label(row, text=t["lemma"], font=F_MONO, bg=PANEL, fg=MUTED, width=10, anchor="w").pack(side="left")
            tk.Label(row, text=t["label"], font=F_MONO, bg=PANEL, fg=color, width=10, anchor="w").pack(side="left")
            tk.Label(row, text=f"{t['conf']}%", font=F_MONO, bg=PANEL, fg=TEXT, width=6, anchor="w").pack(side="left")

    def _update_confidence_canvas(self):
        c = self.conf_canvas
        c.delete("all")
        w = c.winfo_width() or 300
        row_h = 22
        for i, t in enumerate(self.tokens):
            y = 10 + i * row_h
            color = LABEL_COLORS.get(t["label"], MUTED)
            c.create_text(6, y + 6, text=t["label"][:4], fill=color, font=F_SMALL, anchor="w")
            bar_x = 60
            bar_w = (w - bar_x - 50) * (t["conf"] / 100)
            c.create_rectangle(bar_x, y, bar_x + bar_w, y + 12, fill=color, outline="")
            c.create_text(w - 8, y + 6, text=f"{t['conf']}%", fill=TEXT, font=F_SMALL, anchor="e")

    def _update_output(self):
        n = len(self.tokens)
        entities = len([t for t in self.tokens if t["label"] != "O"])
        high_conf = len([t for t in self.tokens if t["conf"] >= 95])
        self.output_text.configure(text=self._output_str(n, entities, n, high_conf, "LOCKED"))

    # ================= ANALYSIS SEQUENCE =================
    def run_analysis(self):
        text = self.input_entry.get().strip()
        if not text:
            return
        self.analyze_btn.configure(state="disabled")
        self.selected_idx = None
        self.tokens = analyze_sentence(text)

        self.signal_status_var.set("SIGNAL STATUS: PROCESSING")
        steps = ["SIGNAL RECEIVED", "DECODING SIGNAL", "CONTEXT ANALYSIS",
                 "SEQUENCE LABELING", "ENTITY DETECTION", "CLASSIFICATION COMPLETE",
                 "INTELLIGENCE OUTPUT READY"]
        self.wave_state = "scanning"
        self.wave_state_var.set("SCANNING")

        def step(i=0):
            if i >= len(steps):
                self._finish_analysis()
                return
            self.analysis_status_var.set(f"ANALYSIS: {steps[i]}")
            if steps[i] == "SEQUENCE LABELING":
                self.wave_state_var.set("ANALYZING")
            self.after(320, lambda: step(i + 1))
        step()

    def _finish_analysis(self):
        self.signal_status_var.set("SIGNAL STATUS: LOCKED")
        self.wave_state = "locked"
        self.wave_state_var.set("SIGNAL LOCKED")
        self._draw_signal_map()
        self._update_classification_panel()
        self._update_entity_panel()
        self._update_linguistic_table()
        self._update_confidence_canvas()
        self._update_output()
        if self.tokens:
            self.selected_idx = 0
            self._draw_signal_map()
            self._update_context_panel(0)
        self.status_labels["SIGNAL"].configure(text="LOCKED", fg=GREEN)
        self.status_labels["CASE"].configure(text="COMPLETE", fg=GREEN)
        self.analyze_btn.configure(state="normal")

    # ================= CLEAR =================
    def clear_all(self):
        self.tokens = []
        self.selected_idx = None
        self.signal_status_var.set("SIGNAL STATUS: READY")
        self.analysis_status_var.set("ANALYSIS: STANDBY")
        self.wave_state = "idle"
        self.wave_state_var.set("IDLE")
        self._draw_map_placeholder()
        self.ctx_text.configure(text="TARGET\n—")
        for w in self.cls_frame.winfo_children():
            w.destroy()
        for w in self.ent_frame.winfo_children():
            w.destroy()
        for w in self.ling_rows_frame.winfo_children():
            w.destroy()
        self.conf_canvas.delete("all")
        self.output_text.configure(text=self._output_str(0, 0, 0, 0, "STANDBY"))
        self.status_labels["SIGNAL"].configure(text="READY", fg=CYAN)
        self.status_labels["CASE"].configure(text="ACTIVE", fg=AMBER)


if __name__ == "__main__":
    app = FlairSignalCenter()
    app.mainloop()