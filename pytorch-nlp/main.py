#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NEURAL THEATRE  --  WHERE EVERY WORD TAKES A ROLE
PyTorch NLP concepts presented as a futuristic theatrical performance.

Pure Python 3 + Tkinter + Tkinter Canvas + standard library only.
No images, no web technology, no external assets, no real model weights.
All NLP results are clearly labelled DEMO MODE.

Run:  python main.py
"""

import tkinter as tk
import math
import random
import re
import hashlib


# ----------------------------------------------------------------------------
#  PALETTE
# ----------------------------------------------------------------------------

IVORY       = "#F7F1E8"
CREAM       = "#FFF9F0"
BURGUNDY    = "#4A1825"
WINE        = "#6E2639"
WINE_LIGHT  = "#8A3450"
CHAMPAGNE   = "#D8B56A"
GOLD_SOFT   = "#EBD49B"
PLUM        = "#5B456B"
PLUM_DEEP   = "#3B2C47"
CORAL       = "#D98E88"
LAVENDER    = "#B9A6D9"
CHARCOAL    = "#29252A"
STAGE_BACK  = "#2C1C2B"
STAGE_DEEP  = "#1E1320"
FLOOR_NEAR  = "#6A4234"
FLOOR_FAR   = "#3A2230"
INK         = "#33252C"
MUTED       = "#9A8894"

F_DISPLAY = "Georgia"
F_BODY    = "Segoe UI"
F_MONO    = "Consolas"


# ----------------------------------------------------------------------------
#  SMALL COLOUR HELPERS
# ----------------------------------------------------------------------------

def hex_to_rgb(c):
    c = c.lstrip("#")
    return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)


def rgb_to_hex(r, g, b):
    clamp = lambda v: max(0, min(255, int(round(v))))
    return "#%02x%02x%02x" % (clamp(r), clamp(g), clamp(b))


def mix(c1, c2, t):
    """Blend two colours. t = 0 gives c1, t = 1 gives c2."""
    r1, g1, b1 = hex_to_rgb(c1)
    r2, g2, b2 = hex_to_rgb(c2)
    return rgb_to_hex(r1 + (r2 - r1) * t, g1 + (g2 - g1) * t, b1 + (b2 - b1) * t)


def lighten(c, t):
    return mix(c, "#FFFFFF", t)


def darken(c, t):
    return mix(c, "#000000", t)


def ease(t):
    """Smooth start / smooth stop."""
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def vgradient(cv, x0, y0, x1, y1, c_top, c_bottom, steps=48, tags=()):
    """Vertical gradient painted as thin rectangles."""
    h = (y1 - y0) / float(steps)
    for i in range(steps):
        col = mix(c_top, c_bottom, i / float(steps - 1))
        cv.create_rectangle(x0, y0 + i * h, x1, y0 + (i + 1) * h + 1,
                            fill=col, outline=col, tags=tags)


def rounded(cv, x0, y0, x1, y1, r=10, **kw):
    """Rounded rectangle built from a smoothed polygon."""
    pts = [x0 + r, y0, x1 - r, y0, x1, y0, x1, y0 + r,
           x1, y1 - r, x1, y1, x1 - r, y1, x0 + r, y1,
           x0, y1, x0, y1 - r, x0, y0 + r, x0, y0]
    return cv.create_polygon(pts, smooth=True, **kw)


# ----------------------------------------------------------------------------
#  DEMO NLP  (no real model -- deterministic fake data, clearly labelled)
# ----------------------------------------------------------------------------

POSITIVE_WORDS = {"good", "great", "happy", "love", "warm", "calm", "bright",
                  "soft", "quiet", "kind", "best", "beautiful", "tired", "rest"}
NEGATIVE_WORDS = {"bad", "sad", "angry", "cold", "dark", "hate", "worst",
                  "broken", "afraid", "lost", "hard", "tired"}

STOP_WORDS = {"the", "a", "an", "on", "in", "at", "of", "to", "is", "was",
              "it", "and", "because", "so", "that", "this", "for", "with"}

ROLE_BY_KIND = {
    "lead": "Lead Token",
    "support": "Supporting Token",
    "context": "Contextual Token",
    "link": "Connective Token",
    "punct": "Stage Direction",
}


class DemoNLP:
    """Produces believable, deterministic, clearly-simulated NLP output."""

    @staticmethod
    def tokenize(text):
        return re.findall(r"[A-Za-z']+|[.,!?;:]", text)

    @staticmethod
    def tensor_for(token, dim=6):
        """Stable pseudo-tensor derived from the token itself."""
        seed = int(hashlib.md5(token.lower().encode("utf-8")).hexdigest()[:8], 16)
        rnd = random.Random(seed)
        return [round(rnd.uniform(-1.0, 1.0), 2) for _ in range(dim)]

    @staticmethod
    def activation_for(token):
        seed = int(hashlib.md5(("a" + token.lower()).encode("utf-8")).hexdigest()[:8], 16)
        return round(0.35 + (seed % 1000) / 1000.0 * 0.62, 2)

    @staticmethod
    def kind_of(token):
        low = token.lower()
        if re.fullmatch(r"[.,!?;:]", token):
            return "punct"
        if low in ("because", "and", "so", "but", "that"):
            return "link"
        if low in STOP_WORDS:
            return "context"
        if len(low) >= 5:
            return "lead"
        return "support"

    @staticmethod
    def classify(tokens):
        low = [t.lower() for t in tokens]
        pos = sum(1 for t in low if t in POSITIVE_WORDS)
        neg = sum(1 for t in low if t in NEGATIVE_WORDS)
        if pos >= neg:
            label, base = "POSITIVE", 0.72 + 0.05 * pos
        else:
            label, base = "NEGATIVE", 0.70 + 0.05 * neg
        conf = min(0.974, base + (len(tokens) % 7) * 0.012)
        return label, round(conf * 100, 1)

    @staticmethod
    def sentiment(tokens):
        label, conf = DemoNLP.classify(tokens)
        return label, round(conf / 100.0, 2)

    @staticmethod
    def ner(tokens):
        found = []
        known_loc = {"pakistan", "sindh", "hyderabad", "karachi", "lahore", "london"}
        for i, t in enumerate(tokens):
            if t.lower() in known_loc:
                found.append(("LOCATION", t))
            elif t[:1].isupper() and i > 0 and t.lower() not in STOP_WORDS:
                found.append(("PERSON", t))
        if not found:
            found = [("PERSON", "Ali"), ("LOCATION", "Pakistan")]
        return found[:3]

    @staticmethod
    def generate(tokens):
        if not tokens:
            return "The stage waits for a script."
        core = [t for t in tokens if t.isalpha()][:6]
        tail = ["quietly", "again", "under the warm light"]
        seed = int(hashlib.md5(" ".join(core).encode("utf-8")).hexdigest()[:6], 16)
        return " ".join(core) + " " + tail[seed % len(tail)] + "."


# ----------------------------------------------------------------------------
#  ACTOR
# ----------------------------------------------------------------------------

class Actor:
    """One token, living on the stage as a performer."""

    def __init__(self, index, token):
        self.index = index
        self.token = token
        self.tid = "T-%03d" % (index + 1)
        self.kind = DemoNLP.kind_of(token)
        self.role = ROLE_BY_KIND[self.kind]
        self.tensor = DemoNLP.tensor_for(token)
        self.activation = DemoNLP.activation_for(token)
        self.layer = (index % 4) + 1

        self.x = 0.0
        self.base_y = 0.0
        self.scale = 0.0        # entrance animation 0 -> 1
        self.glow = 0.0         # activation glow 0 -> 1
        self.selected = False
        self.on_stage = False

    @property
    def body_color(self):
        table = {"lead": CHAMPAGNE, "support": CORAL,
                 "context": LAVENDER, "link": GOLD_SOFT, "punct": MUTED}
        return table[self.kind]


# ----------------------------------------------------------------------------
#  NEURAL STAGE  --  the hero canvas
# ----------------------------------------------------------------------------

class NeuralStage(tk.Canvas):

    def __init__(self, master, width, height, on_select):
        tk.Canvas.__init__(self, master, width=width, height=height,
                           bg=IVORY, highlightthickness=0)
        self.W = width
        self.H = height
        self.on_select = on_select

        # stage opening (inside the proscenium frame)
        self.fx0 = 18
        self.fy0 = 12
        self.fx1 = width - 18
        self.fy1 = height - 10
        self.in_x0 = self.fx0 + 16
        self.in_y0 = self.fy0 + 62          # marquee sits above this
        self.in_x1 = self.fx1 - 16
        self.in_y1 = self.fy1 - 12

        self.floor_top = self.in_y0 + 172
        self.base_y = self.floor_top + 16
        self.arch_x = (self.in_x0 + self.in_x1) / 2.0
        self.arch_y = self.in_y0 + 78

        self.actors = []
        self.curtain = 0.0          # 0 = closed-ish, 1 = fully open
        self.curtain_target = 0.0
        self.sweep = 0.0
        self.pulse = 0.0
        self.stage_glow = 0.0
        self.particles = []
        self.marquee_lit = 0
        self.marquee_total = 26
        self.result_title = "TONIGHT'S RESULT"
        self.result_main = ""
        self.result_sub = "PRESS  RUN PERFORMANCE"
        self.reveal = 0.0
        self.status_line = "CURTAIN DOWN"

        self.draw_static()
        self.bind("<Button-1>", self._click)
        self._tick()

    # -- static scenery ------------------------------------------------------

    def draw_static(self):
        self.delete("bg")
        W, H = self.W, self.H

        # outer house wall
        vgradient(self, 0, 0, W, H, CREAM, "#EFE2D4", 30, tags=("bg",))

        # stage void
        vgradient(self, self.in_x0, self.in_y0, self.in_x1, self.in_y1,
                  STAGE_DEEP, STAGE_BACK, 40, tags=("bg",))

        # upstage arch -- the doorway to backstage
        ax, ay = self.arch_x, self.arch_y
        self.create_oval(ax - 92, ay - 56, ax + 92, ay + 72,
                         fill=darken(PLUM_DEEP, 0.25), outline="", tags=("bg",))
        self.create_oval(ax - 70, ay - 42, ax + 70, ay + 56,
                         fill=darken(PLUM, 0.35), outline=PLUM, tags=("bg",))
        self.create_oval(ax - 48, ay - 28, ax + 48, ay + 40,
                         fill=darken(PLUM_DEEP, 0.45), outline="", tags=("bg",))
        for i in range(7):
            a = math.pi * (0.15 + 0.7 * i / 6.0)
            self.create_line(ax - 92 * math.cos(a), ay - 56 * math.sin(a),
                             ax - 70 * math.cos(a), ay - 42 * math.sin(a),
                             fill=mix(PLUM, CHAMPAGNE, 0.35), width=1, tags=("bg",))

        # stage floor in perspective
        self.create_polygon(self.in_x0, self.in_y1,
                            self.in_x1, self.in_y1,
                            self.in_x1 - 150, self.floor_top,
                            self.in_x0 + 150, self.floor_top,
                            fill=FLOOR_FAR, outline="", tags=("bg",))
        depth = self.in_y1 - self.floor_top
        for i in range(22):
            t = i / 21.0
            y = self.floor_top + depth * t
            inset = 150 * (1 - t)
            col = mix(FLOOR_FAR, FLOOR_NEAR, t * t)
            self.create_line(self.in_x0 + inset, y, self.in_x1 - inset, y,
                             fill=col, width=int(1 + 3 * t), tags=("bg",))
        # receding boards
        for k in range(-7, 8):
            xf = self.arch_x + k * 44
            xn = self.arch_x + k * 82
            self.create_line(xf, self.floor_top, xn, self.in_y1,
                             fill=mix(FLOOR_FAR, "#000000", 0.25), width=1, tags=("bg",))

        # atmospheric haze (stipple stands in for transparency)
        for i, (cy, rx, ry, st) in enumerate(
                [(self.in_y0 + 120, 460, 90, "gray12"),
                 (self.floor_top + 20, 560, 70, "gray12"),
                 (self.in_y0 + 60, 380, 60, "gray12")]):
            self.create_oval(self.arch_x - rx, cy - ry, self.arch_x + rx, cy + ry,
                             fill=LAVENDER, outline="", stipple=st, tags=("bg",))

        # overhead lighting rig
        rig_y = self.in_y0 + 12
        self.create_line(self.in_x0 + 30, rig_y, self.in_x1 - 30, rig_y,
                         fill=darken(CHARCOAL, 0.1), width=6, tags=("bg",))
        self.create_line(self.in_x0 + 30, rig_y + 5, self.in_x1 - 30, rig_y + 5,
                         fill=mix(CHARCOAL, CHAMPAGNE, 0.25), width=1, tags=("bg",))
        self.rig_lights = []
        for i in range(9):
            x = self.in_x0 + 70 + (self.in_x1 - self.in_x0 - 140) * i / 8.0
            self.create_line(x, rig_y, x, rig_y + 16, fill="#55484F", width=2, tags=("bg",))
            self.create_polygon(x - 11, rig_y + 16, x + 11, rig_y + 16,
                                x + 7, rig_y + 30, x - 7, rig_y + 30,
                                fill=darken(CHARCOAL, 0.05), outline=CHAMPAGNE,
                                tags=("bg",))
            self.rig_lights.append((x, rig_y + 30))

        # proscenium frame
        self.create_rectangle(self.fx0, self.fy0, self.fx1, self.fy1,
                              outline=BURGUNDY, width=3, tags=("bg",))
        vgradient(self, self.fx0, self.fy0, self.fx0 + 16, self.fy1,
                  WINE, BURGUNDY, 24, tags=("bg",))
        vgradient(self, self.fx1 - 16, self.fy0, self.fx1, self.fy1,
                  WINE, BURGUNDY, 24, tags=("bg",))
        vgradient(self, self.fx0, self.fy1 - 12, self.fx1, self.fy1,
                  BURGUNDY, darken(BURGUNDY, 0.3), 10, tags=("bg",))
        vgradient(self, self.fx0, self.fy0, self.fx1, self.fy0 + 58,
                  BURGUNDY, WINE, 20, tags=("bg",))
        # gold inlay
        self.create_rectangle(self.fx0 + 6, self.fy0 + 6, self.fx1 - 6, self.fy1 - 5,
                              outline=CHAMPAGNE, width=1, tags=("bg",))
        for x in (self.fx0 + 8, self.fx1 - 8):
            for y in (self.fy0 + 8, self.fy1 - 7):
                self.create_oval(x - 4, y - 4, x + 4, y + 4,
                                 fill=GOLD_SOFT, outline=BURGUNDY, tags=("bg",))

    # -- layout ---------------------------------------------------------------

    def set_actors(self, actors):
        self.actors = actors
        n = len(actors)
        if n == 0:
            return
        span_x = (self.in_x1 - self.in_x0) - 210
        rows = 1 if n <= 9 else 2
        per_row = int(math.ceil(n / float(rows)))
        for i, a in enumerate(actors):
            row = i // per_row
            col = i % per_row
            count = min(per_row, n - row * per_row)
            if count == 1:
                fx = 0.5
            else:
                fx = col / float(count - 1)
            a.x = self.in_x0 + 105 + span_x * fx
            arc = math.sin(fx * math.pi) * 10
            a.base_y = self.base_y + row * 54 - arc
            a.scale = 0.0
            a.glow = 0.0
            a.on_stage = False

    # -- interaction ----------------------------------------------------------

    def _click(self, ev):
        best, bd = None, 44
        for a in self.actors:
            if not a.on_stage:
                continue
            d = math.hypot(ev.x - a.x, ev.y - (a.base_y - 34))
            if d < bd:
                best, bd = a, d
        if best is not None:
            self.select(best.index)

    def select(self, index):
        for a in self.actors:
            a.selected = (a.index == index)
        for a in self.actors:
            if a.selected:
                self.on_select(a)
                return

    def selected_actor(self):
        for a in self.actors:
            if a.selected:
                return a
        return None

    # -- animation loop -------------------------------------------------------

    def _tick(self):
        # curtain easing
        if abs(self.curtain - self.curtain_target) > 0.002:
            self.curtain += (self.curtain_target - self.curtain) * 0.10
        else:
            self.curtain = self.curtain_target

        self.sweep = (self.sweep + 0.012) % 1.0
        self.pulse = (self.pulse + 0.06) % (math.pi * 2)

        # particles
        alive = []
        for p in self.particles:
            p["t"] += p["sp"]
            if p["t"] < 1.0:
                alive.append(p)
        self.particles = alive

        self.redraw_dynamic()
        self.after(40, self._tick)

    # -- dynamic layers -------------------------------------------------------

    def redraw_dynamic(self):
        self.delete("dyn")
        self.draw_stage_glow()
        self.draw_spotlights()
        self.draw_connections()
        for a in self.actors:
            if a.on_stage:
                self.draw_actor(a)
        self.draw_particles()
        self.draw_curtain()
        self.draw_marquee()
        self.draw_status()

    def draw_stage_glow(self):
        if self.stage_glow <= 0.01:
            return
        st = "gray25" if self.stage_glow > 0.5 else "gray12"
        self.create_rectangle(self.in_x0, self.in_y0, self.in_x1, self.in_y1,
                              fill=CHAMPAGNE, outline="", stipple=st, tags=("dyn",))

    def draw_spotlight(self, sx, sy, tx, ty, spread, color, strong=False):
        self.create_polygon(sx - 8, sy, sx + 8, sy,
                            tx + spread, ty, tx - spread, ty,
                            fill=color, outline="", smooth=False,
                            stipple="gray25" if strong else "gray12", tags=("dyn",))
        self.create_oval(tx - spread, ty - spread * 0.28,
                         tx + spread, ty + spread * 0.28,
                         fill=color, outline="", stipple="gray25" if strong else "gray12",
                         tags=("dyn",))

    def draw_spotlights(self):
        if self.curtain < 0.25:
            return
        # slow sweeping house light
        sweep_x = self.in_x0 + 120 + (self.in_x1 - self.in_x0 - 240) * \
            (0.5 + 0.5 * math.sin(self.sweep * math.pi * 2))
        rig = min(self.rig_lights, key=lambda p: abs(p[0] - sweep_x))
        self.draw_spotlight(rig[0], rig[1], sweep_x, self.base_y + 8, 58, LAVENDER)

        sel = self.selected_actor()
        if sel and sel.on_stage:
            rig = min(self.rig_lights, key=lambda p: abs(p[0] - sel.x))
            self.draw_spotlight(rig[0], rig[1], sel.x, sel.base_y + 6, 50,
                                GOLD_SOFT, strong=True)
        for a in self.actors:
            if a.on_stage and a.glow > 0.55 and not a.selected:
                rig = min(self.rig_lights, key=lambda p: abs(p[0] - a.x))
                self.draw_spotlight(rig[0], rig[1], a.x, a.base_y + 6, 34, CORAL)

    def draw_connections(self):
        sel = self.selected_actor()
        if not sel or not sel.on_stage:
            return
        for a in self.actors:
            if a is sel or not a.on_stage:
                continue
            if abs(a.index - sel.index) > 2 and a.kind != sel.kind:
                continue
            x1, y1 = sel.x, sel.base_y - 40
            x2, y2 = a.x, a.base_y - 40
            mx, my = (x1 + x2) / 2.0, min(y1, y2) - 42
            self.create_line(x1, y1, mx, my, x2, y2, smooth=True,
                             fill=mix(CHAMPAGNE, LAVENDER, 0.4), width=2,
                             tags=("dyn",))
            self.create_line(x1, y1, mx, my, x2, y2, smooth=True,
                             fill=CREAM, width=1, tags=("dyn",))

    def draw_actor(self, a):
        s = ease(a.scale)
        if s <= 0.02:
            return
        x, base = a.x, a.base_y
        h = 46 * s
        w = 15 * s
        if a.selected:
            h *= 1.14
            w *= 1.14
        pulse = 0.5 + 0.5 * math.sin(self.pulse + a.index)
        glow = a.glow * (0.65 + 0.35 * pulse)

        # pedestal
        self.create_oval(x - 26 * s, base - 7 * s, x + 26 * s, base + 9 * s,
                         fill=mix(FLOOR_NEAR, CHARCOAL, 0.45), outline="", tags=("dyn",))
        self.create_oval(x - 20 * s, base - 10 * s, x + 20 * s, base + 4 * s,
                         fill=mix(BURGUNDY, CHAMPAGNE, 0.18 + 0.4 * glow),
                         outline=CHAMPAGNE, tags=("dyn",))

        body = mix(a.body_color, "#FFFFFF", 0.15 + 0.5 * glow)
        edge = mix(body, CREAM, 0.5)

        # illuminated silhouette
        self.create_polygon(x - w, base - 6 * s,
                            x - w * 0.55, base - h,
                            x + w * 0.55, base - h,
                            x + w, base - 6 * s,
                            fill=body, outline=edge, smooth=True, tags=("dyn",))
        # inner light column
        self.create_line(x, base - 10 * s, x, base - h + 4,
                         fill=mix(CREAM, body, 0.3), width=max(1, int(3 * s)),
                         tags=("dyn",))
        # mask / head
        hr = 11 * s * (1.15 if a.selected else 1.0)
        hy = base - h - hr - 2
        self.create_polygon(x, hy - hr, x + hr, hy, x, hy + hr, x - hr, hy,
                            fill=mix(CREAM, body, 0.35), outline=CHAMPAGNE, tags=("dyn",))
        self.create_oval(x - hr * 0.35, hy - hr * 0.3, x + hr * 0.35, hy + hr * 0.3,
                         fill=mix(BURGUNDY, GOLD_SOFT, glow), outline="", tags=("dyn",))
        if glow > 0.3:
            self.create_oval(x - hr * 2.4, hy - hr * 2.4, x + hr * 2.4, hy + hr * 2.4,
                             outline=mix(CHAMPAGNE, CREAM, glow), width=1, tags=("dyn",))

        # tensor carried by the actor: tiny light columns on the pedestal rim
        for i, v in enumerate(a.tensor):
            bx = x - 15 + i * 6
            bh = 3 + abs(v) * 11 * a.glow
            self.create_line(bx, base + 7, bx, base + 7 - bh,
                             fill=mix(LAVENDER, GOLD_SOFT, (v + 1) / 2.0),
                             width=2, tags=("dyn",))

        if s > 0.85:
            self.create_text(x, base + 22, text=a.token.upper(),
                             font=(F_DISPLAY, 9, "bold"),
                             fill=CREAM if not a.selected else GOLD_SOFT, tags=("dyn",))
            self.create_text(x, base + 34, text=a.tid, font=(F_MONO, 7),
                             fill=mix(CREAM, STAGE_BACK, 0.45), tags=("dyn",))

    def draw_particles(self):
        for p in self.particles:
            t = ease(p["t"])
            x = (1 - t) ** 2 * p["x0"] + 2 * (1 - t) * t * p["cx"] + t ** 2 * p["x1"]
            y = (1 - t) ** 2 * p["y0"] + 2 * (1 - t) * t * p["cy"] + t ** 2 * p["y1"]
            r = p["r"] * (1.0 - 0.4 * abs(t - 0.5) * 2)
            self.create_oval(x - r, y - r, x + r, y + r,
                             fill=p["c"], outline="", tags=("dyn",))
            self.create_oval(x - r * 2.2, y - r * 2.2, x + r * 2.2, y + r * 2.2,
                             fill=p["c"], outline="", stipple="gray12", tags=("dyn",))

    def emit_to_backstage(self, actor, n=5, color=None):
        for i in range(n):
            self.particles.append({
                "x0": actor.x, "y0": actor.base_y - 50,
                "x1": self.arch_x + random.uniform(-22, 22),
                "y1": self.arch_y + random.uniform(-10, 18),
                "cx": (actor.x + self.arch_x) / 2 + random.uniform(-40, 40),
                "cy": self.in_y0 + random.uniform(40, 90),
                "t": -0.10 * i, "sp": random.uniform(0.020, 0.032),
                "r": random.uniform(1.6, 3.0),
                "c": color or mix(LAVENDER, GOLD_SOFT, random.random()),
            })

    def emit_to_marquee(self, n=16):
        for i in range(n):
            self.particles.append({
                "x0": self.arch_x + random.uniform(-26, 26),
                "y0": self.arch_y,
                "x1": self.arch_x + random.uniform(-150, 150),
                "y1": self.fy0 + 30,
                "cx": self.arch_x + random.uniform(-200, 200),
                "cy": self.in_y0 + 10,
                "t": -0.05 * i, "sp": random.uniform(0.022, 0.034),
                "r": random.uniform(1.8, 3.2),
                "c": mix(GOLD_SOFT, CORAL, random.random()),
            })

    # -- curtains -------------------------------------------------------------

    def draw_curtain(self):
        c = ease(self.curtain)
        half = (self.in_x1 - self.in_x0) / 2.0
        closed_w = half * 1.02
        open_w = half * 0.16
        w = closed_w + (open_w - closed_w) * c
        folds = 9
        for side in (-1, 1):
            if side < 0:
                x_edge = self.in_x0
            else:
                x_edge = self.in_x1
            for f in range(folds):
                t0 = f / float(folds)
                t1 = (f + 1) / float(folds)
                p0 = x_edge + (w * t0) * (1 if side < 0 else -1)
                p1 = x_edge + (w * t1) * (1 if side < 0 else -1)
                shade = 0.20 + 0.55 * abs(math.sin(t0 * math.pi * folds / 2.4))
                col = mix(WINE_LIGHT, BURGUNDY, shade)
                self.create_polygon(p0, self.in_y0, p1, self.in_y0,
                                    p1, self.in_y1, p0 + (p1 - p0) * 0.12, self.in_y1,
                                    fill=col, outline="", tags=("dyn",))
                self.create_line(p1, self.in_y0, p1, self.in_y1,
                                 fill=mix(col, "#000000", 0.35), width=1, tags=("dyn",))
            # inner lit edge
            edge_x = x_edge + w * (1 if side < 0 else -1)
            self.create_line(edge_x, self.in_y0, edge_x, self.in_y1,
                             fill=CHAMPAGNE, width=2, tags=("dyn",))
            # hem
            self.create_line(x_edge, self.in_y1 - 5, edge_x, self.in_y1 - 5,
                             fill=GOLD_SOFT, width=2, tags=("dyn",))

        # valance across the top
        vh = 34
        for i in range(24):
            t = i / 23.0
            x = self.in_x0 + (self.in_x1 - self.in_x0) * t
            xw = (self.in_x1 - self.in_x0) / 23.0
            col = mix(WINE_LIGHT, BURGUNDY, 0.2 + 0.6 * abs(math.sin(t * math.pi * 12)))
            self.create_polygon(x, self.in_y0, x + xw, self.in_y0,
                                x + xw, self.in_y0 + vh - 10,
                                x + xw / 2, self.in_y0 + vh,
                                x, self.in_y0 + vh - 10,
                                fill=col, outline="", tags=("dyn",))
        self.create_line(self.in_x0, self.in_y0 + vh - 9, self.in_x1, self.in_y0 + vh - 9,
                         fill=CHAMPAGNE, width=1, tags=("dyn",))

    # -- marquee --------------------------------------------------------------

    def draw_marquee(self):
        x0, y0 = self.fx0 + 22, self.fy0 + 8
        x1, y1 = self.fx1 - 22, self.fy0 + 54
        rounded(self, x0, y0, x1, y1, r=12,
                fill=mix(BURGUNDY, PLUM_DEEP, 0.35), outline=CHAMPAGNE, width=2,
                tags=("dyn",))
        rounded(self, x0 + 6, y0 + 5, x1 - 6, y1 - 5, r=9,
                fill="", outline=mix(CHAMPAGNE, BURGUNDY, 0.5), tags=("dyn",))

        # bulbs around the border
        pts = []
        n_side = 9
        for i in range(n_side):
            pts.append((x0 + 14 + (x1 - x0 - 28) * i / (n_side - 1.0), y0 + 5))
        for i in range(n_side):
            pts.append((x1 - 14 - (x1 - x0 - 28) * i / (n_side - 1.0), y1 - 5))
        pts.append((x0 + 5, (y0 + y1) / 2))
        pts.append((x1 - 5, (y0 + y1) / 2))
        self.marquee_total = len(pts)
        for i, (bx, by) in enumerate(pts):
            lit = i < self.marquee_lit
            col = GOLD_SOFT if lit else mix(BURGUNDY, CHAMPAGNE, 0.18)
            if lit:
                self.create_oval(bx - 6, by - 6, bx + 6, by + 6,
                                 fill=CHAMPAGNE, outline="", stipple="gray12",
                                 tags=("dyn",))
            self.create_oval(bx - 3, by - 3, bx + 3, by + 3,
                             fill=col, outline=darken(BURGUNDY, 0.2), tags=("dyn",))

        # marquee text
        cx = (x0 + x1) / 2
        self.create_text(cx, y0 + 16, text=self.result_title,
                         font=(F_DISPLAY, 10, "bold"),
                         fill=mix(CHAMPAGNE, CREAM, 0.3), tags=("dyn",))
        shown = self.result_main[:max(0, int(len(self.result_main) * self.reveal))]
        self.create_text(cx, y0 + 36, text=shown,
                         font=(F_DISPLAY, 17, "bold"), fill=CREAM, tags=("dyn",))
        self.create_text(x0 + 60, y0 + 36, text="DEMO MODE",
                         font=(F_MONO, 7), fill=mix(CHAMPAGNE, BURGUNDY, 0.35),
                         tags=("dyn",))
        self.create_text(x1 - 62, y0 + 36, text=self.result_sub,
                         font=(F_MONO, 7), fill=mix(CHAMPAGNE, BURGUNDY, 0.25),
                         tags=("dyn",))

    def draw_status(self):
        self.create_text(self.fx0 + 26, self.fy1 - 6, anchor="w",
                         text=self.status_line, font=(F_MONO, 8),
                         fill=GOLD_SOFT, tags=("dyn",))
        self.create_text(self.fx1 - 26, self.fy1 - 6, anchor="e",
                         text="NEURAL STAGE  /  FORWARD PASS VIEW",
                         font=(F_MONO, 8), fill=mix(GOLD_SOFT, BURGUNDY, 0.35),
                         tags=("dyn",))


# ----------------------------------------------------------------------------
#  BACKSTAGE
# ----------------------------------------------------------------------------

class Backstage(tk.Canvas):

    LAYERS = ["LAYER 01  EMBEDDING",
              "LAYER 02  LINEAR",
              "LAYER 03  ATTENTION",
              "LAYER 04  ACTIVATION"]

    def __init__(self, master, width, height):
        tk.Canvas.__init__(self, master, width=width, height=height,
                           bg=IVORY, highlightthickness=0)
        self.W, self.H = width, height
        self.state = ["READY"] * 4
        self.energy = [0.0] * 4
        self.flow = 0.0
        self.particles = []
        self.draw_static()
        self._tick()

    def draw_static(self):
        self.delete("bg")
        vgradient(self, 0, 0, self.W, self.H, PLUM_DEEP, darken(PLUM_DEEP, 0.4),
                  30, tags=("bg",))
        self.create_rectangle(1, 1, self.W - 1, self.H - 1,
                              outline=mix(PLUM, CHAMPAGNE, 0.3), width=2, tags=("bg",))
        self.create_text(16, 18, anchor="w", text="BACKSTAGE",
                         font=(F_DISPLAY, 13, "bold"), fill=GOLD_SOFT, tags=("bg",))
        self.create_text(16, 34, anchor="w",
                         text="hidden neural computation",
                         font=(F_BODY, 8), fill=mix(LAVENDER, PLUM, 0.3), tags=("bg",))
        self.create_line(14, 44, self.W - 14, 44,
                         fill=mix(PLUM, CHAMPAGNE, 0.25), tags=("bg",))

        # hanging cables and lamps across the top
        for i in range(16):
            x = 20 + (self.W - 40) * i / 15.0
            sag = 10 + 6 * math.sin(i * 0.9)
            self.create_line(x, 48, x, 48 + sag, fill=mix(PLUM, "#000000", 0.3),
                             width=1, tags=("bg",))

        # module positions
        self.mods = []
        mw, mh = (self.W - 60) / 4.0, 62
        for i in range(4):
            x = 24 + i * (mw + 4)
            y = 86
            self.mods.append((x, y, x + mw - 8, y + mh))

    def set_state(self, idx, state):
        self.state[idx] = state
        if state == "ACTIVE":
            self.energy[idx] = 1.0
            x0, y0, x1, y1 = self.mods[idx]
            for _ in range(10):
                self.particles.append({
                    "x": random.uniform(x0, x1), "y": y1,
                    "vy": -random.uniform(0.6, 1.6),
                    "life": 1.0, "r": random.uniform(1.2, 2.4)})

    def reset(self):
        self.state = ["READY"] * 4
        self.energy = [0.0] * 4
        self.particles = []

    def _tick(self):
        self.flow = (self.flow + 0.02) % 1.0
        for i in range(4):
            if self.state[i] != "ACTIVE" and self.energy[i] > 0:
                self.energy[i] = max(0.0, self.energy[i] - 0.02)
        alive = []
        for p in self.particles:
            p["y"] += p["vy"]
            p["life"] -= 0.02
            if p["life"] > 0:
                alive.append(p)
        self.particles = alive
        self.redraw()
        self.after(40, self._tick)

    def redraw(self):
        self.delete("dyn")
        colors = {"READY": mix(PLUM, LAVENDER, 0.35),
                  "PROCESSING": CORAL,
                  "ACTIVE": CHAMPAGNE}
        for i, (x0, y0, x1, y1) in enumerate(self.mods):
            st = self.state[i]
            e = self.energy[i]
            glowc = colors[st]
            if e > 0.05:
                self.create_rectangle(x0 - 5, y0 - 5, x1 + 5, y1 + 5,
                                      fill=glowc, outline="", stipple="gray12",
                                      tags=("dyn",))
            rounded(self, x0, y0, x1, y1, r=8,
                    fill=mix(PLUM_DEEP, glowc, 0.12 + 0.35 * e),
                    outline=glowc, width=1, tags=("dyn",))
            self.create_text((x0 + x1) / 2, y0 + 15,
                             text=self.LAYERS[i].split("  ")[0],
                             font=(F_DISPLAY, 9, "bold"), fill=CREAM, tags=("dyn",))
            self.create_text((x0 + x1) / 2, y0 + 29,
                             text=self.LAYERS[i].split("  ")[1],
                             font=(F_MONO, 7), fill=mix(CREAM, PLUM, 0.4), tags=("dyn",))
            # status lamp
            lx, ly = (x0 + x1) / 2, y0 + 47
            self.create_oval(lx - 5, ly - 5, lx + 5, ly + 5,
                             fill=glowc, outline=darken(glowc, 0.4), tags=("dyn",))
            self.create_text((x0 + x1) / 2, y0 + 58, text=st,
                             font=(F_MONO, 7), fill=glowc, tags=("dyn",))
            # feed cable from rig down into module
            self.create_line(lx, 58, lx, y0, fill=mix(PLUM, glowc, 0.4),
                             width=2, tags=("dyn",))

        for p in self.particles:
            r = p["r"]
            self.create_oval(p["x"] - r, p["y"] - r, p["x"] + r, p["y"] + r,
                             fill=mix(CHAMPAGNE, CORAL, 1 - p["life"]),
                             outline="", tags=("dyn",))

        # tensor flow channel
        cy = self.H - 28
        self.create_line(24, cy, self.W - 24, cy,
                         fill=mix(PLUM, CHAMPAGNE, 0.2), width=6, tags=("dyn",))
        for k in range(10):
            t = (self.flow + k / 10.0) % 1.0
            x = 24 + (self.W - 48) * t
            self.create_oval(x - 3, cy - 3, x + 3, cy + 3,
                             fill=GOLD_SOFT, outline="", tags=("dyn",))
        self.create_text(24, cy - 14, anchor="w",
                         text="TENSOR FLOW   FORWARD PASS   ACTIVATION",
                         font=(F_MONO, 7), fill=mix(LAVENDER, CREAM, 0.3), tags=("dyn",))


# ----------------------------------------------------------------------------
#  ACTOR PROFILE
# ----------------------------------------------------------------------------

class ActorProfile(tk.Canvas):

    def __init__(self, master, width, height):
        tk.Canvas.__init__(self, master, width=width, height=height,
                           bg=IVORY, highlightthickness=0)
        self.W, self.H = width, height
        self.actor = None
        self.phase = 0.0
        self.draw_static()
        self._tick()

    def draw_static(self):
        vgradient(self, 0, 0, self.W, self.H, CREAM, "#F0E4D6", 24, tags=("bg",))
        self.create_rectangle(1, 1, self.W - 1, self.H - 1,
                              outline=BURGUNDY, width=2, tags=("bg",))
        self.create_rectangle(7, 7, self.W - 7, self.H - 7,
                              outline=CHAMPAGNE, width=1, tags=("bg",))
        for x in (11, self.W - 11):
            for y in (11, self.H - 11):
                self.create_oval(x - 3, y - 3, x + 3, y + 3,
                                 fill=CHAMPAGNE, outline=BURGUNDY, tags=("bg",))
        self.create_text(20, 24, anchor="w", text="ACTOR PROFILE",
                         font=(F_DISPLAY, 13, "bold"), fill=BURGUNDY, tags=("bg",))
        self.create_line(18, 36, self.W - 18, 36, fill=mix(BURGUNDY, IVORY, 0.6),
                         tags=("bg",))

    def show(self, actor):
        self.actor = actor

    def _tick(self):
        self.phase += 0.08
        self.redraw()
        self.after(60, self._tick)

    def redraw(self):
        self.delete("dyn")
        a = self.actor
        if a is None:
            self.create_text(self.W / 2, self.H / 2 - 6,
                             text="NO ACTOR UNDER THE SPOTLIGHT",
                             font=(F_BODY, 9), fill=MUTED, tags=("dyn",))
            self.create_text(self.W / 2, self.H / 2 + 12,
                             text="click any actor on the stage, or a name in the cast list",
                             font=(F_BODY, 8), fill=MUTED, tags=("dyn",))
            return

        # character name, large
        self.create_text(20, 62, anchor="w", text=a.token,
                         font=(F_DISPLAY, 24, "bold italic"), fill=WINE, tags=("dyn",))
        self.create_text(20, 84, anchor="w", text=a.role.upper(),
                         font=(F_MONO, 8), fill=PLUM, tags=("dyn",))

        fields = [("TOKEN ID", a.tid), ("POSITION", "%02d" % (a.index + 1)),
                  ("LAYER", "%02d" % a.layer),
                  ("STATUS", "ON STAGE" if a.on_stage else "BACKSTAGE")]
        for i, (k, v) in enumerate(fields):
            x = 20 + (i % 2) * 118
            y = 106 + (i // 2) * 30
            self.create_text(x, y, anchor="w", text=k, font=(F_MONO, 7),
                             fill=MUTED, tags=("dyn",))
            self.create_text(x, y + 13, anchor="w", text=v,
                             font=(F_BODY, 10, "bold"), fill=INK, tags=("dyn",))

        # tensor spotlight -- vertical light columns
        bx0 = self.W - 176
        self.create_text(bx0, 58, anchor="w", text="TENSOR SPOTLIGHT",
                         font=(F_MONO, 7), fill=MUTED, tags=("dyn",))
        base = 150
        for i, v in enumerate(a.tensor):
            x = bx0 + 8 + i * 26
            h = abs(v) * 56
            up = v >= 0
            top = base - h if up else base
            col = mix(PLUM, CHAMPAGNE, (v + 1) / 2.0)
            wob = 1 + 0.08 * math.sin(self.phase + i)
            rounded(self, x - 7, base - h * wob if up else base,
                    x + 7, base if up else base + h * wob, r=4,
                    fill=col, outline=lighten(col, 0.3), tags=("dyn",))
            self.create_text(x, base + (h + 12) if not up else base - h * wob - 9,
                             text="%.2f" % v, font=(F_MONO, 7), fill=INK, tags=("dyn",))
        self.create_line(bx0, base, self.W - 22, base,
                         fill=mix(BURGUNDY, IVORY, 0.55), tags=("dyn",))

        # activation meter
        self.create_text(20, 172, anchor="w", text="ACTIVATION",
                         font=(F_MONO, 7), fill=MUTED, tags=("dyn",))
        self.create_text(96, 172, anchor="w", text="%.2f" % a.activation,
                         font=(F_BODY, 10, "bold"), fill=WINE, tags=("dyn",))
        mw = 120
        self.create_rectangle(20, 182, 20 + mw, 190,
                              fill=mix(IVORY, BURGUNDY, 0.12), outline="", tags=("dyn",))
        for i in range(int(mw * a.activation / 6)):
            x = 20 + i * 6
            self.create_rectangle(x, 182, x + 4, 190,
                                  fill=mix(CORAL, CHAMPAGNE, i / 20.0),
                                  outline="", tags=("dyn",))


# ----------------------------------------------------------------------------
#  CAST LIST
# ----------------------------------------------------------------------------

class CastList(tk.Canvas):

    def __init__(self, master, width, height, on_select):
        tk.Canvas.__init__(self, master, width=width, height=height,
                           bg=IVORY, highlightthickness=0)
        self.W, self.H = width, height
        self.on_select = on_select
        self.actors = []
        self.offset = 0
        self.row_h = 21
        self.top = 46
        self.rows_visible = int((self.H - self.top - 18) / self.row_h)
        self.draw_static()
        self.bind("<Button-1>", self._click)
        self.bind("<MouseWheel>", self._wheel)
        self.bind("<Button-4>", lambda e: self._scroll(-1))
        self.bind("<Button-5>", lambda e: self._scroll(1))

    def draw_static(self):
        vgradient(self, 0, 0, self.W, self.H, CREAM, "#F0E4D6", 24, tags=("bg",))
        self.create_rectangle(1, 1, self.W - 1, self.H - 1,
                              outline=BURGUNDY, width=2, tags=("bg",))
        self.create_text(16, 22, anchor="w", text="CAST LIST",
                         font=(F_DISPLAY, 13, "bold"), fill=BURGUNDY, tags=("bg",))
        self.create_text(self.W - 16, 24, anchor="e", text="scroll for more",
                         font=(F_BODY, 7), fill=MUTED, tags=("bg",))
        self.create_line(14, 36, self.W - 14, 36,
                         fill=mix(BURGUNDY, IVORY, 0.6), tags=("bg",))

    def set_actors(self, actors):
        self.actors = actors
        self.offset = 0
        self.redraw()

    def _wheel(self, ev):
        self._scroll(-1 if ev.delta > 0 else 1)

    def _scroll(self, d):
        max_off = max(0, len(self.actors) - self.rows_visible)
        self.offset = max(0, min(max_off, self.offset + d))
        self.redraw()

    def _click(self, ev):
        idx = int((ev.y - self.top) // self.row_h) + self.offset
        if 0 <= idx < len(self.actors):
            self.on_select(self.actors[idx].index)

    def redraw(self):
        self.delete("dyn")
        if not self.actors:
            self.create_text(self.W / 2, self.H / 2, text="no cast yet",
                             font=(F_BODY, 9), fill=MUTED, tags=("dyn",))
            return
        shown = self.actors[self.offset:self.offset + self.rows_visible]
        for i, a in enumerate(shown):
            y = self.top + i * self.row_h
            if a.selected:
                rounded(self, 12, y - 2, self.W - 12, y + self.row_h - 4, r=6,
                        fill=mix(CHAMPAGNE, CREAM, 0.45), outline=CHAMPAGNE,
                        tags=("dyn",))
            self.create_text(20, y + 7, anchor="w", text=a.tid,
                             font=(F_MONO, 8), fill=PLUM, tags=("dyn",))
            self.create_text(72, y + 7, anchor="w", text=a.token,
                             font=(F_BODY, 9, "bold" if a.selected else "normal"),
                             fill=INK, tags=("dyn",))
            dot = a.body_color
            self.create_oval(self.W - 28, y + 3, self.W - 20, y + 11,
                             fill=dot, outline=darken(dot, 0.3), tags=("dyn",))


# ----------------------------------------------------------------------------
#  HEADER
# ----------------------------------------------------------------------------

class HeaderBar(tk.Canvas):

    def __init__(self, master, width, height):
        tk.Canvas.__init__(self, master, width=width, height=height,
                           bg=IVORY, highlightthickness=0)
        vgradient(self, 0, 0, width, height, BURGUNDY, WINE, 20)
        self.create_line(0, height - 2, width, height - 2, fill=CHAMPAGNE, width=2)
        self.create_text(22, 20, anchor="w", text="NEURAL THEATRE",
                         font=(F_DISPLAY, 19, "bold"), fill=CREAM)
        self.create_text(22, 41, anchor="w",
                         text="where every word takes a role",
                         font=(F_DISPLAY, 10, "italic"), fill=GOLD_SOFT)
        self.create_text(width - 22, 20, anchor="e", text="PYTORCH  NLP",
                         font=(F_MONO, 11), fill=CHAMPAGNE)
        self.create_text(width - 22, 40, anchor="e",
                         text="demonstration data only - no model weights loaded",
                         font=(F_MONO, 7), fill=mix(GOLD_SOFT, WINE, 0.4))
        for i in range(30):
            x = 300 + i * 12
            if x > width - 300:
                break
            self.create_oval(x - 2, height / 2 - 2, x + 2, height / 2 + 2,
                             fill=mix(CHAMPAGNE, WINE, 0.4 + 0.4 * math.sin(i)),
                             outline="")


# ----------------------------------------------------------------------------
#  CONTROL DECK  (script + buttons + task selector)
# ----------------------------------------------------------------------------

TASKS = ["TEXT CLASSIFICATION", "NAMED ENTITY RECOGNITION",
         "SENTIMENT ANALYSIS", "TEXT GENERATION"]

SAMPLES = [
    "The cat sat on the mat because it was tired.",
    "Ali walked through Hyderabad at night and felt calm.",
    "The quiet garden in Pakistan was beautiful and warm.",
]


class ControlDeck(tk.Canvas):

    def __init__(self, master, width, height, app):
        tk.Canvas.__init__(self, master, width=width, height=height,
                           bg=IVORY, highlightthickness=0)
        self.W, self.H = width, height
        self.app = app
        self.task = 0
        self.buttons = {}
        self.task_boxes = []
        self.sample_i = 0

        self.hover = None
        self.draw_frame()
        self.build_script_box()
        self.draw_tasks()
        self.draw_buttons()
        self.bind("<Button-1>", self._click)
        self.bind("<Motion>", self._hover)

    # -- drawing --------------------------------------------------------------

    def draw_frame(self):
        vgradient(self, 0, 0, self.W, self.H, CREAM, "#EFE2D4", 20, tags=("bg",))
        self.create_line(0, self.H - 1, self.W, self.H - 1,
                         fill=mix(BURGUNDY, IVORY, 0.55), tags=("bg",))

        # script paper, drawn by hand
        self.sx0, self.sy0, self.sx1, self.sy1 = 14, 10, 560, self.H - 12
        self.create_polygon(self.sx0 + 5, self.sy0 + 5, self.sx1 + 5, self.sy0 + 5,
                            self.sx1 + 5, self.sy1 + 5, self.sx0 + 5, self.sy1 + 5,
                            fill=mix(BURGUNDY, CREAM, 0.72), outline="", tags=("bg",))
        self.create_rectangle(self.sx0, self.sy0, self.sx1, self.sy1,
                              fill="#FFFDF8", outline=BURGUNDY, width=2, tags=("bg",))
        self.create_line(self.sx0 + 34, self.sy0, self.sx0 + 34, self.sy1,
                         fill=CORAL, tags=("bg",))
        for i in range(5):
            y = self.sy0 + 12 + i * 5
            self.create_oval(self.sx0 + 12, y, self.sx0 + 20, y + 4,
                             outline=mix(BURGUNDY, CREAM, 0.5), fill=IVORY, tags=("bg",))
        self.create_text(self.sx0 + 44, self.sy0 + 12, anchor="w", text="THE SCRIPT",
                         font=(F_DISPLAY, 11, "bold"), fill=BURGUNDY, tags=("bg",))
        self.create_text(self.sx1 - 10, self.sy0 + 12, anchor="e",
                         text="act one / scene one",
                         font=(F_DISPLAY, 8, "italic"), fill=MUTED, tags=("bg",))

    def build_script_box(self):
        self.text = tk.Text(self, height=2, wrap="word", relief="flat",
                            bg="#FFFDF8", fg=INK, font=(F_DISPLAY, 11),
                            insertbackground=WINE, highlightthickness=0,
                            selectbackground=mix(CHAMPAGNE, CREAM, 0.4),
                            padx=4, pady=2)
        self.text.insert("1.0", SAMPLES[0])
        self.create_window(self.sx0 + 44, self.sy0 + 26, anchor="nw",
                           window=self.text,
                           width=self.sx1 - self.sx0 - 56,
                           height=self.sy1 - self.sy0 - 36)

    def draw_tasks(self):
        self.delete("task")
        x0 = 576
        bw, bh = 186, 20
        self.create_text(x0, 14, anchor="w", text="PERFORMANCE ON TONIGHT",
                         font=(F_MONO, 7), fill=MUTED, tags=("task",))
        self.task_boxes = []
        for i, t in enumerate(TASKS):
            col = i % 2
            row = i // 2
            x = x0 + col * (bw + 8)
            y = 24 + row * (bh + 6)
            sel = (i == self.task)
            rounded(self, x, y, x + bw, y + bh, r=9,
                    fill=mix(CREAM, CHAMPAGNE, 0.55) if sel else CREAM,
                    outline=BURGUNDY if sel else mix(BURGUNDY, IVORY, 0.55),
                    width=2 if sel else 1, tags=("task",))
            self.create_oval(x + 9, y + bh / 2 - 4, x + 17, y + bh / 2 + 4,
                             fill=WINE if sel else IVORY,
                             outline=BURGUNDY, tags=("task",))
            self.create_text(x + 24, y + bh / 2, anchor="w", text=t,
                             font=(F_BODY, 8, "bold" if sel else "normal"),
                             fill=INK, tags=("task",))
            self.task_boxes.append((x, y, x + bw, y + bh, i))

    def draw_buttons(self):
        self.delete("btn")
        self.buttons = {}
        bx = 972
        specs = [("RUN PERFORMANCE", "run", 200, 40, bx, 12, WINE, CREAM, True),
                 ("LOAD SCRIPT", "load", 96, 26, bx, 60, CREAM, BURGUNDY, False),
                 ("RESET STAGE", "reset", 96, 26, bx + 104, 60, CREAM, BURGUNDY, False)]
        for label, key, w, h, x, y, fill, fg, big in specs:
            hov = (self.hover == key)
            f = lighten(fill, 0.10) if hov else fill
            if big:
                rounded(self, x - 3, y - 3, x + w + 3, y + h + 3, r=14,
                        fill=mix(CHAMPAGNE, CREAM, 0.4), outline="", tags=("btn",))
            rounded(self, x, y, x + w, y + h, r=12 if big else 8,
                    fill=f, outline=BURGUNDY, width=2, tags=("btn",))
            if big:
                self.create_polygon(x + 22, y + h / 2 - 7, x + 22, y + h / 2 + 7,
                                    x + 34, y + h / 2,
                                    fill=CHAMPAGNE, outline="", tags=("btn",))
                self.create_text(x + w / 2 + 12, y + h / 2, text=label,
                                 font=(F_DISPLAY, 12, "bold"), fill=fg, tags=("btn",))
            else:
                self.create_text(x + w / 2, y + h / 2, text=label,
                                 font=(F_BODY, 8, "bold"), fill=fg, tags=("btn",))
            self.buttons[key] = (x, y, x + w, y + h)

        # right edge: what is happening panel title
        self.create_text(self.W - 14, 14, anchor="e",
                         text="stage controls", font=(F_MONO, 7),
                         fill=MUTED, tags=("btn",))

    # -- events ---------------------------------------------------------------

    def _hover(self, ev):
        h = None
        for k, (x0, y0, x1, y1) in self.buttons.items():
            if x0 <= ev.x <= x1 and y0 <= ev.y <= y1:
                h = k
        if h != self.hover:
            self.hover = h
            self.config(cursor="hand2" if h else "")
            self.draw_buttons()

    def _click(self, ev):
        for k, (x0, y0, x1, y1) in self.buttons.items():
            if x0 <= ev.x <= x1 and y0 <= ev.y <= y1:
                if k == "run":
                    self.app.run_performance()
                elif k == "load":
                    self.sample_i = (self.sample_i + 1) % len(SAMPLES)
                    self.text.delete("1.0", "end")
                    self.text.insert("1.0", SAMPLES[self.sample_i])
                    self.app.reset_stage()
                elif k == "reset":
                    self.app.reset_stage()
                return
        for x0, y0, x1, y1, i in self.task_boxes:
            if x0 <= ev.x <= x1 and y0 <= ev.y <= y1:
                self.task = i
                self.draw_tasks()
                self.app.task_changed()
                return

    def script_text(self):
        return self.text.get("1.0", "end").strip()


# ----------------------------------------------------------------------------
#  TICKER  (WHAT IS HAPPENING?)
# ----------------------------------------------------------------------------

CONCEPTS = [
    ("TOKEN", "Words are converted into processable units."),
    ("TENSOR", "PyTorch represents data as numerical tensors."),
    ("FORWARD PASS", "Data moves through the neural network to produce an output."),
    ("ACTIVATION", "Neurons respond to the processed information."),
    ("OUTPUT", "The network produces a task-specific result."),
]


class Ticker(tk.Canvas):

    def __init__(self, master, width, height):
        tk.Canvas.__init__(self, master, width=width, height=height,
                           bg=IVORY, highlightthickness=0)
        self.W, self.H = width, height
        self.i = 0
        self.forced = None
        vgradient(self, 0, 0, width, height, BURGUNDY, WINE, 12, tags=("bg",))
        self.create_line(0, 0, width, 0, fill=CHAMPAGNE, width=2, tags=("bg",))
        self._cycle()

    def force(self, key):
        for i, (k, _) in enumerate(CONCEPTS):
            if k == key:
                self.i = i
        self.redraw()

    def _cycle(self):
        self.redraw()
        self.i = (self.i + 1) % len(CONCEPTS)
        self.after(4200, self._cycle)

    def redraw(self):
        self.delete("dyn")
        k, v = CONCEPTS[self.i]
        self.create_text(18, self.H / 2, anchor="w", text="WHAT IS HAPPENING?",
                         font=(F_MONO, 8), fill=mix(GOLD_SOFT, WINE, 0.35),
                         tags=("dyn",))
        self.create_text(160, self.H / 2, anchor="w", text=k,
                         font=(F_DISPLAY, 10, "bold"), fill=CHAMPAGNE, tags=("dyn",))
        self.create_text(272, self.H / 2, anchor="w", text=v,
                         font=(F_BODY, 9), fill=CREAM, tags=("dyn",))
        for i in range(len(CONCEPTS)):
            x = self.W - 20 - (len(CONCEPTS) - 1 - i) * 14
            r = 4 if i == self.i else 2
            self.create_oval(x - r, self.H / 2 - r, x + r, self.H / 2 + r,
                             fill=CHAMPAGNE if i == self.i else mix(WINE, CHAMPAGNE, 0.3),
                             outline="", tags=("dyn",))


# ----------------------------------------------------------------------------
#  PERFORMANCE ENGINE
# ----------------------------------------------------------------------------

class PerformanceEngine:
    """Runs the scripted forward-pass show, one act at a time."""

    def __init__(self, app):
        self.app = app
        self.running = False
        self.jobs = []

    def cancel(self):
        for j in self.jobs:
            try:
                self.app.after_cancel(j)
            except Exception:
                pass
        self.jobs = []
        self.running = False

    def at(self, ms, fn):
        self.jobs.append(self.app.after(ms, fn))

    def start(self, actors, result):
        self.cancel()
        self.running = True
        app = self.app
        stage = app.stage
        back = app.backstage
        back.reset()

        stage.marquee_lit = 0
        stage.reveal = 0.0
        stage.stage_glow = 0.0
        stage.result_main = ""
        stage.result_sub = "PERFORMANCE IN PROGRESS"

        t = 0

        # ACT I -- curtains open
        def act1():
            stage.status_line = "ACT I  -  CURTAIN RISES"
            stage.curtain_target = 1.0
            app.ticker.force("TOKEN")
        self.at(t, act1); t += 1300

        # ACT II -- the script enters
        def act2():
            stage.status_line = "ACT II  -  THE SCRIPT ENTERS THE HOUSE"
            back.set_state(0, "PROCESSING")
        self.at(t, act2); t += 700

        # ACT III -- actors take their places
        def enter(i):
            def go():
                a = actors[i]
                a.on_stage = True
                self._grow(a)
                stage.status_line = "ACT III  -  %s TAKES THE STAGE" % a.token.upper()
            return go

        for i in range(len(actors)):
            self.at(t + i * 110, enter(i))
        t += len(actors) * 110 + 300

        # ACT IV -- tensor data activates
        def act4():
            stage.status_line = "ACT IV  -  TENSOR DATA ACTIVATES"
            app.ticker.force("TENSOR")
            back.set_state(0, "ACTIVE")
            back.set_state(1, "PROCESSING")
        self.at(t, act4); t += 400

        def light(i):
            def go():
                a = actors[i]
                self._glow(a, a.activation)
                stage.emit_to_backstage(a, n=3)
            return go
        for i in range(len(actors)):
            self.at(t + i * 90, light(i))
        t += len(actors) * 90 + 400

        # ACT V -- the backstage layers process
        def layer(i):
            def go():
                app.ticker.force("FORWARD PASS")
                stage.status_line = "ACT V  -  LAYER %02d PROCESSING" % (i + 1)
                for k in range(i):
                    back.set_state(k, "ACTIVE")
                back.set_state(i, "ACTIVE")
                if i + 1 < 4:
                    back.set_state(i + 1, "PROCESSING")
            return go
        for i in range(4):
            self.at(t + i * 420, layer(i))
        t += 4 * 420 + 300

        # ACT VI -- spotlights sweep, data returns
        def act6():
            stage.status_line = "ACT VI  -  SPOTLIGHTS FIND THE LEADS"
            app.ticker.force("ACTIVATION")
            stage.emit_to_marquee(18)
            leads = [a for a in actors if a.kind == "lead"] or actors[:1]
            stage.select(leads[0].index)
        self.at(t, act6); t += 900

        # FINAL ACT -- the result
        def final():
            stage.status_line = "FINAL ACT  -  TONIGHT'S RESULT"
            app.ticker.force("OUTPUT")
            stage.result_title = result["title"]
            stage.result_main = result["main"]
            stage.result_sub = result["sub"]
            self._reveal(result.get("conf", 0.9))
        self.at(t, final)

    # -- small tweens ---------------------------------------------------------

    def _grow(self, a, step=0.0):
        a.scale = min(1.0, a.scale + 0.14)
        if a.scale < 1.0:
            self.app.after(28, lambda: self._grow(a))

    def _glow(self, a, target):
        if a.glow < target:
            a.glow = min(target, a.glow + 0.10)
            self.app.after(30, lambda: self._glow(a, target))

    def _reveal(self, conf, step=0):
        stage = self.app.stage
        stage.reveal = min(1.0, stage.reveal + 0.06)
        stage.stage_glow = min(0.75, stage.stage_glow + 0.03)
        lit_goal = int(stage.marquee_total * conf)
        if stage.marquee_lit < lit_goal:
            stage.marquee_lit += 1
        if stage.reveal < 1.0 or stage.marquee_lit < lit_goal:
            self.app.after(45, lambda: self._reveal(conf))
        else:
            stage.status_line = "CURTAIN CALL  -  PERFORMANCE COMPLETE  (DEMO MODE)"
            self.running = False


# ----------------------------------------------------------------------------
#  APPLICATION
# ----------------------------------------------------------------------------

APP_W, APP_H = 1400, 860
PAD = 14


class NeuralTheatreApp(tk.Tk):

    def __init__(self):
        tk.Tk.__init__(self)
        self.title("NEURAL THEATRE  -  PyTorch NLP  -  where every word takes a role")
        self.geometry("%dx%d" % (APP_W, APP_H))
        self.minsize(1180, 780)
        self.configure(bg=IVORY)

        inner_w = APP_W - 2 * PAD

        self.header = HeaderBar(self, inner_w, 56)
        self.header.pack(padx=PAD, pady=(10, 6))

        self.controls = ControlDeck(self, inner_w, 96, self)
        self.controls.pack(padx=PAD, pady=(0, 6))

        self.stage = NeuralStage(self, inner_w, 386, self.on_actor_selected)
        self.stage.pack(padx=PAD, pady=(0, 6))

        bottom = tk.Frame(self, bg=IVORY)
        bottom.pack(padx=PAD, pady=(0, 6))

        bw = 576
        pw = 424
        cw = inner_w - bw - pw - 20

        self.backstage = Backstage(bottom, bw, 214)
        self.backstage.grid(row=0, column=0, padx=(0, 10))
        self.profile = ActorProfile(bottom, pw, 214)
        self.profile.grid(row=0, column=1, padx=(0, 10))
        self.cast = CastList(bottom, cw, 214, self.select_from_cast)
        self.cast.grid(row=0, column=2)

        self.ticker = Ticker(self, inner_w, 28)
        self.ticker.pack(padx=PAD, pady=(0, 10))

        self.engine = PerformanceEngine(self)
        self.actors = []

        self.bind("<Return>", lambda e: self.run_performance())
        self.bind("<Escape>", lambda e: self.reset_stage())

        self.prepare_cast()

    # -- wiring ---------------------------------------------------------------

    def prepare_cast(self):
        text = self.controls.script_text()
        tokens = DemoNLP.tokenize(text)
        self.actors = [Actor(i, t) for i, t in enumerate(tokens)]
        self.stage.set_actors(self.actors)
        self.cast.set_actors(self.actors)
        self.profile.show(None)

    def on_actor_selected(self, actor):
        self.profile.show(actor)
        self.cast.redraw()

    def select_from_cast(self, index):
        self.stage.select(index)
        self.cast.redraw()

    def task_changed(self):
        if self.stage.result_main:
            res = self.build_result()
            self.stage.result_title = res["title"]
            self.stage.result_main = res["main"]
            self.stage.result_sub = res["sub"]
            self.stage.reveal = 1.0
            self.stage.marquee_lit = int(self.stage.marquee_total * res["conf"])

    def build_result(self):
        tokens = [a.token for a in self.actors]
        task = self.controls.task
        if task == 0:
            label, conf = DemoNLP.classify(tokens)
            return {"title": "TONIGHT'S RESULT  /  TEXT CLASSIFICATION",
                    "main": "%s   %.1f%%" % (label, conf),
                    "sub": "DEMO OUTPUT", "conf": conf / 100.0}
        if task == 1:
            ents = DemoNLP.ner(tokens)
            main = "   ".join("%s: %s" % (k, v) for k, v in ents)
            return {"title": "TONIGHT'S RESULT  /  NAMED ENTITY RECOGNITION",
                    "main": main, "sub": "DEMO OUTPUT", "conf": 0.88}
        if task == 2:
            label, score = DemoNLP.sentiment(tokens)
            return {"title": "TONIGHT'S RESULT  /  SENTIMENT ANALYSIS",
                    "main": "%s   %.2f" % (label, score),
                    "sub": "DEMO OUTPUT", "conf": score}
        gen = DemoNLP.generate(tokens)
        return {"title": "TONIGHT'S RESULT  /  TEXT GENERATION",
                "main": gen[:58], "sub": "DEMO OUTPUT", "conf": 0.84}

    # -- actions --------------------------------------------------------------

    def run_performance(self):
        self.prepare_cast()
        self.engine.start(self.actors, self.build_result())

    def reset_stage(self):
        self.engine.cancel()
        self.stage.curtain_target = 0.0
        self.stage.marquee_lit = 0
        self.stage.reveal = 0.0
        self.stage.stage_glow = 0.0
        self.stage.particles = []
        self.stage.result_title = "TONIGHT'S RESULT"
        self.stage.result_main = ""
        self.stage.result_sub = "PRESS  RUN PERFORMANCE"
        self.stage.status_line = "CURTAIN DOWN  -  STAGE RESET"
        self.backstage.reset()
        self.prepare_cast()


if __name__ == "__main__":
    app = NeuralTheatreApp()
    app.mainloop()