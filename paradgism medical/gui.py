"""
gui.py -- Tkinter GUI for the Medical Diagnostic System.

Six page consultation: Welcome -> Registration -> Vitals -> Symptoms -> Consultation -> Results

"""

import math
import queue
import random
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from typing import List, Optional, Tuple

from state_handler import UserSession
from input_processor_bridge import (
    extractSymptoms,
    prioritizeSymptoms,
    computeSeverityScore,
    getWeight,
    symptomDisplayName,
)
import re
from prolog_bridge import PrologBridge
import patient_history
import consultation_log

# ── Consultation tuning constants ──────────────────────────────────────
MAX_QUESTIONS              = 30
MIN_SYMPTOMS               = 2
CONFIDENCE_THRESHOLD       = 0.75
NEWS2_ESCALATION_THRESHOLD = 5


def loadPrecautions(solutions_path: Path) -> dict:
    precautions: dict = {}
    if not solutions_path.exists():
        return precautions
    pattern = re.compile(r"precaution\(([^,]+),\s*([^)]+)\)\.")
    for line in solutions_path.read_text(encoding="utf-8").splitlines():
        m = pattern.search(line)
        if m:
            disease = m.group(1).strip()
            action  = m.group(2).strip().replace("_", " ")
            precautions.setdefault(disease, []).append(action)
    return precautions


def loadDescriptions(desc_path: Path) -> dict:
    descriptions: dict = {}
    if not desc_path.exists():
        return descriptions
    pattern = re.compile(r'description\(([^,]+),\s*"([^"]+)"\)')
    for line in desc_path.read_text(encoding="utf-8").splitlines():
        m = pattern.search(line)
        if m:
            descriptions[m.group(1).strip()] = m.group(2).strip()
    return descriptions


# ── Colour palette ─────────────────────────────────────────────────────
BG         = "#f0f4f8"
cardBg     = "#ffffff"
headerBg   = "#1e3a5f"
headerFg   = "#ffffff"
SIDEBAR_BG = "#1e3a5f"
SIDEBAR_FG = "#94b0d1"
PRIMARY    = "#2563eb"
PRIMARY_FG = "#ffffff"
YES_CLR    = "#16a34a"
NO_CLR     = "#dc2626"
TEXT       = "#1e293b"
MUTED      = "#64748b"
SEV_LOW    = "#16a34a"
SEV_MOD    = "#d97706"
SEV_HIGH   = "#ea580c"
SEV_CRIT   = "#dc2626"
WELCOME_BG = "#e8f0fb"
DOCTOR_BG  = "#dbeafe"

HOVER = {
    PRIMARY:   "#1d4ed8",
    YES_CLR:   "#15803d",
    NO_CLR:    "#b91c1c",
    "#7c3aed": "#6d28d9",
    "#059669": "#047857",
    "#6b7280": "#4b5563",
}

MOSAIC_PALETTE = [
    "#edf2f7", "#f2f6fa", "#eef3f8", "#f0f5fb",
    "#ebf0f5", "#f4f7fb", "#e9eff5", "#f1f5f9",
    "#ecf1f7", "#f3f7fc",
]
MOSAIC_TILE = 38


# ══════════════════════════════════════════════════════════════════════════════
#  Animated Doctor Widget
# ══════════════════════════════════════════════════════════════════════════════

class DoctorCanvas(tk.Canvas):
    """Animated Akinator-style doctor character for the consultation page."""

    EXPRESSIONS = frozenset({"neutral", "happy", "thinking", "concerned", "surprised"})

    def __init__(self, parent, **kw):
        kw.setdefault("highlightthickness", 0)
        kw.setdefault("width", 200)
        kw.setdefault("height", 320)
        super().__init__(parent, **kw)
        self.configure(bg=DOCTOR_BG)

        self.expr     = "neutral"
        self.bobY     = 0.0
        self.bobDir   = 1
        self.armAng   = 0.0
        self.armDir   = 1
        self.blinkSt  = False
        self.blinkCnt = 0
        self.blinkNxt = 100

        self.bind("<Configure>", lambda e: self.redraw())
        self.after(50, self.tick)

    def setExpression(self, expr: str) -> None:
        if expr in self.EXPRESSIONS:
            self.expr = expr

    def tick(self) -> None:
        if not self.winfo_exists():
            return

        self.bobY += 0.35 * self.bobDir
        if self.bobY >= 4:
            self.bobDir = -1
        elif self.bobY <= -4:
            self.bobDir = 1

        if self.expr in ("happy", "surprised"):
            self.armAng += 4 * self.armDir
            if self.armAng >= 28:
                self.armDir = -1
            elif self.armAng <= 0:
                self.armDir = 1
        else:
            self.armAng = max(0.0, self.armAng - 3.0)
            self.armDir = 1

        self.blinkCnt += 1
        if self.blinkCnt >= self.blinkNxt:
            self.blinkSt = True
            if self.blinkCnt >= self.blinkNxt + 4:
                self.blinkSt  = False
                self.blinkCnt = 0
                self.blinkNxt = random.randint(60, 150)

        self.redraw()
        self.after(50, self.tick)

    def redraw(self) -> None:
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 10 or h < 10:
            return

        cx  = w // 2
        oy  = max(0, (h - 300) // 2)
        bob = int(self.bobY)
        arm = int(self.armAng)

        def y(base): return base + oy + bob

        # Background with dot grid
        self.create_rectangle(0, 0, w, h, fill=DOCTOR_BG, outline="")
        for gx in range(12, w, 22):
            for gy in range(12, h, 22):
                self.create_oval(gx-2, gy-2, gx+2, gy+2, fill="#bfdbfe", outline="")

        # Ground shadow
        self.create_oval(cx-30, y(290), cx+30, y(300), fill="#b8cfe0", outline="")

        # Shoes
        self.create_oval(cx-28, y(265), cx-2,  y(280), fill="#111", outline="")
        self.create_oval(cx+2,  y(265), cx+28, y(280), fill="#111", outline="")

        # Trousers
        self.create_rectangle(cx-22, y(218), cx-4,  y(268), fill="#1e3a5f", outline="#152b4a")
        self.create_rectangle(cx+4,  y(218), cx+22, y(268), fill="#1e3a5f", outline="#152b4a")

        # White coat body
        self.create_rectangle(cx-36, y(116), cx+36, y(222), fill="#f5f5f5", outline="#d8d8d8")

        # Shirt / collar
        self.create_polygon([cx-15, y(116), cx, y(138), cx+15, y(116)], fill="#1e40af", outline="")

        # Tie
        tp = [cx-5, y(130), cx+5, y(130), cx+8, y(170), cx, y(182), cx-8, y(170)]
        self.create_polygon(tp, fill="#b91c1c", outline="#991b1b")

        # Lapels
        self.create_polygon([cx-36, y(116), cx-10, y(116), cx-16, y(166), cx-36, y(166)],
                            fill="#ececec", outline="#ccc")
        self.create_polygon([cx+36, y(116), cx+10, y(116), cx+16, y(166), cx+36, y(166)],
                            fill="#ececec", outline="#ccc")

        # Buttons
        for bi in range(3):
            by = y(176 + bi * 13)
            self.create_oval(cx-4, by-4, cx+4, by+4, fill="#ddd", outline="#bbb")

        # Breast pocket + pen
        self.create_rectangle(cx-34, y(153), cx-15, y(174), fill="#ececec", outline="#ccc")
        self.create_rectangle(cx-30, y(146), cx-24, y(158), fill="#2563eb", outline="")
        self.create_oval(     cx-30, y(141), cx-24, y(148), fill="#fbbf24", outline="")

        # Stethoscope
        self.create_arc(cx+8,  y(141), cx+32, y(171),
                        start=0, extent=-270, style="arc", outline="#555", width=3)
        self.create_oval(cx+27, y(167), cx+37, y(177), fill="#666", outline="#444", width=2)

        # Left arm (waves when happy/surprised)
        lbx, lby = cx-62, y(176) - arm
        self.create_line(cx-36, y(136), lbx, lby, fill="#f0f0f0", width=16, capstyle="round")
        self.create_line(cx-36, y(136), lbx, lby, fill="#ddd",    width=1)
        self.create_oval(lbx-7, lby-6, lbx+7, lby+8, fill="#fcd5b5", outline="#e8a87c")

        # Right arm + clipboard
        self.create_line(cx+36, y(136), cx+62, y(178), fill="#f0f0f0", width=16, capstyle="round")
        self.create_line(cx+36, y(136), cx+62, y(178), fill="#ddd",    width=1)
        self.create_rectangle(cx+56, y(172), cx+76, y(208), fill="#fffbe6", outline="#c8a000")
        self.create_rectangle(cx+59, y(168), cx+73, y(176), fill="#888",    outline="#666")
        for li in range(3):
            ly = y(180 + li * 9)
            self.create_line(cx+59, ly, cx+74, ly, fill="#ccc", width=1)

        # Neck
        self.create_rectangle(cx-8, y(106), cx+8, y(120), fill="#fcd5b5", outline="#e8a87c")

        # Head
        self.create_oval(cx-32, y(38), cx+32, y(110), fill="#fcd5b5", outline="#e8a87c", width=2)

        # Hair
        self.create_arc( cx-32, y(32),  cx+32, y(78),  start=0, extent=180, fill="#3d2b1f", outline="")
        self.create_oval(cx-37, y(53),  cx-24, y(80),  fill="#3d2b1f", outline="")
        self.create_oval(cx+24, y(53),  cx+37, y(80),  fill="#3d2b1f", outline="")

        # Ears
        self.create_oval(cx-39, y(64), cx-27, y(81), fill="#fcd5b5", outline="#e8a87c")
        self.create_oval(cx+27, y(64), cx+39, y(81), fill="#fcd5b5", outline="#e8a87c")

        # Eyebrows
        expr  = self.expr
        blink = self.blinkSt

        if expr == "thinking":
            self.create_line(cx-22, y(62), cx-8,  y(66), fill="#3d2b1f", width=2)
            self.create_line(cx+8,  y(58), cx+22, y(62), fill="#3d2b1f", width=2)
        elif expr == "concerned":
            self.create_line(cx-22, y(62), cx-8,  y(66), fill="#3d2b1f", width=2)
            self.create_line(cx+8,  y(66), cx+22, y(62), fill="#3d2b1f", width=2)
        elif expr == "surprised":
            self.create_arc(cx-22, y(52), cx-6,  y(66), start=0, extent=180, style="arc", outline="#3d2b1f", width=2)
            self.create_arc(cx+6,  y(52), cx+22, y(66), start=0, extent=180, style="arc", outline="#3d2b1f", width=2)
        else:
            self.create_line(cx-22, y(64), cx-8,  y(64), fill="#3d2b1f", width=2)
            self.create_line(cx+8,  y(64), cx+22, y(64), fill="#3d2b1f", width=2)

        # Eyes
        if blink:
            self.create_line(cx-20, y(74), cx-8,  y(74), fill="#333", width=2)
            self.create_line(cx+8,  y(74), cx+20, y(74), fill="#333", width=2)
        elif expr == "happy":
            self.create_arc(cx-20, y(70), cx-8,  y(80), start=0, extent=180, style="arc", outline="#333", width=2)
            self.create_arc(cx+8,  y(70), cx+20, y(80), start=0, extent=180, style="arc", outline="#333", width=2)
        elif expr == "surprised":
            self.create_oval(cx-20, y(68), cx-8,  y(82), fill="#222", outline="")
            self.create_oval(cx+8,  y(68), cx+20, y(82), fill="#222", outline="")
        else:
            self.create_oval(cx-20, y(70), cx-9,  y(80), fill="#333", outline="")
            self.create_oval(cx+9,  y(70), cx+20, y(80), fill="#333", outline="")
            self.create_oval(cx-18, y(71), cx-15, y(74), fill="white", outline="")
            self.create_oval(cx+11, y(71), cx+14, y(74), fill="white", outline="")

        # Glasses (on top of eyes)
        self.create_oval(cx-22, y(66), cx-6,  y(82), outline="#555", width=2)
        self.create_oval(cx+6,  y(66), cx+22, y(82), outline="#555", width=2)
        self.create_line(cx-6,  y(74), cx+6,  y(74), fill="#555", width=2)
        self.create_line(cx-22, y(74), cx-32, y(72), fill="#555", width=2)
        self.create_line(cx+22, y(74), cx+32, y(72), fill="#555", width=2)

        # Nose
        self.create_oval(cx-4, y(82), cx+4, y(90), fill="#e8a87c", outline="")

        # Mouth
        if expr == "happy":
            self.create_arc(cx-14, y(89), cx+14, y(106), start=200, extent=140, fill="#c44", outline="#a33")
            self.create_arc(cx-11, y(91), cx+11, y(104), start=205, extent=130, fill="white", outline="")
        elif expr == "thinking":
            self.create_line([cx-10, y(96), cx-3, y(92), cx+3, y(96), cx+10, y(92)],
                             fill="#c44", width=2, smooth=True)
        elif expr == "concerned":
            self.create_arc(cx-12, y(95), cx+12, y(107), start=20,  extent=140, style="arc", outline="#c44", width=2)
        elif expr == "surprised":
            self.create_oval(cx-8, y(90), cx+8, y(106), fill="#c44", outline="#a33")
        else:
            self.create_arc(cx-12, y(91), cx+12, y(105), start=210, extent=120, style="arc", outline="#c44", width=2)


# ══════════════════════════════════════════════════════════════════════════════
#  Main GUI
# ══════════════════════════════════════════════════════════════════════════════

class DiagnosticGUI:

    STEPS = [
        ("1", "Welcome"),
        ("2", "Patient Info"),
        ("3", "Vital Signs"),
        ("4", "Symptoms"),
        ("5", "Consultation"),
        ("6", "Results"),
    ]

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Medical Diagnostic System v2.63")
        self.root.geometry("960x780")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)

        self.session: Optional[UserSession] = None
        self.bridge = PrologBridge()
        self.precautions  = loadPrecautions(Path(__file__).parent / "solutions.pl")
        self.descriptions = loadDescriptions(Path(__file__).parent / "symptoms_descriptions.pl")
        self.questionQueue: List[Tuple[str, str]] = []
        self.qIndex = 0
        self.extractedSymptoms: List[str] = []

        self.resultQueue: queue.Queue = queue.Queue()
        self.inferenceThread: Optional[threading.Thread] = None

        self.doctorWidget:  Optional[DoctorCanvas] = None
        self.doctorStatus:  Optional[tk.Label]     = None
        self.typeJob:       Optional[str]           = None

        self.buildChrome()
        self.buildWelcome()
        self.buildRegistration()
        self.buildVitals()
        self.buildSymptoms()
        self.buildConsultation()
        self.buildResults()
        self.show("welcome")
        self.pollResultQueue()

    # ── chrome ─────────────────────────────────────────────────────────────────

    def buildChrome(self) -> None:
        hdr = tk.Frame(self.root, bg=headerBg, height=60)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        crossCvs = tk.Canvas(hdr, bg=headerBg, width=32, height=32, highlightthickness=0)
        crossCvs.pack(side="left", padx=(18, 6), pady=14)
        crossCvs.create_rectangle(12, 2,  20, 30, fill="#60a5fa", outline="")
        crossCvs.create_rectangle(2,  12, 30, 20, fill="#60a5fa", outline="")

        tk.Label(hdr, text="Medical Diagnostic System",
                 font=("Segoe UI", 15, "bold"),
                 bg=headerBg, fg=headerFg).pack(side="left", pady=14)
        tk.Label(hdr, text="v2.63",
                 font=("Segoe UI", 9),
                 bg=headerBg, fg="#4a6fa5").pack(side="left", padx=6, pady=16)

        row = tk.Frame(self.root, bg=BG)
        row.pack(fill="both", expand=True)

        self.sidebar = tk.Frame(row, bg=SIDEBAR_BG, width=178)
        self.sidebar.pack(fill="y", side="left")
        self.sidebar.pack_propagate(False)
        tk.Label(self.sidebar, text="STEPS", font=("Segoe UI", 8, "bold"),
                 bg=SIDEBAR_BG, fg="#4a6fa5").pack(anchor="w", padx=18, pady=(22, 6))

        self.stepFrames: List[tuple] = []
        for num, label in self.STEPS:
            frm = tk.Frame(self.sidebar, bg=SIDEBAR_BG, cursor="arrow")
            frm.pack(fill="x")
            nLbl = tk.Label(frm, text=num, font=("Segoe UI", 10, "bold"),
                            bg=SIDEBAR_BG, fg=SIDEBAR_FG, width=3)
            nLbl.pack(side="left", padx=(14, 4), pady=10)
            lLbl = tk.Label(frm, text=label, font=("Segoe UI", 10),
                            bg=SIDEBAR_BG, fg=SIDEBAR_FG, anchor="w")
            lLbl.pack(side="left")
            self.stepFrames.append((frm, nLbl, lLbl))

        self.content = tk.Frame(row, bg=BG)
        self.content.pack(fill="both", expand=True, padx=22, pady=18)
        self.pages: dict = {}

    def show(self, name: str) -> None:
        for p in self.pages.values():
            p.pack_forget()
        self.pages[name].pack(fill="both", expand=True)
        order = ["welcome", "registration", "vitals", "symptoms", "consultation", "results"]
        active = order.index(name) if name in order else 0
        for i, (frm, nLbl, lLbl) in enumerate(self.stepFrames):
            if i == active:
                frm.configure(bg=PRIMARY)
                nLbl.configure(bg=PRIMARY, fg="white")
                lLbl.configure(bg=PRIMARY, fg="white")
            elif i < active:
                frm.configure(bg=SIDEBAR_BG)
                nLbl.configure(bg=SIDEBAR_BG, fg="#4ade80")
                lLbl.configure(bg=SIDEBAR_BG, fg="#4ade80")
            else:
                frm.configure(bg=SIDEBAR_BG)
                nLbl.configure(bg=SIDEBAR_BG, fg=SIDEBAR_FG)
                lLbl.configure(bg=SIDEBAR_BG, fg=SIDEBAR_FG)

    # ── widget helpers ─────────────────────────────────────────────────────────

    def title(self, parent, text: str) -> tk.Label:
        return tk.Label(parent, text=text, font=("Segoe UI", 17, "bold"),
                        bg=parent["bg"], fg=TEXT)

    def sub(self, parent, text: str) -> tk.Label:
        return tk.Label(parent, text=text, font=("Segoe UI", 10),
                        bg=parent["bg"], fg=MUTED)

    def lbl(self, parent, text: str, size=11, bold=False, color=TEXT, **kw) -> tk.Label:
        w = "bold" if bold else "normal"
        return tk.Label(parent, text=text, font=("Segoe UI", size, w),
                        bg=parent["bg"], fg=color, **kw)

    def card(self, parent) -> tk.Frame:
        return tk.Frame(parent, bg=cardBg, relief="flat", bd=1)

    def btn(self, parent, text, cmd, color=PRIMARY, fg="white", width=13) -> tk.Button:
        hover = HOVER.get(color, color)
        b = tk.Button(parent, text=text, command=cmd,
                      font=("Segoe UI", 11, "bold"),
                      bg=color, fg=fg, activebackground=hover, activeforeground=fg,
                      relief="flat", bd=0, padx=18, pady=11,
                      cursor="hand2", width=width)
        b.bind("<Enter>", lambda _: b.configure(bg=hover))
        b.bind("<Leave>", lambda _: b.configure(bg=color))
        return b

    def navRow(self, parent) -> tk.Frame:
        f = tk.Frame(parent, bg=BG)
        f.pack(side="bottom", anchor="e", pady=(12, 0))
        return f

    def field(self, parent, labelText: str, var: tk.StringVar, hint="") -> None:
        tk.Label(parent, text=labelText, font=("Segoe UI", 10, "bold"),
                 bg=cardBg, fg=TEXT).pack(anchor="w")
        if hint:
            tk.Label(parent, text=hint, font=("Segoe UI", 8),
                     bg=cardBg, fg=MUTED).pack(anchor="w")
        ent = tk.Entry(parent, textvariable=var, font=("Segoe UI", 12),
                       relief="solid", bd=1, fg=TEXT, width=36,
                       insertbackground=PRIMARY)
        ent.pack(anchor="w", pady=(3, 12))
        ent.bind("<FocusIn>",  lambda e: ent.configure(highlightthickness=2,
                                                        highlightbackground=PRIMARY,
                                                        highlightcolor=PRIMARY))
        ent.bind("<FocusOut>", lambda e: ent.configure(highlightthickness=0))

    def addMosaicBg(self, page: tk.Frame) -> None:
        cvs = tk.Canvas(page, bg=BG, highlightthickness=0)
        cvs.place(x=0, y=0, relwidth=1, relheight=1)

        def draw(*_):
            w = cvs.winfo_width()
            h = cvs.winfo_height()
            if w < 10 or h < 10:
                return
            cvs.delete("all")
            for gx in range(0, w, MOSAIC_TILE):
                for gy in range(0, h, MOSAIC_TILE):
                    col = MOSAIC_PALETTE[
                        ((gx // MOSAIC_TILE) * 3 + (gy // MOSAIC_TILE) * 7) % len(MOSAIC_PALETTE)
                    ]
                    cvs.create_rectangle(gx + 1, gy + 1,
                                         gx + MOSAIC_TILE - 1, gy + MOSAIC_TILE - 1,
                                         fill=col, outline="")

        cvs.bind("<Configure>", draw)

    # ── PAGE 1: Welcome ────────────────────────────────────────────────────────

    def buildWelcome(self) -> None:
        page = tk.Frame(self.content, bg=BG)
        self.pages["welcome"] = page
        self.addMosaicBg(page)

        cvs = tk.Canvas(page, bg=WELCOME_BG, highlightthickness=0)
        cvs.pack(expand=True, fill="both", padx=30, pady=20)

        inner = tk.Frame(cvs, bg=WELCOME_BG)

        tk.Label(inner, text="Welcome to the",
                 font=("Segoe UI", 13), bg=WELCOME_BG, fg=MUTED).pack()
        tk.Label(inner, text="Medical Diagnostic System",
                 font=("Segoe UI", 26, "bold"), bg=WELCOME_BG, fg=TEXT).pack()
        tk.Label(inner,
                 text="DISCLAIMER: Educational tool only.  Always consult a licensed physician.",
                 font=("Segoe UI", 9), bg=WELCOME_BG, fg="#ef4444").pack(pady=(4, 18))

        btnFrame = tk.Frame(inner, bg=WELCOME_BG)
        btnFrame.pack()
        self.btn(btnFrame, "Begin Consultation  →", self.goRegistration, width=22).pack(pady=4)
        self.pulseR   = 32
        self.pulseDir = 1
        self.ecgPhase = 0
        cvsState = {"cx": 0, "cy": 0, "w": 0, "h": 0}

        def redraw(*_):
            w = cvs.winfo_width()
            h = cvs.winfo_height()
            if w < 10 or h < 10:
                return

            cvs.delete("mosaic")
            for gx in range(0, w, MOSAIC_TILE):
                for gy in range(0, h, MOSAIC_TILE):
                    col = MOSAIC_PALETTE[
                        ((gx // MOSAIC_TILE) * 3 + (gy // MOSAIC_TILE) * 7) % len(MOSAIC_PALETTE)
                    ]
                    cvs.create_rectangle(gx + 1, gy + 1,
                                         gx + MOSAIC_TILE - 1, gy + MOSAIC_TILE - 1,
                                         fill=col, outline="", tags="mosaic")

            cx, cy = w // 2, h // 3 - 10
            cvs.delete("cross")
            arm, thick = 28, 9
            cvs.create_rectangle(cx-thick, cy-arm, cx+thick, cy+arm,
                                  fill=PRIMARY, outline="", tags="cross")
            cvs.create_rectangle(cx-arm, cy-thick, cx+arm, cy+thick,
                                  fill=PRIMARY, outline="", tags="cross")

            cvs.delete("win")
            cvs.create_window(w // 2, cy + arm + 60, window=inner, anchor="n", tags="win")
            cvsState["cx"] = cx
            cvsState["cy"] = cy
            cvsState["w"]  = w
            cvsState["h"]  = h

        def pulse():
            if not cvs.winfo_exists():
                return
            cx = cvsState["cx"]
            cy = cvsState["cy"]
            if cx:
                cvs.delete("pulse")
                r = self.pulseR
                shade = "#93c5fd" if r < 48 else "#bfdbfe"
                cvs.create_oval(cx-r, cy-r, cx+r, cy+r,
                                outline=shade, width=2, tags="pulse")
                self.pulseR += self.pulseDir
                if self.pulseR >= 58:
                    self.pulseDir = -1
                elif self.pulseR <= 32:
                    self.pulseDir = 1
            cvs.after(35, pulse)

        def ecg():
            if not cvs.winfo_exists():
                return
            w = cvsState["w"]
            h = cvsState["h"]
            if w < 10:
                cvs.after(40, ecg)
                return
            cvs.delete("ecg")
            yBase = h - 28
            phase = self.ecgPhase
            pts = []
            for px in range(0, w + 1, 2):
                t = (px + phase) % 120
                if   t < 38:  yv = 0
                elif t < 46:  yv = -7  * math.sin(math.pi * (t - 38) / 8)
                elif t < 51:  yv = -42 * math.sin(math.pi * (t - 46) / 5)
                elif t < 58:  yv =  16 * math.sin(math.pi * (t - 51) / 7)
                else:         yv = 0
                pts.extend([px, yBase + yv])
            if len(pts) >= 4:
                cvs.create_line(pts, fill="#3b82f6", width=2, tags="ecg", smooth=False)
            self.ecgPhase = (phase + 3) % 120
            cvs.after(35, ecg)

        cvs.bind("<Configure>", redraw)
        cvs.after(200, pulse)
        cvs.after(400, ecg)

    # ── PAGE 2: Registration ───────────────────────────────────────────────────

    def buildRegistration(self) -> None:
        page = tk.Frame(self.content, bg=BG)
        self.pages["registration"] = page
        self.addMosaicBg(page)

        self.title(page, "Patient Registration").pack(anchor="w")
        self.sub(page, "Enter the patient's basic information to begin.").pack(anchor="w", pady=(2, 16))

        c = self.card(page)
        c.pack(fill="x")
        tk.Frame(c, bg=PRIMARY, height=4).pack(fill="x")

        inner = tk.Frame(c, bg=cardBg)
        inner.pack(fill="x", padx=32, pady=24)

        self.nameVar   = tk.StringVar()
        self.ageVar    = tk.StringVar()
        self.genderVar = tk.StringVar(value="Rather not say")
        self.field(inner, "Full Name", self.nameVar)
        self.field(inner, "Age (optional)", self.ageVar, hint="Leave blank to skip")

        tk.Label(inner, text="Gender (optional)", font=("Segoe UI", 10, "bold"),
                 bg=cardBg, fg=TEXT).pack(anchor="w")
        ttk.Combobox(inner, textvariable=self.genderVar,
                     values=["Rather not say", "Male", "Female"],
                     state="readonly", width=20,
                     font=("Segoe UI", 12)).pack(anchor="w", pady=(3, 12))

        noticeFrame = tk.Frame(inner, bg="#eff6ff", padx=12, pady=8)
        noticeFrame.pack(fill="x", pady=(0, 4))
        tk.Label(noticeFrame, text="ℹ  Patient history", font=("Segoe UI", 9, "bold"),
                 bg="#eff6ff", fg="#1e40af").pack(anchor="w")
        self.historyLbl = tk.Label(noticeFrame,
                                   text="Enter a name above to check visit history.",
                                   font=("Segoe UI", 9), bg="#eff6ff", fg="#1e40af",
                                   wraplength=480, justify="left")
        self.historyLbl.pack(anchor="w")

        self.nameVar.trace_add("write", lambda *_: self.checkHistory())

        nav = self.navRow(page)
        self.btn(nav, "Next  →", self.goVitals).pack(side="right")

    # ── PAGE 3: Vital Signs ────────────────────────────────────────────────────

    def buildVitals(self) -> None:
        page = tk.Frame(self.content, bg=BG)
        self.pages["vitals"] = page
        self.addMosaicBg(page)

        self.title(page, "Vital Signs  (NEWS2)").pack(anchor="w")
        self.sub(page, "National Early Warning Score 2 — enter any available readings. All fields optional.").pack(anchor="w", pady=(2, 16))

        c = self.card(page)
        c.pack(fill="x")
        tk.Frame(c, bg="#059669", height=4).pack(fill="x")

        inner = tk.Frame(c, bg=cardBg)
        inner.pack(fill="x", padx=32, pady=20)

        self.tempVar  = tk.StringVar()
        self.rrVar    = tk.StringVar()
        self.hrVar    = tk.StringVar()
        self.sbpVar   = tk.StringVar()
        self.spo2Var  = tk.StringVar()
        self.o2Var    = tk.BooleanVar()
        self.acvpuVar = tk.StringVar(value="A")

        grid = tk.Frame(inner, bg=cardBg)
        grid.pack(fill="x")

        def vitalField(parent, row, col, label, var, hint):
            f = tk.Frame(parent, bg=cardBg)
            f.grid(row=row, column=col, sticky="ew", padx=(0, 20), pady=4)
            tk.Label(f, text=label, font=("Segoe UI", 10, "bold"), bg=cardBg, fg=TEXT).pack(anchor="w")
            tk.Label(f, text=hint,  font=("Segoe UI", 8),           bg=cardBg, fg=MUTED).pack(anchor="w")
            tk.Entry(f, textvariable=var, font=("Segoe UI", 12),
                     relief="solid", bd=1, fg=TEXT, width=20,
                     insertbackground=PRIMARY).pack(anchor="w", pady=(3, 0))

        vitalField(grid, 0, 0, "Temperature (°C)",          self.tempVar,  "e.g. 37.0  |  Normal: 36.1 – 38.0")
        vitalField(grid, 0, 1, "Respiration Rate (br/min)", self.rrVar,    "e.g. 16    |  Normal: 12 – 20")
        vitalField(grid, 1, 0, "Heart Rate (BPM)",          self.hrVar,    "e.g. 75    |  Normal: 51 – 90")
        vitalField(grid, 1, 1, "Systolic BP (mmHg)",        self.sbpVar,   "e.g. 120   |  Normal: 111 – 219")
        vitalField(grid, 2, 0, "SpO₂ (%)",                  self.spo2Var,  "e.g. 98    |  Normal: 96+")
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

        tk.Frame(inner, bg="#e2e8f0", height=1).pack(fill="x", pady=(14, 10))

        row2 = tk.Frame(inner, bg=cardBg)
        row2.pack(fill="x")

        o2Frame = tk.Frame(row2, bg=cardBg)
        o2Frame.pack(side="left", padx=(0, 30))
        tk.Label(o2Frame, text="On supplemental O₂?",
                 font=("Segoe UI", 10, "bold"), bg=cardBg, fg=TEXT).pack(anchor="w")
        tk.Checkbutton(o2Frame, text="Yes — patient is on supplemental oxygen",
                       variable=self.o2Var, bg=cardBg, fg=TEXT,
                       font=("Segoe UI", 10), activebackground=cardBg).pack(anchor="w", pady=(4, 0))

        acvpuFrame = tk.Frame(row2, bg=cardBg)
        acvpuFrame.pack(side="left")
        tk.Label(acvpuFrame, text="Alertness (ACVPU)",
                 font=("Segoe UI", 10, "bold"), bg=cardBg, fg=TEXT).pack(anchor="w")
        tk.Label(acvpuFrame, text="A=Alert  C=Confused  V=Voice  P=Pain  U=Unresponsive",
                 font=("Segoe UI", 8), bg=cardBg, fg=MUTED).pack(anchor="w")
        ttk.Combobox(acvpuFrame, textvariable=self.acvpuVar,
                     values=["A", "C", "V", "P", "U"],
                     state="readonly", width=6,
                     font=("Segoe UI", 12)).pack(anchor="w", pady=(4, 0))

        self.vitalsInfo = tk.Label(c, text="", font=("Segoe UI", 11, "bold"),
                                   bg=cardBg, fg=PRIMARY)
        self.vitalsInfo.pack(anchor="w", padx=32, pady=(8, 16))

        nav = self.navRow(page)
        self.btn(nav, "Next  →", self.goSymptoms).pack(side="right")
        self.btn(nav, "←  Back", self.goRegistration, color="#6b7280", width=30).pack(side="right", padx=8)

    # ── PAGE 4: Free-text symptoms ─────────────────────────────────────────────

    def buildSymptoms(self) -> None:
        page = tk.Frame(self.content, bg=BG)
        self.pages["symptoms"] = page
        self.addMosaicBg(page)

        self.title(page, "Symptom Description").pack(anchor="w")
        self.sub(page, "Describe symptoms in plain language — the AI layer will identify them.").pack(anchor="w", pady=(2, 16))

        c = self.card(page)
        c.pack(fill="both", expand=True)
        tk.Frame(c, bg="#7c3aed", height=4).pack(fill="x")

        inner = tk.Frame(c, bg=cardBg)
        inner.pack(fill="both", expand=True, padx=32, pady=22)

        tk.Label(inner, text="Describe your symptoms in your own words:",
                 font=("Segoe UI", 11, "bold"), bg=cardBg, fg=TEXT).pack(anchor="w")
        tk.Label(inner, text='e.g.  "I have a fever, dry cough, and feel very tired"',
                 font=("Segoe UI", 9), bg=cardBg, fg=MUTED).pack(anchor="w", pady=(2, 6))

        textFrame = tk.Frame(inner, bg="#f8fafc", relief="solid", bd=1)
        textFrame.pack(fill="x")
        self.freeText = tk.Text(textFrame, font=("Segoe UI", 12), height=4,
                                relief="flat", bd=0, fg=TEXT, wrap="word",
                                bg="#f8fafc", padx=10, pady=8,
                                insertbackground=PRIMARY)
        self.freeText.pack(fill="x")

        self.btn(inner, "Analyse Text  →", self.analyseText, color="#7c3aed", width=16).pack(anchor="w", pady=(10, 14))

        tk.Frame(inner, bg="#e2e8f0", height=1).pack(fill="x", pady=(0, 10))

        tk.Label(inner, text="Detected symptoms:",
                 font=("Segoe UI", 11, "bold"), bg=cardBg, fg=TEXT).pack(anchor="w")

        self.badgeFrame = tk.Frame(inner, bg=cardBg)
        self.badgeFrame.pack(fill="x", pady=4)
        self.noneLbl = tk.Label(self.badgeFrame,
                                text="None yet — click Analyse Text or proceed to questions.",
                                font=("Segoe UI", 10), bg=cardBg, fg=MUTED)
        self.noneLbl.pack(anchor="w")

        nav = self.navRow(page)
        self.btn(nav, "Start Questions  →", self.goConsultation).pack(side="right")
        self.btn(nav, "Diagnose Now", self.instantDiagnose, color="#059669", width=13).pack(side="right", padx=6)
        self.btn(nav, "←  Back", self.goVitals, color="#6b7280", width=10).pack(side="right", padx=8)

    def analyseText(self) -> None:
        raw = self.freeText.get("1.0", "end").strip()
        for w in self.badgeFrame.winfo_children():
            w.destroy()

        if not raw:
            tk.Label(self.badgeFrame, text="Please enter some symptoms first.",
                     font=("Segoe UI", 10), bg=cardBg, fg=MUTED).pack(anchor="w")
            self.extractedSymptoms = []
            return

        try:
            extracted   = extractSymptoms(raw)
            prioritized = prioritizeSymptoms(extracted)
        except Exception as e:
            tk.Label(self.badgeFrame, text=f"Error: {e}",
                     font=("Segoe UI", 10), bg=cardBg, fg="#dc2626").pack(anchor="w")
            self.extractedSymptoms = []
            return

        self.extractedSymptoms = prioritized

        if prioritized:
            row = tk.Frame(self.badgeFrame, bg=cardBg)
            row.pack(anchor="w")
            for sym in prioritized:
                w = getWeight(sym)
                col  = "#2563eb" if w >= 5 else "#7c3aed" if w >= 3 else "#6b7280"
                hcol = "#1d4ed8" if w >= 5 else "#6d28d9" if w >= 3 else "#4b5563"
                lbl = tk.Label(row, text=f"  {symptomDisplayName(sym)}  [w={w}]  ",
                               font=("Segoe UI", 10, "bold"),
                               bg=col, fg="white", padx=4, pady=5, cursor="hand2")
                lbl.pack(side="left", padx=3, pady=3)
                lbl.bind("<Enter>", lambda e, l=lbl, hc=hcol: l.configure(bg=hc))
                lbl.bind("<Leave>", lambda e, l=lbl, c=col:   l.configure(bg=c))
        else:
            tk.Label(self.badgeFrame, text="No recognised symptoms found.",
                     font=("Segoe UI", 10), bg=cardBg, fg=MUTED).pack(anchor="w")

    # ── PAGE 5: Consultation — Doctor + Q&A ───────────────────────────────────

    def buildConsultation(self) -> None:
        page = tk.Frame(self.content, bg=BG)
        self.pages["consultation"] = page
        self.addMosaicBg(page)

        hdr = tk.Frame(page, bg=BG)
        hdr.pack(fill="x", pady=(0, 6))
        tk.Label(hdr, text="Symptom Assessment",
                 font=("Segoe UI", 17, "bold"), bg=BG, fg=TEXT).pack(side="left")
        self.patientLbl = tk.Label(hdr, text="", font=("Segoe UI", 10), bg=BG, fg=MUTED)
        self.patientLbl.pack(side="left", padx=14, pady=6)

        progRow = tk.Frame(page, bg=BG)
        progRow.pack(fill="x", pady=(0, 8))
        self.progLbl = tk.Label(progRow, text="Question 0 of --",
                                font=("Segoe UI", 9), bg=BG, fg=MUTED)
        self.progLbl.pack(anchor="w")
        self.progBar = ttk.Progressbar(progRow, length=480, mode="determinate")
        self.progBar.pack(fill="x", pady=2)

        split = tk.Frame(page, bg=BG)
        split.pack(fill="both", expand=True)

        # Doctor panel
        docPanel = tk.Frame(split, bg=DOCTOR_BG, width=205)
        docPanel.pack(side="left", fill="y")
        docPanel.pack_propagate(False)

        self.doctorWidget = DoctorCanvas(docPanel, width=205)
        self.doctorWidget.pack(fill="both", expand=True)

        self.doctorStatus = tk.Label(
            docPanel,
            text="Hello! I'm Dr. AI.",
            font=("Segoe UI", 9, "italic"),
            bg=DOCTOR_BG, fg="#1e40af",
            wraplength=190, justify="center"
        )
        self.doctorStatus.pack(pady=(0, 8))

        # Right panel
        right = tk.Frame(split, bg=BG)
        right.pack(side="left", fill="both", expand=True, padx=(12, 0))

        self.inferenceBanner = tk.Label(
            right, text="  ● Ready",
            font=("Segoe UI", 9), bg=BG, fg=YES_CLR, anchor="w"
        )
        self.inferenceBanner.pack(fill="x", pady=(0, 4))

        # Speech bubble
        bubbleOuter = tk.Frame(right, bg=BG)
        bubbleOuter.pack(fill="x", pady=(0, 8))
        tk.Frame(bubbleOuter, bg=PRIMARY, width=5).pack(side="left", fill="y")
        bubble = tk.Frame(bubbleOuter, bg="#eff6ff", padx=18, pady=16)
        bubble.pack(side="left", fill="both", expand=True)
        self.qLbl = tk.Label(bubble, text="",
                             font=("Segoe UI", 14, "bold"),
                             bg="#eff6ff", fg="#1e3a5f",
                             wraplength=420, justify="left")
        self.qLbl.pack(anchor="w")

        # Answer buttons
        btnCard = tk.Frame(right, bg=cardBg, padx=18, pady=14)
        btnCard.pack(fill="x")
        btnRow = tk.Frame(btnCard, bg=cardBg)
        btnRow.pack()

        self.btnYes = self.btn(btnRow, "✓  YES", lambda: self.answer(True),
                               color=YES_CLR, width=11)
        self.btnYes.pack(side="left", padx=8, pady=4)

        self.btnNo = self.btn(btnRow, "✗  NO", lambda: self.answer(False),
                              color=NO_CLR, width=11)
        self.btnNo.pack(side="left", padx=8, pady=4)

        self.btnSkip = self.btn(btnRow, "?  Not sure", lambda: self.answer(None),
                                color="#6b7280", width=11)
        self.btnSkip.pack(side="left", padx=8, pady=4)

        tk.Label(btnCard, text="Answer based on your current symptoms",
                 font=("Segoe UI", 8), bg=cardBg, fg=MUTED).pack(pady=(4, 0))

        confirmedArea = tk.Frame(right, bg=BG)
        confirmedArea.pack(fill="x", pady=(8, 0))
        tk.Label(confirmedArea, text="Confirmed so far:",
                 font=("Segoe UI", 10, "bold"), bg=BG, fg=MUTED).pack(anchor="w", pady=(0, 4))
        self.confirmedStrip = tk.Frame(confirmedArea, bg=BG)
        self.confirmedStrip.pack(fill="x")

    # ── PAGE 6: Results ────────────────────────────────────────────────────────

    def buildResults(self) -> None:
        page = tk.Frame(self.content, bg=BG)
        self.pages["results"] = page
        self.addMosaicBg(page)

        self.title(page, "Diagnosis Results").pack(anchor="w")
        self.sub(page, "Based on reported symptoms and logical inference.").pack(anchor="w", pady=(2, 12))

        outer = tk.Frame(page, bg=BG)
        outer.pack(fill="both", expand=True)

        canvas = tk.Canvas(outer, bg=BG, bd=0, highlightthickness=0)
        vsb    = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        self.resInner = tk.Frame(canvas, bg=BG)

        self.resInner.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.resInner, anchor="nw")
        canvas.configure(yscrollcommand=vsb.set)

        canvas.bind_all("<MouseWheel>",
                        lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        canvas.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        self.resCanvas = canvas

    # ── Navigation actions ─────────────────────────────────────────────────────

    def checkHistory(self) -> None:
        name = self.nameVar.get().strip()
        if len(name) < 2:
            self.historyLbl.configure(text="Enter a name above to check visit history.")
            return
        msg = patient_history.summary(name)
        if msg:
            chronic = patient_history.chronicSymptoms(name)
            extra = ""
            if chronic:
                extra = "  Chronic: " + ", ".join(symptomDisplayName(s) for s in chronic[:4])
            self.historyLbl.configure(text=msg + extra, fg="#1e40af")
        else:
            self.historyLbl.configure(text="New patient — no previous visits on file.", fg=MUTED)

    def goRegistration(self) -> None:
        self.show("registration")

    def goVitals(self) -> None:
        name = self.nameVar.get().strip() or "Anonymous"
        ageStr = self.ageVar.get().strip()
        age    = int(ageStr) if ageStr.isdigit() else None
        self.session = UserSession(patient_name=name, age=age, gender=self.genderVar.get())
        self.show("vitals")

    def goSymptoms(self) -> None:
        if not self.session:
            return
        vitals = self.session.record.vital_signs
        try:
            t   = self.tempVar.get().strip()
            rr  = self.rrVar.get().strip()
            h   = self.hrVar.get().strip()
            sbp = self.sbpVar.get().strip()
            s   = self.spo2Var.get().strip()
            if t:   vitals.temperature_celsius = float(t)
            if rr:  vitals.respiration_rate    = int(rr)
            if h:   vitals.heart_rate_bpm      = int(h)
            if sbp: vitals.systolic_bp         = int(sbp)
            if s:   vitals.oxygen_saturation   = float(s)
            vitals.on_supplemental_o2 = self.o2Var.get()
            acvpu = self.acvpuVar.get().strip().upper()
            if acvpu in ("A", "C", "V", "P", "U"):
                vitals.acvpu = acvpu
        except ValueError:
            pass

        news2 = vitals.news2Score()
        risk  = vitals.news2Risk()
        riskCol = {"LOW": YES_CLR, "MEDIUM": SEV_MOD, "HIGH": SEV_CRIT}.get(
            risk.split()[0], PRIMARY
        )
        self.vitalsInfo.configure(text=f"NEWS2 Score: {news2}  —  {risk}", fg=riskCol)

        for sym in vitals.asSymptoms():
            self.session.record.confirm(sym)

        self.show("symptoms")

    def instantDiagnose(self) -> None:
        if not self.session:
            return
        if not self.extractedSymptoms:
            messagebox.showinfo(
                "No Symptoms Detected",
                "Please type your symptoms and click 'Analyse Text' first."
            )
            return
        for sym in self.extractedSymptoms:
            if not self.session.hasBeenAsked(sym):
                self.session.recordExchange(sym, "", "yes")
        self.excluded         = set()
        self.questionsPosed   = 0
        self.pendingFollowups = []
        self.currentSym       = ""
        self.currentQ         = ""
        self.finish()

    def goConsultation(self) -> None:
        if not self.session:
            return

        for sym in self.extractedSymptoms:
            if not self.session.hasBeenAsked(sym):
                self.session.recordExchange(sym, "", "yes")

        self.excluded:          set       = set()
        self.questionsPosed:   int       = 0
        self.pendingFollowups: List[str] = []
        self.currentSym:       str       = ""
        self.currentQ:         str       = ""

        self.patientLbl.configure(text=f"—  {self.session.patient_name}")

        news2 = self.session.record.vital_signs.news2Score()
        if news2 >= NEWS2_ESCALATION_THRESHOLD:
            self.pendingFollowups = [
                s for s in self.bridge.getRedFlags()
                if not self.session.hasBeenAsked(s)
            ]

        self.setDoctorExpr("neutral")
        self.updateDoctorStatus("Hello! Let's figure out what's going on.")
        self.show("consultation")
        self.nextQuestion()

    def nextQuestion(self) -> None:
        if not self.session or self.questionsPosed >= MAX_QUESTIONS:
            self.finish()
            return

        while self.pendingFollowups:
            sym = self.pendingFollowups.pop(0)
            if not self.session.hasBeenAsked(sym) and sym not in self.excluded:
                self.askQuestion(sym)
                return

        self.setButtonsEnabled(False)
        self.inferenceBanner.configure(text="  ◌  Reasoning…", fg=SEV_MOD)
        self.setDoctorExpr("thinking")
        self.updateDoctorStatus("Let me think…")

        asked     = list(self.session.log.asked_symptoms)
        confirmed = list(self.session.record.confirmed)
        denied    = list(self.session.record.denied)
        excluded  = set(self.excluded)

        self.inferenceThread = threading.Thread(
            target=self.runPrologQuery,
            args=(asked, confirmed, denied, excluded),
            daemon=True,
        )
        self.inferenceThread.start()

    # ── Concurrency helpers ────────────────────────────────────────────────────

    def runPrologQuery(self, asked, confirmed, denied, excluded) -> None:
        sym = self.bridge.queryNextQuestion(asked, confirmed, denied, excluded)
        self.resultQueue.put(lambda: self.onSymbolReady(sym))

    def onSymbolReady(self, sym: Optional[str]) -> None:
        self.inferenceBanner.configure(text="  ●  Ready", fg=YES_CLR)
        self.setDoctorExpr("neutral")
        if sym is None:
            self.updateDoctorStatus("I have enough information now!")
            self.finish()
        else:
            self.askQuestion(sym)
            self.setButtonsEnabled(True)

    def pollResultQueue(self) -> None:
        try:
            callback = self.resultQueue.get_nowait()
            callback()
        except queue.Empty:
            pass
        self.root.after(50, self.pollResultQueue)

    def setButtonsEnabled(self, enabled: bool) -> None:
        state = tk.NORMAL if enabled else tk.DISABLED
        for b in (self.btnYes, self.btnNo, self.btnSkip):
            b.configure(state=state)

    def askQuestion(self, sym: str) -> None:
        self.currentSym = sym
        self.currentQ   = self.bridge.getQuestionText(sym)
        self.refreshQuestion()

    def refreshQuestion(self) -> None:
        assert self.session is not None
        self.progLbl.configure(
            text=f"Question {self.questionsPosed + 1}  (max {MAX_QUESTIONS})"
        )
        self.progBar.configure(maximum=MAX_QUESTIONS, value=self.questionsPosed)

        self.startTypeAnimation(self.qLbl, self.currentQ)
        self.setDoctorExpr("neutral")
        self.updateDoctorStatus("Please answer honestly.")

        for w in self.confirmedStrip.winfo_children():
            w.destroy()
        confirmed = sorted(self.session.record.confirmed, key=getWeight, reverse=True)
        if confirmed:
            row = tk.Frame(self.confirmedStrip, bg=BG)
            row.pack(anchor="w")
            for s in confirmed[:8]:
                tk.Label(row, text=f"  {symptomDisplayName(s)}  ",
                         font=("Segoe UI", 9), bg="#dcfce7", fg="#166534",
                         padx=2, pady=3).pack(side="left", padx=2, pady=2)
        else:
            tk.Label(self.confirmedStrip, text="None confirmed yet.",
                     font=("Segoe UI", 9), bg=BG, fg=MUTED).pack(anchor="w")

    def answer(self, yes: Optional[bool]) -> None:
        if not self.currentSym or not self.session:
            return

        if self.typeJob:
            self.root.after_cancel(self.typeJob)
            self.typeJob = None
            self.qLbl.configure(text=self.currentQ)

        sym, q = self.currentSym, self.currentQ
        if yes is True:
            response = "yes"
        elif yes is None:
            response = "?"
        else:
            response = "no"
        self.session.recordExchange(sym, q, response)
        self.questionsPosed += 1

        if yes is True:
            self.setDoctorExpr("happy")
            self.updateDoctorStatus("Good to know!")
            self.root.after(1400, lambda: self.setDoctorExpr("thinking"))
            session = self.session
            self.pendingFollowups = [
                f for f in self.bridge.queryFollowups(sym)
                if session is not None
                and not session.hasBeenAsked(f)
                and f not in self.excluded
            ]
        elif yes is None:
            self.setDoctorExpr("thinking")
            self.updateDoctorStatus("No worries, let's move on.")
        else:
            self.setDoctorExpr("concerned")
            self.updateDoctorStatus("I see, noted.")
            self.root.after(1400, lambda: self.setDoctorExpr("thinking"))
            for skip in self.bridge.queryExclusions(sym):
                self.excluded.add(skip)

        confirmed = list(self.session.record.confirmed)
        if len(confirmed) >= MIN_SYMPTOMS:
            candidates = self.bridge.queryDiagnosis(
                confirmed=confirmed, denied=list(self.session.record.denied)
            )
            if candidates and candidates[0][1] >= CONFIDENCE_THRESHOLD:
                self.finish(candidates)
                return

        self.nextQuestion()

    def finish(self, pre: Optional[list] = None) -> None:
        if not self.session:
            return
        confirmed = list(self.session.record.confirmed)
        denied    = list(self.session.record.denied)
        sev       = computeSeverityScore(confirmed)

        candidates = pre or self.bridge.queryDiagnosis(confirmed=confirmed, denied=denied)
        disease, confidence = candidates[0] if candidates else ("undetermined", 0.0)

        candDicts = [{"disease": d, "confidence": c} for d, c in candidates]
        self.session.finalize(disease, confidence, sev)
        self.session.record.candidate_diagnoses = candDicts

        patient_history.recordVisit(
            name=self.session.patient_name,
            diagnosis=disease,
            confirmed=confirmed,
            severity=sev,
            candidates=candDicts,
            gender=self.session.gender,
        )

        self.lastCandidates = candidates
        self.setDoctorExpr("happy")
        self.updateDoctorStatus("Assessment complete!")

        import re as reLib
        visitDt  = self.session.record.created_at
        safeName = reLib.sub(r"[^\w]", "_", self.session.patient_name.strip())
        folderName = f"{safeName}_{visitDt.strftime('%Y-%m-%d')}"
        patientDir = Path(__file__).parent / "patient_data" / folderName
        patientDir.mkdir(parents=True, exist_ok=True)

        sid       = self.session.session_id
        vitals    = self.session.record.vital_signs
        sevLabel  = (
            "CRITICAL" if sev >= 30 else
            "HIGH"     if sev >= 18 else
            "MODERATE" if sev >= 9  else
            "LOW"
        )

        txtPath  = patientDir / f"consultation_{sid}.txt"
        jsonPath = patientDir / f"consultation_{sid}.json"
        xlsxPath = patientDir / f"consultation_{sid}.xlsx"

        try:
            txtPath.write_text(self.session.generateReport(), encoding="utf-8")
        except Exception as exc:
            print(f"[save] Could not write text report: {exc}")

        try:
            jsonPath.write_text(self.session.log.exportJson(), encoding="utf-8")
        except Exception as exc:
            print(f"[save] Could not write JSON log: {exc}")

        try:
            consultation_log.record(
                patient_name     = self.session.patient_name,
                session_id       = sid,
                age              = self.session.age,
                gender           = self.session.gender,
                vitals_summary   = vitals.summary(),
                news2Score      = vitals.news2Score(),
                news2Risk       = vitals.news2Risk(),
                confirmed        = sorted(self.session.record.confirmed),
                denied           = sorted(self.session.record.denied),
                skipped          = sorted(self.session.record.skipped),
                diagnosis        = disease,
                confidence       = confidence,
                severity         = sev,
                severity_label   = sevLabel,
                candidates       = candDicts,
                questions_asked  = self.session.log.size(),
                durationSeconds  = self.session.record.durationSeconds(),
                visit_dt         = visitDt,
                file_path        = xlsxPath,
            )
        except Exception as exc:
            print(f"[consultation_log] Could not write Excel log: {exc}")

        self.savedPaths = (txtPath, jsonPath, xlsxPath)

        self.populateResults()
        self.show("results")

    # ── Results population ─────────────────────────────────────────────────────

    @staticmethod
    def news2CareLevel(score: int, vitalsRecorded: bool):
        if not vitalsRecorded:
            return (
                "N/A",
                "Vital signs were not recorded. Enter vitals on the previous screen for a "
                "personalised care recommendation.",
                "#f8fafc", TEXT, "#64748b",
            )
        if score == 0:
            return (
                "SELF-CARE",
                "Your vital signs are within normal range. Self-care is appropriate. "
                "Monitor symptoms and contact your family doctor if they worsen or persist beyond 48 hours.",
                "#f0fdf4", "#166534", "#16a34a",
            )
        elif score <= 4:
            return (
                "SEE YOUR GP",
                "NEWS2 score indicates a LOW clinical risk. You should see your family doctor (GP) "
                "within the next 24–48 hours, or sooner if symptoms worsen.",
                "#eff6ff", "#1e40af", "#2563eb",
            )
        elif score <= 6:
            return (
                "URGENT GP TODAY",
                "NEWS2 score indicates a MEDIUM clinical risk. Contact your family doctor urgently "
                "for a same-day assessment, or go to an urgent care clinic. Do not wait.",
                "#fffbeb", "#92400e", "#d97706",
            )
        else:
            return (
                "GO TO EMERGENCY",
                "NEWS2 score indicates HIGH clinical risk. Go to the Emergency Department immediately "
                "or call emergency services (999). Hospital admission is likely required.",
                "#fef2f2", "#991b1b", "#dc2626",
            )

    def buildDiffRow(self, parent: tk.Frame, rank: int, cand: dict) -> None:
        dName = cand["disease"]
        dConf = cand["confidence"]
        col   = "#166534" if dConf >= 0.6 else "#92400e" if dConf >= 0.4 else "#6b7280"
        hdrBg = "#f1f5f9"

        wrapper = tk.Frame(parent, bg=cardBg)
        wrapper.pack(fill="x", padx=18, pady=(0, 6))

        hdr = tk.Frame(wrapper, bg=hdrBg, relief="solid", bd=1, cursor="hand2")
        hdr.pack(fill="x")

        tk.Label(hdr, text=f"#{rank}  {dName.replace('_', ' ').title()}",
                 font=("Segoe UI", 11, "bold"), bg=hdrBg, fg=col,
                 padx=12, pady=9).pack(side="left")
        hint = tk.Label(hdr, text=f"{dConf:.0%} confidence  ▼ Click for precautions",
                        font=("Segoe UI", 9), bg=hdrBg, fg=MUTED, padx=10, pady=9)
        hint.pack(side="right")

        detailBg = "#fefce8"
        detail   = tk.Frame(wrapper, bg=detailBg)

        precs = self.precautions.get(dName, [])
        if precs:
            for p in precs:
                pr = tk.Frame(detail, bg=detailBg)
                pr.pack(fill="x", padx=16, pady=2)
                tk.Label(pr, text="•",                                  font=("Segoe UI", 12), bg=detailBg, fg="#854d0e").pack(side="left")
                tk.Label(pr, text=p.replace("_", " ").title(),          font=("Segoe UI", 10), bg=detailBg, fg=TEXT     ).pack(side="left", padx=6)
        else:
            tk.Label(detail, text="No specific precautions on file for this condition.",
                     font=("Segoe UI", 10), bg=detailBg, fg=MUTED, padx=16, pady=8).pack(anchor="w")
        tk.Frame(detail, bg=detailBg, height=6).pack()

        def toggle(event=None):
            if detail.winfo_ismapped():
                detail.pack_forget()
                hint.configure(text=f"{dConf:.0%} confidence  ▼ Click for precautions")
            else:
                detail.pack(fill="x")
                hint.configure(text=f"{dConf:.0%} confidence  ▲ Hide precautions")
            self.resCanvas.configure(scrollregion=self.resCanvas.bbox("all"))

        for widget in hdr.winfo_children():
            widget.bind("<Button-1>", toggle)
        hdr.bind("<Button-1>", toggle)

    def populateResults(self) -> None:
        assert self.session is not None
        for w in self.resInner.winfo_children():
            w.destroy()

        r       = self.session.record
        disease = r.diagnosis or "undetermined"
        conf    = r.confidence
        sev     = r.severity_score

        if   sev >= 30: sevCol, sevLbl = SEV_CRIT, "CRITICAL"
        elif sev >= 18: sevCol, sevLbl = SEV_HIGH, "HIGH"
        elif sev >= 9:  sevCol, sevLbl = SEV_MOD,  "MODERATE"
        else:           sevCol, sevLbl = SEV_LOW,  "LOW"

        vitals         = r.vital_signs
        n2Score        = vitals.news2Score()
        n2Risk         = vitals.news2Risk()
        vitalsRecorded = vitals.summary() != "Not recorded"

        riskWord  = n2Risk.split()[0]
        n2Palette = {
            "LOW":    ("#f0fdf4", "#166534", YES_CLR),
            "MEDIUM": ("#fffbeb", "#92400e", SEV_MOD),
            "HIGH":   ("#fef2f2", "#991b1b", SEV_CRIT),
        }
        vbg, vtxt, vbadge = n2Palette.get(riskWord, ("#f0f4f8", TEXT, PRIMARY))

        n2Card = tk.Frame(self.resInner, bg=vbg, relief="flat", bd=1)
        n2Card.pack(fill="x", pady=(0, 10))
        innerN2 = tk.Frame(n2Card, bg=vbg)
        innerN2.pack(fill="x", padx=22, pady=10)

        leftN2 = tk.Frame(innerN2, bg=vbg)
        leftN2.pack(side="left", expand=True, fill="both")
        tk.Label(leftN2, text="NEWS2 — National Early Warning Score 2  (RCP 2017)",
                 font=("Segoe UI", 9, "bold"), bg=vbg, fg=vtxt).pack(anchor="w")
        tk.Label(leftN2, text=vitals.summary() if vitalsRecorded else "Vital signs not recorded.",
                 font=("Segoe UI", 9), bg=vbg, fg=vtxt,
                 wraplength=430, justify="left").pack(anchor="w", pady=(2, 0))

        rightN2 = tk.Frame(innerN2, bg=vbg)
        rightN2.pack(side="right")
        badgeN2 = tk.Frame(rightN2, bg=vbadge, padx=14, pady=8)
        badgeN2.pack()
        tk.Label(badgeN2, text=str(n2Score), font=("Segoe UI", 22, "bold"), bg=vbadge, fg="white").pack()
        tk.Label(badgeN2, text=riskWord,     font=("Segoe UI", 9,  "bold"), bg=vbadge, fg="white").pack()

        careBadge, careText, careBg, careFg, careBadgeBg = \
            self.news2CareLevel(n2Score, vitalsRecorded)
        recCard  = tk.Frame(self.resInner, bg=careBg, relief="flat", bd=1)
        recCard.pack(fill="x", pady=(0, 10))
        recInner = tk.Frame(recCard, bg=careBg)
        recInner.pack(fill="x", padx=22, pady=10)

        badgeFrame = tk.Frame(recInner, bg=careBadgeBg, padx=10, pady=6)
        badgeFrame.pack(side="left")
        tk.Label(badgeFrame, text=careBadge, font=("Segoe UI", 9, "bold"), bg=careBadgeBg, fg="white").pack()
        tk.Label(recInner, text=careText, font=("Segoe UI", 10), bg=careBg, fg=careFg,
                 wraplength=480, justify="left").pack(side="left", padx=14)

        # Diagnosis hero card
        hero = self.card(self.resInner)
        hero.pack(fill="x", pady=(0, 10))
        tk.Frame(hero, bg=PRIMARY, height=5).pack(fill="x")

        body = tk.Frame(hero, bg=cardBg)
        body.pack(fill="x", padx=22, pady=14)

        left = tk.Frame(body, bg=cardBg)
        left.pack(side="left", expand=True, fill="both")
        diagTxt = disease.replace("_", " ").upper() if disease != "undetermined" else "UNDETERMINED"
        tk.Label(left, text=diagTxt,           font=("Segoe UI", 22, "bold"), bg=cardBg, fg=PRIMARY).pack(anchor="w")
        tk.Label(left, text="MOST LIKELY DIAGNOSIS", font=("Segoe UI", 8),   bg=cardBg, fg=MUTED  ).pack(anchor="w")

        rightBody = tk.Frame(body, bg=cardBg)
        rightBody.pack(side="right")
        for val, label, col in [
            (f"{conf:.0%}", "confidence", PRIMARY),
            (str(sev),     f"severity\n{sevLbl}", sevCol),
        ]:
            box = tk.Frame(rightBody, bg=col, padx=16, pady=10)
            box.pack(side="left", padx=6)
            tk.Label(box, text=val,   font=("Segoe UI", 20, "bold"), bg=col, fg="white").pack()
            tk.Label(box, text=label, font=("Segoe UI", 8),          bg=col, fg="white").pack()

        # Differential diagnoses
        others = [
            c for c in (getattr(r, "candidate_diagnoses", None) or [])
            if c["disease"] != disease
        ]
        if others:
            diffCard = self.card(self.resInner)
            diffCard.pack(fill="x", pady=(0, 10))
            tk.Label(diffCard, text="Differential Diagnoses  —  click a row to view precautions",
                     font=("Segoe UI", 12, "bold"), bg=cardBg, fg=TEXT
                     ).pack(anchor="w", padx=22, pady=(14, 8))
            for rank, cand in enumerate(others[:2], start=2):
                self.buildDiffRow(diffCard, rank, cand)
            tk.Frame(diffCard, bg=cardBg, height=6).pack()

        # Description
        desc = self.descriptions.get(disease, "")
        if desc:
            dc = self.card(self.resInner)
            dc.pack(fill="x", pady=(0, 10))
            tk.Label(dc, text="About this Condition",
                     font=("Segoe UI", 12, "bold"), bg=cardBg, fg=TEXT).pack(anchor="w", padx=22, pady=(14, 4))
            tk.Label(dc, text=desc, font=("Segoe UI", 10), bg=cardBg, fg=TEXT,
                     wraplength=560, justify="left", anchor="w").pack(fill="x", padx=22, pady=(0, 14))

        # Confirmed symptoms grid
        symCard = self.card(self.resInner)
        symCard.pack(fill="x", pady=(0, 10))
        tk.Label(symCard, text=f"Confirmed Symptoms  ({len(r.confirmed)})",
                 font=("Segoe UI", 12, "bold"), bg=cardBg, fg=TEXT).pack(anchor="w", padx=22, pady=(14, 8))

        symGrid = tk.Frame(symCard, bg=cardBg)
        symGrid.pack(fill="x", padx=22, pady=(0, 14))
        for i, sym in enumerate(sorted(r.confirmed, key=getWeight, reverse=True)):
            w = getWeight(sym)
            bg  = "#eff6ff" if w >= 5 else "#f5f3ff" if w >= 3 else "#f8fafc"
            fgc = "#1d4ed8" if w >= 5 else "#6d28d9" if w >= 3 else TEXT
            tk.Label(symGrid, text=f"  {symptomDisplayName(sym)}  [w={w}]  ",
                     font=("Segoe UI", 10), bg=bg, fg=fgc,
                     padx=4, pady=6, anchor="w",
                     relief="flat").grid(row=i // 2, column=i % 2,
                                         sticky="ew", padx=4, pady=2)
        symGrid.columnconfigure(0, weight=1)
        symGrid.columnconfigure(1, weight=1)

        # Primary precautions
        precs = self.precautions.get(disease, [])
        if precs:
            pc = self.card(self.resInner)
            pc.pack(fill="x", pady=(0, 10))
            tk.Label(pc, text="Recommended Precautions",
                     font=("Segoe UI", 12, "bold"), bg=cardBg, fg=TEXT).pack(anchor="w", padx=22, pady=(14, 8))
            for p in precs:
                row = tk.Frame(pc, bg=cardBg)
                row.pack(fill="x", padx=22, pady=2)
                tk.Label(row, text="•",                           font=("Segoe UI", 12, "bold"), bg=cardBg, fg=YES_CLR).pack(side="left")
                tk.Label(row, text=p.replace("_", " ").title(),   font=("Segoe UI", 11),         bg=cardBg, fg=TEXT   ).pack(side="left", padx=8)
            tk.Frame(pc, bg=cardBg, height=10).pack()

        # Session footer
        footer = self.card(self.resInner)
        footer.pack(fill="x", pady=(0, 10))
        tk.Frame(footer, bg="#e2e8f0", height=1).pack(fill="x")

        infoRow = tk.Frame(footer, bg=cardBg)
        infoRow.pack(fill="x", padx=22, pady=(12, 6))
        tk.Label(infoRow,
                 text=(f"Session: {self.session.session_id}     "
                       f"Patient: {self.session.patient_name}     "
                       f"Questions answered: {self.session.log.size()}"),
                 font=("Segoe UI", 9), bg=cardBg, fg=MUTED).pack(side="left")

        footerBtns = tk.Frame(footer, bg=cardBg)
        footerBtns.pack(anchor="e", padx=22, pady=(0, 14))
        self.btn(footerBtns, "Save Report", self.save,    color=YES_CLR,  width=12).pack(side="left", padx=5)
        self.btn(footerBtns, "New Patient", self.restart, color="#6b7280", width=12).pack(side="left", padx=5)

        tk.Label(self.resInner,
                 text="DISCLAIMER: AI-assisted educational tool only. Always consult a licensed medical professional.",
                 font=("Segoe UI", 9), bg=BG, fg="#ef4444", wraplength=560).pack(pady=8)

    # ── Doctor helpers ─────────────────────────────────────────────────────────

    def setDoctorExpr(self, expr: str) -> None:
        if self.doctorWidget and self.doctorWidget.winfo_exists():
            self.doctorWidget.setExpression(expr)

    def updateDoctorStatus(self, msg: str) -> None:
        if self.doctorStatus and self.doctorStatus.winfo_exists():
            self.doctorStatus.configure(text=msg)

    def startTypeAnimation(self, widget: tk.Label, text: str) -> None:
        if self.typeJob:
            self.root.after_cancel(self.typeJob)
            self.typeJob = None
        widget.configure(text="")
        self.typeText(widget, text, 0)

    def typeText(self, widget: tk.Label, text: str, index: int) -> None:
        if not widget.winfo_exists():
            return
        widget.configure(text=text[:index])
        if index < len(text):
            self.typeJob = self.root.after(18, lambda: self.typeText(widget, text, index + 1))
        else:
            self.typeJob = None

    # ── File save ──────────────────────────────────────────────────────────────

    def save(self) -> None:
        assert self.session is not None
        paths = getattr(self, "savedPaths", None)
        if paths:
            txt, jsn, xlsx = paths
            messagebox.showinfo(
                "Patient Data Saved",
                f"All files saved to patient_data/:\n\n"
                f"  Text:  {txt.name}\n"
                f"  JSON:  {jsn.name}\n"
                f"  Excel: {xlsx.name}"
            )
        else:
            messagebox.showwarning("Save", "No session data to show.")

    # ── New consultation ───────────────────────────────────────────────────────

    def restart(self) -> None:
        self.session = None
        self.extractedSymptoms = []
        self.freeText.delete("1.0", "end")
        for w in self.badgeFrame.winfo_children():
            w.destroy()
        self.noneLbl = tk.Label(self.badgeFrame,
                                text="None yet — click Analyse Text or proceed to questions.",
                                font=("Segoe UI", 10), bg=cardBg, fg=MUTED)
        self.noneLbl.pack(anchor="w")
        for var in (self.nameVar, self.ageVar, self.tempVar, self.rrVar,
                    self.hrVar, self.sbpVar, self.spo2Var):
            var.set("")
        self.genderVar.set("Rather not say")
        self.o2Var.set(False)
        self.acvpuVar.set("A")
        self.vitalsInfo.configure(text="")
        self.setDoctorExpr("neutral")
        self.updateDoctorStatus("Hello! I'm Dr. AI.")
        self.show("welcome")

    # ── Main loop ──────────────────────────────────────────────────────────────

    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    DiagnosticGUI().run()
