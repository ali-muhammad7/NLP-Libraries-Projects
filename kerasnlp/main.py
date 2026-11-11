import tkinter as tk
import random, math

# ===================== PALETTE =====================
PEARL     = "#F6F4EC"
SAGE      = "#B9C9AE"
MINT      = "#DCEBD9"
AQUA      = "#D7EAE6"
LAVENDER  = "#E9E3F5"
PEACH     = "#F5DCC8"
BLUSH     = "#F6DDE0"
GOLD      = "#D9A441"
WHITE     = "#FFFFFF"
TEXT      = "#33402F"
MUTED     = "#93998C"
BORDER    = "#E3E6DA"
SHADOW    = "#EAEBE1"
GREEN_TXT = "#4C6B49"

F_TITLE = ("Georgia", 24, "bold")
F_SUB   = ("Georgia", 10, "italic")
F_LABEL = ("Segoe UI", 9, "bold")
F_SMALL = ("Segoe UI", 8)
F_BODY  = ("Segoe UI", 10)

SAMPLES = [
    "The cat sat on the mat because it was tired.",
    "Ali is studying artificial intelligence in Pakistan.",
    "Machine learning helps computers discover patterns in data.",
    "Sir Raheel teaches deep learning at Hyderabad University.",
    "Neural networks learn representations through layers of activation.",
]

TASK_DEMO = {
    "TEXT CLASSIFICATION": {"label": "POSITIVE", "confidence": 91.4, "extra": ""},
    "NAMED ENTITY RECOGNITION": {"label": "PERSON: Ali", "confidence": 95.0, "extra": "LOCATION: Pakistan"},
    "SENTIMENT ANALYSIS": {"label": "Positive", "confidence": 87.0, "extra": ""},
    "TEXT GENERATION": {"label": "...quietly on the mat.", "confidence": 80.0, "extra": ""},
}


def build_dynamic_result(task, tokens):
    """Builds a result that reacts to the sentence the user typed,
    instead of always showing the same fixed demo values."""
    if task == "NAMED ENTITY RECOGNITION":
        found = [t for t in tokens if t[:1].isupper()]
        if not found:
            return {"label": "No entities found", "confidence": 0.0, "extra": ""}
        main = found[0]
        extra = f"LOCATION: {found[1]}" if len(found) > 1 else ""
        return {"label": f"PERSON: {main}", "confidence": 95.0, "extra": extra}

    if task == "TEXT GENERATION":
        last = tokens[-1] if tokens else "language"
        return {"label": f"...continues gently with '{last}' in focus.",
                "confidence": 80.0, "extra": ""}

    # TEXT CLASSIFICATION and SENTIMENT ANALYSIS stay as static demo values
    return TASK_DEMO[task]


EDU = ["TOKENIZATION", "EMBEDDING", "NEURAL LAYERS", "ACTIVATION", "PREDICTION"]
EDU_NOTES = {
    "TOKENIZATION": "Breaks text into smaller units a model can process.",
    "EMBEDDING": "Maps tokens into numerical representations.",
    "NEURAL LAYERS": "Transform representations through learned operations.",
    "ACTIVATION": "Controls how strongly neurons respond.",
    "PREDICTION": "Produces the final task-specific output.",
}


def pseudo_vector(word, n=6):
    seed = abs(hash(word.lower())) % 10000
    rnd = random.Random(seed)
    return [round(rnd.uniform(-1, 1), 2) for _ in range(n)]


def pseudo_activation(word):
    seed = abs(hash("act|" + word.lower())) % 10000
    rnd = random.Random(seed)
    return round(0.35 + rnd.random() * 0.6, 2)


def round_rect(canvas, x1, y1, x2, y2, r=18, **kw):
    pts = [x1+r,y1, x2-r,y1, x2,y1, x2,y1+r, x2,y2-r, x2,y2,
           x2-r,y2, x1+r,y2, x1,y2, x1,y2-r, x1,y1+r, x1,y1]
    return canvas.create_polygon(pts, smooth=True, **kw)


def petal_points(cx, cy, angle, length, width):
    dx, dy = math.cos(angle), math.sin(angle)
    px, py = -dy, dx
    tip = (cx + dx*length, cy + dy*length)
    m1 = (cx + dx*length*0.55 + px*width/2, cy + dy*length*0.55 + py*width/2)
    m2 = (cx + dx*length*0.55 - px*width/2, cy + dy*length*0.55 - py*width/2)
    return [cx, cy, m2[0], m2[1], tip[0], tip[1], m1[0], m1[1]]


class NeuralBloomApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("KERAS NLP — Neural Bloom")
        self.geometry("1400x850")
        self.minsize(1200, 750)
        self.configure(bg=PEARL)

        self.tokens = []
        self.selected_idx = None
        self.current_task = "TEXT CLASSIFICATION"
        self.grow_stage = 0
        self.particles = []

        self.bg_canvas = tk.Canvas(self, bg=PEARL, highlightthickness=0)
        self.bg_canvas.place(relx=0, rely=0, relwidth=1, relheight=1)

        self._build_header()
        self._build_text_seed()
        self._build_token_sprouts()
        self._build_neural_tree()
        self._build_inspector()
        self._build_prediction()
        self._build_pipeline_strip()

        self.after(150, self._draw_background)
        self.after(200, self._animate_particles)
        self.after(300, lambda: self.load_sentence(SAMPLES[0]))
        self._sample_idx = 0

    # ---------------- BACKGROUND ----------------
    def _draw_background(self):
        c = self.bg_canvas
        w, h = c.winfo_width(), c.winfo_height()
        if w < 10:
            self.after(100, self._draw_background); return
        c.delete("atmo")
        blobs = [(0.1*w, 0.15*h, 250, MINT), (0.9*w, 0.1*h, 220, LAVENDER),
                 (0.12*w, 0.88*h, 240, AQUA), (0.9*w, 0.85*h, 230, PEACH),
                 (0.5*w, 0.5*h, 300, BLUSH)]
        for bx, by, r, col in blobs:
            c.create_oval(bx-r, by-r, bx+r, by+r, fill=col, outline="", stipple="gray25", tags="atmo")
        c.tag_lower("atmo")
        for _ in range(14):
            x, y = random.uniform(0, w), random.uniform(0, h)
            p = c.create_oval(x, y, x+3, y+3, fill=GOLD, outline="", tags="atmo")
            self.particles.append([p, random.uniform(-0.15, 0.15), random.uniform(0.05, 0.2)])
        c.tag_lower("atmo")

    def _animate_particles(self):
        w, h = self.bg_canvas.winfo_width(), self.bg_canvas.winfo_height()
        for item in self.particles:
            p, dx, dy = item
            self.bg_canvas.move(p, dx, dy)
            coords = self.bg_canvas.coords(p)
            if coords and (coords[1] > h or coords[0] < 0 or coords[0] > w):
                self.bg_canvas.moveto(p, random.uniform(0, w), 0)
        self.after(90, self._animate_particles)

    # ---------------- HEADER ----------------
    def _build_header(self):
        header = tk.Frame(self, bg=PEARL)
        header.place(relx=0.5, rely=0.015, relwidth=0.96, relheight=0.09, anchor="n")
        tk.Label(header, text="NEURAL BLOOM", font=F_TITLE, bg=PEARL, fg=TEXT).pack()
        tk.Label(header, text="WHERE LANGUAGE GROWS INTO INTELLIGENCE", font=("Georgia", 10, "bold"),
                 bg=PEARL, fg="#7C9A70").pack()

        task_row = tk.Frame(self, bg=PEARL)
        task_row.place(relx=0.98, rely=0.015, anchor="ne")
        self.task_buttons = {}
        for t in TASK_DEMO:
            b = tk.Button(task_row, text=t, font=("Segoe UI", 7, "bold"), bg=WHITE, fg=TEXT,
                          relief="flat", padx=6, pady=4, activebackground=MINT,
                          command=lambda t=t: self.set_task(t))
            b.pack(side="left", padx=2)
            self.task_buttons[t] = b
        self._refresh_task_buttons()

    def _refresh_task_buttons(self):
        for t, b in self.task_buttons.items():
            b.configure(bg=SAGE, fg=WHITE) if t == self.current_task else b.configure(bg=WHITE, fg=TEXT)

    def set_task(self, task):
        self.current_task = task
        self._refresh_task_buttons()
        self._draw_prediction()

    # ---------------- TEXT SEED ----------------
    def _build_text_seed(self):
        panel = tk.Frame(self, bg=WHITE, highlightbackground=BORDER, highlightthickness=1)
        panel.place(relx=0.02, rely=0.13, relwidth=0.21, relheight=0.24)
        tk.Label(panel, text="TEXT SEED", font=F_LABEL, bg=WHITE, fg=GREEN_TXT).pack(anchor="w", padx=14, pady=(12, 8))

        self.seed_var = tk.StringVar()
        wrap = tk.Frame(panel, bg=MINT, highlightbackground=BORDER, highlightthickness=1)
        wrap.pack(fill="x", padx=14)
        self.seed_entry = tk.Entry(wrap, textvariable=self.seed_var, font=("Segoe UI", 10),
                                    bg=MINT, fg=TEXT, relief="flat", insertbackground=GREEN_TXT)
        self.seed_entry.pack(fill="x", padx=8, pady=8)

        tk.Button(panel, text="GROW MODEL", font=("Segoe UI", 9, "bold"), bg=SAGE, fg=WHITE,
                  relief="flat", padx=10, pady=6, command=self.grow_model).pack(pady=(12, 4))
        row = tk.Frame(panel, bg=WHITE)
        row.pack()
        tk.Button(row, text="SAMPLE", font=F_SMALL, bg=LAVENDER, fg=TEXT, relief="flat",
                  padx=8, pady=4, command=self.load_next_sample).pack(side="left", padx=3)
        tk.Button(row, text="RESET", font=F_SMALL, bg=BLUSH, fg=TEXT, relief="flat",
                  padx=8, pady=4, command=self.reset_ecosystem).pack(side="left", padx=3)

    def load_next_sample(self):
        self._sample_idx = (self._sample_idx + 1) % len(SAMPLES)
        self.load_sentence(SAMPLES[self._sample_idx])

    # ---------------- TOKEN SPROUTS ----------------
    def _build_token_sprouts(self):
        wrapper = tk.Frame(self, bg=PEARL)
        wrapper.place(relx=0.02, rely=0.39, relwidth=0.21, relheight=0.26)
        tk.Label(wrapper, text="TOKEN SPROUTS", font=F_LABEL, bg=PEARL, fg=GREEN_TXT).pack(anchor="w", padx=2)
        self.sprout_canvas = tk.Canvas(wrapper, bg=WHITE, highlightbackground=BORDER, highlightthickness=1)
        self.sprout_canvas.pack(fill="both", expand=True, pady=(4, 0))
        self.sprout_canvas.bind("<Button-1>", self._on_sprout_click)
        self.sprout_canvas.bind("<Configure>", lambda e: self._draw_sprouts())
        self.sprout_hits = {}

    def _draw_sprouts(self):
        c = self.sprout_canvas
        c.delete("all")
        self.sprout_hits = {}
        w, h = c.winfo_width() or 260, c.winfo_height() or 180
        if not self.tokens:
            c.create_text(w/2, h/2, text="Grow the model to\nsee sprouts", fill=MUTED, font=F_SMALL, justify="center")
            return
        n = len(self.tokens)
        cols = 3
        cell_w, cell_h = w/cols, h/max(1, (n+cols-1)//cols)
        for i, tok in enumerate(self.tokens):
            col, row = i % cols, i // cols
            cx = cell_w*col + cell_w/2
            base_y = cell_h*row + cell_h - 14
            selected = (i == self.selected_idx)
            stem_h = 26 if selected else 18
            c.create_line(cx, base_y, cx, base_y-stem_h, fill=SAGE, width=2)
            c.create_polygon(cx, base_y-stem_h*0.5, cx+10, base_y-stem_h*0.6, cx, base_y-stem_h*0.35,
                             fill=MINT, outline=SAGE, smooth=True)
            node_r = 8 if selected else 6
            node = c.create_oval(cx-node_r, base_y-stem_h-node_r, cx+node_r, base_y-stem_h+node_r,
                                 fill=GOLD if selected else PEACH, outline=SAGE)
            c.create_text(cx, base_y-stem_h-node_r-8, text=tok, font=("Segoe UI", 8, "bold"), fill=TEXT)
            self.sprout_hits[node] = i

    def _on_sprout_click(self, event):
        item = self.sprout_canvas.find_closest(event.x, event.y)
        idx = self.sprout_hits.get(item[0]) if item else None
        if idx is None:
            return
        self.selected_idx = idx
        self._draw_sprouts()
        self._update_inspector(idx)
        self._draw_neural_tree()

    # ---------------- NEURAL TREE ----------------
    def _build_neural_tree(self):
        panel = tk.Frame(self, bg=PEARL)
        panel.place(relx=0.25, rely=0.13, relwidth=0.5, relheight=0.78)
        tk.Label(panel, text="THE NEURAL TREE", font=F_LABEL, bg=PEARL, fg=GREEN_TXT).pack(pady=(0, 4))
        self.tree_canvas = tk.Canvas(panel, bg=WHITE, highlightbackground=BORDER, highlightthickness=1)
        self.tree_canvas.pack(fill="both", expand=True)
        self.tree_canvas.bind("<Configure>", lambda e: self._draw_neural_tree())

    def _draw_neural_tree(self):
        c = self.tree_canvas
        c.delete("all")
        w, h = c.winfo_width() or 600, c.winfo_height() or 500
        cx, base_y = w/2, h*0.72
        stage = self.grow_stage

        data = build_dynamic_result(self.current_task, self.tokens)
        c.create_text(cx, 22, text="PREDICTION BLOOM", font=("Segoe UI", 9, "bold"), fill=GREEN_TXT)
        if stage >= 6:
            c.create_text(cx, 40, text=f"{data['label']} · {data['confidence']}%", font=F_SMALL, fill=GOLD)

        trunk_h = min(1, stage/3) * (h*0.38)
        top_y = base_y - trunk_h
        c.create_line(cx, base_y, cx, top_y, fill=SAGE, width=6, capstyle="round")

        # roots
        if stage >= 1:
            root_frac = min(1, stage/2)
            n_roots = 5
            for i in range(n_roots):
                ang = math.pi*0.15 + (math.pi*0.7)*(i/(n_roots-1))
                rl = (h*0.16) * root_frac
                rx = cx + math.cos(ang) * rl
                ry = base_y + math.sin(ang) * rl
                c.create_line(cx, base_y, rx, ry, fill=MINT, width=2)
                if stage >= 3 and self.selected_idx is not None:
                    vec = pseudo_vector(self.tokens[self.selected_idx])
                    if i < len(vec):
                        c.create_text(rx, ry+10, text=f"{vec[i]:+.2f}", font=F_SMALL, fill=SAGE)
            c.create_text(cx, base_y + h*0.16*root_frac + 24, text="EMBEDDING ROOTS", font=F_SMALL, fill=MUTED)

        # branches + blossom nodes
        if stage >= 4:
            branch_frac = min(1, (stage-3)/2)
            colors = [LAVENDER, AQUA, PEACH, GOLD]
            n_branch = 4
            for i in range(n_branch):
                ang = -math.pi/2 + (math.pi*0.55)*((i/(n_branch-1)) - 0.5)
                bl = (h*0.22) * branch_frac
                bx = cx + math.sin(ang) * bl
                by = top_y - math.cos(ang) * bl
                c.create_line(cx, top_y, bx, by, fill=SAGE, width=2)
                r = 9 if stage >= 6 else 5
                c.create_oval(bx-r, by-r, bx+r, by+r, fill=colors[i % len(colors)], outline=SAGE)

        # final flower forming at very top
        if stage >= 6:
            conf = data["confidence"]
            n_pet = max(3, min(8, round(conf/15)))
            length = 14 + conf*0.12
            for k in range(n_pet):
                ang = 2*math.pi*k/n_pet
                pts = petal_points(cx, top_y-6, ang, length, length*0.55)
                c.create_polygon(pts, smooth=True, fill=BLUSH, outline=PEACH)
            c.create_oval(cx-9, top_y-15, cx+9, top_y+3, fill=GOLD, outline=PEACH)

    # ---------------- INSPECTOR ----------------
    def _build_inspector(self):
        panel = tk.Frame(self, bg=WHITE, highlightbackground=BORDER, highlightthickness=1)
        panel.place(relx=0.77, rely=0.13, relwidth=0.21, relheight=0.34)
        tk.Label(panel, text="SPECIMEN INSPECTOR", font=F_LABEL, bg=WHITE, fg=GOLD).pack(anchor="w", padx=14, pady=(12, 8))
        self.inspector_text = tk.Label(panel, text="Click a sprout to\ninspect its specimen.",
                                        font=F_BODY, bg=WHITE, fg=TEXT, justify="left", anchor="nw")
        self.inspector_text.pack(anchor="w", padx=14, fill="both", expand=True)

    def _update_inspector(self, idx):
        word = self.tokens[idx]
        prev_w = self.tokens[idx-1] if idx > 0 else "—"
        next_w = self.tokens[idx+1] if idx < len(self.tokens)-1 else "—"
        vec = pseudo_vector(word, 3)
        act = pseudo_activation(word)
        txt = (f"TOKEN\n{word}\n\n"
               f"TOKEN ID\nT-{idx+1:03d}\n\n"
               f"POSITION\n{idx+1:02d}\n\n"
               f"CONTEXT\n{prev_w} | {word} | {next_w}\n\n"
               f"EMBEDDING\n{vec[0]}  {vec[1]}  {vec[2]}\n\n"
               f"ACTIVATION\n{act}")
        self.inspector_text.configure(text=txt)

    # ---------------- PREDICTION FLOWER ----------------
    def _build_prediction(self):
        panel = tk.Frame(self, bg=WHITE, highlightbackground=BORDER, highlightthickness=1)
        panel.place(relx=0.77, rely=0.49, relwidth=0.21, relheight=0.42)
        tk.Label(panel, text="PREDICTION", font=F_LABEL, bg=WHITE, fg="#C97A7A").pack(pady=(12, 4))
        self.pred_canvas = tk.Canvas(panel, bg=WHITE, highlightthickness=0)
        self.pred_canvas.pack(fill="both", expand=True)
        self.pred_canvas.bind("<Configure>", lambda e: self._draw_prediction())
        self.pred_label = tk.Label(panel, text="", font=("Segoe UI", 10, "bold"), bg=WHITE, fg=TEXT)
        self.pred_label.pack()
        tk.Label(panel, text="DEMO MODE", font=F_SMALL, bg=WHITE, fg=MUTED).pack(pady=(0, 10))

    def _draw_prediction(self):
        c = self.pred_canvas
        c.delete("all")
        w, h = c.winfo_width() or 260, c.winfo_height() or 200
        cx, cy = w/2, h/2
        data = build_dynamic_result(self.current_task, self.tokens)
        conf = data["confidence"]
        n_pet = 4 if conf < 60 else 6
        length = 18 + conf*0.5
        for k in range(n_pet):
            ang = 2*math.pi*k/n_pet
            pts = petal_points(cx, cy, ang, length, length*0.6)
            c.create_polygon(pts, smooth=True, fill=BLUSH, outline=PEACH, width=1.5)
        r = 12 + conf*0.08
        c.create_oval(cx-r, cy-r, cx+r, cy+r, fill=GOLD, outline=PEACH)
        label_text = data['label']
        if data.get('extra'):
            label_text += f"\n{data['extra']}"
        self.pred_label.configure(text=f"{label_text} · {conf}%")

    # ---------------- PIPELINE STRIP ----------------
    def _build_pipeline_strip(self):
        strip = tk.Frame(self, bg=PEARL)
        strip.place(relx=0.5, rely=0.965, relwidth=0.7, anchor="s")
        row = tk.Frame(strip, bg=PEARL)
        row.pack()
        for i, stage in enumerate(EDU):
            f = tk.Frame(row, bg=PEARL)
            f.pack(side="left", padx=10)
            dot = tk.Canvas(f, width=10, height=10, bg=PEARL, highlightthickness=0)
            dot.create_oval(1, 1, 9, 9, fill=SAGE, outline="")
            dot.pack()
            tk.Label(f, text=stage, font=("Segoe UI", 7, "bold"), bg=PEARL, fg=GREEN_TXT).pack()
            if i < len(EDU)-1:
                tk.Label(row, text="→", font=("Segoe UI", 8), bg=PEARL, fg=MUTED).pack(side="left")

    # ---------------- GROW / LOAD / RESET ----------------
    def load_sentence(self, sentence):
        self.seed_var.set(sentence)
        self.grow_model()

    def grow_model(self):
        text = self.seed_var.get().strip().rstrip(".!?")
        if not text:
            return
        self.tokens = text.split()
        self.selected_idx = None
        self.grow_stage = 0
        self._draw_sprouts()
        self._draw_neural_tree()

        def step(i=0):
            self.grow_stage = i
            self._draw_neural_tree()
            if i in (2, 3):
                self._draw_sprouts()
            if i >= 6:
                self._draw_prediction()
                self.selected_idx = 0
                self._draw_sprouts()
                self._update_inspector(0)
                return
            self.after(280, lambda: step(i+1))
        step()

    def reset_ecosystem(self):
        self.tokens = []
        self.selected_idx = None
        self.grow_stage = 0
        self._draw_sprouts()
        self._draw_neural_tree()
        self.pred_canvas.delete("all")
        self.pred_label.configure(text="")
        self.inspector_text.configure(text="Click a sprout to\ninspect its specimen.")


if __name__ == "__main__":
    app = NeuralBloomApp()
    app.mainloop()