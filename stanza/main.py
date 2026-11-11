import tkinter as tk
import threading
import random
import stanza

# Load the Stanza pipeline once at startup.
# First run downloads the model — after that it loads fast.
print("Loading Stanza pipeline...")
NLP = stanza.Pipeline(lang='en', processors='tokenize,pos,lemma,depparse,ner', verbose=False)

# ---------- Theme colors ----------
BG = "#eef1f6"
PANEL = "#ffffff"
BORDER = "#d7dde5"
TEXT = "#1c2430"
MUTED = "#7c8798"
BLUE = "#2f5fa8"
BLUE_BG = "#eaf1fb"
GREEN = "#1f8b5c"
GREEN_BG = "#e9f7f0"
ORANGE = "#c97a1f"
ORANGE_BG = "#fbf1e2"
RED = "#c23b4e"
RED_BG = "#fbeaed"
PURPLE = "#7a4fb0"
PURPLE_BG = "#f2ecfa"

FONT_MONO_BOLD = ("Courier New", 10, "bold")
FONT_TITLE = ("Arial", 20, "bold")


class StanzaForensicsApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("STANZA — NLP Forensics Lab")
        self.geometry("1000x750")
        self.configure(bg=BG)

        self.sentence_data = None
        self.selected_id = None
        self.card_items = {}

        self._build_header()
        self._build_input_section()
        self._build_pipeline_section()
        self._build_board_and_profile()
        self._build_footer()

    # ---------------- Header ----------------
    def _build_header(self):
        header = tk.Frame(self, bg=BG)
        header.pack(fill="x", padx=20, pady=(18, 6))

        left = tk.Frame(header, bg=BG)
        left.pack(side="left")
        tk.Label(left, text="STANZA", font=FONT_TITLE, bg=BG, fg="#101521").pack(anchor="w")
        tk.Label(left, text="NLP FORENSICS LAB — LINGUISTIC EVIDENCE ANALYSIS SYSTEM",
                 font=("Courier New", 9), bg=BG, fg=MUTED).pack(anchor="w")

        right = tk.Frame(header, bg=BG)
        right.pack(side="right")
        row1 = tk.Frame(right, bg=BG)
        row1.pack(anchor="e")
        tk.Label(row1, text="●", fg=GREEN, bg=BG, font=("Courier New", 9)).pack(side="left")
        tk.Label(row1, text=" SYSTEM ONLINE", fg=TEXT, bg=BG, font=("Courier New", 9)).pack(side="left")

        self.case_id_var = tk.StringVar(value="CASE ID: STZ-2048")
        tk.Label(right, textvariable=self.case_id_var, fg=BLUE, bg=BG,
                 font=("Courier New", 9)).pack(anchor="e")

        self.status_var = tk.StringVar(value="ANALYSIS STATUS: READY")
        self.status_label = tk.Label(right, textvariable=self.status_var, fg=ORANGE, bg=BG,
                                      font=("Courier New", 9, "bold"))
        self.status_label.pack(anchor="e")

    # ---------------- Input ----------------
    def _build_input_section(self):
        section = self._panel()
        tk.Label(section, text="NEW CASE / EVIDENCE INPUT", font=("Courier New", 9, "bold"),
                 bg=PANEL, fg=MUTED).pack(anchor="w", pady=(0, 8))

        self.input_entry = tk.Entry(section, font=("Arial", 12), relief="solid", bd=1)
        self.input_entry.insert(0, "Ali visited Hyderabad University yesterday.")
        self.input_entry.pack(fill="x", ipady=6)

        btn_row = tk.Frame(section, bg=PANEL)
        btn_row.pack(anchor="w", pady=(10, 0))

        self.open_btn = tk.Button(btn_row, text="OPEN CASE", font=FONT_MONO_BOLD,
                                   fg=GREEN, bg=PANEL, activebackground=GREEN_BG,
                                   relief="solid", bd=1, padx=14, pady=4,
                                   command=self.start_pipeline)
        self.open_btn.pack(side="left", padx=(0, 8))

        self.clear_btn = tk.Button(btn_row, text="CLEAR EVIDENCE", font=FONT_MONO_BOLD,
                                    fg=RED, bg=PANEL, activebackground=RED_BG,
                                    relief="solid", bd=1, padx=14, pady=4,
                                    command=self.clear_case)
        self.clear_btn.pack(side="left")

    # ---------------- Pipeline ----------------
    def _build_pipeline_section(self):
        section = self._panel()
        tk.Label(section, text="INVESTIGATION PIPELINE", font=("Courier New", 9, "bold"),
                 bg=PANEL, fg=MUTED).pack(anchor="w", pady=(0, 10))

        row = tk.Frame(section, bg=PANEL)
        row.pack(fill="x")

        self.stage_names = ["TOKEN", "POS", "LEMMA", "DEPEND", "ENTITY", "REPORT"]
        self.stage_boxes = {}
        for name in self.stage_names:
            box = tk.Frame(row, bg=PANEL, highlightbackground=BORDER, highlightthickness=1.5, bd=0)
            box.pack(side="left", expand=True, fill="x", padx=4)
            lbl = tk.Label(box, text=name, font=FONT_MONO_BOLD, bg=PANEL, fg=BLUE)
            lbl.pack(pady=(6, 0))
            stat = tk.Label(box, text="● READY", font=("Courier New", 8), bg=PANEL, fg=BLUE)
            stat.pack(pady=(0, 6))
            self.stage_boxes[name] = (box, lbl, stat)

    def set_stage(self, name, state):
        box, lbl, stat = self.stage_boxes[name]
        colors = {
            "pending": (BORDER, BLUE, "READY", PANEL),
            "scan":    (ORANGE, ORANGE, "SCAN", ORANGE_BG),
            "done":    (GREEN, GREEN, "DONE", GREEN_BG),
        }
        border, color, text, bg = colors[state]
        box.configure(bg=bg, highlightbackground=border)
        lbl.configure(fg=color, bg=bg)
        stat.configure(fg=color, bg=bg, text=f"● {text}")

    # ---------------- Board + Profile ----------------
    def _build_board_and_profile(self):
        wrap = tk.Frame(self, bg=BG)
        wrap.pack(fill="both", expand=True, padx=20, pady=6)

        board_panel = tk.Frame(wrap, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        board_panel.pack(side="left", fill="both", expand=True, padx=(0, 8))
        tk.Label(board_panel, text="FORENSIC EVIDENCE BOARD", font=FONT_MONO_BOLD,
                 bg=PANEL, fg=TEXT).pack(anchor="w", padx=14, pady=(12, 8))

        self.board_canvas = tk.Canvas(board_panel, bg=PANEL, height=220, highlightthickness=0)
        self.board_canvas.pack(fill="both", expand=True, padx=14, pady=(0, 4))
        self.board_canvas.bind("<Button-1>", self.on_canvas_click)

        self.caption_var = tk.StringVar(value="")
        tk.Label(board_panel, textvariable=self.caption_var, font=("Courier New", 8),
                 bg=PANEL, fg=MUTED).pack(pady=(0, 12))

        right_col = tk.Frame(wrap, bg=BG)
        right_col.pack(side="left", fill="y")

        profile_panel = tk.Frame(right_col, bg=PANEL, highlightbackground=BORDER, highlightthickness=1, width=280)
        profile_panel.pack(fill="x")
        self.profile_title_var = tk.StringVar(value="EVIDENCE PROFILE")
        tk.Label(profile_panel, textvariable=self.profile_title_var, font=FONT_MONO_BOLD,
                 bg=PANEL, fg=TEXT).pack(anchor="w", padx=14, pady=(12, 8))
        self.profile_text = tk.Label(profile_panel, text="TOKEN: —", font=("Courier New", 10),
                                      bg=PANEL, fg=TEXT, justify="left", anchor="w")
        self.profile_text.pack(anchor="w", padx=14, pady=(0, 14))

        entity_panel = tk.Frame(right_col, bg=PANEL, highlightbackground=BORDER, highlightthickness=1, width=280)
        entity_panel.pack(fill="x", pady=(12, 0))
        tk.Label(entity_panel, text="ENTITY DISCOVERY", font=FONT_MONO_BOLD,
                 bg=PANEL, fg=TEXT).pack(anchor="w", padx=14, pady=(12, 8))
        self.pills_frame = tk.Frame(entity_panel, bg=PANEL)
        self.pills_frame.pack(anchor="w", padx=14, pady=(0, 14), fill="x")

    # ---------------- Footer ----------------
    def _build_footer(self):
        footer = tk.Frame(self, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        footer.pack(fill="x", padx=20, pady=(6, 18))
        self.footer_vars = {
            "TOKENS": tk.StringVar(value="0"),
            "ENTITIES": tk.StringVar(value="0"),
            "RELATIONS": tk.StringVar(value="0"),
            "CASE STATUS": tk.StringVar(value="PENDING"),
        }
        for key, var in self.footer_vars.items():
            f = tk.Frame(footer, bg=PANEL)
            f.pack(side="left", expand=True, pady=10)
            tk.Label(f, text=f"{key}: ", font=("Courier New", 9), bg=PANEL, fg=MUTED).pack(side="left")
            tk.Label(f, textvariable=var, font=("Courier New", 9, "bold"), bg=PANEL, fg=TEXT).pack(side="left")

    # ---------------- Helpers ----------------
    def _panel(self):
        section = tk.Frame(self, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        section.pack(fill="x", padx=20, pady=6)
        inner = tk.Frame(section, bg=PANEL)
        inner.pack(fill="x", padx=16, pady=14)
        return inner

    # ---------------- Pipeline execution ----------------
    def start_pipeline(self):
        text = self.input_entry.get().strip()
        if not text:
            return
        self.open_btn.configure(state="disabled")
        self.case_id_var.set(f"CASE ID: STZ-{random.randint(2000, 2999)}")
        self.status_var.set("ANALYSIS STATUS: PROCESSING")
        self.status_label.configure(fg=BLUE)
        for name in self.stage_names:
            self.set_stage(name, "pending")
        self.selected_id = None

        threading.Thread(target=self._run_stanza, args=(text,), daemon=True).start()

    def _run_stanza(self, text):
        doc = NLP(text)
        sent = doc.sentences[0]
        tokens = []
        for i, w in enumerate(sent.words):
            tokens.append({
                "id": i,
                "text": w.text,
                "pos": w.upos,
                "lemma": w.lemma,
                "head": w.head,   # 1-indexed, 0 = root
                "dep": w.deprel,
                "entity": None,
            })

        # attach NER labels (crude word-level match against entity spans)
        for ent in sent.ents:
            ent_words = ent.text.split()
            for tok in tokens:
                if tok["text"] in ent_words:
                    tok["entity"] = ent.type

        root_idx = next((t["id"] for t in tokens if t["head"] == 0), 0)
        for t in tokens:
            t["head_text"] = "ROOT" if t["head"] == 0 else tokens[t["head"] - 1]["text"]

        self.sentence_data = {"tokens": tokens, "root_idx": root_idx}
        self.after(0, self._animate_stages)

    def _animate_stages(self):
        def step(i=0):
            if i >= len(self.stage_names):
                self._finish_pipeline()
                return
            name = self.stage_names[i]
            self.set_stage(name, "scan")
            self.after(280, lambda: (self.set_stage(name, "done"),
                                      self.after(120, lambda: step(i + 1))))
        step()

    def _finish_pipeline(self):
        self.status_var.set("ANALYSIS STATUS: COMPLETE")
        self.status_label.configure(fg=GREEN)
        self.draw_board()
        root_tok = self.sentence_data["tokens"][self.sentence_data["root_idx"]]
        self.selected_id = root_tok["id"]
        self.show_profile(root_tok)
        self.show_entities()
        self.update_footer()
        self.open_btn.configure(state="normal")

    # ---------------- Board drawing ----------------
    def draw_board(self):
        c = self.board_canvas
        c.delete("all")
        self.card_items = {}
        tokens = self.sentence_data["tokens"]
        root_idx = self.sentence_data["root_idx"]

        card_w, card_h, gap = 100, 46, 16
        x, y = 14, 14
        positions = {}

        for t in tokens:
            is_root = t["id"] == root_idx
            border = ORANGE if is_root else BLUE
            fill = PANEL
            if t["id"] == self.selected_id:
                fill = ORANGE_BG if is_root else BLUE_BG
            rect = c.create_rectangle(x, y, x + card_w, y + card_h, outline=border, width=1.5, fill=fill)
            label = f'E-0{t["id"] + 1}' + (" · ROOT" if is_root else "")
            c.create_text(x + card_w / 2, y + 14, text=label, font=("Courier New", 7),
                           fill=ORANGE if is_root else MUTED)
            c.create_text(x + card_w / 2, y + 30, text=t["text"], font=FONT_MONO_BOLD,
                           fill=ORANGE if is_root else TEXT)
            self.card_items[rect] = t["id"]
            positions[t["id"]] = (x + card_w / 2, y + card_h)
            x += card_w + gap

        root_x, root_bottom = positions[root_idx]
        bus_y = root_bottom + 20
        for t in tokens:
            if t["id"] == root_idx:
                continue
            cx, cy = positions[t["id"]]
            c.create_line(cx, cy, cx, bus_y, fill="#c3cbd6")
            c.create_line(cx, bus_y, root_x, bus_y, fill="#c3cbd6")
        c.create_line(root_x, bus_y, root_x, root_bottom, fill="#c3cbd6")

        self.caption_var.set(f"EVIDENCE GRID — {len(tokens)} ITEMS SCANNED")

    def on_canvas_click(self, event):
        item = self.board_canvas.find_closest(event.x, event.y)
        if not item:
            return
        bbox = self.board_canvas.bbox(item[0])
        if not bbox or not (bbox[0] <= event.x <= bbox[2] and bbox[1] <= event.y <= bbox[3]):
            return
        tid = self.card_items.get(item[0])
        if tid is None:
            return
        self.selected_id = tid
        self.draw_board()
        tok = next(t for t in self.sentence_data["tokens"] if t["id"] == tid)
        self.show_profile(tok)

    # ---------------- Profile / entities / footer ----------------
    def show_profile(self, t):
        self.profile_title_var.set(f'EVIDENCE PROFILE — E-0{t["id"] + 1}')
        text = (f'TOKEN: {t["text"]}\n'
                f'POS: {t["pos"]}     LEMMA: {t["lemma"]}\n'
                f'HEAD: {t["head_text"]}     DEP: {t["dep"]}\n'
                f'ENTITY: {t["entity"] or "—"}')
        self.profile_text.configure(text=text)

    def show_entities(self):
        for widget in self.pills_frame.winfo_children():
            widget.destroy()
        ents = [t for t in self.sentence_data["tokens"] if t["entity"]]
        if not ents:
            tk.Label(self.pills_frame, text="no entities found", font=("Courier New", 9),
                     bg=PANEL, fg=MUTED).pack(anchor="w")
            return
        color_map = {
            "PERSON": (GREEN, GREEN_BG),
            "GPE": (BLUE, BLUE_BG), "LOC": (BLUE, BLUE_BG),
            "ORG": (PURPLE, PURPLE_BG),
        }
        row = tk.Frame(self.pills_frame, bg=PANEL)
        row.pack(anchor="w", fill="x")
        for t in ents:
            fg, bg = color_map.get(t["entity"], (MUTED, "#f2f3f6"))
            label = "LOC" if t["entity"] == "GPE" else t["entity"]
            pill = tk.Label(row, text=f' {label}: {t["text"]} ', font=("Courier New", 8, "bold"),
                             fg=fg, bg=bg, relief="solid", bd=1)
            pill.pack(side="left", padx=3, pady=3)

    def update_footer(self):
        tokens = self.sentence_data["tokens"]
        self.footer_vars["TOKENS"].set(str(len(tokens)))
        self.footer_vars["ENTITIES"].set(str(len([t for t in tokens if t["entity"]])))
        self.footer_vars["RELATIONS"].set(str(len(tokens) - 1))
        self.footer_vars["CASE STATUS"].set("COMPLETE")

    # ---------------- Clear ----------------
    def clear_case(self):
        self.sentence_data = None
        self.selected_id = None
        self.board_canvas.delete("all")
        self.caption_var.set("")
        for name in self.stage_names:
            self.set_stage(name, "pending")
        self.status_var.set("ANALYSIS STATUS: READY")
        self.status_label.configure(fg=ORANGE)
        self.profile_title_var.set("EVIDENCE PROFILE")
        self.profile_text.configure(text="TOKEN: —")
        for widget in self.pills_frame.winfo_children():
            widget.destroy()
        tk.Label(self.pills_frame, text="no entities yet", font=("Courier New", 9),
                 bg=PANEL, fg=MUTED).pack(anchor="w")
        for key in self.footer_vars:
            self.footer_vars[key].set("0" if key != "CASE STATUS" else "PENDING")


if __name__ == "__main__":
    app = StanzaForensicsApp()
    app.mainloop()