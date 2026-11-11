#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
POLYGLOT — THE LIVING LANGUAGE GLOBE
"Every Language Has a Place"

A Tkinter-only (Canvas) demo where the whole interface is built around one
continuously rotating, illustrated Earth.

  USER TEXT -> LANGUAGE SIGNAL -> DEMO DETECTION -> EARTH SEARCHES ->
  EARTH SLOWS DOWN -> EARTH STOPS -> REGION GLOWS -> LANGUAGE INFO APPEARS

HONESTY NOTE
  This is a visual / educational demo. Language detection is SIMULATED
  (Unicode script checks + a few keyword lists) and the regions are only
  "Associated Linguistic Regions" - a language does NOT come from one point.

Run:   python main.py          (Python 3.x, standard library only)

File layout (all in this one file, separated by big banner comments):
  1. Settings & palette          5. ParticleSystem   (signal particles)
  2. Helpers                     6. GlobeAnimator    (rotation physics)
  3. Data (map, languages)       7. GlobeRenderer    (3D-illusion globe)
  4. LanguageDetectorDemo        8. LanguageGlobeApp (UI + story timeline)
"""

import math
import random
import re
import time
import traceback
import tkinter as tk
from dataclasses import dataclass
from tkinter import font as tkfont

# =====================================================================
# 1. SETTINGS & PALETTE
# =====================================================================
# +1 = centre longitude increases (Europe -> Asia -> Pacific -> Americas,
# the order in the brief).  The real Earth turns the other way; set to -1
# if you want physical accuracy.
SPIN_DIRECTION = 1
IDLE_SPEED = 5.0          # degrees / second while idle
IDLE_TILT = 18.0          # camera looks slightly down on the northern half
FRAME_MS = 30             # ~33 fps
HOLD_BEFORE_RESUME = 12.0 # seconds the globe stays parked on a found region

P = {
    "bg_top": "#061f45", "bg_mid": "#0a4577", "bg_bot": "#118aa0",
    "ivory": "#f8f2de", "gold": "#f5c95f", "coral": "#ff8b74",
    "turq": "#41dcd0", "cyan": "#86e8ff", "lav": "#b9aaf3",
    "ink": "#082a52", "dim": "#9cc9dc", "soft": "#8fdcee",
    "field": "#0c3560",
    "land": "#7cc6a0", "coast": "#dff5cf",
    "night": "#072f63", "dusk2": "#0a4380", "dusk1": "#0e5a97",
}
SANS = ["Segoe UI", "SF Pro Text", "Helvetica Neue", "Noto Sans",
        "DejaVu Sans", "Arial", "Helvetica"]
SERIF = ["Georgia", "Palatino Linotype", "Cambria", "Noto Serif",
         "DejaVu Serif", "Times New Roman", "Times"]
PLACEHOLDER = "Type something in any language..."


# =====================================================================
# 2. HELPERS
# =====================================================================
def clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v


def lerp(a, b, t):
    return a + (b - a) * t


def smoothstep(t):
    t = clamp(t, 0.0, 1.0)
    return t * t * (3 - 2 * t)


def ease_out(t):
    t = clamp(t, 0.0, 1.0)
    return 1 - (1 - t) ** 3


_rgb_cache = {}


def hex_rgb(h):
    v = _rgb_cache.get(h)
    if v is None:
        v = (int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16))
        _rgb_cache[h] = v
    return v


def mix(a, b, t):
    """Blend two hex colours (t=0 -> a, t=1 -> b). Tk has no alpha, so this
    is how every 'translucent' or 'glowing' colour in the app is made."""
    t = clamp(t, 0.0, 1.0)
    ra, rb = hex_rgb(a), hex_rgb(b)
    return "#%02x%02x%02x" % (int(ra[0] + (rb[0] - ra[0]) * t),
                              int(ra[1] + (rb[1] - ra[1]) * t),
                              int(ra[2] + (rb[2] - ra[2]) * t))


def gradient(stops, t):
    """stops = [(pos, '#hex'), ...] sorted by pos."""
    if t <= stops[0][0]:
        return stops[0][1]
    for (p0, c0), (p1, c1) in zip(stops, stops[1:]):
        if t <= p1:
            return mix(c0, c1, (t - p0) / (p1 - p0))
    return stops[-1][1]


def bg_at(y, H):
    t = clamp(y / max(1.0, H), 0.0, 1.0)
    return gradient([(0, P["bg_top"]), (0.55, P["bg_mid"]), (1, P["bg_bot"])], t)


def rounded_poly(x1, y1, x2, y2, r):
    """Points for a rounded rectangle (use with smooth=True)."""
    r = min(r, (x2 - x1) / 2.0, (y2 - y1) / 2.0)
    return [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
            x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]


def quad_bezier(p0, c, p1, t):
    u = 1 - t
    return (u * u * p0[0] + 2 * u * t * c[0] + t * t * p1[0],
            u * u * p0[1] + 2 * u * t * c[1] + t * t * p1[1])


def ll_to_vec(lat, lon):
    phi, lam = math.radians(lat), math.radians(lon)
    return (math.cos(phi) * math.sin(lam), math.sin(phi), math.cos(phi) * math.cos(lam))


def vec_to_ll(v):
    x, y, z = v
    return math.degrees(math.asin(clamp(y, -1, 1))), math.degrees(math.atan2(x, z))


def ang_dist(a, b):
    """Angle in degrees between two (lat, lon) points."""
    va, vb = ll_to_vec(*a), ll_to_vec(*b)
    d = clamp(sum(p * q for p, q in zip(va, vb)), -1, 1)
    return math.degrees(math.acos(d))


def midpoint(a, b):
    va, vb = ll_to_vec(*a), ll_to_vec(*b)
    s = [p + q for p, q in zip(va, vb)]
    n = math.sqrt(sum(v * v for v in s)) or 1.0
    return vec_to_ll([v / n for v in s])


def slerp(a, b, t):
    va, vb = ll_to_vec(*a), ll_to_vec(*b)
    d = clamp(sum(p * q for p, q in zip(va, vb)), -1, 1)
    om = math.acos(d)
    if om < 1e-6:
        return a
    s = math.sin(om)
    k1, k2 = math.sin((1 - t) * om) / s, math.sin(t * om) / s
    return vec_to_ll([k1 * p + k2 * q for p, q in zip(va, vb)])


def densify(poly, step=5.0):
    """Insert points on long edges so polygons curve nicely on the sphere."""
    out = []
    n = len(poly)
    for i in range(n):
        lo1, la1 = poly[i]
        lo2, la2 = poly[(i + 1) % n]
        d = max(abs(lo2 - lo1), abs(la2 - la1))
        k = max(1, int(d / step))
        for j in range(k):
            f = j / k
            out.append((lo1 + (lo2 - lo1) * f, la1 + (la2 - la1) * f))
    return out


# =====================================================================
# 3. DATA — simplified world map, cities, demo languages
# =====================================================================
# (lon, lat) outlines — deliberately simple, this is a stylised globe.
NORTH_AMERICA = [(-168, 66), (-162, 70), (-156, 71.3), (-141, 69.6), (-128, 70), (-115, 68.5),
    (-100, 68), (-95, 72), (-88, 68.5), (-82, 68.5), (-81, 63), (-90, 59), (-93, 57), (-85, 55),
    (-80, 52), (-78, 56), (-77, 60), (-70, 61), (-64, 60), (-61, 56), (-56, 52), (-60, 48),
    (-66, 45), (-70, 43), (-70, 41.5), (-74, 40.5), (-76, 37), (-76, 35), (-81, 31.5), (-80, 27),
    (-80.5, 25.2), (-82, 27), (-83, 29.5), (-86, 30.3), (-89.5, 30), (-92, 29.5), (-95, 28.8),
    (-97.3, 26), (-97.8, 22), (-96, 19), (-94, 18.3), (-91, 18.7), (-90.5, 21), (-87, 21.5),
    (-87.5, 18), (-88.3, 15.8), (-84, 15.7), (-83.4, 11), (-81.5, 8.8), (-79.5, 9.5), (-77.5, 8.7),
    (-78.5, 7.3), (-80.5, 7.4), (-83, 8.3), (-85.6, 10.3), (-87.5, 13), (-91.5, 14), (-94.5, 16),
    (-97, 15.8), (-101, 17.3), (-105.3, 20), (-105.7, 22.5), (-110, 27), (-114, 31), (-117, 32.5),
    (-118.5, 34), (-121, 35.5), (-122.5, 37.7), (-124, 40.5), (-124, 46), (-124.7, 48.4),
    (-127, 50.5), (-130, 54), (-133, 57), (-137, 58.6), (-141, 60), (-146, 60.7), (-150, 59.5),
    (-152, 58), (-156, 57), (-160, 55.8), (-163, 54.8), (-160, 58.5), (-162, 60), (-165, 62),
    (-165, 64.5)]
SOUTH_AMERICA = [(-77, 8.5), (-75, 11), (-72, 12), (-71, 11), (-68, 10.6), (-64, 10.5), (-61, 9),
    (-57, 6), (-52, 4.5), (-50, 1), (-50, -1), (-45, -1.5), (-40, -3), (-35, -5.5), (-35, -9),
    (-37.5, -12), (-39, -15), (-39.5, -19), (-41, -22), (-44, -23), (-48, -25.5), (-48.5, -28),
    (-51, -31), (-53, -34), (-57, -35), (-57, -38), (-62, -39), (-65, -41), (-64.5, -43.5),
    (-66, -46), (-68, -49), (-69, -52), (-68.5, -54), (-72, -54), (-74, -51), (-75.5, -47),
    (-74, -42), (-73.5, -37), (-71.5, -32), (-70.5, -26), (-70, -20), (-71, -17.5), (-76, -14),
    (-78, -11), (-81, -6), (-80.5, -2.5), (-80, 0), (-78.5, 2), (-77.5, 4.5), (-77, 7)]
GREENLAND = [(-73, 78), (-68, 81), (-55, 83), (-35, 83.5), (-20, 82), (-19, 76), (-21, 72),
    (-24, 70.5), (-32, 68), (-40, 65), (-43, 60), (-48, 61), (-52, 64), (-54, 67), (-56, 70),
    (-60, 75), (-66, 76)]
BAFFIN = [(-80, 63.5), (-72, 62), (-65, 63), (-62, 66.5), (-66, 69), (-73, 71), (-80, 73.5),
    (-88, 72.5), (-90, 69.5), (-84, 67), (-78, 66)]
ELLESMERE = [(-90, 77), (-78, 76), (-65, 80), (-72, 83), (-90, 82), (-95, 79)]
EURASIA = [(-9, 37), (-9, 39.5), (-9.3, 43), (-8, 43.7), (-2, 43.5), (-1.5, 46), (-4.5, 48.3),
    (-1.5, 48.7), (1.5, 50.2), (4, 51.5), (8, 53.6), (8.5, 56.5), (10.5, 57.5), (10.5, 55),
    (12, 54.3), (14, 54), (18.5, 54.5), (21, 55.5), (21, 57.5), (24, 57.3), (23.5, 59.3),
    (28, 59.8), (30, 60), (23, 60), (21.5, 61), (21.5, 63.5), (25, 65), (22, 66), (17.5, 62.5),
    (19, 60), (16.5, 57), (14, 55.5), (12.5, 56.5), (11, 59), (8, 58), (5.5, 58.8), (5, 62),
    (9, 63.5), (12.5, 66), (15.5, 68.8), (20, 70), (26, 71), (31, 70.5), (33, 69.3), (41, 67),
    (41, 66), (44, 66.5), (45, 68), (52, 68.4), (58, 68.8), (60, 69.8), (66.5, 70.5), (69, 73),
    (73, 72.5), (80, 73.5), (87, 75), (100, 77), (104, 77.7), (112, 76), (113, 73.7), (120, 73),
    (128, 73.3), (135, 71.5), (141, 72.5), (150, 71.5), (160, 69.7), (168, 69.5), (176, 69),
    (180, 68.5), (180, 65), (178, 64.5), (174, 62.5), (170, 60.3), (164, 59.8), (163, 57.5),
    (160, 54.5), (156.8, 51), (155.7, 55.5), (156, 58), (161, 60.8), (155, 59.3), (150, 59.5),
    (143, 59.3), (140, 57.5), (137, 54), (140.5, 53), (141, 49), (138, 46), (135, 43), (131, 42.5),
    (129.5, 40.5), (128, 38.5), (129.4, 36), (129, 35), (126.5, 34.5), (126, 37), (125, 39.5),
    (121.5, 40.5), (122, 40), (121, 38.8), (118, 38), (119, 36), (121, 36.8), (120, 35),
    (121.5, 32), (121.8, 30.7), (122, 29.5), (120.5, 26.5), (119.5, 25.5), (117, 23.5),
    (114, 22.3), (110.5, 21), (108, 21.5), (106.5, 20), (105.7, 18.5), (107, 16), (109, 12.5),
    (107, 10.5), (105, 8.6), (104.5, 10), (102.5, 12), (100.5, 13.5), (99.5, 10), (101, 6.8),
    (103.3, 4), (104.2, 1.4), (102, 2.5), (100.5, 5), (98.5, 8.5), (98, 12), (97.5, 16.5),
    (94.5, 16), (94, 19), (92, 21.5), (91, 22.5), (89, 21.8), (87, 21), (85, 19.5), (82, 17),
    (80.2, 15), (79.8, 11), (78, 8.5), (76.5, 9.5), (75, 12.5), (73, 17.5), (72.8, 21), (70, 20.8),
    (68.8, 22.5), (70, 23.5), (67.5, 24.3), (66.5, 25.2), (62, 25.2), (58, 25.5), (57, 27),
    (53, 26.8), (51, 28.5), (49, 30), (48, 29.5), (49.5, 27), (50.2, 26.2), (50.8, 24.8),
    (51.6, 24.3), (54, 24.2), (56, 26.2), (57, 23.7), (59.5, 22.4), (58, 20.5), (55, 17.5),
    (52, 16), (48, 14), (44.5, 12.8), (43.2, 13.2), (42.7, 15.8), (41, 19), (39, 21.5),
    (37.2, 25), (35, 28), (34.5, 29.5), (35, 31.5), (35, 33.5), (36, 34.5), (36, 36.5), (34, 36.2),
    (31, 36.7), (28, 36.7), (26.5, 38.5), (26.3, 40), (24, 40.8), (23, 40.6), (24, 38),
    (23, 36.5), (21.5, 37), (20.5, 39), (19.5, 41), (19, 42.2), (16, 43.5), (13.7, 45.3),
    (12.3, 45.3), (12.5, 44), (14, 42.2), (16, 41.5), (18.5, 40.2), (17, 39), (16.5, 38),
    (15.6, 38), (15.8, 40), (13, 41.3), (10.5, 43), (8.8, 44.3), (7.5, 43.8), (4, 43.4),
    (3, 42.4), (3.2, 41.7), (0.8, 41), (0, 39.5), (-0.5, 38.5), (-1.5, 37.2), (-4.5, 36.7),
    (-5.6, 36), (-6.3, 36.8), (-7.5, 37.2)]
AFRICA = [(-5.9, 35.8), (-2, 35.2), (2, 36.8), (10, 37.2), (11, 35.5), (10.2, 33.8), (13, 32.8),
    (15.2, 32.3), (19, 30.3), (20, 32), (23, 32.7), (25, 31.8), (29, 30.9), (32, 31.2),
    (32.5, 29.8), (34, 27), (35.5, 24), (37.2, 21), (38.7, 18), (41, 14.7), (43.2, 12.8),
    (44, 10.5), (51.2, 11.8), (51, 10), (49.8, 6.5), (48, 4.5), (45, 2), (41.5, -1.7), (40, -4),
    (39, -6.5), (39.5, -9), (40.5, -11), (40.5, -15), (37, -17.8), (35, -20), (35, -22.5),
    (32.9, -25.8), (32.8, -28.5), (30, -31.5), (27, -33.6), (22, -34.2), (20, -34.8),
    (18.4, -34), (17.8, -31), (16, -28.5), (14.8, -25), (14.2, -22), (11.8, -17), (13.5, -12),
    (12, -6), (9, -1), (9.5, 3.5), (8.5, 4.5), (6.5, 4.3), (4.5, 6.2), (1, 5.8), (-2, 4.7),
    (-4.5, 5.2), (-7.5, 4.4), (-10.5, 6.5), (-13, 8.2), (-14.7, 10.8), (-16.5, 12.5),
    (-17.5, 14.7), (-16.5, 19.5), (-16, 22), (-14.5, 26), (-12, 28), (-9.8, 29.8), (-9.7, 32.5),
    (-8, 33.5), (-6.5, 34.5)]
AUSTRALIA = [(113.5, -22), (114, -26), (115, -34), (118, -35), (122, -34), (124, -33),
    (129, -31.5), (132, -32), (135.5, -34.7), (137.5, -33), (138, -35.5), (140, -38),
    (144, -38.3), (146, -39), (149.5, -37.5), (150.5, -35), (153, -31), (153.5, -28),
    (152.5, -25), (150, -22.5), (148.5, -20), (146, -18.5), (145.5, -15), (143.5, -13),
    (142.5, -10.7), (141.5, -13), (141.8, -17), (140, -17.6), (137.5, -16), (135.5, -15),
    (136.7, -12.2), (132, -11.5), (130, -13), (129.5, -15), (127, -14), (125, -15.5),
    (123, -17), (122, -18), (120, -19.8), (117, -20.7)]
ISLANDS = [
    [(-5.7, 50), (-3, 50.7), (1.4, 51), (1.7, 52.7), (0, 53.5), (-1.5, 55), (-2, 56.2),
     (-1.7, 57.5), (-3.5, 58.6), (-5, 58.6), (-6, 57), (-5.5, 55.5), (-4.5, 54.7), (-3, 54.9),
     (-3, 53.5), (-4.5, 53), (-4.3, 52), (-5.2, 51.7), (-3.5, 51.4), (-4.5, 50.3)],   # Britain
    [(-10, 51.8), (-6.3, 52.2), (-6, 53.8), (-5.5, 54.6), (-7.5, 55.3), (-9.5, 54.2), (-10, 53)],
    [(-24, 65), (-22, 66.4), (-16, 66.5), (-13.5, 65), (-15, 64.2), (-19, 63.4), (-22.5, 63.8)],
    [(130.9, 33.9), (132.5, 35.4), (135.5, 35.7), (136.8, 37.3), (139.5, 38.3), (140, 40.8),
     (141.5, 41.4), (142, 39.5), (141, 37.5), (140.8, 35.7), (139.8, 35), (138, 34.6),
     (136.7, 34.5), (135, 33.6), (133, 34), (131.5, 34.2)],                            # Honshu
    [(140, 42), (141.5, 43.5), (142, 45.4), (145.5, 44), (143.5, 42.9), (141, 41.9)],  # Hokkaido
    [(129.7, 33), (131, 33.9), (131.8, 32), (130.5, 31), (129.8, 32.5)],               # Kyushu
    [(132.7, 33.9), (134.5, 34.2), (134.3, 33.3), (133, 32.8)],                        # Shikoku
    [(142, 46), (143, 49), (143, 54), (142, 54), (142, 50)],                           # Sakhalin
    [(95.3, 5.6), (98, 4), (100, 2), (104, -1), (106, -3), (105.5, -5.8), (102, -4),
     (99, -1.5), (96, 2.5)],                                                            # Sumatra
    [(105.2, -6.8), (108, -6.3), (112, -6.8), (114.5, -7.8), (111, -8.3), (107, -7.7)],  # Java
    [(109, 1.5), (111, 2.4), (114, 4.5), (117, 7), (119, 5), (118, 1), (116.5, -2.5),
     (114.5, -4), (111, -3), (110, -1)],                                                # Borneo
    [(119.5, -5), (120.5, -2.5), (119.8, 0.5), (121, 1.3), (124.5, 1), (122, -1), (123, -4),
     (121.5, -4.8)],                                                                    # Sulawesi
    [(131, -0.8), (134, -0.8), (138, -1.7), (141, -2.6), (145, -4.5), (148, -6), (150.5, -10.5),
     (147, -10), (144, -7.7), (141, -9), (138, -8.3), (137.8, -5), (134.5, -3.5), (132, -2.8)],
    [(120, 18.5), (122.5, 18.3), (122, 14.2), (124, 13), (121, 13.5), (120.5, 16)],    # Luzon
    [(122, 7), (126.5, 9), (126.3, 6.2), (124, 6.5)],                                  # Mindanao
    [(120.2, 23), (121.5, 25.2), (121.8, 24), (120.8, 22)],                            # Taiwan
    [(79.8, 6.5), (81.8, 7.2), (81.5, 8.7), (80, 9.5), (79.6, 8)],                     # Sri Lanka
    [(172.7, -34.5), (174.5, -36.5), (176, -37.5), (178.5, -37.7), (175.5, -41.5),
     (174.5, -41.3), (173, -39.2)],                                                     # NZ north
    [(172.7, -40.6), (174.3, -41.7), (172.7, -43.5), (170.5, -46), (166.5, -46), (168, -44),
     (171, -42.5)],                                                                     # NZ south
    [(44, -25), (47, -25), (50, -15), (49, -12), (44, -17)],                           # Madagascar
    [(-85, 21.9), (-82.5, 23), (-79.5, 22.5), (-77, 20.6), (-74.2, 20.2), (-77.5, 19.9),
     (-80, 21.7)],                                                                      # Cuba
    [(-74.4, 18.5), (-72.5, 19.9), (-69.5, 19.3), (-68.5, 18.4), (-71, 17.8)],
    [(-59.3, 47.6), (-56, 51.6), (-52.7, 49.5), (-52.8, 47.5), (-55, 46.8)],
]
LAND_POLYS = [NORTH_AMERICA, SOUTH_AMERICA, GREENLAND, BAFFIN, ELLESMERE, EURASIA,
              AFRICA, AUSTRALIA] + ISLANDS
BLACK_SEA = [(28, 41.5), (28, 43.5), (30, 45.5), (33, 46), (35, 45), (38, 47), (40, 43.5),
             (41.5, 41.5), (36, 41.5), (32, 41.5)]
CASPIAN = [(47, 45), (50, 46), (53, 45), (53, 41), (54, 37), (50, 37), (49, 40), (47, 43)]
SEA_POLYS = [BLACK_SEA, CASPIAN]

# (lat, lon) of big cities — only used for the little night-side "city lights"
CITIES = [(40.7, -74), (34, -118.2), (19.4, -99.1), (-23.5, -46.6), (-34.6, -58.4), (4.7, -74),
    (51.5, -0.1), (48.9, 2.35), (40.4, -3.7), (52.5, 13.4), (55.75, 37.6), (41, 29), (30, 31.2),
    (6.5, 3.4), (-1.3, 36.8), (-26.2, 28), (24.7, 46.7), (35.7, 51.4), (24.9, 67), (31.5, 74.3),
    (28.6, 77.2), (19, 72.8), (23.8, 90.4), (13.75, 100.5), (1.35, 103.8), (-6.2, 106.8),
    (39.9, 116.4), (31.2, 121.5), (37.6, 127), (35.7, 139.7), (-33.9, 151.2), (43.7, -79.4),
    (41.9, -87.6), (49.3, -123), (-12, -77), (-33.4, -70.7), (-33.9, 18.4), (14.6, 121),
    (22.3, 114.2), (33.3, 44.4), (41.9, 12.5), (50.45, 30.5), (-37.8, 145), (-36.85, 174.8),
    (25.8, -80.2), (59.9, 30.3), (13.1, 80.3), (33.7, 73), (35.2, 129)]


@dataclass
class Language:
    key: str
    name: str
    native: str
    script: str
    region: str      # short "Associated Region"
    target: str      # "Target Area" highlighted on the globe
    family: str
    lat: float
    lon: float
    zone: float      # highlight radius in degrees
    sample: str
    note: str


LANGS = [
    Language("urdu", "Urdu", "اردو", "Perso-Arabic", "South Asia", "Pakistan / North India",
             "Indo-European", 30.4, 69.3, 9.0, "مجھے مصنوعی ذہانت بہت پسند ہے",
             "Written right-to-left in the Perso-Arabic script, often in a flowing Nastaliq style."),
    Language("english", "English", "English", "Latin", "British Isles / Global",
             "United Kingdom", "Indo-European", 52.5, -1.5, 4.5,
             "I enjoy learning how machines understand language.",
             "Germanic roots with a huge amount of Latin and French vocabulary."),
    Language("arabic", "Arabic", "العربية", "Arabic", "Middle East",
             "Arabian Peninsula", "Afro-Asiatic", 24.0, 45.0, 12.0, "مرحبا، كيف حالك اليوم؟",
             "Written right-to-left; most letters change shape depending on their place in a word."),
    Language("french", "French", "Français", "Latin", "Europe / Francophone",
             "France", "Indo-European", 46.6, 2.3, 5.5, "Bonjour, comment allez-vous ?",
             "A Romance language, official in many countries across Europe, Africa and beyond."),
    Language("spanish", "Spanish", "Español", "Latin", "Iberia / Latin America",
             "Spain", "Indo-European", 40.2, -3.7, 5.5, "Hola, ¿cómo estás?",
             "A Romance language spoken in Spain and across most of Latin America."),
    Language("japanese", "Japanese", "日本語", "Japanese (Kanji + Kana)", "East Asia",
             "Japan", "Japonic", 36.5, 138.2, 6.0, "こんにちは、元気ですか？",
             "Mixes Kanji, Hiragana and Katakana inside a single writing system."),
    Language("chinese", "Chinese", "中文", "Chinese characters (Hanzi)", "East Asia",
             "China", "Sino-Tibetan", 34.5, 104.0, 13.0, "你好，很高兴认识你",
             "Written with Hanzi; spoken forms include Mandarin and Cantonese."),
    Language("german", "German", "Deutsch", "Latin", "Central Europe",
             "Germany", "Indo-European", 51.0, 10.3, 4.5, "Hallo, wie geht es dir?",
             "A Germanic language; all nouns are capitalised in writing."),
    Language("hindi", "Hindi", "हिन्दी", "Devanagari", "South Asia",
             "Northern India", "Indo-European", 25.5, 79.0, 8.0, "नमस्ते, आप कैसे हैं?",
             "Written left-to-right in Devanagari; closely related to Urdu in everyday speech."),
    Language("russian", "Russian", "Русский", "Cyrillic", "Eastern Europe / Northern Asia",
             "Russia", "Indo-European", 56.0, 40.0, 14.0, "Привет, как дела?",
             "A Slavic language written in the Cyrillic alphabet."),
    Language("korean", "Korean", "한국어", "Hangul", "East Asia",
             "Korean Peninsula", "Koreanic", 36.5, 127.8, 3.8, "안녕하세요, 잘 지내세요?",
             "Hangul is a purpose-designed alphabet arranged in syllable blocks."),
    Language("portuguese", "Portuguese", "Português", "Latin", "Iberia / Brazil",
             "Brazil", "Indo-European", -12.0, -52.0, 12.0, "Olá, tudo bem com você?",
             "A Romance language spoken in Portugal, Brazil and parts of Africa."),
    Language("turkish", "Turkish", "Türkçe", "Latin", "Anatolia / West Asia",
             "Türkiye", "Turkic", 39.0, 35.0, 5.5, "Merhaba, nasılsın?",
             "A Turkic language, written in the Latin alphabet since 1928."),
    Language("swahili", "Swahili", "Kiswahili", "Latin", "East Africa",
             "Tanzania / Kenya", "Niger-Congo (Bantu)", -5.0, 36.0, 8.0,
             "Habari, karibu sana rafiki.",
             "A Bantu language used widely across East Africa as a shared language."),
]
LANG = {l.key: l for l in LANGS}
SAMPLE_KEYS = ["urdu", "english", "arabic", "japanese", "french", "spanish",
               "chinese", "german", "russian"]


# =====================================================================
# 4. LANGUAGE DETECTOR (DEMO ONLY)
# =====================================================================
@dataclass
class LanguageSignal:
    """The result of a demo detection."""
    key: str
    confidence: int     # shown as "Demo Confidence" — simulated, not a real probability
    text: str
    chars: int


class LanguageDetectorDemo:
    """Simulated detection: look at which writing system the text uses, then
    (for Latin text) count a few telltale letters and common words. It is
    NOT real NLP and is intentionally tiny."""

    URDU_LETTERS = set("\u0679\u0688\u0691\u06BA\u06D2\u06D3\u06C1\u06BE\u06AF\u0686"
                       "\u067E\u0698\u06A9\u06CC")
    WORDS = {
        "english": "the is are am i you he she we they this that with how what where why hello hi "
                   "thanks thank love like enjoy learning machines understand language and to of in "
                   "it for on my your can do does not good morning",
        "french": "bonjour salut merci comment allez vous je suis est les des une oui non très "
                  "bien avec pour dans nous ça bonsoir revoir madame monsieur aime",
        "spanish": "hola cómo como estás estas gracias buenos días dias buenas tardes noches por "
                   "favor soy eres está muy bien qué que amigo gusta el la los las",
        "german": "hallo wie geht es dir ich bin nicht und danke bitte ist das der die den ein "
                  "eine guten morgen tag gut sehr mit",
        "portuguese": "olá ola tudo bem você voce obrigado obrigada não nao muito eu sou está bom "
                      "dia com uma",
        "turkish": "merhaba nasılsın nasilsin teşekkürler tesekkurler evet hayır ben sen iyi "
                   "günaydın selam",
        "swahili": "habari jambo asante karibu sana rafiki mzuri pole ndiyo hapana",
    }
    CHARS = {"french": ("éèêëàâçùûôîïœ", 1), "spanish": ("¿¡ñ", 3), "german": ("äöüß", 2),
             "portuguese": ("ãõ", 2), "turkish": ("ışğİ", 3)}

    def __init__(self):
        self.wordsets = {k: set(v.split()) for k, v in self.WORDS.items()}

    @staticmethod
    def _script_counts(text):
        n = dict(arabic=0, kana=0, han=0, hangul=0, deva=0, cyr=0, latin=0)
        for ch in text:
            o = ord(ch)
            if 0x0600 <= o <= 0x06FF or 0x0750 <= o <= 0x077F or 0xFB50 <= o <= 0xFDFF or 0xFE70 <= o <= 0xFEFF:
                n["arabic"] += 1
            elif 0x3040 <= o <= 0x30FF or 0x31F0 <= o <= 0x31FF:
                n["kana"] += 1
            elif 0x4E00 <= o <= 0x9FFF or 0x3400 <= o <= 0x4DBF:
                n["han"] += 1
            elif 0xAC00 <= o <= 0xD7AF or 0x1100 <= o <= 0x11FF:
                n["hangul"] += 1
            elif 0x0900 <= o <= 0x097F:
                n["deva"] += 1
            elif 0x0400 <= o <= 0x04FF:
                n["cyr"] += 1
            elif ch.isalpha() and o < 0x250:
                n["latin"] += 1
        return n

    def detect(self, text):
        chars = len([c for c in text if not c.isspace()])
        n = self._script_counts(text)
        conf_script = 94 + (len(text) % 4)          # 94-97, deterministic
        if n["kana"]:
            return LanguageSignal("japanese", conf_script, text, chars)
        if n["hangul"] > 0 and n["hangul"] >= n["han"]:
            return LanguageSignal("korean", conf_script, text, chars)
        top = max(n, key=lambda k: n[k])
        if n[top] > 0 and top != "latin":
            if top == "arabic":
                urdu = any(ch in self.URDU_LETTERS for ch in text)
                return LanguageSignal("urdu" if urdu else "arabic", conf_script, text, chars)
            key = {"han": "chinese", "deva": "hindi", "cyr": "russian"}[top]
            return LanguageSignal(key, conf_script, text, chars)
        # Latin script: score keywords and telltale letters
        words = re.findall(r"[^\W\d_]+", text.lower())
        scores = {}
        for lang, ws in self.wordsets.items():
            scores[lang] = 2 * sum(1 for w in words if w in ws)
        for lang, (letters, wgt) in self.CHARS.items():
            scores[lang] += wgt * sum(1 for ch in text.lower() if ch in letters)
        best = max(scores, key=lambda k: scores[k])
        if scores[best] == 0:
            return LanguageSignal("english", 72, text, chars)   # honest low-confidence default
        return LanguageSignal(best, int(clamp(76 + scores[best] * 2, 76, 97)), text, chars)


# =====================================================================
# 5. PARTICLE SYSTEM — text characters that become a signal
# =====================================================================
class ParticleSystem:
    def __init__(self, canvas):
        self.c = canvas
        self.rng = random.Random(7)
        self.chars = []
        self.ripples = []
        self.dust = []
        for _ in range(54):
            v = self.rng.uniform(-0.22, 0.22)
            self.dust.append(dict(a=self.rng.uniform(0, 6.283), r=self.rng.uniform(1.04, 1.55),
                                  v=v if abs(v) > 0.03 else 0.08, s=self.rng.uniform(0.8, 2.1),
                                  ph=self.rng.uniform(0, 6.28), k=self.rng.choice(("ivory", "cyan", "gold"))))

    def spawn_text(self, text, box, entry):
        """Every character of the sentence becomes one particle that flies
        along a curve into the globe. Returns how long the whole flight takes."""
        glyphs = [ch for ch in text if not ch.isspace()]
        if len(glyphs) > 46:
            step = len(glyphs) / 46.0
            glyphs = [glyphs[int(i * step)] for i in range(46)]
        x1, y1, x2, y2 = box
        self.chars = []
        end, n = 0.0, max(1, len(glyphs))
        for i, ch in enumerate(glyphs):
            p0 = (self.rng.uniform(x1 + 12, x2 - 12), self.rng.uniform(y1 + 12, y2 - 12))
            ctrl = ((p0[0] + entry[0]) / 2, min(p0[1], entry[1]) - self.rng.uniform(60, 150))
            delay = i / n * 0.95 + self.rng.uniform(0, 0.12)
            dur = self.rng.uniform(0.9, 1.25)
            self.chars.append(dict(ch=ch, delay=delay, dur=dur, age=0.0, p0=p0, c=ctrl,
                                   p1=entry, landed=False))
            end = max(end, delay + dur)
        return end

    def add_ripple(self, x, y, color, life=1.0, r=30, delay=0.0):
        self.ripples.append(dict(x=x, y=y, age=-delay, life=life, r=r, color=color))

    def clear(self):
        self.chars = []
        self.ripples = []

    def update(self, dt):
        for p in self.chars:
            p["age"] += dt
            if not p["landed"] and p["age"] >= p["delay"] + p["dur"]:
                p["landed"] = True
                self.add_ripple(p["p1"][0] + self.rng.uniform(-4, 4), p["p1"][1] + self.rng.uniform(-8, 8),
                                P["cyan"], 0.8, 22)
        self.chars = [p for p in self.chars if p["age"] < p["delay"] + p["dur"] + 0.05]
        for r in self.ripples:
            r["age"] += dt
        self.ripples = [r for r in self.ripples if r["age"] < r["life"]]
        for d in self.dust:
            d["a"] += d["v"] * dt

    def draw_dust(self, cx, cy, R, t):
        c = self.c
        cols = {"ivory": P["ivory"], "cyan": P["cyan"], "gold": P["gold"]}
        for d in self.dust:
            x = cx + R * d["r"] * math.cos(d["a"])
            y = cy + R * d["r"] * 0.86 * math.sin(d["a"])
            if math.hypot(x - cx, y - cy) < R * 1.005:
                continue
            tw = 0.5 + 0.5 * math.sin(t * 1.7 + d["ph"])
            col = mix("#0a4577", cols[d["k"]], 0.35 + 0.55 * tw)
            s = d["s"]
            c.create_oval(x - s, y - s, x + s, y + s, fill=col, outline="", tags="dyn")

    def draw_ripples(self):
        c = self.c
        for r in self.ripples:
            if r["age"] < 0:
                continue
            u = r["age"] / r["life"]
            rad = 4 + r["r"] * ease_out(u)
            col = mix(r["color"], "#0e6f92", u ** 0.8)
            c.create_oval(r["x"] - rad, r["y"] - rad, r["x"] + rad, r["y"] + rad,
                          outline=col, width=2 if u < 0.5 else 1, tags="dyn")

    def draw_chars(self, app):
        c = self.c
        for p in self.chars:
            a = p["age"] - p["delay"]
            if a < 0:      # still waiting inside the input chamber: shimmer
                x, y = p["p0"]
                y += math.sin(app.t * 3 + x) * 2
                col = mix(P["ivory"], P["cyan"], 0.35 + 0.3 * math.sin(app.t * 4 + y))
                c.create_text(x, y, text=p["ch"], fill=col, font=app.F(15, "bold"), tags="dyn")
                continue
            u = clamp(a / p["dur"], 0, 1)
            e = smoothstep(u) * 0.85 + u * 0.15
            x, y = quad_bezier(p["p0"], p["c"], p["p1"], e)
            col = mix(P["ivory"], P["gold"], u * 2) if u < 0.5 else mix(P["gold"], P["cyan"], (u - 0.5) * 2)
            for k in (3, 2, 1):      # little glowing trail
                uu = max(0.0, u - 0.035 * k)
                tx, ty = quad_bezier(p["p0"], p["c"], p["p1"], smoothstep(uu) * 0.85 + uu * 0.15)
                tr = 2.2 - 0.4 * k
                c.create_oval(tx - tr, ty - tr, tx + tr, ty + tr,
                              fill=mix("#0a4577", col, 0.5 - 0.1 * k), outline="", tags="dyn")
            if u < 0.55:
                c.create_text(x, y, text=p["ch"], fill=col, font=app.F(15, "bold"), tags="dyn")
            else:
                r = 3.2 * (1 - (u - 0.55) / 0.45) + 0.8
                c.create_oval(x - r, y - r, x + r, y + r, fill=col, outline="", tags="dyn")


# =====================================================================
# 6. GLOBE ANIMATOR — rotation physics
# =====================================================================
class GlobeAnimator:
    """Owns the globe's centre longitude / tilt and its speed.

    idle    : slow, elegant spin
    scan    : speeds up while the signal arrives
    seek    : fast spin that eases out and STOPS on the target
    located : parked (speed 0); later 'resume_idle' spins up again"""

    def __init__(self):
        self.lon = 15.0
        self.tilt = IDLE_TILT
        self.speed = IDLE_SPEED * SPIN_DIRECTION
        self.target_speed = self.speed
        self.mode = "idle"
        self.on_arrive = None
        self.accel = 1.4
        self.s_t = self.s_dur = self.s_df = self.s_v0 = 0.0
        self.s_lon0 = self.s_tilt0 = self.s_tilt1 = self.s_target = 0.0

    @staticmethod
    def _profile(u):
        """0..1 -> 0..1. Quick start, long gentle slow-down, zero speed at the
        end (that is what makes the stop feel intentional)."""
        g = u ** 0.72
        return g * g * (3 - 2 * g)

    def begin_scan(self):
        self.mode = "scan"
        self.target_speed = 38.0 * SPIN_DIRECTION
        self.accel = 1.6

    def resume_idle(self):
        self.mode = "idle"
        self.target_speed = IDLE_SPEED * SPIN_DIRECTION
        self.accel = 0.9

    def reset(self):
        self.on_arrive = None
        self.resume_idle()

    def seek_to(self, lat, lon, spins=True, on_arrive=None):
        self.mode = "seek"
        self.on_arrive = on_arrive
        self.s_lon0 = self.lon
        self.s_t = 0.0
        d = (lon - self.lon) * SPIN_DIRECTION
        if spins:                       # always turn forward, at least ~half a turn
            df = d % 360.0
            if df < 150:
                df += 360.0
            self.s_dur = 3.4 + df / 150.0
            self.s_v0 = clamp(self.speed * SPIN_DIRECTION, 0.0, 60.0)
        else:                           # short, direct turn (click on a beacon)
            df = ((d + 180.0) % 360.0) - 180.0
            self.s_dur = 1.5 + abs(df) / 110.0
            self.s_v0 = 0.0
        self.s_df = df
        self.s_target = lon
        self.s_tilt0 = self.tilt
        self.s_tilt1 = clamp(lat * 0.6, -14.0, 30.0)

    def update(self, dt):
        if self.mode == "seek":
            self.s_t += dt
            u = clamp(self.s_t / self.s_dur, 0.0, 1.0)
            h = u * (1 - u) ** 2          # keeps the starting speed continuous
            self.lon = self.s_lon0 + SPIN_DIRECTION * (self.s_df * self._profile(u) + self.s_v0 * self.s_dur * h)
            self.tilt = lerp(self.s_tilt0, self.s_tilt1, smoothstep(u))
            self.speed = 0.0
            if u >= 1.0:
                self.lon = self.s_target
                self.mode = "located"
                self.target_speed = 0.0
                cb, self.on_arrive = self.on_arrive, None
                if cb:
                    cb()
        else:
            self.speed += (self.target_speed - self.speed) * min(1.0, dt * self.accel)
            self.lon += self.speed * dt
            if self.mode == "idle":
                self.tilt += (IDLE_TILT - self.tilt) * min(1.0, dt * 0.35)
        self.lon = ((self.lon + 180.0) % 360.0) - 180.0


# =====================================================================
# 7. GLOBE RENDERER — the 3D illusion (orthographic projection)
# =====================================================================
class GlobeRenderer:
    """Draws the Earth on a Canvas. Every latitude/longitude is projected onto
    the visible disc; parts on the far side are clipped away exactly at the
    horizon, so continents really slide around a sphere."""

    LIGHT = (-0.40, 0.34, 0.85)      # sun direction in view space

    def __init__(self, canvas):
        self.c = canvas
        self.cx = self.cy = 0.0
        self.R = 200.0
        n = math.sqrt(sum(v * v for v in self.LIGHT))
        self.L = tuple(v / n for v in self.LIGHT)
        self.land = [self._prep(densify(p, 5.0)) for p in LAND_POLYS]
        self.seas = [self._prep(densify(p, 5.0)) for p in SEA_POLYS]
        self.cities = [self._pt(la, lo) for la, lo in CITIES]
        self.meridians = [[self._pt(la, lo) for la in range(-84, 85, 6)] for lo in range(-180, 180, 30)]
        self.parallels = [(la, [self._pt(la, lo) for lo in range(-180, 181, 6)]) for la in (-60, -30, 0, 30, 60)]
        self.clouds = self._make_clouds()
        self.night_specs = []
        self.term_line = []

    # ---- preparation -------------------------------------------------
    @staticmethod
    def _pt(lat, lon):
        phi = math.radians(lat)
        return (math.radians(lon), math.sin(phi), math.cos(phi))

    def _prep(self, poly):
        return [self._pt(la, lo) for lo, la in poly]

    def _make_clouds(self):
        rng = random.Random(11)
        out = []
        for _ in range(20):
            lat, lon = rng.uniform(-55, 60), rng.uniform(-180, 180)
            puffs = []
            for _ in range(3):
                plat, dlon = lat + rng.uniform(-3, 3), rng.uniform(-6, 6)
                w, h = rng.uniform(3, 6.5), rng.uniform(1.1, 2.3)
                pts = []
                for k in range(10):
                    a = 2 * math.pi * k / 10
                    j = rng.uniform(0.8, 1.15)
                    la = plat + h * math.sin(a) * j
                    dl = dlon + w * math.cos(a) * j
                    pts.append((math.radians(dl), math.sin(math.radians(la)), math.cos(math.radians(la))))
                puffs.append(pts)
            phi = math.radians(lat)
            out.append((math.radians(lon), math.sin(phi), math.cos(phi), puffs))
        return out

    def set_geometry(self, cx, cy, R):
        """Called whenever the window is resized."""
        self.cx, self.cy, self.R = cx, cy, R
        Lx, Ly, Lz = self.L
        s = math.hypot(Lx, Ly)
        e1 = (Ly / s, -Lx / s)
        e2 = (-Lz * Lx / s, -Lz * Ly / s)
        th_n = math.atan2(-Ly, -Lx)             # direction of the night side
        self.night_specs = []
        for f, col in ((0.85, P["dusk1"]), (0.93, P["dusk2"]), (1.0, P["night"])):
            pts = []
            for k in range(25):                # limb arc on the night side
                a = th_n + math.pi / 2 - math.pi * k / 24
                pts += [cx + R * math.cos(a), cy - R * math.sin(a)]
            for j in range(1, 28):             # terminator (a squashed ellipse)
                t = math.pi - math.pi * j / 28
                nx = math.cos(t) * e1[0] + f * math.sin(t) * e2[0]
                ny = math.cos(t) * e1[1] + f * math.sin(t) * e2[1]
                pts += [cx + R * nx, cy - R * ny]
            self.night_specs.append((pts, col))
        self.term_line = []
        for j in range(0, 29):
            t = math.pi * j / 28
            self.term_line += [cx + R * (math.cos(t) * e1[0] + math.sin(t) * e2[0]),
                               cy - R * (math.cos(t) * e1[1] + math.sin(t) * e2[1])]

    # ---- projection --------------------------------------------------
    @staticmethod
    def view_params(lon0_deg, tilt_deg):
        t = math.radians(tilt_deg)
        return (math.radians(lon0_deg), math.sin(t), math.cos(t))

    @staticmethod
    def to_view(lonr, sl, cl, vp):
        lon0, sl0, cl0 = vp
        dl = lonr - lon0
        cd = math.cos(dl)
        return (cl * math.sin(dl), cl0 * sl - sl0 * cl * cd, sl0 * sl + cl0 * cl * cd)

    def view_ll(self, lat, lon, vp):
        lonr, sl, cl = self._pt(lat, lon)
        return self.to_view(lonr, sl, cl, vp)

    def screen(self, x, y, rad=1.0):
        return self.cx + self.R * rad * x, self.cy - self.R * rad * y

    @staticmethod
    def visible(x, y, z):
        """A point (even one floating above the surface) is visible when it is
        on the near side, or on the far side but outside the disc."""
        return z >= 0 or (x * x + y * y) >= 1.0

    def ocean(self, rho):
        return gradient([(0, "#2fb7df"), (0.55, "#1479bd"), (0.85, "#0a4a89"), (1, "#072e62")], rho)

    # ---- clipping ----------------------------------------------------
    @staticmethod
    def _limb_angle(a, b):
        t = a[2] / (a[2] - b[2])
        return math.atan2(a[1] + t * (b[1] - a[1]), a[0] + t * (b[0] - a[0]))

    def clip_poly(self, v):
        """Clip a projected polygon at the horizon; the far-side gap is closed
        with an arc along the limb. Returns flat screen coordinates or None."""
        n = len(v)
        toks, front, cross = [], False, False
        for i in range(n):
            a, b = v[i], v[(i + 1) % n]
            if a[2] >= 0:
                toks.append((0, a[0], a[1]))
                front = True
                if b[2] < 0:
                    toks.append((1, self._limb_angle(a, b)))
                    cross = True
            elif b[2] >= 0:
                toks.append((2, self._limb_angle(a, b)))
                cross = True
        if not front:
            return None
        cx, cy, R = self.cx, self.cy, self.R
        out = []
        if not cross:
            for t in toks:
                out += [cx + R * t[1], cy - R * t[2]]
            return out
        m = len(toks)
        for i, t in enumerate(toks):
            if t[0] == 0:
                out += [cx + R * t[1], cy - R * t[2]]
            elif t[0] == 1:
                a0, a1 = t[1], t[1]
                for k in range(1, m + 1):
                    tk = toks[(i + k) % m]
                    if tk[0] == 2:
                        a1 = tk[1]
                        break
                da = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
                steps = max(2, int(abs(da) / 0.12) + 1)
                for s in range(steps + 1):
                    a = a0 + da * s / steps
                    out += [cx + R * math.cos(a), cy - R * math.sin(a)]
        return out

    # ---- drawing primitives on the sphere -----------------------------
    def draw_poly(self, pts, vp, **kw):
        v = [self.to_view(l, s, cc, vp) for l, s, cc in pts]
        poly = self.clip_poly(v)
        if poly and len(poly) >= 6:
            return self.c.create_polygon(poly, tags="dyn", **kw)

    def draw_line(self, pts, vp, closed=False, rad=1.0, **kw):
        """Polyline made of the visible runs only."""
        run = []
        seq = list(pts) + ([pts[0]] if closed else [])
        for l, s, cc in seq:
            x, y, z = self.to_view(l, s, cc, vp)
            if self.visible(x, y, z) and z > -0.02:
                run.extend(self.screen(x, y, rad))
            else:
                if len(run) >= 4:
                    self.c.create_line(run, tags="dyn", **kw)
                run = []
        if len(run) >= 4:
            self.c.create_line(run, tags="dyn", **kw)

    def zone_points(self, lat, lon, rdeg, seed=0.0, wob=0.14, n=28):
        """A wobbly circle of angular radius rdeg around (lat, lon)."""
        out = []
        p1, l1 = math.radians(lat), math.radians(lon)
        for k in range(n):
            th = 2 * math.pi * k / n
            rr = rdeg * (1 + wob * math.sin(3 * th + seed) + wob * 0.5 * math.sin(5 * th + seed * 1.7))
            d = math.radians(rr)
            p2 = math.asin(clamp(math.sin(p1) * math.cos(d) + math.cos(p1) * math.sin(d) * math.cos(th), -1, 1))
            l2 = l1 + math.atan2(math.sin(th) * math.sin(d) * math.cos(p1),
                                 math.cos(d) - math.sin(p1) * math.sin(p2))
            out.append((l2, math.sin(p2), math.cos(p2)))
        return out

    # ---- the globe itself ---------------------------------------------
    def draw_base(self, tag):
        """Static ocean sphere: nested circles, shifted toward the light."""
        c, cx, cy, R = self.c, self.cx, self.cy, self.R
        N = 30
        for k in range(N):
            rho = 1 - k / N * 0.985
            r = R * rho
            off = 0.17 * R * (1 - rho)
            x, y = cx - off * 0.85, cy - off * 0.7
            c.create_oval(x - r, y - r, x + r, y + r, fill=self.ocean(rho), outline="", tags=tag)

    def draw_land(self, vp):
        for pts in self.land:
            self.draw_poly(pts, vp, fill=P["land"], outline=P["coast"], width=1)
        for pts in self.seas:
            self.draw_poly(pts, vp, fill="#1a7dbb", outline="#5bb9e0", width=1)

    def draw_overlays(self, vp, t):
        """Grid, clouds, night side, city lights, atmosphere rim."""
        c, cx, cy, R = self.c, self.cx, self.cy, self.R
        grid = mix("#3f9fd0", "#c8f2ff", 0.30)
        for pts in self.meridians:
            self.draw_line(pts, vp, fill=grid, width=1)
        for la, pts in self.parallels:
            self.draw_line(pts, vp, fill=mix(grid, "#ffffff", 0.25) if la == 0 else grid, width=1)
        # clouds drift a little faster than the ground
        drift = math.radians(t * 0.8)
        for clon, csl, ccl, puffs in self.clouds:
            x, y, z = self.to_view(clon + drift, csl, ccl, vp)
            if z < 0.15:
                continue
            col = mix("#3f9fd0", "#d4ecf6", clamp((z - 0.15) / 0.6, 0, 1) * 0.85)
            for pts in puffs:
                v = [self.to_view(clon + drift + dl, sl, cl, vp) for dl, sl, cl in pts]
                poly = self.clip_poly(v)
                if poly and len(poly) >= 6:
                    c.create_polygon(poly, fill=col, outline="", tags="dyn")
        # night side (three bands = soft dusk) + golden terminator line
        for pts, col in self.night_specs:
            c.create_polygon(pts, fill=col, outline="", tags="dyn")
        c.create_line(self.term_line, fill=mix(P["night"], P["gold"], 0.38), width=1, tags="dyn")
        # city lights
        Lx, Ly, Lz = self.L
        for lonr, sl, cl in self.cities:
            x, y, z = self.to_view(lonr, sl, cl, vp)
            if z < 0.05:
                continue
            nl = x * Lx + y * Ly + z * Lz
            b = clamp((0.25 - nl) / 0.5, 0.10, 1.0)
            sx, sy = self.screen(x, y)
            if b > 0.55:
                r = 3.6
                c.create_oval(sx - r, sy - r, sx + r, sy + r, fill=mix(P["night"], "#c99a3d", 0.6),
                              outline="", tags="dyn")
            r = 1.0 + 1.1 * b
            c.create_oval(sx - r, sy - r, sx + r, sy + r, fill=mix("#6fb3a0", "#ffe08a", b),
                          outline="", tags="dyn")
        # atmosphere rim + glassy reflection
        for i in range(6):
            r = R - 1 - i * 3.2
            col = mix(self.ocean(r / R), P["cyan"], 0.08 + 0.42 * (1 - i / 6.0))
            c.create_oval(cx - r, cy - r, cx + r, cy + r, outline=col, width=4, tags="dyn")
        c.create_oval(cx - R, cy - R, cx + R, cy + R, outline=mix(P["cyan"], "#ffffff", 0.35),
                      width=2, tags="dyn")
        rr = R * 0.93
        c.create_arc(cx - rr, cy - rr, cx + rr, cy + rr, start=112, extent=44, style="arc",
                     outline="#e6fbff", width=3, tags="dyn")
        c.create_arc(cx - rr, cy - rr, cx + rr, cy + rr, start=163, extent=12, style="arc",
                     outline="#c9f3ff", width=3, tags="dyn")


# =====================================================================
# 8. THE APPLICATION — UI + story timeline
# =====================================================================
ORBITS = [  # rad (x globe radius), inclination, screen roll, deg/s, colours
    dict(rad=1.18, inc=74, roll=-20, spd=26, col=P["gold"], sat=P["gold"], ph=20),
    dict(rad=1.26, inc=64, roll=28, spd=-15, col=P["cyan"], sat=P["cyan"], ph=140),
    dict(rad=1.10, inc=58, roll=105, spd=21, col=P["lav"], sat=P["lav"], ph=250),
]

FLOW_LABELS = ["TEXT", "LANGUAGE", "SCRIPT", "LINGUISTIC REGION", "LANGUAGE RELATIONSHIP"]


class LanguageGlobeApp:
    def __init__(self, root):
        self.root = root
        root.title("POLYGLOT — The Living Language Globe")
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        w, h = min(1400, sw - 40), min(850, sh - 90)
        root.geometry("%dx%d+%d+%d" % (w, h, max(0, (sw - w) // 2), max(0, (sh - h) // 2 - 20)))
        root.minsize(1120, 690)
        root.configure(bg=P["bg_top"])

        fams = set(tkfont.families())
        self.sans = next((f for f in SANS if f in fams), "Helvetica")
        self.serif = next((f for f in SERIF if f in fams), "Times")
        self._fonts = {}

        self.c = tk.Canvas(root, highlightthickness=0, bd=0, bg=P["bg_top"])
        self.c.pack(fill="both", expand=True)

        self.renderer = GlobeRenderer(self.c)
        self.anim = GlobeAnimator()
        self.parts = ParticleSystem(self.c)
        self.detector = LanguageDetectorDemo()

        # ---- state ----
        self.W = self.H = 0
        self.t = 0.0
        self.frame = 0
        self.last = time.perf_counter()
        self.phase = "idle"            # idle | scan | seek | located
        self.phase_t = 0.0
        self.located_t = 0.0
        self.reveal_t = 0.0
        self.zone_t = 0.0
        self.arc_t = 0.0
        self.scan_len = 2.0
        self.signal = None
        self.info_lang = None
        self.info_mode = "idle"        # idle | trace | browse | compare
        self.selected = None
        self.compare = None
        self.cmp_split = False
        self.cmp_focus = 0
        self.slots = {"A": "urdu", "B": "japanese"}
        self.flow_stage = 0
        self.resumed = False
        self.burst_pending = False
        self.orbit_boost = 1.0
        self.orbit_boost_target = 1.0
        self.beacon_xy = {}
        self.hover_beacon = None
        self.mouse = (0, 0)
        self.toast_msg, self.toast_t = "", 0.0
        self.explore_open = False
        self.menu = None
        self.pill_rect = None
        self.buttons = {}
        self.lay = {}
        self.rp = {}
        self.vals_dirty = True
        self.orbit_phase = [o["ph"] for o in ORBITS]
        self._relayout_job = None
        rng = random.Random(3)
        self.stars = [(rng.random(), rng.random(), rng.uniform(0.6, 1.9), rng.random()) for _ in range(170)]

        # ---- the one real widget: the text box (styled to blend in) ----
        self.ph_active = True
        self.text = tk.Text(self.c, wrap="word", bd=0, highlightthickness=0, relief="flat",
                            bg=P["field"], fg=P["dim"], insertbackground=P["gold"],
                            selectbackground="#2b78b5", selectforeground=P["ivory"],
                            font=self.F(15), padx=2, pady=2, undo=True)
        self.text_win = self.c.create_window(0, 0, window=self.text, anchor="nw", tags="textwin")
        self._show_placeholder()
        self.text.bind("<FocusIn>", self._focus_in)
        self.text.bind("<FocusOut>", self._focus_out)
        self.text.bind("<Return>", lambda e: (self.start_trace(), "break")[1])
        self.text.bind("<Shift-Return>", lambda e: None)

        self.c.bind("<Configure>", self.on_configure)
        self.c.bind("<Motion>", self.on_motion)
        self.c.bind("<Button-1>", self.on_click)
        self.c.bind("<Leave>", self.on_leave)
        root.bind("<Escape>", lambda e: self.close_overlays())

        root.after(60, self.relayout)
        root.after(120, self.tick)

    # ------------------------------------------------------------------
    # small drawing helpers
    # ------------------------------------------------------------------
    def F(self, size, weight="normal", slant="roman", serif=False):
        key = (size, weight, slant, serif)
        f = self._fonts.get(key)
        if f is None:
            f = tkfont.Font(family=self.serif if serif else self.sans, size=-size, weight=weight, slant=slant)
            self._fonts[key] = f
        return f

    def T(self, x, y, s, size=12, color=None, weight="normal", anchor="w", tag="ui", serif=False,
          slant="roman", width=None, justify="left"):
        kw = dict(text=s, fill=color or P["ivory"], font=self.F(size, weight, slant, serif),
                  anchor=anchor, tags=tag)
        if width:
            kw["width"] = width
        if justify != "left":
            kw["justify"] = justify
        return self.c.create_text(x, y, **kw)

    def fit(self, s, max_w, sizes=(17, 15, 13, 11, 10), weight="normal", serif=True):
        for sz in sizes:
            f = self.F(sz, weight, "roman", serif)
            if f.measure(s) <= max_w:
                return sz
        return sizes[-1]

    def panel_fill(self, y):
        return mix(bg_at(y, self.H), "#ffffff", 0.10)

    # ------------------------------------------------------------------
    # text box placeholder logic
    # ------------------------------------------------------------------
    def _show_placeholder(self):
        self.text.delete("1.0", "end")
        self.text.insert("1.0", PLACEHOLDER)
        self.text.config(fg=P["dim"])
        self.ph_active = True

    def _focus_in(self, _e):
        if self.ph_active:
            self.text.delete("1.0", "end")
            self.text.config(fg=P["ivory"])
            self.ph_active = False

    def _focus_out(self, _e):
        if not self.text.get("1.0", "end").strip():
            self._show_placeholder()

    def get_text(self):
        return "" if self.ph_active else self.text.get("1.0", "end").strip()

    def set_text(self, s):
        self.ph_active = False
        self.text.delete("1.0", "end")
        self.text.insert("1.0", s)
        self.text.config(fg=P["ivory"])

    # ------------------------------------------------------------------
    # layout
    # ------------------------------------------------------------------
    def on_configure(self, _e):
        if self._relayout_job:
            self.root.after_cancel(self._relayout_job)
        self._relayout_job = self.root.after(60, self.relayout)

    def compute_layout(self):
        W, H = self.W, self.H
        m, top, strip_h = 24, 84, 76
        strip = (m, H - m - strip_h, W - m, H - m)
        pw = clamp(W * 0.235, 300, 350)
        py1, py2 = top, strip[1] - 14
        left, right = (m, py1, m + pw, py2), (W - m - pw, py1, W - m, py2)
        gap = right[0] - left[2]
        self.gcx = W / 2.0
        self.gcy = (top + strip[1]) / 2.0 - 4
        self.gR = min(gap * 0.385, (strip[1] - top) * 0.40)
        self.left, self.right, self.strip = left, right, strip
        L = {}
        x1, y1, x2, y2 = left
        pad = 20
        ix, iw = x1 + pad, x2 - x1 - 2 * pad
        box_top = y1 + pad + 58
        compare_top = y2 - pad - 88
        trace_top = compare_top - 16 - 76
        chips_top = trace_top - 14 - 98
        box_bottom = chips_top - 12
        L["ix"], L["iw"], L["pad"] = ix, iw, pad
        L["box"] = (ix, box_top, ix + iw, box_bottom)
        L["chips_top"] = chips_top
        cw = (iw - 12) / 3.0
        L["chips"] = []
        for i, key in enumerate(SAMPLE_KEYS):
            r, cc = divmod(i, 3)
            xa = ix + cc * (cw + 6)
            ya = chips_top + 18 + r * 28
            L["chips"].append((key, (xa, ya, xa + cw, ya + 24)))
        L["trace"] = (ix, trace_top, ix + iw, trace_top + 40)
        hw = (iw - 8) / 2.0
        L["clear"] = (ix, trace_top + 48, ix + hw, trace_top + 76)
        L["reset"] = (ix + hw + 8, trace_top + 48, ix + iw, trace_top + 76)
        L["compare_top"] = compare_top
        sw_ = (iw - 24) / 2.0
        L["slotA"] = (ix, compare_top + 20, ix + sw_, compare_top + 48)
        L["slotB"] = (ix + iw - sw_, compare_top + 20, ix + iw, compare_top + 48)
        L["compare"] = (ix, compare_top + 56, ix + iw, compare_top + 88)
        L["port_l"] = (x2, (box_top + box_bottom) / 2.0)
        # right panel
        x1, y1, x2, y2 = right
        k = clamp((y2 - y1) / 580.0, 0.84, 1.0)
        self.rp = dict(x=x1 + pad, x2=x2 - pad, w=x2 - x1 - 2 * pad, k=k, y1=y1, y2=y2)
        oy = lambda v: y1 + v * k
        self.rp["oy"] = oy
        L["explore"] = (x1 + pad, oy(318), x2 - pad, oy(348))
        L["port_r"] = (x1, oy(150))
        self.lay = L

    def relayout(self):
        self._relayout_job = None
        c = self.c
        W, H = c.winfo_width(), c.winfo_height()
        if W < 200 or H < 200:
            self.root.after(100, self.relayout)
            return
        self.W, self.H = W, H
        self.compute_layout()
        for tg in ("static", "ui", "menu", "explore"):
            c.delete(tg)
        self.renderer.set_geometry(self.gcx, self.gcy, self.gR)
        self.draw_background()
        self.renderer.draw_base("static")
        self.draw_panels()
        bx = self.lay["box"]
        c.coords("textwin", bx[0] + 12, bx[1] + 10)
        c.itemconfigure("textwin", width=max(40, bx[2] - bx[0] - 24), height=max(30, bx[3] - bx[1] - 20))
        self.build_buttons()
        for key in self.buttons:
            self.draw_button(key)
        if self.explore_open:
            self.draw_explore()
        self.menu = None
        self.vals_dirty = True

    # ------------------------------------------------------------------
    # static drawing: background, panels, header
    # ------------------------------------------------------------------
    def draw_background(self):
        c, W, H = self.c, self.W, self.H
        n = 90
        for i in range(n):
            y = H * i / n
            c.create_rectangle(0, y, W, y + H / n + 1, fill=bg_at(y + H / n / 2, H), outline="", tags="static")
        cx, cy, R = self.gcx, self.gcy, self.gR
        base = bg_at(cy, H)
        for i in range(16):                       # soft turquoise glow behind the Earth
            r = R * (2.0 - i * 0.06)
            f = (i / 16.0) ** 1.6
            c.create_oval(cx - r, cy - r, cx + r, cy + r, fill=mix(base, "#38c9d6", 0.02 + 0.20 * f),
                          outline="", tags="static")
        for (rx, ry, st, ex) in ((2.05, 1.65, 200, 120), (1.75, 1.4, 20, 100), (2.4, 1.9, 300, 70)):
            c.create_arc(cx - R * rx, cy - R * ry, cx + R * rx, cy + R * ry, start=st, extent=ex,
                         style="arc", outline=mix(base, P["ivory"], 0.10), width=1, tags="static")
        for sx, sy, sz, ph in self.stars:
            x, y = sx * W, sy * H
            c.create_oval(x - sz, y - sz, x + sz, y + sz,
                          fill=mix(bg_at(y, H), P["ivory"] if ph > 0.3 else P["cyan"], 0.35 + 0.5 * ph),
                          outline="", tags="static")

    def draw_panel(self, x1, y1, x2, y2, accent):
        c, H = self.c, self.H
        r = 26
        c.create_polygon(rounded_poly(x1 - 1, y1 - 1, x2 + 1, y2 + 1, r), smooth=True, fill="",
                         outline=mix(bg_at((y1 + y2) / 2, H), P["cyan"], 0.16), width=4, tags="ui")
        n = 70                                     # vertical gradient, slice by slice
        for j in range(n):
            ya = y1 + (y2 - y1) * j / n
            yb = y1 + (y2 - y1) * (j + 1) / n
            ym = (ya + yb) / 2.0
            d = min(ym - y1, y2 - ym)
            inset = r - math.sqrt(max(0.0, r * r - (r - d) ** 2)) if d < r else 0.0
            c.create_rectangle(x1 + inset, ya, x2 - inset, yb + 1, fill=self.panel_fill(ym), outline="",
                               tags="ui")
        c.create_polygon(rounded_poly(x1, y1, x2, y2, r), smooth=True, fill="",
                         outline=mix(self.panel_fill((y1 + y2) / 2), P["cyan"], 0.55), width=1, tags="ui")
        d = 2 * r - 6                              # curved corner brackets
        for (bx, by, st) in ((x1 + 5, y1 + 5, 90), (x2 - 5 - d, y1 + 5, 0),
                             (x1 + 5, y2 - 5 - d, 180), (x2 - 5 - d, y2 - 5 - d, 270)):
            c.create_arc(bx, by, bx + d, by + d, start=st, extent=90, style="arc", outline=accent,
                         width=2, tags="ui")

    def draw_panels(self):
        c = self.c
        self.draw_header()
        # ---------- left: input chamber ----------
        x1, y1, x2, y2 = self.left
        L = self.lay
        self.draw_panel(x1, y1, x2, y2, P["gold"])
        ix, iw, pad = L["ix"], L["iw"], L["pad"]
        self.T(ix, y1 + pad + 10, "LANGUAGE SIGNAL", 20, P["ivory"], "bold", serif=True)
        self.T(ix, y1 + pad + 28, "Enter a sentence and trace its linguistic region.", 12, P["soft"],
               anchor="nw", slant="italic", width=iw)
        bx = L["box"]
        c.create_polygon(rounded_poly(*bx, 16), smooth=True, fill=P["field"],
                         outline=mix(P["field"], P["cyan"], 0.55), width=1, tags="ui")
        c.create_arc(bx[0] + 6, bx[1] + 6, bx[0] + 34, bx[1] + 34, start=90, extent=90, style="arc",
                     outline=P["gold"], width=2, tags="ui")
        self.T(L["ix"], L["chips_top"] + 6, "TRY A SAMPLE", 10, P["soft"], "bold")
        self.T(L["ix"], L["compare_top"] + 6, "COMPARE TWO LANGUAGES", 10, P["soft"], "bold")
        px = L["ix"] + iw / 2.0
        self.T(px, L["compare_top"] + 34, "\u2194", 15, P["gold"], "bold", anchor="center")
        # signal port (where particles leave the chamber)
        pxl, pyl = L["port_l"]
        for rr, col in ((9, mix(self.panel_fill(pyl), P["gold"], 0.25)), (5, P["gold"])):
            c.create_oval(pxl - rr, pyl - rr, pxl + rr, pyl + rr, fill=col, outline="", tags="ui")
        # ---------- right: linguistic signal ----------
        x1, y1, x2, y2 = self.right
        oy, k = self.rp["oy"], self.rp["k"]
        self.draw_panel(x1, y1, x2, y2, P["turq"])
        rx = self.rp["x"]
        self.T(rx, oy(26), "LINGUISTIC SIGNAL", 19, P["ivory"], "bold", serif=True)
        self.T(rx, oy(46), "DEMO LANGUAGE DETECTION  \u00b7  SIMULATED", 9, P["soft"], "bold")
        c.create_line(rx, oy(364), self.rp["x2"], oy(364), fill=mix(self.panel_fill(oy(364)), P["cyan"], 0.35),
                      tags="ui")
        self.T(rx, oy(380), "HOW POLYGLOT SEES LANGUAGE", 10, P["gold"], "bold")
        prx, pry = self.lay["port_r"]
        for rr, col in ((9, mix(self.panel_fill(pry), P["turq"], 0.25)), (5, P["turq"])):
            c.create_oval(prx - rr, pry - rr, prx + rr, pry + rr, fill=col, outline="", tags="ui")
        # ---------- bottom: linguistic profile strip ----------
        x1, y1, x2, y2 = self.strip
        self.draw_panel(x1, y1, x2, y2, P["lav"])
        self.T(x1 + 30, y1 + 30, "LINGUISTIC", 15, P["gold"], "bold", serif=True)
        self.T(x1 + 30, y1 + 50, "PROFILE", 15, P["ivory"], "bold", serif=True)
        cx0 = x1 + 178
        cw = (x2 - 20 - cx0) / 5.0
        self.strip_cols = []
        for i, lab in enumerate(("LANGUAGE", "SCRIPT", "REGION", "FAMILY", "STATUS")):
            xx = cx0 + i * cw
            c.create_line(xx, y1 + 16, xx, y2 - 16, fill=mix(self.panel_fill(y1), P["cyan"], 0.3), tags="ui")
            self.T(xx + 16, y1 + 24, lab, 10, P["soft"], "bold")
            self.strip_cols.append((xx + 16, cw - 26))
        # ---------- globe caption ----------
        gx = self.gcx
        self.T(gx, 96, "LIVING LANGUAGE GLOBE", 17, P["ivory"], "bold", anchor="center", serif=True)
        self.T(gx, 116, "Tracing language through the world's linguistic regions", 11, P["soft"],
               anchor="center", slant="italic")
        wcap = self.F(17, "bold", "roman", True).measure("LIVING LANGUAGE GLOBE") / 2 + 22
        for sgn in (-1, 1):
            c.create_line(gx + sgn * wcap, 96, gx + sgn * (wcap + 70), 96,
                          fill=mix(bg_at(96, self.H), P["gold"], 0.5), tags="ui")
            c.create_oval(gx + sgn * (wcap + 74) - 2, 94, gx + sgn * (wcap + 74) + 2, 98,
                          fill=P["gold"], outline="", tags="ui")

    def draw_header(self):
        c, m = self.c, 24
        cx, cy = m + 22, 40
        c.create_oval(cx - 18, cy - 18, cx + 18, cy + 18, fill="#0f6fb0", outline=P["cyan"], width=2, tags="ui")
        c.create_oval(cx - 7, cy - 18, cx + 7, cy + 18, outline=P["cyan"], tags="ui")
        c.create_line(cx - 18, cy, cx + 18, cy, fill=P["cyan"], tags="ui")
        c.create_arc(cx - 26, cy - 10, cx + 26, cy + 10, start=200, extent=140, style="arc",
                     outline=P["gold"], width=2, tags="ui")
        c.create_oval(cx + 21, cy - 4, cx + 27, cy + 2, fill=P["gold"], outline="", tags="ui")
        self.T(m + 56, 34, "POLYGLOT", 30, P["ivory"], "bold", serif=True)
        self.T(m + 58, 60, "Every Language Has a Place", 13, P["gold"], slant="italic")
        self.T(self.W - m, 60, "DEMO LANGUAGE DETECTION  \u00b7  SAMPLE DATA  \u00b7  REGIONS ARE APPROXIMATE",
               9, P["soft"], "bold", anchor="e")

    # ------------------------------------------------------------------
    # custom buttons (all drawn on the canvas)
    # ------------------------------------------------------------------
    def build_buttons(self):
        L = self.lay
        self.buttons = {}

        def add(key, rect, label, kind, cb, **kw):
            self.buttons[key] = dict(rect=rect, label=label, kind=kind, cb=cb, hover=False, **kw)

        add("trace", L["trace"], "TRACE LANGUAGE", "primary", self.start_trace)
        add("clear", L["clear"], "CLEAR SIGNAL", "ghost", self.clear_signal)
        add("reset", L["reset"], "RESET GLOBE", "ghost", self.reset_globe)
        for key, rect in L["chips"]:
            add("chip:" + key, rect, LANG[key].name.upper(), "chip", lambda k=key: self.pick_sample(k))
        add("slotA", L["slotA"], "", "slot", lambda: self.open_menu("A"), slot="A")
        add("slotB", L["slotB"], "", "slot", lambda: self.open_menu("B"), slot="B")
        add("compare", L["compare"], "COMPARE  \u2194", "accent", self.run_compare)
        add("explore", L["explore"], "EXPLORE LANGUAGE", "ghost", self.open_explore)

    def draw_button(self, key):
        b = self.buttons.get(key)
        if not b:
            return
        c = self.c
        tag = "btn_" + key.replace(":", "_")
        c.delete(tag)
        x1, y1, x2, y2 = b["rect"]
        hov, kind = b["hover"], b["kind"]
        tags = ("ui", tag)
        my = (y1 + y2) / 2.0
        pf = self.panel_fill(my)
        if kind == "primary":
            if hov:
                c.create_polygon(rounded_poly(x1 - 3, y1 - 3, x2 + 3, y2 + 3, 22), smooth=True, fill="",
                                 outline=P["gold"], width=2, tags=tags)
            c.create_polygon(rounded_poly(x1, y1, x2, y2, 20), smooth=True,
                             fill=mix(P["gold"], "#ffffff", 0.28 if hov else 0.0), outline="", tags=tags)
            for rr in (5, 9, 13):
                c.create_arc(x1 + 24 - rr, my - rr, x1 + 24 + rr, my + rr, start=-45, extent=90, style="arc",
                             outline=P["ink"], width=2, tags=tags)
            self.T((x1 + x2) / 2 + 12, my, b["label"], 14, P["ink"], "bold", anchor="center", tag=tags)
        elif kind == "ghost" and key == "explore" and (self.compare or not self.info_lang):
            c.create_polygon(rounded_poly(x1, y1, x2, y2, 14), smooth=True, fill=mix(pf, "#000000", 0.06),
                             outline=mix(pf, P["cyan"], 0.25), width=1, tags=tags)
            self.T((x1 + x2) / 2, my, b["label"], 11, P["dim"], "bold", anchor="center", tag=tags)
        elif kind == "ghost":
            c.create_polygon(rounded_poly(x1, y1, x2, y2, 14), smooth=True,
                             fill=mix(pf, "#ffffff", 0.14 if hov else 0.03),
                             outline=mix(pf, P["cyan"], 0.9 if hov else 0.55), width=1, tags=tags)
            self.T((x1 + x2) / 2, my, b["label"], 11, P["cyan"], "bold", anchor="center", tag=tags)
        elif kind == "chip":
            c.create_polygon(rounded_poly(x1, y1, x2, y2, 12), smooth=True,
                             fill=mix(pf, "#ffffff", 0.16 if hov else 0.06),
                             outline=P["gold"] if hov else mix(pf, P["cyan"], 0.5), width=1, tags=tags)
            self.T((x1 + x2) / 2, my, b["label"], 10, P["ivory"] if hov else P["soft"], "bold",
                   anchor="center", tag=tags)
        elif kind == "slot":
            slot = b["slot"]
            col = P["coral"] if slot == "A" else P["turq"]
            c.create_polygon(rounded_poly(x1, y1, x2, y2, 14), smooth=True,
                             fill=mix(pf, "#ffffff", 0.14 if hov else 0.05),
                             outline=mix(pf, col, 0.9 if hov else 0.6), width=1, tags=tags)
            c.create_oval(x1 + 10, my - 4, x1 + 18, my + 4, fill=col, outline="", tags=tags)
            self.T(x1 + 26, my, LANG[self.slots[slot]].name, 12, P["ivory"], "bold", tag=tags)
            self.T(x2 - 12, my, "\u25be", 10, P["soft"], anchor="e", tag=tags)
        elif kind == "accent":
            c.create_polygon(rounded_poly(x1, y1, x2, y2, 16), smooth=True,
                             fill=P["turq"] if hov else mix(pf, P["turq"], 0.12),
                             outline=P["turq"], width=1, tags=tags)
            self.T((x1 + x2) / 2, my, b["label"], 12, P["ink"] if hov else P["turq"], "bold",
                   anchor="center", tag=tags)

    # ------------------------------------------------------------------
    # actions
    # ------------------------------------------------------------------
    def toast(self, msg):
        self.toast_msg, self.toast_t = msg, 2.6

    def close_overlays(self):
        self.explore_open = False
        self.c.delete("explore")
        self.close_menu()

    def pick_sample(self, key):
        self.set_text(LANG[key].sample)
        self.text.focus_set()
        self.text.mark_set("insert", "end")

    def entry_point(self):
        a = math.radians(168)
        return (self.gcx + self.gR * math.cos(a), self.gcy - self.gR * math.sin(a))

    def _reset_reveal(self):
        self.reveal_t = 0.0
        self.zone_t = 0.0
        self.arc_t = 0.0
        self.located_t = 0.0
        self.resumed = False
        self.vals_dirty = True
        self.draw_button("explore")

    def start_trace(self):
        text = self.get_text()
        if not text:
            self.toast("Type a sentence, or pick a sample language first.")
            return
        self.close_overlays()
        self.compare = None
        self.cmp_split = False
        sig = self.detector.detect(text)
        self.signal, self.info_lang, self.info_mode = sig, LANG[sig.key], "trace"
        self.selected = None
        self.phase, self.phase_t = "scan", 0.0
        self._reset_reveal()
        self.flow_stage = 1
        self.anim.begin_scan()
        self.orbit_boost_target = 4.0
        self.parts.clear()
        self.scan_len = self.parts.spawn_text(text, self.lay["box"], self.entry_point())

    def browse(self, key):
        lang = LANG[key]
        self.close_overlays()
        self.compare, self.signal, self.cmp_split = None, None, False
        self.info_lang, self.info_mode, self.selected = lang, "browse", None
        self.phase, self.phase_t = "seek", 0.0
        self._reset_reveal()
        self.flow_stage = 2
        self.parts.clear()
        self.orbit_boost_target = 2.5
        self.anim.seek_to(lang.lat, lang.lon, spins=False, on_arrive=self.on_arrive)

    def run_compare(self):
        a, b = self.slots["A"], self.slots["B"]
        if a == b:
            self.toast("Pick two different languages to compare.")
            return
        self.close_overlays()
        self.signal, self.selected = None, None
        self.compare, self.info_mode, self.info_lang = (a, b), "compare", None
        self.phase, self.phase_t = "seek", 0.0
        self._reset_reveal()
        self.flow_stage = 2
        self.parts.clear()
        self.orbit_boost_target = 2.5
        la, lb = LANG[a], LANG[b]
        d = ang_dist((la.lat, la.lon), (lb.lat, lb.lon))
        if d <= 118:
            self.cmp_split = False
            mlat, mlon = midpoint((la.lat, la.lon), (lb.lat, lb.lon))
            self.anim.seek_to(mlat, mlon, spins=False, on_arrive=self.on_arrive)
        else:            # too far apart to see both: the globe alternates
            self.cmp_split, self.cmp_focus = True, 0
            self.anim.seek_to(la.lat, la.lon, spins=False, on_arrive=self.on_arrive)

    def clear_signal(self):
        self.close_overlays()
        self._show_placeholder()
        self.signal = self.info_lang = self.selected = self.compare = None
        self.info_mode, self.phase, self.flow_stage = "idle", "idle", 0
        self.cmp_split = False
        self.parts.clear()
        self.orbit_boost_target = 1.0
        self.anim.resume_idle()
        self._reset_reveal()

    def reset_globe(self):
        self.clear_signal()
        self.slots = {"A": "urdu", "B": "japanese"}
        self.anim.reset()
        for key in ("slotA", "slotB"):
            self.draw_button(key)

    def on_arrive(self):
        """The globe has stopped: wake up the region."""
        self.phase = "located"
        self._reset_reveal()
        self.orbit_boost_target = 1.0
        self.burst_pending = True
        if not self.compare and self.info_lang:
            self.selected = self.info_lang.key

    def on_swap_arrive(self):
        self.located_t = 0.0
        self.burst_pending = True

    def open_explore(self):
        if not self.info_lang or self.phase != "located" or self.compare:
            self.toast("Trace a sentence or click a beacon first.")
            return
        self.close_menu()
        self.explore_open = True
        self.draw_explore()

    # ---- popup menu for the compare slots ----
    def open_menu(self, slot):
        self.close_menu()
        self.explore_open = False
        self.c.delete("explore")
        b = self.buttons["slot" + slot]
        x1, y1, x2, y2 = b["rect"]
        cols, cw, ch = 2, 118, 26
        rows = (len(LANGS) + 1) // 2
        mw, mh = cols * cw + 16, rows * ch + 16
        mx = clamp(x1, 8, self.W - mw - 8)
        my = clamp(y1 - mh - 6, 8, self.H - mh - 8)
        c = self.c
        tags = ("menu", "overlay")
        c.create_polygon(rounded_poly(mx, my, mx + mw, my + mh, 14), smooth=True, fill="#0b3a68",
                         outline=P["cyan"], width=1, tags=tags)
        items = []
        for i, lang in enumerate(LANGS):
            r, cc = divmod(i, cols)
            ax, ay = mx + 8 + cc * cw, my + 8 + r * ch
            rect = (ax, ay, ax + cw - 4, ay + ch - 2)
            items.append((rect, lang.key))
            self.T(ax + 10, ay + ch / 2 - 1, lang.name, 12, P["ivory"], tag=tags)
        self.menu = dict(slot=slot, items=items, rect=(mx, my, mx + mw, my + mh))

    def close_menu(self):
        self.c.delete("menu")
        self.menu = None

    # ------------------------------------------------------------------
    # explore card
    # ------------------------------------------------------------------
    def draw_explore(self):
        c = self.c
        c.delete("explore")
        lang = self.info_lang
        if not lang:
            return
        cw, ch = min(540, self.W * 0.42), 262
        x1 = self.gcx - cw / 2
        y1 = self.gcy - ch / 2 + 26
        x2, y2 = x1 + cw, y1 + ch
        tags = ("explore", "overlay")
        c.create_polygon(rounded_poly(x1 + 5, y1 + 8, x2 + 5, y2 + 8, 24), smooth=True, fill="#062a55",
                         outline="", tags=tags)
        c.create_polygon(rounded_poly(x1, y1, x2, y2, 24), smooth=True, fill="#0d3f6f", outline=P["gold"],
                         width=1, tags=tags)
        self.T(x1 + 24, y1 + 34, lang.name.upper(), 26, P["gold"], "bold", serif=True, tag=tags)
        self.T(x2 - 56, y1 + 34, lang.native, 20, P["ivory"], anchor="e", serif=True, tag=tags)
        c.create_line(x1 + 24, y1 + 58, x2 - 24, y1 + 58, fill=mix("#0d3f6f", P["cyan"], 0.4), tags=tags)
        self.T(x1 + 24, y1 + 76, "SAMPLE", 10, P["soft"], "bold", tag=tags)
        self.T(x1 + 24, y1 + 96, lang.sample, 16, P["ivory"], anchor="w", tag=tags, width=cw - 48)
        cols = (("SCRIPT", lang.script), ("REGION", lang.region), ("FAMILY", lang.family))
        colw = (cw - 48) / 3.0
        for i, (lab, val) in enumerate(cols):
            xx = x1 + 24 + i * colw
            self.T(xx, y1 + 128, lab, 10, P["soft"], "bold", tag=tags)
            self.T(xx, y1 + 146, val, 12, P["ivory"], "bold", anchor="nw", tag=tags, width=colw - 8)
        self.T(x1 + 24, y1 + 186, lang.note, 12, P["dim"], anchor="nw", slant="italic", tag=tags, width=cw - 48)
        rel = [l.name for l in LANGS if l.family == lang.family and l.key != lang.key]
        rel_txt = "RELATED IN THIS DEMO:  " + ("  \u00b7  ".join(rel[:5]) if rel else "none (a family of its own here)")
        self.T(x1 + 24, y2 - 40, rel_txt, 10, P["gold"], "bold", tag=tags, width=cw - 48, anchor="nw")
        self.T(x1 + 24, y2 - 16, "Associated Linguistic Region \u2014 a visual approximation, not a point of origin.",
               9, P["soft"], slant="italic", tag=tags)
        cx_, cy_ = x2 - 28, y1 + 34
        c.create_oval(cx_ - 12, cy_ - 12 + 0, cx_ + 12, cy_ + 12, outline=P["cyan"], tags=tags)
        c.create_line(cx_ - 4, cy_ - 4, cx_ + 4, cy_ + 4, fill=P["cyan"], width=2, tags=tags)
        c.create_line(cx_ - 4, cy_ + 4, cx_ + 4, cy_ - 4, fill=P["cyan"], width=2, tags=tags)
        self.explore_rect = (x1, y1, x2, y2)

    # ------------------------------------------------------------------
    # mouse
    # ------------------------------------------------------------------
    @staticmethod
    def _in(rect, x, y):
        return rect[0] <= x <= rect[2] and rect[1] <= y <= rect[3]

    def on_leave(self, _e):
        self.mouse = (-1, -1)
        self.hover_beacon = None

    def on_motion(self, e):
        self.mouse = (e.x, e.y)
        cursor = ""
        for key, b in self.buttons.items():
            if key == "explore" and (self.compare or not self.info_lang):
                continue
            h = self._in(b["rect"], e.x, e.y)
            if h != b["hover"]:
                b["hover"] = h
                self.draw_button(key)
            if h:
                cursor = "hand2"
        self.hover_beacon = None
        best = 15.0
        for key, (sx, sy, z) in self.beacon_xy.items():
            d = math.hypot(sx - e.x, sy - e.y)
            if d < best and z > 0.08:
                best, self.hover_beacon = d, key
        if self.hover_beacon or (self.pill_rect and self._in(self.pill_rect, e.x, e.y)):
            cursor = "hand2"
        self.c.configure(cursor=cursor)

    def on_click(self, e):
        x, y = e.x, e.y
        if self.menu:
            for rect, key in self.menu["items"]:
                if self._in(rect, x, y):
                    self.slots[self.menu["slot"]] = key
                    self.draw_button("slot" + self.menu["slot"])
                    break
            self.close_menu()
            return
        if self.explore_open:
            if not self._in(self.explore_rect, x, y) or (self.explore_rect[2] - 44 < x and y < self.explore_rect[1] + 54):
                self.close_overlays()
            return
        for key, b in self.buttons.items():
            if key == "explore" and (self.compare or not self.info_lang):
                continue
            if self._in(b["rect"], x, y):
                self.root.focus_set() if key.startswith("slot") else None
                b["cb"]()
                return
        if self.pill_rect and self._in(self.pill_rect, x, y):
            self.open_explore()
            return
        rp = self.rp
        if (self.info_lang and self.phase == "located" and not self.compare
                and rp["x"] <= x <= rp["x2"] and rp["oy"](70) <= y <= rp["oy"](110)):
            self.open_explore()
            return
        if self.hover_beacon:
            self.browse(self.hover_beacon)

    # ------------------------------------------------------------------
    # main loop
    # ------------------------------------------------------------------
    def tick(self):
        now = time.perf_counter()
        dt = min(0.06, now - self.last)
        self.last = now
        try:
            if self.W:
                self.t += dt
                self.frame += 1
                self.update(dt)
                self.draw_frame()
        except Exception:
            traceback.print_exc()
        self.root.after(FRAME_MS, self.tick)

    def update(self, dt):
        self.anim.update(dt)
        self.parts.update(dt)
        self.orbit_boost += (self.orbit_boost_target - self.orbit_boost) * min(1.0, dt * 2.0)
        for i, o in enumerate(ORBITS):
            self.orbit_phase[i] += o["spd"] * dt * (self.orbit_boost if i == 0 else 1 + 0.15 * (self.orbit_boost - 1))
        if self.toast_t > 0:
            self.toast_t -= dt
        if self.phase == "scan":
            self.phase_t += dt
            if self.flow_stage < 2 and self.phase_t > 0.9:
                self.flow_stage = 2
            if self.phase_t >= self.scan_len + 0.25:
                lang = self.info_lang
                self.phase, self.phase_t = "seek", 0.0
                self.flow_stage = max(self.flow_stage, 2)
                self.anim.seek_to(lang.lat, lang.lon, spins=True, on_arrive=self.on_arrive)
        elif self.phase == "seek":
            self.phase_t += dt
        elif self.phase == "located":
            self.reveal_t += dt
            self.zone_t = min(1.0, self.zone_t + dt / 0.9)
            self.arc_t = min(1.0, self.arc_t + dt / 1.2)
            if self.anim.mode == "located":
                self.located_t += dt
            for stage, when in ((3, 0.15), (4, 0.7), (5, 1.3)):
                if self.reveal_t > when:
                    self.flow_stage = max(self.flow_stage, stage)
            if self.compare and self.cmp_split and self.anim.mode == "located" and self.located_t > 3.6:
                self.cmp_focus ^= 1
                lang = LANG[self.compare[self.cmp_focus]]
                self.anim.seek_to(lang.lat, lang.lon, spins=False, on_arrive=self.on_swap_arrive)
            if (not self.compare and not self.resumed and self.anim.mode == "located"
                    and self.located_t > HOLD_BEFORE_RESUME):
                self.resumed = True
                self.anim.resume_idle()

    # ------------------------------------------------------------------
    # per-frame drawing
    # ------------------------------------------------------------------
    def active_zones(self):
        if self.compare:
            a, b = self.compare
            return [dict(lang=LANG[a], fill="#ff9a80", edge="#ffe1d8", tag="A"),
                    dict(lang=LANG[b], fill="#4fe0d2", edge="#d9fffb", tag="B")]
        if self.selected and self.phase == "located":
            return [dict(lang=LANG[self.selected], fill="#f3cf6b", edge="#fff4cf", tag="")]
        return []

    def status(self):
        if self.phase == "scan":
            return "SIGNAL DETECTED", P["gold"], "LINGUISTIC SIGNAL DETECTED"
        if self.phase == "seek":
            return "SEARCHING THE GLOBE", P["coral"], "EARTH IS SEARCHING FOR THE ASSOCIATED REGION\u2026"
        if self.phase == "located":
            if self.compare:
                return "COMPARING REGIONS", P["turq"], "TWO ASSOCIATED REGIONS SHOWN ON THE EARTH"
            return "REGION LOCKED", P["turq"], "ASSOCIATED LINGUISTIC REGION LOCATED"
        return "EARTH ROTATING", P["cyan"], ""

    def draw_frame(self):
        c = self.c
        c.delete("dyn")
        R, A = self.renderer, self.anim
        vp = R.view_params(A.lon, A.tilt)
        t = self.t
        self.draw_twinkle()
        self.draw_halo()
        self.parts.draw_dust(R.cx, R.cy, R.R, t)
        orbits = self.compute_orbits()
        self.draw_orbits(orbits, "back")
        self.draw_channels()
        R.draw_land(vp)
        self.draw_zones(vp)
        R.draw_overlays(vp, t)
        self.draw_links(vp)
        self.draw_beacons(vp)
        self.draw_orbits(orbits, "front")
        self.draw_signal_arc()
        self.parts.draw_ripples()
        self.parts.draw_chars(self)
        self.draw_status_ui()
        self.draw_tooltip()
        self.draw_toast()
        if self.vals_dirty or self.frame % 2 == 0:
            self.draw_values()
            self.vals_dirty = False
        c.tag_raise("vals")
        c.tag_raise("overlay")

    def draw_twinkle(self):
        c, H = self.c, self.H
        for i, (sx, sy, sz, ph) in enumerate(self.stars[:26]):
            x, y = sx * self.W, sy * H
            tw = 0.5 + 0.5 * math.sin(self.t * (0.8 + ph) + i)
            r = sz * (0.8 + 0.7 * tw)
            c.create_oval(x - r, y - r, x + r, y + r, fill=mix(bg_at(y, H), "#ffffff", 0.35 + 0.55 * tw),
                          outline="", tags="dyn")

    def draw_halo(self):
        c, R = self.c, self.renderer
        base = bg_at(R.cy, self.H)
        for i in range(5):
            r = R.R * (1.012 + 0.024 * i)
            amt = 0.55 * (1 - i / 5.0) * (0.78 + 0.22 * math.sin(self.t * 1.3))
            c.create_oval(R.cx - r, R.cy - r, R.cx + r, R.cy + r, outline=mix(base, P["cyan"], amt),
                          width=2 if i == 0 else 1, tags="dyn")

    # ---- orbits ----
    def compute_orbits(self):
        R = self.renderer
        out = []
        for i, o in enumerate(ORBITS):
            inc, roll = math.radians(o["inc"]), math.radians(o["roll"])
            ci, si, cr, sr = math.cos(inc), math.sin(inc), math.cos(roll), math.sin(roll)

            def pos(theta_deg, o=o, ci=ci, si=si, cr=cr, sr=sr):
                th = math.radians(theta_deg)
                x, y, z = o["rad"] * math.cos(th), o["rad"] * math.sin(th) * ci, o["rad"] * math.sin(th) * si
                return x * cr - y * sr, x * sr + y * cr, z

            pts = []
            for k in range(0, 361, 5):
                x, y, z = pos(k)
                pts.append((R.cx + R.R * x, R.cy - R.R * y, z, R.visible(x, y, z)))
            out.append((o, pts, pos))
        return out

    def draw_orbits(self, orbits, layer):
        c, base = self.c, bg_at(self.renderer.cy, self.H)
        R = self.renderer.R
        for i, (o, pts, pos) in enumerate(orbits):
            col = mix(base, o["col"], 0.65 if layer == "front" else 0.28)
            run = []
            for (sx, sy, z, vis) in pts:
                ok = vis and ((z >= 0) if layer == "front" else (z < 0))
                if ok:
                    run.extend((sx, sy))
                else:
                    if len(run) >= 4:
                        c.create_line(run, fill=col, width=1.5 if layer == "front" else 1, tags="dyn")
                    run = []
            if len(run) >= 4:
                c.create_line(run, fill=col, width=1.5 if layer == "front" else 1, tags="dyn")
            # the satellite that carries the signal
            th = self.orbit_phase[i]
            x, y, z = pos(th)
            if not self.renderer.visible(x, y, z):
                continue
            if (z >= 0) != (layer == "front"):
                continue
            sx, sy = self.renderer.cx + R * x, self.renderer.cy - R * y
            big = 1.0 + (0.9 * (self.orbit_boost - 1) / 3.0 if i == 0 else 0.0)
            for k in range(1, 7):     # fading trail
                tx, ty, tz = pos(th - k * 3.2 * (1 if o["spd"] > 0 else -1))
                if self.renderer.visible(tx, ty, tz):
                    r = max(0.6, 2.4 - k * 0.3)
                    c.create_oval(self.renderer.cx + R * tx - r, self.renderer.cy - R * ty - r,
                                  self.renderer.cx + R * tx + r, self.renderer.cy - R * ty + r,
                                  fill=mix(base, o["sat"], 0.6 - k * 0.08), outline="", tags="dyn")
            c.create_oval(sx - 9 * big, sy - 9 * big, sx + 9 * big, sy + 9 * big,
                          outline=mix(base, o["sat"], 0.35), tags="dyn")
            c.create_oval(sx - 3.6 * big, sy - 3.6 * big, sx + 3.6 * big, sy + 3.6 * big,
                          fill=o["sat"], outline="", tags="dyn")
            c.create_oval(sx - 1.5, sy - 1.5, sx + 1.5, sy + 1.5, fill="#ffffff", outline="", tags="dyn")

    # ---- signal channels (dotted curves between panels and globe) ----
    def draw_channels(self):
        c, R = self.c, self.renderer
        base = bg_at(R.cy, self.H)
        p0 = self.lay["port_l"]
        e = self.entry_point()
        ctrl = ((p0[0] + e[0]) / 2, min(p0[1], e[1]) - 70)
        hot = 0.75 if self.phase == "scan" else 0.28
        pts = []
        for i in range(0, 31):
            pts.extend(quad_bezier(p0, ctrl, e, i / 30.0))
        c.create_line(pts, fill=mix(base, P["gold"], hot), width=1, dash=(2, 7),
                      dashoffset=int(self.t * 30) % 9, tags="dyn")
        a = math.radians(12)
        x0, y0 = R.cx + R.R * math.cos(a), R.cy - R.R * math.sin(a)
        p1 = self.lay["port_r"]
        ctrl = ((x0 + p1[0]) / 2, min(y0, p1[1]) - 70)
        hot = 0.8 if self.phase == "located" else 0.25
        pts = []
        for i in range(0, 31):
            pts.extend(quad_bezier((x0, y0), ctrl, p1, i / 30.0))
        c.create_line(pts, fill=mix(base, P["turq"], hot), width=1, dash=(2, 7),
                      dashoffset=-int(self.t * 30) % 9, tags="dyn")

    # ---- zones ----
    def draw_zones(self, vp):
        R = self.renderer
        for z in self.active_zones():
            lang = z["lang"]
            g = ease_out(self.zone_t)
            if g <= 0:
                continue
            seed = (hash(lang.key) % 100) / 16.0
            pulse = 0.5 + 0.5 * math.sin(self.t * 3.2)
            pts = R.zone_points(lang.lat, lang.lon, lang.zone * g, seed)
            R.draw_poly(pts, vp, fill=mix(z["fill"], "#ffffff", 0.18 * pulse), outline=z["edge"], width=2)
            for i in range(3):
                ph = (self.t * 0.45 + i / 3.0) % 1.0
                ring = R.zone_points(lang.lat, lang.lon, lang.zone * (1.05 + ph * 1.6), seed, wob=0.05, n=44)
                R.draw_line(ring, vp, closed=True, fill=mix(z["edge"], "#1a6fae", ph ** 0.8),
                            width=2 if ph < 0.5 else 1)

    def draw_links(self, vp):
        """Compare mode: a curved arc hopping between the two regions."""
        if not self.compare:
            return
        la, lb = LANG[self.compare[0]], LANG[self.compare[1]]
        R = self.renderer
        run = []
        segs = []
        for i in range(0, 41):
            u = i / 40.0
            lat, lon = slerp((la.lat, la.lon), (lb.lat, lb.lon), u)
            x, y, z = R.view_ll(lat, lon, vp)
            lift = 1.0 + 0.10 * math.sin(math.pi * u)
            if R.visible(x * lift, y * lift, z):
                run.extend(R.screen(x, y, lift))
            else:
                if len(run) >= 4:
                    segs.append(run)
                run = []
        if len(run) >= 4:
            segs.append(run)
        for s in segs:
            c = self.c
            c.create_line(s, fill=P["ivory"], width=2, dash=(6, 4), dashoffset=int(self.t * 20) % 10, tags="dyn")

    # ---- beacons ----
    def highlight_map(self):
        if self.compare:
            return {self.compare[0]: ("A", P["coral"]), self.compare[1]: ("B", P["turq"])}
        if self.selected and self.phase == "located":
            return {self.selected: ("", P["gold"])}
        return {}

    def draw_beacons(self, vp):
        c, R = self.c, self.renderer
        hl = self.highlight_map()
        self.beacon_xy = {}
        self.pill_rect = None
        pills = []
        for i, lang in enumerate(LANGS):
            x, y, z = R.view_ll(lang.lat, lang.lon, vp)
            if z < 0.06:
                continue
            sx, sy = R.screen(x, y)
            self.beacon_xy[lang.key] = (sx, sy, z)
            ph = self.t * 2.0 + i
            if lang.key in hl:
                tag, col = hl[lang.key]
                if self.burst_pending:
                    for k in range(3):
                        self.parts.add_ripple(sx, sy, col, 1.4, 70, delay=k * 0.25)
                    self.burst_pending = False
                pulse = 0.5 + 0.5 * math.sin(self.t * 4)
                for k in range(2):
                    rr = 8 + 8 * ((self.t * 0.9 + k * 0.5) % 1.0)
                    c.create_oval(sx - rr, sy - rr, sx + rr, sy + rr, outline=mix("#1479bd", col, 1 - ((self.t * 0.9 + k * 0.5) % 1.0)),
                                  tags="dyn")
                for s, ang in ((17, self.t * 90), (17, self.t * 90 + 180)):      # orbital ring around the beacon
                    c.create_arc(sx - s, sy - s * 0.6, sx + s, sy + s * 0.6, start=ang, extent=110, style="arc",
                                 outline=col, width=2, tags="dyn")
                c.create_oval(sx - 6.5, sy - 6.5, sx + 6.5, sy + 6.5, fill=col, outline="#ffffff", width=1, tags="dyn")
                c.create_oval(sx - 2.2, sy - 2.2, sx + 2.2, sy + 2.2, fill="#ffffff", outline="", tags="dyn")
                pills.append((lang, sx, sy, col, tag))
            else:
                hov = self.hover_beacon == lang.key
                r = 2.4 + 1.1 * z + 0.6 * math.sin(ph) + (2.0 if hov else 0)
                if hov:
                    c.create_oval(sx - r - 5, sy - r - 5, sx + r + 5, sy + r + 5, outline=P["ivory"], tags="dyn")
                c.create_oval(sx - r, sy - r, sx + r, sy + r, fill="#fff3c4", outline="#0c3f70", width=1, tags="dyn")
        for lang, sx, sy, col, tag in pills:
            self.draw_pill(lang, sx, sy, col, tag)

    def draw_pill(self, lang, sx, sy, col, tag):
        c, R = self.c, self.renderer
        title = ("%s \u00b7 " % tag if tag else "") + lang.name.upper()
        f1, f2 = self.F(13, "bold"), self.F(9)
        sub = lang.target
        w = max(f1.measure(title), f2.measure(sub)) + 26
        h = 40
        up = sy - R.cy > -R.R * 0.55
        px = clamp(sx - w / 2, 10, self.W - w - 10)
        py = sy - 64 if up else sy + 24
        py = clamp(py, 8, self.H - h - 8)
        stem_y = py + h if up else py
        c.create_line(sx, sy - 7 if up else sy + 7, sx, stem_y, fill=col, width=1, tags="dyn")
        c.create_polygon(rounded_poly(px, py, px + w, py + h, 14), smooth=True, fill="#0b3a68", outline=col,
                         width=1, tags="dyn")
        c.create_text(px + w / 2, py + 14, text=title, fill=P["ivory"], font=f1, tags="dyn")
        c.create_text(px + w / 2, py + 29, text=sub, fill=P["soft"], font=f2, tags="dyn")
        if not self.compare:
            self.pill_rect = (px, py, px + w, py + h)

    def draw_signal_arc(self):
        if not (self.phase == "located" and not self.compare and self.selected):
            return
        bp = self.beacon_xy.get(self.selected)
        if not bp or bp[2] < 0.08:
            return
        p0, p1 = self.lay["port_l"], (bp[0], bp[1])
        dist = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
        ctrl = ((p0[0] + p1[0]) / 2, min(p0[1], p1[1]) - dist * 0.30)
        prog = ease_out(self.arc_t)
        n = max(2, int(44 * prog))
        pts = []
        for i in range(n + 1):
            pts.extend(quad_bezier(p0, ctrl, p1, prog * i / n))
        base = bg_at(self.renderer.cy, self.H)
        self.c.create_line(pts, fill=mix(base, P["gold"], 0.7), width=1.5, dash=(7, 5),
                           dashoffset=int(self.t * 30) % 12, tags="dyn")
        sx, sy = quad_bezier(p0, ctrl, p1, (self.t * 0.5) % 1.0 * prog)
        self.c.create_oval(sx - 3, sy - 3, sx + 3, sy + 3, fill=P["gold"], outline="", tags="dyn")

    # ---- overlays: status, banner, tooltip, toast ----
    def draw_status_ui(self):
        c = self.c
        label, col, banner = self.status()
        x, y = self.W - 24, 30
        f = self.F(11, "bold")
        w = f.measure(label) + 44
        c.create_polygon(rounded_poly(x - w, y - 14, x, y + 14, 14), smooth=True, fill="#0b3a68", outline=col,
                         width=1, tags="dyn")
        pulse = 0.5 + 0.5 * math.sin(self.t * 5)
        c.create_oval(x - w + 12, y - 4, x - w + 20, y + 4, fill=mix("#0b3a68", col, 0.5 + 0.5 * pulse),
                      outline="", tags="dyn")
        c.create_text(x - w + 28, y, text=label, fill=P["ivory"], font=f, anchor="w", tags="dyn")
        if banner:
            f2 = self.F(12, "bold")
            bw = f2.measure(banner) + 44
            by = self.gcy + self.gR + 30
            edge = mix("#0b3a68", col, 0.55 + 0.45 * pulse)
            c.create_polygon(rounded_poly(self.gcx - bw / 2, by - 15, self.gcx + bw / 2, by + 15, 15), smooth=True,
                             fill="#0b3a68", outline=edge, width=2, tags="dyn")
            c.create_text(self.gcx, by, text=banner, fill=col, font=f2, tags="dyn")

    def draw_tooltip(self):
        key = self.hover_beacon
        if not key or key not in self.beacon_xy:
            return
        lang = LANG[key]
        c = self.c
        lines = (("LANGUAGE", lang.name), ("REGION", lang.region), ("SCRIPT", lang.script))
        f1, f2 = self.F(9, "bold"), self.F(12, "bold")
        w = max(f2.measure(v) for _, v in lines) + 26
        h = 6 + len(lines) * 30
        mx, my = self.mouse
        x = clamp(mx + 16, 8, self.W - w - 8)
        y = clamp(my - h - 10, 8, self.H - h - 8)
        c.create_polygon(rounded_poly(x, y, x + w, y + h, 12), smooth=True, fill="#0b3a68", outline=P["gold"],
                         width=1, tags="dyn")
        for i, (lab, val) in enumerate(lines):
            yy = y + 12 + i * 30
            c.create_text(x + 13, yy, text=lab, fill=P["soft"], font=f1, anchor="w", tags="dyn")
            c.create_text(x + 13, yy + 13, text=val, fill=P["ivory"], font=f2, anchor="w", tags="dyn")

    def draw_toast(self):
        if self.toast_t <= 0:
            return
        f = self.F(12, "bold")
        w = f.measure(self.toast_msg) + 40
        x, y = self.gcx, self.gcy - self.gR * 0.05
        self.c.create_polygon(rounded_poly(x - w / 2, y - 18, x + w / 2, y + 18, 18), smooth=True,
                              fill="#0b3a68", outline=P["coral"], width=2, tags="dyn")
        self.c.create_text(x, y, text=self.toast_msg, fill=P["ivory"], font=f, tags="dyn")

    # ------------------------------------------------------------------
    # dynamic text values (right panel, profile strip, flow steps)
    # ------------------------------------------------------------------
    def scramble(self, n, seed):
        r = random.Random(int(self.t * 14) * 31 + seed)
        return "".join(r.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789#%&") for _ in range(n))

    def prog(self, i, dur=0.55):
        return clamp((self.reveal_t - 0.15 * i) / dur, 0.0, 1.0)

    def reveal(self, s, i):
        p = self.prog(i)
        n = int(len(s) * p + 0.0001)
        out = s[:n]
        if p < 1.0:
            out += "\u258c"
        return out

    def relation_text(self):
        if not self.compare:
            return ""
        la, lb = LANG[self.compare[0]], LANG[self.compare[1]]
        if la.family == lb.family and la.script == lb.script:
            return "SAME FAMILY \u00b7 SAME SCRIPT"
        if la.family == lb.family:
            return "SAME FAMILY \u00b7 DIFFERENT SCRIPT"
        if la.script == lb.script:
            return "DIFFERENT FAMILY \u00b7 SAME SCRIPT"
        return "DIFFERENT FAMILY & SCRIPT"

    def draw_values(self):
        c = self.c
        c.delete("vals")
        rp, oy, k = self.rp, self.rp["oy"], self.rp["k"]
        x, x2, w = rp["x"], rp["x2"], rp["w"]
        busy = self.phase in ("scan", "seek")
        located = self.phase == "located"
        lang = self.info_lang
        cmp_ = self.compare
        dash = "\u2014"

        def val(text, i, seed):
            if busy:
                return self.scramble(max(6, min(14, len(text))), seed), P["dim"]
            if located:
                return self.reveal(text, i), None
            return dash, P["dim"]

        # ------------------ right panel ------------------
        if cmp_:
            la, lb = LANG[cmp_[0]], LANG[cmp_[1]]
            head = "%s  \u2194  %s" % (la.name.upper(), lb.name.upper())
            self.T(x, oy(88), head, self.fit(head, w, (24, 20, 17, 14), "bold"), P["gold"], "bold",
                   serif=True, tag="vals")
            rows = [("SCRIPT", la.script, lb.script), ("ASSOCIATED REGION", la.region, lb.region),
                    ("LANGUAGE FAMILY", la.family, lb.family)]
            for i, (lab, a, b) in enumerate(rows):
                yy = oy(122 + i * 52)
                self.T(x, yy, lab, 9, P["soft"], "bold", tag="vals")
                for j, (txt, colr) in enumerate(((a, P["coral"]), (b, P["turq"]))):
                    s, dc = val(txt.upper(), i + j, 9 + i * 3 + j)
                    c.create_oval(x, yy + 12 + j * 16 - 3, x + 6, yy + 12 + j * 16 + 3, fill=colr, outline="", tags="vals")
                    self.T(x + 14, yy + 15 + j * 16 - 3, s, 12, dc or P["ivory"], "bold", tag="vals")
            yy = oy(122 + 3 * 52)
            self.T(x, yy, "RELATIONSHIP", 9, P["soft"], "bold", tag="vals")
            rel = self.relation_text()
            s, dc = val(rel, 4, 21)
            self.T(x, yy + 16, s, 11, dc or P["gold"], "bold", tag="vals")
            if self.cmp_split and located:
                self.T(x, oy(330), "Regions are far apart \u2014 the globe alternates between them.", 10,
                       P["dim"], slant="italic", anchor="nw", width=w, tag="vals")
        else:
            name = lang.name.upper() if lang else ""
            if not lang:
                s, dc = dash, P["dim"]
            else:
                s, dc = val(name, 0, 1)
            nsz = self.fit(name or "LANGUAGE", w * 0.62, (36, 32, 28, 24), "bold")
            self.T(x, oy(88), s if lang else "AWAITING SIGNAL",
                   nsz if lang else 22, dc or P["gold"] if lang else P["dim"], "bold", serif=True, tag="vals")
            if lang and located:
                self.T(x2, oy(92), lang.native, 20, P["ivory"], anchor="e", serif=True, tag="vals")
            fields = [("SCRIPT", lang.script.upper() if lang else ""), ("ASSOCIATED REGION", lang.region.upper() if lang else ""),
                      ("TARGET AREA", lang.target.upper() if lang else ""), ("LANGUAGE FAMILY", lang.family.upper() if lang else "")]
            for i, (lab, txt) in enumerate(fields):
                yy = oy(126 + i * 38)
                self.T(x, yy, lab, 9, P["soft"], "bold", tag="vals")
                s, dc = val(txt, i + 1, 5 + i * 7) if lang else (dash, P["dim"])
                self.T(x, yy + 16 * k, s, self.fit(s, w, (15, 13, 11), "bold", False), dc or P["ivory"], "bold",
                       tag="vals")
            yy = oy(126 + 4 * 38)
            self.T(x, yy, "DEMO CONFIDENCE", 9, P["soft"], "bold", tag="vals")
            if lang and located and self.signal:
                p = self.prog(5, 0.9)
                shown = int(self.signal.confidence * p)
                self.T(x, yy + 16, "%d%%" % shown, 15, P["ivory"], "bold", tag="vals")
                bx1, bx2, by = x + 58, x2, yy + 17
                c.create_polygon(rounded_poly(bx1, by - 4, bx2, by + 4, 4), smooth=True,
                                 fill=mix(self.panel_fill(by), "#000000", 0.2), outline="", tags="vals")
                fw = (bx2 - bx1) * shown / 100.0
                if fw > 10:
                    c.create_polygon(rounded_poly(bx1, by - 4, bx1 + fw, by + 4, 4), smooth=True,
                                     fill=P["turq"], outline="", tags="vals")
            elif lang and located:
                self.T(x, yy + 16, "n/a \u2014 picked on the globe", 12, P["dim"], slant="italic", tag="vals")
            elif busy:
                self.T(x, yy + 16, self.scramble(3, 40), 15, P["dim"], "bold", tag="vals")
            else:
                self.T(x, yy + 16, dash, 15, P["dim"], "bold", tag="vals")

        # ---------- flow steps ----------
        fy0 = oy(402)
        pitch = 26 * k if k < 1 else 27
        for i, lab in enumerate(FLOW_LABELS):
            yy = fy0 + i * pitch
            lit = self.flow_stage >= i + 1
            act = self.flow_stage == i + 1
            col = P["gold"] if lit else mix(self.panel_fill(yy), P["cyan"], 0.35)
            nx = x + 8
            if i < 4:
                nxt = self.flow_stage >= i + 2
                c.create_line(nx, yy + 6, nx, yy + pitch - 6, fill=P["gold"] if nxt else mix(self.panel_fill(yy), P["cyan"], 0.25),
                              tags="vals")
            if act:
                r = 7 + 2 * math.sin(self.t * 5)
                c.create_oval(nx - r, yy - r, nx + r, yy + r, outline=P["gold"], tags="vals")
            c.create_oval(nx - 4.5, yy - 4.5, nx + 4.5, yy + 4.5, fill=col if lit else self.panel_fill(yy),
                          outline=col, tags="vals")
            self.T(x + 24, yy, lab, 10, P["ivory"] if lit else P["dim"], "bold", tag="vals")
            fv = self.flow_value(i)
            if fv:
                self.T(x2, yy, fv, 10, P["gold"], anchor="e", tag="vals")

        # ------------------ bottom strip ------------------
        y1s, y2s = self.strip[1], self.strip[3]
        if cmp_:
            la, lb = LANG[cmp_[0]], LANG[cmp_[1]]
            vals = ["%s \u2194 %s" % (la.name, lb.name), "%s / %s" % (la.script.split(" (")[0], lb.script.split(" (")[0]),
                    "%s / %s" % (la.region.split(" /")[0], lb.region.split(" /")[0]),
                    "%s / %s" % (la.family.split(" (")[0], lb.family.split(" (")[0])]
            status = "COMPARING" if located else ("SEARCHING\u2026" if busy else dash)
        elif lang:
            vals = [lang.name, lang.script, lang.region, lang.family]
            status = {"scan": "SIGNAL RECEIVED", "seek": "SEARCHING REGION\u2026",
                      "located": "REGION LOCATED" if self.info_mode == "trace" else "REGION SELECTED"}.get(self.phase, "STANDING BY")
        else:
            vals, status = [dash] * 4, "STANDING BY"
        for i, (cx_, cw_) in enumerate(self.strip_cols):
            if i < 4:
                txt = vals[i]
                if busy and lang and not cmp_:
                    s, dc = self.scramble(min(10, max(6, len(txt))), 60 + i), P["dim"]
                elif located and lang and not cmp_:
                    s, dc = self.reveal(txt, i), None
                else:
                    s, dc = txt, (P["ivory"] if cmp_ and located else P["dim"])
                    if cmp_ and busy:
                        s, dc = self.scramble(8, 70 + i), P["dim"]
                self.T(cx_, y1s + 50, s, self.fit(txt if not busy else s, cw_, (18, 16, 14, 12, 10), "bold"),
                       dc or P["ivory"], "bold", serif=True, tag="vals")
            else:
                colr = P["turq"] if located else (P["gold"] if busy else P["dim"])
                pr = 0.5 + 0.5 * math.sin(self.t * 5)
                c.create_oval(cx_, y1s + 44, cx_ + 8, y1s + 52, fill=mix(self.panel_fill(y1s), colr, 0.5 + 0.5 * pr if busy or located else 0.6),
                              outline="", tags="vals")
                self.T(cx_ + 16, y1s + 50, status, self.fit(status, cw_ - 18, (14, 12, 10), "bold", False), colr,
                       "bold", tag="vals")

    def flow_value(self, i):
        st = self.flow_stage
        if st < i + 1:
            return ""
        located = self.phase == "located"
        lang = self.info_lang
        if self.compare:
            return ["2 picked", "compared", "", "", ""][i] if i < 2 else (
                ["", "", "2 scripts", "2 regions", self.relation_text().split(" \u00b7")[0].title()][i] if located or i < 2 else "")
        if i == 0:
            return ("%d characters" % self.signal.chars) if self.signal else "picked on globe"
        if not lang:
            return ""
        if i == 1:
            return lang.name if located else "detected\u2026"
        if not located:
            return ""
        if i == 2:
            return lang.script.split(" (")[0]
        if i == 3:
            return lang.region.split(" /")[0]
        return lang.family.split(" (")[0]


# =====================================================================
def main():
    root = tk.Tk()
    LanguageGlobeApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()