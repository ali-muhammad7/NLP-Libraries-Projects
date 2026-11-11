import tkinter as tk
import random, math

# ===================== PALETTE =====================
PEARL     = "#F7F5F2"
ICE       = "#EAF7FA"
LAVENDER  = "#EEE8FF"
AQUA      = "#DDF7F2"
CHAMPAGNE = "#F7EFD8"
CORAL     = "#F7D8D2"
WHITE     = "#FFFFFF"
TEXT      = "#30323A"
MUTED     = "#9a9dab"
VIOLET    = "#8D7BEA"
AQUA_ACC  = "#5CCBC1"
BORDER    = "#E4E1F0"
SHADOW    = "#EAE7F2"

F_TITLE = ("Georgia", 24, "bold")
F_SUB   = ("Georgia", 10, "italic")
F_LABEL = ("Segoe UI", 9, "bold")
F_SMALL = ("Segoe UI", 8)
F_BODY  = ("Segoe UI", 10)

SAMPLE_SENTENCES = [
    "The cat sat on the mat because it was tired.",
    "Ali visited the university because he had an exam.",
    "The transformer model learned language patterns quickly.",
]

TASK_DEMO = {
    "TEXT CLASSIFICATION": {"label": "POSITIVE", "confidence": 91.4,
                             "secondary": [("NEGATIVE", 8.6)]},
    "NAMED ENTITY RECOGNITION": {"label": "PERSON: Ali", "confidence": 95.0,
                                  "secondary": [("LOCATION: Pakistan", 92.0)]},
    "FILL MASK": {"label": "mat", "confidence": 88.7,
                  "secondary": [("floor", 6.2), ("rug", 3.1)]},
    "TEXT GENERATION": {"label": "quietly on the mat, watching the door.",
                         "confidence": 84.0, "secondary": []},
}

EDU_NOTES = {
    "tokenize": "Text is divided into model-readable token units.",
    "embed": "Tokens are represented as numerical vectors.",
    "attend": "Each token evaluates the relevance of other tokens.",
    "layer": "Attention and feed-forward transformations refine context.",
    "predict": "The processed representation produces a task-specific output.",
}


def pseudo_weight(w1, w2):
    seed = abs(hash(w1.lower() + "|" + w2.lower())) % 10000
    rnd = random.Random(seed)
    return round(0.15 + rnd.random() * 0.75, 2)


def pseudo_vector(word):
    seed = abs(hash(word.lower())) % 10000
    rnd = random.Random(seed)
    return [round(rnd.uniform(-1, 1), 2) for _ in range(6)]


def round_rect(canvas, x1, y1, x2, y2, r=18, **kw):
    pts = [x1+r,y1, x2-r,y1, x2,y1, x2,y1+r, x2,y2-r, x2,y2,
           x2-r,y2, x1+r,y2, x1,y2, x1,y2-r, x1,y1+r, x1,y1]
    return canvas.create_polygon(pts, smooth=True, **kw)


def glass_panel(canvas, x1, y1, x2, y2, r=18, fill=WHITE, outline=BORDER):
    round_rect(canvas, x1+5, y1+7, x2+5, y2+7, r, fill=SHADOW, outline="")
    round_rect(canvas, x1, y1, x2, y2, r, fill=fill, outline=outline, width=1)


class PrismaticTransformerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PRISMATIC TRANSFORMER — The Crystal Mind")
        self.geometry("1400x850")
        self.minsize(1200, 750)
        self.configure(bg=PEARL)

        self.tokens = []
        self.selected_idx = None
        self.current_task = "TEXT CLASSIFICATION"
        self.particles = []
        self.pulse_phase = 0

        self.bg_canvas = tk.Canvas(self, bg=PEARL, highlightthickness=0)
        self.bg_canvas.place(relx=0, rely=0, relwidth=1, relheight=1)

        self._build_header()
        self._build_text_portal()
        self._build_token_inspector()
        self._build_token_garden()
        self._build_crystal_embedding()
        self._build_transformation_stack()
        self._build_prediction_crystal()

        self.after(150, self._draw_background)
        self.after(200, self._animate_particles)
        self.after(300, lambda: self.load_sentence(SAMPLE_SENTENCES[0]))
        self._sample_idx = 0

    # ---------------- BACKGROUND ----------------
    def _draw_background(self):
        c = self.bg_canvas
        w, h = c.winfo_width(), c.winfo_height()
        if w < 10:
            self.after(100, self._draw_background); return
        c.delete("atmo")
        blobs = [(0.1*w, 0.1*h, 260, LAVENDER), (0.85*w, 0.15*h, 220, ICE),
                 (0.15*w, 0.85*h, 240, AQUA), (0.9*w, 0.8*h, 260, CHAMPAGNE),
                 (0.5*w, 0.5*h, 300, CORAL)]
        for bx, by, r, col in blobs:
            c.create_oval(bx-r, by-r, bx+r, by+r, fill=col, outline="", stipple="gray25", tags="atmo")
        c.tag_lower("atmo")
        for _ in range(16):
            x, y = random.uniform(0, w), random.uniform(0, h)
            p = c.create_oval(x, y, x+3, y+3, fill=WHITE, outline=VIOLET, tags="atmo")
            self.particles.append([p, random.uniform(-0.3, 0.3), random.uniform(-0.3, 0.3)])
        c.tag_lower("atmo")

    def _animate_particles(self):
        w, h = self.bg_canvas.winfo_width(), self.bg_canvas.winfo_height()
        for item in self.particles:
            p, dx, dy = item
            self.bg_canvas.move(p, dx, dy)
            coords = self.bg_canvas.coords(p)
            if coords and (coords[0] < 0 or coords[0] > w or coords[1] < 0 or coords[1] > h):
                self.bg_canvas.moveto(p, random.uniform(0, w), random.uniform(0, h))
        self.after(80, self._animate_particles)

    # ---------------- HEADER ----------------
    def _build_header(self):
        header = tk.Frame(self, bg=PEARL)
        header.place(relx=0.02, rely=0.015, relwidth=0.96, relheight=0.11)

        left = tk.Frame(header, bg=PEARL)
        left.pack(side="left", anchor="w")
        tk.Label(left, text="PRISMATIC TRANSFORMER", font=F_TITLE, bg=PEARL, fg=TEXT).pack(anchor="w")
        tk.Label(left, text="THE CRYSTAL MIND", font=("Georgia", 11, "bold"), bg=PEARL, fg=VIOLET).pack(anchor="w")
        tk.Label(left, text="Exploring language through attention, representation and transformation",
                 font=F_SUB, bg=PEARL, fg=MUTED).pack(anchor="w", pady=(2, 0))

        right = tk.Frame(header, bg=PEARL)
        right.pack(side="right", anchor="e")
        tk.Label(right, text="TASK", font=F_SMALL, bg=PEARL, fg=MUTED).pack(anchor="e")
        row = tk.Frame(right, bg=PEARL)
        row.pack(anchor="e", pady=(2, 0))
        self.task_buttons = {}
        for task in TASK_DEMO:
            b = tk.Button(row, text=task, font=("Segoe UI", 8, "bold"), bg=WHITE, fg=TEXT,
                          relief="flat", padx=8, pady=5, activebackground=LAVENDER,
                          command=lambda t=task: self.set_task(t))
            b.pack(side="left", padx=3)
            self.task_buttons[task] = b
        self._refresh_task_buttons()

    def _refresh_task_buttons(self):
        for t, b in self.task_buttons.items():
            b.configure(bg=VIOLET, fg=WHITE) if t == self.current_task else b.configure(bg=WHITE, fg=TEXT)

    def set_task(self, task):
        self.current_task = task
        self._refresh_task_buttons()
        self._draw_prediction_crystal()

    # ---------------- TEXT PORTAL ----------------
    def _build_text_portal(self):
        panel = tk.Frame(self, bg=WHITE, highlightbackground=BORDER, highlightthickness=1)
        panel.place(relx=0.02, rely=0.14, relwidth=0.22, relheight=0.28)

        tk.Label(panel, text="TEXT PORTAL", font=F_LABEL, bg=WHITE, fg=VIOLET).pack(anchor="w", padx=14, pady=(12, 8))

        self.portal_var = tk.StringVar()
        entry_wrap = tk.Frame(panel, bg=ICE, highlightbackground=BORDER, highlightthickness=1)
        entry_wrap.pack(fill="x", padx=14)
        self.portal_entry = tk.Entry(entry_wrap, textvariable=self.portal_var, font=("Segoe UI", 10),
                                      bg=ICE, fg=TEXT, relief="flat", insertbackground=VIOLET)
        self.portal_entry.pack(fill="x", padx=8, pady=8)

        btn_row = tk.Frame(panel, bg=WHITE)
        btn_row.pack(anchor="w", padx=14, pady=12)
        self.analyze_btn = tk.Button(btn_row, text="ANALYZE", font=("Segoe UI", 9, "bold"),
                                      bg=VIOLET, fg=WHITE, relief="flat", padx=12, pady=5,
                                      command=self.run_analysis)
        self.analyze_btn.pack(side="left", padx=(0, 6))
        tk.Button(btn_row, text="LOAD SAMPLE", font=("Segoe UI", 8, "bold"), bg=AQUA, fg=TEXT,
                  relief="flat", padx=10, pady=5, command=self.load_next_sample).pack(side="left", padx=(0, 6))
        tk.Button(btn_row, text="CLEAR", font=("Segoe UI", 8, "bold"), bg=CORAL, fg=TEXT,
                  relief="flat", padx=10, pady=5, command=self.clear_portal).pack(side="left")

        tk.Label(panel, text="TOKENIZATION\n" + EDU_NOTES["tokenize"], font=F_SMALL, bg=WHITE, fg=MUTED,
                 justify="left", wraplength=230).pack(anchor="w", padx=14, pady=(6, 10))

    def load_next_sample(self):
        self._sample_idx = (self._sample_idx + 1) % len(SAMPLE_SENTENCES)
        self.load_sentence(SAMPLE_SENTENCES[self._sample_idx])

    def clear_portal(self):
        self.portal_var.set("")

    # ---------------- TOKEN INSPECTOR ----------------
    def _build_token_inspector(self):
        panel = tk.Frame(self, bg=WHITE, highlightbackground=BORDER, highlightthickness=1)
        panel.place(relx=0.02, rely=0.44, relwidth=0.22, relheight=0.30)
        tk.Label(panel, text="TOKEN INSPECTOR", font=F_LABEL, bg=WHITE, fg=VIOLET).pack(anchor="w", padx=14, pady=(12, 8))
        self.inspector_text = tk.Label(panel, text="Click a crystal in the\nToken Garden to inspect it.",
                                        font=F_BODY, bg=WHITE, fg=TEXT, justify="left", anchor="nw")
        self.inspector_text.pack(anchor="w", padx=14, fill="both", expand=True)

    def _update_inspector(self, idx):
        word = self.tokens[idx]
        prev_w = self.tokens[idx-1] if idx > 0 else "—"
        next_w = self.tokens[idx+1] if idx < len(self.tokens)-1 else "—"
        weights = sorted(((t, pseudo_weight(word, t)) for j, t in enumerate(self.tokens) if j != idx),
                          key=lambda x: -x[1])[:4]
        att_lines = "\n".join(f"{w.upper():<10}{int(v*100)}%" for w, v in weights)
        txt = (f"TOKEN\n{word}\n\n"
               f"TOKEN ID\nT-{idx+1:03d}\n\n"
               f"POSITION\n{idx+1:02d}\n\n"
               f"CONTEXT\n{prev_w} | {word} | {next_w}\n\n"
               f"ATTENTION\n{att_lines}")
        self.inspector_text.configure(text=txt)

    # ---------------- TOKEN GARDEN (+ Attention Refraction) ----------------
    def _build_token_garden(self):
        panel = tk.Frame(self, bg=PEARL)
        panel.place(relx=0.26, rely=0.14, relwidth=0.46, relheight=0.30)
        tk.Label(panel, text="TOKEN GARDEN  ·  ATTENTION REFRACTION", font=F_LABEL,
                 bg=PEARL, fg=VIOLET).pack(anchor="w", padx=4, pady=(0, 4))
        self.garden_canvas = tk.Canvas(panel, bg=WHITE, highlightbackground=BORDER, highlightthickness=1)
        self.garden_canvas.pack(fill="both", expand=True)
        self.garden_canvas.bind("<Button-1>", self._on_garden_click)
        self.garden_canvas.bind("<Configure>", lambda e: self._draw_token_garden())
        self.token_hit_areas = {}

    def _draw_token_garden(self):
        c = self.garden_canvas
        c.delete("all")
        self.token_hit_areas = {}
        w = c.winfo_width() or 500
        h = c.winfo_height() or 200
        if not self.tokens:
            c.create_text(w/2, h/2, text="Analyze a sentence to grow the Token Garden",
                           fill=MUTED, font=F_SMALL)
            return
        n = len(self.tokens)
        spacing = w / (n + 1)
        positions = []
        for i, tok in enumerate(self.tokens):
            x = spacing * (i + 1)
            y = h/2 + (18 if i % 2 == 0 else -18)
            positions.append((x, y))

        # attention beams from selected token
        if self.selected_idx is not None:
            sx, sy = positions[self.selected_idx]
            weights = [(j, pseudo_weight(self.tokens[self.selected_idx], self.tokens[j]))
                       for j in range(n) if j != self.selected_idx]
            weights.sort(key=lambda x: -x[1])
            for j, val in weights[:4]:
                tx, ty = positions[j]
                width = 1 + val * 4
                col = VIOLET if val > 0.5 else AQUA_ACC
                c.create_line(sx, sy, tx, ty, fill=col, width=width, smooth=True)
                mx, my = (sx+tx)/2, (sy+ty)/2 - 8
                c.create_text(mx, my, text=f"{int(val*100)}%", font=F_SMALL, fill=col)

        for i, tok in enumerate(self.tokens):
            x, y = positions[i]
            selected = (i == self.selected_idx)
            size = 20 if selected else 15
            color = VIOLET if selected else AQUA
            outline = VIOLET
            pts = [x, y-size, x+size, y, x, y+size, x-size, y]
            item = c.create_polygon(pts, fill=color, outline=outline, width=1.5)
            c.create_text(x, y+size+12, text=tok, font=("Segoe UI", 9, "bold"), fill=TEXT)
            c.create_text(x, y+size+24, text=f"T-{i+1:03d}", font=F_SMALL, fill=MUTED)
            self.token_hit_areas[item] = i

    def _on_garden_click(self, event):
        item = self.garden_canvas.find_closest(event.x, event.y)
        if not item:
            return
        idx = self.token_hit_areas.get(item[0])
        if idx is None:
            return
        self.selected_idx = idx
        self._draw_token_garden()
        self._update_inspector(idx)
        self._draw_embedding_prism()
        self._pulse_crystal()

    # ---------------- CRYSTAL MIND + EMBEDDING PRISM ----------------
    def _build_crystal_embedding(self):
        panel = tk.Frame(self, bg=PEARL)
        panel.place(relx=0.26, rely=0.46, relwidth=0.46, relheight=0.30)
        tk.Label(panel, text="CRYSTAL MIND  ·  EMBEDDING PRISM", font=F_LABEL,
                 bg=PEARL, fg=VIOLET).pack(anchor="w", padx=4, pady=(0, 4))
        self.crystal_canvas = tk.Canvas(panel, bg=WHITE, highlightbackground=BORDER, highlightthickness=1)
        self.crystal_canvas.pack(fill="both", expand=True)
        self.crystal_canvas.bind("<Configure>", lambda e: (self._draw_crystal_mind(), self._draw_embedding_prism()))

    def _draw_crystal_mind(self, scale=1.0):
        c = self.crystal_canvas
        c.delete("crystal")
        w = c.winfo_width() or 500
        h = c.winfo_height() or 200
        cx, cy = w * 0.28, h / 2
        base = min(w, h) * 0.32 * scale
        for i, (r, col) in enumerate([(base, LAVENDER), (base*0.7, AQUA), (base*0.4, VIOLET)]):
            pts = []
            for k in range(6):
                ang = math.pi/3*k - math.pi/6
                pts += [cx + r*math.cos(ang), cy + r*math.sin(ang)]
            c.create_polygon(pts, fill=col, outline=VIOLET, width=1, tags="crystal")
        c.create_text(cx, cy + base + 16, text="CRYSTAL CORE", font=F_SMALL, fill=MUTED, tags="crystal")

    def _pulse_crystal(self):
        steps = [1.0, 1.08, 1.14, 1.08, 1.0]
        def anim(i=0):
            if i >= len(steps):
                return
            self._draw_crystal_mind(scale=steps[i])
            self._draw_embedding_prism()
            self.after(80, lambda: anim(i+1))
        anim()

    def _draw_embedding_prism(self):
        c = self.crystal_canvas
        c.delete("prism")
        w = c.winfo_width() or 500
        h = c.winfo_height() or 200
        px, py = w * 0.75, h / 2
        size = min(w, h) * 0.24
        pts = [px, py-size, px+size, py-size*0.4, px+size, py+size*0.4, px, py+size,
               px-size, py+size*0.4, px-size, py-size*0.4]
        c.create_polygon(pts, fill=ICE, outline=AQUA_ACC, width=1.4, tags="prism")
        if self.selected_idx is not None:
            word = self.tokens[self.selected_idx]
            c.create_text(px, py-size-14, text=f'"{word}"', font=("Segoe UI", 9, "bold"),
                          fill=TEXT, tags="prism")
            vec = pseudo_vector(word)
            random.Random(word).shuffle(vec)
            for i, v in enumerate(vec):
                vx = px + random.Random(word+str(i)).uniform(-size*0.6, size*0.6)
                vy = py - size*0.5 + i * (size / 3)
                c.create_text(vx, vy, text=f"{v:+.2f}", font=F_SMALL, fill=VIOLET, tags="prism")
        else:
            c.create_text(px, py, text="select a token", font=F_SMALL, fill=MUTED, tags="prism")

    # ---------------- TRANSFORMATION STACK ----------------
    def _build_transformation_stack(self):
        panel = tk.Frame(self, bg=PEARL)
        panel.place(relx=0.74, rely=0.14, relwidth=0.24, relheight=0.44)
        tk.Label(panel, text="TRANSFORMATION STACK", font=F_LABEL, bg=PEARL, fg=VIOLET).pack(anchor="w", padx=4, pady=(0, 4))
        self.stack_canvas = tk.Canvas(panel, bg=WHITE, highlightbackground=BORDER, highlightthickness=1)
        self.stack_canvas.pack(fill="both", expand=True)
        self.stack_canvas.bind("<Button-1>", self._on_stack_click)
        self.stack_canvas.bind("<Configure>", lambda e: self._draw_stack())
        self.stack_labels = ["ATTENTION", "FEED FORWARD", "NORMALIZATION", "ATTENTION"]
        self.stack_hits = {}
        self.expanded_layer = None

    def _draw_stack(self):
        c = self.stack_canvas
        c.delete("all")
        self.stack_hits = {}
        w = c.winfo_width() or 260
        h = c.winfo_height() or 300
        n = 4
        layer_h = h / (n + 1)
        for i in range(n):
            y = layer_h * (i + 0.6)
            rw = w * (0.7 - i*0.04)
            x1, x2 = (w-rw)/2, (w+rw)/2
            col = LAVENDER if i % 2 == 0 else AQUA
            item = round_rect(c, x1, y, x2, y+layer_h*0.6, r=14, fill=col, outline=VIOLET, width=1)
            c.create_text((x1+x2)/2, y+layer_h*0.18, text=f"LAYER {i+1:02d}", font=("Segoe UI", 9, "bold"), fill=TEXT)
            c.create_text((x1+x2)/2, y+layer_h*0.42, text=self.stack_labels[i], font=F_SMALL, fill=MUTED)
            self.stack_hits[item] = i
        if self.expanded_layer is not None:
            c.create_text(w/2, h-14, text=EDU_NOTES["layer"], font=F_SMALL, fill=VIOLET, width=w-20)

    def _on_stack_click(self, event):
        item = self.stack_canvas.find_closest(event.x, event.y)
        idx = self.stack_hits.get(item[0]) if item else None
        self.expanded_layer = idx
        self._draw_stack()

    # ---------------- PREDICTION CRYSTAL ----------------
    def _build_prediction_crystal(self):
        panel = tk.Frame(self, bg=PEARL)
        panel.place(relx=0.74, rely=0.60, relwidth=0.24, relheight=0.24)
        tk.Label(panel, text="PREDICTION CRYSTAL", font=F_LABEL, bg=PEARL, fg=VIOLET).pack(anchor="w", padx=4, pady=(0, 4))
        self.pred_canvas = tk.Canvas(panel, bg=WHITE, highlightbackground=BORDER, highlightthickness=1)
        self.pred_canvas.pack(fill="both", expand=True)
        self.pred_canvas.bind("<Configure>", lambda e: self._draw_prediction_crystal())

    def _draw_prediction_crystal(self):
        c = self.pred_canvas
        c.delete("all")
        w = c.winfo_width() or 260
        h = c.winfo_height() or 150
        data = TASK_DEMO[self.current_task]
        conf = data["confidence"]
        cx, cy = w*0.35, h/2
        r = 20 + (conf/100) * min(w, h) * 0.28
        glow = VIOLET if conf >= 90 else AQUA_ACC if conf >= 70 else MUTED
        pts = []
        for k in range(6):
            ang = math.pi/3*k
            pts += [cx + r*math.cos(ang), cy + r*math.sin(ang)]
        c.create_polygon(pts, fill=LAVENDER, outline=glow, width=2)
        c.create_text(cx, cy-6, text=data["label"], font=("Segoe UI", 9, "bold"), fill=TEXT, width=r*1.6)
        c.create_text(cx, cy+14, text=f"{conf}%", font=("Segoe UI", 10, "bold"), fill=glow)

        sx = w*0.75
        for i, (lbl, val) in enumerate(data["secondary"]):
            sy = 20 + i*26
            sr = 8 + val*0.15
            c.create_oval(sx-sr, sy-sr, sx+sr, sy+sr, fill=AQUA, outline=AQUA_ACC)
            c.create_text(sx+sr+6, sy, text=f"{lbl} {val}%", font=F_SMALL, fill=MUTED, anchor="w")

    # ---------------- ANALYSIS ----------------
    def load_sentence(self, sentence):
        self.portal_var.set(sentence)
        self.run_analysis()

    def run_analysis(self):
        text = self.portal_var.get().strip().rstrip(".!?")
        if not text:
            return
        self.tokens = text.split()
        self.selected_idx = 0
        self._draw_token_garden()
        self._update_inspector(0)
        self._draw_crystal_mind()
        self._draw_embedding_prism()
        self._draw_stack()
        self._draw_prediction_crystal()
        self._pulse_crystal()


if __name__ == "__main__":
    app = PrismaticTransformerApp()
    app.mainloop()